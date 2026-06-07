from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from enterprise_rag_agent.config import AgentSettings
from enterprise_rag_agent.memory import ConversationMemory, format_memories
from enterprise_rag_agent.prompts import (
    ANSWER_PROMPT,
    INTENT_PROMPT,
    MEMORY_PROMPT,
    REFLECTION_PROMPT,
    REWRITE_PROMPT,
    TOOL_PROMPT,
)
from enterprise_rag_agent.reranker import BGEReranker
from enterprise_rag_agent.schemas import (
    AgentState,
    IntentResult,
    MemoryRecord,
    ReflectionResult,
    RewriteResult,
)
from enterprise_rag_agent.tools import build_default_tools
from enterprise_rag_agent.vectorstore import BGEM3Embeddings, build_vector_store


def _format_docs(docs: list[dict[str, Any]]) -> str:
    if not docs:
        return "无召回结果"
    blocks = []
    for index, doc in enumerate(docs, start=1):
        blocks.append(
            f"[{index}] {doc['title']} ({doc['department']})\n{doc['content']}"
        )
    return "\n\n".join(blocks)


def _format_tool_outputs(tool_outputs: list[dict[str, Any]]) -> str:
    if not tool_outputs:
        return "无工具结果"
    return "\n".join(
        f"- {item['tool_name']}: {item['output']}" for item in tool_outputs
    )


def _last_topic(memories: list[str]) -> str:
    if not memories:
        return ""
    text = memories[-1].strip()
    return text[:40]


def _parse_json_model(content: str, model_cls):
    payload = content.strip()
    if payload.startswith("```"):
        payload = payload.strip("`")
        payload = payload.replace("json", "", 1).strip()
    start = payload.find("{")
    end = payload.rfind("}")
    if start >= 0 and end >= 0:
        payload = payload[start : end + 1]
    data = json.loads(payload)
    return model_cls.model_validate(data)


@dataclass
class OfflineRuntime:
    top_k: int

    def rewrite(self, query: str, memories: list[str]) -> RewriteResult:
        topic = _last_topic(memories)
        rewritten = query.strip()
        if topic and len(rewritten) < 24:
            rewritten = f"{rewritten}（结合历史上下文：{topic}）"
        return RewriteResult(
            rewritten_query=rewritten,
            rationale="离线模式下采用轻量改写，尽量保留原始语义。",
        )

    def intent(self, query: str, rewritten: str) -> IntentResult:
        text = f"{query} {rewritten}".lower()
        tool_names: list[str] = []
        needs_tools = False
        needs_retrieval = True
        intent = "qa"

        if re.search(r"\b(time|clock|now|几点|时间)\b", text):
            intent = "tool"
            needs_tools = True
            tool_names.append("current_time")
            needs_retrieval = False
        elif any(keyword in text for keyword in ["工单", "报修", "打不开", "vpn", "邮箱", "权限"]):
            intent = "tool"
            needs_tools = True
            tool_names.append("create_helpdesk_ticket")
        elif any(keyword in text for keyword in ["报销", "年假", "制度", "流程", "申请", "规定", "政策"]):
            intent = "policy"
        elif any(keyword in text for keyword in ["你好", "谢谢", "你是谁"]):
            intent = "chit_chat"
            needs_retrieval = False

        return IntentResult(
            intent=intent,
            needs_retrieval=needs_retrieval,
            needs_tools=needs_tools,
            tool_names=tool_names,
            reason="离线模式下基于关键词进行意图路由。",
        )

    def answer(
        self,
        user_query: str,
        rewritten_query: str,
        intent: str,
        retrieval_context: str,
        tool_context: str,
        memory_context: str,
    ) -> str:
        parts = [
            f"问题：{user_query}",
            f"改写：{rewritten_query}",
            f"意图：{intent}",
        ]
        if retrieval_context != "无召回结果":
            parts.append(f"知识库依据：\n{retrieval_context}")
        if tool_context != "无工具结果":
            parts.append(f"工具结果：\n{tool_context}")
        parts.append(f"相关记忆：\n{memory_context}")
        parts.append("这是离线模式返回的演示答案，等你配置好 OpenAI key 后会自动切换成真实模型回答。")
        return "\n\n".join(parts)

    def reflect(
        self,
        user_query: str,
        final_answer: str,
        retrieved_docs: list[dict[str, Any]],
        tool_outputs: list[dict[str, Any]],
    ) -> ReflectionResult:
        confidence = "high" if retrieved_docs or tool_outputs else "medium"
        needs_follow_up = False
        follow_up_question = ""
        if not retrieved_docs and not tool_outputs:
            confidence = "low"
            if any(keyword in user_query for keyword in ["怎么", "如何", "为何", "为什么"]):
                needs_follow_up = True
                follow_up_question = "你希望我优先按制度说明，还是按实际操作步骤来回答？"
        return ReflectionResult(
            confidence=confidence,  # type: ignore[arg-type]
            issues=[],
            needs_follow_up=needs_follow_up,
            follow_up_question=follow_up_question,
        )

    def memory_summary(self, user_query: str, final_answer: str) -> str:
        return f"用户询问：{user_query}。本轮回答要点：{final_answer[:80]}。"


def build_agent(settings: AgentSettings):
    use_offline = not bool(settings.openai_api_key.strip())

    if settings.embedding_backend != "bge-m3":
        raise ValueError(
            f"Unsupported embedding backend: {settings.embedding_backend}. "
            "Only `bge-m3` is currently implemented."
        )

    embeddings = BGEM3Embeddings(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
        use_fp16=settings.embedding_use_fp16,
        batch_size=settings.embedding_batch_size,
    )

    if use_offline:
        offline = OfflineRuntime(top_k=settings.top_k)
        llm = None
    else:
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.temperature,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or None,
        )
        offline = None

    knowledge_store = build_vector_store(
        settings.kb_path,
        embeddings,
        backend=settings.vector_store_backend,
        index_dir=settings.vector_store_path,
    )
    memory_store = ConversationMemory(
        path=settings.memory_path,
        vector_store=InMemoryVectorStore(embeddings),
    )
    reranker = None
    if settings.reranker_enabled:
        reranker = BGEReranker(
            model_name=settings.reranker_model_name,
            device=settings.reranker_device,
            use_fp16=settings.reranker_use_fp16,
            batch_size=settings.reranker_batch_size,
        )
    tools = build_default_tools()
    tools_by_name = {tool.name: tool for tool in tools}

    def recall_memory(state: AgentState) -> AgentState:
        memories = memory_store.recall(
            session_id=state["session_id"],
            query=state["user_query"],
        )
        return {"recalled_memories": memories}

    def rewrite_query(state: AgentState) -> AgentState:
        if use_offline:
            result = offline.rewrite(state["user_query"], state.get("recalled_memories", []))
        else:
            response = llm.invoke(
                [
                    SystemMessage(content=REWRITE_PROMPT),
                    HumanMessage(
                        content=(
                            f"当前问题：{state['user_query']}\n"
                            f"相关记忆：\n{format_memories(state.get('recalled_memories', []))}\n"
                            "请只输出 JSON，字段为 rewritten_query 和 rationale。"
                        )
                    ),
                ]
            )
            result = _parse_json_model(response.content, RewriteResult)
        return {
            "rewritten_query": result.rewritten_query,
            "rewrite_reason": result.rationale,
        }

    def detect_intent(state: AgentState) -> AgentState:
        if use_offline:
            result = offline.intent(
                state["user_query"],
                state.get("rewritten_query", state["user_query"]),
            )
        else:
            response = llm.invoke(
                [
                    SystemMessage(content=INTENT_PROMPT),
                    HumanMessage(
                        content=(
                            f"用户问题：{state['user_query']}\n"
                            f"改写问题：{state.get('rewritten_query', state['user_query'])}\n"
                            "请只输出 JSON，字段为 intent、needs_retrieval、needs_tools、tool_names、reason。"
                        )
                    ),
                ]
            )
            result = _parse_json_model(response.content, IntentResult)
        return {
            "intent": result.intent,
            "intent_reason": result.reason,
            "needs_retrieval": result.needs_retrieval,
            "needs_tools": result.needs_tools,
            "requested_tools": result.tool_names,
        }

    def retrieve_docs(state: AgentState) -> AgentState:
        if not state.get("needs_retrieval", True):
            return {"retrieved_docs": []}

        docs = knowledge_store.similarity_search(
            state.get("rewritten_query", state["user_query"]),
            k=max(settings.top_k, settings.retrieval_fetch_k),
        )
        results: list[dict[str, Any]] = [
            {
                "content": doc.page_content,
                "title": doc.metadata.get("title", "unknown"),
                "department": doc.metadata.get("department", ""),
                "source": doc.metadata.get("source", ""),
            }
            for doc in docs
        ]
        if reranker is not None:
            results = reranker.rerank(
                query=state.get("rewritten_query", state["user_query"]),
                docs=results,
                top_k=settings.top_k,
            )
        else:
            results = results[: settings.top_k]
        return {"retrieved_docs": results}

    def invoke_tools(state: AgentState) -> AgentState:
        if not state.get("needs_tools", False):
            return {"tool_outputs": []}

        if use_offline:
            tool_outputs: list[dict[str, Any]] = []
            for tool_name in state.get("requested_tools", []):
                tool = tools_by_name.get(tool_name)
                if not tool:
                    continue
                if tool_name == "current_time":
                    output = tool.invoke({})
                else:
                    output = tool.invoke(
                        {
                            "issue": state.get("rewritten_query", state["user_query"]),
                            "priority": "normal",
                        }
                    )
                tool_outputs.append(
                    {"tool_name": tool_name, "args": {}, "output": output}
                )
            return {"tool_outputs": tool_outputs}

        tool_outputs: list[dict[str, Any]] = []
        for tool_name in state.get("requested_tools", []):
            tool = tools_by_name.get(tool_name)
            if not tool:
                continue
            if tool_name == "current_time":
                output = tool.invoke({})
            else:
                output = tool.invoke(
                    {
                        "issue": state.get("rewritten_query", state["user_query"]),
                        "priority": "normal",
                    }
                )
            tool_outputs.append(
                {
                    "tool_name": tool_name,
                    "args": {},
                    "output": output,
                }
            )
        return {"tool_outputs": tool_outputs}

    def summarize(state: AgentState) -> AgentState:
        retrieval_context = _format_docs(state.get("retrieved_docs", []))
        tool_context = _format_tool_outputs(state.get("tool_outputs", []))
        memory_context = format_memories(state.get("recalled_memories", []))

        if use_offline:
            answer_text = offline.answer(
                user_query=state["user_query"],
                rewritten_query=state.get("rewritten_query", state["user_query"]),
                intent=state.get("intent", "qa"),
                retrieval_context=retrieval_context,
                tool_context=tool_context,
                memory_context=memory_context,
            )
        else:
            answer = llm.invoke(
                [
                    SystemMessage(
                        content=ANSWER_PROMPT.format(
                            user_query=state["user_query"],
                            rewritten_query=state.get("rewritten_query", state["user_query"]),
                            intent=state.get("intent", "qa"),
                            retrieval_context=retrieval_context,
                            tool_context=tool_context,
                            memory_context=memory_context,
                        )
                    )
                ]
            )
            answer_text = answer.content

        return {
            "answer_summary": answer_text,
            "final_answer": answer_text,
        }

    def reflect(state: AgentState) -> AgentState:
        if use_offline:
            review = offline.reflect(
                user_query=state["user_query"],
                final_answer=state["final_answer"],
                retrieved_docs=state.get("retrieved_docs", []),
                tool_outputs=state.get("tool_outputs", []),
            )
        else:
            response = llm.invoke(
                [
                    SystemMessage(content=REFLECTION_PROMPT),
                    HumanMessage(
                        content=(
                            f"问题：{state['user_query']}\n"
                            f"回答：{state['final_answer']}\n"
                            f"召回内容：\n{_format_docs(state.get('retrieved_docs', []))}\n"
                            f"工具结果：\n{_format_tool_outputs(state.get('tool_outputs', []))}\n"
                            "请只输出 JSON，字段为 confidence、issues、needs_follow_up、follow_up_question。"
                        )
                    ),
                ]
            )
            review = _parse_json_model(response.content, ReflectionResult)

        final_answer = state["final_answer"]
        if review.needs_follow_up and review.follow_up_question:
            final_answer = f"{final_answer}\n\n补充确认：{review.follow_up_question}"

        return {
            "reflection": review.model_dump(),
            "final_answer": final_answer,
        }

    def write_memory(state: AgentState) -> AgentState:
        if use_offline:
            memory_text = offline.memory_summary(
                user_query=state["user_query"],
                final_answer=state["final_answer"],
            )
        else:
            memory_summary = llm.invoke(
                [
                    SystemMessage(content=MEMORY_PROMPT),
                    HumanMessage(
                        content=(
                            f"用户问题：{state['user_query']}\n"
                            f"最终回答：{state['final_answer']}\n"
                            "请只输出一到两句中文摘要，不要加其它说明。"
                        )
                    ),
                ]
            )
            memory_text = memory_summary.content

        memory_store.remember(
            MemoryRecord(
                session_id=state["session_id"],
                summary=memory_text,
                source_query=state["user_query"],
                final_answer=state["final_answer"],
                metadata={
                    "intent": state.get("intent", "qa"),
                    "confidence": state.get("reflection", {}).get("confidence", "unknown"),
                },
            )
        )
        return {}

    graph = StateGraph(AgentState)
    graph.add_node("recall_memory", recall_memory)
    graph.add_node("rewrite_query", rewrite_query)
    graph.add_node("detect_intent", detect_intent)
    graph.add_node("retrieve_docs", retrieve_docs)
    graph.add_node("invoke_tools", invoke_tools)
    graph.add_node("summarize", summarize)
    graph.add_node("reflect", reflect)
    graph.add_node("write_memory", write_memory)

    graph.add_edge(START, "recall_memory")
    graph.add_edge("recall_memory", "rewrite_query")
    graph.add_edge("rewrite_query", "detect_intent")
    graph.add_edge("detect_intent", "retrieve_docs")
    graph.add_edge("retrieve_docs", "invoke_tools")
    graph.add_edge("invoke_tools", "summarize")
    graph.add_edge("summarize", "reflect")
    graph.add_edge("reflect", "write_memory")
    graph.add_edge("write_memory", END)

    return graph.compile()

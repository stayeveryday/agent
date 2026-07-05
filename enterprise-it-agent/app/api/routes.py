from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.audit.log import get_audit_event, list_audit_events
from app.chains.basic_chat import ask, inspect_chain
from app.chains.chat_model import ask_model
from app.chains.intent_classifier import classify_intent
from app.demo.acceptance import run_acceptance
from app.demo.scenarios import get_demo_scenarios_doc
from app.evals.dataset import preview_eval_dataset
from app.evals.runner import run_evaluations
from app.graph.checkpoints import approve_checkpoint, create_checkpoint, reject_checkpoint
from app.prompts.it_support import get_it_support_prompt
from app.graph.state import build_initial_state, describe_agent_state
from app.graph.workflow import describe_minimal_graph, run_minimal_graph
from app.memory.store import clear_session_memory, get_session_memory
from app.observability.tracing import get_trace, list_traces
from app.rag.answer import answer_with_rag
from app.rag.ingest import ingest_knowledge_base
from app.rag.preview import preview_chunks
from app.rag.retriever import search_knowledge_base
from app.schemas.chat import (
    ChainDebugResponse,
    ChatRequest,
    ChatResponse,
    ModelChatResponse,
    PromptPreviewResponse,
)
from app.schemas.demo import DemoAcceptanceRequest, DemoAcceptanceResponse, DemoScenariosResponse
from app.schemas.evals import (
    EvalDatasetPreviewRequest,
    EvalDatasetPreviewResponse,
    EvalRunRequest,
    EvalRunResponse,
)
from app.schemas.graph import (
    AgentStateDescriptionResponse,
    AgentStatePreviewRequest,
    AgentStatePreviewResponse,
)
from app.schemas.intent import IntentResult
from app.schemas.memory import SessionMemoryClearResponse, SessionMemoryResponse
from app.schemas.rag import (
    RagAnswerRequest,
    RagAnswerResponse,
    RagIngestResponse,
    RagPreviewRequest,
    RagPreviewResponse,
    RagSearchRequest,
    RagSearchResponse,
)
from app.schemas.tools import ToolListResponse, ToolRunRequest, ToolRunResponse
from app.schemas.tracing import TraceListResponse, TraceResponse
from app.schemas.audit import AuditEventResponse, AuditListResponse
from app.schemas.workflow import (
    GraphApprovalRequest,
    GraphApprovalResponse,
    GraphDescriptionResponse,
    GraphRunRequest,
    GraphRunResponse,
)
from app.streaming.sse import stream_graph_run
from app.tools.executor import run_tool
from app.tools.registry import list_tool_summaries

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/demo/scenarios", response_model=DemoScenariosResponse)
def demo_scenarios() -> DemoScenariosResponse:
    return DemoScenariosResponse(**get_demo_scenarios_doc())


@router.post("/demo/acceptance", response_model=DemoAcceptanceResponse)
def demo_acceptance(req: DemoAcceptanceRequest) -> DemoAcceptanceResponse:
    try:
        result = run_acceptance(include_slow=req.include_slow, write_report=req.write_report)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Acceptance run failed: {exc}") from exc
    return DemoAcceptanceResponse(**result)


@router.post("/evals/dataset", response_model=EvalDatasetPreviewResponse)
def eval_dataset_preview(req: EvalDatasetPreviewRequest) -> EvalDatasetPreviewResponse:
    try:
        result = preview_eval_dataset(limit=req.limit)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return EvalDatasetPreviewResponse(**result)


@router.post("/evals/run", response_model=EvalRunResponse)
def eval_run(req: EvalRunRequest) -> EvalRunResponse:
    try:
        result = run_evaluations(limit=req.limit, category=req.category)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Eval run failed: {exc}") from exc
    return EvalRunResponse(**result)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        answer = ask(req.question, style=req.style)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model invocation failed: {exc}") from exc

    return ChatResponse(answer=answer)


@router.post("/model-chat", response_model=ModelChatResponse)
def model_chat(req: ChatRequest) -> ModelChatResponse:
    try:
        answer = ask_model(req.question)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model invocation failed: {exc}") from exc

    return ModelChatResponse(answer=answer)


@router.post("/prompt-preview", response_model=PromptPreviewResponse)
def prompt_preview(req: ChatRequest) -> PromptPreviewResponse:
    prompt_value = get_it_support_prompt(style=req.style).invoke({"question": req.question})
    messages = [
        {"type": message.type, "content": str(message.content)}
        for message in prompt_value.messages
    ]
    return PromptPreviewResponse(messages=messages)


@router.post("/chain-debug", response_model=ChainDebugResponse)
def chain_debug(req: ChatRequest) -> ChainDebugResponse:
    try:
        details = inspect_chain(req.question, style=req.style)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model invocation failed: {exc}") from exc

    return ChainDebugResponse(**details)


@router.post("/intent", response_model=IntentResult)
def intent(req: ChatRequest) -> IntentResult:
    try:
        result = classify_intent(req.question)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model invocation failed: {exc}") from exc

    return result


@router.get("/rag/preview", response_model=RagPreviewResponse)
def rag_preview() -> RagPreviewResponse:
    return RagPreviewResponse(**preview_chunks())


@router.post("/rag/preview-tuned", response_model=RagPreviewResponse)
def rag_preview_tuned(req: RagPreviewRequest) -> RagPreviewResponse:
    return RagPreviewResponse(
        **preview_chunks(
            limit=req.limit,
            chunk_size=req.chunk_size,
            chunk_overlap=req.chunk_overlap,
        )
    )


@router.post("/rag/ingest", response_model=RagIngestResponse)
def rag_ingest(req: RagPreviewRequest) -> RagIngestResponse:
    return RagIngestResponse(
        **ingest_knowledge_base(
            chunk_size=req.chunk_size,
            chunk_overlap=req.chunk_overlap,
        )
    )


@router.post("/rag/search", response_model=RagSearchResponse)
def rag_search(req: RagSearchRequest) -> RagSearchResponse:
    return RagSearchResponse(
        **search_knowledge_base(
            query=req.query,
            top_k=req.top_k,
            fetch_k=req.fetch_k,
            department=req.department,
            access_level=req.access_level,
        )
    )


@router.post("/rag/answer", response_model=RagAnswerResponse)
def rag_answer(req: RagAnswerRequest) -> RagAnswerResponse:
    try:
        result = answer_with_rag(
            question=req.question,
            top_k=req.top_k,
            fetch_k=req.fetch_k,
            department=req.department,
            access_level=req.access_level,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model invocation failed: {exc}") from exc

    return RagAnswerResponse(**result)


@router.get("/tools", response_model=ToolListResponse)
def list_tools() -> ToolListResponse:
    return ToolListResponse(tools=list_tool_summaries())


@router.post("/tools/run", response_model=ToolRunResponse)
def execute_tool(req: ToolRunRequest) -> ToolRunResponse:
    try:
        result = run_tool(tool_name=req.tool_name, arguments=req.arguments)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Tool execution failed: {exc}") from exc
    return ToolRunResponse(**result)


@router.get("/graph/state", response_model=AgentStateDescriptionResponse)
def graph_state_description() -> AgentStateDescriptionResponse:
    return AgentStateDescriptionResponse(**describe_agent_state())


@router.post("/graph/state/preview", response_model=AgentStatePreviewResponse)
def graph_state_preview(req: AgentStatePreviewRequest) -> AgentStatePreviewResponse:
    return AgentStatePreviewResponse(
        state=build_initial_state(
            user_query=req.user_query,
            department=req.department,
            access_level=req.access_level,
        )
    )


@router.get("/graph/workflow", response_model=GraphDescriptionResponse)
def graph_workflow_description() -> GraphDescriptionResponse:
    return GraphDescriptionResponse(**describe_minimal_graph())


@router.post("/graph/run", response_model=GraphRunResponse)
def graph_run(req: GraphRunRequest) -> GraphRunResponse:
    try:
        state = run_minimal_graph(
            user_query=req.user_query,
            session_id=req.session_id,
            department=req.department,
            access_level=req.access_level,
            approved=req.approved,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Graph execution failed: {exc}") from exc
    if state.get("approval_status") == "pending":
        checkpoint_id = create_checkpoint(state)
        state["approval_checkpoint_id"] = checkpoint_id
    return GraphRunResponse(state=dict(state))


@router.post("/graph/stream")
def graph_stream(req: GraphRunRequest) -> StreamingResponse:
    return StreamingResponse(
        stream_graph_run(
            user_query=req.user_query,
            session_id=req.session_id,
            department=req.department,
            access_level=req.access_level,
            approved=req.approved,
        ),
        media_type="text/event-stream",
    )


@router.post("/graph/approvals/{checkpoint_id}/approve", response_model=GraphApprovalResponse)
def graph_approval_approve(checkpoint_id: str) -> GraphApprovalResponse:
    try:
        state = approve_checkpoint(checkpoint_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Approval resume failed: {exc}") from exc
    return GraphApprovalResponse(checkpoint_id=checkpoint_id, state=dict(state))


@router.get("/memory/{session_id}", response_model=SessionMemoryResponse)
def memory_get(session_id: str) -> SessionMemoryResponse:
    return SessionMemoryResponse(session=get_session_memory(session_id))


@router.delete("/memory/{session_id}", response_model=SessionMemoryClearResponse)
def memory_clear(session_id: str) -> SessionMemoryClearResponse:
    return SessionMemoryClearResponse(
        session_id=session_id,
        cleared=clear_session_memory(session_id),
    )


@router.get("/traces", response_model=TraceListResponse)
def traces_list() -> TraceListResponse:
    return TraceListResponse(traces=list_traces())


@router.get("/traces/{trace_id}", response_model=TraceResponse)
def trace_get(trace_id: str) -> TraceResponse:
    trace = get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace not found: {trace_id}")
    return TraceResponse(trace=trace)


@router.get("/audit/events", response_model=AuditListResponse)
def audit_events_list() -> AuditListResponse:
    return AuditListResponse(events=list_audit_events())


@router.get("/audit/events/{audit_id}", response_model=AuditEventResponse)
def audit_event_get(audit_id: str) -> AuditEventResponse:
    event = get_audit_event(audit_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Audit event not found: {audit_id}")
    return AuditEventResponse(event=event)


@router.post("/graph/approvals/{checkpoint_id}/reject", response_model=GraphApprovalResponse)
def graph_approval_reject(
    checkpoint_id: str,
    req: GraphApprovalRequest,
) -> GraphApprovalResponse:
    try:
        state = reject_checkpoint(checkpoint_id, reason=req.reason)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Approval rejection failed: {exc}") from exc
    return GraphApprovalResponse(checkpoint_id=checkpoint_id, state=dict(state))

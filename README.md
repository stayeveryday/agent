# 企业 RAG Agent（LangChain）

这是一个从零搭建的最小可运行版本，覆盖了企业 RAG 常见的 7 个能力：

1. Query 改写
2. 意图识别
3. 向量召回
4. 工具调用
5. 总结生成
6. 反思校验
7. 会话记忆

## 架构说明

整体使用 `LangGraph` 串起多节点流程：

```text
用户问题
  -> 记忆召回
  -> Query 改写
  -> 意图识别
  -> 知识库召回
  -> 工具调用
  -> 总结回答
  -> 反思校验
  -> 写入记忆
```

当前实现默认使用：

- `ChatOpenAI` 作为大模型
- DeepSeek 兼容接口作为默认在线模型端点
- 本地哈希 embedding 作为召回向量表示
- `InMemoryVectorStore` 作为最小示例向量库
- 本地 `JSONL` 文件作为长期记忆持久化

这样便于先跑通，再替换成企业内部能力，比如：

- 向量库：Milvus / PGVector / Elasticsearch / Weaviate
- 工具：工单系统、组织架构、CRM、ERP、审批系统
- 记忆：Redis / Postgres / 专用 Memory Store
- 权限：按部门、角色、租户做检索过滤

## 目录结构

```text
src/enterprise_rag_agent/
  agent.py          # LangGraph 主流程
  config.py         # 配置与运行时装配
  memory.py         # 短期/长期记忆
  prompts.py        # Prompt 模板
  schemas.py        # 状态与结构化输出
  tools.py          # 默认示例工具
  vectorstore.py    # 示例知识库装载与检索
demo.py             # 本地运行入口
data/sample_kb.json # 示例企业知识库
```

## 安装

```bash
pip install -e .
```

设置环境变量：

```bash
set OPENAI_API_KEY=your_key
set OPENAI_BASE_URL=https://api.deepseek.com
set OPENAI_MODEL=deepseek-chat
```

可选：

```bash
set ENTERPRISE_AGENT_MEMORY_PATH=data\memory.jsonl
set ENTERPRISE_AGENT_KB_PATH=data\sample_kb.json
```

说明：

- `OPENAI_API_KEY` 这里填 DeepSeek 的 key
- 当前版本的召回层使用本地哈希 embedding，不再依赖外部 embedding API
- 如果 `OPENAI_API_KEY` 为空，程序会自动进入离线演示模式

## 运行

```bash
python demo.py
```

## 改造建议

这个版本已经把企业化扩展点分开了，推荐下一步按下面顺序升级：

1. 把 `sample_kb.json` 替换为企业知识文档切片产物
2. 把 `InMemoryVectorStore` 换成正式向量库
3. 在召回前后加权限过滤
4. 将 `tools.py` 接到真实企业系统 API
5. 将 `memory.py` 替换为 Redis / Postgres 持久层
6. 给反思节点增加低置信度重试或人工兜底

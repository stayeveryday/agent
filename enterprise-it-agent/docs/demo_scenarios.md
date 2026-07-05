# Demo Scenarios

These scenarios are the Day 28 end-to-end demo checklist for the Enterprise IT Agent.

## 1. Health Check

Endpoint:

```text
GET /health
```

Expected:

```text
{"status":"ok"}
```

## 2. Knowledge RAG

Endpoint:

```text
POST /graph/run
```

Body:

```json
{
  "session_id": "demo-rag-001",
  "user_query": "How do I reset my company email login?"
}
```

Expected:

```text
intent = knowledge_question
route_name = rag
retrieved_docs has at least one item
rag_sources includes email_login_reset.md
```

## 3. Permission-Scoped RAG

Endpoint:

```text
POST /graph/run
```

Body:

```json
{
  "session_id": "demo-rag-002",
  "user_query": "What information is needed for asset lookup?",
  "access_level": "restricted"
}
```

Expected:

```text
route_name = rag
rag_sources includes asset_lookup_policy.md
```

## 4. Ticket Status Tool

Endpoint:

```text
POST /graph/run
```

Body:

```json
{
  "session_id": "demo-tool-001",
  "user_query": "Please check ticket INC-1001 status."
}
```

Expected:

```text
route_name = tool
tool_name = get_ticket_status
tool_arguments.ticket_id = INC-1001
```

## 5. Asset Lookup Tool

Endpoint:

```text
POST /graph/run
```

Body:

```json
{
  "session_id": "demo-tool-002",
  "user_query": "Please look up asset for employee u10018."
}
```

Expected:

```text
route_name = tool
tool_name = lookup_asset
tool_arguments.employee_id = u10018
```

## 6. Ticket Creation Requires Approval

Endpoint:

```text
POST /graph/run
```

Body:

```json
{
  "session_id": "demo-approval-001",
  "user_query": "Please create a high priority network ticket for u10077. Laptop cannot connect to office wifi."
}
```

Expected:

```text
tool_name = create_ticket
approval_status = pending
approval_checkpoint_id is returned
tool_result is empty
```

## 7. Resume After Approval

Endpoint:

```text
POST /graph/approvals/{approval_checkpoint_id}/approve
```

Expected:

```text
approval_status = approved
tool_result contains created ticket
```

## 8. Session Memory Follow-Up

Step 1:

```json
{
  "session_id": "demo-memory-001",
  "user_query": "Please check ticket INC-1001 status."
}
```

Step 2:

```json
{
  "session_id": "demo-memory-001",
  "user_query": "What is its status now?"
}
```

Expected:

```text
second resolved_user_query contains INC-1001
```

## 9. Trace Inspection

Endpoint:

```text
GET /traces/{trace_id}
```

Expected:

```text
events include classify_intent, route_by_intent, route node, final_answer
```

## 10. Audit Inspection

Endpoint:

```text
GET /audit/events
```

Expected:

```text
events include tool_call and approval/checkpoint events after tool demos
```

## 11. Eval Smoke Test

Endpoint:

```text
POST /evals/run
```

Body:

```json
{
  "category": "tool"
}
```

Expected:

```text
failed = 0
```

## 12. SSE Streaming

Endpoint:

```text
POST /graph/stream
```

Expected:

```text
event: start
event: state
event: final
event: done
```


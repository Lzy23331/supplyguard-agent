# Async Task Execution

## Modes

`execution_mode=sync` keeps the original behavior: the API creates a task, runs the full Agent chain, and returns the completed result.

`execution_mode=async` creates a task with `pending` status and returns immediately. A FastAPI `BackgroundTasks` job then runs the same orchestrator in the background.

## Why BackgroundTasks

This batch intentionally avoids Celery, Redis, RabbitMQ, SSE and WebSocket. `BackgroundTasks` is enough for a local MVP: it is simple, has no new infrastructure dependency, and keeps the synchronous Agent chain reusable.

## Status Flow

Normal flow:

```text
pending -> running -> completed
```

Failure flow:

```text
pending -> running -> failed
```

When a background task fails, `diligence_tasks.error_message` stores the failure summary and an `AsyncTaskService` event is written.

## Frontend Polling

The task detail page polls every 2 seconds while status is `pending` or `running`:

```text
GET /api/diligence/tasks/{task_id}
GET /api/diligence/tasks/{task_id}/events
```

When status becomes `completed`, polling stops and the page loads evidence and report content. When status becomes `failed`, polling stops and the error message remains visible with the partial AgentTimeline.

## LLM Compatibility

Async mode does not change the first-batch LLM boundaries. `IntakeAgent` can still generate a diligence plan, `RAGPolicyTool` can still rewrite policy queries, and `llm_call_logs` records mock, real and fallback calls.

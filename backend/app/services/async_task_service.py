from typing import Any

from app.agents.orchestrator import Orchestrator
from app.database import init_db
from app.repositories import add_event, get_task, update_task


def _supplier_from_task(task: dict[str, Any]) -> dict[str, Any]:
    supplier = dict(task["supplier"])
    supplier.setdefault("id", task["supplier"]["id"])
    supplier["material_text"] = task.get("material_text")
    supplier["upload_ids"] = task.get("upload_ids") or []
    supplier["query_type"] = task.get("query_type")
    supplier["company_name"] = task.get("company_name") or supplier.get("name")
    return supplier


def run_diligence_task_background(task_id: str) -> None:
    init_db()
    task = get_task(task_id)
    if not task:
        return
    try:
        update_task(task_id, status="running", error_message=None)
        Orchestrator().run(task_id, _supplier_from_task(task))
        update_task(task_id, status="completed", error_message=None)
    except Exception as exc:  # pragma: no cover - exercised through route-level tests
        message = str(exc)
        update_task(task_id, status="failed", error_message=message, summary=message)
        add_event(
            task_id,
            "AsyncTaskService",
            "task_failed",
            "failed",
            f"后台尽调任务执行失败：{message}",
        )

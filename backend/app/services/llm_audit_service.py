import logging

from app.database import get_db
from app.repositories import now_iso

logger = logging.getLogger(__name__)


def _truncate(value: str | None, limit: int = 1000) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if len(text) <= limit else f"{text[:limit]}..."


def log_llm_call(
    db,
    task_id: str | None,
    agent_name: str,
    llm_task_type: str,
    model_mode: str,
    model_name: str | None,
    prompt_name: str,
    input_summary: str,
    output_summary: str | None,
    success: bool,
    fallback_used: bool = False,
    fallback_reason: str | None = None,
    error_message: str | None = None,
    latency_ms: int | None = None,
) -> None:
    try:
        if db is not None and hasattr(db, "execute"):
            conn = db
            conn.execute(
                """
                INSERT INTO llm_call_logs
                (task_id, agent_name, llm_task_type, model_mode, model_name, prompt_name,
                 input_summary, output_summary, success, fallback_used, fallback_reason,
                 error_message, latency_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    agent_name,
                    llm_task_type,
                    model_mode,
                    model_name,
                    prompt_name,
                    _truncate(input_summary),
                    _truncate(output_summary),
                    1 if success else 0,
                    1 if fallback_used else 0,
                    _truncate(fallback_reason, 500),
                    _truncate(error_message, 1000),
                    latency_ms,
                    now_iso(),
                ),
            )
            return
        conn_ctx = db if db is not None else get_db()
        with conn_ctx as conn:
            conn.execute(
                """
                INSERT INTO llm_call_logs
                (task_id, agent_name, llm_task_type, model_mode, model_name, prompt_name,
                 input_summary, output_summary, success, fallback_used, fallback_reason,
                 error_message, latency_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    agent_name,
                    llm_task_type,
                    model_mode,
                    model_name,
                    prompt_name,
                    _truncate(input_summary),
                    _truncate(output_summary),
                    1 if success else 0,
                    1 if fallback_used else 0,
                    _truncate(fallback_reason, 500),
                    _truncate(error_message, 1000),
                    latency_ms,
                    now_iso(),
                ),
            )
    except Exception as exc:  # pragma: no cover - audit must never break flow
        logger.warning("Failed to write llm_call_logs: %s", exc)

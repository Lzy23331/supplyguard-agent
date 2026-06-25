from app.database import get_db, init_db
from app.services.task_service import TaskService


def test_intake_agent_writes_llm_plan_event(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "mock")
    init_db()

    task = TaskService().create_task_from_sample("low")

    with get_db() as conn:
        event = conn.execute(
            """
            SELECT * FROM agent_events
            WHERE task_id=? AND agent_name='IntakeAgent' AND summary LIKE '%结构化尽调计划%'
            ORDER BY id DESC LIMIT 1
            """,
            (task["id"],),
        ).fetchone()
    assert event is not None
    assert event["tool_name"] == "LLMTaskService.generate_intake_plan"


def test_llm_call_logs_success_record_is_written(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "mock")
    init_db()

    task = TaskService().create_task_from_sample("medium")

    with get_db() as conn:
        row = conn.execute(
            "SELECT success, llm_task_type FROM llm_call_logs WHERE task_id=? AND llm_task_type='intake_plan' ORDER BY id DESC LIMIT 1",
            (task["id"],),
        ).fetchone()
    assert row is not None
    assert row["success"] == 1

from app.database import get_db, init_db
from app.repositories import create_task_record, get_task
from app.schemas import SupplierCreate
from app.services.async_task_service import run_diligence_task_background


def test_background_task_completes_and_writes_events():
    init_db()
    supplier = SupplierCreate(
        name="Async Unit Supplier",
        industry="包装材料",
        region="上海",
        annual_spend=120000,
        cooperation_type="标准采购",
    )
    task_id = create_task_record(supplier)

    run_diligence_task_background(task_id)

    task = get_task(task_id)
    assert task is not None
    assert task["status"] == "completed"
    assert task["risk_level"] in {"low", "medium", "high"}
    with get_db() as conn:
        events = conn.execute("SELECT * FROM agent_events WHERE task_id=? ORDER BY id", (task_id,)).fetchall()
    assert events


def test_background_task_failure_sets_failed(monkeypatch):
    init_db()
    supplier = SupplierCreate(name="Broken Async Supplier", annual_spend=1000)
    task_id = create_task_record(supplier)

    def fail_run(self, task_id, supplier):
        raise RuntimeError("forced async failure")

    monkeypatch.setattr("app.services.async_task_service.Orchestrator.run", fail_run)

    run_diligence_task_background(task_id)

    task = get_task(task_id)
    assert task is not None
    assert task["status"] == "failed"
    assert "forced async failure" in task["error_message"]
    with get_db() as conn:
        event = conn.execute(
            "SELECT * FROM agent_events WHERE task_id=? AND agent_name='AsyncTaskService' ORDER BY id DESC LIMIT 1",
            (task_id,),
        ).fetchone()
    assert event is not None
    assert event["status"] == "failed"

from app.agents.base import AgentContext
from app.agents.material_analysis_agent import MaterialAnalysisAgent
from app.database import get_db, init_db
from app.repositories import create_task_record, list_evidence
from app.schemas import SupplierCreate


def test_material_analysis_agent_saves_user_input_evidence(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "mock")
    init_db()
    supplier = SupplierCreate(name="Material Demo", annual_spend=1000)
    task_id = create_task_record(supplier, material_text="供应商存在交付延期和付款纠纷。")
    context = AgentContext(
        task_id=task_id,
        supplier={"name": "Material Demo", "material_text": "供应商存在交付延期和付款纠纷。"},
        evidence=[],
    )

    result = MaterialAnalysisAgent().run(context)

    assert len(result["evidence"]) >= 2
    saved = list_evidence(task_id)
    assert any(item["source_type"] == "user_input" for item in saved)
    with get_db() as conn:
        event = conn.execute(
            "SELECT * FROM agent_events WHERE task_id=? AND agent_name='MaterialAnalysisAgent' ORDER BY id DESC LIMIT 1",
            (task_id,),
        ).fetchone()
    assert event is not None


def test_material_analysis_agent_skips_empty_material():
    init_db()
    supplier = SupplierCreate(name="No Material Demo", annual_spend=1000)
    task_id = create_task_record(supplier)
    context = AgentContext(task_id=task_id, supplier={"name": "No Material Demo"}, evidence=[])

    result = MaterialAnalysisAgent().run(context)

    assert result["evidence"] == []

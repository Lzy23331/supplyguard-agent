from fastapi.testclient import TestClient

from app.main import app
from app.services.task_service import TaskService
from app.tools.risk_rules import RiskRuleTool

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_empty_material_keeps_sample_risk_levels():
    service = TaskService()
    assert service.create_task_from_sample("supplier_low_001")["risk_level"] == "low"
    assert service.create_task_from_sample("supplier_medium_001")["risk_level"] == "medium"
    assert service.create_task_from_sample("supplier_high_001")["risk_level"] == "high"


def test_sync_material_text_generates_user_input_evidence():
    task = unwrap(
        client.post(
            "/api/diligence/tasks",
            json={
                "supplier_id": "supplier_low_001",
                "execution_mode": "sync",
                "material_text": "该供应商过去一年存在交付延期、付款纠纷和合同争议。",
            },
        )
    )

    evidence = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/evidence"))
    assert any(item["source_type"] == "user_input" for item in evidence)
    assert any("交付延期" in item.get("risk_keywords", []) for item in evidence)
    events = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/events"))
    assert any(event["agent_name"] == "MaterialAnalysisAgent" for event in events)


def test_async_material_text_flow_completes():
    task = unwrap(
        client.post(
            "/api/diligence/tasks",
            json={
                "supplier_id": "supplier_low_001",
                "execution_mode": "async",
                "material_text": "用户材料提到供应商存在资料缺失。",
            },
        )
    )

    detail = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}"))
    assert detail["status"] in {"running", "completed"}
    evidence = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/evidence"))
    assert any(item["source_type"] == "user_input" for item in evidence)


def test_should_use_for_scoring_false_is_ignored():
    risk = RiskRuleTool().assess(
        [
            {
                "title": "低置信度用户材料",
                "content": "交付延期",
                "severity": "warning",
                "rule_signals": ["multiple_late_delivery"],
                "metadata_json": {"should_use_for_scoring": False},
            }
        ],
        {"name": "Complete Supplier", "website": "https://example.com", "region": "上海", "industry": "制造", "cooperation_type": "标准采购", "annual_spend": 0},
    )

    assert risk["total_score"] == 0


def test_risk_keyword_normalization_scores_user_input_synonyms():
    risk = RiskRuleTool().assess(
        [
            {
                "title": "用户材料显示延期交付",
                "content": "供应商多次延期交付并出现付款争议。",
                "severity": "warning",
                "source_type": "user_input",
                "risk_keywords": ["延期交付", "付款争议"],
                "confidence": 0.8,
            }
        ],
        {"name": "Complete Supplier", "website": "https://example.com", "region": "上海", "industry": "制造", "cooperation_type": "标准采购", "annual_spend": 0},
    )

    assert risk["total_score"] >= 20
    assert any(rule["rule_id"] in {"multiple_late_delivery", "multiple_payment_disputes"} for rule in risk["triggered_rules"])

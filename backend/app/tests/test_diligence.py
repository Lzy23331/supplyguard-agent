import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app
from app.services.samples import list_sample_suppliers
from app.tools.mock_search import MockSearchTool
from app.tools.rag_policy import RAGPolicyTool
from app.tools.risk_rules import RiskRuleTool


client = TestClient(app)


def test_create_task_and_events_report():
    init_db()
    sample = next(item for item in list_sample_suppliers() if item["sample_key"] == "low")
    response = client.post("/api/diligence/tasks", json={"supplier": sample})
    assert response.status_code == 200
    task = response.json()
    assert task["status"] == "completed"
    assert task["risk_level"] == "low"
    assert task["total_score"] < 40

    events = client.get(f"/api/diligence/tasks/{task['id']}/events").json()
    assert len(events) >= 10
    assert any(event["agent_name"] == "ReportAgent" for event in events)
    assert any("开始执行" in event["summary"] for event in events)

    report = client.get(f"/api/diligence/tasks/{task['id']}/report").json()["markdown"]
    assert "风险等级" in report
    assert "证据链" in report
    assert "准入建议" in report


def test_sample_suppliers_generate_different_risk_levels():
    expected = {"low": "low", "medium": "medium", "high": "high"}
    for sample in list_sample_suppliers():
        response = client.post("/api/diligence/tasks", json={"supplier": sample})
        assert response.status_code == 200
        task = response.json()
        assert task["risk_level"] == expected[sample["sample_key"]]
        if sample["sample_key"] == "medium":
            assert 45 <= task["total_score"] <= 55
        if sample["sample_key"] == "high":
            assert task["total_score"] == 100


def test_mock_search_returns_structured_economic_evidence():
    sample = next(item for item in list_sample_suppliers() if item["sample_key"] == "high")
    evidence = MockSearchTool().search(sample)
    assert evidence
    assert any("rule_signals" in item for item in evidence)
    assert any("economic_rationale" in item for item in evidence)


def test_rag_policy_tool_retrieves_rules():
    matches = RAGPolicyTool().retrieve("sanctions bribery high risk 制裁 黑名单 高风险")
    assert matches
    assert any("制裁" in match["chunk"] or "sanction" in match["chunk"].lower() for match in matches)


def test_risk_rule_tool_hits_high_risk():
    risk = RiskRuleTool().assess(
        [
            {
                "title": "Sanction alert",
                "content": "beneficial owner sanction and bribery risk",
                "severity": "critical",
                "rule_signals": ["sanction_or_blacklist", "bribery_or_fraud"],
                "economic_rationale": "Regulatory and payment-blocking exposure is severe.",
            }
        ],
        {"annual_spend": 2000000, "procurement_amount": 2000000},
    )
    assert risk["risk_level"] == "high"
    assert risk["raw_score"] >= risk["total_score"]
    assert risk["total_score"] >= 70
    assert all({"rule", "dimension", "points", "evidence_source"}.issubset(item) for item in risk["hit_rules"])


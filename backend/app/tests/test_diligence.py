import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app
from app.services.samples import list_sample_suppliers
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
    assert task["risk_level"] == "Low"
    assert task["total_score"] < 35

    events = client.get(f"/api/diligence/tasks/{task['id']}/events").json()
    assert len(events) >= 10
    assert any(event["agent_name"] == "ReportAgent" for event in events)

    report = client.get(f"/api/diligence/tasks/{task['id']}/report").json()["markdown"]
    assert "Risk level" in report
    assert "Evidence Chain" in report
    assert "Recommendation" in report


def test_sample_suppliers_generate_different_risk_levels():
    expected = {"low": "Low", "medium": "Medium", "high": "High"}
    for sample in list_sample_suppliers():
        response = client.post("/api/diligence/tasks", json={"supplier": sample})
        assert response.status_code == 200
        task = response.json()
        assert task["risk_level"] == expected[sample["sample_key"]]


def test_rag_policy_tool_retrieves_rules():
    matches = RAGPolicyTool().retrieve("sanctions bribery high risk")
    assert matches
    assert any("High risk" in match["chunk"] or "sanctions" in match["chunk"].lower() for match in matches)


def test_risk_rule_tool_hits_high_risk():
    risk = RiskRuleTool().assess(
        [{"title": "Sanction alert", "content": "beneficial owner sanction and bribery risk", "severity": "critical"}],
        {"annual_spend": 2000000},
    )
    assert risk["risk_level"] == "High"


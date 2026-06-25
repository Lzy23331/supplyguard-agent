from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_company_name_query_northbridge_scores_high_and_saves_external_evidence():
    task = unwrap(client.post("/api/diligence/tasks", json={
        "execution_mode": "sync",
        "company_name": "Northbridge Electronics Trading LLC.",
        "procurement_amount": 5000000,
        "cooperation_type": "紧急采购",
    }))

    assert task["status"] == "completed"
    assert task["risk_level"] == "high"
    assert task["total_score"] >= 70

    evidence = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/evidence"))
    source_types = {item.get("source_type") for item in evidence}
    assert "mock_external" in source_types
    assert "internal_record" in source_types

    events = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/events"))
    assert any(event["agent_name"] == "CompanyResolverAgent" for event in events)
    assert any(event["agent_name"] == "EvidenceProviderManager" for event in events)


def test_company_name_query_aster_stays_low():
    task = unwrap(client.post("/api/diligence/tasks", json={
        "execution_mode": "sync",
        "company_name": "Aster Precision Components Co., Ltd.",
        "procurement_amount": 320000,
        "cooperation_type": "常规采购",
    }))

    assert task["status"] == "completed"
    assert task["risk_level"] == "low"

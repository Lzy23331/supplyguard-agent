from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def create_from_sample(supplier_id: str):
    response = client.post(f"/api/diligence/tasks/from-sample/{supplier_id}")
    assert response.status_code == 200
    return unwrap(response)


def test_health_and_samples():
    health = client.get("/health")
    assert health.status_code == 200
    assert unwrap(health)["status"] == "ok"

    samples = unwrap(client.get("/api/samples/suppliers"))
    assert len(samples) == 3
    required = {"id", "sample_key", "name", "industry", "region", "procurement_amount", "cooperation_type", "business_status", "profile_completeness", "ownership_transparency", "urgency", "summary", "tags", "expected_risk_level"}
    assert required.issubset(samples[0])


def test_create_all_sample_tasks_and_read_related_resources():
    low = create_from_sample("supplier_low_001")
    medium = create_from_sample("supplier_medium_001")
    high = create_from_sample("supplier_high_001")

    assert low["risk_level"] == "low"
    assert medium["risk_level"] == "medium"
    assert high["risk_level"] == "high"
    assert high["total_score"] == 100
    assert high["raw_score"] >= 100

    detail = unwrap(client.get(f"/api/diligence/tasks/{high['task_id']}"))
    assert detail["task"]["status"] == "completed"
    assert detail["risk_assessment"]["risk_level"] == "high"
    assert detail["risk_assessment"]["triggered_rules"]

    events = unwrap(client.get(f"/api/diligence/tasks/{high['task_id']}/events"))
    assert events
    assert {"id", "agent_name", "event_type", "status", "summary", "tool_name", "tool_input", "tool_output_summary", "created_at"}.issubset(events[0])

    evidence = unwrap(client.get(f"/api/diligence/tasks/{high['task_id']}/evidence"))
    assert evidence
    assert {"id", "source", "category", "title", "content", "severity", "rule_signals", "economic_rationale", "url", "created_at"}.issubset(evidence[0])

    report = unwrap(client.get(f"/api/diligence/tasks/{high['task_id']}/report"))
    assert report["task_id"] == high["task_id"]
    assert "# 供应商准入尽调报告" in report["markdown_content"]


def test_missing_supplier_returns_404_code():
    response = client.post("/api/diligence/tasks/from-sample/supplier_missing_999")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SUPPLIER_NOT_FOUND"

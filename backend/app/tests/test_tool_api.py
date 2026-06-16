from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def data(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert data(response) == {"status": "ok", "service": "supplyguard-agent"}


def test_tool_endpoints_return_expected_shapes():
    samples = client.get("/api/samples/suppliers")
    assert samples.status_code == 200
    assert len(data(samples)) >= 3

    evidence = client.get("/api/tools/mock-search/supplier_high_001")
    assert evidence.status_code == 200
    evidence_data = data(evidence)
    assert any("sanction_or_blacklist" in item.get("rule_signals", []) for item in evidence_data)

    risk = client.get("/api/tools/risk-assessment/supplier_high_001")
    assert risk.status_code == 200
    risk_data = data(risk)
    assert risk_data["risk_level"] == "high"
    assert risk_data["total_score"] == 100

    policies = client.get("/api/tools/policy-search", params={"query": "制裁名单 黑名单 境外供应商"})
    assert policies.status_code == 200
    policy_data = data(policies)
    assert policy_data[0]["score"] > 0
    assert policy_data[0]["matched_keywords"]

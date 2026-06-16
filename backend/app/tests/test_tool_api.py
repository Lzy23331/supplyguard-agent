from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "supplyguard-agent"}


def test_tool_endpoints_return_expected_shapes():
    samples = client.get("/api/samples/suppliers")
    assert samples.status_code == 200
    assert len(samples.json()) >= 3

    evidence = client.get("/api/tools/mock-search/supplier_high_001")
    assert evidence.status_code == 200
    assert any("sanction_or_blacklist" in item.get("rule_signals", []) for item in evidence.json())

    risk = client.get("/api/tools/risk-assessment/supplier_high_001")
    assert risk.status_code == 200
    assert risk.json()["risk_level"] == "high"
    assert risk.json()["total_score"] == 100

    policies = client.get("/api/tools/policy-search", params={"query": "制裁名单 黑名单 境外供应商"})
    assert policies.status_code == 200
    assert policies.json()[0]["score"] > 0
    assert policies.json()[0]["matched_keywords"]

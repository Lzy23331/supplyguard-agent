from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_real_mode_without_keys_falls_back_to_mock_and_completes(monkeypatch):
    monkeypatch.setenv("PROVIDER_MODE", "real")
    monkeypatch.setenv("PROVIDER_FALLBACK_TO_MOCK", "true")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "real")
    monkeypatch.setenv("COMPANY_INFO_PROVIDER", "real")
    monkeypatch.setenv("SANCTIONS_PROVIDER", "real")
    for key in [
        "SERPAPI_API_KEY",
        "GOOGLE_CSE_API_KEY",
        "GOOGLE_CSE_CX",
        "NEWSAPI_KEY",
        "OPENSANCTIONS_API_KEY",
        "OPENCORPORATES_API_TOKEN",
        "COMPANIES_HOUSE_API_KEY",
        "QCC_API_KEY",
        "TIANYANCHA_TOKEN",
    ]:
        monkeypatch.setenv(key, "")
    monkeypatch.setenv("SANCTIONS_LOCAL_CSV", "data/external/missing_sanctions_for_test.csv")
    get_settings.cache_clear()

    task = unwrap(client.post("/api/diligence/tasks", json={
        "execution_mode": "sync",
        "company_name": "Northbridge Electronics Trading LLC.",
        "procurement_amount": 5000000,
        "cooperation_type": "紧急采购",
    }))

    assert task["status"] == "completed"
    assert task["risk_level"] == "high"
    evidence = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/evidence"))
    assert any(item.get("source_type") == "mock_external" for item in evidence)
    assert any(item.get("source_name") for item in evidence)
    events = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/events"))
    assert any("已回退" in event["summary"] for event in events)

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_uploaded_file_high_risk_evidence_scores():
    upload = unwrap(client.post(
        "/api/uploads/materials",
        files={"file": ("risk.txt", "供应商存在疑似制裁名单关联和黑名单风险提示，同时存在付款纠纷和交付争议。", "text/plain")},
    ))
    task = unwrap(client.post("/api/diligence/tasks", json={
        "execution_mode": "sync",
        "supplier_id": "supplier_medium_001",
        "upload_ids": [upload["upload_id"]],
    }))

    assert task["risk_level"] == "high"
    assert task["total_score"] >= 70
    evidence = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/evidence"))
    uploaded = [item for item in evidence if item.get("source_type") == "uploaded_file"]
    assert uploaded
    assert any((item.get("metadata_json") or {}).get("should_use_for_scoring") for item in uploaded)


def test_missing_upload_id_writes_event_but_task_completes():
    task = unwrap(client.post("/api/diligence/tasks", json={
        "execution_mode": "sync",
        "supplier_id": "supplier_low_001",
        "upload_ids": ["upload_missing_for_test"],
    }))

    assert task["status"] == "completed"
    events = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/events"))
    assert any("不存在" in event["summary"] for event in events)

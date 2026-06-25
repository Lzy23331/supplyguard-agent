from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_sync_execution_mode_still_completes():
    response = client.post(
        "/api/diligence/tasks",
        json={"supplier_id": "supplier_low_001", "execution_mode": "sync"},
    )

    assert response.status_code == 200
    task = unwrap(response)
    assert task["status"] == "completed"
    assert task["risk_level"] == "low"


def test_async_execution_mode_returns_pending_summary_and_task_completes():
    response = client.post(
        "/api/diligence/tasks",
        json={"supplier_id": "supplier_medium_001", "execution_mode": "async"},
    )

    assert response.status_code == 200
    task = unwrap(response)
    assert task["task_id"]
    assert task["status"] in {"pending", "running", "completed"}

    detail = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}"))
    assert detail["status"] in {"running", "completed"}

    events = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/events"))
    assert events


def test_async_sample_route_is_supported():
    response = client.post("/api/diligence/tasks/from-sample/supplier_high_001?execution_mode=async")

    assert response.status_code == 200
    task = unwrap(response)
    assert task["task_id"]
    assert task["status"] in {"pending", "running", "completed"}

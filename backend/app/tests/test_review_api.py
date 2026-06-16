from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_review_submission_persists_and_marks_task_reviewed():
    task = unwrap(client.post("/api/diligence/tasks/from-sample/supplier_medium_001"))
    response = client.post(
        f"/api/diligence/tasks/{task['task_id']}/review",
        json={"reviewer": "demo_reviewer", "decision": "approve_with_conditions", "comment": "要求供应商补充合规证明和近三年交付记录后再准入。"},
    )
    assert response.status_code == 200
    review = unwrap(response)
    assert review["task_id"] == task["task_id"]
    assert review["decision"] == "approve_with_conditions"

    detail = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}"))
    assert detail["task"]["status"] == "reviewed"

    with get_db() as conn:
        row = conn.execute("SELECT decision FROM human_reviews WHERE task_id=? ORDER BY id DESC LIMIT 1", (task["task_id"],)).fetchone()
    assert row["decision"] == "approve_with_conditions"


def test_review_missing_task_returns_404():
    response = client.post("/api/diligence/tasks/task_missing/review", json={"reviewer": "demo", "decision": "reject"})
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "TASK_NOT_FOUND"

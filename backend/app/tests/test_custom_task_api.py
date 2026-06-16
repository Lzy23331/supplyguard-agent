from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_custom_supplier_task_without_mock_evidence_completes():
    response = client.post(
        "/api/diligence/tasks",
        json={
            "supplier": {
                "name": "Demo Supplier Ltd.",
                "website": "https://example.com/demo",
                "industry": "电子元器件",
                "region": "广东深圳",
                "procurement_amount": 800000,
                "annual_spend": 800000,
                "cooperation_type": "标准采购",
                "business_status": "正常",
                "company_age_years": 5,
                "profile_completeness": "中",
                "ownership_transparency": "中",
                "urgency": "常规",
            }
        },
    )
    assert response.status_code == 200
    task = unwrap(response)
    assert task["task_id"]
    assert task["status"] == "completed"
    assert task["risk_level"] in {"low", "medium", "high"}
    assert isinstance(task["total_score"], int)

    detail = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}"))
    assert detail["supplier"]["name"] == "Demo Supplier Ltd."

    events = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/events"))
    assert events

    report = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/report"))
    assert "Demo Supplier Ltd." in report["markdown_content"]


def test_task_list_includes_recent_custom_task():
    created = unwrap(client.post("/api/diligence/tasks", json={"supplier": {"name": "List Demo Supplier", "industry": "包装材料", "region": "上海", "annual_spend": 100000, "cooperation_type": "标准采购"}}))
    tasks = unwrap(client.get("/api/diligence/tasks"))
    assert any(item["task_id"] == created["task_id"] for item in tasks)

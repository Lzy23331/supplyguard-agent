from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_provider_status_masks_secrets_and_reports_demo_mode():
    data = unwrap(client.get("/api/system/provider-status"))
    assert data["deployment_mode"] in {"demo", "production", "local"}
    assert data["demo_mode_available"] is True
    for key in ["tencent_secret_id_mask", "api_key_mask"]:
        if data.get(key):
            assert data[key].startswith("****")
            assert len(data[key]) <= 8


def test_demo_case_run_creates_task_with_cached_search_profile_and_pdf():
    cases = unwrap(client.get("/api/demo-cases"))
    assert {item["case_id"] for item in cases} >= {"byd_cached_demo", "huawei_cached_demo", "xiaomi_cached_demo"}

    detail = unwrap(client.post("/api/demo-cases/byd_cached_demo/run"))
    task_id = detail["task_id"]
    diagnostics = unwrap(client.get(f"/api/diligence/tasks/{task_id}/diagnostics"))
    assert diagnostics["web_search_result_count"] >= 8
    assert diagnostics["real_url_count"] >= 3
    assert diagnostics["profile_snapshot_count"] >= 8
    assert diagnostics["scoring_evidence_count"] == 0

    report = unwrap(client.get(f"/api/diligence/tasks/{task_id}/report"))
    assert report["filename"] == f"supplyguard-report-{task_id}.md"
    assert task_id in report["markdown_content"]
    assert "Cached Demo Mode" in report["markdown_content"]

    pdf = client.get(f"/api/diligence/tasks/{task_id}/report.pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")


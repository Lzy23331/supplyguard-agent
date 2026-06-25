from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app
from app.repositories import create_task_record, save_company_profile_snapshots, save_report, save_web_search_results
from app.schemas import SupplierCreate

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def create_task(name: str) -> str:
    init_db()
    return create_task_record(SupplierCreate(name=name, procurement_amount=500000, cooperation_type="常规采购"), query_type="company_name", company_name=name)


def test_diagnostics_counts_real_urls_for_current_task():
    task_id = create_task("诊断测试企业A")
    save_web_search_results(
        task_id,
        [
            {
                "query": "诊断测试企业A 查询",
                "title": f"诊断测试企业A 搜索结果 {index}",
                "url": f"https://example.com/a-{index}",
                "snippet": "普通搜索记录。",
                "rank": index,
                "decision": "display_only",
                "decision_reason": "目标相关但未形成可评分风险证据",
                "metadata_json": {"provider_mode": "real", "should_use_for_scoring": False},
            }
            for index in range(1, 6)
        ],
    )
    data = unwrap(client.get(f"/api/diligence/tasks/{task_id}/diagnostics"))

    assert data["task_id"] == task_id
    assert data["web_search_result_count"] == 5
    assert data["real_url_count"] == 5
    assert data["search_query_count"] == 1


def test_detail_returns_company_profile_snapshot_counts_and_fields():
    task_id = create_task("画像测试企业A")
    save_company_profile_snapshots(
        task_id,
        [
            {"company_name": "画像测试企业A", "field_name": "company_full_name", "field_value": "画像测试企业A", "confidence": 0.8, "source_url": "https://example.com/profile", "reason": "测试字段"},
            {"company_name": "画像测试企业A", "field_name": "industry", "field_value": "制造业", "confidence": 0.7, "source_url": "https://example.com/profile", "reason": "测试字段"},
            {"company_name": "画像测试企业A", "field_name": "registered_address", "field_value": "深圳市", "confidence": 0.7, "source_url": "https://example.com/profile", "reason": "测试字段"},
        ],
    )
    detail = unwrap(client.get(f"/api/diligence/tasks/{task_id}"))

    assert detail["task_id"] == task_id
    assert detail["profile_snapshot_count"] == 3
    assert detail["profile_non_empty_count"] == 3
    assert {item["field_name"] for item in detail["company_profile"]} >= {"company_full_name", "industry", "registered_address"}


def test_report_export_is_bound_to_requested_task_id():
    task_a = create_task("绑定测试企业A")
    task_b = create_task("绑定测试企业B")
    save_web_search_results(
        task_a,
        [
            {
                "query": "绑定测试企业A 查询",
                "title": "绑定测试企业A 搜索结果",
                "url": "https://example.com/task-a-only",
                "snippet": "A 任务真实 URL。",
                "rank": 1,
                "decision": "display_only",
                "metadata_json": {"provider_mode": "real", "should_use_for_scoring": False},
            }
        ],
    )
    save_report(task_a, f"# 报告A\n## 1. 基本信息\n- 任务 ID：{task_a}\n- URL：https://example.com/task-a-only")
    save_report(task_b, f"# 报告B\n## 1. 基本信息\n- 任务 ID：{task_b}\n- 该任务无联网搜索结果")

    report_a = unwrap(client.get(f"/api/diligence/tasks/{task_a}/report"))
    report_b = unwrap(client.get(f"/api/diligence/tasks/{task_b}/report"))

    assert report_a["task_id"] == task_a
    assert report_a["filename"] == f"supplyguard-report-{task_a}.md"
    assert "https://example.com/task-a-only" in report_a["markdown_content"]
    assert task_a in report_a["markdown_content"]
    assert report_b["task_id"] == task_b
    assert report_b["filename"] == f"supplyguard-report-{task_b}.md"
    assert "https://example.com/task-a-only" not in report_b["markdown_content"]
    assert task_b in report_b["markdown_content"]

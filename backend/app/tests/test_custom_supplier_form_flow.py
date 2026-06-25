from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_custom_low_risk_supplier_stays_low_or_medium_not_high():
    task = unwrap(client.post("/api/diligence/tasks", json={
        "execution_mode": "sync",
        "supplier": {
            "name": "GreenField Precision Manufacturing Ltd.",
            "website": "https://example.com/greenfield",
            "industry": "精密零部件",
            "region": "江苏苏州",
            "procurement_amount": 500000,
            "cooperation_type": "标准采购",
            "business_status": "正常",
            "company_age_years": 8,
            "profile_completeness": "高",
        },
        "material_text": "该供应商资料完整，公开材料未发现行政处罚、重大失信、黑名单、制裁或重大交付纠纷。",
    }))

    assert task["status"] == "completed"
    assert task["risk_level"] in {"low", "medium"}
    assert task["risk_level"] != "high"


def test_custom_high_risk_supplier_scores_high_and_saves_user_input_evidence():
    task = unwrap(client.post("/api/diligence/tasks", json={
        "execution_mode": "sync",
        "supplier": {
            "name": "Orion Cross-border Electronics Trading LLC",
            "website": "",
            "industry": "电子元器件贸易",
            "region": "境外",
            "procurement_amount": 5000000,
            "cooperation_type": "紧急采购",
            "business_status": "信息不透明",
            "company_age_years": 1,
            "profile_completeness": "低",
        },
        "material_text": "该供应商主体注册信息披露不完整，未提供最终受益所有人说明。公开材料显示存在疑似制裁名单关联和黑名单风险提示，同时存在多起付款纠纷和交付争议。该项目属于高额紧急采购，供应商要求较高比例预付款，且未提供完整合规声明。",
    }))

    assert task["status"] == "completed"
    assert task["risk_level"] == "high"
    assert task["total_score"] >= 70

    evidence = unwrap(client.get(f"/api/diligence/tasks/{task['task_id']}/evidence"))
    user_items = [item for item in evidence if item.get("source_type") == "user_input"]
    assert user_items
    assert all(item.get("source_name") == "用户粘贴材料" for item in user_items)
    assert any((item.get("metadata_json") or {}).get("should_use_for_scoring") for item in user_items)


def test_custom_supplier_without_material_still_completes():
    task = unwrap(client.post("/api/diligence/tasks", json={
        "execution_mode": "sync",
        "supplier": {"name": "No Material Custom Supplier", "procurement_amount": 0},
    }))

    assert task["status"] == "completed"
    assert task["risk_level"] in {"low", "medium", "high"}


def test_sample_entry_still_works():
    low = unwrap(client.post("/api/diligence/tasks/from-sample/supplier_low_001"))
    medium = unwrap(client.post("/api/diligence/tasks/from-sample/supplier_medium_001"))
    high = unwrap(client.post("/api/diligence/tasks/from-sample/supplier_high_001"))

    assert low["risk_level"] == "low"
    assert medium["risk_level"] == "medium"
    assert high["risk_level"] == "high"

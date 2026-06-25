import json

from app.llm.mock_client import MockLLMClient


def test_mock_intake_plan_is_deterministic_and_supplier_aware():
    client = MockLLMClient()
    prompt = json.dumps(
        {
            "supplier_profile": {
                "region": "境外",
                "cooperation_type": "紧急采购",
                "procurement_amount": 3500000,
                "profile_completeness": "低",
                "business_status": "信息不透明",
            }
        },
        ensure_ascii=False,
    )

    plan = client.complete_json(system_prompt="", user_prompt=prompt, task_type="intake_plan")

    assert {"focus_areas", "suggested_tools", "risk_hypotheses", "questions_for_review"} <= set(plan)
    assert "境外供应商审查" in plan["focus_areas"]
    assert "制裁风险" in plan["focus_areas"]
    assert "紧急采购风险" in plan["focus_areas"]
    assert any("采购金额较高" in item for item in plan["risk_hypotheses"])
    assert any("注册证明" in item for item in plan["questions_for_review"])


def test_mock_policy_query_rewrite_returns_three_to_six_queries():
    client = MockLLMClient()
    prompt = json.dumps(
        {
            "supplier_profile": {"region": "境外", "cooperation_type": "紧急采购"},
            "evidence_keywords": ["制裁", "黑名单", "交付延期", "合同争议"],
        },
        ensure_ascii=False,
    )

    result = client.complete_json(system_prompt="", user_prompt=prompt, task_type="policy_query_rewrite")

    assert 3 <= len(result["queries"]) <= 6
    assert len(result["queries"]) == len(set(result["queries"]))
    assert any("制裁" in query for query in result["queries"])

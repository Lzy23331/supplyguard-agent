from app.services.evidence_scoring_service import EvidenceScoringService
from app.tools.risk_rules import RiskRuleTool


def test_observation_risk_never_scores():
    item = {
        "title": "联网搜索未发现明确高风险线索",
        "source_url": None,
        "source_type": "web_search",
        "risk_keywords": ["观察性风险"],
        "confidence": 0.35,
        "should_use_for_scoring": True,
    }

    should_score, reason = EvidenceScoringService().should_score(item)
    risk = RiskRuleTool().assess([item], {"name": "测试企业", "website": "https://example.com", "industry": "制造业", "region": "广东省"})

    assert should_score is False
    assert reason == "observation_or_no_obvious_risk"
    assert not any(rule["actual_risk"] for rule in risk["triggered_rules"])


def test_company_profile_completion_suppresses_missing_fields():
    supplier = {
        "name": "测试企业",
        "procurement_amount": 500000,
        "company_profile": [
            {"field_name": "website", "field_value": "https://example.com", "confidence": 0.6},
            {"field_name": "industry", "field_value": "制造业", "confidence": 0.6},
            {"field_name": "registered_address", "field_value": "广东省深圳市", "confidence": 0.6},
        ],
    }

    risk = RiskRuleTool().assess([], supplier)
    rule_ids = {rule["rule_id"] for rule in risk["triggered_rules"]}

    assert "website_missing" not in rule_ids
    assert "industry_missing" not in rule_ids
    assert "region_missing" not in rule_ids


def test_only_missing_info_and_high_procurement_is_not_high_risk():
    supplier = {"name": "测试企业", "procurement_amount": 5000000}

    risk = RiskRuleTool().assess([], supplier)

    assert risk["total_score"] <= 45
    assert risk["risk_level"] in {"low", "medium"}
    assert risk["actual_risk_rule_count"] == 0


def test_real_web_search_penalty_evidence_scores_with_url_and_entity_match():
    evidence = [
        {
            "source_type": "web_search",
            "title": "测试企业行政处罚决定书",
            "content": "测试企业存在行政处罚记录。",
            "source_url": "https://creditchina.gov.cn/test-penalty",
            "risk_keywords": ["administrative_penalty"],
            "confidence": 0.72,
            "severity": "critical",
            "metadata_json": {"entity_match_score": 0.8, "should_use_for_scoring": True},
        }
    ]

    risk = RiskRuleTool().assess(evidence, {"name": "测试企业", "website": "https://example.com", "industry": "制造业", "region": "广东省"})

    assert any(rule["rule_id"] == "serious_administrative_penalty" for rule in risk["triggered_rules"])
    assert risk["actual_risk_rule_count"] >= 1


def test_unrelated_same_name_web_search_does_not_score():
    evidence = [
        {
            "source_type": "web_search",
            "title": "同名公司行政处罚决定书",
            "content": "另一家同名公司存在行政处罚记录。",
            "source_url": "https://creditchina.gov.cn/other-penalty",
            "risk_keywords": ["administrative_penalty"],
            "confidence": 0.72,
            "severity": "critical",
            "metadata_json": {"entity_match_score": 0.3, "should_use_for_scoring": True},
        }
    ]

    risk = RiskRuleTool().assess(evidence, {"name": "测试企业", "website": "https://example.com", "industry": "制造业", "region": "广东省"})

    assert not any(rule["rule_id"] == "serious_administrative_penalty" for rule in risk["triggered_rules"])
    assert risk["actual_risk_rule_count"] == 0

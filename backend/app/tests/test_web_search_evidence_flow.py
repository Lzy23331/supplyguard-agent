from app.tools.external_evidence_normalizer import ExternalEvidenceNormalizer
from app.tools.risk_rules import RiskRuleTool
from app.tools.search_result_evidence_extractor import SearchResultEvidenceExtractor


def test_web_search_high_risk_evidence_affects_risk_score():
    candidates = SearchResultEvidenceExtractor().extract([
        {
            "query": "Northbridge 黑名单 制裁",
            "purpose": "compliance_risk",
            "title": "Northbridge 疑似黑名单与制裁风险",
            "snippet": "搜索摘要显示该供应商存在黑名单、制裁和失信被执行人风险提示。",
            "url": "https://example.com/northbridge-risk",
            "rank": 1,
        }
    ])
    normalizer = ExternalEvidenceNormalizer()
    evidence = [normalizer.normalize(candidate, "TencentWebSearchProvider", "web_search") for candidate in candidates]
    risk = RiskRuleTool().assess(evidence, {
        "name": "Northbridge Electronics Trading LLC.",
        "region": "境外",
        "industry": "电子元器件贸易",
        "procurement_amount": 5000000,
        "cooperation_type": "紧急采购",
        "profile_completeness": "低",
        "ownership_transparency": "低",
        "business_status": "信息不透明",
        "company_age_years": 1,
        "urgency": "紧急",
    })

    assert evidence[0]["source_type"] == "web_search"
    assert evidence[0]["should_use_for_scoring"] is True
    assert risk["risk_level"] == "high"
    assert risk["total_score"] >= 70

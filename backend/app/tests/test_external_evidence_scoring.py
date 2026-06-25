from app.tools.risk_rules import RiskRuleTool


def test_external_evidence_source_types_are_scored():
    evidence = [
        {
            "source_type": "mock_external",
            "title": "疑似制裁名单关联与黑名单风险提示",
            "content": "存在疑似制裁名单关联和黑名单风险提示。",
            "severity": "critical",
            "risk_keywords": ["疑似制裁名单关联", "黑名单"],
            "confidence": 0.93,
        },
        {
            "source_type": "internal_record",
            "title": "内部记录提示预付款争议",
            "content": "要求较高预付款比例且存在付款纠纷记录。",
            "severity": "critical",
            "risk_keywords": ["预付款", "付款纠纷"],
            "confidence": 0.88,
        },
    ]

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

    assert risk["risk_level"] == "high"
    assert risk["total_score"] >= 70

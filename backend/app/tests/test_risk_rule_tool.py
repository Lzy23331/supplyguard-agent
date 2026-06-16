from app.services.sample_service import list_sample_suppliers
from app.tools.mock_search_tool import MockSearchTool
from app.tools.risk_rule_tool import RiskRuleTool


def _assess(sample_key: str):
    supplier = next(item for item in list_sample_suppliers() if item["sample_key"] == sample_key)
    evidence = MockSearchTool().search_by_supplier_id(supplier["id"])
    return RiskRuleTool().assess(evidence, supplier)


def test_low_medium_high_risk_levels():
    assert _assess("low")["risk_level"] == "low"
    assert _assess("medium")["risk_level"] == "medium"
    assert _assess("high")["risk_level"] == "high"


def test_medium_score_is_stable():
    result = _assess("medium")
    assert 45 <= result["total_score"] <= 55


def test_high_score_is_capped_with_raw_score():
    result = _assess("high")
    assert result["raw_score"] >= 100
    assert result["total_score"] == 100


def test_high_triggered_rules_include_sanction_or_blacklist():
    result = _assess("high")
    assert any(rule["rule_id"] == "sanction_or_blacklist" for rule in result["triggered_rules"])


def test_all_results_have_dimensions_and_recommendations():
    for sample_key in ["low", "medium", "high"]:
        result = _assess(sample_key)
        assert set(result["dimension_scores"]) == {"compliance", "business", "delivery", "completeness", "reputation"}
        assert result["recommendation"]

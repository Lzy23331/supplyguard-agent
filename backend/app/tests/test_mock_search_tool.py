from app.tools.mock_search_tool import MockSearchTool


def test_mock_search_reads_all_sample_suppliers():
    tool = MockSearchTool()
    assert tool.search_by_supplier_id("supplier_low_001")
    assert tool.search_by_supplier_id("supplier_medium_001")
    assert tool.search_by_supplier_id("supplier_high_001")


def test_high_risk_contains_sanction_signal():
    evidence = MockSearchTool().search_by_supplier_id("supplier_high_001")
    signals = {signal for item in evidence for signal in item.get("rule_signals", [])}
    assert "sanction_or_blacklist" in signals


def test_missing_supplier_returns_empty_list():
    assert MockSearchTool().search_by_supplier_id("supplier_missing_999") == []

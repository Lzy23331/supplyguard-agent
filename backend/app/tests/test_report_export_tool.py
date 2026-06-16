from app.services.task_service import TaskService
from app.tools.report_export import ReportExportTool
from app.tools.risk_rules import RiskRuleTool


REQUIRED_SECTIONS = [
    "# 供应商准入尽调报告",
    "## 1. 基本信息",
    "## 2. 综合结论",
    "## 3. 风险评分",
    "## 4. 合规风险分析",
    "## 5. 经营与交付风险分析",
    "## 6. 关键证据链",
    "## 7. 命中政策依据",
    "## 8. 准入建议",
    "## 9. 人工复核建议",
]


def test_report_export_tool_builds_required_sections_and_cap_note():
    supplier = {"name": "High Risk Supplier", "annual_spend": 5000000, "region": "境外", "cooperation_type": "紧急采购"}
    evidence = [
        {
            "id": "e1",
            "source": "mock",
            "title": "Sanction and blacklist alert",
            "content": "命中制裁名单、黑名单、商业贿赂和欺诈风险。",
            "severity": "critical",
            "rule_signals": ["sanction_or_blacklist", "bribery_or_fraud", "opaque_ownership"],
        }
    ]
    risk = RiskRuleTool().assess(evidence, supplier)
    assert risk["raw_score"] >= 100
    assert risk["total_score"] == 100
    assert risk["triggered_rules"]

    markdown = ReportExportTool().build_markdown(
        supplier=supplier,
        evidence=evidence,
        risk=risk,
        policies=[{"doc_name": "risk_rating_rules.md", "section_title": "高风险", "content": "制裁名单、黑名单、升级审批。", "matched_keywords": ["制裁名单", "黑名单"]}],
    )
    for section in REQUIRED_SECTIONS:
        assert section in markdown
    assert "原始累计风险分" in markdown
    assert "截断" in markdown


def test_persisted_report_contains_policy_evidence_and_recommendation():
    service = TaskService()
    task = service.create_task_from_sample("supplier_high_001")
    report = service.get_report(task["id"])

    assert report is not None
    assert "制裁" in report or "黑名单" in report
    assert "关键证据链" in report
    assert "建议拒绝准入" in report or "建议升级审批" in report

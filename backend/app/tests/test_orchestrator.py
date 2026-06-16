from app.services.task_service import TaskService


def test_orchestrator_runs_all_sample_risk_levels():
    service = TaskService()

    low = service.create_task_from_sample("supplier_low_001")
    assert low["status"] == "completed"
    assert low["risk_level"] == "low"
    assert "建议准入" in low["recommendation"]

    medium = service.create_task_from_sample("supplier_medium_001")
    assert medium["status"] == "completed"
    assert medium["risk_level"] == "medium"
    assert 45 <= medium["total_score"] <= 55
    assert "补充材料" in medium["recommendation"] or "人工复核" in medium["recommendation"]

    high = service.create_task_from_sample("supplier_high_001")
    assert high["status"] == "completed"
    assert high["risk_level"] == "high"
    assert high["total_score"] == 100
    assert "拒绝" in high["recommendation"] or "升级审批" in high["recommendation"]


def test_orchestrator_persists_evidence_and_report():
    service = TaskService()
    task = service.create_task_from_sample("high")

    evidence = service.get_evidence(task["id"])
    assert evidence
    assert any("sanction_or_blacklist" in item.get("rule_signals", []) for item in evidence)

    report = service.get_report(task["id"])
    assert report is not None
    assert "# 供应商准入尽调报告" in report
    assert "## 7. 命中政策依据" in report

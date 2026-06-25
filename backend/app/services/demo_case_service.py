from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.database import init_db
from app.repositories import (
    add_assessment,
    add_event,
    create_task_record,
    get_task,
    get_task_detail,
    list_tasks,
    save_company_profile_snapshots,
    save_report,
    save_risk_assessment,
    save_web_search_results,
    task_diagnostics,
    update_supplier_for_task,
    update_task,
)
from app.schemas import SupplierCreate
from app.tools.report_export import ReportExportTool


class DemoCaseService:
    name = "DemoCaseService"

    def __init__(self, path: Path | None = None) -> None:
        settings = get_settings()
        self.path = path or (settings.data_dir / "demo_cases" / "demo_cases.json")
        self.report_tool = ReportExportTool()

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8-sig"))

    def _case(self, case_id: str) -> dict[str, Any] | None:
        return next((item for item in self._load() if item.get("case_id") == case_id), None)

    def list_cases(self) -> list[dict[str, Any]]:
        cases = []
        for item in self._load():
            rows = item.get("web_search_results") or []
            profile = item.get("company_profile") or {}
            cases.append(
                {
                    "case_id": item["case_id"],
                    "company_name": item["company_name"],
                    "description": item.get("description"),
                    "industry": item.get("industry"),
                    "region": item.get("region"),
                    "risk_level": item.get("risk_level"),
                    "score": item.get("score"),
                    "web_search_results_count": len(rows),
                    "real_url_count": sum(1 for row in rows if row.get("url")),
                    "profile_field_count": sum(1 for value in profile.values() if value),
                    "report_available": True,
                    "cached_demo": True,
                }
            )
        return cases

    def preview(self, case_id: str) -> dict[str, Any]:
        item = self._case(case_id)
        if not item:
            raise ValueError(f"Demo case not found: {case_id}")
        rows = item.get("web_search_results") or []
        profile = item.get("company_profile") or {}
        return {
            "case_id": item["case_id"],
            "company_name": item["company_name"],
            "description": item.get("description"),
            "risk_level": item.get("risk_level"),
            "score": item.get("score"),
            "search_queries": item.get("search_queries") or [],
            "web_search_results_preview": rows[:5],
            "company_profile_preview": profile,
            "web_search_results_count": len(rows),
            "real_url_count": sum(1 for row in rows if row.get("url")),
            "profile_field_count": sum(1 for value in profile.values() if value),
            "cached_demo": True,
        }

    def run_case(self, case_id: str) -> dict[str, Any]:
        init_db()
        item = self._case(case_id)
        if not item:
            raise ValueError(f"Demo case not found: {case_id}")
        supplier = SupplierCreate(
            name=item["company_name"],
            website=item.get("website"),
            industry=item.get("industry"),
            region=item.get("region"),
            procurement_amount=item.get("procurement_amount") or 0,
            annual_spend=item.get("procurement_amount") or 0,
            cooperation_type=item.get("cooperation_type"),
            sample_key=f"demo_{case_id}",
            business_status=(item.get("company_profile") or {}).get("business_status"),
            summary=item.get("description"),
            tags=["cached_demo", case_id],
            expected_risk_level=item.get("risk_level"),
        )
        task_id = create_task_record(supplier, query_type="company_name", company_name=item["company_name"])
        update_supplier_for_task(task_id, {"website": item.get("website"), "industry": item.get("industry"), "region": item.get("region")})
        web_rows = [self._web_row(row, case_id) for row in item.get("web_search_results") or []]
        save_web_search_results(task_id, web_rows)
        save_company_profile_snapshots(task_id, self._profile_rows(item, web_rows))
        risk = self._risk_result(item)
        save_risk_assessment(task_id, risk)
        for dimension in risk["dimensions"]:
            add_assessment(task_id, dimension)
        report = self.report_tool.build_markdown(
            supplier={
                "name": item["company_name"],
                "website": item.get("website"),
                "industry": item.get("industry"),
                "region": item.get("region"),
                "procurement_amount": item.get("procurement_amount"),
                "annual_spend": item.get("procurement_amount"),
                "cooperation_type": item.get("cooperation_type"),
                "company_name": item["company_name"],
                "query_type": "company_name",
                "task_id": task_id,
            },
            evidence=[],
            risk=risk,
            policies=self._policies(item),
            plan={"checks": ["缓存演示案例", "联网搜索覆盖", "企业画像补全", "证据可信度评估", "规则评分", "报告导出"]},
            web_search_results=web_rows,
            company_profile=self._profile_rows(item, web_rows),
            search_queries=[{"query": query, "purpose": "demo_due_diligence"} for query in item.get("search_queries") or []],
            task_id=task_id,
        )
        polished = self._polish_report(report, item)
        save_report(task_id, polished)
        add_event(
            task_id,
            "DemoCaseService",
            "demo_case_loaded",
            "completed",
            f"已加载缓存演示案例 {case_id}，未调用腾讯云或 LLM 实时 API。",
            tool_name=self.name,
            tool_input={"case_id": case_id, "cached_demo": True},
            tool_output_summary=f"web_search_results={len(web_rows)}; profile_fields={len(item.get('company_profile') or {})}",
        )
        add_event(
            task_id,
            "ReportPolishAgent",
            "report_polish",
            "completed",
            "已使用确定性缓存模板生成专业化报告；未改变风险分数、等级或证据事实。",
            tool_name="LLMReportWriter",
            tool_input={"mode": "cached_demo", "llm_called": False},
            tool_output_summary="llm_polish_status=deterministic_cached_demo",
        )
        update_task(task_id, status="completed", risk_level=item.get("risk_level"), total_score=item.get("score"), recommendation=item.get("recommendation"), summary=item.get("description"))
        return get_task_detail(task_id) or {"task_id": task_id}

    def _web_row(self, row: dict[str, Any], case_id: str) -> dict[str, Any]:
        return {
            **row,
            "source_type": "web_search",
            "source_name": "腾讯云联网搜索（缓存演示）",
            "confidence": 0.82 if row.get("decision") == "score_evidence" else 0.62,
            "evidence_strength": "cached_demo",
            "entity_relation_type": "exact_target" if (row.get("entity_match_score") or 0) >= 0.8 else "related_or_display",
            "is_duplicate": False,
            "metadata_json": {
                "provider_mode": "cached_demo",
                "demo_case_id": case_id,
                "should_use_for_scoring": row.get("decision") == "score_evidence",
            },
        }

    def _profile_rows(self, item: dict[str, Any], web_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        profile = item.get("company_profile") or {}
        source = next((row for row in web_rows if row.get("url")), {})
        rows = []
        for field, value in profile.items():
            rows.append(
                {
                    "company_name": item["company_name"],
                    "field_name": field,
                    "field_value": value,
                    "confidence": 0.82 if value else 0.0,
                    "source_type": "web_search_profile",
                    "source_name": "缓存演示公开网页摘要",
                    "source_url": source.get("url"),
                    "query": source.get("query"),
                    "extraction_method": "cached_demo_seed",
                    "requires_manual_verification": True,
                    "reason": "缓存演示字段，来源于公开网页摘要，需以官方工商核验为准。",
                    "metadata_json": {"demo_case_id": item["case_id"]},
                }
            )
        return rows

    def _risk_result(self, item: dict[str, Any]) -> dict[str, Any]:
        dimensions = []
        for dimension, score in (item.get("dimension_scores") or {}).items():
            level = "high" if score >= 70 else "medium" if score >= 40 else "low"
            dimensions.append({"dimension": dimension, "score": score, "level": level, "rationale": "缓存演示风险维度评分。"})
        triggered = [
            {"rule_id": rule, "rule_name": rule, "dimension": "compliance" if "sanction" in rule or "dishonesty" in rule else "business", "score": 0, "reason": "缓存演示命中规则", "actual_risk": item.get("risk_level") == "high"}
            for rule in item.get("matched_rules") or []
        ]
        return {
            "raw_score": item.get("score"),
            "total_score": item.get("score"),
            "risk_level": item.get("risk_level"),
            "recommendation": item.get("recommendation"),
            "dimensions": dimensions,
            "dimension_scores": item.get("dimension_scores") or {},
            "triggered_rules": triggered,
            "actual_risk_rule_count": sum(1 for row in item.get("web_search_results") or [] if row.get("decision") == "score_evidence"),
        }

    def _policies(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"doc_name": "supplier_onboarding_policy.md", "section_title": "资料完整性与人工复核", "matched_keywords": ["资料完整性", "人工复核"], "content": "供应商准入应保留公开证据链，资料缺失或高额采购时应补充材料并人工复核。"},
            {"doc_name": "procurement_review_sop.md", "section_title": "高额采购复核", "matched_keywords": ["高额采购", "补充材料"], "content": "高额采购应核验主体身份、履约能力和替代供应商方案。"},
        ]

    def _polish_report(self, report: str, item: dict[str, Any]) -> str:
        header = "\n> 报告版本：Cached Demo Mode 专业化报告。以下内容基于预置公开网页摘要和规则评分生成，未调用实时 API；LLM 不改变分数、等级或证据事实。\n"
        return report.replace("# 供应商准入尽调报告", "# 供应商准入尽调报告" + header, 1)


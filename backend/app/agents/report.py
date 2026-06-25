from app.agents.base import AgentContext, BaseAgent
from app.repositories import list_company_profile_snapshots, list_events, list_evidence, list_web_search_results, save_company_profile_snapshots, save_report
from app.services.company_profile_extractor import CompanyProfileExtractor
from app.tools.report_export import ReportExportTool


class ReportAgent(BaseAgent):
    name = "ReportAgent"

    def __init__(self) -> None:
        self.report_tool = ReportExportTool()
        self.profile_extractor = CompanyProfileExtractor()

    def _search_queries_from_events(self, task_id: str) -> list[dict[str, str]]:
        queries: list[dict[str, str]] = []
        for event in list_events(task_id):
            payload = event.get("tool_input") or {}
            if isinstance(payload, dict):
                raw_queries = payload.get("queries") or payload.get("search_queries")
                if isinstance(raw_queries, list):
                    for item in raw_queries:
                        if isinstance(item, dict) and item.get("query"):
                            queries.append({"query": str(item.get("query")), "purpose": str(item.get("purpose") or "due_diligence")})
                        elif isinstance(item, str):
                            queries.append({"query": item, "purpose": "due_diligence"})
            output = event.get("tool_output_summary") or ""
            if not queries and event.get("event_type") == "search_query_plan" and output:
                for part in str(output).replace("；", "\n").replace(";", "\n").splitlines():
                    part = part.strip()
                    if part:
                        queries.append({"query": part, "purpose": "due_diligence"})
        seen = set()
        result = []
        for item in queries:
            query = item.get("query")
            if query and query not in seen:
                seen.add(query)
                result.append(item)
        return result
    def run(self, context: AgentContext) -> AgentContext:
        try:
            self.started(context, "开始生成供应商准入尽调报告。")
            evidence = list_evidence(context["task_id"]) or context.get("evidence", [])
            web_search_results = list_web_search_results(context["task_id"])
            company_profile = list_company_profile_snapshots(context["task_id"])
            if not company_profile and web_search_results:
                company_name = context["supplier"].get("company_name") or context["supplier"].get("name")
                extracted_profile = self.profile_extractor.extract(
                    task_id=context["task_id"],
                    company_name=company_name,
                    search_results=web_search_results,
                )
                save_company_profile_snapshots(context["task_id"], [{**row, "company_name": company_name} for row in extracted_profile])
                company_profile = list_company_profile_snapshots(context["task_id"])
                self.event(
                    context["task_id"],
                    "company_profile_report_fallback",
                    "completed",
                    "报告生成前发现企业画像为空，已基于已入库联网搜索结果补抽企业画像字段。",
                    tool_name=self.profile_extractor.name,
                    tool_input={"web_search_results": len(web_search_results), "company_name": company_name},
                    tool_output_summary=f"profile_fields={len(company_profile)}",
                )
            search_queries = context.get("search_queries") or self._search_queries_from_events(context["task_id"])
            markdown = self.report_tool.build_markdown(
                supplier=context["supplier"],
                evidence=evidence,
                risk=context["risk"],
                policies=context.get("policies", []),
                compliance_summary=context.get("compliance_summary"),
                business_summary=context.get("business_summary"),
                plan=context.get("plan"),
                web_search_results=web_search_results,
                company_profile=company_profile,
                search_queries=search_queries,
                task_id=context["task_id"],
            )
            self.tool_called(
                context,
                self.report_tool.name,
                {"supplier_id": context["supplier"].get("id"), "risk_level": context["risk"].get("risk_level")},
                f"生成 Markdown 报告 {len(markdown)} 个字符。",
            )
            scoring_count = sum(1 for item in web_search_results if self.report_tool._is_scoring_web_search(item))
            display_count = sum(1 for item in web_search_results if item.get("decision") == "display_only")
            profile_count = len(company_profile)
            real_url_count = sum(1 for item in web_search_results if item.get("url") or item.get("source_url"))
            no_url_reason = None
            if web_search_results and real_url_count == 0:
                no_url_reason = "web_search_results 已入库但所有记录缺少 URL，可能是 API 返回为空 URL 或入库前被清洗。"
            elif not web_search_results:
                no_url_reason = "web_search_results 未入库，报告只能展示 evidence_items 中的联网搜索摘要。"
            self.event(
                context["task_id"],
                "report_web_search_section",
                "completed",
                f"报告已展示联网搜索记录 {len(web_search_results)} 条，其中真实 URL {real_url_count} 条，可评分证据 {scoring_count} 条，普通记录 {display_count} 条，企业画像字段 {profile_count} 项。",
                tool_name=self.report_tool.name,
                tool_input={"task_id": context["task_id"], "real_url_count": real_url_count, "no_url_reason": no_url_reason},
                tool_output_summary=f"web_search_results={len(web_search_results)}; real_urls={real_url_count}; score_evidence={scoring_count}; display_only={display_count}; company_profile={profile_count}; no_url_reason={no_url_reason or 'none'}",
            )
            save_report(context["task_id"], markdown)
            context["report"] = markdown
            context["report_markdown"] = markdown
            self.completed(context, "已生成 Markdown 格式供应商准入尽调报告。")
            return context
        except Exception as exc:  # pragma: no cover
            self.failed(context, f"报告生成失败：{exc}")
            raise






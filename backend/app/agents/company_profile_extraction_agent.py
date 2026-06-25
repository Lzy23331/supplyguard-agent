from app.agents.base import AgentContext, BaseAgent
from app.repositories import list_company_profile_snapshots, list_web_search_results, save_company_profile_snapshots
from app.services.company_profile_extractor import CompanyProfileExtractor


class CompanyProfileExtractionAgent(BaseAgent):
    name = "CompanyProfileExtractionAgent"

    FIELD_TO_SUPPLIER = {
        "company_full_name": "name",
        "website": "website",
        "industry": "industry",
        "region": "region",
        "business_status": "business_status",
    }

    def __init__(self) -> None:
        self.extractor = CompanyProfileExtractor()

    def run(self, context: AgentContext) -> AgentContext:
        supplier = context["supplier"]
        if not (supplier.get("query_type") == "company_name" or supplier.get("company_name")):
            return context
        self.started(context, "开始从联网搜索标题、摘要和 URL 抽取企业画像字段。")
        company_name = supplier.get("company_name") or supplier.get("name")
        web_rows = list_web_search_results(context["task_id"])
        if not web_rows:
            self.event(
                context["task_id"],
                "company_profile_skipped",
                "completed",
                "未发现联网搜索结果，跳过企业画像抽取。",
                tool_name=self.extractor.name,
                tool_input={"company_name": company_name},
                tool_output_summary="web_search_results=0",
            )
            context["company_profile"] = []
            return context
        rows = self.extractor.extract(task_id=context["task_id"], company_name=company_name, search_results=web_rows)
        save_company_profile_snapshots(context["task_id"], [{**row, "company_name": company_name} for row in rows])
        saved = list_company_profile_snapshots(context["task_id"])
        completed_fields = []
        for item in saved:
            target = self.FIELD_TO_SUPPLIER.get(item.get("field_name"))
            if target and item.get("field_value") and (item.get("confidence") or 0) >= 0.6:
                supplier[target] = item["field_value"]
                completed_fields.append(item.get("field_name"))
        context["supplier"] = supplier
        context["company_profile"] = saved
        self.tool_called(
            context,
            self.extractor.name,
            {"company_name": company_name, "web_search_results": len(web_rows)},
            f"抽取企业画像字段 {len(saved)} 项，高置信补全字段 {len(completed_fields)} 项。",
        )
        self.event(
            context["task_id"],
            "company_profile_extracted",
            "completed",
            "企业画像字段已按字段级来源 URL 保存；所有字段均标记为搜索摘要推断，需人工复核。",
            tool_name=self.extractor.name,
            tool_input={"fields": [item.get("field_name") for item in saved], "completed_fields": completed_fields},
            tool_output_summary=f"profile_fields={len(saved)}; completed_fields={len(completed_fields)}",
        )
        self.completed(context, f"企业画像抽取完成，共保存 {len(saved)} 个字段。")
        return context

from app.agents.base import AgentContext, BaseAgent
from app.repositories import update_supplier_for_task
from app.services.company_query_service import CompanyQueryService


class CompanyResolverAgent(BaseAgent):
    name = "CompanyResolverAgent"

    def __init__(self) -> None:
        self.service = CompanyQueryService()

    def run(self, context: AgentContext) -> AgentContext:
        supplier = context["supplier"]
        company_name = supplier.get("company_name") or supplier.get("name")
        self.started(context, f"开始解析企业名称：{company_name}。")
        resolved = self.service.resolve_profile(
            company_name=company_name,
            procurement_amount=supplier.get("procurement_amount"),
            cooperation_type=supplier.get("cooperation_type"),
        )
        resolved["id"] = supplier.get("id")
        resolved["query_type"] = "company_name"
        resolved["company_name"] = company_name
        resolved["material_text"] = supplier.get("material_text")
        resolved["upload_ids"] = supplier.get("upload_ids") or []
        update_supplier_for_task(context["task_id"], resolved)
        context["supplier"] = resolved
        status = resolved.get("resolution_status")
        if status == "matched_mock_profile":
            self.event(
                context["task_id"],
                "resolver_candidate_hit",
                "completed",
                f"命中模拟企业档案：{resolved.get('name')}。",
                tool_name="MockCompanyInfoProvider.resolve",
                tool_input={"company_name": company_name},
                tool_output_summary=resolved.get("summary"),
            )
        else:
            self.event(
                context["task_id"],
                "resolver_incomplete_created",
                "completed",
                "未命中模拟企业档案，已创建信息不完整供应商画像。",
                tool_name="CompanyQueryService.resolve_profile",
                tool_input={"company_name": company_name},
                tool_output_summary=resolved.get("summary"),
            )
        self.completed(context, f"企业名称解析完成：{resolved.get('name')}。")
        return context

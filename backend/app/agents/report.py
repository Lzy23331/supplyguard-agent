from app.agents.base import AgentContext, BaseAgent
from app.repositories import save_report
from app.tools.report_export import ReportExportTool


class ReportAgent(BaseAgent):
    name = "ReportAgent"

    def __init__(self) -> None:
        self.report_tool = ReportExportTool()

    def run(self, context: AgentContext) -> AgentContext:
        try:
            self.started(context, "开始生成供应商准入尽调报告。")
            markdown = self.report_tool.build_markdown(
                supplier=context["supplier"],
                evidence=context.get("evidence", []),
                risk=context["risk"],
                policies=context.get("policies", []),
                compliance_summary=context.get("compliance_summary"),
                business_summary=context.get("business_summary"),
                plan=context.get("plan"),
            )
            self.tool_called(
                context,
                self.report_tool.name,
                {"supplier_id": context["supplier"].get("id"), "risk_level": context["risk"].get("risk_level")},
                f"生成 Markdown 报告 {len(markdown)} 个字符。",
            )
            save_report(context["task_id"], markdown)
            context["report"] = markdown
            context["report_markdown"] = markdown
            self.completed(context, "已生成 Markdown 格式供应商准入尽调报告。")
            return context
        except Exception as exc:  # pragma: no cover
            self.failed(context, f"报告生成失败：{exc}")
            raise

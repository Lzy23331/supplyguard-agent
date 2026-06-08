from app.agents.base import AgentContext, BaseAgent
from app.repositories import save_report
from app.tools.report_export import ReportExportTool


class ReportAgent(BaseAgent):
    name = "ReportAgent"

    def __init__(self) -> None:
        self.report_tool = ReportExportTool()

    def run(self, context: AgentContext) -> AgentContext:
        markdown = self.report_tool.build_markdown(
            context["supplier"], context["plan"], context["evidence"], context["risk"], context["policies"]
        )
        save_report(context["task_id"], markdown)
        context["report"] = markdown
        self.event(context["task_id"], "completed", "已生成 Markdown 格式供应商尽调报告。", [{"tool": self.report_tool.name}])
        return context

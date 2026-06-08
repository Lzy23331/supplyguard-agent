from app.agents.base import AgentContext, BaseAgent
from app.tools.evidence_store import EvidenceStoreTool
from app.tools.mock_search import MockSearchTool


class EvidenceCollectorAgent(BaseAgent):
    name = "EvidenceCollectorAgent"

    def __init__(self) -> None:
        self.search_tool = MockSearchTool()
        self.store_tool = EvidenceStoreTool()

    def run(self, context: AgentContext) -> AgentContext:
        evidence = self.search_tool.search(context["supplier"])
        count = self.store_tool.save_many(context["task_id"], evidence)
        context["evidence"] = evidence
        self.event(
            context["task_id"],
            "completed",
            f"已收集并保存 {count} 条供应商证据。",
            [{"tool": self.search_tool.name, "count": len(evidence)}, {"tool": self.store_tool.name, "count": count}],
        )
        return context

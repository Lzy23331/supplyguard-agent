from app.agents.base import AgentContext, BaseAgent
from app.tools.evidence_store import EvidenceStoreTool
from app.tools.mock_search import MockSearchTool


class EvidenceCollectorAgent(BaseAgent):
    name = "EvidenceCollectorAgent"

    def __init__(self) -> None:
        self.search_tool = MockSearchTool()
        self.store_tool = EvidenceStoreTool()

    def run(self, context: AgentContext) -> AgentContext:
        try:
            self.started(context, "开始收集供应商公开信息、合同履约和模拟风险证据。")
            supplier = context["supplier"]
            evidence = self.search_tool.search(supplier)
            self.tool_called(
                context,
                self.search_tool.name,
                {"supplier_id": supplier.get("id"), "sample_key": supplier.get("sample_key"), "name": supplier.get("name")},
                f"返回 {len(evidence)} 条模拟证据。",
            )
            self.store_tool.save_many(context["task_id"], evidence)
            self.tool_called(
                context,
                self.store_tool.name,
                {"task_id": context["task_id"], "evidence_count": len(evidence)},
                f"已写入 {len(evidence)} 条证据。",
            )
            context["evidence"] = evidence
            context["evidence_items"] = evidence
            self.completed(context, f"证据收集完成，共获得 {len(evidence)} 条证据。")
            return context
        except Exception as exc:  # pragma: no cover
            self.failed(context, f"证据收集失败：{exc}")
            raise

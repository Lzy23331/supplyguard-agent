from app.agents.base import AgentContext, BaseAgent
from app.repositories import add_assessment

LEVEL_LABELS = {"low": "低风险", "medium": "中风险", "high": "高风险"}
DIMENSION_LABELS = {
    "compliance": "合规风险",
    "business": "经营风险",
    "delivery": "交付风险",
    "completeness": "资料完整性",
    "reputation": "舆情风险",
}


class BusinessRiskAgent(BaseAgent):
    name = "BusinessRiskAgent"

    def run(self, context: AgentContext) -> AgentContext:
        for item in context["risk"]["dimensions"]:
            if item["dimension"] != "compliance":
                add_assessment(context["task_id"], item)
        levels = {
            DIMENSION_LABELS.get(d["dimension"], d["dimension"]): LEVEL_LABELS.get(d["level"], d["level"])
            for d in context["risk"]["dimensions"]
        }
        self.event(context["task_id"], "completed", f"经营、交付、资料完整性与舆情风险评估完成：{levels}。", [])
        return context

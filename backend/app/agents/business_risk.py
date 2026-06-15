from app.agents.base import AgentContext, BaseAgent
from app.repositories import add_assessment

LEVEL_LABELS = {"Low": "低风险", "Medium": "中风险", "High": "高风险"}
DIMENSION_LABELS = {
    "Compliance": "合规风险",
    "Business": "经营风险",
    "Delivery": "交付风险",
    "Completeness": "资料完整性",
    "Reputation": "舆情风险",
}


class BusinessRiskAgent(BaseAgent):
    name = "BusinessRiskAgent"

    def run(self, context: AgentContext) -> AgentContext:
        for item in context["risk"]["dimensions"]:
            if item["dimension"] != "Compliance":
                add_assessment(context["task_id"], item)
        levels = {
            DIMENSION_LABELS.get(d["dimension"], d["dimension"]): LEVEL_LABELS.get(d["level"], d["level"])
            for d in context["risk"]["dimensions"]
        }
        self.event(context["task_id"], "completed", f"经营、交付、资料完整性与舆情风险评估完成：{levels}。", [])
        return context

from app.agents.base import AgentContext, BaseAgent
from app.repositories import add_assessment


class BusinessRiskAgent(BaseAgent):
    name = "BusinessRiskAgent"

    def run(self, context: AgentContext) -> AgentContext:
        for item in context["risk"]["dimensions"]:
            if item["dimension"] != "Compliance":
                add_assessment(context["task_id"], item)
        levels = {d["dimension"]: d["level"] for d in context["risk"]["dimensions"]}
        self.event(context["task_id"], "completed", f"Business and delivery risks evaluated: {levels}.", [])
        return context


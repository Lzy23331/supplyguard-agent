from app.agents.base import AgentContext, BaseAgent


class IntakeAgent(BaseAgent):
    name = "IntakeAgent"

    def run(self, context: AgentContext) -> AgentContext:
        supplier = context["supplier"]
        checks = ["identity verification", "compliance screening", "business stability", "delivery continuity"]
        if supplier.get("annual_spend", 0) >= 1000000:
            checks.append("high value procurement approval")
        context["plan"] = {"checks": checks, "priority": "high" if len(checks) > 4 else "standard"}
        self.event(context["task_id"], "completed", f"已生成尽调计划，共包含 {len(checks)} 个检查项。", [])
        return context

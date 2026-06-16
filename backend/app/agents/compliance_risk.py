from app.agents.base import AgentContext, BaseAgent
from app.repositories import add_assessment
from app.tools.rag_policy import RAGPolicyTool
from app.tools.risk_rules import RiskRuleTool


class ComplianceRiskAgent(BaseAgent):
    name = "ComplianceRiskAgent"

    def __init__(self) -> None:
        self.rag_tool = RAGPolicyTool()
        self.rule_tool = RiskRuleTool()

    def run(self, context: AgentContext) -> AgentContext:
        query = " ".join([context["supplier"]["industry"], context["supplier"]["region"], "sanction bribery compliance risk rating"])
        policies = self.rag_tool.retrieve(query)
        risk = self.rule_tool.assess(context["evidence"], context["supplier"])
        context["policies"] = policies
        context["risk"] = risk
        compliance = next(d for d in risk["dimensions"] if d["dimension"] == "compliance")
        add_assessment(context["task_id"], compliance)
        self.event(
            context["task_id"],
            "completed",
            f"合规风险评估完成，等级为 {compliance['level']}，评分为 {compliance['score']}。",
            [{"tool": self.rag_tool.name, "matches": len(policies)}, {"tool": self.rule_tool.name}],
        )
        return context


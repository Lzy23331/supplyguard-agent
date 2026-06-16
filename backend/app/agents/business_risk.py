from app.agents.base import AgentContext, BaseAgent


class BusinessRiskAgent(BaseAgent):
    name = "BusinessRiskAgent"

    BUSINESS_DIMENSIONS = {"business", "delivery", "completeness", "reputation"}

    def run(self, context: AgentContext) -> AgentContext:
        try:
            self.started(context, "开始整理经营、交付、资料完整性和声誉风险结论。")
            risk = context["risk"]
            dimensions = [d for d in risk.get("dimensions", []) if d.get("dimension") in self.BUSINESS_DIMENSIONS]
            triggered_rules = [r for r in risk.get("triggered_rules", []) if r.get("dimension") in self.BUSINESS_DIMENSIONS]
            evidence_titles = [item.get("title") for item in context.get("evidence", [])]
            context["business_summary"] = {
                "dimensions": dimensions,
                "triggered_rules": triggered_rules,
                "evidence_titles": evidence_titles,
                "conclusion": "经营与交付风险已结合采购暴露、交付记录、争议状态和资料透明度完成分析。",
            }
            self.completed(context, f"经营与交付风险分析完成，涉及 {len(dimensions)} 个维度、{len(triggered_rules)} 条命中规则。")
            return context
        except Exception as exc:  # pragma: no cover
            self.failed(context, f"经营风险分析失败：{exc}")
            raise

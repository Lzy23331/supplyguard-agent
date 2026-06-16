from app.agents.base import AgentContext, BaseAgent


class IntakeAgent(BaseAgent):
    name = "IntakeAgent"

    def run(self, context: AgentContext) -> AgentContext:
        try:
            self.started(context, "开始读取供应商基础资料并生成尽调计划。")
            supplier = context["supplier"]
            checks = ["主体身份核验", "合规名单筛查", "经营稳定性评估", "交付连续性评估"]
            key_concerns = []
            if supplier.get("annual_spend", 0) >= 1000000 or supplier.get("procurement_amount", 0) >= 1000000:
                checks.append("高额采购审批")
                key_concerns.append("采购金额较高，需要关注集中采购暴露。")
            if supplier.get("region") == "境外":
                checks.append("境外供应商合规筛查")
                key_concerns.append("境外主体需要关注制裁、出口管制和受益所有人透明度。")
            if supplier.get("profile_completeness") in {"中", "低"}:
                checks.append("补充材料核验")
                key_concerns.append("资料完整性不足，可能提高准入不确定性。")

            plan = {
                "checks": checks,
                "priority": "high" if len(checks) >= 6 else "standard",
                "tools_to_use": ["MockSearchTool", "RAGPolicyTool", "RiskRuleTool", "ReportExportTool"],
                "key_concerns": key_concerns or ["当前资料完整，按标准准入流程复核。"],
                "reason": "根据采购金额、地区、资料完整性和合作类型确定尽调范围。",
            }
            context["plan"] = plan
            context["diligence_plan"] = plan
            self.completed(context, f"已生成尽调计划，包含 {len(checks)} 个检查项。")
            return context
        except Exception as exc:  # pragma: no cover - defensive event trail
            self.failed(context, f"尽调计划生成失败：{exc}")
            raise

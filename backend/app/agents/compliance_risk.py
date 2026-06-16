from app.agents.base import AgentContext, BaseAgent
from app.repositories import add_assessment, save_risk_assessment
from app.tools.rag_policy import RAGPolicyTool
from app.tools.risk_rules import RiskRuleTool


class ComplianceRiskAgent(BaseAgent):
    name = "ComplianceRiskAgent"

    def __init__(self) -> None:
        self.rag_tool = RAGPolicyTool()
        self.rule_tool = RiskRuleTool()

    def _policy_query(self, supplier: dict) -> str:
        sample_key = supplier.get("sample_key")
        if sample_key == "high" or supplier.get("region") == "境外" or supplier.get("urgency") == "紧急":
            return "制裁名单 黑名单 观察名单 出口管制 境外供应商 受益所有人 信息不透明 紧急采购 升级审批 拒绝准入"
        if sample_key == "medium" or supplier.get("profile_completeness") == "中":
            return "交付延期 合同争议 付款纠纷 补充材料 人工复核 高额采购"
        return "标准准入 资料完整 年度复查 合规筛查 供应商准入"

    def run(self, context: AgentContext) -> AgentContext:
        try:
            self.started(context, "开始检索政策依据并执行规则风险评分。")
            supplier = context["supplier"]
            query = self._policy_query(supplier)
            policies = self.rag_tool.retrieve(query, top_k=5)
            self.tool_called(
                context,
                self.rag_tool.name,
                {"query": query, "top_k": 5},
                f"返回 {len(policies)} 条政策片段。",
            )
            risk = self.rule_tool.assess(context["evidence"], supplier)
            self.tool_called(
                context,
                self.rule_tool.name,
                {"supplier_id": supplier.get("id"), "evidence_count": len(context["evidence"])},
                f"raw_score={risk.get('raw_score')}，total_score={risk.get('total_score')}，risk_level={risk.get('risk_level')}，命中 {len(risk.get('triggered_rules', []))} 条规则。",
            )
            save_risk_assessment(context["task_id"], risk)
            for dimension in risk.get("dimensions", []):
                add_assessment(context["task_id"], dimension)

            compliance_dimension = next((d for d in risk.get("dimensions", []) if d.get("dimension") == "compliance"), None)
            context["policies"] = policies
            context["policy_chunks"] = policies
            context["risk"] = risk
            context["risk_assessment"] = risk
            context["compliance_summary"] = {
                "level": compliance_dimension.get("level") if compliance_dimension else risk.get("risk_level"),
                "score": compliance_dimension.get("score") if compliance_dimension else risk.get("total_score"),
                "key_rules": [r for r in risk.get("triggered_rules", []) if r.get("dimension") == "compliance"],
                "policy_matches": policies,
            }
            self.completed(
                context,
                f"风险评分完成：{risk.get('risk_level')} / {risk.get('total_score')}，原始累计分 {risk.get('raw_score')}。",
            )
            return context
        except Exception as exc:  # pragma: no cover
            self.failed(context, f"合规风险评估失败：{exc}")
            raise

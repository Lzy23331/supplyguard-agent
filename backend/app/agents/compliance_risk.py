from app.agents.base import AgentContext, BaseAgent
from app.repositories import add_assessment, save_risk_assessment
from app.tools.rag_policy import RAGPolicyTool
from app.tools.risk_rules import RiskRuleTool


class ComplianceRiskAgent(BaseAgent):
    name = "ComplianceRiskAgent"

    def __init__(self) -> None:
        self.rag_tool = RAGPolicyTool()
        self.rule_tool = RiskRuleTool()

    def _policy_query(self, supplier: dict, risk: dict) -> str:
        triggered = risk.get("triggered_rules") or []
        actual_rules = [rule for rule in triggered if rule.get("actual_risk")]
        rule_ids = {str(rule.get("rule_id") or rule.get("rule") or "") for rule in actual_rules}

        if rule_ids & {"sanction_or_blacklist"}:
            return "制裁名单 黑名单 观察名单 出口管制 升级审批 拒绝准入 证据链"
        if rule_ids & {"major_dishonesty", "serious_administrative_penalty", "bribery_or_fraud"}:
            return "失信 被执行 行政处罚 商业贿赂 欺诈 合规复核 升级审批"
        if rule_ids & {"business_abnormal", "multiple_contract_disputes", "multiple_payment_disputes", "multiple_late_delivery", "negative_media_single", "negative_media_multiple"}:
            return "经营异常 合同争议 付款纠纷 交付延期 负面舆情 人工复核"

        spend = float(supplier.get("procurement_amount") or supplier.get("annual_spend") or 0)
        if spend >= 1000000:
            return "资料完整性 高额采购 受益所有人 人工复核 补充材料 采购暴露"
        return "标准准入 资料完整 年度复查 合规筛查 供应商准入"

    def run(self, context: AgentContext) -> AgentContext:
        try:
            self.started(context, "开始执行规则风险评分并检索匹配政策依据。")
            supplier = context["supplier"]
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

            query = self._policy_query(supplier, risk)
            if risk.get("actual_risk_rule_count", 0) == 0:
                policies = self.rag_tool.retrieve(query, top_k=5)
                rewritten_queries = [query]
                rewrite_used = False
            else:
                policies, rewritten_queries, rewrite_used = self.rag_tool.retrieve_with_query_rewrite(
                    task_id=context["task_id"],
                    supplier_profile=supplier,
                    evidence_items=context.get("evidence", []),
                    fallback_query=query,
                    top_k=5,
                )
            self.tool_called(
                context,
                self.rag_tool.name,
                {"query": query, "rewritten_queries": rewritten_queries, "top_k": 5},
                f"返回 {len(policies)} 条政策片段。",
            )
            self.event(
                context["task_id"],
                "query_rewrite",
                "completed",
                "已完成政策检索 query rewrite。" if rewrite_used else "query rewrite 不可用，已回退到规则匹配关键词检索。",
                tool_name="LLMTaskService.rewrite_policy_queries",
                tool_input={"evidence_count": len(context.get("evidence", [])), "fallback_query": query},
                tool_output_summary="；".join(rewritten_queries)[:1000],
            )

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


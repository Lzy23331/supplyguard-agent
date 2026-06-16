from typing import Any


class ReportExportTool:
    name = "ReportExportTool"
    LEVEL_LABELS = {"low": "低风险", "medium": "中风险", "high": "高风险"}
    DIMENSION_LABELS = {
        "compliance": "合规风险",
        "business": "经营风险",
        "delivery": "交付风险",
        "completeness": "资料完整性",
        "reputation": "声誉风险",
    }
    SEVERITY_LABELS = {"info": "信息", "warning": "预警", "critical": "严重"}

    def _dimension_table(self, risk: dict[str, Any]) -> str:
        lines = ["| 风险维度 | 分数 | 等级 | 判断依据 |", "| --- | ---: | --- | --- |"]
        for item in risk.get("dimensions", []):
            lines.append(
                f"| {self.DIMENSION_LABELS.get(item.get('dimension'), item.get('dimension'))} "
                f"| {item.get('score')} | {self.LEVEL_LABELS.get(item.get('level'), item.get('level'))} "
                f"| {item.get('rationale')} |"
            )
        return "\n".join(lines)

    def _triggered_rules(self, risk: dict[str, Any]) -> str:
        rules = risk.get("triggered_rules") or risk.get("hit_rules") or []
        if not rules:
            return "- 未命中加分规则。"
        lines = []
        for item in rules:
            rule_name = item.get("rule_name") or item.get("rule")
            score = item.get("score") or item.get("points")
            dimension = self.DIMENSION_LABELS.get(item.get("dimension"), item.get("dimension"))
            evidence = item.get("evidence_ids") or item.get("evidence_source") or item.get("reason")
            lines.append(f"- `{item.get('rule_id', rule_name)}` {rule_name}（{dimension}，+{score}）：证据来源 {evidence}")
        return "\n".join(lines)

    def _evidence_lines(self, evidence: list[dict[str, Any]]) -> str:
        if not evidence:
            return "- 暂无证据。"
        return "\n".join(
            f"- **{item.get('title')}** [{self.SEVERITY_LABELS.get(item.get('severity', 'info'), item.get('severity', 'info'))}]：{item.get('content')}"
            for item in evidence
        )

    def _policy_lines(self, policies: list[dict[str, Any]]) -> str:
        if not policies:
            return "- 未检索到明确政策片段，建议人工复核政策库。"
        lines = []
        for item in policies:
            doc = item.get("doc_name") or item.get("document")
            section = item.get("section_title") or "相关条款"
            keywords = "、".join(item.get("matched_keywords") or item.get("keywords") or [])
            content = (item.get("content") or item.get("chunk") or "").strip().replace("\n", " ")
            excerpt = content[:220] + ("..." if len(content) > 220 else "")
            lines.append(f"- **{doc} / {section}**（关键词：{keywords or '无'}）：{excerpt}")
        return "\n".join(lines)

    def build_markdown(
        self,
        supplier: dict[str, Any],
        evidence: list[dict[str, Any]],
        risk: dict[str, Any],
        policies: list[dict[str, Any]],
        compliance_summary: dict[str, Any] | None = None,
        business_summary: dict[str, Any] | None = None,
        plan: dict[str, Any] | None = None,
    ) -> str:
        risk_level = self.LEVEL_LABELS.get(risk.get("risk_level"), risk.get("risk_level"))
        raw_score = risk.get("raw_score", risk.get("total_score"))
        total_score = risk.get("total_score")
        cap_note = ""
        if raw_score is not None and total_score is not None and raw_score > total_score:
            cap_note = f"\n\n该供应商原始累计风险分为 **{raw_score}**，超过评分上限，系统按规则将总分截断为 **{total_score} / 100**。"
        checks = "、".join((plan or {}).get("checks", [])) or "标准供应商准入尽调"
        compliance_rules = compliance_summary.get("key_rules", []) if compliance_summary else []
        business_rules = business_summary.get("triggered_rules", []) if business_summary else []

        return f"""# 供应商准入尽调报告

## 1. 基本信息
- 供应商名称：**{supplier.get('name')}**
- 官网：{supplier.get('website') or '未提供'}
- 行业：{supplier.get('industry') or '未提供'}
- 地区：{supplier.get('region') or '未提供'}
- 年采购金额：{supplier.get('annual_spend')}
- 合作类型：{supplier.get('cooperation_type') or '未提供'}
- 尽调范围：{checks}

## 2. 综合结论
- 内部风险等级：**{risk.get('risk_level')}**（前端展示：{risk_level}）
- 综合评分：**{total_score} / 100**
- 准入建议：**{risk.get('recommendation')}**{cap_note}

## 3. 风险评分
{self._dimension_table(risk)}

命中规则：
{self._triggered_rules(risk)}

## 4. 合规风险分析
合规风险重点来自制裁名单、黑名单、出口管制、受益所有人透明度、行政处罚、商业贿赂或欺诈等信号。本次命中合规规则 {len(compliance_rules)} 条，需结合政策片段和证据链判断是否准入、升级审批或拒绝准入。

## 5. 经营与交付风险分析
经营与交付风险重点来自采购暴露、交付延期、合同争议、付款纠纷、资料缺失和补充材料情况。本次命中经营交付类规则 {len(business_rules)} 条，需判断供应商是否具备稳定履约能力。

## 6. 关键证据链
{self._evidence_lines(evidence)}

## 7. 命中政策依据
{self._policy_lines(policies)}

## 8. 准入建议
{risk.get('recommendation')}

## 9. 人工复核建议
- low：资料完整且未发现关键风险时，可按标准准入并纳入年度复查。
- medium：建议补充材料，必要时由采购、法务或合规进行人工复核。
- high：建议拒绝准入或提交升级审批，并保留完整证据链与政策依据。
"""

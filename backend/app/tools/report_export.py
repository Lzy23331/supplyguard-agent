from typing import Any


class ReportExportTool:
    name = "ReportExportTool"
    LEVEL_LABELS = {"low": "低风险", "medium": "中风险", "high": "高风险"}
    DIMENSION_LABELS = {
        "compliance": "合规风险",
        "business": "经营风险",
        "delivery": "交付风险",
        "completeness": "资料完整性",
        "reputation": "舆情风险",
    }
    SEVERITY_LABELS = {"info": "信息", "warning": "预警", "critical": "严重"}
    CHECK_LABELS = {
        "identity verification": "主体身份核验",
        "compliance screening": "合规筛查",
        "business stability": "经营稳定性评估",
        "delivery continuity": "交付连续性评估",
        "high value procurement approval": "高金额采购审批",
    }

    def build_markdown(
        self,
        supplier: dict[str, Any],
        plan: dict[str, Any],
        evidence: list[dict[str, Any]],
        risk: dict[str, Any],
        policies: list[dict[str, Any]],
    ) -> str:
        evidence_lines = "\n".join(
            f"- **{item['title']}** [{self.SEVERITY_LABELS.get(item.get('severity', 'info'), item.get('severity', 'info'))}]: {item['content']}" for item in evidence
        )
        dimension_lines = "\n".join(
            f"| {self.DIMENSION_LABELS.get(d['dimension'], d['dimension'])} | {d['score']} | {self.LEVEL_LABELS.get(d['level'], d['level'])} | {d['rationale']} |" for d in risk["dimensions"]
        )
        hit_rule_lines = "\n".join(
            f"- `{item['rule']}` ({self.DIMENSION_LABELS.get(item['dimension'], item['dimension'])}, +{item['points']}): {item['evidence_source']}" for item in risk.get("hit_rules", [])
        ) or "- 未命中加分规则。"
        policy_lines = "\n".join(f"- `{p['document']}`：{p['chunk'][:180]}..." for p in policies) or "- 未检索到明确政策片段。"
        checks = [self.CHECK_LABELS.get(check, check) for check in plan["checks"]]
        risk_level = self.LEVEL_LABELS.get(risk["risk_level"], risk["risk_level"])
        raw_score_note = ""
        if risk.get("raw_score", risk["total_score"]) > risk["total_score"]:
            raw_score_note = f"\n- 原始累计风险分：**{risk['raw_score']}**，按评分规则截断为 **{risk['total_score']} / 100**。"
        return f"""# 供应商准入尽调报告：{supplier['name']}

## 一、结论摘要

- 风险等级：**{risk_level}**
- 综合评分：**{risk['total_score']} / 100**
- 准入建议：**{risk['recommendation']}**
- 尽调范围：{'、'.join(checks)}{raw_score_note}

## 二、供应商画像

- 官网：{supplier.get('website') or 'N/A'}
- 行业：{supplier.get('industry')}
- 地区：{supplier.get('region')}
- 年采购金额：{supplier.get('annual_spend')}
- 合作类型：{supplier.get('cooperation_type')}

## 三、风险评估

| 风险维度 | 评分 | 等级 | 判断依据 |
| --- | ---: | --- | --- |
{dimension_lines}

## 四、命中规则

{hit_rule_lines}

## 五、证据链

{evidence_lines}

## 六、政策依据

{policy_lines}

## 七、人工复核建议

{risk['recommendation']}
"""

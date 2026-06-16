from typing import Any


class RiskRuleTool:
    name = "RiskRuleTool"

    SIGNAL_SCORES = {
        "sanction_or_blacklist": ("compliance", 40),
        "major_dishonesty": ("compliance", 35),
        "serious_administrative_penalty": ("compliance", 30),
        "bribery_or_fraud": ("compliance", 35),
        "overseas_opaque": ("compliance", 20),
        "business_abnormal": ("business", 25),
        "registration_gaps": ("business", 15),
        "young_high_value_supplier": ("business", 15),
        "high_procurement_amount": ("business", 10),
        "medium_profile_completeness": ("completeness", 5),
        "medium_ownership_transparency": ("completeness", 5),
        "supplementary_performance_materials_missing": ("completeness", 5),
        "multiple_late_delivery": ("delivery", 20),
        "single_late_delivery": ("delivery", 10),
        "multiple_payment_disputes": ("delivery", 20),
        "multiple_contract_disputes": ("delivery", 20),
        "minor_contract_dispute": ("delivery", 10),
        "urgent_incomplete_supplier": ("delivery", 15),
        "website_missing": ("completeness", 5),
        "beneficial_owner_missing": ("completeness", 10),
        "negative_media_multiple": ("reputation", 20),
        "negative_media_single": ("reputation", 10),
    }
    HIGH_TERMS = ["sanction", "制裁", "bribery", "贿赂", "fraud", "欺诈", "重大失信", "blacklist", "黑名单", "watchlist", "观察名单"]
    MEDIUM_TERMS = ["lawsuit", "诉讼", "经营异常", "late delivery", "延期", "补充材料", "dispute", "争议", "纠纷", "complaint", "投诉"]

    def assess(self, evidence: list[dict[str, Any]], supplier: dict[str, Any]) -> dict[str, Any]:
        raw_score = 0
        hit_rules: list[dict[str, Any]] = []
        has_critical = False

        def add_rule(rule: str, dimension: str, points: int, evidence_source: str, rationale: str) -> None:
            nonlocal raw_score, has_critical
            if any(item["rule"] == rule for item in hit_rules):
                return
            raw_score += points
            has_critical = has_critical or points >= 30
            hit_rules.append({"rule": rule, "dimension": dimension, "points": points, "evidence_source": evidence_source, "rationale": rationale, "evidence_ids": []})

        for item in evidence:
            text = f"{item.get('title', '')} {item.get('content', '')}".lower()
            severity = item.get("severity", "info")
            source = item.get("title", "evidence")
            rationale = item.get("economic_rationale", "Evidence triggered a configured risk rule.")
            for signal in item.get("rule_signals", []):
                dimension, points = self.SIGNAL_SCORES.get(signal, ("compliance", 5))
                add_rule(signal, dimension, points, source, rationale)
            if severity == "critical" and any(term.lower() in text for term in self.HIGH_TERMS):
                add_rule("critical_compliance_signal", "compliance", 35, source, "严重证据包含制裁、黑名单、商业贿赂、欺诈或重大失信等合规风险表述。")
            elif severity == "warning" and any(term.lower() in text for term in self.MEDIUM_TERMS):
                add_rule("warning_business_or_delivery_signal", "delivery", 10, source, "预警证据包含诉讼、争议、延期或投诉等经营交付风险表述。")

        spend = supplier.get("procurement_amount") or supplier.get("annual_spend") or 0
        if supplier.get("website") in (None, ""):
            add_rule("website_missing", "completeness", 5, "supplier_profile", "官网缺失会增加主体核验成本和身份不确定性。")
        if not supplier.get("region"):
            add_rule("region_missing", "completeness", 5, "supplier_profile", "地区缺失会增加司法辖区和合同执行判断难度。")
        if not supplier.get("industry"):
            add_rule("industry_missing", "completeness", 5, "supplier_profile", "行业缺失会削弱品类相关风险判断。")
        if not supplier.get("cooperation_type"):
            add_rule("cooperation_type_missing", "completeness", 5, "supplier_profile", "合作类型缺失会影响采购暴露和控制措施设计。")
        if supplier.get("business_status") in {"异常", "信息不透明", "停业", "注销"}:
            add_rule("business_abnormal", "business", 25, "supplier_profile", "经营状态异常或信息不透明会提高交易对手履约失败概率。")
        if supplier.get("profile_completeness") == "低":
            add_rule("registration_gaps", "business", 15, "supplier_profile", "资料完整性低会增加尽调成本和逆向选择风险。")
        if supplier.get("profile_completeness") == "中":
            add_rule("medium_profile_completeness", "completeness", 5, "supplier_profile", "资料完整性中等，准入前需要补充核验材料。")
        if supplier.get("ownership_transparency") == "低":
            add_rule("beneficial_owner_missing", "completeness", 10, "supplier_profile", "受益所有人透明度低会增加问责和制裁筛查难度。")
        if supplier.get("ownership_transparency") == "中":
            add_rule("medium_ownership_transparency", "completeness", 5, "supplier_profile", "受益所有人透明度中等，仍需人工复核剩余不确定性。")
        if (supplier.get("company_age_years") or 99) < 2 and spend >= 1000000:
            add_rule("young_high_value_supplier", "business", 15, "supplier_profile", "成立时间短且采购金额高，会增加供应连续性和议价风险。")
        if spend >= 1000000:
            add_rule("high_procurement_amount", "business", 10, "supplier_profile", "采购暴露越高，替代采购、停供和争议成本越高。")
        if supplier.get("urgency") == "紧急" and supplier.get("profile_completeness") == "低":
            add_rule("urgent_incomplete_supplier", "delivery", 15, "supplier_profile", "紧急采购叠加信息不完整，会削弱议价能力和尽调质量。")

        total = min(raw_score, 100)
        level = "high" if has_critical and total >= 70 else self._level(total)
        dimensions = [
            self._dimension("compliance", self._sum(hit_rules, "compliance"), "覆盖制裁、黑名单、商业贿赂、欺诈、重大失信和境外主体不透明风险。"),
            self._dimension("business", self._sum(hit_rules, "business"), "覆盖经营状态、信息透明度、供应商成熟度和采购金额暴露。"),
            self._dimension("delivery", self._sum(hit_rules, "delivery"), "覆盖交付延期、付款纠纷、合同争议和紧急采购执行风险。"),
            self._dimension("completeness", self._sum(hit_rules, "completeness"), "覆盖主体身份、地区、行业、合作类型和受益所有人资料缺失。"),
            self._dimension("reputation", self._sum(hit_rules, "reputation"), "覆盖负面舆情、客户投诉和公开争议信号。"),
        ]
        recommendation = {
            "low": "建议准入，并按标准年度监控机制持续跟踪。",
            "medium": "建议补充材料后准入，或进入采购负责人/合规负责人人工复核。",
            "high": "建议拒绝准入；如业务必须采购，应升级至合规委员会或管理层审批。",
        }[level]
        dimension_scores = {item["dimension"]: item["score"] for item in dimensions}
        triggered_rules = [
            {
                "rule_id": item["rule"],
                "dimension": item["dimension"],
                "rule_name": item["rule"],
                "score": item["points"],
                "reason": item["rationale"],
                "evidence_ids": item.get("evidence_ids", []),
            }
            for item in hit_rules
        ]
        return {
            "raw_score": raw_score,
            "total_score": total,
            "risk_level": level,
            "recommendation": recommendation,
            "dimensions": dimensions,
            "dimension_scores": dimension_scores,
            "hit_rules": hit_rules,
            "triggered_rules": triggered_rules,
        }

    def _sum(self, hit_rules: list[dict[str, Any]], dimension: str) -> int:
        return min(100, sum(item["points"] for item in hit_rules if item["dimension"] == dimension))

    def _dimension(self, name: str, score: int, rationale: str) -> dict[str, Any]:
        bounded = max(0, min(100, score))
        return {"dimension": name, "score": bounded, "level": self._level(bounded), "rationale": rationale}

    def _level(self, score: int) -> str:
        if score >= 70:
            return "high"
        if score >= 40:
            return "medium"
        return "low"



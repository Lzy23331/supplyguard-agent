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
                add_rule("critical_compliance_signal", "compliance", 35, source, "Critical evidence contains sanctions, blacklist, bribery, fraud or major dishonesty language.")
            elif severity == "warning" and any(term.lower() in text for term in self.MEDIUM_TERMS):
                add_rule("warning_business_or_delivery_signal", "delivery", 10, source, "Warning evidence contains litigation, dispute, delay or complaint language.")

        spend = supplier.get("procurement_amount") or supplier.get("annual_spend") or 0
        if supplier.get("website") in (None, ""):
            add_rule("website_missing", "completeness", 5, "supplier_profile", "Missing website increases verification cost and identity uncertainty.")
        if not supplier.get("region"):
            add_rule("region_missing", "completeness", 5, "supplier_profile", "Missing region makes jurisdiction and enforcement review harder.")
        if not supplier.get("industry"):
            add_rule("industry_missing", "completeness", 5, "supplier_profile", "Missing industry weakens category-specific risk review.")
        if not supplier.get("cooperation_type"):
            add_rule("cooperation_type_missing", "completeness", 5, "supplier_profile", "Missing cooperation type makes exposure and control design unclear.")
        if supplier.get("business_status") in {"异常", "信息不透明", "停业", "注销"}:
            add_rule("business_abnormal", "business", 25, "supplier_profile", "Abnormal or opaque business status increases counterparty failure probability.")
        if supplier.get("profile_completeness") == "低":
            add_rule("registration_gaps", "business", 15, "supplier_profile", "Low profile completeness increases due diligence cost and adverse selection risk.")
        if supplier.get("profile_completeness") == "中":
            add_rule("medium_profile_completeness", "completeness", 5, "supplier_profile", "Medium profile completeness requires supplementary verification before onboarding.")
        if supplier.get("ownership_transparency") == "低":
            add_rule("beneficial_owner_missing", "completeness", 10, "supplier_profile", "Low beneficial ownership transparency makes accountability and sanctions screening harder.")
        if supplier.get("ownership_transparency") == "中":
            add_rule("medium_ownership_transparency", "completeness", 5, "supplier_profile", "Medium ownership transparency leaves residual verification work for human review.")
        if (supplier.get("company_age_years") or 99) < 2 and spend >= 1000000:
            add_rule("young_high_value_supplier", "business", 15, "supplier_profile", "A young supplier with high spend creates continuity and bargaining-power risk.")
        if spend >= 1000000:
            add_rule("high_procurement_amount", "business", 10, "supplier_profile", "Higher procurement exposure increases replacement, interruption and dispute costs.")
        if supplier.get("urgency") == "紧急" and supplier.get("profile_completeness") == "低":
            add_rule("urgent_incomplete_supplier", "delivery", 15, "supplier_profile", "Urgency plus incomplete information weakens negotiation and diligence quality.")

        total = min(raw_score, 100)
        level = "high" if has_critical and total >= 70 else self._level(total)
        dimensions = [
            self._dimension("compliance", self._sum(hit_rules, "compliance"), "Covers sanctions, blacklist, bribery, fraud, major dishonesty and opaque overseas ownership."),
            self._dimension("business", self._sum(hit_rules, "business"), "Covers operating status, information transparency, supplier maturity and procurement exposure."),
            self._dimension("delivery", self._sum(hit_rules, "delivery"), "Covers late delivery, payment disputes, contract disputes and urgent procurement execution risk."),
            self._dimension("completeness", self._sum(hit_rules, "completeness"), "Covers missing identity, geography, category, cooperation and ownership materials."),
            self._dimension("reputation", self._sum(hit_rules, "reputation"), "Covers adverse media, complaints and public dispute signals."),
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


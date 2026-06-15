from typing import Any


class RiskRuleTool:
    name = "RiskRuleTool"

    SIGNAL_SCORES = {
        "sanction_or_blacklist": 40,
        "major_dishonesty": 35,
        "serious_administrative_penalty": 30,
        "bribery_or_fraud": 35,
        "overseas_opaque": 20,
        "business_abnormal": 25,
        "registration_gaps": 15,
        "young_high_value_supplier": 15,
        "high_procurement_amount": 10,
        "multiple_late_delivery": 20,
        "single_late_delivery": 10,
        "multiple_payment_disputes": 20,
        "multiple_contract_disputes": 20,
        "minor_contract_dispute": 10,
        "urgent_incomplete_supplier": 15,
        "website_missing": 5,
        "negative_media_multiple": 20,
        "negative_media_single": 10,
    }
    HIGH_TERMS = ["sanction", "制裁", "bribery", "贿赂", "fraud", "欺诈", "重大失信", "blacklist", "黑名单", "watchlist", "观察名单"]
    MEDIUM_TERMS = ["lawsuit", "诉讼", "经营异常", "late delivery", "延期", "补充材料", "dispute", "争议", "纠纷", "complaint", "投诉"]

    def assess(self, evidence: list[dict[str, Any]], supplier: dict[str, Any]) -> dict[str, Any]:
        score = 0
        hit_rules: list[dict[str, Any]] = []
        has_critical = False

        def add_rule(rule: str, points: int, source: str, rationale: str) -> None:
            nonlocal score, has_critical
            if any(item["rule"] == rule for item in hit_rules):
                return
            score += points
            has_critical = has_critical or points >= 30
            hit_rules.append({"rule": rule, "points": points, "source": source, "rationale": rationale})

        for item in evidence:
            text = f"{item.get('title', '')} {item.get('content', '')}".lower()
            severity = item.get("severity", "info")
            for signal in item.get("rule_signals", []):
                add_rule(
                    signal,
                    self.SIGNAL_SCORES.get(signal, 5),
                    item.get("title", "evidence"),
                    item.get("economic_rationale", "Evidence triggered a configured risk rule."),
                )
            if severity == "critical" and any(term.lower() in text for term in self.HIGH_TERMS):
                add_rule(
                    "critical_compliance_signal",
                    35,
                    item.get("title", "evidence"),
                    "Critical evidence contains sanctions, blacklist, bribery, fraud or major dishonesty language.",
                )
            elif severity == "warning" and any(term.lower() in text for term in self.MEDIUM_TERMS):
                add_rule(
                    "warning_business_or_delivery_signal",
                    10,
                    item.get("title", "evidence"),
                    "Warning evidence contains litigation, dispute, delay or complaint language.",
                )

        spend = supplier.get("procurement_amount") or supplier.get("annual_spend") or 0
        if supplier.get("website") in (None, ""):
            add_rule("website_missing", 5, "supplier_profile", "Missing website increases verification cost and identity uncertainty.")
        if not supplier.get("region"):
            add_rule("region_missing", 5, "supplier_profile", "Missing region makes jurisdiction and enforcement review harder.")
        if not supplier.get("industry"):
            add_rule("industry_missing", 5, "supplier_profile", "Missing industry weakens category-specific risk review.")
        if not supplier.get("cooperation_type"):
            add_rule("cooperation_type_missing", 5, "supplier_profile", "Missing cooperation type makes exposure and control design unclear.")
        if supplier.get("business_status") in {"异常", "信息不透明", "停业", "注销"}:
            add_rule("business_abnormal", 25, "supplier_profile", "Abnormal or opaque business status increases counterparty failure probability.")
        if supplier.get("profile_completeness") == "低":
            add_rule("registration_gaps", 15, "supplier_profile", "Low profile completeness increases due diligence cost and adverse selection risk.")
        if supplier.get("ownership_transparency") == "低":
            add_rule("beneficial_owner_missing", 10, "supplier_profile", "Low beneficial ownership transparency makes accountability and sanctions screening harder.")
        if (supplier.get("company_age_years") or 99) < 2 and spend >= 1000000:
            add_rule("young_high_value_supplier", 15, "supplier_profile", "A young supplier with high spend creates continuity and bargaining-power risk.")
        if spend >= 1000000:
            add_rule("high_procurement_amount", 10, "supplier_profile", "Higher procurement exposure increases replacement, interruption and dispute costs.")
        if supplier.get("urgency") == "紧急" and supplier.get("profile_completeness") == "低":
            add_rule("urgent_incomplete_supplier", 15, "supplier_profile", "Urgency plus incomplete information weakens negotiation and diligence quality.")

        total = min(100, score)
        level = "High" if has_critical and total >= 70 else self._level(total)
        dimensions = [
            self._dimension(
                "Compliance",
                self._sum(hit_rules, {"sanction_or_blacklist", "major_dishonesty", "serious_administrative_penalty", "bribery_or_fraud", "overseas_opaque", "critical_compliance_signal"}),
                "Covers sanctions, blacklist, bribery, fraud, major dishonesty and opaque overseas ownership.",
            ),
            self._dimension(
                "Business",
                self._sum(hit_rules, {"business_abnormal", "registration_gaps", "young_high_value_supplier", "high_procurement_amount", "beneficial_owner_missing", "website_missing"}),
                "Covers operating status, information transparency, supplier maturity and procurement exposure.",
            ),
            self._dimension(
                "Delivery",
                self._sum(hit_rules, {"multiple_late_delivery", "single_late_delivery", "multiple_payment_disputes", "multiple_contract_disputes", "minor_contract_dispute", "urgent_incomplete_supplier", "warning_business_or_delivery_signal"}),
                "Covers late delivery, payment disputes, contract disputes and urgent procurement execution risk.",
            ),
            self._dimension(
                "Completeness",
                self._sum(hit_rules, {"website_missing", "region_missing", "industry_missing", "cooperation_type_missing", "registration_gaps", "beneficial_owner_missing"}),
                "Covers missing identity, geography, category, cooperation and ownership materials.",
            ),
            self._dimension(
                "Reputation",
                self._sum(hit_rules, {"negative_media_multiple", "negative_media_single", "warning_business_or_delivery_signal"}),
                "Covers adverse media, complaints and public dispute signals.",
            ),
        ]
        recommendation = {
            "Low": "建议准入，并按标准年度监控机制持续跟踪。",
            "Medium": "建议补充材料后准入，或进入采购负责人/合规负责人人工复核。",
            "High": "建议拒绝准入；如业务必须采购，应升级至合规委员会或管理层审批。",
        }[level]
        return {
            "total_score": total,
            "risk_level": level,
            "recommendation": recommendation,
            "dimensions": dimensions,
            "hit_rules": hit_rules,
        }

    def _sum(self, hit_rules: list[dict[str, Any]], names: set[str]) -> int:
        return min(100, sum(item["points"] for item in hit_rules if item["rule"] in names))

    def _dimension(self, name: str, score: int, rationale: str) -> dict[str, Any]:
        bounded = max(0, min(100, score))
        return {"dimension": name, "score": bounded, "level": self._level(bounded), "rationale": rationale}

    def _level(self, score: int) -> str:
        if score >= 70:
            return "High"
        if score >= 40:
            return "Medium"
        return "Low"

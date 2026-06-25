from __future__ import annotations

from typing import Any

from app.services.evidence_scoring_service import EvidenceScoringService


class RiskRuleTool:
    name = "RiskRuleTool"

    SIGNAL_SCORES = {
        "sanction_or_blacklist": ("compliance", 40),
        "major_dishonesty": ("compliance", 35),
        "serious_administrative_penalty": ("compliance", 30),
        "bribery_or_fraud": ("compliance", 35),
        "overseas_opaque": ("compliance", 20),
        "business_abnormal": ("business", 25),
        "registration_gaps": ("business", 12),
        "young_high_value_supplier": ("business", 15),
        "high_procurement_amount": ("business", 10),
        "medium_profile_completeness": ("completeness", 5),
        "medium_ownership_transparency": ("completeness", 5),
        "supplementary_performance_materials_missing": ("completeness", 5),
        "multiple_late_delivery": ("delivery", 20),
        "single_late_delivery": ("delivery", 10),
        "multiple_payment_disputes": ("delivery", 20),
        "multiple_contract_disputes": ("delivery", 10),
        "minor_contract_dispute": ("delivery", 5),
        "urgent_incomplete_supplier": ("delivery", 15),
        "website_missing": ("completeness", 4),
        "region_missing": ("completeness", 4),
        "industry_missing": ("completeness", 4),
        "cooperation_type_missing": ("completeness", 4),
        "beneficial_owner_missing": ("completeness", 8),
        "negative_media_multiple": ("reputation", 20),
        "negative_media_single": ("reputation", 10),
    }
    KEYWORD_SIGNAL_MAP = {
        "administrative_penalty": "serious_administrative_penalty",
        "行政处罚": "serious_administrative_penalty",
        "处罚": "serious_administrative_penalty",
        "dishonesty_enforcement": "major_dishonesty",
        "失信": "major_dishonesty",
        "被执行人": "major_dishonesty",
        "限制高消费": "major_dishonesty",
        "business_abnormality": "business_abnormal",
        "经营异常": "business_abnormal",
        "lawsuit_dispute": "multiple_contract_disputes",
        "诉讼": "multiple_contract_disputes",
        "合同纠纷": "multiple_contract_disputes",
        "付款纠纷": "multiple_payment_disputes",
        "交付争议": "multiple_late_delivery",
        "quality_recall": "single_late_delivery",
        "质量问题": "single_late_delivery",
        "sanction_blacklist": "sanction_or_blacklist",
        "制裁": "sanction_or_blacklist",
        "黑名单": "sanction_or_blacklist",
        "出口管制": "sanction_or_blacklist",
        "negative_public_opinion": "negative_media_single",
        "负面舆情": "negative_media_single",
        "投诉": "negative_media_single",
        "bribery": "bribery_or_fraud",
        "fraud": "bribery_or_fraud",
        "贿赂": "bribery_or_fraud",
        "欺诈": "bribery_or_fraud",
        "overseas_opaque": "overseas_opaque",
        "境外主体": "overseas_opaque",
        "信息不透明": "overseas_opaque",
    }
    HIGH_SIGNALS = {"sanction_or_blacklist", "major_dishonesty", "serious_administrative_penalty", "bribery_or_fraud"}
    INFO_ONLY_SIGNALS = {"high_procurement_amount", "supplementary_performance_materials_missing", "website_missing", "region_missing", "industry_missing", "cooperation_type_missing", "medium_profile_completeness", "medium_ownership_transparency", "registration_gaps", "beneficial_owner_missing", "young_high_value_supplier", "urgent_incomplete_supplier"}
    PROFILE_COMPLETION_FIELDS = {
        "website": {"website", "homepage"},
        "region": {"region", "address", "registered_address"},
        "industry": {"industry", "business_scope", "description"},
        "registration": {"company_full_name", "unified_social_credit_code", "registered_capital", "established_date", "business_status"},
    }

    def __init__(self) -> None:
        self.evidence_scoring = EvidenceScoringService()

    def assess(self, evidence: list[dict[str, Any]], supplier: dict[str, Any]) -> dict[str, Any]:
        raw_score = 0
        hit_rules: list[dict[str, Any]] = []
        has_critical = False
        actual_risk_rule_count = 0

        def add_rule(rule: str, dimension: str, points: int, evidence_source: str, rationale: str, *, actual_risk: bool = False) -> None:
            nonlocal raw_score, has_critical, actual_risk_rule_count
            if any(item["rule"] == rule for item in hit_rules):
                return
            raw_score += points
            has_critical = has_critical or (actual_risk and points >= 30)
            actual_risk_rule_count += 1 if actual_risk else 0
            hit_rules.append({"rule": rule, "dimension": dimension, "points": points, "evidence_source": evidence_source, "rationale": rationale, "actual_risk": actual_risk, "evidence_ids": []})

        for item in evidence:
            should_score, reason = self.evidence_scoring.should_score(item)
            if not should_score:
                continue
            source = item.get("title") or item.get("source_name") or "evidence"
            rationale = item.get("economic_rationale") or "证据包含明确风险信号，按规则纳入评分。"
            signals = [*self._list(item.get("rule_signals")), *self.normalize_risk_keywords(item)]
            for signal in dict.fromkeys(signals):
                dimension, points = self.SIGNAL_SCORES.get(signal, ("compliance", 5))
                add_rule(signal, dimension, points, source, rationale, actual_risk=signal not in self.INFO_ONLY_SIGNALS)
            if item.get("severity") == "critical" and not signals:
                add_rule("critical_unclassified_signal", "compliance", 20, source, f"严重级别证据通过过滤：{reason}", actual_risk=True)

        spend = float(supplier.get("procurement_amount") or supplier.get("annual_spend") or 0)
        if not self._profile_completed(supplier, "website"):
            add_rule("website_missing", "completeness", 4, "supplier_profile", "官网缺失增加主体核验成本，但不等同实质经营风险。")
        if not self._profile_completed(supplier, "region"):
            add_rule("region_missing", "completeness", 4, "supplier_profile", "地区或注册地址缺失增加人工核验成本，但不等同实质经营风险。")
        if not self._profile_completed(supplier, "industry"):
            add_rule("industry_missing", "completeness", 4, "supplier_profile", "行业缺失影响品类风险判断，但不单独构成高风险。")
        if not supplier.get("cooperation_type"):
            add_rule("cooperation_type_missing", "completeness", 4, "supplier_profile", "合作类型缺失影响控制措施设计。")

        profile_completed_count = self._profile_completed_count(supplier)
        if self._profile_low(supplier) and profile_completed_count < 3:
            add_rule("registration_gaps", "business", 12, "supplier_profile", "主体基础资料不足，需要补充材料或人工复核。")
        elif self._profile_medium(supplier):
            add_rule("medium_profile_completeness", "completeness", 5, "supplier_profile", "主体资料完整性中等，建议准入前补充核验。")

        if self._ownership_medium(supplier):
            add_rule("medium_ownership_transparency", "completeness", 5, "supplier_profile", "受益所有人透明度中等，建议人工复核。")
        if self._ownership_low(supplier) and (self._is_overseas_or_opaque(supplier) or spend >= 1000000):
            add_rule("beneficial_owner_missing", "completeness", 8, "supplier_profile", "受益所有人信息不足，仅在境外、信息不透明或高额采购场景下加权。")

        if self._business_abnormal(supplier):
            add_rule("business_abnormal", "business", 25, "supplier_profile", "经营状态异常或信息不透明会显著提高履约不确定性。", actual_risk=True)
        if (supplier.get("company_age_years") or 99) < 2 and spend >= 1000000:
            add_rule("young_high_value_supplier", "business", 15, "supplier_profile", "成立时间较短且采购金额较高，需要增强履约核验。")
        if spend >= 1000000:
            add_rule("high_procurement_amount", "business", 10, "supplier_profile", "采购金额较高代表暴露度较高，但不单独代表供应商存在重大风险。")
        if self._is_urgent(supplier) and self._profile_low(supplier):
            add_rule("urgent_incomplete_supplier", "delivery", 15, "supplier_profile", "紧急采购叠加资料不足会削弱议价和核验质量。")

        total = min(raw_score, 100)
        if actual_risk_rule_count == 0:
            total = min(total, 45)
        level = "high" if has_critical and total >= 70 else self._level(total)
        dimensions = [
            self._dimension("compliance", self._sum(hit_rules, "compliance"), "制裁、黑名单、失信、行政处罚、贿赂欺诈等明确合规风险。"),
            self._dimension("business", self._sum(hit_rules, "business"), "经营状态、主体成熟度、资料缺口和采购暴露。"),
            self._dimension("delivery", self._sum(hit_rules, "delivery"), "交付延期、付款纠纷、合同争议和紧急采购执行风险。"),
            self._dimension("completeness", self._sum(hit_rules, "completeness"), "官网、地区、行业、合作类型、受益所有人等资料完整性。"),
            self._dimension("reputation", self._sum(hit_rules, "reputation"), "负面舆情、投诉和公开争议信号。"),
        ]
        recommendation = self._recommendation(level, actual_risk_rule_count)
        return {
            "raw_score": raw_score,
            "total_score": total,
            "risk_level": level,
            "recommendation": recommendation,
            "dimensions": dimensions,
            "dimension_scores": {item["dimension"]: item["score"] for item in dimensions},
            "hit_rules": hit_rules,
            "triggered_rules": [
                {
                    "rule_id": item["rule"],
                    "dimension": item["dimension"],
                    "rule_name": item["rule"],
                    "score": item["points"],
                    "reason": item["rationale"],
                    "evidence_ids": item.get("evidence_ids", []),
                    "actual_risk": item.get("actual_risk", False),
                }
                for item in hit_rules
            ],
            "actual_risk_rule_count": actual_risk_rule_count,
        }

    def normalize_risk_keywords(self, item: dict[str, Any]) -> list[str]:
        metadata = item.get("metadata_json") or item.get("metadata") or {}
        raw_keywords = item.get("risk_keywords") or item.get("matched_risk_keywords") or metadata.get("risk_keywords") or []
        text_parts = [*self._list(raw_keywords), item.get("title", ""), item.get("content", ""), item.get("raw_text", "")]
        text = " ".join(str(value) for value in text_parts).lower()
        signals: list[str] = []
        for keyword, signal in self.KEYWORD_SIGNAL_MAP.items():
            if keyword.lower() in text and signal not in signals:
                signals.append(signal)
        return signals

    def _profile_completed(self, supplier: dict[str, Any], group: str) -> bool:
        if group == "website" and supplier.get("website"):
            return True
        if group == "region" and (supplier.get("region") or supplier.get("registered_address") or supplier.get("address")):
            return True
        if group == "industry" and (supplier.get("industry") or supplier.get("business_scope") or supplier.get("description")):
            return True
        fields = supplier.get("company_profile") or supplier.get("company_profile_snapshots") or []
        wanted = self.PROFILE_COMPLETION_FIELDS.get(group, set())
        for item in fields:
            if item.get("field_name") in wanted and item.get("field_value") and (item.get("confidence") or 0) >= 0.5:
                return True
        return False

    def _profile_completed_count(self, supplier: dict[str, Any]) -> int:
        groups = ["website", "region", "industry", "registration"]
        count = sum(1 for group in groups if self._profile_completed(supplier, group))
        fields = supplier.get("company_profile") or supplier.get("company_profile_snapshots") or []
        registration_hits = {item.get("field_name") for item in fields if item.get("field_value") and (item.get("confidence") or 0) >= 0.5}
        if registration_hits & self.PROFILE_COMPLETION_FIELDS["registration"]:
            count += 1 if not self._profile_completed(supplier, "registration") else 0
        return count

    def _profile_low(self, supplier: dict[str, Any]) -> bool:
        return supplier.get("profile_completeness") in {"低", "low", "浣?"} or supplier.get("sample_key") == "high"

    def _profile_medium(self, supplier: dict[str, Any]) -> bool:
        return supplier.get("profile_completeness") in {"中", "medium", "涓?"} or supplier.get("sample_key") == "medium"

    def _ownership_low(self, supplier: dict[str, Any]) -> bool:
        return supplier.get("ownership_transparency") in {"低", "low", "浣?"} or supplier.get("sample_key") == "high"

    def _ownership_medium(self, supplier: dict[str, Any]) -> bool:
        return supplier.get("ownership_transparency") in {"中", "medium", "涓?"} or supplier.get("sample_key") == "medium"

    def _business_abnormal(self, supplier: dict[str, Any]) -> bool:
        status = str(supplier.get("business_status") or "")
        return any(term in status for term in ["异常", "信息不透明", "停业", "注销", "吊销", "淇℃伅涓嶉€忔槑"])

    def _is_overseas_or_opaque(self, supplier: dict[str, Any]) -> bool:
        text = " ".join(str(supplier.get(key) or "") for key in ["region", "summary", "business_status"])
        return any(term in text for term in ["境外", "海外", "信息不透明", "澧冨", "淇℃伅涓嶉€忔槑"])

    def _is_urgent(self, supplier: dict[str, Any]) -> bool:
        text = " ".join(str(supplier.get(key) or "") for key in ["urgency", "cooperation_type", "summary"])
        return any(term in text for term in ["紧急", "urgent", "绱ф€"])

    def _list(self, value: Any) -> list[str]:
        if not value:
            return []
        if isinstance(value, str):
            return [part.strip() for part in value.replace("，", ",").replace(";", ",").split(",") if part.strip()]
        return [str(item).strip() for item in value if str(item).strip()]

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

    def _recommendation(self, level: str, actual_risk_rule_count: int) -> str:
        if level == "high":
            return "建议拒绝准入或提交升级审批；如业务必须采购，应由合规、法务和采购负责人联合复核明确风险证据。"
        if level == "medium":
            if actual_risk_rule_count == 0:
                return "建议补充资料并人工复核；当前主要是信息完整性或采购暴露问题，未发现明确高风险证据。"
            return "建议补充材料后准入或进入采购负责人/合规负责人复核，重点核验已命中的实际风险证据。"
        return "建议准入，并保留联网搜索记录和企业画像字段，纳入常规年度复查。"



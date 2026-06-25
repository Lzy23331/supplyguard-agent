from __future__ import annotations

from typing import Any


class EvidenceScoringService:
    """Classify whether an evidence item is allowed to affect the risk score."""

    name = "EvidenceScoringService"
    OBSERVATION_KEYWORDS = {
        "观察性风险",
        "无明显风险",
        "未发现明显风险",
        "search_observation",
        "no_obvious_risk",
        "普通搜索记录",
    }
    NON_RISK_TEXT = (
        "未发现明确高风险",
        "未发现明显风险",
        "企业简介",
        "企业介绍",
        "百科",
        "官网",
        "招聘",
        "产品页",
        "普通搜索记录",
    )

    def should_score(self, item: dict[str, Any]) -> tuple[bool, str]:
        metadata = item.get("metadata_json") or item.get("metadata") or {}
        source_type = item.get("source_type") or ("mock_sample" if item.get("source") else "unknown")
        explicit = item.get("should_use_for_scoring")
        if explicit is None:
            explicit = metadata.get("should_use_for_scoring")
        if explicit in (False, 0, "0"):
            return False, "explicitly_not_for_scoring"

        keywords = self._keywords(item)
        text = " ".join(str(item.get(key) or "") for key in ["title", "content", "raw_text", "snippet"])
        if self._is_observation(keywords, text):
            return False, "observation_or_no_obvious_risk"
        if not keywords and not item.get("rule_signals"):
            return False, "no_structured_risk_signal"

        if source_type == "web_search":
            url = item.get("source_url") or item.get("url")
            if not url or str(url).strip() in {"未提供", "None", "null"}:
                return False, "missing_source_url"
            entity_score = metadata.get("entity_match_score", item.get("entity_match_score"))
            if isinstance(entity_score, (int, float)) and entity_score < 0.6:
                return False, "entity_match_below_threshold"
            confidence = item.get("confidence", metadata.get("confidence"))
            if isinstance(confidence, (int, float)) and confidence < 0.5:
                return False, "confidence_below_threshold"
            if not keywords and not item.get("rule_signals"):
                return False, "no_risk_signal"

        confidence = item.get("confidence", metadata.get("confidence"))
        if isinstance(confidence, (int, float)) and confidence < 0.5 and item.get("severity") != "critical":
            return False, "confidence_below_threshold"
        return True, "actual_risk_evidence"

    def _keywords(self, item: dict[str, Any]) -> list[str]:
        metadata = item.get("metadata_json") or item.get("metadata") or {}
        raw = item.get("risk_keywords") or item.get("matched_risk_keywords") or metadata.get("risk_keywords") or []
        if isinstance(raw, str):
            return [part.strip() for part in raw.replace("，", ",").replace(";", ",").split(",") if part.strip()]
        return [str(value).strip() for value in raw if str(value).strip()]

    def _is_observation(self, keywords: list[str], text: str) -> bool:
        joined = " ".join(keywords)
        if any(keyword in joined for keyword in self.OBSERVATION_KEYWORDS):
            return True
        return any(phrase in text for phrase in self.NON_RISK_TEXT)


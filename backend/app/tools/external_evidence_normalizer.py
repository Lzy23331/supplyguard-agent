from typing import Any


class ExternalEvidenceNormalizer:
    name = "ExternalEvidenceNormalizer"

    def normalize(self, candidate: dict[str, Any] | Any, provider_name: str, source_type: str) -> dict[str, Any]:
        if hasattr(candidate, "model_dump"):
            candidate = candidate.model_dump()
        metadata = candidate.get("metadata_json") or candidate.get("metadata") or {}
        keywords = candidate.get("risk_keywords") or []
        if isinstance(keywords, str):
            keywords = [part.strip() for part in keywords.replace("；", ",").replace(";", ",").replace("，", ",").split(",") if part.strip()]
        confidence = candidate.get("confidence")
        if confidence is None:
            confidence = 0.65
        should_score = metadata.get("should_use_for_scoring")
        if should_score is None:
            should_score = bool(confidence >= 0.5 or candidate.get("severity") == "critical")
        content = candidate.get("content") or candidate.get("raw_text") or candidate.get("title") or "外部证据候选项"
        candidate_id = candidate.get("id")
        return {
            "id": f"{provider_name}:{candidate_id}" if candidate_id else None,
            "source": source_type,
            "source_type": source_type,
            "source_name": candidate.get("source_name") or provider_name,
            "source_url": candidate.get("source_url"),
            "category": candidate.get("category") or "external_evidence",
            "title": candidate.get("title") or "外部证据",
            "content": content,
            "normalized_content": candidate.get("normalized_content") or content,
            "severity": candidate.get("severity") or "info",
            "risk_keywords": keywords,
            "confidence": float(confidence),
            "raw_text": candidate.get("raw_text") or content,
            "extracted_by": provider_name,
            "should_use_for_scoring": should_score,
            "economic_rationale": candidate.get("economic_rationale") or "外部证据源命中供应商风险信号，需纳入准入评分和人工复核。",
            "metadata_json": {
                "provider": provider_name,
                "risk_keywords": keywords,
                "should_use_for_scoring": should_score,
                **metadata,
            },
        }

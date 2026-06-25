import json
import time
from typing import Any

from app.config import get_settings
from app.llm.llm_factory import create_llm_client
from app.llm.prompts.evidence_extraction_prompt import SYSTEM_PROMPT, build_user_prompt
from app.services.llm_audit_service import log_llm_call


class EvidenceExtractionTool:
    name = "EvidenceExtractionTool"

    KEYWORD_RULES = [
        ("制裁", "compliance", "sanction_or_blacklist", "critical", 0.90),
        ("疑似制裁", "compliance", "sanction_or_blacklist", "critical", 0.90),
        ("黑名单", "compliance", "sanction_or_blacklist", "critical", 0.90),
        ("重大失信", "compliance", "major_dishonesty", "critical", 0.88),
        ("行政处罚", "compliance", "serious_administrative_penalty", "warning", 0.82),
        ("经营异常", "business", "business_abnormal", "warning", 0.80),
        ("交付延期", "delivery", "multiple_late_delivery", "warning", 0.78),
        ("交付争议", "delivery", "multiple_contract_disputes", "warning", 0.76),
        ("付款纠纷", "delivery", "multiple_payment_disputes", "warning", 0.78),
        ("付款争议", "delivery", "multiple_payment_disputes", "warning", 0.78),
        ("合同争议", "delivery", "multiple_contract_disputes", "warning", 0.76),
        ("合同纠纷", "delivery", "multiple_contract_disputes", "warning", 0.76),
        ("负面新闻", "reputation", "negative_media_single", "warning", 0.72),
        ("资料缺失", "completeness", "registration_gaps", "warning", 0.75),
        ("主体信息不完整", "completeness", "registration_gaps", "warning", 0.75),
        ("注册信息披露不完整", "completeness", "registration_gaps", "warning", 0.75),
        ("最终受益所有人", "completeness", "beneficial_owner_missing", "warning", 0.80),
        ("受益所有人", "completeness", "beneficial_owner_missing", "warning", 0.80),
        ("合规声明", "completeness", "registration_gaps", "warning", 0.75),
        ("官网缺失", "completeness", "website_missing", "info", 0.70),
        ("成立时间短", "business", "young_high_value_supplier", "warning", 0.70),
        ("预付款", "delivery", "multiple_payment_disputes", "warning", 0.70),
    ]

    def extract_evidence_from_text(
        self,
        supplier_profile: dict[str, Any],
        material_text: str,
        task_id: str | None = None,
        db=None,
        source_type: str = "user_input",
        source_name: str = "用户粘贴材料",
        source_url: str | None = None,
    ) -> list[dict[str, Any]]:
        text = (material_text or "").strip()
        if not text:
            return []
        text = text[:20000]
        if (get_settings().model_mode or "mock").lower() != "llm":
            items = self._keyword_extract(text, extracted_by="MockKeywordExtractor", source_type=source_type, source_name=source_name, source_url=source_url)
            self._log_keyword_fallback(db, task_id, supplier_profile, text, items, "MODEL_MODE is not llm")
            return items
        start = time.perf_counter()
        user_prompt = build_user_prompt(supplier_profile, text)
        try:
            bundle = create_llm_client()
            raw = bundle.client.complete_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                task_type="evidence_extraction",
            )
            items = self._normalize_llm_items(raw.get("evidence_items", []), text, source_type=source_type, source_name=source_name, source_url=source_url)
            log_llm_call(
                db,
                task_id,
                "EvidenceExtractionTool",
                "evidence_extraction",
                bundle.actual_model_mode,
                bundle.model_name,
                "evidence_extraction_prompt",
                self._summary({"supplier": supplier_profile, "material_length": len(text)}),
                self._summary({"evidence_count": len(items), "evidence_items": items}),
                True,
                bundle.fallback_used,
                bundle.fallback_reason,
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
            return items
        except Exception as exc:
            items = self._keyword_extract(text, extracted_by="MockKeywordExtractor", source_type=source_type, source_name=source_name, source_url=source_url)
            log_llm_call(
                db,
                task_id,
                "EvidenceExtractionTool",
                "evidence_extraction",
                "mock",
                "mock-keyword-extractor",
                "evidence_extraction_prompt",
                self._summary({"supplier": supplier_profile, "material_length": len(text)}),
                self._summary({"evidence_count": len(items), "evidence_items": items}),
                True,
                True,
                f"Fallback to keyword extraction after LLM failure: {exc}",
                error_message=str(exc),
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
            return items

    def _keyword_extract(self, text: str, extracted_by: str, source_type: str = "user_input", source_name: str = "用户粘贴材料", source_url: str | None = None) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for keyword, risk_type, signal, severity, confidence in self.KEYWORD_RULES:
            index = text.find(keyword)
            if index < 0:
                continue
            if self._is_negated(text, index):
                continue
            quote = self._quote(text, index, len(keyword))
            items.append(
                self._item(
                    title=f"用户材料提及{keyword}",
                    content=f"用户材料显示供应商存在“{keyword}”相关风险信号。",
                    risk_type=risk_type,
                    risk_keywords=[keyword],
                    rule_signals=[signal],
                    severity=severity,
                    confidence=confidence,
                    source_quote=quote,
                    should_use_for_scoring=confidence >= 0.75,
                    extracted_by=extracted_by,
                    source_type=source_type,
                    source_name=source_name,
                    source_url=source_url,
                )
            )
            if len(items) >= 10:
                break
        return items

    def _normalize_llm_items(self, raw_items: Any, material_text: str, source_type: str = "user_input", source_name: str = "用户粘贴材料", source_url: str | None = None) -> list[dict[str, Any]]:
        if not isinstance(raw_items, list):
            return []
        items: list[dict[str, Any]] = []
        for raw in raw_items[:10]:
            if not isinstance(raw, dict):
                continue
            quote = str(raw.get("source_quote") or "").strip()
            if not quote or quote not in material_text:
                continue
            risk_keywords = [str(item).strip() for item in raw.get("risk_keywords", []) if str(item).strip()]
            risk_keywords = self._merge_detected_keywords(risk_keywords, f"{raw.get('title', '')} {raw.get('content', '')} {quote}")
            risk_keywords = [keyword for keyword in risk_keywords if not self._keyword_negated(keyword, f"{raw.get('content', '')} {quote}")]
            if not risk_keywords:
                continue
            confidence = float(raw.get("confidence") or 0.65)
            severity = self._severity(raw.get("severity"), confidence)
            signals = self._signals_from_keywords(risk_keywords, severity)
            should_score = self._should_use_for_scoring(raw.get("should_use_for_scoring"), confidence, severity, risk_keywords, signals)
            items.append(
                self._item(
                    title=str(raw.get("title") or "用户材料风险证据")[:120],
                    content=str(raw.get("content") or quote)[:1000],
                    risk_type=str(raw.get("risk_type") or "business"),
                    risk_keywords=risk_keywords,
                    rule_signals=signals,
                    severity=severity,
                    confidence=confidence,
                    source_quote=quote,
                    should_use_for_scoring=should_score,
                    extracted_by="LLM",
                    source_type=source_type,
                    source_name=source_name,
                    source_url=source_url,
                )
            )
        return items

    def _signals_from_keywords(self, keywords: list[str], severity: str) -> list[str]:
        signals: list[str] = []
        joined = " ".join(keywords)
        for keyword, _, signal, _, _ in self.KEYWORD_RULES:
            if keyword in joined and signal not in signals:
                signals.append(signal)
        if not signals and severity == "critical":
            signals.append("critical_compliance_signal")
        if not signals and severity == "warning":
            signals.append("warning_business_or_delivery_signal")
        return signals

    def _merge_detected_keywords(self, keywords: list[str], text: str) -> list[str]:
        merged = list(dict.fromkeys(keywords))
        for keyword, _, _, _, _ in self.KEYWORD_RULES:
            if keyword in text and keyword not in merged:
                merged.append(keyword)
        return merged

    def _keyword_negated(self, keyword: str, text: str) -> bool:
        index = text.find(keyword)
        return index >= 0 and self._is_negated(text, index)

    def _is_negated(self, text: str, index: int) -> bool:
        window = text[max(0, index - 12):index]
        return any(term in window for term in ["未发现", "无", "没有", "不存在", "未见", "未涉及"])

    def _should_use_for_scoring(self, raw_value: Any, confidence: float, severity: str, keywords: list[str], signals: list[str]) -> bool:
        high_risk = severity == "critical" or "sanction_or_blacklist" in signals or "major_dishonesty" in signals or "serious_administrative_penalty" in signals
        if high_risk:
            return True
        if raw_value is False and confidence < 0.5:
            return False
        if raw_value is True:
            return True
        return confidence >= 0.5 and bool(keywords or signals)

    def _item(
        self,
        *,
        title: str,
        content: str,
        risk_type: str,
        risk_keywords: list[str],
        rule_signals: list[str],
        severity: str,
        confidence: float,
        source_quote: str,
        should_use_for_scoring: bool,
        extracted_by: str,
        source_type: str = "user_input",
        source_name: str = "用户粘贴材料",
        source_url: str | None = None,
    ) -> dict[str, Any]:
        cleaned_keywords = [keyword for keyword in risk_keywords if keyword]
        if not cleaned_keywords:
            cleaned_keywords = [risk_type or "user_material_risk"]
        normalized_content = content.strip() or source_quote.strip()
        raw_text = source_quote.strip() or normalized_content
        title_text = title.strip() or "用户材料风险证据"
        return {
            "source": source_type,
            "category": risk_type,
            "title": title_text,
            "content": normalized_content,
            "risk_type": risk_type,
            "risk_keywords": cleaned_keywords,
            "rule_signals": rule_signals if should_use_for_scoring else [],
            "severity": severity,
            "confidence": max(0.0, min(1.0, confidence)),
            "source_type": source_type,
            "source_name": source_name,
            "source_url": source_url,
            "source_quote": raw_text,
            "raw_text": raw_text,
            "normalized_content": normalized_content,
            "extracted_by": extracted_by,
            "should_use_for_scoring": should_use_for_scoring,
            "metadata_json": {
                "risk_type": risk_type,
                "severity": severity,
                "risk_keywords": cleaned_keywords,
                "source_quote": raw_text,
                "should_use_for_scoring": should_use_for_scoring,
                "confidence": confidence,
            },
            "economic_rationale": "用户主动提供材料中的风险信号，需结合公开证据和政策规则复核。",
        }

    def _severity(self, value: Any, confidence: float) -> str:
        text = str(value or "").lower()
        if text in {"high", "critical", "高", "严重"}:
            return "critical"
        if text in {"medium", "warning", "中", "中高"}:
            return "warning"
        return "warning" if confidence >= 0.75 else "info"

    def _quote(self, text: str, index: int, length: int) -> str:
        start = max(0, index - 50)
        end = min(len(text), index + length + 50)
        return text[start:end].strip()

    def _summary(self, value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)[:1000]

    def _log_keyword_fallback(self, db, task_id: str | None, supplier: dict[str, Any], text: str, items: list[dict[str, Any]], reason: str) -> None:
        log_llm_call(
            db,
            task_id,
            "EvidenceExtractionTool",
            "evidence_extraction",
            "mock",
            "mock-keyword-extractor",
            "evidence_extraction_prompt",
            self._summary({"supplier": supplier, "material_length": len(text)}),
            self._summary({"evidence_count": len(items), "evidence_items": items}),
            True,
            True,
            reason,
        )

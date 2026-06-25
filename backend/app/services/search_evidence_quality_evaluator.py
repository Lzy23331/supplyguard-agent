from __future__ import annotations

import re
from typing import Any

from app.services.domain_trust_classifier import DomainTrustClassifier


class SearchEvidenceQualityEvaluator:
    name = "SearchEvidenceQualityEvaluator"

    RISK_TAGS: dict[str, tuple[str, float]] = {
        "行政处罚": ("administrative_penalty", 0.85),
        "处罚": ("administrative_penalty", 0.72),
        "严重违法": ("dishonesty_enforcement", 0.9),
        "失信": ("dishonesty_enforcement", 0.88),
        "被执行人": ("dishonesty_enforcement", 0.82),
        "限制高消费": ("dishonesty_enforcement", 0.82),
        "经营异常": ("business_abnormality", 0.78),
        "异常经营": ("business_abnormality", 0.72),
        "诉讼": ("lawsuit_dispute", 0.62),
        "纠纷": ("lawsuit_dispute", 0.62),
        "裁判文书": ("lawsuit_dispute", 0.68),
        "开庭公告": ("lawsuit_dispute", 0.62),
        "质量": ("quality_recall", 0.58),
        "召回": ("quality_recall", 0.78),
        "黑名单": ("sanction_blacklist", 0.9),
        "制裁": ("sanction_blacklist", 0.92),
        "出口管制": ("sanction_blacklist", 0.85),
        "负面": ("negative_public_opinion", 0.58),
        "舆情": ("negative_public_opinion", 0.58),
        "投诉": ("negative_public_opinion", 0.55),
        "administrative_penalty": ("administrative_penalty", 0.85),
        "dishonesty_enforcement": ("dishonesty_enforcement", 0.88),
        "business_abnormality": ("business_abnormality", 0.78),
        "lawsuit_dispute": ("lawsuit_dispute", 0.62),
        "quality_recall": ("quality_recall", 0.7),
        "sanction_blacklist": ("sanction_blacklist", 0.9),
        "negative_public_opinion": ("negative_public_opinion", 0.58),
    }
    DEALER_TERMS = ("经销商", "4s店", "4S店", "销售服务", "门店", "专营店", "维修站", "服务中心")
    BRAND_NEWS_TERMS = ("车型", "新车", "手机", "产品", "发布", "销量", "报价", "测评", "股价", "财报", "发布会")
    NEGATION_TERMS = ("未被列入", "一切正常", "非制裁名单", "不是制裁名单", "不影响公司正常业务", "不影响正常业务", "经营正常", "生产经营一切正常", "无正当理由", "回应", "澄清", "网传")
    RELATED_ENTITY_TERMS = ("汽车工业有限公司", "汽车有限公司", "汽车销售有限公司", "供应链管理有限公司", "电动车有限公司", "长沙市比亚迪", "上海比亚迪", "深圳市比亚迪供应链")
    COMPANY_SUFFIXES = ("股份有限公司", "有限责任公司", "有限公司", "集团", "科技", "技术", "通讯", "汽车", "公司")

    def __init__(self) -> None:
        self.domain_classifier = DomainTrustClassifier()

    def evaluate(self, rows: list[dict[str, Any]], *, company_name: str) -> list[dict[str, Any]]:
        evaluated = []
        for row in rows:
            evaluated.append(self.evaluate_one(row, company_name=company_name))
        return evaluated

    def evaluate_one(self, row: dict[str, Any], *, company_name: str) -> dict[str, Any]:
        item = dict(row)
        title = item.get("title") or ""
        snippet = item.get("snippet") or ""
        url = item.get("url")
        text = f"{title} {snippet} {url or ''}"
        domain_trust = self.domain_classifier.classify(url, item.get("site"))
        entity_relation_type, entity_match_score, entity_reason = self._entity_match(text, company_name)
        matched_risk_keywords, risk_relevance_score = self._risk_keywords(text)
        if self._has_negation_context(text):
            matched_risk_keywords = []
            risk_relevance_score = 0.0
        confidence = round(min(0.98, 0.35 * entity_match_score + 0.35 * risk_relevance_score + 0.30 * domain_trust.score), 2)
        evidence_strength = self._strength(confidence, risk_relevance_score)
        decision, reason, excluded_reason = self._decision(
            url=url,
            is_duplicate=bool(item.get("is_duplicate")),
            entity_relation_type=entity_relation_type,
            entity_match_score=entity_match_score,
            risk_relevance_score=risk_relevance_score,
            domain_trust_score=domain_trust.score,
            confidence=confidence,
            matched_risk_keywords=matched_risk_keywords,
        )
        item.update(
            {
                "source_type": "web_search",
                "source_name": "腾讯云联网搜索",
                "domain": self.domain_classifier.domain(url or item.get("site")),
                "domain_trust_level": domain_trust.level,
                "domain_trust_score": domain_trust.score,
                "entity_match_score": entity_match_score,
                "risk_relevance_score": risk_relevance_score,
                "confidence": confidence,
                "evidence_strength": evidence_strength,
                "entity_relation_type": entity_relation_type,
                "decision": decision,
                "decision_reason": reason,
                "matched_risk_keywords": matched_risk_keywords,
                "excluded_reason": excluded_reason or item.get("excluded_reason"),
                "metadata_json": {
                    **(item.get("metadata_json") or item.get("metadata") or {}),
                    "entity_reason": entity_reason,
                    "domain_reason": domain_trust.reason,
                    "should_use_for_scoring": decision == "score_evidence",
                },
            }
        )
        return item

    def _entity_match(self, text: str, company_name: str) -> tuple[str, float, str]:
        clean_text = text.lower()
        target = (company_name or "").strip()
        core = self._company_core(target)
        if target and target.lower() in clean_text:
            title = text.split("http", 1)[0]
            title_part = title[: max(1, min(len(title), 120))]
            if target not in title_part and self._contains_any(title_part, self.RELATED_ENTITY_TERMS):
                return "group_or_subsidiary", 0.55, "目标企业出现在摘要中，但标题主体为子公司、关联公司或品牌主体"
            if self._contains_any(text, self.DEALER_TERMS):
                return "dealer_or_service", 0.48, "命中目标名称但语境为经销商或服务网点"
            if self._contains_any(text, self.BRAND_NEWS_TERMS):
                return "brand_or_product_news", 0.42, "命中目标品牌但语境为产品或品牌新闻"
            return "exact_target", 0.9, "完整目标企业名称匹配"
        if core and core.lower() in clean_text:
            if self._contains_any(text, self.RELATED_ENTITY_TERMS):
                return "group_or_subsidiary", 0.55, "仅命中品牌核心名称，文本主体为子公司、关联公司或销售服务主体"
            if self._contains_any(text, self.DEALER_TERMS):
                return "dealer_or_service", 0.42, "核心名称匹配但语境为经销商或服务网点"
            if self._contains_any(text, self.BRAND_NEWS_TERMS):
                return "brand_or_product_news", 0.32, "核心名称匹配但语境为品牌或产品新闻"
            if "子公司" in text or "控股" in text or "集团" in text:
                return "group_or_subsidiary", 0.55, "可能为集团、子公司或关联主体"
            return "likely_target", 0.62, "仅目标企业核心名称匹配，未达到完整主体匹配"
        return "unrelated_same_name_or_unknown", 0.1, "未匹配目标企业名称或核心名称"

    def _risk_keywords(self, text: str) -> tuple[list[str], float]:
        matched: list[str] = []
        score = 0.0
        lower = text.lower()
        for keyword, (tag, value) in self.RISK_TAGS.items():
            if keyword.lower() in lower:
                if tag not in matched:
                    matched.append(tag)
                score = max(score, value)
        return matched, round(score, 2)

    def _decision(
        self,
        *,
        url: str | None,
        is_duplicate: bool,
        entity_relation_type: str,
        entity_match_score: float,
        risk_relevance_score: float,
        domain_trust_score: float,
        confidence: float,
        matched_risk_keywords: list[str],
    ) -> tuple[str, str, str | None]:
        if is_duplicate:
            return "exclude", "重复搜索结果已排除", "duplicate"
        if not url:
            return "exclude", "缺少真实 URL，不能进入报告评分", "missing_url"
        if entity_match_score < 0.35:
            return "exclude", "主体匹配度过低，疑似同名无关结果", "entity_unrelated"
        if domain_trust_score < 0.3:
            return "exclude", "来源可信度过低", "low_domain_trust"
        if entity_relation_type in {"dealer_or_service", "brand_or_product_news", "group_or_subsidiary"}:
            return "display_only", "与目标品牌或关联主体相关，但不直接归因于签约主体", None
        if not matched_risk_keywords:
            return "display_only", "目标相关但未形成可评分高风险证据", None
        if set(matched_risk_keywords).issubset({"lawsuit_dispute"}) and domain_trust_score < 0.72:
            return "display_only", "诉讼/合同纠纷来自媒体或普通网页，仅展示；需法院公告或高可信企业数据库确认后才参与评分", None
        if domain_trust_score < 0.65 and set(matched_risk_keywords).issubset({"business_abnormality", "quality_recall"}):
            return "display_only", "普通网页来源仅展示，需法院、监管或高可信来源确认后才参与评分", None
        if (
            entity_match_score >= 0.65
            and risk_relevance_score >= 0.55
            and domain_trust_score >= 0.35
            and matched_risk_keywords
            and confidence >= 0.55
        ):
            return "score_evidence", "主体匹配、风险相关性和来源可信度均达到评分阈值", None
        return "display_only", "目标相关但未形成可评分高风险证据", None

    def _has_negation_context(self, text: str) -> bool:
        return self._contains_any(text, self.NEGATION_TERMS)
    def _company_core(self, company_name: str) -> str:
        core = company_name
        for suffix in self.COMPANY_SUFFIXES:
            core = core.replace(suffix, "")
        return re.sub(r"\s+", "", core).strip()

    def _contains_any(self, text: str, terms: tuple[str, ...]) -> bool:
        return any(term.lower() in text.lower() for term in terms)

    def _strength(self, confidence: float, risk_score: float) -> str:
        if confidence >= 0.75 and risk_score >= 0.75:
            return "strong"
        if confidence >= 0.55 and risk_score >= 0.55:
            return "medium"
        return "weak"




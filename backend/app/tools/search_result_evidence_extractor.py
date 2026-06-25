from typing import Any

from app.evidence_providers.base import EvidenceCandidate


class SearchResultEvidenceExtractor:
    name = "SearchResultEvidenceExtractor"
    STRONG_KEYWORDS = [
        "行政处罚",
        "经营异常",
        "严重违法",
        "失信",
        "被执行人",
        "限制高消费",
        "黑名单",
        "制裁",
        "出口管制",
        "欠税",
        "税收违法",
    ]
    MEDIUM_KEYWORDS = [
        "合同纠纷",
        "买卖合同纠纷",
        "付款纠纷",
        "交付延期",
        "质量问题",
        "环保处罚",
        "安全事故",
        "诉讼",
        "开庭公告",
        "裁判文书",
        "破产重整",
        "股权冻结",
    ]
    WEAK_KEYWORDS = ["风险", "争议", "投诉", "违规"]

    def extract(self, results: list[dict[str, Any]]) -> list[EvidenceCandidate]:
        evidence: list[EvidenceCandidate] = []
        seen: set[tuple[str, str]] = set()
        for result in results:
            title = result.get("title") or "联网搜索结果"
            snippet = result.get("snippet") or result.get("summary") or ""
            url = result.get("url") or result.get("link")
            raw_text = f"{title} {snippet}".strip()
            target_company = result.get("company_name") or result.get("target_company")
            exact_company_match = not target_company or str(target_company) in raw_text
            relevance = 0.82 if exact_company_match else 0.35
            keywords = self._keywords(raw_text)
            if not keywords:
                keywords = ["search_observation"]
            strong = any(keyword in self.STRONG_KEYWORDS for keyword in keywords)
            medium = any(keyword in self.MEDIUM_KEYWORDS for keyword in keywords)
            dedupe_key = (url or raw_text, ",".join(keywords))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            confidence = 0.78 if strong else 0.65 if medium else 0.45 if keywords == ["search_observation"] else 0.52
            if not exact_company_match:
                confidence = min(confidence, 0.49)
            should_score = bool(url and exact_company_match and confidence >= 0.5 and (strong or medium))
            evidence.append(
                EvidenceCandidate(
                    title=f"联网搜索命中：{title}",
                    content=snippet or title,
                    risk_keywords=keywords,
                    source_type="web_search",
                    source_name="腾讯云联网搜索",
                    source_url=url,
                    confidence=confidence,
                    raw_text=raw_text,
                    severity="critical" if strong else "warning" if medium else "info",
                    metadata={
                        "query": result.get("query"),
                        "purpose": result.get("purpose"),
                        "site": result.get("site"),
                        "rank": result.get("rank"),
                        "should_use_for_scoring": should_score,
                        "source": result.get("source") or "tencent_web_search",
                        "provider": result.get("source") or "tencent_web_search",
                        "provider_mode": result.get("provider_mode") or "real",
                        "retrieved_at": result.get("retrieved_at"),
                        "target_company": target_company,
                        "exact_company_match": exact_company_match,
                        "relevance": relevance,
                    },
                )
            )
        return evidence

    def _keywords(self, text: str) -> list[str]:
        keywords: list[str] = []
        for keyword in [*self.STRONG_KEYWORDS, *self.MEDIUM_KEYWORDS, *self.WEAK_KEYWORDS]:
            if keyword in text and keyword not in keywords:
                keywords.append(keyword)
        return keywords

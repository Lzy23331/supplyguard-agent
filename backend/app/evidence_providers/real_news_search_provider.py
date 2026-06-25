from typing import Any

import httpx

from app.config import get_settings
from app.evidence_providers.base import EvidenceCandidate, EvidenceProvider


class RealNewsSearchProvider(EvidenceProvider):
    name = "RealNewsSearchProvider"
    provider_name = "RealNewsSearchProvider"
    source_type = "real_external"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.newsapi_key)

    def collect(
        self,
        *,
        company_name: str,
        resolved_company: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[EvidenceCandidate]:
        if not self.is_configured():
            return []
        params = {
            "q": company_name,
            "apiKey": self.settings.newsapi_key,
            "language": "zh",
            "pageSize": 10,
            "sortBy": "relevancy",
        }
        with httpx.Client(timeout=self.settings.provider_timeout_seconds) as client:
            data = client.get("https://newsapi.org/v2/everything", params=params).json()
        return [
            EvidenceCandidate(
                title=row.get("title") or "新闻结果",
                content=row.get("description") or row.get("content") or row.get("title") or "",
                risk_keywords=self._keywords(row.get("title", ""), row.get("description", ""), row.get("content", "")),
                source_type=self.source_type,
                source_name=self.name,
                source_url=row.get("url"),
                confidence=0.68,
                raw_text=row.get("description") or row.get("content") or row.get("title"),
                severity="warning" if self._keywords(row.get("title", ""), row.get("description", ""), row.get("content", "")) else "info",
                metadata={"published_at": row.get("publishedAt"), "source": (row.get("source") or {}).get("name")},
            )
            for row in (data.get("articles") or [])[:5]
        ]

    def _keywords(self, *parts: str) -> list[str]:
        text = " ".join(part or "" for part in parts)
        keywords = ["处罚", "诉讼", "纠纷", "召回", "制裁", "黑名单", "延迟交付", "交付延期"]
        return [keyword for keyword in keywords if keyword in text]

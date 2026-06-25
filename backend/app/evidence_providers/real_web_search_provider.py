from typing import Any

import httpx

from app.config import get_settings
from app.evidence_providers.base import EvidenceCandidate, EvidenceProvider


class RealWebSearchProvider(EvidenceProvider):
    name = "RealWebSearchProvider"
    provider_name = "RealWebSearchProvider"
    source_type = "real_external"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        if self.settings.web_search_api == "serpapi":
            return bool(self.settings.serpapi_api_key)
        if self.settings.web_search_api == "google_cse":
            return bool(self.settings.google_cse_api_key and self.settings.google_cse_cx)
        return False

    def collect(
        self,
        *,
        company_name: str,
        resolved_company: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[EvidenceCandidate]:
        if not self.is_configured():
            return []
        query = f"{company_name} 制裁 黑名单 行政处罚 失信 合同纠纷 负面新闻"
        if self.settings.web_search_api == "serpapi":
            params = {"engine": "google", "q": query, "api_key": self.settings.serpapi_api_key}
            with httpx.Client(timeout=self.settings.provider_timeout_seconds) as client:
                data = client.get("https://serpapi.com/search.json", params=params).json()
            rows = data.get("organic_results") or []
        else:
            params = {
                "q": query,
                "key": self.settings.google_cse_api_key,
                "cx": self.settings.google_cse_cx,
            }
            with httpx.Client(timeout=self.settings.provider_timeout_seconds) as client:
                data = client.get("https://www.googleapis.com/customsearch/v1", params=params).json()
            rows = data.get("items") or []
        return [
            EvidenceCandidate(
                title=row.get("title") or "网页搜索结果",
                content=row.get("snippet") or row.get("description") or row.get("title") or "",
                risk_keywords=self._keywords(row.get("title", ""), row.get("snippet", "")),
                source_type=self.source_type,
                source_name=self.name,
                source_url=row.get("link"),
                confidence=0.65,
                raw_text=row.get("snippet") or row.get("title"),
                severity="warning" if self._keywords(row.get("title", ""), row.get("snippet", "")) else "info",
                metadata={"query": query, "provider_api": self.settings.web_search_api},
            )
            for row in rows[:5]
        ]

    def _keywords(self, *parts: str) -> list[str]:
        text = " ".join(part or "" for part in parts)
        keywords = ["制裁", "黑名单", "行政处罚", "失信", "合同纠纷", "负面新闻", "欺诈", "诉讼"]
        return [keyword for keyword in keywords if keyword in text]

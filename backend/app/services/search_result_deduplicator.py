from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


class SearchResultDeduplicator:
    name = "SearchResultDeduplicator"

    def deduplicate(self, rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        kept: list[dict[str, Any]] = []
        duplicates: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        seen_clean_urls: set[str] = set()
        by_domain: dict[str, list[dict[str, Any]]] = {}

        for row in rows:
            item = dict(row)
            url_key = self._url_key(item.get("url"))
            clean_key = self._clean_url_key(item.get("url"))
            domain = self._domain(item.get("url") or item.get("site"))
            title_key = self._text_key(item.get("title"))
            snippet_key = self._text_key(item.get("snippet"))
            reason = None

            if url_key and url_key in seen_urls:
                reason = "duplicate_url"
            elif clean_key and clean_key in seen_clean_urls:
                reason = "duplicate_canonical_url"
            else:
                for previous in by_domain.get(domain, []):
                    title_score = self._similarity(title_key, self._text_key(previous.get("title")))
                    snippet_score = self._similarity(snippet_key, self._text_key(previous.get("snippet")))
                    if domain and title_score >= 0.88:
                        reason = "duplicate_same_domain_title"
                        break
                    if snippet_key and snippet_score >= 0.9:
                        reason = "duplicate_similar_snippet"
                        break

            if reason:
                item.update({"is_duplicate": True, "decision": "exclude", "excluded_reason": reason})
                duplicates.append(item)
                continue

            item["is_duplicate"] = False
            kept.append(item)
            if url_key:
                seen_urls.add(url_key)
            if clean_key:
                seen_clean_urls.add(clean_key)
            by_domain.setdefault(domain, []).append(item)

        return kept, duplicates

    def _url_key(self, url: str | None) -> str:
        if not url:
            return ""
        parsed = urlparse(url.strip())
        return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/").lower(), "", parsed.query, ""))

    def _clean_url_key(self, url: str | None) -> str:
        if not url:
            return ""
        parsed = urlparse(url.strip())
        query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if not k.lower().startswith(("utm_", "spm", "from", "source"))]
        return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/").lower(), "", urlencode(query), ""))

    def _domain(self, value: str | None) -> str:
        if not value:
            return ""
        parsed = urlparse(value if "://" in value else f"https://{value}")
        return parsed.netloc.lower().removeprefix("www.")

    def _text_key(self, value: str | None) -> str:
        return re.sub(r"[\W_]+", "", (value or "").lower())[:180]

    def _similarity(self, left: str, right: str) -> float:
        if not left or not right:
            return 0.0
        return SequenceMatcher(None, left, right).ratio()

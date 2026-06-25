import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.evidence_providers.base import EvidenceCandidate, EvidenceProvider
from app.repositories import save_web_search_results
from app.services.provider_audit_service import ProviderAuditService
from app.services.search_evidence_quality_evaluator import SearchEvidenceQualityEvaluator
from app.services.search_result_deduplicator import SearchResultDeduplicator


class TencentWebSearchProvider(EvidenceProvider):
    name = "TencentWebSearchProvider"
    provider_name = "TencentWebSearchProvider"
    source_type = "web_search"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.audit = ProviderAuditService()
        self.deduplicator = SearchResultDeduplicator()
        self.evaluator = SearchEvidenceQualityEvaluator()

    def is_configured(self) -> bool:
        return bool(self.settings.tencentcloud_secret_id and self.settings.tencentcloud_secret_key)

    def collect(
        self,
        *,
        company_name: str,
        resolved_company: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[EvidenceCandidate]:
        if not self.is_configured():
            return []
        task_id = (context or {}).get("task_id")
        plan = (context or {}).get("search_queries") or (resolved_company or {}).get("search_queries") or []
        if not plan:
            plan = [{"query": f"{company_name} 行政处罚 经营异常 失信 黑名单 合同纠纷", "purpose": "due_diligence"}]
        max_queries = 5
        top_k = max(1, min(int(self.settings.tencent_web_search_top_k or 5), 5))
        max_total = max(1, int(self.settings.web_search_max_total_results or 25))
        all_results: list[dict[str, Any]] = []
        failed_count = 0
        query_counts: list[dict[str, Any]] = []
        active_plan = plan[:max_queries]

        self._audit(
            task_id,
            "web_search_queries_planned",
            "completed",
            f"SearchQueryPlannerAgent 生成 {len(active_plan)} 条腾讯云搜索 query。",
            {"queries": [item.get("query") for item in active_plan]},
            f"query_count={len(active_plan)}",
        )

        for item in active_plan:
            query = item.get("query") or company_name
            purpose = item.get("purpose") or "due_diligence"
            start = time.perf_counter()
            try:
                payload = self._build_payload(query, top_k)
                data = self._request(payload)
                results = self.standardize_response(data, query=query, purpose=purpose, top_k=top_k, company_name=company_name)
                all_results.extend(results)
                query_counts.append({"query": query, "count": len(results)})
                self._event(task_id, "provider_completed", "completed", f"腾讯云联网搜索 query 成功，返回 {len(results)} 条结果。", query, len(results), start)
            except Exception as exc:
                failed_count += 1
                query_counts.append({"query": query, "count": 0, "error_message": str(exc)})
                self._event(task_id, "provider_warning", "warning", f"腾讯云联网搜索 query 失败，已继续其他 query：{exc}", query, 0, start)
                continue

        if failed_count >= len(active_plan) and not all_results:
            raise RuntimeError("Tencent web search failed for all planned queries")

        retained = all_results[: min(max_total, max_queries * top_k)]
        kept, duplicates = self.deduplicator.deduplicate(retained)
        evaluated = self.evaluator.evaluate(kept, company_name=company_name)
        duplicate_rows = self.evaluator.evaluate(duplicates, company_name=company_name) if duplicates else []
        all_evaluated = [*evaluated, *duplicate_rows]
        score_count = sum(1 for item in all_evaluated if item.get("decision") == "score_evidence")
        display_count = sum(1 for item in all_evaluated if item.get("decision") == "display_only")
        exclude_count = sum(1 for item in all_evaluated if item.get("decision") == "exclude")

        if task_id:
            saved_count = save_web_search_results(task_id, all_evaluated)
            self._audit(
                task_id,
                "web_search_query_results",
                "completed",
                "腾讯云联网搜索已按 query 记录返回数量。",
                {"query_counts": query_counts, "provider": "TencentWebSearchProvider", "fallback": False, "saved_to_web_search_results": saved_count},
                f"query_counts={json.dumps(query_counts, ensure_ascii=False)}; saved_to_web_search_results={saved_count}",
            )
            self._audit(
                task_id,
                "web_search_deduplicated",
                "completed",
                f"SearchResultDeduplicator 去重前 {len(retained)} 条，去重后 {len(kept)} 条，排除重复 {len(duplicates)} 条。",
                {"raw_count": len(retained), "deduped_count": len(kept), "duplicate_count": len(duplicates)},
                f"raw={len(retained)}; deduped={len(kept)}; duplicates={len(duplicates)}",
            )
            self._audit(
                task_id,
                "web_search_quality_evaluated",
                "completed",
                f"SearchEvidenceQualityEvaluator 完成 {len(all_evaluated)} 条评估：score_evidence={score_count}, display_only={display_count}, exclude={exclude_count}。",
                {"score_evidence": score_count, "display_only": display_count, "exclude": exclude_count},
                f"score_evidence={score_count}; display_only={display_count}; exclude={exclude_count}",
            )
            self._audit(
                task_id,
                "llm_disambiguation_status",
                "completed",
                "LLMSubjectDisambiguationService 未启用，本次使用规则消歧 fallback。",
                {"enabled": False, "evaluated_count": 0, "fallback": True},
                "enabled=false; evaluated=0; fallback=true",
            )

        return [self._to_candidate(item) for item in all_evaluated if item.get("decision") == "score_evidence"]

    def standardize_response(self, data: dict[str, Any], *, query: str, purpose: str, top_k: int, company_name: str | None = None) -> list[dict[str, Any]]:
        response = data.get("Response") if isinstance(data.get("Response"), dict) else data
        rows = response.get("Results") or response.get("ResultList") or response.get("Data") or response.get("Pages") or response.get("Items") or []
        if isinstance(rows, dict):
            rows = rows.get("Results") or rows.get("Items") or rows.get("List") or []
        results: list[dict[str, Any]] = []
        for index, row in enumerate(rows[:top_k], start=1):
            if isinstance(row, str):
                try:
                    row = json.loads(row)
                except json.JSONDecodeError:
                    row = {"title": row[:80], "snippet": row}
            title = row.get("Title") or row.get("title") or row.get("Name") or row.get("name") or "联网搜索结果"
            snippet = row.get("Snippet") or row.get("snippet") or row.get("Summary") or row.get("summary") or row.get("Content") or row.get("content") or row.get("Description") or row.get("passage") or ""
            url = row.get("Url") or row.get("URL") or row.get("url") or row.get("Link") or row.get("link")
            item = {
                "query": query,
                "purpose": purpose,
                "title": title,
                "url": url,
                "snippet": snippet,
                "site": row.get("Site") or row.get("site") or self._site(url),
                "source": "tencent_web_search",
                "rank": row.get("Rank") or row.get("rank") or index,
                "provider_mode": "real",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            }
            if company_name:
                item["company_name"] = company_name
            results.append(item)
        return results

    def _to_candidate(self, item: dict[str, Any]) -> EvidenceCandidate:
        keywords = item.get("matched_risk_keywords") or []
        metadata = item.get("metadata_json") or {}
        metadata.update(
            {
                "query": item.get("query"),
                "rank": item.get("rank"),
                "domain": item.get("domain"),
                "domain_trust_level": item.get("domain_trust_level"),
                "domain_trust_score": item.get("domain_trust_score"),
                "entity_match_score": item.get("entity_match_score"),
                "risk_relevance_score": item.get("risk_relevance_score"),
                "entity_relation_type": item.get("entity_relation_type"),
                "decision": item.get("decision"),
                "decision_reason": item.get("decision_reason"),
                "provider": "TencentWebSearchProvider",
                "provider_mode": "real",
                "should_use_for_scoring": True,
            }
        )
        severity = "critical" if any(k in keywords for k in ["sanction_blacklist", "dishonesty_enforcement", "administrative_penalty"]) else "warning"
        return EvidenceCandidate(
            title=f"联网搜索风险证据：{item.get('title') or '公开网页结果'}",
            content=item.get("snippet") or item.get("title") or "腾讯云联网搜索返回可评分风险证据。",
            risk_keywords=keywords,
            source_type="web_search",
            source_name="腾讯云联网搜索",
            source_url=item.get("url"),
            confidence=item.get("confidence"),
            raw_text=f"{item.get('title') or ''}\n{item.get('snippet') or ''}".strip(),
            severity=severity,
            metadata=metadata,
        )

    def _build_payload(self, query: str, top_k: int) -> dict[str, Any]:
        return {"Query": query}

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        timestamp = int(time.time())
        headers = self._signed_headers(body, timestamp)
        data = self._post(body, headers)
        error = (data.get("Response") or {}).get("Error")
        if error and "does not support this region" in str(error.get("Message", "")) and "X-TC-Region" in headers:
            headers = dict(headers)
            headers.pop("X-TC-Region", None)
            data = self._post(body, headers)
            error = (data.get("Response") or {}).get("Error")
        if error:
            raise RuntimeError(error.get("Message") or error.get("Code") or "Tencent API error")
        return data

    def _post(self, body: str, headers: dict[str, str]) -> dict[str, Any]:
        with httpx.Client(timeout=self.settings.tencent_web_search_timeout_seconds) as client:
            response = client.post(self.settings.tencent_web_search_endpoint, content=body.encode("utf-8"), headers=headers)
            response.raise_for_status()
            return response.json()

    def _signed_headers(self, body: str, timestamp: int) -> dict[str, str]:
        endpoint = self.settings.tencent_web_search_endpoint
        host = urlparse(endpoint).netloc
        service = host.split(".")[0]
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")
        canonical_request = "\n".join(
            [
                "POST",
                "/",
                "",
                f"content-type:application/json; charset=utf-8\nhost:{host}\nx-tc-action:{self.settings.tencent_web_search_action.lower()}\n",
                "content-type;host;x-tc-action",
                hashlib.sha256(body.encode("utf-8")).hexdigest(),
            ]
        )
        credential_scope = f"{date}/{service}/tc3_request"
        string_to_sign = "\n".join(["TC3-HMAC-SHA256", str(timestamp), credential_scope, hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()])
        secret_date = self._sign(("TC3" + (self.settings.tencentcloud_secret_key or "")).encode("utf-8"), date)
        secret_service = self._sign(secret_date, service)
        secret_signing = self._sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        authorization = (
            "TC3-HMAC-SHA256 "
            f"Credential={self.settings.tencentcloud_secret_id}/{credential_scope}, "
            "SignedHeaders=content-type;host;x-tc-action, "
            f"Signature={signature}"
        )
        return {
            "Authorization": authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Host": host,
            "X-TC-Action": self.settings.tencent_web_search_action,
            "X-TC-Version": self.settings.tencent_web_search_version,
            "X-TC-Region": self.settings.tencentcloud_region,
            "X-TC-Timestamp": str(timestamp),
        }

    def _sign(self, key: bytes, message: str) -> bytes:
        return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()

    def _site(self, url: str | None) -> str | None:
        return urlparse(url).netloc if url else None

    def _event(self, task_id: str | None, event_type: str, status: str, summary: str, query: str, count: int, start: float) -> None:
        if not task_id:
            return
        latency_ms = int((time.perf_counter() - start) * 1000)
        self.audit.event(task_id, event_type, status, summary, self.name, {"query": query}, f"count={count}; latency_ms={latency_ms}")

    def _audit(self, task_id: str | None, event_type: str, status: str, summary: str, tool_input: dict[str, Any], output: str) -> None:
        if not task_id:
            return
        self.audit.event(task_id, event_type, status, summary, self.name, tool_input, output)



import re
from typing import Any

from app.config import get_settings
from app.services.llm_task_service import rewrite_policy_queries
from app.tools.document_parser import DocumentParserTool


class RAGPolicyTool:
    name = "RAGPolicyTool"

    def __init__(self) -> None:
        self.policy_dir = get_settings().policies_dir
        self.parser = DocumentParserTool()

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        terms = self._terms(query)
        results: list[dict[str, Any]] = []
        for chunk in self.parser.parse_policy_chunks(self.policy_dir):
            title = chunk["section_title"].lower()
            keyword_text = " ".join(chunk.get("keywords", [])).lower()
            content = chunk["content"].lower()
            score = 0
            matched: set[str] = set()
            for term in terms:
                if term in title:
                    score += 3
                    matched.add(term)
                if term in keyword_text:
                    score += 2
                    matched.add(term)
                if term in content:
                    score += 1
                    matched.add(term)
            if score:
                results.append({**chunk, "score": score, "matched_keywords": sorted(matched), "document": chunk["doc_name"], "chunk": chunk["content"][:800]})
        return sorted(results, key=lambda item: (item["score"], len(item["matched_keywords"])), reverse=True)[:top_k]

    def retrieve_with_query_rewrite(
        self,
        *,
        task_id: str | None,
        supplier_profile: dict[str, Any],
        evidence_items: list[dict[str, Any]],
        fallback_query: str,
        top_k: int = 3,
    ) -> tuple[list[dict[str, Any]], list[str], bool]:
        try:
            evidence_keywords = self.extract_evidence_keywords(evidence_items)
            queries = rewrite_policy_queries(
                None,
                task_id,
                supplier_profile,
                evidence_keywords,
                agent_name=self.name,
            )
            rewrite_used = True
        except Exception:
            queries = [fallback_query]
            rewrite_used = False

        merged: dict[tuple[str, str, str], dict[str, Any]] = {}
        for query in queries or [fallback_query]:
            for item in self.retrieve(query, top_k=top_k):
                key = (item.get("doc_name", ""), item.get("section_title", ""), item.get("content", ""))
                if key not in merged or item.get("score", 0) > merged[key].get("score", 0):
                    merged[key] = item
        results = sorted(
            merged.values(),
            key=lambda item: (item.get("score", 0), len(item.get("matched_keywords", []))),
            reverse=True,
        )[:top_k]
        if not results and fallback_query not in queries:
            results = self.retrieve(fallback_query, top_k=top_k)
        return results, queries, rewrite_used

    def extract_evidence_keywords(self, evidence_items: list[dict[str, Any]]) -> list[str]:
        keyword_table = [
            "制裁",
            "黑名单",
            "重大失信",
            "经营异常",
            "行政处罚",
            "交付延期",
            "付款纠纷",
            "合同争议",
            "负面新闻",
            "资料缺失",
            "官网缺失",
            "成立时间短",
            "境外",
            "紧急采购",
            "高额采购",
        ]
        found: list[str] = []
        for item in evidence_items:
            for signal in item.get("risk_keywords") or item.get("rule_signals") or []:
                if isinstance(signal, str):
                    found.append(signal)
            text = f"{item.get('title', '')} {item.get('content', '')}"
            for keyword in keyword_table:
                if keyword in text:
                    found.append(keyword)
        seen: set[str] = set()
        return [item for item in found if item and not (item in seen or seen.add(item))]

    def _terms(self, query: str) -> set[str]:
        return {term.lower() for term in re.findall(r"[\w\u4e00-\u9fff]+", query) if len(term) > 1}

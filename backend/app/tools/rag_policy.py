import re
from typing import Any

from app.config import get_settings
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

    def _terms(self, query: str) -> set[str]:
        return {term.lower() for term in re.findall(r"[\w\u4e00-\u9fff]+", query) if len(term) > 1}

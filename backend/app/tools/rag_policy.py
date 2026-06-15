import re
from app.config import get_settings
from app.tools.document_parser import DocumentParserTool


class RAGPolicyTool:
    name = "RAGPolicyTool"

    def __init__(self) -> None:
        self.policy_dir = get_settings().project_root / "data" / "policies"
        self.parser = DocumentParserTool()

    def retrieve(self, query: str, top_k: int = 4) -> list[dict[str, str | int]]:
        terms = {t.lower() for t in re.findall(r"[\w\u4e00-\u9fff]+", query) if len(t) > 1}
        chunks = []
        for doc in self.parser.read_documents(self.policy_dir):
            for idx, chunk in enumerate(re.split(r"\n#{1,3} ", doc["content"])):
                text = chunk.strip()
                if not text:
                    continue
                haystack = text.lower()
                score = sum(1 for term in terms if term in haystack)
                if score:
                    chunks.append({"document": doc["name"], "chunk": text[:800], "score": score, "index": idx})
        return sorted(chunks, key=lambda item: item["score"], reverse=True)[:top_k]

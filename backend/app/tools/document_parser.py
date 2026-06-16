import re
from pathlib import Path
from typing import Any


class DocumentParserTool:
    name = "DocumentParserTool"

    HEADING_PATTERN = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
    KEYWORD_PATTERN = re.compile(r"关键词[:：]\s*(.+)")

    def read_documents(self, directory: Path) -> list[dict[str, str]]:
        docs = []
        for path in sorted(directory.glob("*")):
            if path.suffix.lower() in {".md", ".txt"}:
                docs.append({"name": path.name, "content": path.read_text(encoding="utf-8")})
        return docs

    def parse_policy_chunks(self, directory: Path) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        for doc in self.read_documents(directory):
            matches = list(self.HEADING_PATTERN.finditer(doc["content"]))
            if not matches:
                for idx, paragraph in enumerate(p for p in doc["content"].split("\n\n") if p.strip()):
                    chunks.append(self._build_chunk(doc["name"], f"paragraph-{idx + 1}", paragraph))
                continue
            for idx, match in enumerate(matches):
                start = match.start()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(doc["content"])
                section = doc["content"][start:end].strip()
                chunks.append(self._build_chunk(doc["name"], match.group(2).strip(), section))
        return chunks

    def _build_chunk(self, doc_name: str, section_title: str, content: str) -> dict[str, Any]:
        keywords: list[str] = []
        for line in content.splitlines():
            match = self.KEYWORD_PATTERN.search(line)
            if match:
                keywords.extend([item.strip() for item in re.split(r"[、,，\s]+", match.group(1)) if item.strip()])
        return {"doc_name": doc_name, "section_title": section_title, "content": content, "keywords": sorted(set(keywords))}

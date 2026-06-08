from pathlib import Path


class DocumentParserTool:
    name = "DocumentParserTool"

    def read_documents(self, directory: Path) -> list[dict[str, str]]:
        docs = []
        for path in sorted(directory.glob("*")):
            if path.suffix.lower() in {".md", ".txt"}:
                docs.append({"name": path.name, "content": path.read_text(encoding="utf-8")})
        return docs


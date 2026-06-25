import csv
from pathlib import Path

from pypdf import PdfReader


class FileParserTool:
    name = "FileParserTool"

    def parse(self, path: Path, file_type: str) -> str:
        suffix = file_type.lower().lstrip(".")
        if suffix in {"txt", "md"}:
            return self._read_text(path)
        if suffix == "csv":
            return self._read_csv(path)
        if suffix == "pdf":
            return self._read_pdf(path)
        raise ValueError(f"Unsupported file type: {file_type}")

    def _read_text(self, path: Path) -> str:
        for encoding in ("utf-8", "gbk"):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        return path.read_text(encoding="utf-8", errors="ignore")

    def _read_csv(self, path: Path) -> str:
        text = self._read_text(path)
        rows = list(csv.reader(text.splitlines()))
        if not rows:
            return ""
        lines = ["CSV 文件内容摘要："]
        headers = rows[0]
        lines.append("表头：" + " | ".join(headers))
        for index, row in enumerate(rows[1:51], start=1):
            pairs = []
            for col_index, value in enumerate(row):
                label = headers[col_index] if col_index < len(headers) else f"列{col_index + 1}"
                pairs.append(f"{label}={value}")
            lines.append(f"第{index}行：" + "；".join(pairs))
        return "\n".join(lines)

    def _read_pdf(self, path: Path) -> str:
        reader = PdfReader(str(path))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
        text = "\n\n".join(page for page in pages if page)
        if not text.strip():
            raise ValueError("PDF 未提取到文本，当前不支持扫描件 OCR")
        return text

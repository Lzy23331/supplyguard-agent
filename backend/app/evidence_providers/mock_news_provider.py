import json
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.evidence_providers.base import EvidenceProvider


class MockNewsProvider(EvidenceProvider):
    name = "MockNewsProvider"
    source_type = "mock_external"

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or get_settings().project_root / "data" / "external_mock" / "news_results.json"

    def search(self, supplier: dict[str, Any]) -> list[dict[str, Any]]:
        company = (supplier.get("name") or supplier.get("company_name") or "").strip().lower()
        rows = json.loads(self.path.read_text(encoding="utf-8"))
        return [
            {**row, "id": f"news-{index}", "metadata_json": {"matched_company": row.get("company_name")}}
            for index, row in enumerate(rows)
            if row.get("company_name", "").lower() == company
        ]

import json
from typing import Any

from app.config import get_settings


class MockSearchTool:
    name = "MockSearchTool"

    def __init__(self) -> None:
        self.search_results_path = get_settings().mock_search_results_path

    def search_by_supplier_id(self, supplier_id: str) -> list[dict[str, Any]]:
        search_results = json.loads(self.search_results_path.read_text(encoding="utf-8"))
        return search_results.get(supplier_id, [])

    def search(self, supplier: dict[str, Any]) -> list[dict[str, Any]]:
        supplier_id = supplier.get("id")
        if supplier_id:
            return self.search_by_supplier_id(supplier_id)
        sample_key = supplier.get("sample_key")
        if sample_key:
            return self.search_by_supplier_id(f"supplier_{sample_key}_001")
        return []

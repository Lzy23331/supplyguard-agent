import json
from typing import Any

from app.config import get_settings


class MockSearchTool:
    name = "MockSearchTool"

    def __init__(self) -> None:
        data_dir = get_settings().project_root / "data" / "samples"
        self.suppliers_path = data_dir / "suppliers.json"
        self.search_results_path = data_dir / "mock_search_results.json"

    def search(self, supplier: dict[str, Any]) -> list[dict[str, Any]]:
        samples = json.loads(self.suppliers_path.read_text(encoding="utf-8"))
        search_results = json.loads(self.search_results_path.read_text(encoding="utf-8"))
        sample_key = supplier.get("sample_key")
        name = supplier.get("name", "").lower()
        for item in samples:
            if item["sample_key"] == sample_key or item["name"].lower() == name:
                return search_results.get(item["id"], [])
        return [
            {
                "source": "public_registry",
                "title": f"{supplier.get('name')} basic registration profile",
                "content": "No material negative record found in the mock public registry dataset.",
                "severity": "info",
                "url": "mock://registry/basic-profile",
            }
        ]

import json
from pathlib import Path
from typing import Any

from app.config import get_settings


class MockSearchTool:
    name = "MockSearchTool"

    def __init__(self) -> None:
        self.data_path = get_settings().project_root / "data" / "sample_suppliers" / "suppliers.json"

    def search(self, supplier: dict[str, Any]) -> list[dict[str, Any]]:
        samples = json.loads(self.data_path.read_text(encoding="utf-8"))
        sample_key = supplier.get("sample_key")
        name = supplier.get("name", "").lower()
        for item in samples:
            if item["sample_key"] == sample_key or item["name"].lower() == name:
                return item["evidence"]
        return [
            {
                "source": "public_registry",
                "title": f"{supplier.get('name')} basic registration profile",
                "content": "No material negative record found in the mock public registry dataset.",
                "severity": "info",
                "url": "mock://registry/basic-profile",
            }
        ]


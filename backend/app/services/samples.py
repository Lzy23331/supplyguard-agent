import json
from typing import Any

from app.config import get_settings


def _load_samples() -> list[dict[str, Any]]:
    return json.loads(get_settings().suppliers_path.read_text(encoding="utf-8"))


def list_sample_suppliers() -> list[dict[str, Any]]:
    return _load_samples()


def get_sample_supplier(identifier: str) -> dict[str, Any] | None:
    for item in _load_samples():
        if item["id"] == identifier or item["sample_key"] == identifier:
            return item
    return None

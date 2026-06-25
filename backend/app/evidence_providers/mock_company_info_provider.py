import json
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.evidence_providers.base import EvidenceProvider


class MockCompanyInfoProvider(EvidenceProvider):
    name = "MockCompanyInfoProvider"
    source_type = "mock_external"

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or get_settings().project_root / "data" / "external_mock" / "company_profiles.json"

    def _profiles(self) -> list[dict[str, Any]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def resolve(self, company_name: str) -> dict[str, Any] | None:
        needle = company_name.strip().lower()
        for profile in self._profiles():
            names = [profile.get("name", ""), *(profile.get("aliases") or [])]
            if any(needle == name.lower() or needle in name.lower() or name.lower() in needle for name in names):
                return profile
        return None

    def search(self, supplier: dict[str, Any]) -> list[dict[str, Any]]:
        profile = self.resolve(supplier.get("name") or supplier.get("company_name") or "")
        if not profile:
            return []
        items = []
        for index, item in enumerate(profile.get("evidence") or []):
            items.append(
                {
                    **item,
                    "id": f"company-info-{index}",
                    "source_name": "模拟企业信息库",
                    "metadata_json": {"matched_company": profile.get("name")},
                }
            )
        return items

import csv
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.evidence_providers.base import EvidenceProvider


class InternalRecordCsvProvider(EvidenceProvider):
    name = "InternalRecordCsvProvider"
    source_type = "internal_record"

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or get_settings().project_root / "data" / "internal" / "internal_supplier_records.csv"

    def search(self, supplier: dict[str, Any]) -> list[dict[str, Any]]:
        company = (supplier.get("name") or supplier.get("company_name") or "").strip().lower()
        if not self.path.exists():
            return []
        rows = []
        with self.path.open("r", encoding="utf-8-sig", newline="") as handle:
            for index, row in enumerate(csv.DictReader(handle)):
                if row.get("company_name", "").lower() != company:
                    continue
                rows.append(
                    {
                        "id": f"internal-{index}",
                        "title": row.get("title"),
                        "content": row.get("content"),
                        "severity": row.get("severity") or "info",
                        "risk_keywords": row.get("risk_keywords") or "",
                        "confidence": float(row.get("confidence") or 0.65),
                        "source_name": "内部供应商记录",
                        "metadata_json": {"matched_company": row.get("company_name")},
                    }
                )
        return rows

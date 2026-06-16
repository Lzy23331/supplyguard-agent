import json
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings
from app.database import init_db, get_db


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def seed_suppliers() -> list[dict[str, Any]]:
    init_db()
    samples = json.loads(get_settings().suppliers_path.read_text(encoding="utf-8"))
    created = now_iso()
    with get_db() as conn:
        for item in samples:
            conn.execute(
                """
                INSERT INTO suppliers
                (id, sample_key, name, website, industry, region, annual_spend, procurement_amount,
                 cooperation_type, business_status, company_age_years, profile_completeness,
                 ownership_transparency, urgency, summary, tags, expected_risk_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  sample_key=excluded.sample_key,
                  name=excluded.name,
                  website=excluded.website,
                  industry=excluded.industry,
                  region=excluded.region,
                  annual_spend=excluded.annual_spend,
                  procurement_amount=excluded.procurement_amount,
                  cooperation_type=excluded.cooperation_type,
                  business_status=excluded.business_status,
                  company_age_years=excluded.company_age_years,
                  profile_completeness=excluded.profile_completeness,
                  ownership_transparency=excluded.ownership_transparency,
                  urgency=excluded.urgency,
                  summary=excluded.summary,
                  tags=excluded.tags,
                  expected_risk_level=excluded.expected_risk_level
                """,
                (
                    item["id"],
                    item.get("sample_key"),
                    item["name"],
                    item.get("website"),
                    item.get("industry"),
                    item.get("region"),
                    item.get("annual_spend", 0),
                    item.get("procurement_amount", item.get("annual_spend", 0)),
                    item.get("cooperation_type"),
                    item.get("business_status"),
                    item.get("company_age_years"),
                    item.get("profile_completeness"),
                    item.get("ownership_transparency"),
                    item.get("urgency"),
                    item.get("summary"),
                    json.dumps(item.get("tags", []), ensure_ascii=False),
                    item.get("expected_risk_level"),
                    created,
                ),
            )
    return samples


def get_seeded_supplier(identifier: str) -> dict[str, Any] | None:
    seed_suppliers()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM suppliers WHERE id=? OR sample_key=?", (identifier, identifier)).fetchone()
    if not row:
        return None
    data = dict(row)
    try:
        data["tags"] = json.loads(data.get("tags") or "[]")
    except json.JSONDecodeError:
        data["tags"] = []
    return data

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .database import get_db
from .schemas import SupplierCreate


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_task_record(supplier: SupplierCreate) -> str:
    task_id = str(uuid.uuid4())
    supplier_id = supplier.sample_key and f"supplier_{supplier.sample_key}_001" or str(uuid.uuid4())
    created = now_iso()
    with get_db() as conn:
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
                supplier_id,
                supplier.sample_key,
                supplier.name,
                supplier.website,
                supplier.industry,
                supplier.region,
                supplier.annual_spend,
                supplier.procurement_amount or supplier.annual_spend,
                supplier.cooperation_type,
                supplier.business_status,
                supplier.company_age_years,
                supplier.profile_completeness,
                supplier.ownership_transparency,
                supplier.urgency,
                getattr(supplier, "summary", None),
                json.dumps(getattr(supplier, "tags", []), ensure_ascii=False),
                getattr(supplier, "expected_risk_level", None),
                created,
            ),
        )
        conn.execute(
            """
            INSERT INTO diligence_tasks
            (id, supplier_id, status, summary, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (task_id, supplier_id, "created", None, created, created),
        )
    return task_id


def update_task(task_id: str, **fields: Any) -> None:
    if not fields:
        return
    fields["updated_at"] = now_iso()
    assignments = ", ".join(f"{key}=?" for key in fields)
    with get_db() as conn:
        conn.execute(f"UPDATE diligence_tasks SET {assignments} WHERE id=?", (*fields.values(), task_id))


def add_event(task_id: str, agent_name: str, status: str, summary: str, tool_calls: list[dict[str, Any]] | None = None) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO agent_events
            (task_id, agent_name, event_type, status, summary, tool_name, tool_input, tool_output_summary, tool_calls, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, agent_name, status, status, summary, None, None, None, json.dumps(tool_calls or [], ensure_ascii=False), now_iso()),
        )


def add_evidence(task_id: str, item: dict[str, Any]) -> None:
    with get_db() as conn:
        task = conn.execute("SELECT supplier_id FROM diligence_tasks WHERE id=?", (task_id,)).fetchone()
        conn.execute(
            """
            INSERT INTO evidence_items
            (id, task_id, supplier_id, source, category, title, content, severity, rule_signals, economic_rationale, url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"{task_id}:{item.get('id')}" if item.get("id") else str(uuid.uuid4()),
                task_id,
                task["supplier_id"] if task else None,
                item["source"],
                item.get("category"),
                item["title"],
                item["content"],
                item.get("severity", "info"),
                json.dumps(item.get("rule_signals", []), ensure_ascii=False),
                item.get("economic_rationale"),
                item.get("url"),
                now_iso(),
            ),
        )


def add_assessment(task_id: str, item: dict[str, Any]) -> None:
    with get_db() as conn:
        task = conn.execute("SELECT supplier_id FROM diligence_tasks WHERE id=?", (task_id,)).fetchone()
        conn.execute(
            """
            INSERT INTO risk_assessments
            (task_id, supplier_id, dimension, score, level, rationale, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, task["supplier_id"] if task else None, item["dimension"], item["score"], item["level"], item["rationale"], now_iso()),
        )


def save_report(task_id: str, markdown: str) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO reports (task_id, markdown, markdown_content, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
              markdown=excluded.markdown,
              markdown_content=excluded.markdown_content,
              created_at=excluded.created_at
            """,
            (task_id, markdown, markdown, now_iso()),
        )


def _decode_json(value: Any, fallback: Any) -> Any:
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def get_task(task_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT t.*, s.name, s.website, s.industry, s.region, s.annual_spend,
                   s.procurement_amount, s.cooperation_type, s.sample_key, s.business_status,
                   s.company_age_years, s.profile_completeness, s.ownership_transparency,
                   s.urgency, s.summary, s.tags, s.expected_risk_level
            FROM diligence_tasks t
            JOIN suppliers s ON s.id = t.supplier_id
            WHERE t.id=?
            """,
            (task_id,),
        ).fetchone()
        if not row:
            return None
        evidence = [dict(r) for r in conn.execute("SELECT * FROM evidence_items WHERE task_id=? ORDER BY created_at, id", (task_id,))]
        dimensions = [dict(r) for r in conn.execute("SELECT * FROM risk_assessments WHERE task_id=? ORDER BY id", (task_id,))]
    data = dict(row)
    for item in evidence:
        item["rule_signals"] = _decode_json(item.get("rule_signals"), [])
    return {
        "id": data["id"],
        "status": data["status"],
        "risk_level": data["risk_level"],
        "total_score": data["total_score"],
        "recommendation": data["recommendation"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
        "supplier": {
            "id": data["supplier_id"],
            "name": data["name"],
            "website": data["website"],
            "industry": data["industry"],
            "region": data["region"],
            "annual_spend": data["annual_spend"],
            "procurement_amount": data["procurement_amount"],
            "cooperation_type": data["cooperation_type"],
            "sample_key": data["sample_key"],
            "business_status": data["business_status"],
            "company_age_years": data["company_age_years"],
            "profile_completeness": data["profile_completeness"],
            "ownership_transparency": data["ownership_transparency"],
            "urgency": data["urgency"],
            "summary": data["summary"],
            "tags": _decode_json(data["tags"], []),
            "expected_risk_level": data["expected_risk_level"],
        },
        "evidence": evidence,
        "dimensions": dimensions,
    }


def list_events(task_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM agent_events WHERE task_id=? ORDER BY id", (task_id,)).fetchall()
    events = []
    for row in rows:
        item = dict(row)
        item["tool_calls"] = _decode_json(item.get("tool_calls"), [])
        events.append(item)
    return events


def get_report(task_id: str) -> str | None:
    with get_db() as conn:
        row = conn.execute("SELECT markdown FROM reports WHERE task_id=?", (task_id,)).fetchone()
    return row["markdown"] if row else None


def save_review(task_id: str, reviewer: str, decision: str, comment: str | None) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO human_reviews (task_id, reviewer, decision, comment, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, reviewer, decision, comment, now_iso()),
        )


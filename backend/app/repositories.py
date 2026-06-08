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
    created = now_iso()
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO suppliers
            (name, website, industry, region, annual_spend, cooperation_type, sample_key, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                supplier.name,
                supplier.website,
                supplier.industry,
                supplier.region,
                supplier.annual_spend,
                supplier.cooperation_type,
                supplier.sample_key,
                created,
            ),
        )
        conn.execute(
            """
            INSERT INTO diligence_tasks
            (id, supplier_id, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, cur.lastrowid, "created", created, created),
        )
    return task_id


def update_task(task_id: str, **fields: Any) -> None:
    if not fields:
        return
    fields["updated_at"] = now_iso()
    assignments = ", ".join(f"{key}=?" for key in fields)
    with get_db() as conn:
        conn.execute(
            f"UPDATE diligence_tasks SET {assignments} WHERE id=?",
            (*fields.values(), task_id),
        )


def add_event(task_id: str, agent_name: str, status: str, summary: str, tool_calls: list[dict[str, Any]] | None = None) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO agent_events (task_id, agent_name, status, summary, tool_calls, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (task_id, agent_name, status, summary, json.dumps(tool_calls or [], ensure_ascii=False), now_iso()),
        )


def add_evidence(task_id: str, item: dict[str, Any]) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO evidence_items (task_id, source, title, content, severity, url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                item["source"],
                item["title"],
                item["content"],
                item.get("severity", "info"),
                item.get("url"),
                now_iso(),
            ),
        )


def add_assessment(task_id: str, item: dict[str, Any]) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO risk_assessments (task_id, dimension, score, level, rationale, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (task_id, item["dimension"], item["score"], item["level"], item["rationale"], now_iso()),
        )


def save_report(task_id: str, markdown: str) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO reports (task_id, markdown, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET markdown=excluded.markdown, created_at=excluded.created_at
            """,
            (task_id, markdown, now_iso()),
        )


def get_task(task_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT t.*, s.name, s.website, s.industry, s.region, s.annual_spend, s.cooperation_type, s.sample_key
            FROM diligence_tasks t
            JOIN suppliers s ON s.id = t.supplier_id
            WHERE t.id=?
            """,
            (task_id,),
        ).fetchone()
        if not row:
            return None
        evidence = [dict(r) for r in conn.execute("SELECT * FROM evidence_items WHERE task_id=? ORDER BY id", (task_id,))]
        dimensions = [dict(r) for r in conn.execute("SELECT * FROM risk_assessments WHERE task_id=? ORDER BY id", (task_id,))]
    data = dict(row)
    return {
        "id": data["id"],
        "status": data["status"],
        "risk_level": data["risk_level"],
        "total_score": data["total_score"],
        "recommendation": data["recommendation"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
        "supplier": {
            "name": data["name"],
            "website": data["website"],
            "industry": data["industry"],
            "region": data["region"],
            "annual_spend": data["annual_spend"],
            "cooperation_type": data["cooperation_type"],
            "sample_key": data["sample_key"],
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
        item["tool_calls"] = json.loads(item["tool_calls"])
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


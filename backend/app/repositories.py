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


def add_event(
    task_id: str,
    agent_name: str,
    event_type: str,
    status: str,
    summary: str,
    tool_name: str | None = None,
    tool_input: dict[str, Any] | list[Any] | str | None = None,
    tool_output_summary: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
) -> None:
    calls = tool_calls or []
    if tool_name:
        calls = [
            *calls,
            {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output_summary": tool_output_summary,
            },
        ]
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO agent_events
            (task_id, agent_name, event_type, status, summary, tool_name, tool_input, tool_output_summary, tool_calls, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                agent_name,
                event_type,
                status,
                summary,
                tool_name,
                json.dumps(tool_input, ensure_ascii=False) if tool_input is not None else None,
                tool_output_summary,
                json.dumps(calls, ensure_ascii=False),
                now_iso(),
            ),
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


def save_risk_assessment(task_id: str, risk: dict[str, Any]) -> None:
    with get_db() as conn:
        task = conn.execute("SELECT supplier_id FROM diligence_tasks WHERE id=?", (task_id,)).fetchone()
        conn.execute(
            """
            INSERT INTO risk_assessments
            (task_id, supplier_id, raw_score, total_score, risk_level, dimension_scores, triggered_rules, recommendation, rationale, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                task["supplier_id"] if task else None,
                risk.get("raw_score"),
                risk.get("total_score"),
                risk.get("risk_level"),
                json.dumps(risk.get("dimension_scores", {}), ensure_ascii=False),
                json.dumps(risk.get("triggered_rules", risk.get("hit_rules", [])), ensure_ascii=False),
                risk.get("recommendation"),
                risk.get("rationale"),
                now_iso(),
            ),
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


def list_evidence(task_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM evidence_items WHERE task_id=? ORDER BY created_at, id", (task_id,)).fetchall()
    evidence = [dict(row) for row in rows]
    for item in evidence:
        item["rule_signals"] = _decode_json(item.get("rule_signals"), [])
    return evidence


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
        dimensions = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM risk_assessments WHERE task_id=? AND dimension IS NOT NULL ORDER BY id",
                (task_id,),
            )
        ]
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
        "evidence": list_evidence(task_id),
        "dimensions": dimensions,
    }


def list_events(task_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM agent_events WHERE task_id=? ORDER BY id", (task_id,)).fetchall()
    events = []
    for row in rows:
        item = dict(row)
        item["tool_input"] = _decode_json(item.get("tool_input"), None)
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


def get_risk_assessment(task_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT raw_score, total_score, risk_level, dimension_scores, triggered_rules, recommendation, rationale
            FROM risk_assessments
            WHERE task_id=? AND raw_score IS NOT NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["dimension_scores"] = _decode_json(data.get("dimension_scores"), {})
    data["triggered_rules"] = _decode_json(data.get("triggered_rules"), [])
    return data


def list_tasks(limit: int = 20) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT t.id AS task_id, t.supplier_id, s.name AS supplier_name, t.status, t.risk_level,
                   t.total_score, t.recommendation, t.created_at, t.updated_at
            FROM diligence_tasks t
            JOIN suppliers s ON s.id = t.supplier_id
            ORDER BY t.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_task_detail(task_id: str) -> dict[str, Any] | None:
    task = get_task(task_id)
    if not task:
        return None
    risk = get_risk_assessment(task_id) or {
        "raw_score": None,
        "total_score": task.get("total_score"),
        "risk_level": task.get("risk_level"),
        "dimension_scores": {},
        "triggered_rules": [],
        "recommendation": task.get("recommendation"),
    }
    return {
        "task": {
            "id": task["id"],
            "status": task["status"],
            "summary": task.get("recommendation") or task.get("summary"),
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
        },
        "supplier": task["supplier"],
        "risk_assessment": risk,
        "dimension_scores": risk.get("dimension_scores", {}),
        "evidence_count": len(task.get("evidence", [])),
        "event_count": len(list_events(task_id)),
    }


def save_review(task_id: str, reviewer: str, decision: str, comment: str | None) -> dict[str, Any]:
    created = now_iso()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO human_reviews (task_id, reviewer, decision, comment, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, reviewer, decision, comment, created),
        )
        conn.execute(
            "UPDATE diligence_tasks SET status=?, updated_at=? WHERE id=?",
            ("reviewed", created, task_id),
        )
    return {"task_id": task_id, "reviewer": reviewer, "decision": decision, "comment": comment, "created_at": created}


def list_reviews(task_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM human_reviews WHERE task_id=? ORDER BY id", (task_id,)).fetchall()
    return [dict(row) for row in rows]

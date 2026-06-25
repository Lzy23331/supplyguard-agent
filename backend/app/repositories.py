import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .database import get_db
from .schemas import SupplierCreate


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_task_record(
    supplier: SupplierCreate,
    material_text: str | None = None,
    upload_ids: list[str] | None = None,
    query_type: str | None = None,
    company_name: str | None = None,
) -> str:
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
            (id, supplier_id, status, summary, error_message, material_text, upload_ids, query_type, company_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                supplier_id,
                "pending",
                None,
                None,
                material_text,
                json.dumps(upload_ids or [], ensure_ascii=False),
                query_type,
                company_name,
                created,
                created,
            ),
        )
    return task_id


def update_supplier_for_task(task_id: str, fields: dict[str, Any]) -> None:
    allowed = {
        "name",
        "website",
        "industry",
        "region",
        "annual_spend",
        "procurement_amount",
        "cooperation_type",
        "business_status",
        "company_age_years",
        "profile_completeness",
        "ownership_transparency",
        "urgency",
        "summary",
        "tags",
        "expected_risk_level",
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return
    if "tags" in updates:
        updates["tags"] = json.dumps(updates.get("tags") or [], ensure_ascii=False)
    assignments = ", ".join(f"{key}=?" for key in updates)
    with get_db() as conn:
        row = conn.execute("SELECT supplier_id FROM diligence_tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            return
        conn.execute(f"UPDATE suppliers SET {assignments} WHERE id=?", (*updates.values(), row["supplier_id"]))


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
            (id, task_id, supplier_id, source, category, title, content, severity, rule_signals,
             risk_keywords, economic_rationale, url, source_type, source_name, source_url, confidence,
             raw_text, normalized_content, extracted_by, should_use_for_scoring, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"{task_id}:{item.get('id')}" if item.get("id") else str(uuid.uuid4()),
                task_id,
                task["supplier_id"] if task else None,
                item.get("source") or item.get("source_type") or "user_input",
                item.get("category"),
                item["title"],
                item["content"],
                item.get("severity", "info"),
                json.dumps(item.get("rule_signals", []), ensure_ascii=False),
                json.dumps(item.get("risk_keywords", []), ensure_ascii=False),
                item.get("economic_rationale"),
                item.get("url") or item.get("source_url"),
                item.get("source_type") or ("mock_sample" if item.get("source") else "user_input"),
                item.get("source_name") or item.get("source") or "模拟公开信息",
                item.get("source_url") or item.get("url"),
                item.get("confidence"),
                item.get("raw_text") or item.get("source_quote"),
                item.get("normalized_content") or item.get("content"),
                item.get("extracted_by"),
                1 if item.get("should_use_for_scoring", (item.get("metadata_json") or {}).get("should_use_for_scoring", True)) else 0,
                json.dumps(item.get("metadata_json") or item.get("metadata") or {}, ensure_ascii=False),
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
        item["risk_keywords"] = _decode_json(item.get("risk_keywords"), [])
        item["metadata_json"] = _decode_json(item.get("metadata_json"), {})
    return evidence


def save_web_search_results(task_id: str, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    created = now_iso()
    with get_db() as conn:
        conn.execute("DELETE FROM web_search_results WHERE task_id=?", (task_id,))
        for row in rows:
            conn.execute(
                """
                INSERT INTO web_search_results
                (task_id, query, title, url, snippet, rank, source_type, source_name, domain,
                 domain_trust_level, domain_trust_score, entity_match_score, risk_relevance_score,
                 confidence, evidence_strength, entity_relation_type, decision, decision_reason,
                 matched_risk_keywords, is_duplicate, excluded_reason, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    row.get("query"),
                    row.get("title"),
                    row.get("url"),
                    row.get("snippet"),
                    row.get("rank"),
                    row.get("source_type", "web_search"),
                    row.get("source_name", "腾讯云联网搜索"),
                    row.get("domain"),
                    row.get("domain_trust_level"),
                    row.get("domain_trust_score"),
                    row.get("entity_match_score"),
                    row.get("risk_relevance_score"),
                    row.get("confidence"),
                    row.get("evidence_strength"),
                    row.get("entity_relation_type"),
                    row.get("decision"),
                    row.get("decision_reason"),
                    json.dumps(row.get("matched_risk_keywords", []), ensure_ascii=False),
                    1 if row.get("is_duplicate") else 0,
                    row.get("excluded_reason"),
                    json.dumps(row.get("metadata_json") or row.get("metadata") or {}, ensure_ascii=False),
                    created,
                ),
            )
    return len(rows)


def list_web_search_results(task_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM web_search_results WHERE task_id=? ORDER BY id", (task_id,)).fetchall()
    results = [dict(row) for row in rows]
    for item in results:
        item["matched_risk_keywords"] = _decode_json(item.get("matched_risk_keywords"), [])
        item["metadata_json"] = _decode_json(item.get("metadata_json"), {})
        item["is_duplicate"] = bool(item.get("is_duplicate"))
    return results

def save_company_profile_snapshots(task_id: str, rows: list[dict[str, Any]]) -> int:
    with get_db() as conn:
        task = conn.execute("SELECT supplier_id, company_name FROM diligence_tasks WHERE id=?", (task_id,)).fetchone()
        conn.execute("DELETE FROM company_profile_snapshots WHERE task_id=?", (task_id,))
        for row in rows:
            conn.execute(
                """
                INSERT INTO company_profile_snapshots
                (task_id, supplier_id, company_name, field_name, field_value, confidence, source_type,
                 source_name, source_url, query, extraction_method, requires_manual_verification,
                 reason, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    task["supplier_id"] if task else None,
                    row.get("company_name") or (task["company_name"] if task else None),
                    row.get("field_name"),
                    row.get("field_value"),
                    row.get("confidence"),
                    row.get("source_type", "web_search_profile"),
                    row.get("source_name", "腾讯云联网搜索"),
                    row.get("source_url"),
                    row.get("query"),
                    row.get("extraction_method", "rule_fallback"),
                    1 if row.get("requires_manual_verification", True) else 0,
                    row.get("reason"),
                    json.dumps(row.get("metadata_json") or row.get("metadata") or {}, ensure_ascii=False),
                    now_iso(),
                ),
            )
    return len(rows)


def list_company_profile_snapshots(task_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM company_profile_snapshots WHERE task_id=? ORDER BY id", (task_id,)).fetchall()
    results = [dict(row) for row in rows]
    for item in results:
        item["metadata_json"] = _decode_json(item.get("metadata_json"), {})
        item["requires_manual_verification"] = bool(item.get("requires_manual_verification"))
    return results


def latest_company_profile(task_id: str) -> dict[str, dict[str, Any]]:
    fields: dict[str, dict[str, Any]] = {}
    for item in list_company_profile_snapshots(task_id):
        name = item.get("field_name")
        if not name:
            continue
        current = fields.get(name)
        if current is None or (item.get("confidence") or 0) >= (current.get("confidence") or 0):
            fields[name] = item
    return fields


def task_diagnostics(task_id: str) -> dict[str, Any]:
    web_rows = list_web_search_results(task_id)
    profile_rows = list_company_profile_snapshots(task_id)
    evidence_rows = list_evidence(task_id)
    report = get_report(task_id)
    query_count = len({row.get("query") for row in web_rows if row.get("query")})
    real_url_count = sum(1 for row in web_rows if row.get("url") or row.get("source_url"))
    profile_non_empty_count = sum(1 for row in profile_rows if row.get("field_value"))
    scoring_evidence_count = sum(
        1
        for item in evidence_rows
        if item.get("source_type") == "web_search" and item.get("should_use_for_scoring") in (1, True)
    )
    scoring_evidence_count += sum(1 for row in web_rows if row.get("decision") == "score_evidence")
    provider_mode = None
    for row in web_rows:
        provider_mode = (row.get("metadata_json") or {}).get("provider_mode")
        if provider_mode:
            break
    if not provider_mode:
        provider_mode = "real" if web_rows else "none"
    return {
        "task_id": task_id,
        "provider_mode": provider_mode,
        "search_query_count": query_count,
        "web_search_result_count": len(web_rows),
        "real_url_count": real_url_count,
        "profile_snapshot_count": len(profile_rows),
        "profile_non_empty_count": profile_non_empty_count,
        "scoring_evidence_count": scoring_evidence_count,
        "evidence_item_count": len(evidence_rows),
        "report_available": bool(report),
        "web_search_results_preview": web_rows[:5],
        "company_profile_preview": profile_rows[:12],
    }

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
        "error_message": data.get("error_message"),
        "material_text": data.get("material_text"),
        "upload_ids": _decode_json(data.get("upload_ids"), []),
        "query_type": data.get("query_type"),
        "company_name": data.get("company_name"),
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
            SELECT t.id AS task_id, t.id AS id, t.supplier_id, s.name AS supplier_name, t.status, t.risk_level,
                   t.total_score, t.recommendation, t.created_at, t.updated_at,
                   s.cooperation_type, s.procurement_amount
            FROM diligence_tasks t
            JOIN suppliers s ON s.id = t.supplier_id
            ORDER BY t.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        diag = task_diagnostics(item["task_id"])
        item.update({key: diag[key] for key in [
            "provider_mode",
            "search_query_count",
            "web_search_result_count",
            "real_url_count",
            "profile_snapshot_count",
            "profile_non_empty_count",
            "scoring_evidence_count",
            "report_available",
        ]})
        result.append(item)
    return result

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
    diagnostics = task_diagnostics(task_id)
    events = list_events(task_id)
    evidence = list_evidence(task_id)
    return {
        "task": {
            "id": task["id"],
            "status": task["status"],
            "summary": task.get("recommendation") or task.get("summary"),
            "error_message": task.get("error_message"),
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
        },
        "id": task["id"],
        "task_id": task["id"],
        "status": task["status"],
        "supplier_id": task["supplier"]["id"],
        "risk_level": task.get("risk_level"),
        "total_score": task.get("total_score"),
        "recommendation": task.get("recommendation"),
        "error_message": task.get("error_message"),
        "supplier": task["supplier"],
        "risk_assessment": risk,
        "dimension_scores": risk.get("dimension_scores", {}),
        "evidence_count": len(evidence),
        "event_count": len(events),
        "company_profile": diagnostics["company_profile_preview"],
        "web_search_results": diagnostics["web_search_results_preview"],
        "events": events,
        "evidence": evidence[:20],
        "diagnostics": diagnostics,
        **{key: diagnostics[key] for key in [
            "provider_mode",
            "search_query_count",
            "web_search_result_count",
            "real_url_count",
            "profile_snapshot_count",
            "profile_non_empty_count",
            "scoring_evidence_count",
            "report_available",
        ]},
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







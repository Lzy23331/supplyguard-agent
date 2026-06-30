import sqlite3
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import get_settings
from .models.db_models import Base


def _db_path() -> Path:
    url = get_settings().database_url
    if not url.startswith("sqlite:///"):
        raise ValueError("Only sqlite:/// database URLs are supported in this demo")
    path = url.replace("sqlite:///", "", 1)
    raw = Path(path)
    if raw.is_absolute():
        return raw
    return (Path(__file__).resolve().parents[1] / raw).resolve()


def _sqlite_url() -> str:
    return f"sqlite:///{_db_path().as_posix()}"


engine = create_engine(_sqlite_url(), connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db():
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _needs_rebuild(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suppliers'").fetchone()
    if not row:
        return False
    cols = {item[1]: item[2].upper() for item in conn.execute("PRAGMA table_info(suppliers)").fetchall()}
    return cols.get("id") != "VARCHAR" and cols.get("id") != "TEXT"


def _drop_existing_tables(conn: sqlite3.Connection) -> None:
    for table in [
        "company_profile_snapshots",
        "web_search_results",
        "llm_call_logs",
        "agent_events",
        "human_reviews",
        "reports",
        "risk_assessments",
        "evidence_items",
        "diligence_tasks",
        "suppliers",
        "real_query_usage",
    ]:
        conn.execute(f"DROP TABLE IF EXISTS {table}")


def _ensure_columns(conn: sqlite3.Connection) -> None:
    task_row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='diligence_tasks'").fetchone()
    if task_row:
        cols = {item[1] for item in conn.execute("PRAGMA table_info(diligence_tasks)").fetchall()}
        for name, ddl in {"error_message": "TEXT", "material_text": "TEXT", "query_type": "TEXT", "company_name": "TEXT"}.items():
            if name not in cols:
                conn.execute(f"ALTER TABLE diligence_tasks ADD COLUMN {name} {ddl}")
        if "upload_ids" not in cols:
            conn.execute("ALTER TABLE diligence_tasks ADD COLUMN upload_ids TEXT")
    evidence_row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evidence_items'").fetchone()
    if evidence_row:
        cols = {item[1] for item in conn.execute("PRAGMA table_info(evidence_items)").fetchall()}
        additions = {
            "risk_keywords": "TEXT",
            "source_type": "TEXT",
            "source_name": "TEXT",
            "source_url": "TEXT",
            "confidence": "REAL",
            "raw_text": "TEXT",
            "normalized_content": "TEXT",
            "extracted_by": "TEXT",
            "should_use_for_scoring": "INTEGER",
            "metadata_json": "TEXT",
        }
        for name, ddl in additions.items():
            if name not in cols:
                conn.execute(f"ALTER TABLE evidence_items ADD COLUMN {name} {ddl}")
    web_search_row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='web_search_results'").fetchone()
    if web_search_row:
        cols = {item[1] for item in conn.execute("PRAGMA table_info(web_search_results)").fetchall()}
        additions = {
            "query": "TEXT",
            "title": "TEXT",
            "url": "TEXT",
            "snippet": "TEXT",
            "rank": "INTEGER",
            "source_type": "TEXT",
            "source_name": "TEXT",
            "domain": "TEXT",
            "domain_trust_level": "TEXT",
            "domain_trust_score": "REAL",
            "entity_match_score": "REAL",
            "risk_relevance_score": "REAL",
            "confidence": "REAL",
            "evidence_strength": "TEXT",
            "entity_relation_type": "TEXT",
            "decision": "TEXT",
            "decision_reason": "TEXT",
            "matched_risk_keywords": "TEXT",
            "is_duplicate": "INTEGER",
            "excluded_reason": "TEXT",
            "metadata_json": "TEXT",
        }
        for name, ddl in additions.items():
            if name not in cols:
                conn.execute(f"ALTER TABLE web_search_results ADD COLUMN {name} {ddl}")
    profile_row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_profile_snapshots'").fetchone()
    if profile_row:
        cols = {item[1] for item in conn.execute("PRAGMA table_info(company_profile_snapshots)").fetchall()}
        additions = {
            "supplier_id": "TEXT",
            "company_name": "TEXT",
            "field_name": "TEXT",
            "field_value": "TEXT",
            "confidence": "REAL",
            "source_type": "TEXT",
            "source_name": "TEXT",
            "source_url": "TEXT",
            "query": "TEXT",
            "extraction_method": "TEXT",
            "requires_manual_verification": "INTEGER",
            "reason": "TEXT",
            "metadata_json": "TEXT",
        }
        for name, ddl in additions.items():
            if name not in cols:
                conn.execute(f"ALTER TABLE company_profile_snapshots ADD COLUMN {name} {ddl}")
def init_db() -> None:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        if _needs_rebuild(conn):
            _drop_existing_tables(conn)
            conn.commit()
    Base.metadata.create_all(bind=engine)
    with sqlite3.connect(path) as conn:
        _ensure_columns(conn)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS real_query_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usage_date TEXT NOT NULL,
                task_id TEXT,
                company_name TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()






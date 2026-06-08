import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import get_settings


def _db_path() -> Path:
    url = get_settings().database_url
    if not url.startswith("sqlite:///"):
        raise ValueError("Only sqlite:/// database URLs are supported in this demo")
    path = url.replace("sqlite:///", "", 1)
    return (Path(__file__).resolve().parents[1] / path).resolve()


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


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                website TEXT,
                industry TEXT,
                region TEXT,
                annual_spend REAL,
                cooperation_type TEXT,
                sample_key TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS diligence_tasks (
                id TEXT PRIMARY KEY,
                supplier_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                risk_level TEXT,
                total_score INTEGER,
                recommendation TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            );
            CREATE TABLE IF NOT EXISTS evidence_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                severity TEXT NOT NULL,
                url TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS risk_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                dimension TEXT NOT NULL,
                score INTEGER NOT NULL,
                level TEXT NOT NULL,
                rationale TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL UNIQUE,
                markdown TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS human_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                decision TEXT NOT NULL,
                comment TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                status TEXT NOT NULL,
                summary TEXT NOT NULL,
                tool_calls TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


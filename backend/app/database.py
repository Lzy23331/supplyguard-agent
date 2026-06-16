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
        "agent_events",
        "human_reviews",
        "reports",
        "risk_assessments",
        "evidence_items",
        "diligence_tasks",
        "suppliers",
    ]:
        conn.execute(f"DROP TABLE IF EXISTS {table}")


def init_db() -> None:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        if _needs_rebuild(conn):
            _drop_existing_tables(conn)
            conn.commit()
    Base.metadata.create_all(bind=engine)

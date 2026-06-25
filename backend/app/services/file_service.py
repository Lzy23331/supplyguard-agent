import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from app.config import get_settings
from app.database import get_db, init_db
from app.repositories import now_iso
from app.tools.file_parser_tool import FileParserTool

ALLOWED_TYPES = {"txt", "md", "csv", "pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def _storage_root() -> Path:
    return get_settings().project_root / "backend" / "storage"


def _uploads_dir() -> Path:
    path = _storage_root() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _parsed_dir() -> Path:
    path = _storage_root() / "parsed_texts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _summary(text: str) -> str:
    clean = " ".join(text.split())
    return clean[:300]


def save_and_parse_material_file(original_filename: str, file_obj: BinaryIO) -> dict:
    init_db()
    suffix = Path(original_filename or "").suffix.lower().lstrip(".")
    if suffix not in ALLOWED_TYPES:
        raise ValueError("仅支持 .txt、.md、.csv、.pdf 文件")

    upload_id = f"upload_{uuid.uuid4().hex[:16]}"
    safe_name = f"{upload_id}.{suffix}"
    file_path = _uploads_dir() / safe_name
    parsed_path = _parsed_dir() / f"{upload_id}.txt"

    with file_path.open("wb") as target:
        shutil.copyfileobj(file_obj, target)
    size = file_path.stat().st_size
    if size > MAX_FILE_SIZE:
        file_path.unlink(missing_ok=True)
        raise ValueError("文件大小不能超过 10MB")

    created = now_iso()
    record = {
        "id": upload_id,
        "filename": safe_name,
        "original_filename": original_filename,
        "file_type": suffix,
        "file_size": size,
        "file_path": str(file_path),
        "parsed_text_path": str(parsed_path),
        "status": "uploaded",
        "summary": None,
        "error_message": None,
        "created_at": created,
        "updated_at": created,
    }
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO uploaded_materials
            (id, filename, original_filename, file_type, file_size, file_path, parsed_text_path,
             status, summary, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(record.values()),
        )

    try:
        text = FileParserTool().parse(file_path, suffix)[:20000]
        parsed_path.write_text(text, encoding="utf-8")
        update_upload_record(upload_id, status="parsed", summary=_summary(text), error_message=None)
        record.update({"status": "parsed", "summary": _summary(text), "text_length": len(text)})
    except Exception as exc:
        update_upload_record(upload_id, status="failed", error_message=str(exc))
        record.update({"status": "failed", "error_message": str(exc), "text_length": 0})
    return record


def update_upload_record(upload_id: str, **fields) -> None:
    fields["updated_at"] = now_iso()
    assignments = ", ".join(f"{key}=?" for key in fields)
    with get_db() as conn:
        conn.execute(f"UPDATE uploaded_materials SET {assignments} WHERE id=?", (*fields.values(), upload_id))


def get_upload_record(upload_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM uploaded_materials WHERE id=?", (upload_id,)).fetchone()
    return dict(row) if row else None


def get_parsed_text(upload_id: str) -> tuple[dict | None, str | None]:
    record = get_upload_record(upload_id)
    if not record or record.get("status") != "parsed":
        return record, None
    path = Path(record["parsed_text_path"])
    return record, path.read_text(encoding="utf-8") if path.exists() else None

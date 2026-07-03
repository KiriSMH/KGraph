from pathlib import Path
import shutil
from typing import Any

from fastapi import APIRouter, File, UploadFile

from app.services.vector_service import index_file


router = APIRouter(tags=["upload"])

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "data" / "uploads"


def _safe_filename(filename: str) -> str:
    return Path(filename or "uploaded_file").name


@router.post("/upload")
def upload_file(file: UploadFile = File(...)) -> dict[str, Any]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = _safe_filename(file.filename or "uploaded_file")
    target_path = UPLOAD_DIR / filename

    with target_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)

    index_result = index_file(target_path, filename)

    return {
        "filename": filename,
        "status": "uploaded",
        "size": target_path.stat().st_size,
        "index_status": index_result.get("status", "unknown"),
        "indexed_chunks": index_result.get("chunks", 0),
        "index_message": index_result.get("message", ""),
    }

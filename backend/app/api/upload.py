from pathlib import Path
import shutil

from fastapi import APIRouter, File, UploadFile


router = APIRouter(tags=["upload"])

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "data" / "uploads"


def _safe_filename(filename: str) -> str:
    return Path(filename or "uploaded_file").name


@router.post("/upload")
def upload_file(file: UploadFile = File(...)) -> dict[str, str | int]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = _safe_filename(file.filename or "uploaded_file")
    target_path = UPLOAD_DIR / filename

    with target_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)

    return {
        "filename": filename,
        "status": "uploaded",
        "size": target_path.stat().st_size,
    }

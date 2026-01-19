from __future__ import annotations

import re
import uuid
import zipfile
from pathlib import Path
from typing import Iterable, List, Optional

from fastapi import HTTPException, UploadFile

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")

MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_PDF = {".pdf"}
ALLOWED_IMAGES = {".jpg", ".jpeg", ".png"}
ALLOWED_DOCX = {".docx"}


def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_extension(filename: str, allowed: Iterable[str]) -> None:
    ext = get_extension(filename)
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


def generate_filename(extension: str) -> str:
    return f"{uuid.uuid4().hex}{extension}"


def save_upload_file(upload_file: UploadFile, allowed: Iterable[str]) -> Path:
    ensure_dirs()
    validate_extension(upload_file.filename or "", allowed)

    extension = get_extension(upload_file.filename or "")
    safe_name = generate_filename(extension)
    destination = UPLOAD_DIR / safe_name

    size = 0
    with destination.open("wb") as buffer:
        while True:
            chunk = upload_file.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_FILE_SIZE_BYTES:
                buffer.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large")
            buffer.write(chunk)

    if size == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Empty upload")

    return destination


def save_multiple_uploads(files: List[UploadFile], allowed: Iterable[str]) -> List[Path]:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    saved: List[Path] = []
    try:
        for f in files:
            saved.append(save_upload_file(f, allowed))
        return saved
    except Exception:
        for p in saved:
            p.unlink(missing_ok=True)
        raise


def create_output_path(extension: str) -> Path:
    ensure_dirs()
    return OUTPUT_DIR / generate_filename(extension)


def create_zip(paths: List[Path], zip_name: str = "files.zip") -> Path:
    output_path = create_output_path(".zip")
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for p in paths:
            zipf.write(p, arcname=p.name)
    return output_path


def safe_cleanup(paths: Iterable[Optional[Path]]) -> None:
    for path in paths:
        if not path:
            continue
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass


def validate_page_range(start: int, end: int, total: int) -> None:
    if start < 1 or end < 1 or start > end or end > total:
        raise HTTPException(status_code=400, detail="Invalid page range")


def sanitize_filename(name: str | None, default_name: str, extension: str) -> str:
    if not name:
        return default_name
    base = Path(name).name.strip()
    if not base:
        return default_name
    stem = Path(base).stem
    stem = re.sub(r"[^A-Za-z0-9 _.-]", "_", stem).strip()
    if not stem:
        stem = Path(default_name).stem
    ext = Path(base).suffix.lower()
    if ext != extension:
        ext = extension
    return f"{stem}{ext}"

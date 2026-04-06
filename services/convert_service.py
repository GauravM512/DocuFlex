from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

from fastapi import HTTPException

import img2pdf

# Import your other utilities
from services.file_utils import create_output_path
from services.lo_worker_manager import LibreOfficeWorkerManager
from services.pdf_service import pdf_to_images
from pdf2docx import Converter

# --- CONFIGURATION ---
# Project root (DocuFlex/) resolved from this file location
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# LibreOffice Python executable (portable on Windows, system install on Linux)
LO_PYTHON_PATH_WINDOWS = PROJECT_ROOT / "libreoffice" / "App" / "libreoffice" / "program" / "python.exe"
LO_PYTHON_PATH_LINUX_CANDIDATES = (
    Path("/usr/bin/python3"),
)

# Path to the worker script
WORKER_SCRIPT = Path(__file__).parent / "uno_worker.py"

_lo_worker_manager: LibreOfficeWorkerManager | None = None

def resolve_lo_python_path() -> Path:
    env_path = os.environ.get("LO_PYTHON_PATH")
    if env_path:
        candidate = Path(env_path)
        if not candidate.exists():
            raise HTTPException(
                status_code=500,
                detail=f"LO_PYTHON_PATH is set but not found: {candidate}"
            )
        return candidate

    if sys.platform.startswith("win") and LO_PYTHON_PATH_WINDOWS.exists():
        return LO_PYTHON_PATH_WINDOWS

    for candidate in LO_PYTHON_PATH_LINUX_CANDIDATES:
        if candidate.exists():
            return candidate

    raise HTTPException(
        status_code=500,
        detail=(
            "LibreOffice Python executable not found. "
            "Set LO_PYTHON_PATH to your LibreOffice python binary."
        ),
    )


def get_lo_worker_manager() -> LibreOfficeWorkerManager:
    global _lo_worker_manager
    if _lo_worker_manager is None:
        _lo_worker_manager = LibreOfficeWorkerManager(
            lo_python=resolve_lo_python_path(),
            worker_script=WORKER_SCRIPT,
        )
    return _lo_worker_manager


def start_lo_worker_manager() -> None:
    get_lo_worker_manager().start()


def stop_lo_worker_manager() -> None:
    global _lo_worker_manager
    if _lo_worker_manager is not None:
        _lo_worker_manager.shutdown()
        _lo_worker_manager = None


def pdf_to_word(pdf_path: Path) -> Path:
    output_path = create_output_path(".docx")
    try:
        converter = Converter(str(pdf_path))
        converter.convert(str(output_path))
        converter.close()
        return output_path
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"PDF to Word failed: {exc}")


def images_to_pdf(image_paths: List[Path]) -> Path:
    output_path = create_output_path(".pdf")

    if not image_paths:
        raise HTTPException(status_code=400, detail="No images to convert")

    try:
        # Convert Path objects → strings (img2pdf prefers str)
        paths = [str(p) for p in image_paths]

        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(paths))

        return output_path

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Image to PDF failed: {exc}")

def pdf_to_image(pdf_path: Path) -> List[Path]:
    return pdf_to_images(pdf_path)

def common_document_to_pdf(doc_path: Path) -> Path:
    """
    Converts doc to PDF by sending a job to the persistent LibreOffice worker.
    """
    output_path = create_output_path(".pdf")
    try:
        return get_lo_worker_manager().convert(doc_path.resolve(), output_path.resolve())
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Conversion error: {exc}")

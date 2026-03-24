from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List

from fastapi import HTTPException
from PIL import Image

# Import your other utilities
from services.file_utils import create_output_path
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

# Path to the worker script we just created
WORKER_SCRIPT = Path(__file__).parent / "uno_worker.py"

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
    try:
        images = [Image.open(p).convert("RGB") for p in image_paths]
        if not images:
            raise HTTPException(status_code=400, detail="No images to convert")
        first, rest = images[0], images[1:]
        first.save(output_path, save_all=True, append_images=rest)
        for img in images:
            img.close()
        return output_path
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Image to PDF failed: {exc}")

def pdf_to_image(pdf_path: Path) -> List[Path]:
    return pdf_to_images(pdf_path)

def common_document_to_pdf(doc_path: Path) -> Path:
    """
    Converts doc to PDF by calling the LO Python worker script via subprocess.
    Requires the LO Server to be running on port 8100.
    """
    output_path = create_output_path(".pdf")

    lo_python = resolve_lo_python_path()

    # Construct the command
    # Syntax: <lo_python.exe> <worker_script.py> <input> <output>
    cmd = [
        str(lo_python),
        str(WORKER_SCRIPT),
        str(doc_path.resolve()),
        str(output_path.resolve())
    ]

    try:
        # Run the worker script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Check for errors
        if result.returncode != 0:
            # Extract error message from worker stderr
            error_msg = result.stderr.strip() or "Unknown UNO error"
            # specific check for connection issues
            if "CONNECTION_ERROR" in error_msg:
                raise HTTPException(
                    status_code=503, 
                    detail="Could not connect to LibreOffice Server. Is it running on port 8100?"
                )
            
            raise HTTPException(
                status_code=400, 
                detail=f"Conversion failed: {error_msg}"
            )

        if not output_path.exists():
             raise HTTPException(status_code=500, detail="Worker finished but no PDF created.")

        return output_path

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Conversion timed out")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Subprocess error: {exc}")
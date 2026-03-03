from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

from pdf2docx import Converter
from fastapi import HTTPException
from PIL import Image

from services.file_utils import create_output_path
from services.pdf_service import pdf_to_images

LIBREOFFICE_SOFFICE_PATH = Path(
    r"E:\TYBCA final year project\DocuFlex\libreoffice\App\libreoffice\program\soffice.exe"
)
LIBREOFFICE_RELATIVE_SOFFICE_PATH = Path("libreoffice/App/libreoffice/program/soffice.exe")


def _resolve_soffice_path() -> str:
    env_path = os.getenv("DOCUFLEX_SOFFICE_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    if LIBREOFFICE_SOFFICE_PATH.exists():
        return str(LIBREOFFICE_SOFFICE_PATH)
    if LIBREOFFICE_RELATIVE_SOFFICE_PATH.exists():
        return str(LIBREOFFICE_RELATIVE_SOFFICE_PATH)
    raise HTTPException(
        status_code=500,
        detail="LibreOffice executable not found. Set DOCUFLEX_SOFFICE_PATH or verify bundled path.",
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
    output_path = create_output_path(".pdf")
    soffice_path = _resolve_soffice_path()
    temp_out_dir = Path(tempfile.mkdtemp(prefix="libreoffice-"))
    try:
        result = subprocess.run(
            [
                soffice_path,
                "--headless",
                "--nologo",
                "--nodefault",
                "--nofirststartwizard",
                "--nolockcheck",
                "--convert-to",
                "pdf",
                "--outdir",
                str(temp_out_dir),
                str(doc_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        if result.returncode != 0:
            error_text = (result.stderr or result.stdout or "Unknown LibreOffice error").strip()
            raise HTTPException(status_code=400, detail=f"LibreOffice conversion failed: {error_text}")

        converted_path = temp_out_dir / f"{doc_path.stem}.pdf"
        if not converted_path.exists():
            converted_candidates = list(temp_out_dir.glob("*.pdf"))
            if not converted_candidates:
                raise HTTPException(
                    status_code=400,
                    detail="LibreOffice did not produce a PDF output file",
                )
            converted_path = converted_candidates[0]

        shutil.move(str(converted_path), str(output_path))
        return output_path
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="LibreOffice conversion timed out")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Document to PDF failed: {exc}")
    finally:
        shutil.rmtree(temp_out_dir, ignore_errors=True)

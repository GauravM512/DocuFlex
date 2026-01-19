from __future__ import annotations

from pathlib import Path
from typing import List

import fitz
import pytesseract
from fastapi import HTTPException
from PIL import Image


def ocr_image(image_path: Path) -> str:
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        img.close()
        return text
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OCR failed: {exc}")


def ocr_pdf(pdf_path: Path, dpi: int = 200) -> str:
    try:
        doc = fitz.open(pdf_path)
        texts: List[str] = []
        for i in range(doc.page_count):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            texts.append(pytesseract.image_to_string(img))
            img.close()
        doc.close()
        return "\n".join(texts)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OCR PDF failed: {exc}")

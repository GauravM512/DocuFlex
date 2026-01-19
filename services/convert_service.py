from __future__ import annotations

from pathlib import Path
from typing import List

import pymupdf
from pdf2docx import Converter
from fastapi import HTTPException
from docx import Document
from PIL import Image

from services.file_utils import create_output_path
from services.pdf_service import pdf_to_images


def pdf_to_word(pdf_path: Path) -> Path:
    output_path = create_output_path(".docx")
    try:
        converter = Converter(str(pdf_path))
        converter.convert(str(output_path))
        converter.close()
        return output_path
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"PDF to Word failed: {exc}")


def word_to_pdf(docx_path: Path) -> Path:
    output_path = create_output_path(".pdf")
    try:
        word_doc = Document(str(docx_path))
        pdf_doc = pymupdf.open()
        text = "\n".join([p.text for p in word_doc.paragraphs])
        if text.strip():
            max_chars = 2500
            chunks = [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
            for chunk in chunks:
                page = pdf_doc.new_page()
                page.insert_textbox(
                    pymupdf.Rect(50, 50, 550, 780),
                    chunk,
                    fontsize=12,
                    color=(0, 0, 0),
                )
        pdf_doc.save(output_path)
        pdf_doc.close()
        return output_path
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Word to PDF failed: {exc}")


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

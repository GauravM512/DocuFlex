from __future__ import annotations

from pathlib import Path
from typing import List

import pymupdf
from pypdf import PdfWriter
from fastapi import HTTPException

from services.file_utils import create_output_path, validate_page_range


def merge_pdfs(pdf_paths: List[Path]) -> Path:
    output_path = create_output_path(".pdf")
    try:
        merged = pymupdf.open()
        for p in pdf_paths:
            doc = pymupdf.open(p)
            merged.insert_pdf(doc)
            doc.close()
        merged.save(output_path)
        merged.close()
        return output_path
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Merge failed: {exc}")


def split_pdf_by_range(pdf_path: Path, start: int, end: int) -> Path:
    output_path = create_output_path(".pdf")
    try:
        doc = pymupdf.open(pdf_path)
        validate_page_range(start, end, doc.page_count)
        new_doc = pymupdf.open()
        new_doc.insert_pdf(doc, from_page=start - 1, to_page=end - 1)
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        return output_path
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Split failed: {exc}")


def split_pdf_by_pages(pdf_path: Path, pages: List[int]) -> Path:
    output_path = create_output_path(".pdf")
    try:
        doc = pymupdf.open(pdf_path)
        total = doc.page_count
        if not pages:
            raise HTTPException(status_code=400, detail="No pages selected")
        if any(p < 1 or p > total for p in pages):
            raise HTTPException(status_code=400, detail="Invalid page selection")
        new_doc = pymupdf.open()
        for p in pages:
            new_doc.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        return output_path
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Split failed: {exc}")


def reorder_pdf_pages(pdf_path: Path, page_order: List[int]) -> Path:
    output_path = create_output_path(".pdf")
    try:
        doc = pymupdf.open(pdf_path)
        total = doc.page_count
        if sorted(page_order) != list(range(1, total + 1)):
            raise HTTPException(status_code=400, detail="Invalid page order")
        new_doc = pymupdf.open()
        for p in page_order:
            new_doc.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        return output_path
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Reorder failed: {exc}")


def compress_pdf(pdf_path: Path, quality: int = 60) -> Path:
    output_path = create_output_path(".pdf")
    try:
        if quality < 1 or quality > 100:
            raise HTTPException(status_code=400, detail="Quality must be between 1 and 100")
        writer = PdfWriter(clone_from=str(pdf_path))
        for page in writer.pages:
            for img in page.images:
                img.replace(img.image, quality=quality)
        with output_path.open("wb") as f:
            writer.write(f)
        return output_path
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Compress failed: {exc}")


def pdf_to_images(pdf_path: Path, dpi: int = 200) -> List[Path]:
    output_paths: List[Path] = []
    try:
        doc = pymupdf.open(pdf_path)
        for i in range(doc.page_count):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=dpi)
            img_path = create_output_path(".png")
            pix.save(img_path)
            output_paths.append(img_path)
        doc.close()
        return output_paths
    except Exception as exc:
        for p in output_paths:
            p.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"PDF to image failed: {exc}")

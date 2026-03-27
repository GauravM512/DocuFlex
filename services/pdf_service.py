from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import List

import pymupdf
from fastapi import HTTPException
from PIL import Image

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


def compress_pdf(pdf_path: Path, dpi: int = 72, quality: int = 50) -> Path:
    output_path = create_output_path(".pdf")
    doc = None
    compressed_doc = None
    try:
        if dpi < 30 or dpi > 300:
            raise HTTPException(status_code=400, detail="DPI must be between 30 and 300")
        if quality < 1 or quality > 100:
            raise HTTPException(status_code=400, detail="Quality must be between 1 and 100")

        doc = pymupdf.open(pdf_path)
        compressed_doc = pymupdf.open()

        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=dpi, alpha=False)

            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img_buffer = BytesIO()
            image.save(img_buffer, format="JPEG", quality=quality, optimize=True)
            image.close()
            img_buffer.seek(0)

            new_page = compressed_doc.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(page.rect, stream=img_buffer.read())

        compressed_doc.save(output_path, deflate=True)
        return output_path
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Compress failed: {exc}")
    finally:
        try:
            if compressed_doc is not None:
                compressed_doc.close()
        except Exception:
            pass
        try:
            if doc is not None:
                doc.close()
        except Exception:
            pass


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


def pdf_to_preview_data_urls(pdf_path: Path, dpi: int = 72, quality: int = 42) -> List[dict]:
    pages: List[dict] = []
    doc = None
    try:
        if dpi < 50 or dpi > 200:
            raise HTTPException(status_code=400, detail="Preview DPI must be between 50 and 200")
        if quality < 20 or quality > 95:
            raise HTTPException(status_code=400, detail="Preview quality must be between 20 and 95")

        doc = pymupdf.open(pdf_path)

        # Adaptive quality for large PDFs to keep previews responsive.
        effective_dpi = dpi
        effective_quality = quality
        max_preview_side = 960
        if doc.page_count > 40:
            effective_dpi = min(effective_dpi, 68)
            effective_quality = min(effective_quality, 40)
            max_preview_side = min(max_preview_side, 800)
        if doc.page_count > 120:
            effective_dpi = min(effective_dpi, 58)
            effective_quality = min(effective_quality, 34)
            max_preview_side = min(max_preview_side, 640)
        if doc.page_count > 250:
            effective_dpi = min(effective_dpi, 50)
            effective_quality = min(effective_quality, 30)
            max_preview_side = min(max_preview_side, 520)

        data_url_prefix = "data:image/webp;base64,"
        base_scale = effective_dpi / 72.0

        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            page_max_side = max(page.rect.width, page.rect.height)
            scaled_limit = max_preview_side / page_max_side if page_max_side else base_scale
            render_scale = min(base_scale, scaled_limit)
            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(render_scale, render_scale),
                alpha=False,
                annots=False,
            )
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img_buffer = BytesIO()
            image.save(img_buffer, format="WEBP", quality=effective_quality, method=6)
            image.close()
            img_buffer.seek(0)
            img_bytes = img_buffer.read()
            data_url = data_url_prefix + base64.b64encode(img_bytes).decode("ascii")
            pages.append({"page": page_num + 1, "dataUrl": data_url})

        return pages
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Preview failed: {exc}")
    finally:
        try:
            if doc is not None:
                doc.close()
        except Exception:
            pass

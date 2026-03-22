from __future__ import annotations

from typing import List

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

from services.file_utils import ALLOWED_PDF, safe_cleanup, sanitize_filename, save_multiple_uploads, save_upload_file
from services.pdf_service import compress_pdf, merge_pdfs, pdf_to_preview_data_urls, reorder_pdf_pages, split_pdf_by_pages, split_pdf_by_range

router = APIRouter(prefix="/api/pdf", tags=["pdf-utils"])


@router.post("/preview")
async def preview(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    pdf_path = save_upload_file(file, ALLOWED_PDF)
    pages = pdf_to_preview_data_urls(pdf_path)
    background_tasks.add_task(safe_cleanup, [pdf_path])
    return {"pages": pages}


@router.post("/merge")
async def merge(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    filename: str | None = Form(None),
):
    pdf_paths = save_multiple_uploads(files, ALLOWED_PDF)
    output_path = merge_pdfs(pdf_paths)
    background_tasks.add_task(safe_cleanup, [*pdf_paths, output_path])
    safe_name = sanitize_filename(filename, "merged.pdf", ".pdf")
    return FileResponse(output_path, filename=safe_name)


@router.post("/split")
async def split(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pages: str | None = Form(None),
    start: int | None = Form(None),
    end: int | None = Form(None),
    filename: str | None = Form(None),
):
    pdf_path = save_upload_file(file, ALLOWED_PDF)
    if pages:
        try:
            page_list = [int(p.strip()) for p in pages.split(",") if p.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Pages must be comma-separated integers")
        output_path = split_pdf_by_pages(pdf_path, page_list)
    else:
        if start is None or end is None:
            raise HTTPException(status_code=400, detail="Provide pages or a start/end range")
        output_path = split_pdf_by_range(pdf_path, start, end)
    background_tasks.add_task(safe_cleanup, [pdf_path, output_path])
    safe_name = sanitize_filename(filename, "split.pdf", ".pdf")
    return FileResponse(output_path, filename=safe_name)


@router.post("/reorder")
async def reorder(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    order: str = Form(...),
    filename: str | None = Form(None),
):
    pdf_path = save_upload_file(file, ALLOWED_PDF)
    try:
        page_order = [int(p.strip()) for p in order.split(",") if p.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Order must be comma-separated integers")
    if not page_order:
        raise HTTPException(status_code=400, detail="Order cannot be empty")
    output_path = reorder_pdf_pages(pdf_path, page_order)
    background_tasks.add_task(safe_cleanup, [pdf_path, output_path])
    safe_name = sanitize_filename(filename, "reordered.pdf", ".pdf")
    return FileResponse(output_path, filename=safe_name)


@router.post("/compress")
async def compress(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dpi: int = Form(72),
    quality: int = Form(50),
    filename: str | None = Form(None),
):
    pdf_path = save_upload_file(file, ALLOWED_PDF)
    output_path = compress_pdf(pdf_path, dpi=dpi, quality=quality)
    background_tasks.add_task(safe_cleanup, [pdf_path, output_path])
    safe_name = sanitize_filename(filename, "compressed.pdf", ".pdf")
    return FileResponse(output_path, filename=safe_name)

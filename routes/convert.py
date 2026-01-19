from __future__ import annotations

from typing import List

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile
from fastapi.responses import FileResponse

from services.convert_service import images_to_pdf, pdf_to_image, pdf_to_word, word_to_pdf
from services.file_utils import (
    ALLOWED_DOCX,
    ALLOWED_IMAGES,
    ALLOWED_PDF,
    create_zip,
    safe_cleanup,
    sanitize_filename,
    save_multiple_uploads,
    save_upload_file,
)

router = APIRouter(prefix="/api/convert", tags=["convert"])


@router.post("/pdf-to-word")
async def convert_pdf_to_word(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    filename: str | None = Form(None),
):
    pdf_path = save_upload_file(file, ALLOWED_PDF)
    output_path = pdf_to_word(pdf_path)
    background_tasks.add_task(safe_cleanup, [pdf_path, output_path])
    safe_name = sanitize_filename(filename, "converted.docx", ".docx")
    return FileResponse(output_path, filename=safe_name)


@router.post("/word-to-pdf")
async def convert_word_to_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    filename: str | None = Form(None),
):
    docx_path = save_upload_file(file, ALLOWED_DOCX)
    output_path = word_to_pdf(docx_path)
    background_tasks.add_task(safe_cleanup, [docx_path, output_path])
    safe_name = sanitize_filename(filename, "converted.pdf", ".pdf")
    return FileResponse(output_path, filename=safe_name)


@router.post("/image-to-pdf")
async def convert_image_to_pdf(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    filename: str | None = Form(None),
):
    image_paths = save_multiple_uploads(files, ALLOWED_IMAGES)
    output_path = images_to_pdf(image_paths)
    background_tasks.add_task(safe_cleanup, [*image_paths, output_path])
    safe_name = sanitize_filename(filename, "converted.pdf", ".pdf")
    return FileResponse(output_path, filename=safe_name)


@router.post("/pdf-to-image")
async def convert_pdf_to_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    filename: str | None = Form(None),
):
    pdf_path = save_upload_file(file, ALLOWED_PDF)
    image_paths = pdf_to_image(pdf_path)
    if len(image_paths) == 1:
        output_path = image_paths[0]
        background_tasks.add_task(safe_cleanup, [pdf_path, output_path])
        safe_name = sanitize_filename(filename, "page-1.png", ".png")
        return FileResponse(output_path, filename=safe_name)

    zip_path = create_zip(image_paths)
    background_tasks.add_task(safe_cleanup, [pdf_path, *image_paths, zip_path])
    safe_name = sanitize_filename(filename, "pages.zip", ".zip")
    return FileResponse(zip_path, filename=safe_name)

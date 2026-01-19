from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, File, UploadFile

from services.file_utils import ALLOWED_IMAGES, ALLOWED_PDF, safe_cleanup, save_upload_file
from services.ocr_service import ocr_image, ocr_pdf

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/image")
async def ocr_from_image(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    image_path = save_upload_file(file, ALLOWED_IMAGES)
    text = ocr_image(image_path)
    background_tasks.add_task(safe_cleanup, [image_path])
    return {"text": text}


@router.post("/pdf")
async def ocr_from_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    pdf_path = save_upload_file(file, ALLOWED_PDF)
    text = ocr_pdf(pdf_path)
    background_tasks.add_task(safe_cleanup, [pdf_path])
    return {"text": text}

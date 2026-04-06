from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routes.convert import router as convert_router
from routes.pdf_utils import router as pdf_router
from services.convert_service import start_lo_worker_manager, stop_lo_worker_manager
from services.file_utils import ensure_dirs

app = FastAPI(title="DocuFlex", version="1.0.0")
app.add_middleware(GZipMiddleware, minimum_size=1024)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(convert_router)
app.include_router(pdf_router)


@app.on_event("startup")
async def startup() -> None:
    ensure_dirs()
    start_lo_worker_manager()


@app.on_event("shutdown")
async def shutdown() -> None:
    stop_lo_worker_manager()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/qr", response_class=HTMLResponse)
async def qr_page(request: Request):
    return templates.TemplateResponse(request=request, name="qr.html", context={})


@app.get("/convert", response_class=HTMLResponse)
async def convert_page(request: Request):
    return templates.TemplateResponse(request=request, name="convert.html", context={})


@app.get("/convert/pdf-to-word", response_class=HTMLResponse)
async def convert_pdf_to_word_page(request: Request):
    return templates.TemplateResponse(request=request, name="convert_pdf_to_word.html", context={})


@app.get("/convert/common-to-pdf", response_class=HTMLResponse)
async def convert_common_to_pdf_page(request: Request):
    return templates.TemplateResponse(request=request, name="convert_common_to_pdf.html", context={})


@app.get("/convert/image-to-pdf", response_class=HTMLResponse)
async def convert_image_to_pdf_page(request: Request):
    return templates.TemplateResponse(request=request, name="convert_image_to_pdf.html", context={})


@app.get("/convert/pdf-to-image", response_class=HTMLResponse)
async def convert_pdf_to_image_page(request: Request):
    return templates.TemplateResponse(request=request, name="convert_pdf_to_image.html", context={})


@app.get("/pdf", response_class=HTMLResponse)
async def pdf_page(request: Request):
    return templates.TemplateResponse(request=request, name="pdf.html", context={})


@app.get("/pdf/merge", response_class=HTMLResponse)
async def pdf_merge_page(request: Request):
    return templates.TemplateResponse(request=request, name="pdf_merge.html", context={})


@app.get("/pdf/split", response_class=HTMLResponse)
async def pdf_split_page(request: Request):
    return templates.TemplateResponse(request=request, name="pdf_split.html", context={})


@app.get("/pdf/reorder", response_class=HTMLResponse)
async def pdf_reorder_page(request: Request):
    return templates.TemplateResponse(request=request, name="pdf_reorder.html", context={})


@app.get("/pdf/compress", response_class=HTMLResponse)
async def pdf_compress_page(request: Request):
    return templates.TemplateResponse(request=request, name="pdf_compress.html", context={})

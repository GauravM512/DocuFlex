from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routes.convert import router as convert_router
from routes.pdf_utils import router as pdf_router
from services.file_utils import ensure_dirs

app = FastAPI(title="DocuFlex", version="1.0.0")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(convert_router)
app.include_router(pdf_router)


@app.on_event("startup")
def startup() -> None:
    ensure_dirs()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/qr", response_class=HTMLResponse)
async def qr_page(request: Request):
    return templates.TemplateResponse("qr.html", {"request": request})


@app.get("/convert", response_class=HTMLResponse)
async def convert_page(request: Request):
    return templates.TemplateResponse("convert.html", {"request": request})


@app.get("/convert/pdf-to-word", response_class=HTMLResponse)
async def convert_pdf_to_word_page(request: Request):
    return templates.TemplateResponse("convert_pdf_to_word.html", {"request": request})


@app.get("/convert/common-to-pdf", response_class=HTMLResponse)
async def convert_common_to_pdf_page(request: Request):
    return templates.TemplateResponse("convert_common_to_pdf.html", {"request": request})


@app.get("/convert/image-to-pdf", response_class=HTMLResponse)
async def convert_image_to_pdf_page(request: Request):
    return templates.TemplateResponse("convert_image_to_pdf.html", {"request": request})


@app.get("/convert/pdf-to-image", response_class=HTMLResponse)
async def convert_pdf_to_image_page(request: Request):
    return templates.TemplateResponse("convert_pdf_to_image.html", {"request": request})


@app.get("/pdf", response_class=HTMLResponse)
async def pdf_page(request: Request):
    return templates.TemplateResponse("pdf.html", {"request": request})


@app.get("/pdf/merge", response_class=HTMLResponse)
async def pdf_merge_page(request: Request):
    return templates.TemplateResponse("pdf_merge.html", {"request": request})


@app.get("/pdf/split", response_class=HTMLResponse)
async def pdf_split_page(request: Request):
    return templates.TemplateResponse("pdf_split.html", {"request": request})


@app.get("/pdf/reorder", response_class=HTMLResponse)
async def pdf_reorder_page(request: Request):
    return templates.TemplateResponse("pdf_reorder.html", {"request": request})


@app.get("/pdf/compress", response_class=HTMLResponse)
async def pdf_compress_page(request: Request):
    return templates.TemplateResponse("pdf_compress.html", {"request": request})

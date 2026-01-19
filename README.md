DocuFlex
========

DocuFlex is a stateless, on-the-go document utility web app built with FastAPI and a lightweight HTML/CSS/JS frontend. It provides PDF conversion, PDF utilities, QR generation, and OCR without using any database or authentication.

Project Abstract
----------------
DocuFlex delivers a set of essential document operations directly in the browser using a simple, fast API. The system accepts files temporarily, processes them, and returns the output for download. No data is stored, which makes it lightweight, privacy-friendly, and suitable for academic use as a final-year project.

Objectives
----------
- Provide a clean, responsive web interface for document utilities.
- Implement core conversion and PDF tools using reliable Python libraries.
- Ensure stateless processing with automatic file cleanup.
- Demonstrate secure file handling and graceful error responses.
- Offer QR code generation and OCR features for extra utility.

Scope
-----
- PDF to Word (text-based extraction)
- Word to PDF (text-based rendering)
- JPG/PNG to PDF
- PDF to image (PNG per page)
- Merge PDFs
- Split PDF by page range
- Reorder PDF pages
- Compress PDF (optimize/deflate)
- QR generation (frontend-only at /qr)
- OCR from image or PDF
- Dark mode UI toggle

Why No Database?
---------------
DocuFlex is stateless by design. Every request is processed independently, and outputs are returned immediately without storage. This avoids personal data retention, reduces complexity, and is ideal for quick document tasks. The system uses temporary local storage only during processing and deletes files after response.

Why FastAPI?
------------
FastAPI is modern, fast, and provides automatic API documentation. It is easy to develop, strongly typed, and highly suitable for modular backend services. Its performance and developer ergonomics make it a strong choice for production-grade APIs and academic projects alike.

System Architecture
-------------------
1. Client submits file(s) using HTML/JS.
2. FastAPI receives the file via UploadFile, validates size and type.
3. Service layer performs processing using PyMuPDF, Pillow, and OCR.
4. Output is returned as a download response.
5. Temporary input/output files are deleted automatically.
6. QR codes are generated directly in the browser using JavaScript.

Folder Structure
----------------
- main.py
- routes/
  - convert.py
  - pdf_utils.py
  - ocr.py
- services/
  - file_utils.py
  - convert_service.py
  - pdf_service.py
  - ocr_service.py
- templates/
  - index.html
- static/
  - styles.css
  - app.js
- uploads/
- outputs/
- requirements.txt

Module Description
------------------
- routes/convert.py: Conversion endpoints (PDF ↔ DOCX, image ↔ PDF).
- routes/pdf_utils.py: PDF utilities (merge, split, reorder, compress).
- routes/ocr.py: OCR endpoints for images and PDFs.
- services/file_utils.py: File validation, size limits, safe storage, cleanup.
- services/convert_service.py: Conversion logic using PyMuPDF, pdf2docx, Pillow.
- services/pdf_service.py: PDF operations with page handling and optimization.
- services/ocr_service.py: OCR pipeline for images and PDFs using Tesseract.
- templates/index.html: Landing page that links to individual tools.
- templates/convert.html: Conversion category page.
- templates/pdf.html: PDF utilities category page.
- templates/ocr.html: OCR category page.
- templates/convert_*.html: Single-function conversion pages.
- templates/pdf_*.html: Single-function PDF utility pages.
- templates/ocr_*.html: Single-function OCR pages.
- templates/qr.html: Advanced frontend QR generator dashboard.
- static/styles.css: Material-inspired UI styles and dark mode.
- static/app.js: Frontend logic for uploads, status messages, and downloads.

Security and Safety
-------------------
- File size limit enforced in `services/file_utils.py` (default 20MB).
- Strict file type validation for PDF, DOCX, and images.
- UUID-based filenames to prevent path traversal.
- Auto-cleanup after response to avoid storage accumulation.

Limitations
-----------
- Word to PDF and PDF to Word are text-based and may not preserve complex formatting.
- Compression is an optimization/deflate pass and may not significantly reduce size for already optimized PDFs.
- OCR quality depends on image clarity and installed Tesseract engine.

Future Enhancements
-------------------
- Multi-language OCR support and language selection.
- Advanced PDF conversion (layout-preserving).
- Batch processing and progress tracking.
- Server-side rate limiting and load control.
- Embed QR into PDFs using server-side or client-side PDF libraries.

Viva Questions & Answers
------------------------
1. What problem does DocuFlex solve?
	It provides a unified, browser-based utility for common document tasks without complex setup or accounts.

2. Why did you choose FastAPI?
	It is fast, modern, easy to develop, and provides automatic API documentation.

3. Why is no database used?
	The app is stateless. Files are processed and deleted immediately, so persistence is unnecessary.

4. How is file security handled?
	File size limits, type validation, UUID filenames, and automatic deletion prevent misuse.

5. What are the key libraries used?
	PyMuPDF for PDF processing, Pillow for images, pdf2docx for PDF-to-DOCX, pytesseract for OCR.

6. What are the limitations?
	Advanced formatting in Word/PDF conversions may not be preserved.

7. How would you scale this application?
	Use object storage, background processing, and container orchestration.

8. How does OCR work here?
	PDFs are rendered to images, then pytesseract extracts text from each image.

9. How is error handling done?
	FastAPI raises HTTP exceptions with clear, user-friendly messages.

10. What improvements can be made?
	 Add multilingual OCR, advanced compression, and AI-based document enhancement.

Setup and Run
-------------
1. Create and activate a Python environment.
2. Install dependencies:
	pip install -r requirements.txt
3. Install Tesseract OCR engine (required for OCR endpoints):
	- Windows: https://github.com/UB-Mannheim/tesseract/wiki
4. Start the server:
	uvicorn main:app --reload
5. Open:
	http://127.0.0.1:8000
	API docs: http://127.0.0.1:8000/docs

Deployment (Optional)
---------------------
- Render/Railway: Use the same uvicorn command, ensure system package for Tesseract is installed.
- Docker:
	- Build: docker build -t docuflex .
	- Run: docker run -p 8000:8000 docuflex

License
-------
Academic use only.

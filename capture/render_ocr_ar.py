# -*- coding: utf-8 -*-
"""
render_ocr_ar.py -- Windows-friendly, pip-only render + OCR of the Arabic PDF.
No system binaries (no Poppler, no Tesseract): PyMuPDF renders pages, EasyOCR reads Arabic.

Setup (once):   pip install pymupdf easyocr
Run:            python capture/render_ocr_ar.py
Output:         capture/pages_txt/ar-NNN.txt  (one per page; resumable — safe to re-run)

EasyOCR downloads its Arabic model on the first run (needs internet). CPU is fine, just slower.
Then continue with step 3 of finish-arabic.md (python capture/clean_ar.py).
"""
import os, pathlib
import fitz            # PyMuPDF
import easyocr

PDF = "capture/Text of the Agreement in Arabic.pdf"
DPI = 300
os.makedirs("capture/pages_txt", exist_ok=True)
tmp = "capture/_ar_page.png"

reader = easyocr.Reader(["ar"])     # add "en" -> Reader(["ar","en"]) if you want Latin tokens too
doc = fitz.open(PDF)
print(f"{len(doc)} pages")
for i in range(len(doc)):
    out = f"capture/pages_txt/ar-{i+1:03d}.txt"
    if os.path.exists(out):
        continue
    doc[i].get_pixmap(dpi=DPI).save(tmp)
    lines = reader.readtext(tmp, detail=0, paragraph=True)
    pathlib.Path(out).write_text("\n".join(lines), encoding="utf-8")
    print(f"  page {i+1}: {len(lines)} blocks")
if os.path.exists(tmp):
    os.remove(tmp)
print("done -> capture/pages_txt/ (next: python capture/clean_ar.py)")

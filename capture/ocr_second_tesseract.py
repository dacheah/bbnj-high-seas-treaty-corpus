#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ocr_second_tesseract.py -- SECOND, INDEPENDENT OCR pass for the Chinese & Arabic BBNJ texts,
using Tesseract (chi_sim / ara). Its output is reconciled against the PRIMARY OCR
(rapidocr/PP-OCR for zh, EasyOCR for ar) to verify the stored text character-by-character:
where two independent engines agree, a character is corroborated; where they disagree, the
assistant adjudicates against the rendered page image.

>>> RUN THIS ON A MACHINE WITH THE TESSERACT LANGUAGE DATA (the corpus sandbox has none). <<<

Prereqs
  * Tesseract 5.x with the `chi_sim` and `ara` language packs.
      Windows: install from https://github.com/UB-Mannheim/tesseract/wiki and tick
      "Chinese (Simplified)" + "Arabic" under *Additional language data*, OR drop
      chi_sim.traineddata and ara.traineddata into ...\\Tesseract-OCR\\tessdata\\.
  * pip install pymupdf pytesseract pillow
  * If tesseract isn't on PATH, set the TESSERACT env var to the .exe, e.g.
      $env:TESSERACT = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

Outputs (per page, so a disagreement maps to one page image for adjudication):
  capture/pages_zh_tess/p-XX.txt   and  capture/zh-tesseract.txt   (pages joined by form-feed)
  capture/pages_ar_tess/p-XX.txt   and  capture/ar-tesseract.txt
  capture/ocr_second_tesseract.json  (manifest: tesseract version, dpi/psm/oem, per-PDF sha256)
"""
import os, sys, io, json, hashlib
try:
    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image
except ImportError as e:
    sys.exit(f"Missing dependency: {e}. Run:  pip install pymupdf pytesseract pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_cmd = os.environ.get("TESSERACT", "")
if _cmd:
    pytesseract.pytesseract.tesseract_cmd = _cmd

DPI, PSM, OEM = 300, "6", "1"   # 300dpi render; PSM 6 = uniform block; OEM 1 = LSTM

JOBS = [
    ("zh", "chi_sim", "un/bbnj-agreement-2023-zh/2023-06-19/original.pdf", "pages_zh_tess", "zh-tesseract.txt"),
    ("ar", "ara",     "un/bbnj-agreement-2023-ar/2023-06-19/original.pdf", "pages_ar_tess", "ar-tesseract.txt"),
]

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return "sha256:" + h.hexdigest()

def main():
    try:
        ver = pytesseract.get_tesseract_version()
        langs = pytesseract.get_languages(config="")
    except Exception as e:
        sys.exit(f"Cannot run tesseract ({e}). Install it and/or set the TESSERACT env var to the .exe.")
    print(f"Tesseract {ver} | languages: {sorted(langs)}")
    missing = [l for l in ("chi_sim", "ara") if l not in langs]
    if missing:
        sys.exit(f"ERROR: missing Tesseract language data {missing}. Install the packs (see header) and re-run.")

    manifest = {"tesseract_version": str(ver), "dpi": DPI, "psm": PSM, "oem": OEM, "jobs": []}
    for tag, tlang, pdf_rel, outdir, combined in JOBS:
        pdf = os.path.join(REPO, "authoritative", pdf_rel)
        if not os.path.exists(pdf):
            print(f"SKIP {tag}: no PDF at {pdf}"); continue
        od = os.path.join(HERE, outdir); os.makedirs(od, exist_ok=True)
        doc = fitz.open(pdf); pages = []
        print(f"\n{tag}: {doc.page_count} pages -> capture/{outdir}/  (tesseract -l {tlang})")
        for i in range(doc.page_count):
            pix = doc[i].get_pixmap(dpi=DPI)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            txt = pytesseract.image_to_string(img, lang=tlang, config=f"--oem {OEM} --psm {PSM}")
            with open(os.path.join(od, f"p-{i+1:02d}.txt"), "w", encoding="utf-8") as f:
                f.write(txt)
            pages.append(txt)
            sys.stdout.write(f"\r  page {i+1}/{doc.page_count}  ({len(txt.strip())} chars)   ")
            sys.stdout.flush()
        with open(os.path.join(HERE, combined), "w", encoding="utf-8") as f:
            f.write("\n\f\n".join(pages))   # pages separated by form-feed for the reconciler
        manifest["jobs"].append({"lang": tag, "tess_lang": tlang, "pdf": pdf_rel,
            "pdf_sha256": sha256_file(pdf), "pages": doc.page_count,
            "per_page_dir": f"capture/{outdir}", "combined": f"capture/{combined}"})
        print(f"\n  wrote capture/{combined} + {doc.page_count} per-page files")
    with open(os.path.join(HERE, "ocr_second_tesseract.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print("\nDONE. Hand back to the assistant:")
    print("  capture/zh-tesseract.txt  capture/ar-tesseract.txt  capture/ocr_second_tesseract.json")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ocr_cloud_gvision.py -- SECOND, INDEPENDENT OCR of the Arabic (and optionally Chinese) BBNJ text
using Google Cloud Vision (DOCUMENT_TEXT_DETECTION). Vision is far stronger on Arabic than
Tesseract, so its reconciliation with the primary (EasyOCR) can verify the text to a verbatim
standard. You run this on a machine with internet; the assistant runs the reconciliation.

>>> Needs a Google Cloud Vision API key (see second-ocr-cloud-runbook.md). <<<

Prereqs:
  pip install pymupdf requests
  $env:GVISION_API_KEY = "AIza...your key..."      # PowerShell
Optional:
  python capture/ocr_cloud_gvision.py --also-zh     # also re-OCR Chinese (3rd engine cross-check)

Output (per page, so a disagreement maps to a page image for adjudication):
  capture/ar-gvision.txt   (+ capture/pages_ar_gv/p-XX.txt)   [and zh-gvision.txt if --also-zh]
  capture/ocr_cloud_gvision.json  (manifest: engine, dpi, per-PDF sha256)
"""
import os, sys, io, json, base64, hashlib, time
try:
    import fitz            # PyMuPDF
    import requests
except ImportError as e:
    sys.exit(f"Missing dependency: {e}. Run:  pip install pymupdf requests")

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
KEY = os.environ.get("GVISION_API_KEY", "").strip()
if not KEY:
    sys.exit("Set GVISION_API_KEY to your Google Cloud Vision API key (see the runbook).")
URL = "https://vision.googleapis.com/v1/images:annotate?key=" + KEY
DPI = 300

JOBS = [("ar", "ara", "un/bbnj-agreement-2023-ar/2023-06-19/original.pdf", "pages_ar_gv", "ar-gvision.txt", "ar")]
if "--also-zh" in sys.argv:
    JOBS.append(("zh", "chi", "un/bbnj-agreement-2023-zh/2023-06-19/original.pdf", "pages_zh_gv", "zh-gvision.txt", "zh"))

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""): h.update(b)
    return "sha256:" + h.hexdigest()

def vision_page(png_bytes, hint):
    body = {"requests": [{"image": {"content": base64.b64encode(png_bytes).decode()},
                          "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                          "imageContext": {"languageHints": [hint]}}]}
    for attempt in range(4):
        r = requests.post(URL, json=body, timeout=90)
        if r.status_code == 200:
            resp = r.json()["responses"][0]
            if "error" in resp and resp["error"]:
                sys.exit(f"Vision API error: {resp['error']}")
            return resp.get("fullTextAnnotation", {}).get("text", "")
        if r.status_code in (429, 503):
            time.sleep(2 * (attempt + 1)); continue
        sys.exit(f"HTTP {r.status_code}: {r.text[:400]}\n(Check: API key valid? Cloud Vision API enabled? Billing enabled?)")
    sys.exit("Repeated rate-limit/5xx from Vision; try again later.")

def main():
    manifest = {"engine": "google-cloud-vision DOCUMENT_TEXT_DETECTION", "dpi": DPI, "jobs": []}
    for tag, _e, pdf_rel, outdir, combined, hint in JOBS:
        pdf = os.path.join(REPO, "authoritative", pdf_rel)
        if not os.path.exists(pdf): print("SKIP", tag, "(no PDF)"); continue
        od = os.path.join(HERE, outdir); os.makedirs(od, exist_ok=True)
        doc = fitz.open(pdf); pages = []
        print(f"\n{tag}: {doc.page_count} pages -> capture/{outdir}/  (Google Vision, hint={hint})")
        for i in range(doc.page_count):
            png = doc[i].get_pixmap(dpi=DPI).tobytes("png")
            txt = vision_page(png, hint)
            open(os.path.join(od, f"p-{i+1:02d}.txt"), "w", encoding="utf-8").write(txt)
            pages.append(txt)
            sys.stdout.write(f"\r  page {i+1}/{doc.page_count}  ({len(txt.strip())} chars)   "); sys.stdout.flush()
        open(os.path.join(HERE, combined), "w", encoding="utf-8").write("\n\f\n".join(pages))
        manifest["jobs"].append({"lang": tag, "pdf": pdf_rel, "pdf_sha256": sha256_file(pdf),
                                 "pages": doc.page_count, "combined": f"capture/{combined}"})
        print(f"\n  wrote capture/{combined} + {doc.page_count} per-page files")
    json.dump(manifest, open(os.path.join(HERE, "ocr_cloud_gvision.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("\nDONE. Tell the assistant; it will run capture/reconcile_ar.py against capture/ar-gvision.txt.")

if __name__ == "__main__":
    main()

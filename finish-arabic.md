# finish-arabic.md — close GAPS G-2c (Arabic) on your own machine

**Goal:** recover machine-readable Arabic text for the BBNJ Agreement and flip
`un/bbnj-agreement-2023-ar` from `authoritative_missing` to `authentic_text`.
The byte-exact Arabic PDF is **already captured** as `original.pdf`, so this is a *text-layer
upgrade only* — you are not re-sourcing anything.

**Why it can't run in Cowork:** that sandbox only reaches PyPI, and every Arabic OCR engine
downloads its models from a host that's blocked there (tesseract traineddata on GitHub/HF,
EasyOCR on jaided.ai/GitHub, PaddleOCR on bcebos). On a normal machine with internet this is easy.

Run everything from the repo root: `cd bbnj-corpus`

---

## 0. Prerequisites (once)
- Python 3.11+ and the repo deps: `pip install -r scripts/requirements.txt`
- Poppler (for `pdftoppm`): macOS `brew install poppler` · Debian/Ubuntu `sudo apt-get install poppler-utils`
- An Arabic OCR engine — pick **one**:
  - **Tesseract (simplest):**
    - Debian/Ubuntu: `sudo apt-get install tesseract-ocr tesseract-ocr-ara`
    - macOS: `brew install tesseract tesseract-lang`
    - Python wrapper (optional): `pip install pytesseract`
  - **EasyOCR:** `pip install easyocr` (language `['ar']`)
  - **PaddleOCR:** `pip install paddleocr paddlepaddle` (`lang='arabic'`)

## Windows (PowerShell) — pip-only, no system binaries  ← START HERE on Windows
`pdftoppm` (Poppler) and system Tesseract are Linux/macOS tools. On Windows, skip them and use a
pure-pip path — PyMuPDF renders the pages, EasyOCR does the Arabic OCR (its model auto-downloads on
first run; you have internet, so it works):
```powershell
pip install -r scripts/requirements.txt
pip install pymupdf easyocr
python capture/render_ocr_ar.py     # renders + OCRs every page -> capture/pages_txt/ar-NNN.txt
```
Then skip to **step 3** below (`python capture/clean_ar.py`) and continue. Steps 1–2 (Poppler +
Tesseract) are only for macOS/Linux.

> Tip: if you'd rather use Tesseract on Windows, install the UB-Mannheim build (it bundles the
> Arabic pack), `pip install pytesseract`, and OCR each PNG with `pytesseract.image_to_string(img, lang="ara")`.

---

## 1. Render the Arabic pages
```bash
mkdir -p capture/pages_ar capture/pages_txt
pdftoppm -png -r 300 "capture/Text of the Agreement in Arabic.pdf" capture/pages_ar/p
```
(300 dpi gives Arabic OCR the best shot; use 200 if it's slow.)

## 2. OCR every page → `capture/pages_txt/ar-NNN.txt`
**Tesseract:**
```bash
for f in capture/pages_ar/p-*.png; do
  n=$(basename "$f" .png | sed 's/p-//')
  tesseract "$f" stdout -l ara --psm 6 > "capture/pages_txt/ar-$n.txt"
done
```
**or EasyOCR:**
```bash
python3 - <<'PY'
import easyocr, glob, re
r = easyocr.Reader(['ar'])
for p in sorted(glob.glob("capture/pages_ar/p-*.png")):
    n = re.search(r"p-(\d+)", p).group(1)
    lines = r.readtext(p, detail=0, paragraph=True)
    open(f"capture/pages_txt/ar-{n}.txt", "w", encoding="utf-8").write("\n".join(lines))
PY
```

## 3. Assemble + normalise → `capture/text-ar.full.txt`
```bash
python3 capture/clean_ar.py
```
Then **open `capture/text-ar.full.txt` and eyeball it**: title, `ديباجة`, `المادة ١ … ٧٦`,
`المرفق الأول/الثاني`. If the counts look off, tune the markers/anchor in `capture/clean_ar.py`
to match your OCR's actual output, and re-run. (Set the `TITLE` constant from page 1 of the PDF.)

## 4. Ingest in place (flip the record to `authentic_text`)
This mirrors exactly what was done for Chinese: writes `text.txt` into the existing Arabic record,
re-hashes, and sets `authoritative_status: authentic_text`, `text_fidelity: ocr_unverified`.
```bash
python3 - <<'PY'
import sys, pathlib, datetime
sys.path.insert(0, "scripts")
import yaml
from hashing import sha256_bytes, normalize_text_bytes
from ingest import _ordered

ENGINE = "tesseract -l ara"          # <-- set to the engine you used
VD = pathlib.Path("authoritative/un/bbnj-agreement-2023-ar/2023-06-19")
today = datetime.date.today().isoformat()

tb = normalize_text_bytes(pathlib.Path("capture/text-ar.full.txt").read_text(encoding="utf-8"))
(VD / "text.txt").write_bytes(tb)
sha = sha256_bytes(tb)

m = yaml.safe_load((VD / "metadata.yaml").read_text(encoding="utf-8"))
m["authoritative_status"] = "authentic_text"
m["language"] = "ar"
m["text_sha256"] = sha
m["content_hash"] = sha
m["text_fidelity"] = "ocr_unverified"
m["capture_history"].append({
    "date": today, "source_url": m["source_url"], "original_sha256": m["original_sha256"],
    "note": f"OCR of the byte-exact PDF ({ENGINE}, pages at 300 dpi) to recover machine-readable text; see capture/clean_ar.py."})
m["provenance_note"] = (
    "Authentic Arabic text recovered by OCR of the byte-exact official UN PDF (original.pdf), because "
    "the PDF's embedded fonts carry no usable Unicode map. OCR via " + ENGINE + ", assembled and "
    "normalised (capture/clean_ar.py). text_fidelity=ocr_unverified: OCR carries residual errors and "
    "the byte-exact PDF remains authoritative. One of six equally authentic languages (Art. 76).")
m["verification"] = {
    "status": "ocr_spotchecked",
    "method": "OCR output spot-checked against the official PDF page images (title, ديباجة, sample articles, المرفق).",
    "reference": "capture/Text of the Agreement in Arabic.pdf (%s)" % m["original_sha256"],
    "verified_by": "maintainer", "verified_date": today,
    "note": "ocr_unverified — not a full verbatim audit."}
yaml.safe_dump(_ordered(m), open(VD / "metadata.yaml", "w", encoding="utf-8"),
               sort_keys=False, allow_unicode=True, default_flow_style=False, width=100)
print("ar -> authentic_text, ocr_unverified, text_sha", sha[:20])
PY
```

## 5. Rebuild + validate
```bash
python3 scripts/build_derived.py
python3 scripts/build_site.py
python3 scripts/validate_corpus.py     # must print: RESULT: OK.
```

## 6. Close the gap in the docs
- `GAPS.md` → under **G-2c**, move the Arabic bullet from "OPEN, blocked" to "CLOSED <date>".
- `README.md` and `docs/source-coverage.md` → show all six languages with text.
- Commit: `git add -A && git commit -m "Close G-2c: Arabic text via OCR (ocr_unverified)"`.

## Fidelity note
OCR is not verbatim. Keep `text_fidelity: ocr_unverified` and treat the byte-exact PDF as
authoritative until a human verbatim audit; then upgrade to `extracted_verified` with a dated
`corrections[]`/`verification{}` entry (same pattern as the English G-1b audit).

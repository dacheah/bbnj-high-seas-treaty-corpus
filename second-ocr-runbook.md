# Second independent OCR pass (Tesseract) — run on your machine

Goal: produce a second, independent OCR of the Chinese and Arabic PDFs with **Tesseract**
(`chi_sim` / `ara`), so I can reconcile it against the stored text character-by-character and
upgrade both from `ocr_unverified` toward verbatim `extracted_verified`. You run the OCR; I run
the reconciliation and adjudicate every disagreement against the page images.

No file hand-off needed — the script writes into `capture/`, which is the same folder I can read.
Just run it and tell me it's done.

## 1) Install Tesseract with the Chinese + Arabic language data
- Download the Windows installer: https://github.com/UB-Mannheim/tesseract/wiki
- During install, expand **"Additional language data (download)"** and tick
  **Chinese (Simplified)** (`chi_sim`) and **Arabic** (`ara`). Finish the install.
- Default install path is `C:\Program Files\Tesseract-OCR\`.

## 2) Install the Python deps
```powershell
cd "C:\Users\dache\Claude\Projects\Project High\bbnj-corpus"
python -m pip install pymupdf pytesseract pillow
```

## 3) Run the second-OCR pass
```powershell
# If tesseract isn't on your PATH, point at the exe first (adjust if you installed elsewhere):
$env:TESSERACT = "C:\Program Files\Tesseract-OCR\tesseract.exe"

python capture/ocr_second_tesseract.py
```
It prints the Tesseract version + languages (it will stop with a clear error if `chi_sim` or
`ara` are missing), then OCRs every page of each PDF at 300 dpi. Expect it to take a few
minutes (≈60 Chinese pages + ≈83 Arabic pages).

## 4) It produces
```
capture/zh-tesseract.txt          # Chinese, pages joined by form-feed
capture/ar-tesseract.txt          # Arabic,  pages joined by form-feed
capture/pages_zh_tess/p-XX.txt    # per-page (for spot inspection)
capture/pages_ar_tess/p-XX.txt
capture/ocr_second_tesseract.json # manifest: tesseract version, dpi/psm, PDF sha256s
```

## 5) Tell me it's done
I'll run `capture/reconcile_ocr.py zh` and `... ar`, which report the character-agreement rate
between the two engines and list every disagreement with its page number. I then read those
pages, correct any genuine OCR errors in the stored text (e.g. the Arabic Article 4 heading that
lost its numeral), and — if every character ends up either agreed-by-two-engines or
visually-confirmed — upgrade both records to `extracted_verified` with a dual-OCR
`verification{}` record and the agreement statistics. Then the usual gates + re-export + a
commit/push runbook.

## Notes
- Tesseract's CJK/Arabic accuracy is only moderate, so expect a fair number of disagreements —
  that's fine and expected; each is a pointer to a spot I check by eye. It does **not** mean the
  stored text is wrong; often Tesseract is the one that's off.
- If `python capture/ocr_second_tesseract.py` says it can't find tesseract, re-check step 3's
  `$env:TESSERACT` path.

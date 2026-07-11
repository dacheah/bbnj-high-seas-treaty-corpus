# Arabic verbatim pass — cloud OCR (Google Cloud Vision)

Tesseract's Arabic was too weak (~78% agreement) to verify the Arabic text. Google Cloud Vision is
excellent at Arabic, so a second pass with it should let us reconcile to a verbatim standard and
upgrade Arabic to `extracted_verified`. You run the OCR; I run the reconciliation and adjudicate.

The whole job is **~83 pages = 83 Vision "units"**, and Google gives the **first 1,000 units/month free**,
so this costs **$0** — but Google does require a billing account to be linked to the project (standard
for Vision, even on the free tier).

## A) Get a Google Cloud Vision API key (one time, ~5 min)
1. Go to **https://console.cloud.google.com/** and sign in with a Google account.
2. **Create a project:** top bar → project dropdown → **New Project** → name it (e.g. "bbnj-ocr") → **Create**,
   then make sure it's the selected project.
3. **Enable billing:** left menu → **Billing** → **Link a billing account** (add a card if you don't have one).
   Nothing here will be charged for this job — it's inside the free tier — but Vision won't run without it.
4. **Enable the API:** left menu → **APIs & Services → Library** → search **"Cloud Vision API"** → open it → **Enable**.
5. **Create the key:** **APIs & Services → Credentials** → **+ Create Credentials** → **API key**. Copy the key
   (looks like `AIzaSy...`).
6. **(Recommended) restrict it:** click the new key → under **API restrictions** choose **Restrict key** →
   select **Cloud Vision API** → **Save**. (Limits the key to just this API.)

## B) Run the second OCR
```powershell
cd "C:\Users\dache\Claude\Projects\Project High\bbnj-corpus"
python -m pip install pymupdf requests
$env:GVISION_API_KEY = "AIzaSy...paste your key..."
python capture/ocr_cloud_gvision.py
```
It OCRs all ~83 Arabic pages via Vision and writes `capture/ar-gvision.txt` (+ per-page files + a
manifest). If the key/billing/API isn't ready it stops with a clear message telling you which.

## C) Tell me it's done
I'll run `capture/reconcile_ar.py`, which reports the Vision-vs-EasyOCR word agreement (should be high)
and lists every disagreement with its page number. I adjudicate each against the page image, correct
the stored Arabic where EasyOCR erred, and — if every word ends up agreed-by-two-strong-engines or
visually confirmed — upgrade Arabic to `extracted_verified` (dual-engine EasyOCR + Google Vision), then
rebuild the derived layer, re-run the gates, re-export, and hand you a commit/push runbook.

## Prefer not to enable Google billing?
**Azure AI Vision (Read)** has a genuinely free tier (F0, 5,000 pages/month) and is also excellent at
Arabic. If you'd rather use Azure, say so and I'll swap the runner to the Azure Read API (endpoint + key
instead of a Google API key) — everything downstream is identical.

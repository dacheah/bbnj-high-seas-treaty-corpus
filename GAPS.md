# Gap register (BBNJ) — recorded, not hidden

Provenance principle: gaps are first-class facts. Each is tracked here until closed.

## G-1 — Agreement English text complete *(CLOSED 2026-07-03)*
- **Was:** the automated fetch truncated the English text at Article 73 (Arts 74–76 + Annexes I–II missing).
- **Closed by:** the maintainer supplied the byte-exact official English PDF; the **complete** authentic
  text (Preamble + Parts I–XII + Articles 1–76 + Annex I + Annex II) was re-derived from it, the original
  artifact upgraded to `original.pdf`, and the change recorded as dated `corrections[]` + a `verification{}`
  record (completeness verified: 76/76 articles, no gaps/dupes; both annexes present).
- **Residual:** none — see G-1b (now closed).

## G-1b — Full verbatim audit of the English text *(CLOSED 2026-07-03)*
- **Done:** audited the stored text against the byte-exact official PDF. Found the default PDF
  extraction had scrambled the reading order of hanging-indent enumerated lists (and had merged two
  Part II items, dropping a `(b)` enumerator and `sharing;`). Re-derived the text from a
  content-stream-order extraction (`pdftotext -raw`) that reads these correctly, cross-checked
  reading order against rendered PDF page images, and confirmed Articles 1–76 + both annexes are
  complete with no gaps/dupes. Also repaired all line-break hyphenation merges. Recorded as dated
  `corrections[]` + a `verification{}` record; **`text_fidelity` upgraded to `extracted_verified`.**

## G-2 — Five authentic-language texts *(partly closed 2026-07-03)*
The Agreement is authentic in six UN languages (Art. 76). Each language is a sibling record
under `un/bbnj-agreement-2023-<lang>`, `version_id: 2023-06-19`, cross-linked to the English.
- **Spanish** (`-es`): clean native extraction (pdftotext -raw); complete; spot-verified against
  the official PDF pages → `extracted_verified`. **Done.**
- **French** (`-fr`): body extracted faithfully; the PDF's display font for the title/headings uses
  non-Unicode glyph substitutions (e.g. B→%, G→*, è→q), repaired against the official French
  headings → `extracted_unverified` (see G-2b). Complete. **Done.**
- **Russian** (`-ru`): the embedded font maps Cyrillic/punctuation to non-Unicode code points;
  recovered via a deterministic decode (Cyrillic offset +0x1D6 + digit/punctuation/guillemet map),
  title + a page spot-verified → `extracted_unverified` (see G-2b). Complete. **Done.**
- **Chinese** (`-zh`) & **Arabic** (`-ar`): byte-exact PDFs captured, but a faithful text is not
  machine-extractable in this environment → `authoritative_missing` (see G-2c).

## G-2b — Full verbatim audit of the French & Russian texts *(open, low priority)*
- fr headings and the ru decode were spot-verified against page images, not audited line by line.
  A full audit (and, for fr, confirming no residual display-font substitutions in article titles)
  would upgrade both to `extracted_verified`.

## G-2c — Chinese & Arabic clean-text extraction *(CLOSED — both OCR'd)*
- **Chinese — CLOSED 2026-07-03.** OCR'd the byte-exact PDF with rapidocr / PP-OCR (models bundled
  in the pip wheel — the only OCR that runs offline in this sandbox), pages rendered at 200 dpi,
  assembled + normalised (capture/clean_zh.py). Record `un/bbnj-agreement-2023-zh` is now
  `authentic_text`, `text_fidelity: ocr_unverified` (complete coverage: 序言 + 第一–十二部分 +
  第一–七十六条 + 附件一/二; residual OCR errors expected — the byte-exact PDF stays authoritative).
  A full verbatim OCR audit is a low-priority residual.
- **Arabic — CLOSED 2026-07-04.** OCR'd the byte-exact PDF on an unrestricted machine (per
  `finish-arabic.md`): PyMuPDF render at 300 dpi + EasyOCR `['ar']` (both pip-only, no system
  binaries), assembled + normalised (capture/render_ocr_ar.py, clean_ar.py). Record
  `un/bbnj-agreement-2023-ar` is now `authentic_text`, `text_fidelity: ocr_unverified` (complete:
  title + الديباجة + المادة ١–٧٦ + المرفق الأول/الثاني; residual OCR errors expected — the
  byte-exact PDF stays authoritative). A full verbatim OCR audit is a low-priority residual.


## G-3 — UNCLOS + implementing agreements not yet ingested *(open)*
- BBNJ-relevant UNCLOS provisions (esp. Part XV, Arts 287/298) and the two prior implementing agreements
  are in scope (doc 05) and queued.

## G-4 — PrepCom / COP1 outputs *(PrepCom layer ingested 2026-07-04; COP1 pending)*
- **Ingested (6 new records, English, `extracted_unverified` — byte-exact PDFs):** the adopted
  **Report of the Preparatory Commission** (3rd session, advance-unedited) and the five GA
  resolutions/decision that govern the process — A/RES/77/321, **78/272** (establishes the PrepCom),
  79/271, 80/107, and decision 78/560 (A/78/L.102). Document types `resolution` / `decision` /
  `prepcom_document`.
- **Queued (drafts, NOT law yet):** A/AC.296/2026/1–8 aids/draft decisions, host-country secretariat
  offers, and the CHM draft study — see `queue/candidates.md`; ingest the COP1-**adopted** versions.
- **Live layer — still pending:** COP1 (11–22 January 2027) will produce the first binding COP
  decisions. The monthly scheduled watch (`bbnj-cop1-watch`) + `monitoring/sources.json` track it;
  the final **edited** PrepCom Report (with an official symbol, in six languages) will supersede the
  advance-unedited version as a new dated version.
- **Residual:** the 6 new records are `extracted_unverified` (clean digital PDFs, spot-checked) and
  English-only for now — a verbatim audit and the other five UN languages are low-priority follow-ups.


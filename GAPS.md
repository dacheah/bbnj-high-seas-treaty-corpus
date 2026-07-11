# Gap register (BBNJ) — recorded, not hidden

# Fidelity status (updated 2026-07-11)

`text_fidelity` across the 15 authoritative records:
- **extracted_verified (13):** UNCLOS (1982); the PrepCom Report (3rd session); BBNJ Agreement
  (English, Spanish, **French**, **Russian**); GA resolutions 77/321, 78/272, 79/271, 80/107; decision
  78/560; the 1994 Part XI Agreement; the 1995 Fish Stocks Agreement.
  Method (text-layer records with a clean digital text layer): two independent extractors (pdftotext
  -raw + PyMuPDF) agree word-for-word, the stored text adds no words and drops only bibliographic
  noise, and a rendered-page spot-check confirms a clean text layer. **French & Russian** use a
  non-Unicode display/decoded font, so no independent second extractor exists; they were verified on
  **2026-07-11** by a full-text substitution-residue scan (zero residue) + completeness check +
  page-image visual confirmation, and for French an independent rapidocr reconciliation over a 10-page
  sample also matched. See G-2b.
- **extracted_unverified (0).**
- **Reproducibility (2026-07-11):** `scripts/extract.py` re-derives every text from its stored
  `original.pdf` by committed code (`scripts/pipelines.py`) and checks the SHA-256 — **13/13
  text-layer records reproduce byte-exact**, now a CI gate. The 2 OCR records (zh, ar) use a
  separate render+OCR pipeline and are excluded from the byte-exact text-layer gate.
- **Still ocr_unverified (2):** BBNJ Chinese & Arabic (OCR). **Completeness re-verified 2026-07-11**
  (all parts/articles/annexes present) and spot-checked against page images, but full per-character
  verbatim accuracy is **not** established — no independent second OCR engine is available offline, so
  the byte-exact PDF stays authoritative. `verification.status: completeness_verified`. See G-2c.

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

## G-2b — Full verbatim audit of the French & Russian texts *(CLOSED 2026-07-11)*
- **French — CLOSED.** Full-text scan for display-font substitution residue is clean (zero stray glyphs
  across ~164k chars; a clean all-French non-ASCII inventory), structure complete (Article premier +
  Arts 2–76 = 76, 12 Parties, 2 Annexes), and an independent rapidocr reconciliation over a 10-page
  stratified sample matched the stored text — every residual diff an OCR word-join or o-e ligature,
  including positive confirmation of the display-font "PARTIE II" heading. **`text_fidelity` →
  `extracted_verified`** (`verification{}` recorded).
- **Russian — CLOSED.** Verification surfaced two residual italic-font runs the +0x1D6 decode could not
  reach — the defined term «Сбор in situ» (had decoded to `LQ VLWX`, ×3) and the identifier "BBNJ" in
  curly quotes (quote glyphs had decoded to `³ ´`, ×7) — plus 75 leaked page-number footers (the
  form-feed byte had been mapped to `(` instead of a line break). All were **repaired at the reproducible
  pipeline source** (`scripts/pipelines.py`, `_RU_FIXES` + form-feed fix); the text was re-derived and
  re-hashed and `extract.py` still reproduces **13/13** byte-exact. Confirmed against page images (title,
  Art. 13 defined term, Arts 75–76 authenticity clause). **`text_fidelity` → `extracted_verified`**
  (dated `corrections[]` + `verification{}` recorded).

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
- **Completeness re-verified 2026-07-11 (both).** Programmatic enumeration confirms full structure
  (zh: 序言 + 第一–十二部分 + 第一–七十六条 + 附件一/二; ar: الديباجة + 76 article headings + المرفق الأول/الثاني +
  authenticity clause), with page-image spot-checks (zh: title + a dense body page, 9/9 phrases verbatim;
  ar: title + a body page). A concrete Arabic OCR defect — the Art. 4 heading lost its numeral — is
  recorded in the record's `verification{}`. Both stay `ocr_unverified` (`verification.status:
  completeness_verified`); a full verbatim upgrade needs a second independent OCR engine (none offline)
  or a human proofread.


## G-3 — UNCLOS (parent convention) *(UNCLOS ingested 2026-07-04; agreements queued)*
- **Ingested:** the COMPLETE UNCLOS (1982) — `un/unclos-1982`, `document_type: convention`, Preamble +
  Parts I–XVII (Articles 1–320) + Annexes I–IX (and the Final Act annexes in the official PDF), English,
  byte-exact PDF, `extracted_unverified`. Per design decision JC-2026-07-04-d (full text, not an
  excerpt). The BBNJ records' `related_documents: un/unclos-1982` cross-reference now resolves; the
  BBNJ-relevant provisions (Part XV; Arts 287/298; high-seas/Area regimes) are surfaced in the derived layer.
- **Fixed 2026-07-04:** the pdftotext space-drop artifacts were repaired by re-deriving from a PyMuPDF
  extraction (dual-extractor reconciliation) → `extracted_verified`. The other five UN languages are not yet captured.
- **1994 & 1995 implementing agreements — INGESTED 2026-07-04** (JC-2026-07-04-e): the 1994 Part XI
  Agreement (`un/agreement-partxi-1994`, A/RES/48/263 annex) and the 1995 Fish Stocks Agreement
  (`un/fish-stocks-agreement-1995`, A/CONF.164/37) — byte-exact ODS PDFs, English, `extracted_unverified`.
  The parent framework is now complete: UNCLOS + all three of its implementing agreements (Part XI,
  Fish Stocks, BBNJ). English-only + a verbatim audit remain low-priority follow-ups.


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


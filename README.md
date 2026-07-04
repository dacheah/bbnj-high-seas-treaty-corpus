# BBNJ / High Seas Treaty Corpus

A neutral, authoritative, machine-readable record of the law governing the **conservation and
sustainable use of marine biological diversity of areas beyond national jurisdiction** — the
2023 **BBNJ Agreement** (the "High Seas Treaty"), which **entered into force on 17 January 2026**,
and its implementing framework.

Built **provenance-first**: every authoritative text carries its source, retrieval date, official
citation, authentic languages, an authoritative-status flag and a SHA-256 content hash; every
change is a new dated version; nothing generated is ever presented as authoritative.

## Layout
```
authoritative/   LAYER 1 — official source texts (authentic language) + full provenance
derived/         LAYER 2 — structure, neutral concept tags, translations (unofficial, traceable)
schema/          the two JSON Schemas (integrity contract)
scripts/         the deterministic pipeline (ingest, build_derived, build_site, validate, watch)
docs/design/     the frozen design-lock (00–06) — the corpus constitution
docs/            source-coverage map, concept vocabulary
capture/         capture inputs + the reproducible cleaner (not authoritative)
monitoring/      sources watched for change
queue/           borderline scope candidates
site/            generated static browsable site (regenerable)
GAPS.md          the gap register — recorded, not hidden
```

## Current contents
- **The BBNJ Agreement in all six authentic UN languages** (Art. 76), as sibling records
  `un/bbnj-agreement-2023-<lang>`, all `2023-06-19`, each captured byte-exact as `original.pdf`:
  - **English** (`extracted_verified`) and **Spanish** (`extracted_verified`) — complete, verified.
  - **French** & **Russian** (`extracted_unverified`) — complete; recovered from non-Unicode display
    fonts (fr headings repaired; ru decoded) and spot-verified (full audit = GAPS G-2b).
  - **Chinese** (`ocr_unverified`) — recovered by OCR (rapidocr/PP-OCR) of the byte-exact PDF; complete.
  - **Arabic** (`ocr_unverified`) — recovered by OCR (PyMuPDF render + EasyOCR) of the byte-exact PDF; complete.
- **The parent convention (G-3):** the complete **UNCLOS (1982)** — Preamble + Articles 1–320 + Annexes I–IX (`un/unclos-1982`, `convention`, English, `extracted_unverified`) — so BBNJ's cross-references (Part XV dispute settlement, Arts 287/298, the high-seas/Area regimes) resolve in-house.
- **The founding instruments & implementation layer (G-4):** the five General Assembly
  resolutions/decision that govern the BBNJ process (A/RES/77/321, 78/272 — which establishes the
  Preparatory Commission — 79/271, 80/107; decision 78/560) and the **adopted PrepCom Report**
  (3rd session, 2026, advance-unedited). English, `extracted_unverified`, byte-exact PDFs. COP1
  (Jan 2027) decisions are pending — tracked by a scheduled watch.
- **Derived layer:** deterministic structure parse (79 units: preamble + 76 articles + 2 annexes)
  + keyword concept tags across 15 neutral concepts (unreviewed).

## Reproduce
```
pip install -r scripts/requirements.txt
python3 scripts/validate_corpus.py     # integrity gate — must be green
python3 scripts/build_derived.py        # regenerate the derived layer
python3 scripts/build_site.py           # regenerate site/
```

## The one rule
Provenance and version integrity override convenience, always. See `docs/design/` and
`docs/maintainers-guide.md`.

Our contributions are CC BY 4.0. Source texts keep their own terms (UN materials: freely
reproducible with attribution, no warranty).

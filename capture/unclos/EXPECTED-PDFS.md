# Awaiting: byte-exact UNCLOS PDF (G-3)

UNCLOS is ~200 pages (320 articles + 9 annexes) — too large for the fetch tool, so byte-exact
download, same as the treaty. Save into `capture/unclos/` with this exact name:

| Save as (in capture/unclos/) | Official source (UN DOALOS) |
|---|---|
| `unclos_e.pdf` | https://www.un.org/depts/los/convention_agreements/texts/unclos/unclos_e.pdf |

On drop I ingest it as `corpus_id: un/unclos-1982`, `version_id: 1982-12-10` (adoption),
`document_type: convention`, authentic in the six UN languages (English first). Extract with
`pdftotext -raw`, clean/reflow (PART / Article / SECTION / ANNEX headers), verify, rebuild, validate.
The 1994 Part XI and 1995 Fish Stocks agreements stay queued (`queue/candidates.md`).

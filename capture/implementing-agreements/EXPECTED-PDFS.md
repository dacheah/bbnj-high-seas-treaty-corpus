# Awaiting: byte-exact PDFs for the 1994 & 1995 implementing agreements

The DOALOS HTML texts were checked (complete, but merged-header formatting + the 1994 page is
marked "not an official document"). For clean authoritative text, download the official ODS PDFs
and save into `capture/implementing-agreements/` with these exact names:

| Save as | Instrument | Viewer (download the English PDF) |
|---|---|---|
| `ares-48-263-1994.pdf`   | 1994 Agreement relating to the Implementation of Part XI of UNCLOS | https://docs.un.org/en/A/RES/48/263 |
| `aconf-164-37-1995.pdf`  | 1995 UN Fish Stocks Agreement (A/CONF.164/37) | https://docs.un.org/en/A/CONF.164/37 |

On drop I ingest each as `document_type: implementing_agreement`, extract with `pdftotext -raw`,
clean/reflow (PART / Article / Section / ANNEX), verify, rebuild, validate:
- 1994 → `corpus_id: un/agreement-partxi-1994`, `version_id: 1994-07-28` (adoption).
- 1995 → `corpus_id: un/fish-stocks-agreement-1995`, `version_id: 1995-08-04` (adoption).
Both relate to `un/unclos-1982`. The captured DOALOS HTML stays in this folder as a reference cross-check.

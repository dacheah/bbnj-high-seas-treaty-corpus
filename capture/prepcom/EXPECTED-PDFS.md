# Awaiting: byte-exact PDFs for the G-4 live layer

Download each and save into `capture/prepcom/` with the EXACT filename below; then I ingest each
as its own record (`pdftotext -raw` → clean → provenance → validate), same standard as the treaty.

## Adopted PrepCom output
| Save as (in capture/prepcom/) | Download from |
|---|---|
| `prepcom-report-2026-3.pdf` | https://www.un.org/bbnjagreement/sites/default/files/2026-05/20260504BbnjPrepComReportFinal_AdvancedUnedited_0.pdf |

## GA resolutions / decision (open the viewer, then download the English PDF)
| Save as | Viewer (click the download/PDF icon) |
|---|---|
| `ares-77-321.pdf` | https://docs.un.org/en/A/RES/77/321 |
| `ares-78-272.pdf` | https://docs.un.org/en/A/RES/78/272 |
| `ares-79-271.pdf` | https://docs.un.org/en/A/RES/79/271 |
| `ares-80-107.pdf` | https://docs.un.org/en/A/RES/80/107 |
| `dec-78-560.pdf`  | https://docs.un.org/en/A/78/L.102 |

## How each is ingested (planned)
- PrepCom Report → `corpus_id: un/prepcom/report-2026-3`, `version_id: 2026-04-02`,
  `document_type: prepcom_document`, note "advance, unedited version" (a later edited version supersedes).
- Each resolution → `corpus_id: un/ga-resolution/A-RES-<n>`, `version_id` = adoption date,
  `document_type: resolution`, authentic in the six UN languages (English ingested first; others flagged).
- Drafts (A/AC.296/2026/1–8) are NOT ingested now — see `queue/candidates.md`; ingest the COP1-adopted
  versions in January 2027.

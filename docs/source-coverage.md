# Source-coverage map (BBNJ) — as of 2026-07-03

Honest inventory of official sources, what each publishes, formats, languages, terms, and the
gaps. Ingestion order: cleanest / most canonical first.

## Tier 1 — Core instrument (authoritative)
| Source | Publishes | Formats | Languages | Official? | Status here |
|---|---|---|---|---|---|
| UN BBNJ Agreement site (`un.org/bbnjagreement`) | The Agreement text | PDF | 6 UN languages | Yes | **en** verified; **es** verified; **fr, ru** ingested (extracted_unverified, headings/decode spot-verified); **zh** OCR'd (ocr_unverified); **ar** OCR'd on an unrestricted machine (ocr_unverified). All six languages now have text.. All as sibling records `un/bbnj-agreement-2023-<lang>`. |
| UN Treaty Collection XXI.10 | Status, signatures, ratifications, declarations, depositary notifications | HTML/PDF | en (+ others) | Yes (depositary) | Monitored; not yet ingested |
| UNCLOS (1982) | Parent convention | PDF/HTML | 6 UN languages | Yes | Queued (BBNJ-relevant provisions) |

## Tier 2 — Implementation instruments (authoritative + emerging)
| Source | Publishes | Status here |
|---|---|---|
| UNGA res. 78/272 | Establishes the Preparatory Commission | Queued |
| Preparatory Commission documents (1st–3rd sessions) | Working docs, recommendations, reports | Monitored; ingest final versions |
| Conference of the Parties (COP1) | Decisions, rules of procedure, subsidiary-body instruments | **Live layer** — monitor; ingest as adopted |
| Clearing-House Mechanism | Governing rules + operational reporting | Capture governing *rules* only; keep *data* out of the authoritative layer |

## Tier 3 — National + regional (authoritative)
National implementing legislation and regional (e.g. EU) measures — expected to grow; ingest from
official gazettes/registries as enacted, in the enacting language.

## Reference only (NOT authoritative-layer)
IOC-UNESCO, WRI, High Seas Alliance, IUCN explainers and Q&As — useful for plain-language concept
mapping; attribute; keep in derived/reference only.

## Known limits
- The sanctioned fetch tool returns a text extraction and caps large PDFs (~142k chars); this
  truncated the English capture at Article 73. Byte-for-byte PDF capture (e.g. a human download or
  a page-range PDF read) is the escalation for complete, verbatim text — see GAPS.md.
- CLOs/144A-style private materials do not arise here; all core sources are public UN documents.

## G-4 live-layer inventory (mapped 2026-07-04)

**State of play:** COP1 is scheduled for **11–22 January 2027**, so no COP decisions exist yet.
PrepCom3 (23 Mar–2 Apr 2026) adopted its **Report**, forwarding recommendations + draft decisions to
COP1. Capture note: un.org-hosted PDFs truncate via the fetch tool and the GA resolutions live in the
UN ODS system (binary PDFs, not fetchable) — so finalized G-4 instruments need **byte-exact PDF**
capture (see `capture/prepcom/EXPECTED-PDFS.md`), same standard as the treaty.

### Finalized / adopted (authoritative — awaiting byte-exact PDF)
| Instrument | Symbol / source | Status |
|---|---|---|
| Report of the Preparatory Commission (3rd session) | un.org PDF (advance, unedited, 2 Apr 2026) | Adopted; awaiting byte-exact capture |
| Resolution 78/272 (establishes the PrepCom) | A/RES/78/272 (24 Apr 2024) | Adopted; ODS |
| Resolution 77/321 | A/RES/77/321 (1 Aug 2023) | Adopted; ODS |
| Resolution 79/271 | A/RES/79/271 (4 Mar 2025) | Adopted; ODS |
| Resolution 80/107 | A/RES/80/107 (9 Dec 2025) | Adopted; ODS |
| Decision 78/560 | A/78/L.102 (13 Aug 2024) | Adopted; ODS |

### Draft / negotiation aids (NOT authoritative — queued, may become COP1 decisions)
A/AC.296/2026/1–8 (Co-Chairs' "aids to discussion" and *draft* COP decisions: RoP for the COP,
financial rules, subsidiary-body ToRs, cooperation arrangements, voluntary trust fund / special fund,
GEF arrangements, secretariat seat). Host-country secretariat offers (Belgium, Chile, China) and the
Consolidated draft CHM study — reference/operational, not authoritative law. → `queue/candidates.md`.

### The live layer (monitor → ingest as adopted)
COP1 decisions (Jan 2027) — rules of procedure, subsidiary-body instruments, financial rules — will be
the first binding COP outputs. Monitored via `monitoring/sources.json` + a scheduled watch.

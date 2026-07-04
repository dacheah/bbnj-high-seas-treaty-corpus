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

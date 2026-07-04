# 01 — Provenance schema (BBNJ)

Every authoritative document carries, from its first commit, enough provenance that a stranger
can trace it to source and detect tampering. Required fields (machine-checked by
`schema/authoritative-metadata.schema.json`):

- `corpus_id` — stable identifier, assigned once (e.g. `un/bbnj-agreement-2023`).
- `version_id` — date the textual state took effect (`YYYY-MM-DD`); for the Agreement, `2023-06-19` (adoption).
- `title`, `short_title`, `jurisdiction` (`international` for UN instruments), `document_type`
  (`treaty`, `implementing_agreement`, `convention`, `prepcom_document`, `cop_decision`,
  `national_legislation`).
- `official_citation` — e.g. `A/CONF.232/2023/4`; UN Treaty Collection chapter `XXI.10`.
- `authentic_languages` (the six UN languages for UN instruments) / `language` (the stored text).
- `source_url`, `source_publisher`, `source_is_official` (UN depositary/issuer vs reproduction).
- `retrieval_date`, `retrieved_by`.
- `original_format`, `original_filename`, `original_sha256` — the byte-exact captured artifact.
- `text_sha256`, `content_hash` — hash of the stored authentic text.
- `text_fidelity` — `verbatim_transcription` > `extracted_verified` > `extracted_unverified` > `ocr_unverified`.
- `authoritative_status` — `authentic_text` | `official_consolidation` | `certified_copy` | `authoritative_missing`.
- `license`, `rights_note` — per source (see doc 04).
- `capture_history[]`, `supersedes`, `superseded_by`, `related_documents[]`, `provenance_note`.
- After a real check against the source: `verification{}`, `corrections[]`.

**Rule:** never claim more fidelity than verified. A visible gap is an asset; a hidden one is a liability.

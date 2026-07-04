# 03 — Authoritative-text policy (BBNJ)

- **Authentic-language only** in `authoritative/`. The BBNJ Agreement and UNCLOS are authentic
  in the six UN languages: Arabic (ar), Chinese (zh), English (en), French (fr), Russian (ru),
  Spanish (es). Store the authentic-language text; any translation into another language is
  derived and unofficial (doc 06).
- **Prefer official sources** — the UN (depositary: the Secretary-General; DOALOS/OLA), the UN
  Treaty Collection, and official UN document symbols. A clean copy from a non-official
  aggregator is `source_is_official: false` and is used only when no official capture is possible.
- **Reproduce faithfully, including defects.** Do not silently "fix" a typo or spacing error in
  the official source; reproduce and flag it. Corrections are dated `corrections[]` entries made
  only against the official source.
- **Gaps are flagged, not filled.** The five non-English authentic texts are recorded gaps
  (see GAPS.md), not fabricated records. Where only a translation exists and no authentic text
  can be obtained, ingest an `authoritative_status: authoritative_missing` placeholder (no text)
  and attach the translation in the derived layer.
- **Fidelity ladder** set honestly; upgrade only after a real check against the source, recording
  a `verification{}` record.

Issuers/authentic languages authoritative for this field: **United Nations** (six UN languages)
for the Agreement, UNCLOS, PrepCom and COP outputs; the enacting State (its official language)
for national implementing legislation.

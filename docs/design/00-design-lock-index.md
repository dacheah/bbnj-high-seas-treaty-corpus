# Design Lock — index (BBNJ / High Seas Treaty Corpus)

These six documents are the **constitution** of this corpus. They are **frozen** as of
2026-07-03. Change them only by a dated decision note appended to the relevant document,
never silently.

The one principle everything serves: **provenance and version integrity override
convenience, always.**

1. `01-provenance-schema.md` — metadata every authoritative document must carry.
2. `02-versioning-scheme.md` — identifiers, and how change is recorded (append-only).
3. `03-authoritative-text-policy.md` — what counts as authoritative; authentic languages; fidelity.
4. `04-licensing-policy.md` — rights to store/redistribute each source type.
5. `05-scope-boundary.md` — what is in and out of scope.
6. `06-two-layer-separation.md` — the wall between authoritative and derived.

These decisions are **inherited from the Space Law Corpus** and adjusted only for
BBNJ-specific sources, languages and scope, per the corpus opportunity brief.

## Judgement calls on record

- **JC-2026-07-03-a (authentic-language rule).** The Agreement is authentic in the six UN
  languages (ar, zh, en, fr, ru, es). Decision: store each authentic-language text as
  authoritative when captured; begin with English; treat the other five as flagged gaps
  (not `authoritative_missing` records, because the authentic texts exist and are reachable —
  they are simply not yet captured). Reason: honesty about coverage without fabricating records.
- **JC-2026-07-03-b (partial first capture).** The flagship Agreement's English text was
  captured via the sanctioned fetch tool, whose extraction was capped mid-Article-73.
  Decision: ingest the captured Preamble–Art. 73 now with `text_fidelity: extracted_unverified`
  and a loud gap note; close the gap (Arts 74–76 + Annexes I–II) by a byte-for-byte PDF
  re-capture recorded as a dated `corrections[]` entry. Reason: a working, honest corpus now;
  the gap is recorded, not hidden.
- **JC-2026-07-03-c (separate corpora).** BBNJ and the deep-seabed-mining (ISA) regime are kept
  as **separate** corpora despite both sitting under UNCLOS/ABNJ. Cross-reference; do not merge.

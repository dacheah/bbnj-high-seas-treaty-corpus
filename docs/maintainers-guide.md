# Maintainer's guide (BBNJ)

## Cadence (from the brief)
- **Phase 1 (active, now):** through COP1 and the Preparatory Commission's finalisation of
  technical details, plus the first national implementing laws. Closer-than-annual monitoring;
  automated watch on the UN BBNJ site, COP outputs and the Clearing-House Mechanism.
- **Phase 2 (settled):** annual review aligned to the COP cycle; earlier updates only on a
  material event.

## Adding an instrument
1. **Capture** from the most official source (UN depositary / UN BBNJ site / official gazette).
   Prefer a byte-exact original (PDF). If a fetch tool caps the text, escalate to a human download
   stored byte-for-byte — a provenance *upgrade*. Never bypass bot-protection/CAPTCHAs.
2. Store only the **authentic-language** text as authoritative. Translations are derived.
3. Write a manifest and run `python3 scripts/ingest.py --manifest <file>.json` (it hashes,
   writes `metadata.yaml`, validates, and refuses to overwrite an existing version).
4. **Verify** the text against the official source; upgrade `text_fidelity` with a dated
   `verification{}` record; log fixes as `corrections[]`.
5. `python3 scripts/build_derived.py` then `python3 scripts/build_site.py`.
6. `python3 scripts/validate_corpus.py` must be green before every commit.

## Closing gap G-1 (complete the Agreement text) — worked example
1. Put the complete official English PDF at `capture/Text-of-the-Agreement-in-English.pdf`.
2. Extract Articles 74–76 and Annexes I–II; append to
   `authoritative/un/bbnj-agreement-2023/2023-06-19/text.txt` (keep the reflow style).
3. Re-hash: `python3 scripts/hashing.py <text.txt>`; update `text_sha256`/`content_hash`.
4. Add a `corrections[]` entry (date, change, reference) and a `verification{}` record;
   swap `original.txt` for the byte-exact PDF and set `original_format: pdf`.
5. `build_derived` → `build_site` → `validate_corpus` (green).

## Neutrality
Concepts describe what a provision is *about*. Record the "freedom of the high seas" vs "common
heritage of mankind" tension neutrally; never editorialise on ambition or adequacy. Curate the
flagship's provision-level tags (`concepts.TAGS`) only after human review; leave the keyword
fallback labelled unreviewed until then.

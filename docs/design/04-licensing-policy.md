# 04 — Licensing policy (BBNJ)

Two different things: **our contributions** vs **the source texts**.

- **Our contributions** — the derived layer, schema, scripts, docs, generated site — are licensed
  **CC BY 4.0**.
- **Source texts are NOT relicensed.** Each keeps its own terms, recorded per document in
  `license` / `rights_note`:
  - **United Nations materials** (the Agreement, UNCLOS, PrepCom/COP documents): official UN
    documents may be freely reproduced with attribution; no warranty. `license: UN-materials-terms`.
    See the UN Terms of Use and Copyright pages.
  - **National implementing legislation**: from official gazettes/registries; rights vary by
    jurisdiction (some assert state copyright with reuse terms) — record per document.
  - **Third-party commentary / NGO-IGO explainers** (High Seas Alliance, WRI, IOC-UNESCO, etc.):
    may assert copyright — **link + cite + our own summary**; do NOT store full text without a
    clear basis. These are reference-only, never authoritative-layer.
- **Storing byte-exact originals** in-repo is appropriate for UN materials; where terms don't
  permit, default to hash + URL + provenance (no stored full text).

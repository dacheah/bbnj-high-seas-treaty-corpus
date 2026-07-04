# 06 — Two-layer separation (BBNJ)

The wall the whole corpus rests on.

- **`authoritative/`** — primary source texts only, in an authentic UN language, with full
  provenance. The legal record. **No machine- or human-generated interpretation, ever.
  Append-only.**
- **`derived/`** — everything generated: structure extraction, neutral concept tags, summaries,
  translations into non-authentic languages. Unofficial, labelled, traceable to a specific
  authoritative version by its text hash. May be regenerated.

Enforced three ways: by **folder location**, by the **schemas** (the authoritative schema forbids
model fields; the derived schema requires a source hash), and by the **validator** (which also
flags a derived artifact as *stale* when its source text hash changes). Where a file lives tells
you what it is. Never present derived content — including the concept tags — as authoritative.

# 02 — Versioning scheme (BBNJ)

Identifiers:

```
un/<slug>-<year>                 e.g. un/bbnj-agreement-2023, un/unclos-1982
un/prepcom/<slug>-<year>         Preparatory Commission documents
un/cop/<decision>-<year>         Conference of the Parties decisions
<ISO-3166-a3>/<slug>-<year>      national implementing legislation
```

On disk, one folder per version:

```
authoritative/<corpus_id>/<version_id>/
    original.<ext>   byte-exact captured artifact (integrity anchor)
    text.txt         the authentic-language text (UTF-8, LF)
    metadata.yaml    full provenance (doc 01)
```

**Append-only. Never overwrite.**
- Same text, re-retrieved → append to `capture_history`.
- Text changed (amendment / official consolidation) → a **new** `version_id` folder; set
  `supersedes` / `superseded_by`.
- Ingestion/extraction error (including the current partial-capture gap) → correct in place with
  a dated `corrections[]` entry and re-hash; the prior state stays in Git history.
- Never force-push or rewrite history. Git is the immutable, dated substrate.

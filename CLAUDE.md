# Working notes for Claude — bbnj-corpus (BBNJ / High Seas Treaty)

## Session preamble (ALWAYS)

Every block of shell commands for this repo must begin with these two lines. No exceptions —
omitting them has already caused commands to run against the wrong repo.

```
cd "C:\Users\dache\Claude\Projects\Project High\bbnj-corpus"
git branch --show-current
```

Several sibling corpus repos live under `C:\Users\dache\Claude\Projects\`, and their scripts share
filenames (`watch_sources.py`, `validate_corpus.py`, `ingest.py`). Running from the wrong folder
produces "did not match any files" at best and stages the wrong repo at worst. The branch check
honours the standing rule: verify the working tree before proposing any git command.

**Note the folder/remote mismatch:** the local folder is `bbnj-corpus`, the GitHub repo is
`bbnj-high-seas-treaty-corpus`. Do not infer either name from the other.

**When the Crawl4AI layer is lifted into this repo** (`scripts/crawl/`, currently only in
deep-seabed-mining-law-corpus), the preamble gains a third line and the venv becomes mandatory:

```
& "$env:USERPROFILE\.venvs\crawl4ai\Scripts\Activate.ps1"
```

Without it the monitor **silently** degrades to whole-page mode for every source — it does not error,
so a missing venv looks like a successful run that quietly did less.

## Repo facts

- Remote: `https://github.com/dacheah/bbnj-high-seas-treaty-corpus.git` — **public dev repo**.
- Default branch: `main`.
- Dependencies: `PyYAML`, `jsonschema`, `pymupdf` (see `scripts/requirements.txt`).

## Repo workflow

- **Write locally, the user pushes.** Never `git commit`, `git push`, or change git config from the
  agent sandbox.
- Stage **only** files explicitly created or changed, **each named individually**. Never `git add .`
  or `git add -A`.
- Name the target branch explicitly in the push command.
- Commit messages: `type: short imperative summary`, double-quoted, no `$`, backticks or nested
  quotes.

## Traps that have bitten before

- **CRLF breaks the hash gate.** Windows checkouts can rewrite `text.txt` to CRLF, whose SHA-256 no
  longer matches the recorded hash. `.gitattributes` pins `original.* binary` and `text.txt text
  eol=lf`. If verification fails on files you did not touch, check line endings first.
- **Metadata-only migrations must not change content hashes.** Prove hash-neutrality before pushing
  (all 45 records were byte-identical on the last migration).

## Layer boundary (non-negotiable)

`authoritative/` stores official files byte-for-byte. Nothing generated — no crawler output, no model
output — is ever written into it as `text.txt`; `scripts/extract.py` is the sole version-pinned
extractor, so reproducibility checks stay valid.

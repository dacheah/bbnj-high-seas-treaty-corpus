# publish-github.md — push the corpus to GitHub (run on your machine)

The repo is publish-ready: `python3 scripts/validate_corpus.py` prints `RESULT: OK.`, ~6.9 MB
of content, bulky page-renders are gitignored. Git couldn't run inside Cowork (mounted-filesystem
quirk), so run these locally, from the repo root.

```powershell
cd "C:\Users\dache\Claude\Projects\Project High\bbnj-corpus"
```

## 0. Remove the stale `.git` first (one-time)
Cowork left a broken, partial `.git` folder (a failed init on the mounted drive — it can't be
deleted from inside Cowork). Delete it before initialising:
```powershell
Remove-Item -Recurse -Force .git
```

## 1. Initialise + first commit
```powershell
git init -b main
git add -A
git status            # sanity-check what's staged (no capture/pages_*/ or *.png)
git commit -m "BBNJ / High Seas Treaty Corpus: initial release — Agreement in 6 authentic UN languages, provenance-first"
```

## 2. Create the GitHub repo + push  (pick ONE)
**A. GitHub CLI (easiest):**
```powershell
gh repo create bbnj-high-seas-treaty-corpus --public --source=. --remote=origin --push
```
**B. Manual:** create a new EMPTY repo on github.com (no README / license / .gitignore), then:
```powershell
git remote add origin https://github.com/<your-user>/bbnj-high-seas-treaty-corpus.git
git push -u origin main
```

## 3. What happens automatically after the push
- **CI integrity gate** (`.github/workflows/validate.yml`) runs `validate_corpus.py` on every push/PR —
  it should go green. This is your public tamper-evidence: anyone can recompute the hashes.
- **Monthly source watcher** (`watch-sources.yml`) opens an issue when a monitored UN page changes.
- Turn `GAPS.md` items (G-2b French/Russian audit, zh/ar OCR audit) into tracked issues.

## 4. Optional — host the browsable site
The static site is in `site/`. GitHub Pages "deploy from a branch" only serves `/` or `/docs`
(both taken here), so publish `site/` via a Pages Action or a `gh-pages` branch. Ask and I'll add a
one-file deploy workflow.

## Notes
- Public is recommended (maximises reuse; CI + watcher are free on public repos). Private also works.
- The byte-exact UN PDFs are included as integrity anchors; UN materials are freely reproducible with
  attribution (recorded per document in each `metadata.yaml` `rights_note`, and in
  `LICENSE-derived-CC-BY-4.0.txt`). Our contributions are CC BY 4.0; source texts keep their own terms.

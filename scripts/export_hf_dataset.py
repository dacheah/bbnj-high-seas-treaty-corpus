#!/usr/bin/env python3
"""
export_hf_dataset.py -- export the corpus into a Hugging Face-ready dataset.

Produces (default: ./hf-dataset/):
  data/documents.jsonl    one row per authoritative instrument version (full text + provenance)
  data/provisions.jsonl   one row per structural provision (article/section) + neutral concept tags
  README.md               the HF dataset card (YAML frontmatter + body), auto-synced to the data

Then publish in one command (needs `pip install huggingface_hub` and `huggingface-cli login`):
  huggingface-cli upload OWNER/REPO ./hf-dataset . --repo-type dataset
Or pass --push OWNER/REPO to this script to upload directly.

Reads only the OPEN layers (authoritative text + derived tags). Nothing proprietary is exported.
"""
import os, sys, json, glob, yaml, argparse, datetime, re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTH = os.path.join(REPO, "authoritative")
DER  = os.path.join(REPO, "derived")

DOC_FIELDS = ["corpus_id","version_id","title","short_title","jurisdiction","document_type",
    "official_citation","authentic_languages","language","adoption_date","entry_into_force_date",
    "source_url","source_publisher","source_is_official","authoritative_status","text_fidelity",
    "content_hash","original_sha256","text_sha256","license","rights_note","provenance_note"]

def load_meta():
    metas = {}
    for mp in glob.glob(os.path.join(AUTH, "**", "metadata.yaml"), recursive=True):
        m = yaml.safe_load(open(mp, encoding="utf-8"))
        if m.get("authoritative_status") == "authoritative_missing":
            continue
        metas[(m["corpus_id"], str(m["version_id"]))] = (m, os.path.dirname(mp))
    return metas

def build_documents(metas):
    rows = []
    for (cid, ver), (m, d) in sorted(metas.items()):
        tpath = os.path.join(d, "text.txt")
        text = open(tpath, encoding="utf-8").read() if os.path.exists(tpath) else None
        row = {k: m.get(k) for k in DOC_FIELDS}
        row["text"] = text
        row["n_chars"] = len(text) if text else 0
        rows.append(row)
    return rows

def _key(label):
    """Normalise a provision label so curated tags ('Art. 2') match structure units ('Article 2')."""
    if not label: return ""
    s = re.sub(r"^\s*(art\.?|article|principle|guideline|section|para\.?|paragraph|\u00a7)\s*", "", str(label).strip().lower())
    tok = s.split()[0] if s.split() else s
    return re.sub(r"[^a-z0-9]", "", tok)

def build_provisions(metas):
    rows = []
    for (cid, ver), (m, _d) in sorted(metas.items()):
        sdir = os.path.join(DER, cid, ver)
        sp, cp = os.path.join(sdir, "structure.json"), os.path.join(sdir, "concepts.json")
        if not os.path.exists(sp):
            continue
        units = json.load(open(sp, encoding="utf-8")).get("units", [])
        tagmap = {}
        if os.path.exists(cp):
            for t in json.load(open(cp, encoding="utf-8")).get("tags", []):
                tagmap[_key(t["unit"])] = t["concepts"]
        for u in units:
            rows.append({
                "corpus_id": cid, "version_id": ver,
                "short_title": m.get("short_title", cid), "jurisdiction": m.get("jurisdiction"),
                "document_type": m.get("document_type"), "language": m.get("language"),
                "unit_label": u.get("label"), "unit_number": u.get("number"),
                "text": u.get("text"), "concepts": tagmap.get(_key(u.get("label")), []),
                "source_text_sha256": m.get("text_sha256"), "source_url": m.get("source_url"),
                "text_fidelity": m.get("text_fidelity")})
    return rows

def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def card(docs, provs, repo_id):
    langs = sorted({d.get("language") for d in docs if d.get("language")})
    verified = sum(1 for d in docs if d.get("text_fidelity") == "extracted_verified")
    n_tags = sum(len(p["concepts"]) for p in provs)
    today = datetime.date.today().isoformat()
    fm = []
    fm.append("---")
    fm.append("pretty_name: BBNJ / High Seas Treaty Corpus")
    fm.append("license: other")
    fm.append("license_name: mixed-provenance")
    fm.append("license_link: https://github.com/dacheah/bbnj-high-seas-treaty-corpus/blob/main/docs/design/04-licensing-policy.md")
    fm.append("language:")
    for l in langs: fm.append("- " + l)
    fm.append("tags:")
    for t in ["legal","law","provenance","legal-nlp","rag"]:
        fm.append("- " + t)
    fm.append("task_categories:")
    fm.append("- text-retrieval")
    fm.append("- text-classification")
    fm.append("size_categories:")
    fm.append("- n<1K")
    fm.append("annotations_creators:")
    fm.append("- machine-generated")
    fm.append("configs:")
    fm.append("- config_name: documents")
    fm.append("  data_files: data/documents.jsonl")
    fm.append("- config_name: provisions")
    fm.append("  data_files: data/provisions.jsonl")
    fm.append("---")

    # instrument table
    tbl = ["| Instrument | Jurisdiction | Adopted | Fidelity |", "|---|---|---|---|"]
    for d in docs:
        tbl.append("| " + str(d.get("short_title") or d.get("title")) + " | " + str(d.get("jurisdiction"))
                   + " | " + str(d.get("adoption_date") or "") + " | `" + str(d.get("text_fidelity")) + "` |")

    b = []
    b.append("# BBNJ / High Seas Treaty Corpus")
    b.append("")
    b.append("A neutral, **provenance-first**, machine-readable record of the **2023 BBNJ Agreement** (the "
             "\"High Seas Treaty\", in force 17 January 2026) in **all six authentic UN languages**, and its "
             "implementing framework. Every record carries its official source, retrieval date, citation, authentic "
             "language, an authoritative-status flag, a SHA-256 content hash, and an honest per-language fidelity flag "
             "(`extracted_verified` \u2192 `extracted_unverified` \u2192 `ocr_unverified`).")
    b.append("")
    b.append("- **Source of truth / build history:** https://github.com/dacheah/bbnj-high-seas-treaty-corpus")
    b.append("- **Human-browsable site:** https://dacheah.github.io/bbnj-high-seas-treaty-corpus/ (enable GitHub Pages)")
    b.append("- **" + str(len(docs)) + "** instruments (" + str(verified) + " verified against official sources) · **"
             + str(len(provs)) + "** provisions · **" + str(n_tags) + "** neutral concept tags")
    b.append("")
    b.append("## Why this dataset is different")
    b.append("")
    b.append("Most legal datasets are scraped text with no sourcing. Here **every row is traceable**: the "
             "authoritative text is stored in its authentic language with a content hash and a fidelity flag, and "
             "anything generated (concept tags, structure) is kept in a separate, clearly-labelled layer. That makes "
             "it low-risk input for retrieval-augmented generation and citation-grounded legal NLP.")
    b.append("")
    b.append("## Configs")
    b.append("")
    b.append("**`documents`** — one row per instrument version: the full authoritative `text` plus provenance "
             "(`source_url`, `official_citation`, `authoritative_status`, `text_fidelity`, `content_hash`, `license`, "
             "`rights_note`, `provenance_note`, dates, jurisdiction, language).")
    b.append("")
    b.append("**`provisions`** — one row per structural unit (article / section / principle / guideline): the unit "
             "`text`, its neutral `concepts` (a model pass, unreviewed), and a link back to the source instrument's "
             "text hash and URL. Ideal as pre-chunked, concept-labelled context for RAG.")
    b.append("")
    b.append("```python")
    b.append("from datasets import load_dataset")
    b.append('docs = load_dataset("' + repo_id + '", "documents")')
    b.append('prov = load_dataset("' + repo_id + '", "provisions")')
    b.append("```")
    b.append("")
    b.append("## Contents")
    b.append("")
    b.extend(tbl)
    b.append("")
    b.append("## Licensing")
    b.append("")
    b.append("**Mixed, and recorded per record.** The compilation, structure, and concept tags (the derived layer) "
             "are **CC BY 4.0**. **Source texts are not relicensed** — each keeps its own terms (e.g. UN-materials "
             "terms; public-domain government works), recorded in every row's `license` / `rights_note`. See the "
             "[licensing policy](https://github.com/dacheah/bbnj-high-seas-treaty-corpus/blob/main/docs/design/04-licensing-policy.md).")
    b.append("")
    b.append("## Disclaimer")
    b.append("")
    b.append("This is a **reference record, not legal advice**. The authoritative text of each instrument is the "
             "original in its authentic language; **translations and concept tags are unofficial and derived** "
             "(the concept tags are an unreviewed model pass — expect occasional over/under-tagging). Always confirm "
             "against the cited official source for anything legally operative.")
    b.append("")
    b.append("## Citation")
    b.append("")
    b.append("```")
    b.append("BBNJ / High Seas Treaty Corpus (Dan Cheah, @dacheah). https://github.com/dacheah/bbnj-high-seas-treaty-corpus")
    b.append("```")
    b.append("")
    b.append("_Dataset generated from the repository by `scripts/export_hf_dataset.py` on " + today + " — do not edit by hand._")
    return "\n".join(fm) + "\n\n" + "\n".join(b) + "\n"

def missing_structures(metas):
    """Records that WILL export with zero provisions because their derived structure is absent.

    build_provisions() silently `continue`s past any record with no derived/<cid>/<ver>/structure.json.
    That is how a freshly-ingested record ships to Hugging Face with full text but NO provisions and
    no warning — the derived layer having gone stale relative to authoritative/. It has already
    happened this session to the ITLOS order (Deep) and Compilation 62 (Origin). Returns the list so
    export can refuse rather than publish an incomplete dataset.
    """
    miss = []
    for (cid, ver), (m, _d) in sorted(metas.items()):
        # A record with no authentic text has no provisions to build — restricted_withheld and
        # authoritative_missing legitimately have no structure. Requiring one would false-flag them
        # (caught testing Origin's restricted FATF record). Only text-bearing records need a structure.
        if m.get("authoritative_status") in ("authoritative_missing", "restricted_withheld"):
            continue
        if not m.get("text_sha256"):
            continue
        if not os.path.exists(os.path.join(DER, cid, ver, "structure.json")):
            miss.append((cid, ver))
    return miss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "hf-dataset"))
    ap.add_argument("--repo-id", default="dacheah/bbnj-high-seas-treaty-corpus")
    ap.add_argument("--push", metavar="REPO_ID", help="upload to this HF dataset repo (needs huggingface_hub + login)")
    ap.add_argument("--allow-incomplete", action="store_true",
                    help="export even if some records have no derived structure (NOT for publishing)")
    args = ap.parse_args()

    metas = load_meta()

    # FAIL CLOSED before writing anything. A publish tool must never quietly ship a corpus that is
    # less complete than it looks. Run build_derived.py and commit its output, then re-export.
    miss = missing_structures(metas)
    if miss and not args.allow_incomplete:
        print("REFUSING to export — %d record(s) have no derived structure and would ship with "
              "ZERO provisions:" % len(miss))
        for cid, ver in miss:
            print("  - %s / %s" % (cid, ver))
        print("The derived layer is stale. Run:  python3 scripts/build_derived.py   then commit "
              "derived/ and re-export. (Override with --allow-incomplete for a local preview only.)")
        return 1

    docs, provs = build_documents(metas), build_provisions(metas)
    os.makedirs(os.path.join(args.out, "data"), exist_ok=True)
    write_jsonl(os.path.join(args.out, "data", "documents.jsonl"), docs)
    write_jsonl(os.path.join(args.out, "data", "provisions.jsonl"), provs)
    open(os.path.join(args.out, "README.md"), "w", encoding="utf-8").write(card(docs, provs, args.push or args.repo_id))
    print("Exported %d documents, %d provisions -> %s" % (len(docs), len(provs), args.out))
    # HF renamed the CLI: the command is `hf` (huggingface-cli is deprecated).
    print("Publish:  hf upload %s %s . --repo-type dataset" % (args.repo_id, args.out))

    if args.push:
        from huggingface_hub import HfApi
        api = HfApi()
        api.create_repo(repo_id=args.push, repo_type="dataset", exist_ok=True)  # no-op if it exists
        api.upload_folder(folder_path=args.out, repo_id=args.push, repo_type="dataset")
        print("Pushed to https://huggingface.co/datasets/%s" % args.push)

if __name__ == "__main__":
    sys.exit(main())

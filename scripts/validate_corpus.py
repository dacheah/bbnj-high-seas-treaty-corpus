"""
validate_corpus.py -- integrity and structure checks for a provenance-first corpus.

Checks: (1) authoritative metadata validates against its schema; (2) recorded
hashes match files on disk; (3) non-"authoritative_missing" records have a
text.txt; (4) each derived-metadata.yaml is a valid list whose items trace to a
real authoritative version and whose artifact files exist; (5) staleness --
a derived artifact whose source_text_sha256 no longer matches the current
authoritative text is warned. The two-layer wall is enforced structurally
(authoritative schema forbids model fields; derived lives under derived/).

Exit 0 = OK, 1 = failures. Warnings do not fail the build.

Usage: python3 validate_corpus.py [--path <subdir>]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
from hashing import sha256_file

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "schema"


def _load_schema(name):
    with open(SCHEMA_DIR / name, "r", encoding="utf-8") as f:
        return Draft202012Validator(json.load(f))


def _load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _path_identity(record_meta, meta, errors):
    """The metadata must agree with the directory the record lives in.

    authoritative/<corpus_id>/<version_id>/metadata.yaml is not a filing convention. It is the
    address every citation, every derived trace and every supersedes chain resolves through. A
    record whose metadata says one thing and whose path says another is misfiled, and it will
    still resolve — to the wrong instrument.

    Added 2026-07-21 after a mutation study showed a record could be given any corpus_id or
    version_id at all and still validate clean, in all five corpora. Found by breaking it on
    purpose, not by reading it.
    """
    try:
        rel = record_meta.parent.relative_to(REPO_ROOT / "authoritative").as_posix()
    except ValueError:
        return
    want_cid, _, want_vid = rel.rpartition("/")
    where = record_meta.relative_to(REPO_ROOT)
    if str(meta.get("corpus_id")) != want_cid:
        errors.append(f"[path] {where}: corpus_id {meta.get('corpus_id')!r} does not match its "
                      f"directory {want_cid!r}")
    if str(meta.get("version_id")) != want_vid:
        errors.append(f"[path] {where}: version_id {meta.get('version_id')!r} does not match its "
                      f"directory name {want_vid!r}")


def validate_authoritative(record_meta, schema, errors, warnings):
    rel = record_meta.relative_to(REPO_ROOT)
    meta = _load_yaml(record_meta)
    vdir = record_meta.parent
    _path_identity(record_meta, meta, errors)
    errs = sorted(schema.iter_errors(meta), key=lambda e: str(list(e.path)))
    for e in errs:
        loc = "/".join(str(p) for p in e.path) or "(root)"
        errors.append(f"[schema] {rel}: {loc}: {e.message}")
    if errs:
        return
    status = meta.get("authoritative_status")
    opath = vdir / meta["original_filename"]
    if status != "authoritative_missing":
        if not opath.exists():
            errors.append(f"[file] {rel}: original artifact missing")
        elif sha256_file(opath) != meta["original_sha256"]:
            errors.append(f"[hash] {rel}: original_sha256 mismatch")
    tpath = vdir / "text.txt"
    if status == "authoritative_missing":
        if tpath.exists():
            errors.append(f"[policy] {rel}: authoritative_missing must not contain text.txt")
    else:
        if not tpath.exists():
            errors.append(f"[file] {rel}: text.txt missing")
        else:
            if sha256_file(tpath) != meta.get("text_sha256"):
                errors.append(f"[hash] {rel}: text_sha256 mismatch")
            if meta.get("content_hash") != meta.get("text_sha256"):
                errors.append(f"[hash] {rel}: content_hash should equal text_sha256")


def validate_derived(record_meta, schema, errors, warnings):
    rel = record_meta.relative_to(REPO_ROOT)
    meta = _load_yaml(record_meta)
    errs = sorted(schema.iter_errors(meta), key=lambda e: str(list(e.path)))
    for e in errs:
        loc = "/".join(str(p) for p in e.path) or "(root)"
        errors.append(f"[schema] {rel}: {loc}: {e.message}")
    if errs:
        return
    for item in meta:
        src_meta = (REPO_ROOT / "authoritative" / item["source_corpus_id"]
                    / str(item["source_version_id"]) / "metadata.yaml")
        if not src_meta.exists():
            errors.append(f"[trace] {rel}: {item['derived_id']}: source version not found")
            continue
        if not (record_meta.parent / item["artifact_file"]).exists():
            errors.append(f"[file] {rel}: {item['derived_id']}: artifact_file missing")
        src = _load_yaml(src_meta)
        if src.get("text_sha256") and item.get("source_text_sha256") != src.get("text_sha256"):
            warnings.append(f"[stale] {rel}: {item['derived_id']} source hash changed -- regenerate/re-review")


def validate_all(subpath=None, allow_empty=False):
    errors, warnings = [], []
    auth_schema = _load_schema("authoritative-metadata.schema.json")
    der_schema = _load_schema("derived-metadata.schema.json")
    scope = REPO_ROOT / subpath if subpath else None
    n_auth = n_der = 0
    for m in sorted((REPO_ROOT / "authoritative").rglob("metadata.yaml")):
        if scope and scope not in m.parents and scope != m.parent:
            continue
        validate_authoritative(m, auth_schema, errors, warnings); n_auth += 1
    for m in sorted((REPO_ROOT / "derived").rglob("derived-metadata.yaml")):
        if scope and scope not in m.parents and scope != m.parent:
            continue
        validate_derived(m, der_schema, errors, warnings); n_der += 1
    if n_auth == 0 and not allow_empty:
        # A gate that reports OK on an empty corpus reports OK on anything. Emptying both layers
        # produced "Checked 0 authoritative record(s)" and "RESULT: OK", exit 0, in all five
        # corpora. Emptying only authoritative/ WAS caught, but incidentally, by the derived
        # layer noticing its sources had gone -- a rescue that vanishes for any corpus without a
        # derived layer, and not the check anyone believed was running.
        errors.append("[empty] no authoritative records found"
                      + (f" under {subpath!r}" if subpath else "")
                      + " -- refusing to report OK on nothing. Use --allow-empty only when "
                        "deliberately bootstrapping a new corpus.")
    return errors, warnings, n_auth, n_der


def main():
    ap = argparse.ArgumentParser(description="Validate the corpus (schema, hashes, two-layer wall, derived staleness).")
    ap.add_argument("--path", default=None, help="Optional subpath to limit validation")
    ap.add_argument("--allow-empty", action="store_true",
                    help="permit a run that finds zero authoritative records (bootstrap only)")
    args = ap.parse_args()
    errors, warnings, n_auth, n_der = validate_all(args.path, args.allow_empty)
    print(f"Checked {n_auth} authoritative record(s), {n_der} derived record(s).")
    for w in warnings:
        print("WARN  " + w)
    for e in errors:
        print("FAIL  " + e)
    if errors:
        print(f"\nRESULT: FAILED with {len(errors)} error(s).")
        return 1
    print(f"\nRESULT: OK{' (with ' + str(len(warnings)) + ' warning(s))' if warnings else ''}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

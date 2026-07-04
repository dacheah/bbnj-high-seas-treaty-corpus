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


def validate_authoritative(record_meta, schema, errors, warnings):
    rel = record_meta.relative_to(REPO_ROOT)
    meta = _load_yaml(record_meta)
    vdir = record_meta.parent
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


def validate_all(subpath=None):
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
    return errors, warnings, n_auth, n_der


def main():
    ap = argparse.ArgumentParser(description="Validate the corpus (schema, hashes, two-layer wall, derived staleness).")
    ap.add_argument("--path", default=None, help="Optional subpath to limit validation")
    args = ap.parse_args()
    errors, warnings, n_auth, n_der = validate_all(args.path)
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

"""
ingest.py — package a captured source document into the authoritative layer.

DESIGN: capture vs. ingest are separated on purpose.
  * CAPTURE (retrieving bytes from a source URL) is done separately, using the
    approved retrieval tooling, and the captured file is handed to this script.
  * INGEST (this script) is fully deterministic and offline: it packages the
    captured original (and an optional cleaned authentic-language text) into an
    authoritative version folder, computes SHA-256 hashes, writes a complete
    metadata.yaml, and validates it.

INVARIANTS (see docs/design/02):
  * Append-only. This script REFUSES to write into a version folder that already
    has a metadata.yaml. Corrections and amendments are NEW versions, never
    overwrites.
  * No fetching, no model output. This is packaging only.

Usage:
    python3 ingest.py --manifest path/to/manifest.json

The manifest is a JSON object with the document's metadata fields plus:
    original_source_path : path to the captured original artifact (required)
    text_source_path     : path to the cleaned authentic-language text (optional;
                           required unless authoritative_status == authoritative_missing)
    capture_note         : note for the first capture_history entry (optional)
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml

from hashing import sha256_file, sha256_bytes, normalize_text_bytes
import validate_corpus

REPO_ROOT = Path(__file__).resolve().parent.parent

_EXT = {"pdf": "pdf", "html": "html", "docx": "docx", "txt": "txt", "other": "bin"}

# Order in which keys are written to metadata.yaml (readability; matches doc 01).
_KEY_ORDER = [
    "corpus_id", "version_id", "title", "short_title",
    "jurisdiction", "document_type", "official_citation", "authentic_languages",
    "adoption_date", "entry_into_force_date", "effective_date",
    "source_url", "source_publisher", "source_is_official",
    "retrieval_date", "retrieved_by", "original_format", "original_filename",
    "content_hash", "original_sha256", "text_sha256", "text_fidelity",
    "language", "authoritative_status", "license", "rights_note",
    "capture_history", "supersedes", "superseded_by", "related_documents",
    "provenance_note",
    # Added by the 2026-07 metadata-layer migration. binding_force and issuing_authority are
    # REQUIRED by authoritative-metadata.schema.json; administering_authority is nullable.
    # They were added to the schema and backfilled into existing records, but this ingester was
    # not updated at the time — so any NEW record would have failed validation on write.
    "binding_force", "issuing_authority", "administering_authority",
]


def _ordered(meta: dict) -> dict:
    out = {}
    for k in _KEY_ORDER:
        if k in meta:
            out[k] = meta[k]
    # Anything unexpected (shouldn't happen) goes last so nothing is silently lost.
    for k, v in meta.items():
        if k not in out:
            out[k] = v
    return out


def ingest_document(manifest: dict, repo_root: Path = REPO_ROOT) -> Path:
    corpus_id = manifest["corpus_id"]
    version_id = str(manifest["version_id"])
    status = manifest["authoritative_status"]

    version_dir = repo_root / "authoritative" / corpus_id / version_id
    if (version_dir / "metadata.yaml").exists():
        raise SystemExit(
            f"REFUSING to overwrite existing record at {version_dir}. "
            f"Corrections/amendments must be a NEW version_id (append-only)."
        )
    version_dir.mkdir(parents=True, exist_ok=True)

    # --- original artifact ---
    original_format = manifest["original_format"]
    original_filename = "original." + _EXT.get(original_format, "bin")
    src_original = Path(manifest["original_source_path"])
    shutil.copyfile(src_original, version_dir / original_filename)
    original_sha256 = sha256_file(version_dir / original_filename)

    # --- authentic-language text (if any) ---
    text_sha256 = None
    if status != "authoritative_missing":
        if manifest.get("text_source_path"):
            raw = Path(manifest["text_source_path"]).read_text(encoding="utf-8")
        elif original_format == "txt":
            raw = src_original.read_text(encoding="utf-8")
        else:
            raise SystemExit("A text_source_path is required unless "
                             "authoritative_status is authoritative_missing.")
        text_bytes = normalize_text_bytes(raw)
        (version_dir / "text.txt").write_bytes(text_bytes)
        text_sha256 = sha256_bytes(text_bytes)

    content_hash = text_sha256 if text_sha256 else original_sha256

    # --- assemble metadata ---
    meta = {
        "corpus_id": corpus_id,
        "version_id": version_id,
        "title": manifest["title"],
        "jurisdiction": manifest["jurisdiction"],
        "document_type": manifest["document_type"],
        "official_citation": manifest["official_citation"],
        "authentic_languages": manifest["authentic_languages"],
        "source_url": manifest["source_url"],
        "source_publisher": manifest["source_publisher"],
        "source_is_official": bool(manifest["source_is_official"]),
        "retrieval_date": manifest["retrieval_date"],
        "retrieved_by": manifest["retrieved_by"],
        "original_format": original_format,
        "original_filename": original_filename,
        "content_hash": content_hash,
        "original_sha256": original_sha256,
        "language": manifest["language"],
        "authoritative_status": status,
        "license": manifest["license"],
        "capture_history": [{
            "date": manifest["retrieval_date"],
            "source_url": manifest["source_url"],
            "original_sha256": original_sha256,
            "note": manifest.get("capture_note", "Initial capture."),
        }],
        "supersedes": manifest.get("supersedes"),
        "superseded_by": manifest.get("superseded_by"),
        "related_documents": manifest.get("related_documents", []),
        "provenance_note": manifest["provenance_note"],
        # Required by the schema since the 2026-07 migration. Deliberately manifest[...] not
        # .get(): a missing value must fail loudly at ingest rather than silently produce a
        # record that fails validation afterwards.
        "binding_force": manifest["binding_force"],
        "issuing_authority": manifest["issuing_authority"],
        "administering_authority": manifest.get("administering_authority"),
    }
    if text_sha256:
        meta["text_sha256"] = text_sha256
        meta["text_fidelity"] = manifest["text_fidelity"]
    for opt in ("short_title", "adoption_date", "entry_into_force_date",
                "effective_date", "rights_note"):
        if manifest.get(opt) is not None:
            meta[opt] = manifest[opt]

    with open(version_dir / "metadata.yaml", "w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(_ordered(meta), f, sort_keys=False, allow_unicode=True,
                       default_flow_style=False, width=100)

    return version_dir


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest a captured document into the authoritative layer.")
    ap.add_argument("--manifest", required=True, help="Path to the ingest manifest JSON.")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    version_dir = ingest_document(manifest)
    rel = version_dir.relative_to(REPO_ROOT)
    print(f"Ingested -> {rel}")

    # Validate just this record immediately.
    errors, warnings, n_auth, _ = validate_corpus.validate_all(str(rel))
    for w in warnings:
        print("WARN  " + w)
    for e in errors:
        print("FAIL  " + e)
    if errors:
        print("\nRESULT: FAILED — the record was written but does not validate. Fix before committing.")
        return 1
    print("\nRESULT: OK — record validates (schema + hashes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

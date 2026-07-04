"""
hashing.py — content hashing for a provenance-first corpus.

A hash is a short fingerprint of a file's exact bytes. If a single character
changes, the hash changes completely. This is how we prove, years later, that a
stored text has not been silently altered.

Rules (fixed in docs/design/01-provenance-schema.md, section 4):
  * Algorithm: SHA-256, always written with the "sha256:" prefix.
  * original_sha256 is computed over the RAW BYTES of the original artifact.
  * text_sha256 is computed over the RAW BYTES of text.txt as stored
    (UTF-8, LF line endings, no BOM).
  * These are computed by tooling, never hand-edited.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

PREFIX = "sha256:"


def sha256_bytes(data: bytes) -> str:
    """Return the prefixed SHA-256 hash of a byte string."""
    return PREFIX + hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    """Return the prefixed SHA-256 hash of a file's raw bytes."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return PREFIX + h.hexdigest()


def normalize_text_bytes(text: str) -> bytes:
    """
    Canonical byte form for a stored text.txt: UTF-8, LF line endings, no BOM,
    exactly one trailing newline. Fixing this makes text_sha256 reproducible on
    any machine.
    """
    # Normalise all line endings to LF.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip a leading BOM if present.
    if text.startswith("﻿"):
        text = text[1:]
    # Exactly one trailing newline.
    text = text.rstrip("\n") + "\n"
    return text.encode("utf-8")


if __name__ == "__main__":
    import sys

    for p in sys.argv[1:]:
        print(f"{sha256_file(p)}  {p}")

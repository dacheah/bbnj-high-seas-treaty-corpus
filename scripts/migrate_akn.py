#!/usr/bin/env python3
"""Add (or refresh) the four AKN identifier fields on every authoritative record.

Dry-run by default. Nothing is written without --apply.

WHY THIS DOES NOT ROUND-TRIP THE YAML
-------------------------------------
The obvious implementation is yaml.safe_load then yaml.safe_dump. It is wrong here. A
round-trip rewrites the whole file: key order changes, quoting style changes, comments are
destroyed, long strings refold. In a provenance corpus that turns a four-line addition into
a whole-file diff, and a whole-file diff is one nobody reads carefully — which is exactly
where an unnoticed change to a source_url or a retrieval_date would hide.

So this edits as TEXT: strip any existing akn_* lines, append the new block, leave every
other byte alone. The result is a diff a human can actually review.

SAFETY
------
metadata.yaml is not itself hashed — content_hash/text_sha256/original_sha256 cover
text.txt and the original artifact, which this never touches. --apply re-reads and
re-validates every file afterwards, and refuses to leave a record in a state akn.check()
would reject.
"""

from __future__ import annotations

import argparse
import collections
import glob
import os
import sys

import yaml

import akn

FIELDS = ("akn_uri", "akn_expression_uri", "akn_uri_basis", "akn_uri_note")


def _render_block(work, expr, basis, note) -> str:
    """Emit the four fields as YAML, using safe_dump only for the small block so quoting and
    escaping are correct without touching the rest of the file."""
    block = collections.OrderedDict(
        (("akn_uri", work), ("akn_expression_uri", expr),
         ("akn_uri_basis", basis), ("akn_uri_note", note or ""))
    )
    return yaml.safe_dump(dict(block), default_flow_style=False, allow_unicode=True,
                          sort_keys=True, width=100)


def _strip_existing(text: str) -> str:
    """Remove a previously written akn_* block, including any continuation lines of a folded
    scalar, so re-running is idempotent rather than accumulating duplicates."""
    out, skipping = [], False
    for line in text.splitlines(keepends=True):
        if any(line.startswith(f + ":") for f in FIELDS):
            skipping = True
            continue
        if skipping:
            # continuation of the previous value (indented, and not a new top-level key)
            if line.strip() and (line[0] in " \t"):
                continue
            skipping = False
        out.append(line)
    return "".join(out)


def process(root: str, reg: dict, apply: bool):
    files = sorted(glob.glob(os.path.join(root, "authoritative", "**", "metadata.yaml"),
                             recursive=True))
    stats = collections.Counter()
    minted_pairs, changed = [], []
    for path in files:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
        meta = yaml.safe_load(raw)
        if not isinstance(meta, dict):
            print(f"  SKIP (not a mapping): {path}")
            stats["skipped"] += 1
            continue

        work, expr, basis, note = akn.mint(meta, reg)
        problems = akn.check(work, basis, note)
        if problems:
            raise SystemExit(f"refusing to write {path}: {problems}")
        stats[basis] += 1
        if work:
            minted_pairs.append((meta.get("corpus_id", path), work, expr))

        already = all(meta.get(f) == v for f, v in
                      zip(FIELDS, (work, expr, basis, note or "")))
        if already:
            continue
        changed.append(path)
        if not apply:
            continue

        body = _strip_existing(raw)
        if body and not body.endswith("\n"):
            body += "\n"
        # newline="\n" is not optional: Windows text mode would emit CRLF into a tracked file
        # and .gitattributes only governs checkout, not what a script writes.
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body + _render_block(work, expr, basis, note))

    collisions = akn.check_collisions(minted_pairs)
    return stats, changed, collisions, len(files)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--apply", action="store_true", help="write changes (default is dry-run)")
    args = ap.parse_args()

    reg = akn.load_registry(os.path.join(args.root, "schema", "akn-registry.json"))
    stats, changed, collisions, n = process(args.root, reg, args.apply)

    mode = "APPLIED" if args.apply else "DRY RUN"
    print(f"[{mode}] {n} record(s) in {args.root}")
    for k in sorted(stats):
        print(f"    {k}: {stats[k]}")
    print(f"    records needing change: {len(changed)}")
    if collisions:
        for c in collisions:
            print(f"    COLLISION: {c}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

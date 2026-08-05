#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_engine.py — verify the build engine against MANIFEST.sha256, set-aware.

WHY THIS EXISTS, AND WHAT `sha256sum -c` MISSES. BUILD.md pins the engine with MANIFEST.sha256 and
verifies it with `sha256sum -c scripts/MANIFEST.sha256`. That command checks every file the manifest
LISTS — so it catches a modified file and a deleted file. It is blind, by construction, to a file
that was ADDED: a new *.py the manifest does not mention is simply never looked at, and the check
passes green.

That is not hypothetical. On 2026-07-21 `draft_versions.py` had been added to the engine but not to
the manifest; `sha256sum -c` reported OK, and the engine fingerprint (the sha256 of the manifest)
still named an engine that no longer existed. An engine-integrity check that cannot see new code is
the wrong check for a system whose whole promise is "this exact engine produced this corpus".

WHAT THIS DOES. Parses the manifest, lists the engine files actually on disk (the SAME glob the
manifest is generated from — *.py *.json *.txt), and reconciles the two SETS as well as the hashes:

    modified   listed, on disk, hash differs
    removed    listed, not on disk
    added      on disk, not listed          <-- the class sha256sum -c cannot see
    ok         listed, on disk, hash matches

Any of modified / removed / added fails. Only an exact set match with matching hashes passes, so the
fingerprint provably names the files that are actually there.

    python3 scripts/verify_engine.py            # verify; exit 1 on any drift
    python3 scripts/verify_engine.py --selftest # offline
"""
from __future__ import annotations
import glob
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # repo root; manifest names are relative to THIS
MANIFEST = os.path.join(HERE, "MANIFEST.sha256")
MANIFEST_NAME = "scripts/MANIFEST.sha256"

# Globs are relative to the REPO ROOT, not to scripts/, and manifest entries are repo-relative
# paths ("scripts/extract.py", "schema/akn-registry.json").
#
# WHY schema/ IS IN SCOPE (widened 2026-08-05). The fingerprint claims to pin "the code that
# PRODUCES the published corpus". schema/akn-registry.json is not code, but it fully determines
# the identifiers akn.py mints: change one country code there and every akn_uri in the corpus
# changes, while a scripts-only fingerprint sits perfectly still. A fingerprint that can miss a
# change to its own output is not pinning what it says it pins. The metadata schemas are in for
# the same reason — they define what the engine will accept and emit.
#
# This widening re-pins the fingerprint once, and renames every manifest entry from a bare
# basename to a repo-relative path. Both are deliberate; regenerate and record the new value.
ENGINE_GLOBS = ("scripts/*.py", "scripts/*.json", "scripts/*.txt", "schema/*.json")
SELF = "verify_engine.py"        # this file can verify itself once it is added to the manifest

# Files that live in scripts/ but are NOT part of the reproducibility engine.
#
# THE DIVIDING LINE. Inside the fingerprint: everything that decides what a corpus byte becomes,
# or asserts that it is right — ingest, extract, the build_* producers, validate_corpus,
# verify_fidelity, repro_gate, the schemas, and the AKN registry. Outside it: the DETECTION layer,
# whose output is gated by a human before anything is ingested, and which therefore cannot silently
# change a published byte.
#
#   watch_sources.py    — the source MONITOR. Watches official URLs and queues changes for human
#                         triage. Before this exclusion, every routine monitor tweak (v3.5 -> v3.6
#                         progress output) moved the fingerprint and made a just-cut release
#                         (v1.4.0) stale for no reason.
#   draft_versions.py   — drafts ingest manifests for HUMAN review; the human then runs ingest.py,
#                         which IS in the engine. Pre-build convenience, not the build.
#   audit_sources.py    — audits the monitor's source registry (are the watched URLs still the right
#                         pages?). Same layer as watch_sources.py, same change cadence.
#   build_monitoring.py — generates monitoring config. Monitoring, not corpus.
#   recipes.json        — crawl recipes consumed by the monitor.
#
# All remain in the repo, version-controlled and drift-checked; they are simply outside the
# reproducibility boundary. Names listed here that do not exist in a given corpus are no-ops, so
# one list serves every corpus in the portfolio.
ENGINE_EXCLUDE = (
    "scripts/watch_sources.py",
    "scripts/draft_versions.py",
    "scripts/audit_sources.py",
    "scripts/build_monitoring.py",
    "scripts/recipes.json",
)

MANIFEST_HEADER = (
    "# Build-engine manifest — SHA-256 of every REPRODUCIBILITY-ENGINE file in the Project Origin\n"
    "# corpus toolkit (the code that PRODUCES the published corpus). Non-producing tooling is\n"
    "# excluded — see ENGINE_EXCLUDE in verify_engine.py — so routine monitoring changes do not move\n"
    "# it. Scope covers scripts/ AND schema/: the schemas and the AKN registry determine what the\n"
    "# engine emits, so a change there MUST move the fingerprint. Paths are repo-relative.\n"
    "# Regenerate with:  python3 verify_engine.py --generate\n"
    "# Verify with:      python3 verify_engine.py\n")


def parse_manifest(text: str) -> dict:
    """{filename: sha256hex} from a `sha256sum`-format file, ignoring # comment lines."""
    out = {}
    for line in text.splitlines():
        line = line.rstrip("\n")
        if not line or line.lstrip().startswith("#"):
            continue
        # `sha256sum` format: "<64 hex><space><space-or-*><filename>"
        parts = line.split(None, 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            continue
        out[parts[1].lstrip("*").strip()] = parts[0].lower()
    return out


def engine_files_on_disk(root: str) -> set:
    names = set()
    for g in ENGINE_GLOBS:
        for p in glob.glob(os.path.join(root, *g.split("/"))):
            names.add(os.path.relpath(p, root).replace(os.sep, "/"))
    # Exclude non-engine tooling here, at the single point that defines "on disk", so BOTH the
    # verify path and the --generate path see the identical set. If they diverged, generate would
    # write a manifest that verify then flags as drifted.
    return names - set(ENGINE_EXCLUDE)


def generate_manifest(root: str) -> str:
    """Produce MANIFEST.sha256 text from the engine files on disk — the one source of truth for
    scope. Byte-identical to what verify expects, so regenerating never spuriously moves the hash."""
    hexes = sha256_of(root)
    files = sorted(engine_files_on_disk(root) - {MANIFEST_NAME})
    return MANIFEST_HEADER + "".join(f"{hexes(fn)}  {fn}\n" for fn in files)


def reconcile(listed: dict, on_disk: set, hash_of) -> dict:
    """Return {filename: state}. state in ok|modified|removed|added.

    `listed` excludes the manifest file itself (it cannot hash-list its own hash). `hash_of` is a
    filename->hex function so this stays a pure, testable function.
    """
    listed = {k: v for k, v in listed.items() if k != MANIFEST_NAME}
    on_disk = {n for n in on_disk if n != MANIFEST_NAME}
    states = {}
    for name in listed:
        if name not in on_disk:
            states[name] = "removed"
        elif hash_of(name) != listed[name]:
            states[name] = "modified"
        else:
            states[name] = "ok"
    for name in on_disk:
        if name not in listed:
            states[name] = "added"
    return states


def sha256_of(root):
    def f(name):
        h = hashlib.sha256()
        with open(os.path.join(root, *name.split("/")), "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    return f


def selftest() -> int:
    m = "# header\n" + "a" * 64 + "  scripts/extract.py\n" + "b" * 64 + "  schema/akn-registry.json\n"
    parsed = parse_manifest(m)
    assert parsed == {"scripts/extract.py": "a" * 64, "schema/akn-registry.json": "b" * 64}, parsed

    fake = {"scripts/extract.py": "a" * 64}
    # a NEW file on disk that the manifest never mentions MUST surface as 'added' — the whole point
    st = reconcile(fake, {"scripts/extract.py", "scripts/new_build_step.py"}, lambda n: "a" * 64)
    assert st["scripts/extract.py"] == "ok"
    assert st["scripts/new_build_step.py"] == "added", "an unlisted engine file must never pass unseen"

    st = reconcile({"scripts/extract.py": "a" * 64}, {"scripts/extract.py"}, lambda n: "c" * 64)
    assert st["scripts/extract.py"] == "modified"
    st = reconcile({"gone.py": "a" * 64}, set(), lambda n: "")
    assert st["gone.py"] == "removed"
    # exact match, matching hash -> clean
    st = reconcile({"x.py": "d" * 64}, {"x.py"}, lambda n: "d" * 64)
    assert st == {"x.py": "ok"}

    # scope: the excluded tooling must NOT count as an engine file. Simulate a scripts/ dir and
    # confirm engine_files_on_disk drops ENGINE_EXCLUDE — otherwise the monitor would re-enter the
    # fingerprint the moment someone touched it.
    import tempfile
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "scripts")); os.makedirs(os.path.join(d, "schema"))
    for fn in ("scripts/extract.py", "scripts/ingest.py", "scripts/watch_sources.py",
               "scripts/draft_versions.py", "scripts/notes.md",
               "scripts/audit_sources.py", "scripts/recipes.json", "scripts/validate_corpus.py",
               "schema/akn-registry.json", "schema/authoritative-metadata.schema.json",
               "schema/README.md", "authoritative/should-not-be-scanned.json"):
        fp_ = os.path.join(d, *fn.split("/"))
        os.makedirs(os.path.dirname(fp_), exist_ok=True)
        open(fp_, "w").close()
    got = engine_files_on_disk(d)
    assert "scripts/extract.py" in got and "scripts/ingest.py" in got, got
    assert "scripts/watch_sources.py" not in got, "the source monitor must be OUTSIDE the fingerprint"
    assert "scripts/draft_versions.py" not in got, "the manifest drafter must be OUTSIDE the fingerprint"
    assert "scripts/audit_sources.py" not in got, "the source auditor is detection, not build"
    assert "scripts/recipes.json" not in got, "crawl recipes are detection, not build"
    assert "scripts/notes.md" not in got, "only *.py/*.json/*.txt are engine files"
    # the widening: schema/ IS in scope, because it determines what the engine emits
    assert "schema/akn-registry.json" in got, "the AKN registry MUST be fingerprinted"
    assert "scripts/validate_corpus.py" in got, "verification tooling stays INSIDE the fingerprint"
    assert "schema/authoritative-metadata.schema.json" in got, "schemas determine engine output"
    assert "schema/README.md" not in got, "only *.json under schema/"
    # and the corpus itself is NOT the engine
    assert "authoritative/should-not-be-scanned.json" not in got, \
        "corpus content must never enter the engine fingerprint"
    # --generate output round-trips: verifying the generated manifest is clean by construction
    man = generate_manifest(d)
    assert "watch_sources.py" not in man and "scripts/extract.py" in man
    assert "schema/akn-registry.json" in man
    parsed2 = parse_manifest(man)
    st = reconcile(parsed2, engine_files_on_disk(d), sha256_of(d))
    assert all(v == "ok" for v in st.values()), st

    print("verify_engine selftest: OK")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--generate" in sys.argv:
        text = generate_manifest(ROOT)
        with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        fp = hashlib.sha256(open(MANIFEST, "rb").read()).hexdigest()
        n = sum(1 for _ in text.splitlines() if _ and not _.startswith("#"))
        print(f"wrote {MANIFEST} ({n} engine files; {', '.join(ENGINE_EXCLUDE)} excluded)")
        print(f"engine fingerprint: {fp}")
        return 0
    if not os.path.isfile(MANIFEST):
        print(f"FAIL: no manifest at {MANIFEST}")
        return 1
    listed = parse_manifest(open(MANIFEST, encoding="utf-8").read())
    on_disk = engine_files_on_disk(ROOT)
    states = reconcile(listed, on_disk, sha256_of(ROOT))

    order = {"added": 0, "modified": 1, "removed": 2, "ok": 3}
    bad = {k: v for k, v in states.items() if v != "ok"}
    for name in sorted(states, key=lambda n: (order[states[n]], n)):
        if states[name] != "ok":
            print(f"  {states[name].upper():9} {name}")
    n_ok = sum(1 for v in states.values() if v == "ok")
    if bad:
        print(f"\nRESULT: FAILED — {len(bad)} file(s) drifted from the manifest "
              f"({sum(v == 'added' for v in bad.values())} added, "
              f"{sum(v == 'modified' for v in bad.values())} modified, "
              f"{sum(v == 'removed' for v in bad.values())} removed). "
              f"Regenerate the manifest and re-record the engine fingerprint.")
        return 1
    fp = hashlib.sha256(open(MANIFEST, "rb").read()).hexdigest()
    print(f"RESULT: OK — {n_ok} engine files match the manifest exactly.")
    print(f"engine fingerprint: {fp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

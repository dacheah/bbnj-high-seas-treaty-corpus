#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repro_gate.py — one reproducibility gate for every corpus.

WHAT THIS REPLACES. Five corpora grew five copies of the same walk/classify/report/exit skeleton
around five (legitimately different) extractors. The extractors are fine; the skeletons were not,
and they disagreed:

  * Deep aborted on the FIRST record without a recipe, so one OCR-derived order kept its whole
    reproduce.yml red and DARK — 27 passing records went unreported behind the abort.
  * BBNJ's denominator was a hardcoded RECIPES list, so a newly ingested record was invisible and
    the gate still printed "13/13".
  * Neo proved 35 of 70 and exited 0 — the honesty was in the prose, not the exit code.
  * Origin printed "69/69" while quietly skipping a 70th record.

Every one of those is the same bug: each gate chose its own denominator and reported success
against it. This gate takes ONE denominator — every metadata.yaml under authoritative/ — and gives
every record exactly one verdict in one vocabulary:

  reproduced  committed code re-derives the stored text (byte-exact, or Space's declared token
              criterion) — the guarantee.
  mismatch    a recipe exists and it DID NOT match — a real failure, investigate.
  uncovered   no recipe. Not invisible, not fatal-on-sight: counted, and gated by a ratchet.
  excluded    declared not-reproducible WITH A REASON (OCR via a network service; secondary
              source; restricted_withheld; authoritative_missing).
  error       the extractor raised. The monitor did not look — never a silent pass.

THE EXTRACTORS ARE NOT TOUCHED. This file reaches into each corpus's own extract.py through a
per-corpus adapter, so a record's verdict and derived hash are a pure function of the unchanged
extractor. That is the safety property the shared-harness refactor rests on: same extractor bytes
-> same verdicts, proven by --emit-json diffing against the pre-refactor baseline.

TWO MODES, ONE CODE PATH, so the audit instrument and the deployed gate can never drift:
    python3 scripts/repro_gate.py                 # gate: policy + invariant, sets exit code
    python3 scripts/repro_gate.py --emit-json     # per-record verdicts as JSON (baseline capture)
    python3 scripts/repro_gate.py --propose        # print the uncovered count, for setting a ceiling
"""
from __future__ import annotations
import argparse
import glob
import hashlib
import json
import os
import sys

VERDICTS = ("reproduced", "mismatch", "uncovered", "excluded", "error")
HERE = os.path.dirname(os.path.abspath(__file__))


def metas(corpus):
    import yaml
    for mp in sorted(glob.glob(os.path.join(corpus, "authoritative", "**", "metadata.yaml"),
                               recursive=True)):
        yield mp, yaml.safe_load(open(mp, encoding="utf-8"))


def row(meta, verdict, detail="", derived=None, extra=None):
    assert verdict in VERDICTS, verdict
    r = {"corpus_id": meta.get("corpus_id"), "version_id": str(meta.get("version_id")),
         "verdict": verdict, "detail": detail,
         "stored_sha256": meta.get("text_sha256"), "derived_sha256": derived}
    if extra:
        r.update(extra)
    return r


def _no_text(meta):
    if meta.get("authoritative_status") in ("authoritative_missing", "restricted_withheld"):
        return f"authoritative_status={meta['authoritative_status']} — no stored text by design"
    if not meta.get("text_sha256"):
        return "no text_sha256 — record stores no text"
    return None


# ---- adapters: the seam into each corpus's own, unchanged extract.py ------------------------
def adapt_deep(corpus, ex):
    for mp, m in metas(corpus):
        why = _no_text(m)
        if why:
            yield row(m, "excluded", why); continue
        d = os.path.dirname(mp)
        try:
            got = ex.rederive(m, d)
        except SystemExit as e:
            yield row(m, "uncovered", str(e)); continue
        except Exception as e:
            yield row(m, "error", f"{type(e).__name__}: {e}"); continue
        if got is None:
            yield row(m, "excluded", "rederive() returned None"); continue
        h = "sha256:" + hashlib.sha256(got).hexdigest()
        yield row(m, "reproduced" if h == m.get("text_sha256") else "mismatch", "", h)


def adapt_origin(corpus, ex):
    from hashing import normalize_text_bytes
    for mp, m in metas(corpus):
        why = _no_text(m)
        if why:
            yield row(m, "excluded", why); continue
        d = os.path.dirname(mp)
        orig = os.path.join(d, "original." + m["original_format"])
        try:
            text = ex.extract(m, orig)
        except ValueError as e:
            yield row(m, "uncovered", str(e)); continue
        except Exception as e:
            yield row(m, "error", f"{type(e).__name__}: {e}"); continue
        h = "sha256:" + hashlib.sha256(normalize_text_bytes(text)).hexdigest()
        ok = h == m.get("text_sha256")
        pre = m["corpus_id"] in getattr(ex, "PREMODULE", ())
        yield row(m, "reproduced" if ok else ("excluded" if pre else "mismatch"),
                  "" if ok else ("PREMODULE — declared content-equivalent" if pre else ""), h)


def adapt_neo(corpus, ex):
    rec = json.load(open(ex.RECIPES, encoding="utf-8"))
    known, secondary = rec["records"], rec["secondary_source"]
    for mp, m in metas(corpus):
        why = _no_text(m)
        if why:
            yield row(m, "excluded", why); continue
        keyk = f"{m['corpus_id']}||{str(m['version_id'])}"
        d = os.path.dirname(mp)
        if keyk in known:
            r = known[keyk]
            try:
                h = ex._sha(ex.METHODS[r["method"]](d, r))
            except Exception as e:
                yield row(m, "error", f"{type(e).__name__}: {e}"); continue
            yield row(m, "reproduced" if h == m.get("text_sha256") else "mismatch",
                      f"method={r['method']}", h)
        elif keyk in secondary:
            yield row(m, "excluded", "secondary_source — not re-derivable from the stored anchor")
        else:
            yield row(m, "uncovered", "no recipe in recipes.json (pending capture)")


def adapt_space(corpus, ex):
    for mp, m in metas(corpus):
        why = _no_text(m)
        if why:
            yield row(m, "excluded", why); continue
        cid, ver, d = m["corpus_id"], str(m["version_id"]), os.path.dirname(mp)
        rp = ex.rpath(cid, ver)
        if not os.path.isfile(rp):
            yield row(m, "uncovered", "no extraction/<cid>/<ver>.json recipe"); continue
        r = json.load(open(rp, encoding="utf-8"))
        try:
            text = open(os.path.join(d, "text.txt"), encoding="utf-8").read()
            got = ex.do_slice(ex.run_extractor(ex.orig_path(d), r["extractor"]), r.get("slice"))
            pct = ex.overlap(got, text, r["overlap_unit"])
        except Exception as e:
            yield row(m, "error", f"{type(e).__name__}: {e}"); continue
        thr = r.get("threshold", 97.0)
        stored_ok = (hashlib.sha256(open(os.path.join(d, "text.txt"), "rb").read()).hexdigest()
                     == str(m.get("text_sha256", ""))[7:])
        yield row(m, "reproduced" if pct >= thr else "mismatch",
                  f"overlap {pct:.2f}% >= {thr}" if pct >= thr else f"overlap {pct:.2f}% < {thr}",
                  None, {"overlap_pct": round(pct, 4), "threshold": thr,
                         "stored_hash_intact": stored_ok})


def adapt_bbnj(corpus, ex):
    from hashing import sha256_bytes, normalize_text_bytes
    recipes = {rel: (extractor, fn) for rel, extractor, fn in ex.RECIPES}
    ocr = set(getattr(ex, "OCR_RECORDS", ()))
    for mp, m in metas(corpus):
        why = _no_text(m)
        if why:
            yield row(m, "excluded", why); continue
        d = os.path.dirname(mp)
        rel = os.path.relpath(d, os.path.join(corpus, "authoritative")).replace(os.sep, "/")
        if rel in ocr:
            yield row(m, "excluded", "OCR pipeline — declared, checked separately"); continue
        if rel not in recipes:
            yield row(m, "uncovered", "not in the hardcoded RECIPES list"); continue
        extractor, fn = recipes[rel]
        try:
            raw = ex.pdftotext_raw(os.path.join(d, m["original_filename"])) \
                if extractor == "pdftotext" else ex.pymupdf_text(os.path.join(d, m["original_filename"]))
            h = sha256_bytes(normalize_text_bytes(fn(raw)))
        except Exception as e:
            yield row(m, "error", f"{type(e).__name__}: {e}"); continue
        yield row(m, "reproduced" if h == m.get("text_sha256") else "mismatch",
                  f"extractor={extractor}", h)


ADAPTERS = {"deep": adapt_deep, "origin": adapt_origin, "neo": adapt_neo,
            "space": adapt_space, "bbnj": adapt_bbnj}


# ---- policy + gate --------------------------------------------------------------------------
def load_policy(corpus):
    """Per-corpus policy, REQUIRED. There is no implicit default: a gate that guesses its own
    exclusions is a gate that can be silently wrong. Fields:
        adapter             one of ADAPTERS
        uncovered_ceiling   max records allowed with verdict 'uncovered' (the ratchet). New
                            uncovered records push the count over it and fail; it can only be
                            lowered by hand as recipes are captured.
        declared_exclusions {corpus_id||version_id: reason} — records that are permanently NOT
                            reproducible for a written reason the extractor itself cannot know
                            (e.g. text recovered by a network OCR service). These move
                            uncovered -> excluded.
    """
    p = os.path.join(corpus, "scripts", "repro-policy.json")
    if not os.path.isfile(p):
        raise SystemExit(f"ERROR: no scripts/repro-policy.json in {corpus}. Every corpus must "
                         f"declare its adapter and its reproducibility ratchet explicitly.")
    pol = json.load(open(p, encoding="utf-8"))
    if pol.get("adapter") not in ADAPTERS:
        raise SystemExit(f"ERROR: policy adapter {pol.get('adapter')!r} is not one of "
                         f"{sorted(ADAPTERS)}.")
    pol.setdefault("uncovered_ceiling", 0)
    pol.setdefault("declared_exclusions", {})
    return pol


def collect(corpus, pol):
    adapter = ADAPTERS[pol["adapter"]]
    excl = pol["declared_exclusions"]
    rows = []
    for r in adapter(corpus, __import__("extract")):
        if r["verdict"] == "uncovered":
            k = f"{r['corpus_id']}||{r['version_id']}"
            if k in excl:
                r = dict(r, verdict="excluded", detail="declared: " + excl[k])
        rows.append(r)
    on_disk = sum(1 for _ in metas(corpus))
    if len(rows) != on_disk:
        raise SystemExit(f"ERROR: gate produced {len(rows)} verdicts for {on_disk} records on "
                         f"disk. Refusing to gate on an incomplete sweep.")
    return rows


def gate(rows, pol):
    from collections import Counter
    c = Counter(r["verdict"] for r in rows)
    ceiling = pol["uncovered_ceiling"]
    reasons = []
    if c["mismatch"]:
        reasons.append(f"{c['mismatch']} MISMATCH — a recipe exists but the text did not re-derive")
    if c["error"]:
        reasons.append(f"{c['error']} ERROR — the extractor raised; the record was not checked")
    if c["uncovered"] > ceiling:
        reasons.append(f"{c['uncovered']} uncovered > ceiling {ceiling} — an unproven record was "
                       f"added; capture its recipe or declare it excluded")
    return c, reasons


def print_report(rows, c, pol):
    n = len(rows)
    print(f"# Reproducibility gate — adapter '{pol['adapter']}', {n} records")
    print(f"  reproduced {c['reproduced']} · mismatch {c['mismatch']} · uncovered "
          f"{c['uncovered']} (ceiling {pol['uncovered_ceiling']}) · excluded {c['excluded']} · "
          f"error {c['error']}\n")
    for v in ("mismatch", "error", "uncovered"):
        show = [r for r in rows if r["verdict"] == v]
        for r in show:
            print(f"  {v:10} {r['corpus_id']}/{r['version_id']}  {r['detail'][:64]}")
    if c["uncovered"] < pol["uncovered_ceiling"]:
        print(f"\n  note: uncovered ({c['uncovered']}) is below the ceiling "
              f"({pol['uncovered_ceiling']}) — a recipe was captured. Lower the ceiling to "
              f"{c['uncovered']} in repro-policy.json to keep the ratchet tight.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.dirname(HERE),
                    help="corpus repo root (default: the repo this script lives in)")
    ap.add_argument("--emit-json", action="store_true", help="per-record verdicts as JSON")
    ap.add_argument("--propose", action="store_true",
                    help="print the current uncovered count and exit (for setting a ceiling)")
    a = ap.parse_args()
    corpus = os.path.abspath(a.corpus)
    sys.path.insert(0, os.path.join(corpus, "scripts"))

    pol = load_policy(corpus)
    rows = collect(corpus, pol)

    if a.emit_json:
        json.dump({"adapter": pol["adapter"], "records": len(rows), "rows": rows},
                  sys.stdout, indent=1)
        return 0

    c, reasons = gate(rows, pol)
    if a.propose:
        print(f"uncovered = {c['uncovered']}  (current ceiling {pol['uncovered_ceiling']})")
        return 0

    print_report(rows, c, pol)
    if reasons:
        print("\nRESULT: FAILED")
        for r in reasons:
            print("  - " + r)
        return 1
    print(f"\nRESULT: OK — {c['reproduced']} reproduced, {c['excluded']} excluded with reason, "
          f"{c['uncovered']} uncovered within the ratchet. Nothing unaccounted for.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

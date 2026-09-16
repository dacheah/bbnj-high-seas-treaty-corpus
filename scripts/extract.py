#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract.py — reproducibility gate. For each authoritative record, re-derive text.txt from its
stored original.pdf by committed code (extractor + pipelines.py) and compare the SHA-256 to the
recorded text_sha256. Prints an "X/Y reproduced byte-exact" summary. Exit 0 iff every checked
record reproduces. OCR-derived records (zh/ar) use a rendered-image OCR pipeline and are reported
separately, not as text-layer failures.

Usage:
    python3 scripts/extract.py            # check all text-layer records, print X/Y reproduced
    python3 scripts/extract.py --attest   # write/refresh per-record toolchain attestations

The workflow pin says which toolchain runs NOW; the attestations under extraction/ record which
toolchain actually re-derived each record. See the ATTEST comment below for why those differ.
"""
import os, re, sys, json, subprocess, tempfile, glob
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipelines
from hashing import sha256_bytes, normalize_text_bytes
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def poppler_version():
    """The pdftotext version — part of the reproducibility claim, so never assume it.
    A newer Poppler extracts different bytes, so this string is recorded per record."""
    try:
        out = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True).stderr or ""
    except FileNotFoundError:
        return "not installed"
    m = re.search(r"version\s+([0-9][0-9.]*)", out)
    return m.group(1) if m else "unknown"

def pymupdf_version():
    """The PyMuPDF version. One record (UNCLOS 1982) is derived with it rather than pdftotext, so its
    toolchain is a Python package version, not a system binary — pinned in scripts/requirements.txt."""
    for mod in ("pymupdf", "fitz"):
        try:
            m = __import__(mod)
        except Exception:
            continue
        for attr in ("__version__", "VersionBind"):
            v = getattr(m, attr, None)
            if v:
                return str(v)
    return "unknown"

def pdftotext_raw(pdf):
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as t: tmp=t.name
    subprocess.run(["pdftotext","-raw","-enc","UTF-8",pdf,tmp], check=True)
    s=open(tmp,encoding="utf-8").read(); os.unlink(tmp); return s

def pymupdf_text(pdf):
    import fitz
    d=fitz.open(pdf); return "\n".join(d[p].get_text("text") for p in range(len(d)))

# recipe: corpus_id/version -> (extractor, pipeline_call)
RECIPES = [
 ("un/unclos-1982/1982-12-10", "pymupdf",  lambda r: pipelines.clean_unclos(r)),
 ("un/bbnj-agreement-2023/2023-06-19", "pdftotext", lambda r: pipelines.clean_english(r)),
 ("un/bbnj-agreement-2023-es/2023-06-19", "pdftotext", lambda r: pipelines.clean_lang("es", r)),
 ("un/bbnj-agreement-2023-fr/2023-06-19", "pdftotext", lambda r: pipelines.clean_lang("fr", r)),
 ("un/bbnj-agreement-2023-ru/2023-06-19", "pdftotext", lambda r: pipelines.clean_lang("ru", r)),
 ("un/ga-resolution/A-RES-77-321/2023-08-01", "pdftotext", lambda r: pipelines.clean_un(r, "A/RES/77/321")),
 ("un/ga-resolution/A-RES-78-272/2024-04-24", "pdftotext", lambda r: pipelines.clean_un(r, "A/RES/78/272")),
 ("un/ga-resolution/A-RES-79-271/2025-03-04", "pdftotext", lambda r: pipelines.clean_un(r, "A/RES/79/271")),
 ("un/ga-resolution/A-RES-80-107/2025-12-09", "pdftotext", lambda r: pipelines.clean_un(r, "A/RES/80/107")),
 ("un/ga-decision/78-560/2024-08-13", "pdftotext", lambda r: pipelines.clean_un(r, "A/78/L.102")),
 ("un/agreement-partxi-1994/1994-07-28", "pdftotext", lambda r: pipelines.clean_ia(r, "A/RES/48/263", "The General Assembly,")),
 ("un/fish-stocks-agreement-1995/1995-08-04", "pdftotext", lambda r: pipelines.clean_ia(r, "A/CONF.164/37", "AGREEMENT FOR THE IMPLEMENTATION")),
 ("un/prepcom/report-2026-3/2026-04-02", "pdftotext", lambda r: pipelines.clean_report(r)),
 ("un/prepcom/report-2026-3/2026-05-04", "pdftotext", lambda r: pipelines.clean_report(r, "A/AC.296/2026/9")),
]
OCR_RECORDS = ["un/bbnj-agreement-2023-zh/2023-06-19", "un/bbnj-agreement-2023-ar/2023-06-19"]

# ---- per-record toolchain attestation (issue #7, option (e)) ---------------------------------
# The reproducibility claim is per record and HISTORICAL: THIS dated text re-derives from THAT
# original, under THAT toolchain. A workflow-level pin states only the present — the runner image
# in use right now — so moving it silently restates the claim for every record at once, and nothing
# anywhere records which toolchain a given record was actually proven under. Each record therefore
# carries its own attestation, in the same file convention space law and deep-seabed use:
#
#     extraction/<corpus_id>/<version_id>.json   ->   extractor: {tool, args, toolchain}
#
# AN ATTESTATION IS WRITTEN ONLY WHERE THE TEXT RE-DERIVED, HASH FOR HASH, IN THE SAME RUN.
# Attesting a text that does not reproduce would be a false provenance claim, so the two OCR
# records get no file — committed deterministic code cannot re-derive an OCR text — and that
# absence is the honest record, reported by --attest and by the CI assertion.
ATTEST = os.path.join(REPO, "extraction")

def _split_rel(rel):
    """'un/bbnj-agreement-2023-es/2023-06-19' -> ('un/bbnj-agreement-2023-es', '2023-06-19')."""
    cid, _, ver = rel.rpartition("/")
    return cid, ver

def extractor_identity(extractor):
    """What actually produced the text — the toolchain that has to hold for reproduction."""
    if extractor == "pdftotext":
        return {"tool": "pdftotext", "args": ["-raw", "-enc", "UTF-8"],
                "toolchain": f"poppler {poppler_version()}"}
    if extractor == "pymupdf":
        return {"tool": "pymupdf", "args": [], "toolchain": f"pymupdf {pymupdf_version()}"}
    return {"tool": extractor, "args": [], "toolchain": None}

def attestation_for(rel, extractor, got):
    cid, ver = _split_rel(rel)
    return {
        "corpus_id": cid,
        "version_id": ver,
        "extractor": extractor_identity(extractor),
        "text_sha256": got,
        "note": ("Toolchain under which this record's text.txt re-derives, proven by scripts/extract.py. "
                 "Written only where the text reproduced hash-for-hash in the same run, and the hash "
                 "beside it is the one that re-derivation produced. The byte-exact original.* and its "
                 "recorded sha256 remain the authoritative anchor; this attests the DERIVATION, not "
                 "the source."),
    }

def write_attestation(rec):
    """Write only if it would actually change.

    A rebuild must not churn these: an attestation whose toolchain and text hash are unchanged is
    left exactly as it is. Deliberately no generated-on date — that would make every run dirty for
    no gain, which is what once left this portfolio's derived layer permanently modified.
    """
    p = os.path.join(ATTEST, rec["corpus_id"], f"{rec['version_id']}.json")
    if os.path.isfile(p):
        try:
            if json.load(open(p, encoding="utf-8")) == rec:
                return False
        except Exception:
            pass
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return True

def main(attest=False):
    ok=fail=0; rows=[]; att_new=[]; att_same=[]; att_skip=[]
    for rel, extractor, fn in RECIPES:
        vd=os.path.join(REPO,"authoritative",rel)
        meta=yaml.safe_load(open(os.path.join(vd,"metadata.yaml"),encoding="utf-8"))
        pdf=os.path.join(vd, meta["original_filename"])
        raw = pdftotext_raw(pdf) if extractor=="pdftotext" else pymupdf_text(pdf)
        got = sha256_bytes(normalize_text_bytes(fn(raw)))
        match = (got == meta["text_sha256"])
        rows.append((rel.split("/")[-2] if "/" in rel else rel, extractor, "OK" if match else "MISMATCH"))
        ok += match; fail += (not match)
        if not match:
            rows[-1]=(rows[-1][0], extractor, f"MISMATCH stored={meta['text_sha256'][7:19]} got={got[7:19]}")
        if attest:
            if match:
                (att_new if write_attestation(attestation_for(rel, extractor, got)) else att_same).append(rel)
            else:
                att_skip.append(rel)
    for name,ex,st in rows:
        print(f"  {name:28} {ex:10} {st}")
    total=ok+fail
    print(f"\nREPRODUCED BYTE-EXACT: {ok}/{total} text-layer records")
    print(f"OCR records (separate pipeline, not checked here): {', '.join(r.split('/')[-2] for r in OCR_RECORDS)}")
    if attest:
        print(f"\nATTESTATIONS: written {len(att_new)}, already correct {len(att_same)}")
        print(f"NOT attested: {len(att_skip)} record(s) that did not reproduce in this run, "
              f"{len(OCR_RECORDS)} OCR record(s) with no text-layer recipe")
        if att_skip:
            print("  did NOT reproduce, so NOT attested: " + ", ".join(att_skip))
        print("  no attestation, OCR pipeline (not text-layer reproducible): " + ", ".join(OCR_RECORDS))
    return 0 if fail==0 else 1

if __name__=="__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Reproducibility gate + per-record toolchain attestation.")
    ap.add_argument("--attest", action="store_true",
                    help="write/refresh per-record toolchain attestations under extraction/")
    _a = ap.parse_args()
    sys.exit(main(attest=_a.attest))

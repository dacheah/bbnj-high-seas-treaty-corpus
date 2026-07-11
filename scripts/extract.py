#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract.py — reproducibility gate. For each authoritative record, re-derive text.txt from its
stored original.pdf by committed code (extractor + pipelines.py) and compare the SHA-256 to the
recorded text_sha256. Prints an "X/Y reproduced byte-exact" summary. Exit 0 iff every checked
record reproduces. OCR-derived records (zh/ar) use a rendered-image OCR pipeline and are reported
separately, not as text-layer failures.
"""
import os, sys, subprocess, tempfile, glob
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipelines
from hashing import sha256_bytes, normalize_text_bytes
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
]
OCR_RECORDS = ["un/bbnj-agreement-2023-zh/2023-06-19", "un/bbnj-agreement-2023-ar/2023-06-19"]

def main():
    ok=fail=0; rows=[]
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
    for name,ex,st in rows:
        print(f"  {name:28} {ex:10} {st}")
    total=ok+fail
    print(f"\nREPRODUCED BYTE-EXACT: {ok}/{total} text-layer records")
    print(f"OCR records (separate pipeline, not checked here): {', '.join(r.split('/')[-2] for r in OCR_RECORDS)}")
    return 0 if fail==0 else 1

if __name__=="__main__":
    sys.exit(main())

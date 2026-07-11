#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reconcile_ar.py -- reconcile the Arabic PRIMARY (stored EasyOCR text) against a SECOND, independent
OCR at WORD level (Arabic has word spaces, so word-level is fast and appropriate). Reports the
word-agreement rate and writes every disagreement -- primary words, secondary words, page number --
to capture/reconcile-ar-report.txt for adjudication against the page image.

Usage:  python capture/reconcile_ar.py [secondary_file]
        default secondary = capture/ar-gvision.txt  (Google Vision);  pass capture/ar-tesseract.txt to compare.
"""
import os, sys, unicodedata, difflib
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
PRIMARY = os.path.join(REPO, "authoritative/un/bbnj-agreement-2023-ar/2023-06-19/text.txt")
SECOND  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "capture/ar-gvision.txt")

HARAKAT = set(chr(c) for c in range(0x064B, 0x0653)) | {"ٰ", "ـ"}   # diacritics, superscript alef, tatweel
BIDI    = set("‎‏‪‫‬‭‮⁦⁧⁨⁩﻿")
FOLD    = str.maketrans("أإآٱىة", "اااايه")   # alef variants -> alef; alef-maqsura -> ya; ta-marbuta -> ha (matching only)
def norm(s):
    s = unicodedata.normalize("NFKC", s)
    s = "".join(c for c in s if c not in HARAKAT and c not in BIDI)
    return s.translate(FOLD)

def load_words(path, paged):
    if paged:
        words, pageof = [], []
        for pi, pg in enumerate(open(path, encoding="utf-8").read().split("\f"), 1):
            for w in norm(pg).split(): words.append(w); pageof.append(pi)
        return words, pageof
    return norm(open(path, encoding="utf-8").read()).split(), None

def main():
    if not os.path.exists(SECOND):
        print(f"[ar] waiting for second OCR at {os.path.relpath(SECOND, REPO)} "
              f"(run capture/ocr_cloud_gvision.py on a machine with internet + an API key)."); return 2
    prim, _ = load_words(PRIMARY, paged=False)
    sec, pageof = load_words(SECOND, paged=True)
    sm = difflib.SequenceMatcher(None, prim, sec, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    den = max(len(prim), len(sec), 1)
    print(f"[ar] primary words: {len(prim)}  secondary words: {len(sec)}")
    print(f"[ar] WORD agreement (2 independent engines): {100*matched/den:.2f}%  ({matched} matched)")
    diffs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal": continue
        pg = pageof[min(j1, len(pageof)-1)] if pageof else "?"
        diffs.append((pg, tag, " ".join(prim[i1:i2]), " ".join(sec[j1:j2])))
    pages = sorted({d[0] for d in diffs})
    print(f"[ar] disagreement regions: {len(diffs)}  spanning {len(pages)} page(s)")
    out = os.path.join(REPO, "capture/reconcile-ar-report.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# Arabic reconciliation: primary(EasyOCR) vs {os.path.basename(SECOND)}\n")
        f.write(f"# word-agreement={100*matched/den:.2f}%  regions={len(diffs)}  pages={pages}\n\n")
        for pg, tag, a, b in diffs:
            f.write(f"[p{pg}] {tag}\n    primary  : {a}\n    secondary: {b}\n")
    print(f"[ar] wrote {os.path.relpath(out, REPO)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

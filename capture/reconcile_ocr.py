#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reconcile_ocr.py -- reconcile the PRIMARY OCR (stored authoritative text) against the
SECOND, INDEPENDENT Tesseract OCR (capture/{zh,ar}-tesseract.txt), character by character.

For each language it reports the character-agreement rate and writes every disagreement
region -- with the primary text, the secondary text, and the page number it sits on -- to
capture/reconcile-<lang>-report.txt, so each disagreement can be adjudicated against that
page's rendered image. Where the two independent engines AGREE, the character is corroborated.

Usage:  python capture/reconcile_ocr.py zh
        python capture/reconcile_ocr.py ar
"""
import os, sys, unicodedata, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

LANGS = {
    "zh": dict(text="authoritative/un/bbnj-agreement-2023-zh/2023-06-19/text.txt",
               tess="capture/zh-tesseract.txt"),
    "ar": dict(text="authoritative/un/bbnj-agreement-2023-ar/2023-06-19/text.txt",
               tess="capture/ar-tesseract.txt"),
}
# characters to drop before comparison: whitespace, tatweel, bidi/zero-width marks
_DROP = set("ـ​‌‍‎‏‪‫‬‭‮﻿")

def normalize(s):
    s = unicodedata.normalize("NFKC", s)
    return "".join(c for c in s if not c.isspace() and c not in _DROP)

def load_secondary(path):
    raw = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    chars, pageof = [], []
    for pi, pg in enumerate(raw.split("\f"), start=1):
        for c in normalize(pg):
            chars.append(c); pageof.append(pi)
    return "".join(chars), pageof

def main(lang):
    cfg = LANGS[lang]
    tpath = os.path.join(REPO, cfg["tess"])
    if not os.path.exists(tpath):
        print(f"[{lang}] waiting for second-OCR output at {cfg['tess']} "
              f"(run capture/ocr_second_tesseract.py on a machine with the Tesseract language data).")
        return 2
    primary = normalize(open(os.path.join(REPO, cfg["text"]), encoding="utf-8").read())
    secondary, pageof = load_secondary(tpath)
    sm = difflib.SequenceMatcher(None, primary, secondary, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    denom = max(len(primary), len(secondary), 1)
    print(f"[{lang}] primary chars: {len(primary)}  secondary chars: {len(secondary)}")
    print(f"[{lang}] character agreement (2 independent engines): {100*matched/denom:.2f}%  "
          f"({matched} matched)")
    diffs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        pg = pageof[min(j1, len(pageof)-1)] if pageof else "?"
        diffs.append((pg, tag, primary[i1:i2], secondary[j1:j2]))
    pages = sorted({d[0] for d in diffs})
    print(f"[{lang}] disagreement regions: {len(diffs)}  spanning {len(pages)} page(s): {pages}")
    out = os.path.join(REPO, f"capture/reconcile-{lang}-report.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# Reconciliation report: {lang}  (primary stored OCR  vs  Tesseract second OCR)\n")
        f.write(f"# agreement={100*matched/denom:.2f}%  regions={len(diffs)}  pages={pages}\n")
        f.write("# Each row: [page] TAG  primary=<...>  tesseract=<...>  -- adjudicate against the page render.\n\n")
        for pg, tag, a, b in diffs:
            f.write(f"[p{pg}] {tag}\n    primary  : {a!r}\n    tesseract: {b!r}\n")
    print(f"[{lang}] wrote {out}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in LANGS:
        sys.exit("usage: reconcile_ocr.py {zh|ar}")
    sys.exit(main(sys.argv[1]))

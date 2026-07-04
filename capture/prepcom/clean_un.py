# -*- coding: utf-8 -*-
"""clean_un.py <infile> <outfile> <symbol> -- normalise a UN resolution/decision -raw extraction.
Strips repeated page-boundary running headers/footers, doc-number and page-number lines, and the
barcode; light reflow (break before numbered operative paragraphs). Wording preserved."""
import re, sys, pathlib
infile, outfile, symbol = sys.argv[1], sys.argv[2], sys.argv[3]
lines = [l.rstrip() for l in pathlib.Path(infile).read_text(encoding="utf-8").replace("\r\n","\n").split("\n")]

sym_re   = re.compile(r"^" + re.escape(symbol) + r"\*?$")   # running-header symbol line
page_re  = re.compile(r"^\d+/\d+$")                          # page number  e.g. 2/4
docno_re = re.compile(r"^\d{2}-\d{5}\*?( \(E\).*)?$")        # UN doc number e.g. 24-07683
bar_re   = re.compile(r"^\*\d{7}\*$")                        # barcode *2407683*
stamp_re = re.compile(r"^\d{2}/\d{2}/\d{2}$")                # date stamp 04/05/26

out, i = [], 0
while i < len(lines):
    l = lines[i]
    if sym_re.match(l):                       # drop running-header block: symbol .. page-number
        j = i + 1
        while j < len(lines) and not page_re.match(lines[j]):
            j += 1
        i = j + 1
        continue
    if page_re.match(l) or docno_re.match(l) or bar_re.match(l) or stamp_re.match(l):
        i += 1; continue
    out.append(l); i += 1

# reflow: join wrapped lines; new paragraph before numbered operative paragraphs / footnote refs
brk = re.compile(r"^(\d+\.\s|The General Assembly\b|Resolution adopted|Decision |[A-Z][a-z]+ decision\b|\d+/\d+\.\s|\*+ )")
paras, cur = [], ""
for l in out:
    if not l.strip():
        continue
    if brk.match(l):
        if cur: paras.append(cur.strip())
        cur = l
    else:
        cur = (cur + " " + l).strip()
if cur: paras.append(cur.strip())
text = "\n\n".join(re.sub(r"[ \t]{2,}", " ", p) for p in paras) + "\n"
pathlib.Path(outfile).write_text(text, encoding="utf-8")
print(f"{symbol}: paras={len(paras)} chars={len(text)}")

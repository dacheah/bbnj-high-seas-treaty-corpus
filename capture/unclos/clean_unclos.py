# -*- coding: utf-8 -*-
"""clean_unclos.py -- normalise the UNCLOS -raw extraction into text-unclos.full.txt.
Drops the table of contents, dot-leader lines and page numbers; reflows on
PART/SECTION/SUBSECTION/Article/ANNEX headers. Wording preserved (pdftotext -raw;
extracted_unverified — some space-drop artifacts from the source PDF remain)."""
import re, pathlib
raw = pathlib.Path("raw-unclos.txt").read_text(encoding="utf-8").replace("\r\n","\n")
lines = [l.rstrip() for l in raw.split("\n")]

TITLE = "United Nations Convention on the Law of the Sea"
# body begins at the real PREAMBLE (the TOC entry is 'PREAMBLE . . . 21', not a bare line)
start = next(i for i,l in enumerate(lines) if l.strip()=="PREAMBLE")
lines = [TITLE, ""] + lines[start:]

dotleader = re.compile(r"(\.\s){4,}|\.{4,}")   # TOC dot leaders
pagenum   = re.compile(r"^\d{1,3}$")
clean = []
for l in lines:
    s = l.strip()
    if not s: continue
    if dotleader.search(l): continue
    if pagenum.match(s): continue
    clean.append(s)

head = re.compile(r"^(PART\s+[IVXL]+|SECTION\s+\d+|SUB-?SECTION\s+[A-Z0-9]+|Article\s+\d+\b|ANNEX\s+[IVX]+|PREAMBLE)\b")
enum = re.compile(r"^(\d+\.\s|\([a-z0-9]{1,4}\)\s|\([ivx]{1,5}\)\s)")
paras, cur = [], ""
for l in clean:
    if head.match(l) or enum.match(l):
        if cur: paras.append(cur.strip())
        cur = l
    else:
        cur = (cur + " " + l).strip()
if cur: paras.append(cur.strip())

text = "\n\n".join(re.sub(r"[ \t]{2,}"," ",p) for p in paras) + "\n"
pathlib.Path("text-unclos.full.txt").write_text(text, encoding="utf-8")
arts = sorted(set(int(m.group(1)) for m in re.finditer(r"(?m)^Article (\d+)\b", text)))
print("chars:", len(text), "| paras:", len(paras))
print("PARTs:", len(re.findall(r"(?m)^PART [IVXL]+", text)),
      "| ANNEXes:", len(re.findall(r"(?m)^ANNEX [IVX]+", text)),
      "| distinct articles:", len(arts), "| range:", (arts[0], arts[-1]) if arts else None)
missing = [n for n in range(1, arts[-1]+1) if n not in arts] if arts else []
print("missing article numbers:", missing[:20], "..." if len(missing)>20 else "")

# -*- coding: utf-8 -*-
"""Re-derive UNCLOS text from the PyMuPDF extraction (fitz-unclos.txt), which preserves the
inter-word spaces that pdftotext -raw dropped. Same normalisation as clean_unclos.py."""
import re, pathlib
raw=pathlib.Path("fitz-unclos.txt").read_text(encoding="utf-8").replace("\r\n","\n")
lines=[l.rstrip() for l in raw.split("\n")]
TITLE="United Nations Convention on the Law of the Sea"
start=next(i for i,l in enumerate(lines) if l.strip()=="PREAMBLE")
lines=[TITLE,""]+lines[start:]
dot=re.compile(r"(\.\s){4,}|\.{4,}"); pg=re.compile(r"^\d{1,3}$")
clean=[l.strip() for l in lines if l.strip() and not dot.search(l) and not pg.match(l.strip())]
head=re.compile(r"^(PART\s+[IVXL]+|SECTION\s+\d+|SUB-?SECTION\s+[A-Z0-9]+|Article\s+\d+\b|ANNEX\s+[IVX]+|PREAMBLE)\b")
enum=re.compile(r"^(\d+\.\s|\([a-z0-9]{1,4}\)\s|\([ivx]{1,5}\)\s)")
paras,cur=[],""
for l in clean:
    if head.match(l) or enum.match(l):
        if cur: paras.append(cur.strip())
        cur=l
    else:
        cur=(cur+" "+l).strip()
if cur: paras.append(cur.strip())
text="\n\n".join(re.sub(r"[ \t]{2,}"," ",p) for p in paras)+"\n"
pathlib.Path("text-unclos.fitz.txt").write_text(text,encoding="utf-8")
arts=sorted(set(int(m.group(1)) for m in re.finditer(r"(?m)^Article (\d+)\b",text)))
print("chars:",len(text),"| articles:",len(arts),"range",(arts[0],arts[-1]),"missing",[n for n in range(1,arts[-1]+1) if n not in arts][:10])
print("PARTs:",len(re.findall(r"(?m)^PART ",text)),"ANNEXes:",len(re.findall(r"(?m)^ANNEX ",text)))
for m in ["newregime","ofthe","conformitywith","Authorityand","tomakethe","PreparatoryCommission"]:
    n=text.count(m)
    if n: print("  RESIDUAL MERGE:",m,n)
print("space-drop merges remaining: check above (none printed = clean)")

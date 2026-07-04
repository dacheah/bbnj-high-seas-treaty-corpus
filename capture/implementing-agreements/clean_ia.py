# -*- coding: utf-8 -*-
"""clean_ia.py <infile> <outfile> <symbol> <start_regex> -- normalise an ODS -raw extraction of a
UN implementing agreement. Strips running headers/footers/page numbers; reflows on
PART/Article/Section/ANNEX/numbered headers. Wording preserved (extracted_unverified)."""
import re, sys, pathlib
infile, outfile, symbol, startre = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
lines=[l.rstrip() for l in pathlib.Path(infile).read_text(encoding="utf-8").replace("\r\n","\n").split("\n")]
# begin at the start marker
si=next((i for i,l in enumerate(lines) if re.search(startre,l)), 0)
lines=lines[si:]
sym=re.compile(r"^"+re.escape(symbol)+r"$")
noise=re.compile(r"^(\d{1,3}|\d{2}-\d{5}\*?|\*\d{6,7}\*|\d{1,3}/\d{1,3})$")
clean=[l for l in lines if l.strip() and not sym.match(l.strip()) and not noise.match(l.strip())]
head=re.compile(r"^(PART\s+[IVXL]+|Article\s+\d+\b|Section\s+\d+\b|ANNEX(\s+[IVX]+)?|PREAMBLE)\b")
enum=re.compile(r"^(\d+\.\s|\([a-z0-9]{1,4}\)\s)")
paras,cur=[],""
for l in clean:
    if head.match(l) or enum.match(l):
        if cur: paras.append(cur.strip())
        cur=l
    else:
        cur=(cur+" "+l).strip()
if cur: paras.append(cur.strip())
text="\n\n".join(re.sub(r"[ \t]{2,}"," ",p) for p in paras)+"\n"
pathlib.Path(outfile).write_text(text,encoding="utf-8")
arts=sorted(set(int(m.group(1)) for m in re.finditer(r"(?m)^Article (\d+)\b",text)))
print(f"{symbol}: chars={len(text)} paras={len(paras)} arts={len(arts)} range={(arts[0],arts[-1]) if arts else None} "
      f"PARTs={len(re.findall(r'(?m)^PART ',text))} ANNEX={len(re.findall(r'(?m)^ANNEX',text))}")

# -*- coding: utf-8 -*-
"""Re-clean the PrepCom Report from pdftotext -raw. Removes ONLY true noise (ADVANCE banner, date
stamps, page markers N and N/80, barcodes, doc numbers). Keeps in-text document symbols
(A/AC.296/...), which are content. Reflows on section/numbered/annex headers."""
import re, pathlib
raw=pathlib.Path("raw-prepcom-report-full.txt").read_text(encoding="utf-8").replace("\r\n","\n")
lines=[l.rstrip() for l in raw.split("\n")]
keep=[]
for l in lines:
    s=l.strip()
    if s=="ADVANCE, UNEDITED VERSION": continue
    if re.match(r"^\d{2}/\d{2}/\d{2}$", s): continue          # 04/05/26
    if re.match(r"^\*\d{6,7}\*$", s): continue                # barcode
    if re.match(r"^\d{1,3}$", s): continue                    # bare page number
    if re.match(r"^\d{1,3}/\d{1,3}$", s): continue            # page marker N/80
    if re.match(r"^(25|26)-\d{5}", s): continue               # doc number
    keep.append(l)
brk=re.compile(r"^(\d+\.\s|[IVXL]+\.\s+[A-Z]|Annex\b|Appendix\b)")
paras,cur=[],""
for l in keep:
    if not l.strip(): continue
    if brk.match(l.strip()):
        if cur: paras.append(cur.strip())
        cur=l.strip()
    else:
        cur=(cur+" "+l.strip()).strip()
if cur: paras.append(cur.strip())
text="\n\n".join(re.sub(r"[ \t]{2,}"," ",p) for p in paras)+"\n"
pathlib.Path("text-prepcom-report.txt").write_text(text,encoding="utf-8")
print("chars:",len(text),"| A/AC.296 refs kept:", len(re.findall(r"A/AC\.296/", text)))

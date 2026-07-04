# -*- coding: utf-8 -*-
"""Assemble + normalise the Chinese OCR (rapidocr) into text-zh.full.txt. OCR => ocr_unverified."""
import re, pathlib
raw = pathlib.Path("zh-ocr-raw.txt").read_text(encoding="utf-8")
lines = [l.strip() for l in raw.split("\n")]
# begin at 序言 (preamble); prepend the clean official title
TITLE = "《联合国海洋法公约》下国家管辖范围以外区域海洋生物多样性的养护和可持续利用协定"
pre = next(i for i,l in enumerate(lines) if l == "序言")
lines = [TITLE, "", "序言"] + lines[pre+1:]
# drop page-number lines: -N- / - N - variants (ascii digits) and bare numbers
pg = re.compile(r"^[-—\s]*\d{1,3}[-—\s]*$")
lines = [l for l in lines if l and not pg.match(l)]
# reflow: break before CJK structural markers; join others with no space
CN="一二三四五六七八九十百零〇"
brk = re.compile(r"^(第[%s]+部分|第[%s0-9]+条|附件[%s]|附件$|序言|（[%s0-9]+）|[%s]+、|\d+[.．、])" % (CN,CN,CN,CN,CN))
paras=[]; cur=""
for l in lines:
    if brk.match(l):
        if cur: paras.append(cur)
        cur=l
    else:
        cur += l
if cur: paras.append(cur)
# collapse stray spaces between CJK
text = "\n\n".join(re.sub(r"(?<=[　-鿿])\s+(?=[　-鿿])","",p) for p in paras)+"\n"
pathlib.Path("text-zh.full.txt").write_text(text, encoding="utf-8")
print("paras:", len(paras), "chars:", len(text))
print("第..部分:", len(re.findall(r"(?m)^第[%s]+部分" % CN, text)))
print("第..条 headers:", len(re.findall(r"(?m)^第[%s0-9]+条" % CN, text)))
print("附件:", re.findall(r"(?m)^附件[%s]" % CN, text))

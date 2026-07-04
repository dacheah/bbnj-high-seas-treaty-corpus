# -*- coding: utf-8 -*-
"""
clean_ar.py -- assemble + normalise Arabic OCR into capture/text-ar.full.txt (OCR => ocr_unverified).
Arabic is RTL and uses word spaces; wrapped lines are joined with a single space.
Expects one file per page at capture/pages_txt/ar-NNN.txt (see finish-arabic.md / render_ocr_ar.py).
"""
import re, glob, pathlib

# Official Arabic title (as it appears on the PDF; OCR-sourced, ocr_unverified).
TITLE = ("اتفاق مبرم في إطار اتفاقية الأمم المتحدة لقانون البحار بشأن حفظ التنوع البيولوجي البحري "
         "في المناطق الواقعة خارج حدود الولاية الوطنية واستخدامه على نحو مستدام")

parts = [pathlib.Path(f).read_text(encoding="utf-8")
         for f in sorted(glob.glob("capture/pages_txt/ar-*.txt"))]
lines = [l.strip() for l in "\n".join(parts).split("\n") if l.strip()]

# Drop the cover: begin at the first occurrence of the preamble heading الديباجة (it is inline
# because EasyOCR merges blocks), trimming anything before it, then prepend one clean title.
ANCHOR = "الديباجة"
k = next((i for i, l in enumerate(lines) if ANCHOR in l), None)
if k is not None:
    lines[k] = lines[k][lines[k].index(ANCHOR):]
    lines = [TITLE, ""] + lines[k:]
else:
    print("WARN: preamble heading not found — inspect the OCR.")

# Drop running page-number lines (Western 0-9 or Arabic-Indic ٠-٩, optional dashes).
AR = "٠١٢٣٤٥٦٧٨٩"
pg = re.compile(r"^[-—\s]*[0-9%s]{1,3}[-—\s]*$" % AR)
lines = [l for l in lines if not pg.match(l)]

# Reflow: new paragraph before a structural marker; otherwise join with a space.
brk = re.compile(r"^(الديباجة|المادة|المرفق|مرفق|الجزء|الجزع)")
paras, cur = [], ""
for l in lines:
    if brk.match(l):
        if cur: paras.append(cur.strip())
        cur = l
    else:
        cur = (cur + " " + l).strip()
if cur: paras.append(cur.strip())

text = "\n\n".join(re.sub(r"[ \t]{2,}", " ", p) for p in paras) + "\n"
pathlib.Path("capture/text-ar.full.txt").write_text(text, encoding="utf-8")
print("paras:", len(paras), "chars:", len(text))
print("المادة headers:", len(re.findall(r"(?m)^المادة", text)),
      "| المرفق:", len(re.findall(r"(?m)^(?:المرفق|مرفق)", text)),
      "| starts-with-title:", text.startswith(TITLE))

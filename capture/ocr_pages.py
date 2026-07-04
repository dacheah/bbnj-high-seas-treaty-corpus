import sys, glob, os
from rapidocr_onnxruntime import RapidOCR
lang, lo, hi = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
ocr = RapidOCR()
pdir = f"pages_{lang}"; odir = "pages_txt"
for p in sorted(glob.glob(f"{pdir}/p-*.png")):
    n = int(os.path.basename(p).split("-")[1].split(".")[0])
    if n < lo or n > hi: continue
    out = f"{odir}/{lang}-{n:03d}.txt"
    if os.path.exists(out): continue
    res, _ = ocr(p, use_cls=False)
    txt = "\n".join(r[1] for r in res) if res else ""
    open(out, "w", encoding="utf-8").write(txt)
    print(f"  {lang} p{n}: {len(txt)} chars, {len(res) if res else 0} lines")

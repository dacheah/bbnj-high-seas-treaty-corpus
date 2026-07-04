"""
clean_lang.py <lang> <infile> <outfile> -- language-aware normalisation of a -raw extraction.
Shares the English approach (drop cover, strip page numbers, join hyphen line-breaks, reflow),
with per-language headings/enumerators and per-language fixes. Wording preserved.
"""
import re, sys, pathlib

lang, infile, outfile = sys.argv[1], sys.argv[2], sys.argv[3]
raw = pathlib.Path(infile).read_text(encoding="utf-8").replace("\r\n","\n").replace("\r","\n")

if lang == "ru":
    _DIG={0x13+i:str(i) for i in range(10)}
    _PUN={0x03:" ",0x0f:",",0x10:"-",0x11:".",0x1d:":",0x1e:";",0x0c:"(",0x00A9:"«",0x00AA:"»"}
    def _dec(s):
        o=[]
        for ch in s:
            c=ord(ch)
            if 0x023A<=c<=0x0279: o.append(chr(c+0x1D6))
            elif c==0x022B: o.append("Ё")
            elif c==0x027B: o.append("ё")
            elif c in _DIG: o.append(_DIG[c])
            elif c in _PUN: o.append(_PUN[c])
            else: o.append(ch)
        return "".join(o)
    raw=_dec(raw)


CFG = {
 "es": dict(
   title=("ACUERDO EN EL MARCO DE LA CONVENCIÓN DE LAS NACIONES UNIDAS SOBRE EL DERECHO DEL MAR "
          "RELATIVO A LA CONSERVACIÓN Y EL USO SOSTENIBLE DE LA DIVERSIDAD BIOLÓGICA MARINA DE LAS "
          "ZONAS SITUADAS FUERA DE LA JURISDICCIÓN NACIONAL"),
   pre=r"^PREÁMBULO$",
   heads=["PARTE","Artículo","ANEXO","PREÁMBULO"]),
 "fr": dict(
   title=("ACCORD SE RAPPORTANT À LA CONVENTION DES NATIONS UNIES SUR LE DROIT DE LA MER ET PORTANT "
          "SUR LA CONSERVATION ET L’UTILISATION DURABLE DE LA DIVERSITÉ BIOLOGIQUE MARINE DES ZONES "
          "NE RELEVANT PAS DE LA JURIDICTION NATIONALE"),
   pre=r"^PR[ÉE]AM.?ULE$",
   heads=["PARTIE","Article","ANNEXE","PRÉAMBULE"]),
 "ru": dict(
   title=("СОГЛАШЕНИЕ НА БАЗЕ КОНВЕНЦИИ ОРГАНИЗАЦИИ ОБЪЕДИНЕННЫХ НАЦИЙ ПО МОРСКОМУ ПРАВУ О "
          "СОХРАНЕНИИ И УСТОЙЧИВОМ ИСПОЛЬЗОВАНИИ МОРСКОГО БИОЛОГИЧЕСКОГО РАЗНООБРАЗИЯ В РАЙОНАХ ЗА "
          "ПРЕДЕЛАМИ ДЕЙСТВИЯ НАЦИОНАЛЬНОЙ ЮРИСДИКЦИИ"),
   pre=r"^ПРЕАМБУЛА$",
   heads=["ЧАСТЬ","Статья","ПРИЛОЖЕНИЕ","ПРЕАМБУЛА"]),
}[lang]

# --- French: repair the garbled display-font glyphs (only in heading lines) ---
if lang == "fr":
    raw = raw.replace("ൗ"," ").replace("¶","’")   # spacing + apostrophe artifacts
FR_MAP = str.maketrans({"%":"B","*":"G","4":"Q","=":"Z","<":"Y","+":"H"})

lines = [l.strip() for l in raw.split("\n")]

# begin at preamble; prepend clean title
pre_re = re.compile(CFG["pre"])
pre = next((i for i,l in enumerate(lines) if pre_re.match(l)), None)
if pre is None:
    sys.exit(f"[{lang}] preamble anchor not found")
lines = [CFG["title"], "", CFG["heads"][3]] + lines[pre+1:]   # normalise preamble heading

# drop page-number lines
page_re = re.compile(r"^\s*-\s*\d+\s*-\s*$")
lines = [l for l in lines if not page_re.match(l)]

# join hyphen line-breaks (Latin)
merged=[]; i=0
while i < len(lines):
    l=lines[i]
    if re.search(r"[A-Za-zÀ-ÿА-Яа-яЁё]-$", l) and i+1<len(lines) and lines[i+1] and not page_re.match(lines[i+1]):
        merged.append(l+lines[i+1]); i+=2
    else:
        merged.append(l); i+=1
lines=merged

H = CFG["heads"]
head_re = re.compile(r"^(" + "|".join(re.escape(h) for h in H[:3]) +
                     r")(\s+([IVXLCDM]+|\d+[A-Za-z]*|premier|premier[eè]re))?\s*$", re.I)
prem_re = re.compile(r"^" + re.escape(H[3]) + r"$")
num_re  = re.compile(r"^\d+\.(\s+\S.*)?$")
let_re  = re.compile(r"^(\([\w]{1,4}\)|[A-Za-zÀ-ÿ]\)|[a-z]\.)(\s+\S.*)?$")
boundary=lambda l: bool(head_re.match(l) or prem_re.match(l) or num_re.match(l) or let_re.match(l))

paras=[]; cur=[]
def flush():
    global cur
    if cur: paras.append(" ".join(x.strip() for x in cur if x.strip()))
    cur=[]

i=0
while i<len(lines):
    l=lines[i]
    if not l.strip(): i+=1; continue
    if head_re.match(l):
        flush()
        title=""
        if i+1<len(lines) and lines[i+1].strip() and not boundary(lines[i+1]):
            title=lines[i+1].strip(); i+=1
        cur=[l.strip()+("\n"+title if title else "")]
        i+=1; continue
    if prem_re.match(l):
        flush(); cur=[H[3]]; i+=1; continue
    if num_re.match(l) or let_re.match(l):
        flush(); cur=[l]; i+=1; continue
    cur.append(l); i+=1
flush()

# French: reverse-map the display-font substitutions inside PART heading paragraphs only
if lang=="fr":
    fixed=[]
    for p in paras:
        if p.startswith("PARTIE") or p.startswith("ANNEXE"):
            p="\n".join(seg.translate(FR_MAP) for seg in p.split("\n"))
        fixed.append(p)
    paras=fixed

out=[re.sub(r"[ \t]{2,}"," ",p.strip()) for p in paras if p.strip()]
text="\n\n".join(out)+"\n"
pathlib.Path(outfile).write_text(text, encoding="utf-8")
nl = chr(10)
arts = len(re.findall("(?m)^"+re.escape(H[1])+r"\s+\d+", text))
nparts = len(re.findall("(?m)^"+re.escape(H[0])+r"\b", text))
nann = len(re.findall("(?m)^"+re.escape(H[2])+r"\b", text))
print("["+lang+"] paras=%d chars=%d %s#=%d %s#=%d %s#=%d" % (len(out),len(text),H[1],arts,H[0],nparts,H[2],nann))

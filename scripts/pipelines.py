# -*- coding: utf-8 -*-
"""
pipelines.py — the canonical, committed text-normalisation functions for the corpus.
Each takes the raw extraction of an original.pdf (pdftotext -raw or PyMuPDF text) and returns the
authoritative text.txt content. These are the reference implementations behind the per-document
capture/ helper scripts; extract.py drives them from each stored original.pdf to prove byte-exact
reproducibility. Layout normalisation only — wording preserved.
"""
import re

def clean_english(raw):
    raw = raw.replace("\r\n","\n").replace("\r","\n")
    lines=[l.strip() for l in raw.split("\n")]
    pre=next(i for i,l in enumerate(lines) if l.strip()=="PREAMBLE")
    TITLE=("AGREEMENT UNDER THE UNITED NATIONS CONVENTION ON THE LAW OF THE SEA ON THE "
           "CONSERVATION AND SUSTAINABLE USE OF MARINE BIOLOGICAL DIVERSITY OF AREAS BEYOND "
           "NATIONAL JURISDICTION")
    lines=[TITLE,""]+lines[pre:]
    page_re=re.compile(r"^\s*-\s*\d+\s*-\s*$")
    lines=[l for l in lines if not page_re.match(l)]
    merged=[]; i=0
    while i<len(lines):
        l=lines[i]
        if re.search(r"[A-Za-z]-$",l) and i+1<len(lines) and lines[i+1] and not page_re.match(lines[i+1]):
            merged.append(l+lines[i+1]); i+=2
        else: merged.append(l); i+=1
    lines=merged
    head_re=re.compile(r"^(PART\s+[IVXLCDM]+|Article\s+\d+[A-Za-z]?|ANNEX\s+[IVX]+|PREAMBLE)\s*$")
    num_re=re.compile(r"^\d+\.(\s+\S.*)?$")
    let_re=re.compile(r"^(\([a-z0-9]{1,4}\)|[a-z]\.)(\s+\S.*)?$")
    boundary=lambda l: bool(head_re.match(l) or num_re.match(l) or let_re.match(l))
    paras=[]; cur=[]
    def flush():
        nonlocal cur
        if cur: paras.append(" ".join(x.strip() for x in cur if x.strip()))
        cur=[]
    i=0
    while i<len(lines):
        l=lines[i]
        if not l.strip(): i+=1; continue
        m=head_re.match(l)
        if m and m.group(1)!="PREAMBLE":
            flush(); title=""
            if i+1<len(lines) and lines[i+1].strip() and not boundary(lines[i+1]):
                title=lines[i+1].strip(); i+=1
            cur=[l.strip()+("\n"+title if title else "")]; i+=1; continue
        if l.strip()=="PREAMBLE":
            flush(); cur=["PREAMBLE"]; i+=1; continue
        if num_re.match(l) or let_re.match(l):
            flush(); cur=[l]; i+=1; continue
        cur.append(l); i+=1
    flush()
    out=[]
    for p in paras:
        p=re.sub(r"[ \t]{2,}"," ",p.strip())
        if p: out.append(p)
    return "\n\n".join(out)+"\n"

_LANG_CFG={
 "es": dict(title=("ACUERDO EN EL MARCO DE LA CONVENCIÓN DE LAS NACIONES UNIDAS SOBRE EL DERECHO DEL MAR "
          "RELATIVO A LA CONSERVACIÓN Y EL USO SOSTENIBLE DE LA DIVERSIDAD BIOLÓGICA MARINA DE LAS "
          "ZONAS SITUADAS FUERA DE LA JURISDICCIÓN NACIONAL"), pre=r"^PREÁMBULO$",
          heads=["PARTE","Artículo","ANEXO","PREÁMBULO"]),
 "fr": dict(title=("ACCORD SE RAPPORTANT À LA CONVENTION DES NATIONS UNIES SUR LE DROIT DE LA MER ET PORTANT "
          "SUR LA CONSERVATION ET L’UTILISATION DURABLE DE LA DIVERSITÉ BIOLOGIQUE MARINE DES ZONES "
          "NE RELEVANT PAS DE LA JURIDICTION NATIONALE"), pre=r"^PR[ÉE]AM.?ULE$",
          heads=["PARTIE","Article","ANNEXE","PRÉAMBULE"]),
 "ru": dict(title=("СОГЛАШЕНИЕ НА БАЗЕ КОНВЕНЦИИ ОРГАНИЗАЦИИ ОБЪЕДИНЕННЫХ НАЦИЙ ПО МОРСКОМУ ПРАВУ О "
          "СОХРАНЕНИИ И УСТОЙЧИВОМ ИСПОЛЬЗОВАНИИ МОРСКОГО БИОЛОГИЧЕСКОГО РАЗНООБРАЗИЯ В РАЙОНАХ ЗА "
          "ПРЕДЕЛАМИ ДЕЙСТВИЯ НАЦИОНАЛЬНОЙ ЮРИСДИКЦИИ"), pre=r"^ПРЕАМБУЛА$",
          heads=["ЧАСТЬ","Статья","ПРИЛОЖЕНИЕ","ПРЕАМБУЛА"]),
}
_FR_FIXES=[("%onne foi","Bonne foi"),("=one d’application","Zone d’application"),
  ("zone, \\ compris","zone, y compris"),("zone, < compris","zone, y compris"),
  ("par zone, \\ compris","par zone, y compris"),("accqs","accès"),("Accqs","Accès"),
  ("Rqglement","Règlement"),("rqglement","règlement"),("Critqres","Critères")]
# Russian: two italic-font runs the +0x1D6 decode cannot reach (Latin-shift italics).
# Confirmed against the official PDF page images (in-situ defined term; "BBNJ" identifier).
_RU_FIXES=[("LQ VLWX","in situ"),("\u00b3BBNJ\u00b4","\u201cBBNJ\u201d")]

def clean_lang(lang, raw):
    raw=raw.replace("\r\n","\n").replace("\r","\n")
    if lang=="ru":
        _DIG={0x13+i:str(i) for i in range(10)}
        _PUN={0x03:" ",0x0f:",",0x10:"-",0x11:".",0x1d:":",0x1e:";",0x0c:"\n",0x00A9:"«",0x00AA:"»"}
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
    CFG=_LANG_CFG[lang]
    if lang=="fr":
        raw=raw.replace("ൗ"," ").replace("¶","’")
    FR_MAP=str.maketrans({"%":"B","*":"G","4":"Q","=":"Z","<":"Y","+":"H"})
    lines=[l.strip() for l in raw.split("\n")]
    pre_re=re.compile(CFG["pre"])
    pre=next((i for i,l in enumerate(lines) if pre_re.match(l)), None)
    if pre is None: raise SystemExit(f"[{lang}] preamble anchor not found")
    lines=[CFG["title"],"",CFG["heads"][3]]+lines[pre+1:]
    page_re=re.compile(r"^\s*-\s*\d+\s*-\s*$")
    lines=[l for l in lines if not page_re.match(l)]
    merged=[]; i=0
    while i<len(lines):
        l=lines[i]
        if re.search(r"[A-Za-zÀ-ÿА-Яа-яЁё]-$",l) and i+1<len(lines) and lines[i+1] and not page_re.match(lines[i+1]):
            merged.append(l+lines[i+1]); i+=2
        else: merged.append(l); i+=1
    lines=merged
    H=CFG["heads"]
    head_re=re.compile(r"^(" + "|".join(re.escape(h) for h in H[:3]) +
                       r")(\s+([IVXLCDM]+|\d+[A-Za-z]*|premier|premier[eè]re))?\s*$", re.I)
    prem_re=re.compile(r"^"+re.escape(H[3])+r"$")
    num_re=re.compile(r"^\d+\.(\s+\S.*)?$")
    let_re=re.compile(r"^(\([\w]{1,4}\)|[A-Za-zÀ-ÿ]\)|[a-z]\.)(\s+\S.*)?$")
    boundary=lambda l: bool(head_re.match(l) or prem_re.match(l) or num_re.match(l) or let_re.match(l))
    paras=[]; cur=[]
    def flush():
        nonlocal cur
        if cur: paras.append(" ".join(x.strip() for x in cur if x.strip()))
        cur=[]
    i=0
    while i<len(lines):
        l=lines[i]
        if not l.strip(): i+=1; continue
        if head_re.match(l):
            flush(); title=""
            if i+1<len(lines) and lines[i+1].strip() and not boundary(lines[i+1]):
                title=lines[i+1].strip(); i+=1
            cur=[l.strip()+("\n"+title if title else "")]; i+=1; continue
        if prem_re.match(l):
            flush(); cur=[H[3]]; i+=1; continue
        if num_re.match(l) or let_re.match(l):
            flush(); cur=[l]; i+=1; continue
        cur.append(l); i+=1
    flush()
    if lang=="fr":
        fixed=[]
        for p in paras:
            if p.startswith("PARTIE") or p.startswith("ANNEXE"):
                p="\n".join(seg.translate(FR_MAP) for seg in p.split("\n"))
            fixed.append(p)
        paras=fixed
    out=[re.sub(r"[ \t]{2,}"," ",p.strip()) for p in paras if p.strip()]
    text="\n\n".join(out)+"\n"
    if lang=="fr":
        for a,b in _FR_FIXES: text=text.replace(a,b)
    if lang=="ru":
        for a,b in _RU_FIXES: text=text.replace(a,b)
    return text

def clean_un(raw, symbol):
    lines=[l.rstrip() for l in raw.replace("\r\n","\n").split("\n")]
    sym_re=re.compile(r"^"+re.escape(symbol)+r"\*?$")
    page_re=re.compile(r"^\d+/\d+$"); docno_re=re.compile(r"^\d{2}-\d{5}\*?( \(E\).*)?$")
    bar_re=re.compile(r"^\*\d{7}\*$"); stamp_re=re.compile(r"^\d{2}/\d{2}/\d{2}$")
    out,i=[],0
    while i<len(lines):
        l=lines[i]
        if sym_re.match(l):
            j=i+1
            while j<len(lines) and not page_re.match(lines[j]): j+=1
            i=j+1; continue
        if page_re.match(l) or docno_re.match(l) or bar_re.match(l) or stamp_re.match(l):
            i+=1; continue
        out.append(l); i+=1
    brk=re.compile(r"^(\d+\.\s|The General Assembly\b|Resolution adopted|Decision |[A-Z][a-z]+ decision\b|\d+/\d+\.\s|\*+ )")
    paras,cur=[],""
    for l in out:
        if not l.strip(): continue
        if brk.match(l):
            if cur: paras.append(cur.strip())
            cur=l
        else: cur=(cur+" "+l).strip()
    if cur: paras.append(cur.strip())
    return "\n\n".join(re.sub(r"[ \t]{2,}"," ",p) for p in paras)+"\n"

def clean_ia(raw, symbol, startre):
    lines=[l.rstrip() for l in raw.replace("\r\n","\n").split("\n")]
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
        else: cur=(cur+" "+l).strip()
    if cur: paras.append(cur.strip())
    return "\n\n".join(re.sub(r"[ \t]{2,}"," ",p) for p in paras)+"\n"

def clean_report(raw):
    lines=[l.rstrip() for l in raw.replace("\r\n","\n").split("\n")]
    keep=[]
    for l in lines:
        s=l.strip()
        if s=="ADVANCE, UNEDITED VERSION": continue
        if re.match(r"^\d{2}/\d{2}/\d{2}$", s): continue
        if re.match(r"^\*\d{6,7}\*$", s): continue
        if re.match(r"^\d{1,3}$", s): continue
        if re.match(r"^\d{1,3}/\d{1,3}$", s): continue
        if re.match(r"^(25|26)-\d{5}", s): continue
        keep.append(l)
    brk=re.compile(r"^(\d+\.\s|[IVXL]+\.\s+[A-Z]|Annex\b|Appendix\b)")
    paras,cur=[],""
    for l in keep:
        if not l.strip(): continue
        if brk.match(l.strip()):
            if cur: paras.append(cur.strip())
            cur=l.strip()
        else: cur=(cur+" "+l.strip()).strip()
    if cur: paras.append(cur.strip())
    text="\n\n".join(re.sub(r"[ \t]{2,}"," ",p) for p in paras)+"\n"
    text=text.replace("India22","India 22")
    return text

def clean_unclos(raw):
    lines=[l.rstrip() for l in raw.replace("\r\n","\n").split("\n")]
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
        else: cur=(cur+" "+l).strip()
    if cur: paras.append(cur.strip())
    return "\n\n".join(re.sub(r"[ \t]{2,}"," ",p) for p in paras)+"\n"

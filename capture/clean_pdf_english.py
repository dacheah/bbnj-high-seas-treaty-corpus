"""
clean_pdf_english.py -- reproducible normalisation of the BYTE-EXACT official PDF.

INPUT : capture/pdf-raw2-english.txt  (pdftotext -raw -enc UTF-8 of the official UN PDF,
        capture/'Text of the Agreement in English.pdf'; sha256 recorded in metadata)
OUTPUT: capture/text-english.full.txt  (complete authentic English text: Preamble +
        Articles 1-76 + Annex I + Annex II)

WHY -raw: pdftotext's default (physical-layout) mode scrambles the reading order of
hanging-indent enumerated items -- it pulls a wrapped trailing fragment (ending in ';' or
'.') to the front of the item (e.g. Annex II (f), Art. 7(n), 12(g), 13(b), 32(e), 33(b),
53(a)). The -raw (content-stream order) mode reads these in the correct order, matching the
PDF page images verified during the G-1b audit. Layout normalisation only; wording preserved.

Documented transformations:
  1. Drop the cover block; begin at PREAMBLE with a single clean title line.
  2. Join line-break hyphenations (line ending 'word-' + next line) with NO space -- all 14
     such breaks in this document are genuine compounds (non-, benefit-, user-, capacity-,
     information-, gender-, middle-); none are syllable-break soft hyphens.
  3. Remove running page-number lines ('- N -').
  4. Reflow: new paragraph before PART/Article/ANNEX headings (heading + its title kept
     together) and before numbered (N.) and lettered ((a)/(i)/a.) sub-provisions; wrapped
     lines are space-joined.
"""
import re, pathlib

HERE = pathlib.Path(__file__).resolve().parent
raw = (HERE / "pdf-raw2-english.txt").read_text(encoding="utf-8")
raw = raw.replace("\r\n", "\n").replace("\r", "\n")
lines = [l.strip() for l in raw.split("\n")]

# 1. begin at PREAMBLE, prepend a single clean title
pre = next(i for i, l in enumerate(lines) if l.strip() == "PREAMBLE")
TITLE = ("AGREEMENT UNDER THE UNITED NATIONS CONVENTION ON THE LAW OF THE SEA ON THE "
         "CONSERVATION AND SUSTAINABLE USE OF MARINE BIOLOGICAL DIVERSITY OF AREAS BEYOND "
         "NATIONAL JURISDICTION")
lines = [TITLE, ""] + lines[pre:]

# 3. drop page-number lines
page_re = re.compile(r"^\s*-\s*\d+\s*-\s*$")
lines = [l for l in lines if not page_re.match(l)]

# 2. join line-break hyphenations (word- \n word  ->  word-word), no space
merged = []
i = 0
while i < len(lines):
    l = lines[i]
    if re.search(r"[A-Za-z]-$", l) and i + 1 < len(lines) and lines[i+1] and not page_re.match(lines[i+1]):
        merged.append(l + lines[i+1]); i += 2
    else:
        merged.append(l); i += 1
lines = merged

# classifiers
head_re = re.compile(r"^(PART\s+[IVXLCDM]+|Article\s+\d+[A-Za-z]?|ANNEX\s+[IVX]+|PREAMBLE)\s*$")
num_re  = re.compile(r"^\d+\.(\s+\S.*)?$")
let_re  = re.compile(r"^(\([a-z0-9]{1,4}\)|[a-z]\.)(\s+\S.*)?$")
boundary = lambda l: bool(head_re.match(l) or num_re.match(l) or let_re.match(l))

paras, cur = [], []
def flush():
    global cur
    if cur:
        paras.append(" ".join(x.strip() for x in cur if x.strip()))
    cur = []

i = 0
while i < len(lines):
    l = lines[i]
    if not l.strip():
        i += 1; continue
    m = head_re.match(l)
    if m and m.group(1) != "PREAMBLE":
        flush()
        title = ""
        if i + 1 < len(lines) and lines[i+1].strip() and not boundary(lines[i+1]):
            title = lines[i+1].strip(); i += 1
        cur = [l.strip() + ("\n" + title if title else "")]
        i += 1; continue
    if l.strip() == "PREAMBLE":
        flush(); cur = ["PREAMBLE"]; i += 1; continue
    if num_re.match(l) or let_re.match(l):
        flush(); cur = [l]; i += 1; continue
    cur.append(l); i += 1
flush()

out = []
for p in paras:
    p = re.sub(r"[ \t]{2,}", " ", p.strip())
    if p:
        out.append(p)
text = "\n\n".join(out) + "\n"
(HERE / "text-english.full.txt").write_text(text, encoding="utf-8")
print("paragraphs:", len(out), "| chars:", len(text),
      "| articles:", len(re.findall(r"(?m)^Article \d+", text)),
      "| parts:", len(re.findall(r"(?m)^PART ", text)),
      "| annexes:", len(re.findall(r"(?m)^ANNEX ", text)))

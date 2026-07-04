"""
clean_english.py -- reproducible normalisation of the captured BBNJ Agreement (English).

INPUT : capture/raw-webfetch-english.txt  (byte-exact output of the fetch of the official
        UN PDF, https://www.un.org/bbnjagreement/.../Text of the Agreement in English.pdf)
OUTPUT: capture/text-english.clean.txt     (authentic English text, extracted_unverified)

This is a CAPTURE helper, not authoritative logic. It performs only layout normalisation of
a machine text-extraction; it does not alter wording. Every transformation is listed below so
a stranger can reproduce and audit it. Fidelity is therefore 'extracted_unverified' (a PDF
byte-for-byte re-capture will upgrade it).

Transformations (documented):
  1. Drop the 3 fetcher header lines (URL, redirect, Content-Type).
  2. Drop the duplicated cover block; text begins at the title + PREAMBLE.
  3. Normalise CRLF/CR -> LF; strip trailing spaces.
  4. Remove running page-number lines matching '- N -'.
  5. Replace stray C0 control bytes left by soft-hyphen line-wraps with '-'.
  6. Reflow hard-wrapped lines into paragraphs, breaking before PART / Article / ANNEX /
     PREAMBLE headings and before numbered (N.) and lettered ((a)) sub-provisions.

KNOWN GAP: the fetch was capped at ~142k characters and stops within Article 73. Articles
74-76 and Annexes I-II are NOT present. This is recorded (see GAPS.md) and will be closed by a
byte-for-byte re-capture of the official PDF (a dated 'corrections' entry).
"""
import re, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
raw = (HERE / "raw-webfetch-english.txt").read_text(encoding="utf-8")

# 3. line endings
raw = raw.replace("\r\n", "\n").replace("\r", "\n")
lines = raw.split("\n")

# 1. drop fetcher header (first 3 lines: url, "->" redirect, Content-Type)
while lines and (lines[0].startswith("http") or lines[0].startswith("→")
                 or lines[0].startswith("Content-Type")):
    lines.pop(0)

# 2. begin at PREAMBLE, re-prepending a single clean title
try:
    pre_idx = next(i for i, l in enumerate(lines) if l.strip() == "PREAMBLE")
except StopIteration:
    sys.exit("PREAMBLE not found -- aborting")
TITLE = ("AGREEMENT UNDER THE UNITED NATIONS CONVENTION ON THE LAW OF THE SEA ON THE "
         "CONSERVATION AND SUSTAINABLE USE OF MARINE BIOLOGICAL DIVERSITY OF AREAS BEYOND "
         "NATIONAL JURISDICTION")
lines = [TITLE, ""] + lines[pre_idx:]

# 3/4/5. per-line cleaning
page_re = re.compile(r"^\s*-\s*\d+\s*-\s*$")
ctrl_re = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
clean = []
for l in lines:
    l = l.rstrip()
    if page_re.match(l):
        continue
    l = ctrl_re.sub("-", l)          # soft-hyphen wrap artifacts -> '-'
    clean.append(l)

# 6. reflow into paragraphs
brk = re.compile(r"^(PART\s+[IVXLCDM]+\b|Article\s+\d+[A-Za-z]?\b|PREAMBLE\b|ANNEX\b|"
                 r"\d+\.\s|\([a-z]{1,3}\)\s)")
art = re.compile(r"^Article\s+\d+[A-Za-z]?\s*$")
part = re.compile(r"^PART\s+[IVXLCDM]+\s*$")

paras, cur = [], []
def flush():
    if cur:
        paras.append(" ".join(x.strip() for x in cur if x.strip()))
    cur.clear()

i = 0
while i < len(clean):
    l = clean[i]
    if not l.strip():
        i += 1
        continue
    if art.match(l):
        # Article header: keep "Article N" + its title line on their own lines
        flush()
        title = clean[i + 1].strip() if i + 1 < len(clean) else ""
        # a Part heading sometimes has its subtitle on the next line too; not here
        paras.append(l.strip() + ("\n" + title if title else ""))
        i += 2
        # collect the article body until next break, join with spaces
        body = []
        while i < len(clean) and not brk.match(clean[i]) and not part.match(clean[i]):
            if clean[i].strip():
                body.append(clean[i].strip())
            i += 1
        if body:
            paras[-1] += "\n" + " ".join(body)
        continue
    if part.match(l):
        flush()
        subtitle = clean[i + 1].strip() if i + 1 < len(clean) else ""
        paras.append(l.strip() + ("\n" + subtitle if subtitle and not art.match(subtitle) else ""))
        i += 2
        continue
    if brk.match(l):
        flush()
        cur.append(l)
        i += 1
        continue
    cur.append(l)
    i += 1
flush()

text = "\n\n".join(p.strip() for p in paras if p.strip()) + "\n"
(HERE / "text-english.clean.txt").write_text(text, encoding="utf-8")
n_art = len(re.findall(r"(?m)^Article \d+", text))
n_part = len(re.findall(r"(?m)^PART ", text))
print("paragraphs:", len(paras))
print("chars:", len(text))
print("part headers:", n_part)

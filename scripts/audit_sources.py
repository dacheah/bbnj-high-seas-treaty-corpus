#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_sources.py — verify every monitored source URL still points where we think it does.

PORTABLE: stdlib only, no dependencies, no crawl layer required. Drop into any corpus that has a
`monitoring/sources.json` with `name` and `url` per source.

WHY THIS EXISTS. A content hash tells you a page changed. It cannot tell you the page was never the
right page. Audited in the deep-seabed corpus on 2026-07-18, three of twenty sources were wrong:

  * a case register that pointed at an overview page — real litigation had accumulated unseen;
  * a "Council documents" source pointing at a URL that SILENTLY REDIRECTED to a year-old agenda item;
  * two regulation sources that both redirected to an access-denied page. The tell was visible for
    weeks in the metadata: two different regulations carried IDENTICAL hashes, which is impossible.

All five returned HTTP 200 with stable content. Hashing reported them healthy the entire time.

WHAT THIS CATCHES, deterministically: HTTP errors, and silent redirects to a different destination.

WHAT IT CANNOT CATCH: a URL that resolves cleanly to a real, related, but WRONG page. That was the
case-register defect, and it was found by a human reading the page. A clean audit means "no broken
plumbing" — never "every source watches the right thing".

ADVISORY ONLY. Never edits sources.json. It reports; a human judges and fixes.

    python3 scripts/audit_sources.py              # report to stdout + monitoring/source_audit.md
    python3 scripts/audit_sources.py --delay 2    # be gentler on the servers
    python3 scripts/audit_sources.py --selftest   # offline checks of the pure logic
"""
from __future__ import annotations
import datetime
import json
import os
import re
import sys
import time
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

HERE = os.path.dirname(os.path.abspath(__file__))          # scripts/
REPO = os.path.dirname(HERE)                                # repo root
SOURCES = os.path.join(REPO, "monitoring", "sources.json")
REPORT = os.path.join(REPO, "monitoring", "source_audit.md")
# MUST match the monitor's agent, or the audit measures the wrong client. Proved 2026-07-18:
# boletinoficial.gob.ar refused a bare token with URLError but served 136 KB to this string.
# An audit that fails where the monitor succeeds reports phantom dead sources — and several
# 403s in the first Neo audit are now suspect for exactly this reason.
UA = "Mozilla/5.0 (compatible; provenance-corpus-monitor/1.0; +https://github.com/dacheah)"

# Structural words that carry no signal when matching a source name against a page title.
STOP_BASE = {"the", "and", "for", "with", "from", "list", "page", "new", "official", "document",
             "documents", "current", "latest", "index", "home", "site", "website"}


# ---- pure logic (offline-testable) ----------------------------------------------------------------
def norm_url(u: str) -> str:
    """Compare URLs ignoring scheme, www, trailing slash and case — differences that never matter."""
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def redirected(requested: str, final: str) -> bool:
    """Compare the ENCODED request against the final URL.

    A non-ASCII URL is percent-encoded before the fetch, so the server reports the encoded form
    back. Comparing that to the raw source URL made every Arabic, Korean and accented-Spanish
    source look like it redirected. Same resource, different spelling — not a redirect.
    """
    return norm_url(encode_url(requested)) != norm_url(final)


def page_title(html: str) -> str:
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html or "")
    if not m:
        return ""
    t = re.sub(r"\s+", " ", m.group(1)).strip()
    # Strip a trailing site-name segment ONLY where the separator is surrounded by whitespace.
    # Requiring the spaces matters: a bare hyphen is usually INSIDE a word, and stripping at it
    # mangled real titles — "Sanctions and Anti-Money Laundering Act 2018" -> "Sanctions and Anti",
    # Japan's "e-Gov..." -> "e" — which then produced bogus name/title mismatch warnings.
    return re.sub(r"\s+[|\-–—]\s+[^|\-–—]*$", "", t).strip() or t


def adaptive_stopwords(names: list, threshold: float = 0.25) -> set:
    """Words appearing across many source names are not distinctive — derive them, don't hand-tune.

    Makes the tool portable: a sanctions corpus and a seabed corpus have different noise words
    ("sanctions", "authority"), and neither should need a curated list.
    """
    if not names:
        return set(STOP_BASE)
    counts = {}
    for n in names:
        for w in set(re.findall(r"[a-z0-9]+", n.lower())):
            if len(w) > 3:
                counts[w] = counts.get(w, 0) + 1
    cut = max(2, int(len(names) * threshold))
    return set(STOP_BASE) | {w for w, c in counts.items() if c >= cut}


def tokens(text: str, stop: set) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
            if len(w) > 3 and w not in stop}


def name_matches_title(name: str, title: str, stop: set) -> bool:
    """Weak by design — one shared meaningful word passes. Meant to catch a source called
    'Council documents' landing on a page titled 'Item 16', not to police wording."""
    nt, tt = tokens(name, stop), tokens(title, stop)
    if not nt or not tt:
        return True          # nothing to judge on; do not manufacture a warning
    return bool(nt & tt)


def verdict(req_url, final_url, status, name, title, stop) -> tuple:
    """Return (level, message). Levels: ok | review | broken."""
    if status is None:
        return "broken", f"could not be fetched — {title}"
    if int(status) >= 400:
        return "broken", f"HTTP {status}"
    notes = []
    if redirected(req_url, final_url):
        notes.append(f"REDIRECTS to {final_url}")
    if not name_matches_title(name, title, stop):
        notes.append(f"page title '{title}' does not resemble the source name")
    return ("review", "; ".join(notes)) if notes else ("ok", f"'{title}'")


def duplicate_hashes(sources: list) -> list:
    """Two sources sharing a content hash is impossible unless both fetch the same page.

    This is how the eCFR block page hid for weeks: two different regulations, one identical hash,
    sitting in the metadata where anyone could have seen it.
    """
    seen, dupes = {}, []
    for s in sources:
        h = s.get("last_sha256")
        if not h:
            continue
        seen.setdefault(h, []).append(s["name"])
    for h, names in seen.items():
        if len(names) > 1:
            dupes.append((h, names))
    return dupes


# ---- live check -----------------------------------------------------------------------------------
def encode_url(u: str) -> str:
    """Make a URL wire-safe without changing what it points at.

    Official sources are not all ASCII: Dubai's legislation portal uses Arabic paths WITH SPACES,
    Korea's law.go.kr uses Hangul, Argentina uses accented Spanish. urllib raises UnicodeEncodeError
    or InvalidURL on these, which the audit then misreports as a BROKEN SOURCE. The source is fine;
    the client was wrong. '%' is kept safe so an already-encoded URL is not double-encoded, and the
    host is IDNA-encoded separately from the path.
    """
    p = urlsplit(u.strip())
    netloc = p.netloc
    if p.hostname:
        try:
            host = p.hostname.encode("idna").decode("ascii")
        except Exception:
            host = p.hostname
        netloc = f"{host}:{p.port}" if p.port else host
    safe = "/%:@&=+$,~()!*';"
    return urlunsplit((p.scheme, netloc, quote(p.path, safe=safe),
                       quote(p.query, safe=safe + "?"), p.fragment))


def fetch(url: str):
    req = Request(encode_url(url), headers={"User-Agent": UA})
    with urlopen(req, timeout=45) as r:
        raw = r.read().decode("utf-8", errors="replace")
        return raw, r.geturl(), int(getattr(r, "status", 200) or 200)


def selftest() -> int:
    stop = set(STOP_BASE)
    assert norm_url("https://WWW.Example.org/a/") == "example.org/a"
    assert not redirected("https://www.example.org/a/", "https://example.org/a")
    assert redirected("https://www.example.org/a/", "https://example.org/b")
    assert page_title("<title>Item 16 - International Seabed Authority</title>") == "Item 16"
    # regression: a hyphen INSIDE a word is not a site-name separator (real 2026-07-18 defect)
    assert page_title("<title>Sanctions and Anti-Money Laundering Act 2018</title>") \
        == "Sanctions and Anti-Money Laundering Act 2018"
    assert page_title("<title>e-Gov law search</title>") == "e-Gov law search"
    assert page_title("<title>Proceeds of Crime Act 2002</title>") == "Proceeds of Crime Act 2002"
    # non-ASCII and space-bearing URLs must be encoded, not reported as broken sources
    assert encode_url("https://www.law.go.kr/법령/가상자산이용자보호법").isascii()
    assert " " not in encode_url("https://dlp.dubai.gov.ae/legislation ar reference/2022/x.html")
    assert encode_url("https://a.test/%D8%A7").count("%D8") == 1, "must not double-encode"
    assert encode_url("https://a.test/a/b?x=1&y=2") == "https://a.test/a/b?x=1&y=2"
    # real defect: a 'Council documents' source landing on 'Item 16'
    assert not name_matches_title("ISA - Council documents", "Item 16", stop)
    # real limitation, asserted so nobody "fixes" it into false alarms: an overview page titled
    # 'Cases' is indistinguishable from the register titled 'List of Cases' by tokens alone.
    assert name_matches_title("ITLOS - List of cases", "Cases", stop)
    # adaptive stopwords: a word in most source names carries no signal
    names = ["OFAC sanctions list", "EU sanctions list", "UN sanctions list", "UK sanctions list"]
    st = adaptive_stopwords(names)
    assert "sanctions" in st, "a word common to most sources must become a stopword"
    assert "ofac" not in st, "a distinctive word must survive"
    assert verdict("https://x/a", "https://x/a", 200, "Mining Code", "Mining Code", stop)[0] == "ok"
    assert verdict("https://x/a", "https://x/b", 200, "Mining Code", "Mining Code", stop)[0] == "review"
    assert verdict("https://x/a", "https://x/a", 404, "Mining Code", "Mining Code", stop)[0] == "broken"
    d = duplicate_hashes([{"name": "A", "last_sha256": "h1"}, {"name": "B", "last_sha256": "h1"},
                          {"name": "C", "last_sha256": "h2"}])
    assert len(d) == 1 and set(d[0][1]) == {"A", "B"}, d
    print("audit_sources selftest: OK")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    delay = 1.0
    if "--delay" in sys.argv:
        delay = float(sys.argv[sys.argv.index("--delay") + 1])

    data = json.load(open(SOURCES, encoding="utf-8"))
    sources = data["sources"] if isinstance(data, dict) and "sources" in data else data
    stop = adaptive_stopwords([s["name"] for s in sources])

    rows, counts = [], {"ok": 0, "review": 0, "broken": 0}
    for i, s in enumerate(sources, 1):
        name, url = s["name"], s["url"]
        try:
            raw, final, status = fetch(url)
            title = page_title(raw)
        except Exception as e:
            raw, final, status, title = "", url, None, f"{type(e).__name__}: {e}"
        level, msg = verdict(url, final, status, name, title, stop)
        counts[level] += 1
        rows.append((level, name, url, msg))
        print(f"[{level.upper():6}] ({i}/{len(sources)}) {name}\n           {msg}")
        if delay:
            time.sleep(delay)

    dupes = duplicate_hashes(sources)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [f"# Source URL audit — {now}", "",
             f"{counts['ok']} ok · {counts['review']} need review · {counts['broken']} broken", "",
             "Advisory only — nothing was changed. A REDIRECT is not automatically wrong (sites move "
             "pages legitimately) but must be confirmed to still be the intended target. A title "
             "mismatch means the page may not be what the source claims to watch.", "",
             "**A clean audit means no broken plumbing — not that every source watches the right "
             "page.** A URL resolving cleanly to a real but wrong page passes this tool; only a "
             "human reading the page catches that.", ""]
    if dupes:
        lines += ["## ⛔ DUPLICATE HASHES", "",
                  "Two sources cannot legitimately share a content hash. This almost always means "
                  "both are fetching the same page — typically an error or access-denied page.", ""]
        for h, names in dupes:
            lines.append(f"- `{h}`")
            for n in names:
                lines.append(f"    - {n}")
        lines.append("")
    for level in ("broken", "review", "ok"):
        picked = [r for r in rows if r[0] == level]
        if not picked:
            continue
        mark = {"broken": "⛔ BROKEN", "review": "🔶 REVIEW", "ok": "✅ OK"}[level]
        lines += [f"## {mark} ({len(picked)})", ""]
        for _, name, url, msg in picked:
            lines += [f"- **{name}**", f"    - `{url}`", f"    - {msg}"]
        lines.append("")
    with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n{counts['ok']} ok · {counts['review']} need review · {counts['broken']} broken")
    if dupes:
        print(f"⛔ {len(dupes)} duplicate hash group(s) — two sources cannot share a hash legitimately")
    print(f"wrote {REPORT}")
    print("Advisory only — sources.json was NOT modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

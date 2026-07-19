"""
watch_sources.py -- Phase F source monitor (consolidated v3).

ONE monitor for the whole corpus portfolio. Merges three generations that had diverged:

  v1 (space, bbnj, neo)  page hash + baseline/changed/unchanged/error.
  v2 (aml-sanctions)     + MANUAL for declared SPAs, + monitor_url for server-rendered
                           alternatives, + SUSPECT when content is implausibly short,
                           + baselines advanced ONLY for trustworthy states.
  v3 (deep-seabed)       + optional schema mode (deterministic CSS extraction via the crawl
                           layer) giving instrument-level diffs, + a broken-selector guard,
                           + false-alarm instrumentation.

This file is the canonical merge, plus two fixes found auditing the portfolio on 2026-07-18:
non-ASCII URL encoding, and a duplicate-hash guard.

WHY EACH GUARD EXISTS (every one is a real failure that happened, not a hypothetical):

  * MANUAL — several official portals are JavaScript apps. A stdlib GET returns a shell, whose
    hash is perfectly STABLE, so the monitor reports "unchanged" forever while the law changes.
    Stable-but-wrong is the worst failure mode for an integrity tool.
  * SUSPECT — a formerly static site migrating to a SPA reintroduces that blind spot silently.
    Any fetch whose stripped text falls below CONTENT_FLOOR is flagged and NOT baselined.
  * SCHEMA_SUSPECT — with a CSS schema, a markup change can make selectors match nothing. Real
    listings lose documents one at a time; broken selectors lose all at once. A collapse is
    reported as probable breakage, never as documents being removed.
  * DUPLICATE HASHES — two sources cannot legitimately share a content hash. In the deep-seabed
    corpus, 15 CFR 970 and 971 carried identical hashes for weeks because both were fetching the
    same access-denied page. It sat in the metadata where anyone could have seen it.
  * URL ENCODING — official sources are not all ASCII. Dubai's legislation portal uses Arabic
    paths with spaces; Korea uses Hangul. urllib raises on these, which gets misread as a dead
    source when the source is fine and the client was wrong.

Automation only WATCHES and queues; the maintainer judges. Nothing is ingested automatically.

    python3 scripts/watch_sources.py             # live run
    python3 scripts/watch_sources.py --selftest  # offline, no network
    python3 scripts/watch_sources.py --tally     # measured whole-page false-alarm rate
"""
from __future__ import annotations
import datetime
import hashlib
import json
import os
import re
import sys
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

# Bump on EVERY behaviour change. 3.0 shipped to five corpora, then gained is_manual() without a
# bump — so all five reported "3.0" while one differed. A drift detector that isn't updated detects
# nothing.
#   3.0  consolidated v1/v2/v3: MANUAL, monitor_url, CONTENT_FLOOR, schema mode, guards
#   3.1  monitor:"manual" declaration distinct from render:"spa"; UA decoupled from this version
#   3.2  all text writes pin newline="\n" — Windows text mode was emitting CRLF into sources.json,
#        last_report.md and snapshots, leaving every run "modified" with an empty diff
MONITOR_VERSION = "3.2"

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SOURCES = os.path.join(REPO, "monitoring", "sources.json")
REPORT = os.path.join(REPO, "monitoring", "last_report.md")
SNAP_DIR = os.path.join(REPO, "monitoring", "snapshots")
ALARM_LOG = os.path.join(REPO, "monitoring", "false_alarm_log.jsonl")

# Identify honestly and give operators a contact route. A bare token is more likely to be
# refused by a WAF than a descriptive agent — several 403s during the 2026-07-18 audit were
# plausibly the agent string rather than a real block.
# DELIBERATELY NOT derived from MONITOR_VERSION. Embedding the tool version meant every bump
# changed the request, and a server may return different content to a different agent — so a
# routine version bump could flag every source as CHANGED. The agent identifies the *client*,
# which is stable; MONITOR_VERSION identifies the *logic*, which is not.
UA = "Mozilla/5.0 (compatible; provenance-corpus-monitor/1.0; +https://github.com/dacheah)"

CONTENT_FLOOR = 1000      # stripped-text chars below which a fetch reads as a shell/error page
SCHEMA_MIN_PREV = 5       # below this, a previous record set is too small to judge a collapse
SCHEMA_DROP_RATIO = 0.5   # a fall below half the previous count reads as broken selectors

# Optional schema mode. Absent crawl layer or crawl4ai -> every source uses whole-page hashing.
sys.path.insert(0, os.path.join(HERE, "crawl"))
try:
    import common as _crawl
    _HAVE_CRAWL = True
except Exception:
    _crawl = None
    _HAVE_CRAWL = False


# ---- pure helpers (offline-testable) --------------------------------------------------------
def to_text(raw: str) -> str:
    """Reduce HTML to comparable text: drop scripts/styles/tags, collapse space."""
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()


def content_hash(raw: str) -> str:
    return "sha256:" + hashlib.sha256(to_text(raw).encode("utf-8")).hexdigest()


def encode_url(u: str) -> str:
    """Percent-encode a URL without changing what it points at. '%' stays safe (no double-encode)."""
    p = urlsplit((u or "").strip())
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


def is_manual(s: dict) -> bool:
    """A source that cannot be honestly auto-monitored, declared explicitly.

    Two ways to say so, because there are two different reasons:
      render: "spa"      the page is a JavaScript app; a stdlib GET returns a shell.
      monitor: "manual"  anything else — a persistent 403, a form-POST search with no stable
                         GET URL, a login wall, a certificate we will not bypass.

    Either is OVERRIDDEN by monitor_url, which points at something a stdlib fetch can read.
    Overloading render:"spa" for blocks was misleading: a 403 is not a rendering problem, and
    the distinction matters when someone later asks why a source is unwatched.
    """
    if s.get("monitor_url"):
        return False
    return s.get("render") == "spa" or s.get("monitor") == "manual"


def monitored_url(s: dict) -> str:
    """Fetch a server-rendered artefact where declared, else the human URL.

    Keeps `url` citable while `monitor_url` carries the machine endpoint — e.g. an eCFR
    versioner API alongside the human eCFR page, or Japan's e-Gov XML API beside its SPA.
    """
    return s.get("monitor_url") or s["url"]


def schema_suspect(prev_count: int, cur_count: int) -> bool:
    """True when a record count COLLAPSES — reads as broken selectors, not removed documents."""
    if prev_count < SCHEMA_MIN_PREV:
        return False
    if cur_count == 0:
        return True
    return cur_count < prev_count * SCHEMA_DROP_RATIO


def duplicate_hashes(sources: list) -> list:
    """Groups of sources sharing a content hash — impossible unless both fetch the same page."""
    seen = {}
    for s in sources:
        h = s.get("last_sha256")
        if h:
            seen.setdefault(h, []).append(s["name"])
    return [(h, names) for h, names in seen.items() if len(names) > 1]


def _rec_key(rec: dict) -> str:
    for k in ("doc_url", "url", "citation", "title"):
        if rec.get(k):
            return str(rec[k]).strip()
    return json.dumps(rec, sort_keys=True, ensure_ascii=False)


def diff_records(prev: list, cur: list) -> dict:
    """Structured diff: new / disappeared / changed-fields."""
    pv = {_rec_key(r): r for r in prev}
    cv = {_rec_key(r): r for r in cur}
    changed = []
    for k in cv:
        if k in pv and cv[k] != pv[k]:
            fields = set(pv[k]) | set(cv[k])
            changed.append({"key": k, "changes": {f: {"was": pv[k].get(f), "now": cv[k].get(f)}
                                                  for f in sorted(fields)
                                                  if pv[k].get(f) != cv[k].get(f)}})
    return {"new": [cv[k] for k in cv if k not in pv],
            "disappeared": [pv[k] for k in pv if k not in cv],
            "changed": changed}


def classify(sources: list, hashes: dict, lengths: dict | None = None) -> list:
    """Pure whole-page diff logic. States: manual, error, suspect, baseline, changed, unchanged."""
    lengths = lengths or {}
    events = []
    for s in sources:
        name = s["name"]
        h = hashes.get(name)
        if is_manual(s):
            events.append((name, "manual", s.get("last_sha256"), h))
        elif h is None or str(h).startswith("ERROR"):
            events.append((name, "error", s.get("last_sha256"), h))
        elif lengths.get(name, CONTENT_FLOOR) < CONTENT_FLOOR:
            events.append((name, "suspect", s.get("last_sha256"), h))
        elif s.get("last_sha256") is None:
            events.append((name, "baseline", None, h))
        elif h != s["last_sha256"]:
            events.append((name, "changed", s["last_sha256"], h))
        else:
            events.append((name, "unchanged", s["last_sha256"], h))
    return events


def log_observation(ts, name, page_changed, records_changed, state) -> dict:
    """One instrumentation row: what whole-page hashing WOULD have flagged vs what really changed."""
    verdict = ("false_alarm" if page_changed and not records_changed
               else "real_change" if records_changed else "quiet")
    return {"ts": ts, "source": name, "page_changed": bool(page_changed),
            "records_changed": bool(records_changed), "state": state, "verdict": verdict}


# ---- live fetch -----------------------------------------------------------------------------
def fetch(url: str) -> str:
    req = Request(encode_url(url), headers={"User-Agent": UA})
    with urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", errors="replace")


def _snap_path(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or "src"
    return os.path.join(SNAP_DIR, slug + ".json")


def schema_check(source: dict) -> dict:
    """Extract via committed CSS schema, hash records AND page, diff, apply the collapse guard."""
    import asyncio
    schema = _crawl.load_schema(source["schema"])
    records, html, _ = asyncio.run(_crawl.crawl_extract(monitored_url(source), schema))
    h_rec = _crawl.records_hash(records)
    h_page = content_hash(html) if html else None
    sp = _snap_path(source["name"])
    prev = json.load(open(sp, encoding="utf-8")).get("records", []) if os.path.isfile(sp) else []
    prev_hash = source.get("last_sha256")
    info = {"records": records, "h_rec": h_rec, "h_page": h_page,
            "prev_count": len(prev), "cur_count": len(records),
            "records_changed": bool(prev_hash is not None and h_rec != prev_hash),
            "page_changed": bool(source.get("last_page_sha256") and h_page
                                 and h_page != source.get("last_page_sha256")),
            "report": None}
    if prev_hash is None or not os.path.isfile(sp):
        # No comparable previous RECORD set: first run, or a source switching from whole-page
        # mode (whose last_sha256 is a PAGE hash). Baseline rather than cry "everything is new".
        info["state"] = "baseline"
    elif schema_suspect(len(prev), len(records)):
        info["state"] = "schema_suspect"
        info["report"] = diff_records(prev, records)
    elif not info["records_changed"]:
        info["state"] = "unchanged"
    else:
        info["state"] = "changed"
        info["report"] = diff_records(prev, records)
    return info


# ---- self-test ------------------------------------------------------------------------------
def selftest() -> int:
    assert content_hash("<p>hi</p>") == content_hash("<p>  hi  </p>")
    # whole-page states, including every guard
    srcs = [{"name": "a", "url": "x", "last_sha256": "sha256:aaa"},
            {"name": "b", "url": "y", "last_sha256": None},
            {"name": "c", "url": "z", "last_sha256": "sha256:ccc"},
            {"name": "d", "url": "w", "last_sha256": "sha256:ddd"},
            {"name": "e", "url": "s", "render": "spa", "last_sha256": "sha256:eee"},
            {"name": "f", "url": "s", "render": "spa", "monitor_url": "api",
             "last_sha256": "sha256:fff"},
            {"name": "g", "url": "v", "last_sha256": None}]
    hh = {"a": "sha256:aaa", "b": "sha256:bbb", "c": "sha256:CHANGED", "d": "ERROR:timeout",
          "e": "sha256:eee", "f": "sha256:fff", "g": "sha256:short"}
    ll = {"a": 5000, "b": 5000, "c": 5000, "d": 0, "e": 40, "f": 5000, "g": 12}
    got = {n: st for n, st, _, _ in classify(srcs, hh, ll)}
    assert got == {"a": "unchanged", "b": "baseline", "c": "changed", "d": "error",
                   "e": "manual", "f": "unchanged", "g": "suspect"}, got
    # a SPA must never be baselined, even on a first run
    assert classify([{"name": "z", "url": "s", "render": "spa", "last_sha256": None}],
                    {"z": "sha256:zz"}, {"z": 30})[0][1] == "manual"
    # monitor_url takes precedence, url is the fallback
    assert monitored_url({"url": "human", "monitor_url": "api"}) == "api"
    assert monitored_url({"url": "human"}) == "human"
    # both manual declarations work, and monitor_url overrides either
    assert is_manual({"render": "spa"}) and is_manual({"monitor": "manual"})
    assert not is_manual({"render": "spa", "monitor_url": "api"})
    assert not is_manual({"monitor": "manual", "monitor_url": "api"})
    assert not is_manual({"url": "x"})
    assert classify([{"name": "m", "url": "x", "monitor": "manual", "last_sha256": None}],
                    {"m": "sha256:mm"}, {"m": 9000})[0][1] == "manual"
    # broken-selector guard boundaries
    assert schema_suspect(38, 0) and schema_suspect(38, 18)
    assert not schema_suspect(38, 19) and not schema_suspect(38, 36) and not schema_suspect(4, 0)
    # structured diff
    d = diff_records([{"doc_url": "a", "title": "A"}, {"doc_url": "b", "title": "B"}],
                     [{"doc_url": "a", "title": "A"}, {"doc_url": "b", "title": "B rev"},
                      {"doc_url": "c", "title": "C"}])
    assert [r["title"] for r in d["new"]] == ["C"] and d["disappeared"] == []
    assert len(d["changed"]) == 1 and d["changed"][0]["key"] == "b"
    # duplicate hashes
    dup = duplicate_hashes([{"name": "A", "last_sha256": "h"}, {"name": "B", "last_sha256": "h"},
                            {"name": "C", "last_sha256": "i"}])
    assert len(dup) == 1 and set(dup[0][1]) == {"A", "B"}
    # non-ASCII URLs must encode, not explode
    assert encode_url("https://www.law.go.kr/법령/가상자산이용자보호법").isascii()
    assert " " not in encode_url("https://dlp.dubai.gov.ae/legislation ar ref/x.html")
    assert encode_url("https://a.test/%D8%A7").count("%D8") == 1
    # instrumentation verdicts
    assert log_observation("t", "s", True, False, "unchanged")["verdict"] == "false_alarm"
    assert log_observation("t", "s", False, True, "changed")["verdict"] == "real_change"
    assert log_observation("t", "s", False, False, "unchanged")["verdict"] == "quiet"
    print(f"watch_sources v{MONITOR_VERSION} selftest: OK")
    return 0


def tally() -> int:
    """Measured false-alarm rate of whole-page hashing, from accumulated schema-mode runs."""
    if not os.path.isfile(ALARM_LOG):
        print("No instrumentation yet. Needs two runs on a schema-mode source.")
        return 0
    rows = [json.loads(l) for l in open(ALARM_LOG, encoding="utf-8") if l.strip()]
    obs = [r for r in rows if r.get("state") in ("changed", "unchanged", "schema_suspect")]
    if not obs:
        print(f"{len(rows)} row(s) logged, none yet comparable (all baselines).")
        return 0
    page = sum(1 for r in obs if r["page_changed"])
    recs = sum(1 for r in obs if r["records_changed"])
    false = sum(1 for r in obs if r["page_changed"] and not r["records_changed"])
    missed = sum(1 for r in obs if r["records_changed"] and not r["page_changed"])
    print(f"Observations: {len(obs)} over {min(r['ts'] for r in obs)} .. {max(r['ts'] for r in obs)}")
    print(f"  whole-page would have flagged : {page}")
    print(f"  real instrument-level changes : {recs}")
    print(f"  FALSE ALARMS                  : {false}")
    if missed:
        print(f"  page quiet but records changed: {missed}  (whole-page would have MISSED these)")
    if page:
        print(f"  => measured false-alarm rate: {false / page * 100:.0f}% of its flags")
    return 0


# ---- run ------------------------------------------------------------------------------------
def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--tally" in sys.argv:
        return tally()

    data = json.load(open(SOURCES, encoding="utf-8"))
    sources = data["sources"] if isinstance(data, dict) and "sources" in data else data
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(SNAP_DIR, exist_ok=True)
    schema_ok = _HAVE_CRAWL and _crawl.crawl4ai_status()[0]

    hashes, lengths, schema_states, observations = {}, {}, {}, []
    for s in sources:
        name = s["name"]
        if s.get("schema") and schema_ok:
            try:
                info = schema_check(s)
                schema_states[name] = info
                observations.append(log_observation(now, name, info["page_changed"],
                                                    info["records_changed"], info["state"]))
                if info["state"] != "schema_suspect":
                    with open(_snap_path(name), "w", encoding="utf-8", newline="\n") as f:
                        json.dump({"generated": now, "records": info["records"]}, f,
                                  indent=2, ensure_ascii=False)
                    s["last_sha256"] = info["h_rec"]
                    if info["h_page"]:
                        s["last_page_sha256"] = info["h_page"]
            except Exception as e:
                schema_states[name] = {"state": "error", "err": f"{type(e).__name__}: {e}"}
            s["last_checked"] = now
            continue
        if is_manual(s):
            hashes[name] = None            # do not even pretend to fetch it
            s["last_checked"] = now
            continue
        try:
            raw = fetch(monitored_url(s))
            lengths[name] = len(to_text(raw))
            hashes[name] = content_hash(raw)
        except Exception as e:
            hashes[name] = f"ERROR:{type(e).__name__}"
        s["last_checked"] = now

    page_sources = [s for s in sources if s["name"] not in schema_states]
    events = classify(page_sources, hashes, lengths)
    st_of = {n: st for n, st, _, _ in events}

    # Advance baselines ONLY for trustworthy states — never a shell, a SPA, or an error.
    for s in page_sources:
        if st_of[s["name"]] in {"baseline", "unchanged", "changed"}:
            h = hashes[s["name"]]
            if h and not str(h).startswith("ERROR"):
                s["last_sha256"] = h

    # ---- report
    dupes = duplicate_hashes(sources)
    n_schema_changed = sum(1 for i in schema_states.values() if i.get("state") == "changed")
    n_schema_susp = sum(1 for i in schema_states.values() if i.get("state") == "schema_suspect")
    counts = {k: sum(1 for _, st, _, _ in events if st == k)
              for k in ("changed", "suspect", "manual", "error")}
    lines = [f"# Source monitor report — {now}", "",
             f"_monitor v{MONITOR_VERSION} · schema mode "
             f"{'on' if schema_ok else 'off (whole-page fallback)'}_", "",
             f"{counts['changed'] + n_schema_changed} changed · {counts['suspect']} suspect · "
             f"{n_schema_susp} schema-suspect · {counts['manual']} manual-review · "
             f"{counts['error']} error · {len(sources)} total", ""]
    if dupes:
        lines += ["## ⛔ DUPLICATE HASHES", "",
                  "Two sources cannot legitimately share a hash — both are probably fetching the "
                  "same error or access-denied page.", ""]
        for h, names in dupes:
            lines += [f"- `{h}`"] + [f"    - {n}" for n in names]
        lines.append("")
    if schema_states:
        lines += ["## Schema-mode sources", ""]
        for name, i in schema_states.items():
            st = i.get("state")
            if st == "schema_suspect":
                lines.append(f"- **{name}** — ⛔ **SCHEMA SUSPECT**: records fell "
                             f"{i['prev_count']} → {i['cur_count']}. Selectors have probably "
                             f"broken; this is NOT read as documents being removed. Baseline and "
                             f"snapshot deliberately NOT advanced.")
            elif st == "changed":
                r = i["report"]
                lines.append(f"- **{name}** — 🔶 CHANGED: {len(r['new'])} new, "
                             f"{len(r['disappeared'])} gone, {len(r['changed'])} amended")
                for x in r["new"]:
                    lines.append(f"    - ➕ {x.get('title') or x.get('citation') or _rec_key(x)}")
                for x in r["disappeared"]:
                    lines.append(f"    - ➖ {x.get('title') or x.get('citation') or _rec_key(x)}")
            elif st == "error":
                lines.append(f"- **{name}** — ⚠️ {i.get('err')}")
            else:
                lines.append(f"- **{name}** — "
                             f"{'🟦 baseline set' if st == 'baseline' else '✅ unchanged'} "
                             f"({i.get('cur_count', '?')} records)")
        lines.append("")
    order = ["changed", "suspect", "manual", "error", "baseline", "unchanged"]
    mark = {"changed": "🔶 CHANGED", "suspect": "🟥 SUSPECT — content too short (shell/error?)",
            "manual": "🟠 MANUAL — JS-rendered source, auto-monitor cannot see the law",
            "error": "⚠️ fetch error", "baseline": "🟦 baseline set", "unchanged": "✅ unchanged"}
    by_state = {k: [] for k in order}
    for name, state, old, new in events:
        by_state[state].append((name, old, new))
    for state in order:
        rows = by_state[state]
        if not rows:
            continue
        lines += [f"## {mark[state]} ({len(rows)})"]
        for name, old, new in rows:
            lines.append(f"- **{name}**")
            if state == "changed":
                lines += [f"    - was `{old}`", f"    - now `{new}`"]
        lines.append("")
    lines += ["_Automation only watches and queues. A flag may be a genuinely new or amended "
              "instrument OR a cosmetic page update — the maintainer triages. **MANUAL** sources "
              "are JavaScript apps a stdlib fetch cannot see. **SUSPECT** means too little text to "
              "trust. **SCHEMA SUSPECT** means selectors probably broke. Nothing is ingested "
              "automatically._"]
    # newline="\n" on EVERY text write. Without it, Python text mode on Windows emits CRLF, so a
    # monitor run left sources.json and last_report.md differing from their LF blobs in line
    # endings only — an empty diff that still shows as modified, on every run, in five corpora.
    # .gitattributes governs checkout, not what a script writes.
    with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    with open(SOURCES, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    if observations:
        with open(ALARM_LOG, "a", encoding="utf-8", newline="\n") as f:
            for o in observations:
                f.write(json.dumps(o, ensure_ascii=False) + "\n")

    flag = (counts["changed"] or counts["suspect"] or n_schema_changed or n_schema_susp or dupes)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"changes={'true' if flag else 'false'}\n")
    print(f"[v{MONITOR_VERSION}] checked {len(sources)} sources; "
          f"{counts['changed'] + n_schema_changed} changed, {counts['suspect']} suspect, "
          f"{n_schema_susp} schema-suspect, {counts['manual']} manual, {counts['error']} errors"
          + (f", {len(dupes)} DUPLICATE-HASH group(s)" if dupes else "") + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())

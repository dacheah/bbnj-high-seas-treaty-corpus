"""
watch_sources.py -- Phase F source monitor.

Fetches each monitored source (monitoring/sources.json), reduces the page to
text, hashes it, and compares against the stored baseline. New or changed
sources are written to monitoring/last_report.md and the baseline is advanced.
Automation only WATCHES and queues; the maintainer judges (see docs/design).

Designed to run in GitHub Actions. Live fetching uses the standard library.
Run offline self-test with:  python3 watch_sources.py --selftest

Note on noise: index/news pages carry a volatile 'Latest news' area, so some
flags may be cosmetic. The reviewer triages; cadence is monthly. This is a
deliberately simple v1 that can be refined (e.g., section-scoped hashing).
"""
from __future__ import annotations
import hashlib, json, os, re, sys, datetime
from urllib.request import Request, urlopen

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SOURCES = os.path.join(REPO, "monitoring", "sources.json")
REPORT = os.path.join(REPO, "monitoring", "last_report.md")
UA = "provenance-corpus-monitor/0.1"


def to_text(raw: str) -> str:
    """Reduce HTML to comparable text: drop scripts/styles/tags, collapse space."""
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()


def content_hash(raw: str) -> str:
    return "sha256:" + hashlib.sha256(to_text(raw).encode("utf-8")).hexdigest()


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", errors="replace")


def classify(sources: list, hashes: dict) -> list:
    """Pure diff logic (offline-testable). hashes: name -> new_hash or 'ERROR:..'."""
    events = []
    for s in sources:
        h = hashes.get(s["name"])
        if h is None or str(h).startswith("ERROR"):
            events.append((s["name"], "error", s.get("last_sha256"), h))
        elif s.get("last_sha256") is None:
            events.append((s["name"], "baseline", None, h))
        elif h != s["last_sha256"]:
            events.append((s["name"], "changed", s["last_sha256"], h))
        else:
            events.append((s["name"], "unchanged", s["last_sha256"], h))
    return events


def selftest() -> int:
    sources = [
        {"name": "a", "url": "x", "last_sha256": "sha256:aaa"},
        {"name": "b", "url": "y", "last_sha256": None},
        {"name": "c", "url": "z", "last_sha256": "sha256:ccc"},
        {"name": "d", "url": "w", "last_sha256": "sha256:ddd"},
    ]
    hashes = {"a": "sha256:aaa", "b": "sha256:bbb", "c": "sha256:CHANGED", "d": "ERROR:timeout"}
    got = {n: st for n, st, _, _ in classify(sources, hashes)}
    expected = {"a": "unchanged", "b": "baseline", "c": "changed", "d": "error"}
    assert got == expected, f"selftest FAILED: {got}"
    assert content_hash("<p>hi</p>") == content_hash("<p>  hi  </p>"), "hash normalisation failed"
    print("watch_sources selftest: OK")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    data = json.load(open(SOURCES, encoding="utf-8"))
    sources = data["sources"]
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    hashes = {}
    for s in sources:
        try:
            hashes[s["name"]] = content_hash(fetch(s["url"]))
        except Exception as e:
            hashes[s["name"]] = f"ERROR:{type(e).__name__}"
    events = classify(sources, hashes)

    actionable = [e for e in events if e[1] in ("changed", "baseline", "error")]
    lines = [f"# Source monitor report — {now}", ""]
    for name, state, old, new in events:
        mark = {"changed": "🔶 CHANGED", "baseline": "🟦 baseline set", "error": "⚠️ fetch error",
                "unchanged": "✅ unchanged"}[state]
        lines.append(f"- **{name}** — {mark}")
        if state == "changed":
            lines.append(f"    - was `{old}`")
            lines.append(f"    - now `{new}`")
    lines += ["", "_Automation only watches and queues. A change here may be a genuinely new/"
              "amended instrument OR a cosmetic page update (e.g. news sidebar) — the maintainer "
              "triages. Nothing is ingested automatically._"]
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # advance baseline for successful fetches
    for s in sources:
        h = hashes[s["name"]]
        if not str(h).startswith("ERROR"):
            s["last_sha256"] = h
        s["last_checked"] = now
    json.dump(data, open(SOURCES, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    changed = any(st == "changed" for _, st, _, _ in events)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"changes={'true' if changed else 'false'}\n")
    print(f"Checked {len(sources)} sources; "
          f"{sum(1 for _,st,_,_ in events if st=='changed')} changed, "
          f"{sum(1 for _,st,_,_ in events if st=='error')} errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

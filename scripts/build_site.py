"""
build_site.py -- generate a static, self-contained browsable site from the repo.
Read-only and regenerable: the repository is the single source of truth; this
renders it into site/. No external dependencies. Every instrument page shows the
authoritative text AND its provenance; derived concept tags are clearly labelled.
"""
import glob, html, json, os, re
import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTH = os.path.join(REPO, "authoritative"); DER = os.path.join(REPO, "derived")
SITE = os.path.join(REPO, "site"); os.makedirs(SITE, exist_ok=True)
CFG = json.load(open(os.path.join(REPO, "site.json"), encoding="utf-8")) if os.path.exists(os.path.join(REPO, "site.json")) else {}
CORPUS_NAME = CFG.get("name", "Corpus")
CORPUS_TAGLINE = CFG.get("tagline", "A neutral, authoritative, structured, machine-readable record \u2014 built provenance-first. Every text carries its source, retrieval date, official citation, language, an authoritative-status flag, and a content hash; every change is a new dated version.")
SITE_GROUPS = CFG.get("groups")  # optional list of [document_type, label]; else auto-derived
_ci = json.load(open(os.path.join(DER, "concept-index.json"), encoding="utf-8"))
VOCAB, CINDEX = _ci["vocabulary"], _ci["index"]

def sl(cid): return "i_" + cid.replace("/", "_") + ".html"
def esc(s): return html.escape(str(s)) if s is not None else ""
def short(h): return esc(h[:16] + "…") if h else ""

def page(title, body, active=""):
    parts = []
    for k, href, label in [("home", "index.html", "Home"), ("concepts", "concepts.html", "Concepts"),
                           ("about", "about.html", "About &amp; provenance")]:
        cls = ' class="on"' if active == k else ''
        parts.append('<a href="' + href + '"' + cls + '>' + label + '</a>')
    nav = "".join(parts)
    return ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>" + esc(title) + " — " + esc(CORPUS_NAME) + "</title>"
            "<link rel=\"stylesheet\" href=\"style.css\"></head><body>"
            "<header><div class=\"wrap\"><a class=\"brand\" href=\"index.html\">" + esc(CORPUS_NAME) + "</a>"
            "<nav>" + nav + "</nav></div></header><main class=\"wrap\">" + body + "</main>"
            "<footer class=\"wrap\"><p>A neutral, provenance-first corpus. Generated from the "
            "repository by <code>scripts/build_site.py</code> — do not edit by hand. Our own contributions "
            "are CC&nbsp;BY&nbsp;4.0; source texts keep their own terms.</p></footer></body></html>")

def render_text(txt):
    out = []
    for para in txt.split("\n\n"):
        p = para.strip()
        if not p: continue
        if len(p) < 90 and re.match(r"^(Article|Principle|Guideline)\b|^[IVX]+\.|^[A-D]\.\s|^\d+\.\s+[A-Z][a-z]+", p):
            out.append("<h3>" + esc(p) + "</h3>")
        else:
            out.append("<p>" + esc(p) + "</p>")
    return "\n".join(out)

insts = []
for m in glob.glob(os.path.join(AUTH, "**", "metadata.yaml"), recursive=True):
    meta = yaml.safe_load(open(m, encoding="utf-8")); d = os.path.dirname(m)
    tp = os.path.join(d, "text.txt")
    meta["_text"] = open(tp, encoding="utf-8").read() if os.path.exists(tp) else ""
    cj = os.path.join(DER, meta["corpus_id"], str(meta["version_id"]), "concepts.json")
    meta["_concepts"] = json.load(open(cj, encoding="utf-8")) if os.path.exists(cj) else None
    insts.append(meta)

for meta in insts:
    cid = meta["corpus_id"]
    src_flag = (' &middot; <span class="ok">official source</span>' if meta.get("source_is_official")
                else ' &middot; <span class="warn">reproduction</span>')
    p = ['<aside class="prov"><h2>Provenance</h2><dl>']
    p.append("<dt>Official citation</dt><dd>" + esc(meta.get("official_citation")) + "</dd>")
    p.append('<dt>Source</dt><dd><a href="' + esc(meta.get("source_url")) + '">' + esc(meta.get("source_publisher")) + "</a>" + src_flag + "</dd>")
    p.append("<dt>Retrieved</dt><dd>" + esc(meta.get("retrieval_date")) + "</dd>")
    p.append("<dt>Authentic languages</dt><dd>" + esc(", ".join(meta.get("authentic_languages", []))) + "</dd>")
    p.append("<dt>Status</dt><dd>" + esc(meta.get("authoritative_status")) + " &middot; fidelity: <b>" + esc(meta.get("text_fidelity")) + "</b></dd>")
    p.append("<dt>Content hash</dt><dd><code>" + short(meta.get("content_hash")) + "</code></dd>")
    if meta.get("verification"):
        p.append("<dt>Verification</dt><dd>" + esc(meta["verification"].get("status")) + " — " + esc(meta["verification"].get("note")) + "</dd>")
    if meta.get("corrections"):
        p.append("<dt>Corrections</dt><dd>" + "<br>".join(esc(c["change"]) for c in meta["corrections"]) + "</dd>")
    p.append('</dl><p class="pn">' + esc(meta.get("provenance_note")) + "</p></aside>")
    prov = "".join(p)

    concepts_html = ""
    if meta["_concepts"] and meta["_concepts"].get("tags"):
        tr = []
        for t in meta["_concepts"]["tags"]:
            chips = " ".join('<a class="chip" href="concepts.html#' + esc(c) + '">' + esc(c) + "</a>" for c in t["concepts"])
            tr.append("<tr><td>" + esc(t["unit"]) + "</td><td>" + chips + "</td></tr>")
        concepts_html = ('<section class="derived"><h2>Concept tags <span class="tag">derived &middot; '
                         'unofficial &middot; model &middot; unreviewed</span></h2><table><thead><tr>'
                         "<th>Provision</th><th>Concepts</th></tr></thead><tbody>" + "".join(tr) + "</tbody></table></section>")

    eif = (" &middot; in force " + esc(meta["entry_into_force_date"])) if meta.get("entry_into_force_date") else ""
    body = ('<article><p class="crumb"><a href="index.html">Home</a> / ' + esc(meta.get("short_title", cid)) + "</p>"
            "<h1>" + esc(meta["title"]) + "</h1>"
            '<p class="sub">' + esc(meta.get("document_type")) + " &middot; adopted " + esc(meta.get("adoption_date") or "n/a")
            + eif + " &middot; <code>" + esc(cid) + "</code></p>" + prov
            + '<section class="auth"><h2>Authoritative text</h2>' + render_text(meta["_text"]) + "</section>" + concepts_html + "</article>")
    open(os.path.join(SITE, sl(cid)), "w", encoding="utf-8").write(page(meta.get("short_title", cid), body))

_types = []
for x in insts:
    dt = x.get("document_type") or "other"
    if dt not in _types: _types.append(dt)
GROUPS = [tuple(g) for g in SITE_GROUPS] if SITE_GROUPS else [(dt, dt.replace("_", " ").capitalize()) for dt in _types]
rows = ""
for dt, label in GROUPS:
    items = sorted([x for x in insts if x["document_type"] == dt], key=lambda x: str(x.get("adoption_date")))
    if not items: continue
    rows += "<h2>" + label + '</h2><ul class="list">'
    for x in items:
        rows += ('<li><a href="' + sl(x["corpus_id"]) + '">' + esc(x["title"]) + '</a> <span class="mini">'
                 + esc(x.get("adoption_date") or "") + " &middot; " + esc(x.get("text_fidelity")) + "</span></li>")
    rows += "</ul>"
home = ("<h1>" + esc(CORPUS_NAME) + "</h1><p class=\"lead\">" + esc(CORPUS_TAGLINE) + "</p><p><b>"
        + str(len(insts)) + "</b> instruments &middot; <b>" + str(sum(len(v) for v in CINDEX.values()))
        + "</b> concept-tagged provisions &middot; <a href=\"concepts.html\">browse by concept →</a></p>" + rows)
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(page("Home", home, "home"))

sec = ""
for c in VOCAB:
    entries = CINDEX.get(c, [])
    sec += '<h2 id="' + esc(c) + '">' + esc(c) + ' <span class="mini">(' + str(len(entries)) + ')</span></h2><p class="def">' + esc(VOCAB[c]) + "</p>"
    if not entries:
        sec += '<p class="mini">(no provisions tagged)</p>'; continue
    by = {}
    for e in entries:
        by.setdefault((e["short_title"], e["corpus_id"]), []).append(e["unit"])
    sec += '<ul class="list">'
    for (sh, cid), us in by.items():
        sec += '<li><a href="' + sl(cid) + '">' + esc(sh) + "</a>: " + esc("; ".join(us)) + "</li>"
    sec += "</ul>"
cpage = ('<h1>Browse by concept <span class="tag">derived &middot; unofficial &middot; model &middot; unreviewed</span></h1>'
         '<p class="lead">Neutral legal concepts and the provisions across the corpus that address each. Tags are a '
         "model pass awaiting human review; they describe what a provision is <i>about</i> and take no doctrinal "
         "position.</p>" + sec)
open(os.path.join(SITE, "concepts.html"), "w", encoding="utf-8").write(page("Concepts", cpage, "concepts"))

about = ("<h1>About &amp; provenance</h1><p class=\"lead\">A neutral legal-infrastructure resource — the "
         "authoritative structured record, organised by neutral concepts. Not advocacy for any "
         "doctrine.</p><h2>The one principle</h2><p>Provenance and version integrity override convenience, always. "
         "Every document carries source URL, retrieval date, official citation, jurisdiction, language, an "
         "authoritative-status flag, and a content hash, from its first commit; every change is a new dated version, "
         "never an overwrite.</p><h2>Two layers, kept apart</h2><p><b>Authoritative</b> = primary source texts in "
         "their authentic enacting language, with full provenance. <b>Derived</b> = machine- or human-generated "
         "structure, concept tags and summaries — unofficial, traceable, never presented as authoritative. The "
         "concept tags on this site are derived and await human review.</p><h2>Licensing</h2><p>Our own contributions "
         "(structure, concept tags, this site) are CC&nbsp;BY&nbsp;4.0. Source texts are not relicensed; each keeps "
         "its own terms, recorded per document.</p>")
open(os.path.join(SITE, "about.html"), "w", encoding="utf-8").write(page("About", about, "about"))

open(os.path.join(SITE, "style.css"), "w", encoding="utf-8").write(
":root{--ink:#1a1c20;--muted:#5b6270;--line:#e2e5ea;--bg:#fbfcfe;--accent:#1f4e79;--warn:#a8500f}\n"
"*{box-sizing:border-box}body{margin:0;font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}\n"
".wrap{max-width:820px;margin:0 auto;padding:0 20px}\n"
"header{border-bottom:1px solid var(--line);background:#fff}header .wrap{display:flex;align-items:center;justify-content:space-between;height:58px}\n"
".brand{font-weight:700;color:var(--accent);text-decoration:none}nav a{margin-left:18px;color:var(--muted);text-decoration:none}nav a.on,nav a:hover{color:var(--accent)}\n"
"main{padding:26px 20px 50px}h1{font-size:1.7rem;line-height:1.25;margin:.2em 0 .3em}h2{font-size:1.15rem;margin:1.6em 0 .4em;color:var(--accent)}\n"
"h3{font-size:1rem;margin:1.3em 0 .2em}a{color:var(--accent)}.lead{font-size:1.08rem;color:#33373d}\n"
".sub,.mini,.crumb,.def{color:var(--muted)}.sub{margin-top:-.3em}.mini{font-size:.85rem}.crumb{font-size:.85rem}\n"
"code{background:#eef1f6;padding:1px 5px;border-radius:4px;font-size:.85em}\n"
".list{list-style:none;padding:0}.list li{padding:.35em 0;border-bottom:1px solid var(--line)}\n"
"aside.prov{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:18px 0}\n"
"aside.prov h2{margin-top:.2em}dl{display:grid;grid-template-columns:170px 1fr;gap:4px 14px;margin:0}\n"
"dt{color:var(--muted);font-size:.86rem}dd{margin:0}.pn{color:var(--muted);font-size:.85rem;margin:.7em 0 0;border-top:1px dashed var(--line);padding-top:.6em}\n"
".ok{color:#1a7f37;font-weight:600}.warn{color:var(--warn);font-weight:600}\n"
".auth p{margin:.5em 0}.auth h3{color:var(--accent)}\n"
".derived{margin-top:26px;border-top:2px solid var(--line);padding-top:8px}\n"
".tag{font-size:.62rem;letter-spacing:.04em;text-transform:uppercase;background:#fdecec;color:#a11;padding:2px 7px;border-radius:20px;vertical-align:middle}\n"
"table{width:100%;border-collapse:collapse;font-size:.92rem}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}\n"
".chip{display:inline-block;background:#eef4fb;color:var(--accent);text-decoration:none;padding:1px 8px;border-radius:20px;font-size:.8rem;margin:2px 3px 2px 0}\n"
"footer{border-top:1px solid var(--line);color:var(--muted);font-size:.82rem;padding:18px 20px 40px;margin-top:30px}\n")
print("site files:", sorted(os.listdir(SITE)))

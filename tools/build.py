"""Builds mydiaryjournal.com from content/pages/*.json into site/.

Run: python tools/build.py
Each content file is one page built for one real search phrase (see tools/plan.json).
Bible verses are written in content as references only ({"verse": "Psalm 46:1"}); the text is
filled in here from the public domain King James Version, so no verse is ever typed by hand.
"""
import csv
import datetime as dt
import html
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, OUT, CONTENT = (os.path.join(ROOT, d) for d in ("src", "site", "content"))
SITE = "https://mydiaryjournal.com"
BRAND = "My Diary Journal"
TODAY = dt.date(2026, 10, 11)
VERSION = "11"  # cache buster for site.css and site.js

SECTIONS = {
    "Diary and journal tools (write online, private, no sign up)": "tools",
    "Journal prompts": "prompts",
    "Journal ideas": "ideas",
    "How to journal": "howto",
    "Journal types (what it is, how to, a page to fill in)": "types",
    "Templates and printables": "templates",
    "Diary": "diary",
    "Prayer, Bible and faith journaling (links to the app)": "faith",
}
HUB_OF = {"tools": "diary", "diary": "diary", "templates": "journal", "prompts": "journal",
          "ideas": "journal", "howto": "journal", "types": "journal", "faith": "prayer-journal"}
HUB_NAMES = {"diary": "Diary", "journal": "Journal", "prayer-journal": "Prayer journal"}
GROUP_NAMES = {"tools": "Write online", "diary": "Diary guides", "templates": "Templates", "prompts": "Journal prompts",
               "ideas": "Journal ideas", "howto": "How to journal", "types": "Kinds of journals", "faith": "Prayer and Bible journaling"}

BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
         "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalm", "Proverbs",
         "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
         "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew",
         "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
         "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon",
         "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"]

problems = []


def warn(slug, msg):
    problems.append(f"{slug or 'home'}: {msg}")


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def url(slug):
    return "/" if not slug else f"/{slug}/"


# ---------------------------------------------------------------- Bible

_kjv = None


def kjv():
    global _kjv
    if _kjv is None:
        _kjv = {}
        with open(os.path.join(ROOT, "tools", "t_kjv.csv"), encoding="utf-8") as f:
            for row in csv.DictReader(f):
                _kjv[(int(row["b"]), int(row["c"]), int(row["v"]))] = row["t"]
    return _kjv


def verse_text(ref):
    m = re.fullmatch(r"(.+?) (\d+):(\d+)(?:-(\d+))?", ref.strip())
    if not m:
        raise ValueError(f"Bad verse reference: {ref}")
    book = m.group(1).replace("Psalms", "Psalm")
    if book not in BOOKS:
        raise ValueError(f"Unknown book in: {ref}")
    b, c, v1 = BOOKS.index(book) + 1, int(m.group(2)), int(m.group(3))
    v2 = int(m.group(4) or v1)
    parts = []
    for v in range(v1, v2 + 1):
        t = kjv().get((b, c, v))
        if t is None:
            raise ValueError(f"Verse not found: {ref}")
        parts.append(re.sub(r"\s+", " ", re.sub(r"\{[^}]*\}", "", t)).strip())
    return " ".join(parts), f"{book} {c}:{v1}" + (f"-{v2}" if v2 != v1 else "")


# ---------------------------------------------------------------- text

def esc(s):
    return html.escape(str(s), quote=True)


def inline(s, slug=None, known=None):
    """Escapes text, then allows **bold** and [label](/internal-link/)."""
    out = esc(s)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)

    def link(m):
        label, href = m.group(1), html.unescape(m.group(2))
        if known is not None and href.startswith("/"):
            target = href.strip("/").split("#")[0]
            if target not in known:
                warn(slug, f"link to missing page {href}")
        return f'<a href="{esc(href)}">{label}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, out)


def plain(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)


def words(page):
    text = [page.get("intro", "")]
    for sec in page.get("sections", []):
        text.append(sec.get("h2", ""))
        for b in sec.get("blocks", []):
            for k, v in b.items():
                if isinstance(v, str):
                    text.append(v)
                elif isinstance(v, list):
                    text += [x if isinstance(x, str) else " ".join(map(str, x.values())) if isinstance(x, dict) else " ".join(x) for x in v]
                elif isinstance(v, dict):
                    text += [str(x) for x in v.values() if isinstance(x, str)]
    for f in page.get("faq", []):
        text += [f["q"], f["a"]]
    return len(" ".join(text).split())


# ---------------------------------------------------------------- pieces

FLOWER = ('<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true"><g fill="#E0909E"><ellipse cx="32" cy="18" rx="9" ry="13"/>'
          '<ellipse cx="32" cy="46" rx="9" ry="13"/><ellipse cx="18" cy="32" rx="13" ry="9"/><ellipse cx="46" cy="32" rx="13" ry="9"/></g>'
          '<circle cx="32" cy="32" r="6" fill="#D9A441"/></svg>')
NAV = [("/diary/", "Diary"), ("/journal-prompts/", "Journal prompts"), ("/prayer-journal/", "Prayer journal"), ("/journal-template/", "Templates")]
TAPES = ["var(--tape-rose)", "var(--tape-sage)", "var(--tape-gold)"]


def header(active=None):
    links = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == active else ""}>{t}</a>' for h, t in NAV)
    return f"""<header class="top">
  <div class="wrap">
    <a class="brand" href="/" aria-label="{BRAND} home">{FLOWER}<span class="script">{BRAND}</span></a>
    <nav class="main" aria-label="Main">{links}</nav>
    <details class="menu"><summary aria-label="Menu"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M4 12h16M4 17h16"/></svg></summary><nav aria-label="Menu">{links}<a href="/">Online diary</a></nav></details>
  </div>
</header>"""


FOOTER = f"""<footer>
  <div class="wrap">
    <span class="script">{BRAND}</span>
    <span>© {TODAY.year} {BRAND}<a href="/about/">About</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></span>
  </div>
</footer>"""


def tape(i, style=""):
    rot = [-3, 2, -2, 3][i % 4]
    return f'<div class="tape" style="--c: {TAPES[i % 3]}; transform: rotate({rot}deg);{style}"></div>'


def diary_html(title_ph="Dear diary,", hint="What happened today?", kind="diary", restore=True, rows=8):
    return f"""<div class="paper diary" data-kind="{esc(kind)}"{'' if restore else ' data-restore="false"'}>
  <div class="spine"></div><div class="margin"></div><div class="ribbon" aria-hidden="true"></div>
  {tape(1, " top:-16px; left:38%;")}
  <div class="page-head"><span class="eyebrow">Today</span><span class="hand date"></span></div>
  <input class="page-title" placeholder="{esc(title_ph)}" aria-label="Page title">
  <p class="diary-prompt hand" hidden style="font-size:24px; color: var(--soft); margin: 2px 0 6px"></p>
  <textarea class="lined" rows="{rows}" placeholder="{esc(hint)}" aria-label="Write here"></textarea>
  <div class="bar"></div>
  <div class="pages"></div>
</div>"""


def sheet_html(key, t, slug):
    fields = []
    for i, f in enumerate(t.get("fields", [])):
        fid = slugify(f["label"]) or f"f{i}"
        rows = int(f.get("lines", 3))
        fields.append(f"""  <div class="field"><label for="{key}-{fid}">{esc(f['label'])}</label>
    <textarea id="{key}-{fid}" class="lined" data-f="{fid}" rows="{rows}" style="--rows:{rows}" placeholder="{esc(f.get('hint', ''))}"></textarea></div>""")
    return f"""<div class="sheet" data-key="{esc(key)}">
  <div class="margin"></div>{tape(0, " top:-16px; left:40%;")}
  <div class="page-head" style="padding-right:0"><span class="eyebrow">{esc(t.get('eyebrow', 'Date'))}</span><input class="sheet-date" data-f="date" aria-label="Date" placeholder="____________"></div>
  <h2 class="sheet-name">{esc(t.get('name', 'My page'))}</h2>
{chr(10).join(fields)}
  <div class="bar no-print"><button class="btn primary" data-a="print" type="button">Print or save as PDF</button><button class="btn" data-a="clear" type="button">Clear</button><span class="saved">Saved on this device</span></div>
</div>"""


def block_html(b, slug, known, idx):
    if "p" in b:
        return f"<p>{inline(b['p'], slug, known)}</p>"
    if "h3" in b:
        return f"<h3>{inline(b['h3'], slug, known)}</h3>"
    if "ul" in b:
        return "<ul>" + "".join(f"<li>{inline(x, slug, known)}</li>" for x in b["ul"]) + "</ul>"
    if "ol" in b:
        return "<ol>" + "".join(f"<li>{inline(x, slug, known)}</li>" for x in b["ol"]) + "</ol>"
    if "prompts" in b:
        items = "".join(
            f'<li><span>{inline(p, slug, known)}</span><button class="btn write no-print" type="button" data-prompt="{esc(plain(p))}">Write</button></li>'
            for p in b["prompts"])
        start = int(b.get("start", 1))
        reset = f' style="counter-reset: p {start - 1}"' if start > 1 else ""
        return f'<ol class="prompts"{reset}>{items}</ol>'
    if "steps" in b:
        return '<ol class="steps">' + "".join(
            f"<li><strong>{inline(s['name'], slug, known)}</strong>{inline(s['text'], slug, known)}</li>" for s in b["steps"]) + "</ol>"
    if "example" in b:
        e = b["example"]
        return f"""<figure class="example" style="margin-left:0; margin-right:0">
  <span class="ex-label">{esc(e.get('label', 'Example'))}</span><span class="ex-date">{esc(e.get('date', ''))}</span>
  {f'<div class="ex-title">{esc(e["title"])}</div>' if e.get('title') else ''}
  <div class="ex-text">{esc(e['text'])}</div>
</figure>"""
    if "verse" in b:
        try:
            text, ref = verse_text(b["verse"])
        except ValueError as err:
            warn(slug, str(err))
            return ""
        return f'<figure class="verse" style="margin-left:0; margin-right:0">{tape(idx)}<blockquote>{esc(text)}</blockquote><cite>{esc(ref)} KJV</cite></figure>'
    if "tip" in b:
        return f'<div class="note"><p>{inline(b["tip"], slug, known)}</p></div>'
    if "table" in b:
        t = b["table"]
        head = "".join(f"<th>{esc(h)}</th>" for h in t["head"])
        rows = "".join("<tr>" + "".join(f"<td>{inline(c, slug, known)}</td>" for c in r) + "</tr>" for r in t["rows"])
        return f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    if "diary" in b:
        d = b["diary"] or {}
        return diary_html(d.get("title", "Dear diary,"), d.get("hint", "Write here"), d.get("kind", slug), restore=False, rows=d.get("rows", 8))
    if "template" in b:
        return sheet_html(b["template"].get("key", slug), b["template"], slug)
    if "starters" in b:
        cards = []
        for i, c in enumerate(b["starters"]):
            cards.append(f'<a class="card" href="#write" data-start="{esc(c.get("title", ""))}" data-hint="{esc(c.get("hint", ""))}">{tape(i)}<h3>{esc(c["name"])}</h3><p>{esc(c.get("text", ""))}</p></a>')
        return f'<div class="cards" style="margin:34px 0">{"".join(cards)}</div>'
    warn(slug, f"unknown block {list(b)}")
    return ""


APP_PANEL = """<section class="block" style="padding-top:24px"><div class="wrap">
  <div class="app">
    <div>
      <div class="eyebrow">Our Android app</div>
      <h2>Prayer Journal for Women</h2>
      <p>52 weeks of Bible verses, reflection and prayer. A prayer list, answered prayers and a page for every day.</p>
      <div class="row">
        <a class="play" href="/prayer-journal-for-women/"><svg width="22" height="24" viewBox="0 0 22 24" aria-hidden="true"><path d="M1 1l12 11L1 23c-.6-.3-1-1-1-1.7V2.7C0 2 .4 1.3 1 1z" fill="#34A853"/><path d="M17 8l-4 4 4 4 4-2.3c1.2-.7 1.2-2.7 0-3.4z" fill="#FBBC04"/><path d="M1 1l12 11 4-4L3.2.4C2.4-.1 1.6 0 1 1z" fill="#4285F4"/><path d="M13 12L1 23c.6.6 1.4.7 2.2.3L17 16z" fill="#EA4335"/></svg><span><small>Coming soon on</small>Google Play</span></a>
        <a href="/prayer-journal-for-women/">See the app</a>
      </div>
    </div>
    <div class="phones">
      <div class="phone a"><div class="tape" style="--c: var(--tape-sage); transform: rotate(4deg)"></div><img src="/assets/app-home.webp" alt="Prayer Journal for Women home screen with this week's Bible verse" width="540" height="1212" loading="lazy"></div>
      <div class="phone b"><div class="tape" style="--c: var(--tape-gold); transform: rotate(-3deg)"></div><img src="/assets/app-prayers.webp" alt="Prayer list with pinned and ongoing prayers" width="540" height="1212" loading="lazy"></div>
    </div>
  </div>
</div></section>"""

DIARY_CTA = """<div class="cta no-print"><div><div class="script">Write it down today</div><p>A free private diary that feels like paper. No sign up.</p></div><a class="btn primary" href="/">Open my diary</a></div>"""


def head(page, slug, schema):
    title = page["title"] if BRAND in page["title"] else f'{page["title"]} · {BRAND}' if len(page["title"]) <= 44 else page["title"]
    canonical = SITE + url(slug)
    og_img = SITE + "/assets/og.png"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(page['description'])}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{'website' if page.get('type') in ('hub', 'plain') else 'article'}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{esc(page['title'])}">
<meta property="og:description" content="{esc(page['description'])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FBF6EF">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="preload" href="/assets/dancing_script.ttf" as="font" type="font/ttf" crossorigin>
<link rel="preload" href="/assets/caveat.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="/assets/site.css?v={VERSION}">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>"""


def schema_for(page, slug, crumbs):
    canonical = SITE + url(slug)
    graph = [{
        "@type": "BreadcrumbList",
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + h} for i, (h, n) in enumerate(crumbs)],
    }]
    org = {"@type": "Organization", "name": BRAND, "url": SITE + "/"}
    if page.get("type") in ("hub", "plain"):
        graph.append({"@type": "WebPage", "name": page["h1"], "url": canonical, "description": page["description"]})
    else:
        graph.append({"@type": "Article", "headline": page["h1"], "description": page["description"], "url": canonical,
                      "mainEntityOfPage": canonical, "datePublished": TODAY.isoformat(), "dateModified": TODAY.isoformat(),
                      "author": org, "publisher": {**org, "logo": {"@type": "ImageObject", "url": SITE + "/assets/app-icon.webp"}},
                      "image": SITE + "/assets/og.png", "inLanguage": "en"})
    if page.get("faq"):
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": plain(f["q"]), "acceptedAnswer": {"@type": "Answer", "text": plain(f["a"])}} for f in page["faq"]]})
    steps = [s for sec in page.get("sections", []) for b in sec.get("blocks", []) for s in b.get("steps", [])]
    if steps and page.get("howto", True):
        graph.append({"@type": "HowTo", "name": page["h1"], "step": [
            {"@type": "HowToStep", "position": i + 1, "name": plain(s["name"]), "text": plain(s["text"])} for i, s in enumerate(steps)]})
    if page.get("type") == "tool" or page.get("app"):
        graph.append({"@type": "WebApplication", "name": BRAND, "url": SITE + "/", "applicationCategory": "LifestyleApplication",
                      "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}})
    return {"@context": "https://schema.org", "@graph": graph}


# ---------------------------------------------------------------- page

def render(page, slug, known, catalog):
    hub = page.get("hub") or HUB_OF.get(page.get("section"), "")
    crumbs = [("/", "Home")]
    if hub and hub != slug:
        crumbs.append((url(hub), HUB_NAMES[hub]))
    crumbs.append((url(slug), page.get("crumb") or page["h1"]))
    schema = schema_for(page, slug, crumbs)
    nav_active = {"diary": "/diary/", "prayer-journal": "/prayer-journal/"}.get(hub)
    if slug == "journal-prompts":
        nav_active = "/journal-prompts/"
    crumb_html = '<nav class="crumbs" aria-label="Breadcrumb">' + "<span>›</span>".join(
        f'<a href="{h}">{esc(n)}</a>' if i < len(crumbs) - 1 else f'<span aria-current="page" style="margin:0">{esc(n)}</span>'
        for i, (h, n) in enumerate(crumbs)) + "</nav>"

    secs = page.get("sections", [])
    ids, body = [], []
    for i, sec in enumerate(secs):
        sid = sec.get("id") or slugify(sec["h2"])[:48]
        ids.append((sid, sec["h2"]))
        body.append(f'<h2 id="{sid}">{inline(sec["h2"], slug, known)}</h2>')
        for j, b in enumerate(sec.get("blocks", [])):
            body.append(block_html(b, slug, known, i + j))
    toc = ""
    if len(ids) >= 4 and page.get("toc", True):
        toc = '<nav class="toc no-print" aria-label="On this page"><span class="eyebrow">On this page</span><ol>' + "".join(
            f'<li><a href="#{i}">{esc(plain(t))}</a></li>' for i, t in ids) + "</ol></nav>"

    top_tool = ""
    w = page.get("writer")
    if w:
        top_tool = f'<div id="write" style="margin: 6px 0 40px">{diary_html(w.get("title", "Dear diary,"), w.get("hint", "Write here"), w.get("kind", slug), restore=w.get("restore", False), rows=w.get("rows", 8))}</div>'
    tpl = ""
    if page.get("template"):
        tpl = f'<div id="write" style="margin: 6px 0 40px">{sheet_html(page["template"].get("key", slug), page["template"], slug)}</div>'

    hub_html = ""
    if page.get("type") == "hub":
        groups = {}
        for s, p in catalog.items():
            if s != slug and (p.get("hub") or HUB_OF.get(p.get("section"))) == slug:
                groups.setdefault(p.get("section"), []).append((s, p))
        parts = []
        for sec_key in ["tools", "diary", "prompts", "ideas", "howto", "types", "templates", "faith"]:
            if sec_key not in groups:
                continue
            items = "".join(f'<li><a href="{url(s)}">{esc(p.get("crumb") or p["h1"])}<small>{esc(p["description"][:110].rsplit(" ", 1)[0])}...</small></a></li>'
                            for s, p in sorted(groups[sec_key], key=lambda x: x[1].get("order", 100)))
            parts.append(f'<h2 id="{sec_key}">{GROUP_NAMES[sec_key]}</h2><ul class="hub-list">{items}</ul>')
        hub_html = "".join(parts)

    faq = ""
    if page.get("faq"):
        faq = '<h2 id="faq">Questions people ask</h2><div class="faq">' + "".join(
            f'<details><summary>{inline(f["q"], slug, known)}</summary><div><p>{inline(f["a"], slug, known)}</p></div></details>' for f in page["faq"]) + "</div>"

    related = ""
    rel = [r for r in page.get("related", []) if r in catalog and r != slug][:6]
    for r in page.get("related", []):
        if r not in catalog and r not in known:
            warn(slug, f"related page not in the plan: {r}")
    if rel:
        cards = "".join(f'<a class="card" href="{url(r)}">{tape(i)}<h3>{esc(catalog[r].get("crumb") or catalog[r]["h1"])}</h3><p>{esc(catalog[r].get("card", ""))}</p></a>'
                        for i, r in enumerate(rel))
        related = f'<section class="block no-print"><div class="wrap"><div class="eyebrow">Keep going</div><h2>More to read and write</h2><div class="cards">{cards}</div></div></section>'

    faith = hub == "prayer-journal"
    cta = "" if page.get("type") in ("plain",) or faith or page.get("type") == "tool" else DIARY_CTA
    byline = "" if page.get("type") in ("hub", "plain") else f'<div class="byline">By {BRAND} · Updated {TODAY.strftime("%B")} {TODAY.day}, {TODAY.year}</div>'

    return f"""{head(page, slug, schema)}
<body>
{header(nav_active)}
<main>
  <div class="wrap narrow">
    {crumb_html}
    <div class="art-head">
      <div class="eyebrow">{esc(page.get('eyebrow', ''))}</div>
      <h1>{esc(page['h1'])}</h1>
      <p class="lead">{inline(page['intro'], slug, known)}</p>
      {byline}
    </div>
    {top_tool}{tpl}
    {toc}
    <div class="prose">
      {chr(10).join(body)}
      {hub_html}
      {faq}
      {cta}
    </div>
  </div>
  {APP_PANEL if faith else ''}
  {related}
</main>
{FOOTER}
<script src="/assets/site.js?v={VERSION}" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------- checks

DASHES = re.compile("[–—]")


def check(page, slug, plan_row):
    s = slug
    t, d = page.get("title", ""), page.get("description", "")
    if not 25 <= len(t) <= 62:
        warn(s, f"title length {len(t)}")
    if not 110 <= len(d) <= 160:
        warn(s, f"description length {len(d)}")
    blob = json.dumps(page, ensure_ascii=False)
    if DASHES.search(blob):
        warn(s, "contains an em or en dash")
    if plan_row:
        kw = plan_row["keyword"]
        low = lambda x: x.lower()
        core = [w for w in kw.split() if len(w) > 2]
        if not all(w in low(t) for w in core[:3]):
            warn(s, f"title may not contain keyword '{kw}'")
        if not all(w in low(page.get("h1", "")) for w in core[:3]):
            warn(s, f"h1 may not contain keyword '{kw}'")
    n = words(page)
    minimum = {"plain": 120, "hub": 120}.get(page.get("type"), 700)
    if n < minimum:
        warn(s, f"only {n} words")
    if page.get("type") not in ("plain", "hub") and len(page.get("faq", [])) < 3:
        warn(s, "fewer than 3 FAQ answers")


# ---------------------------------------------------------------- main

def main():
    plan = json.load(open(os.path.join(ROOT, "tools", "plan.json"), encoding="utf-8"))
    plan_by_slug = {}
    for r in plan:
        s = "" if r["keyword"] == "online diary free" else slugify(r["keyword"])
        plan_by_slug[s] = {**r, "section_key": SECTIONS[r["section"]]}

    catalog = {}
    for name in sorted(os.listdir(os.path.join(CONTENT, "pages"))):
        if not name.endswith(".json"):
            continue
        try:
            page = json.load(open(os.path.join(CONTENT, "pages", name), encoding="utf-8"))
        except json.JSONDecodeError as e:
            warn(name, f"bad JSON: {e}")
            continue
        slug = page.get("slug", name[:-5])
        if slug in plan_by_slug and not page.get("section"):
            page["section"] = plan_by_slug[slug]["section_key"]
        catalog[slug] = page

    known = set(catalog) | {""} | {s for s in plan_by_slug}
    only = [a.split("=", 1)[1] for a in sys.argv if a.startswith("--only=")]
    only = set(only[0].split(",")) if only else None
    if "--check" in sys.argv:
        for slug, page in catalog.items():
            if only and slug not in only:
                continue
            check(page, slug, plan_by_slug.get(slug))
            render(page, slug, set(catalog) | {""} | {"diary", "journal", "prayer-journal"} | set(plan_by_slug), catalog)
        print(f"checked {len(only) if only else len(catalog)} pages")
        print(f"{len(problems)} problems:" if problems else "no problems")
        if problems:
            print("  " + "\n  ".join(problems))
        return
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)

    for slug, page in catalog.items():
        check(page, slug, plan_by_slug.get(slug))
        dest = os.path.join(OUT, slug) if slug else OUT
        os.makedirs(dest, exist_ok=True)
        with open(os.path.join(dest, "index.html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(render(page, slug, known, catalog))

    missing = [s for s in plan_by_slug if s and s not in catalog]

    # 404
    nf = {"title": "Page not found", "description": "This page is not here.", "h1": "This page is not here", "type": "plain",
          "intro": "The page may have moved. Try the [online diary](/) or the [journal prompts](/journal-prompts/)."}
    with open(os.path.join(OUT, "404.html"), "w", encoding="utf-8") as f:
        f.write(render(nf, "404", known, catalog).replace('<link rel="canonical"', '<meta name="robots" content="noindex"><link rel="canonical"'))

    # sitemap and robots
    urls = [""] + sorted(s for s in catalog if s)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for s in urls:
        sm.append(f"  <url><loc>{SITE}{url(s)}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>")
    sm.append("</urlset>")
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")
    open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

    # duplicate titles and descriptions
    for field in ("title", "description"):
        seen = {}
        for s, p in catalog.items():
            seen.setdefault(p.get(field, "").lower(), []).append(s)
        for v, ss in seen.items():
            if len(ss) > 1:
                problems.append(f"duplicate {field}: {', '.join(ss)}")

    print(f"built {len(catalog)} pages + home + 404 into site/")
    print(f"plan pages still to write: {len(missing)}")
    if "--missing" in sys.argv:
        print("  " + "\n  ".join(missing))
    if problems:
        print(f"{len(problems)} problems:")
        print("  " + "\n  ".join(problems))


if __name__ == "__main__":
    main()

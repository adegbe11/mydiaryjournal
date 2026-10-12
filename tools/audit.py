"""Audits the built site in site/: broken internal links, missing tags, duplicate titles, page weight.
Run after tools/build.py:  python tools/audit.py
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.h1, self.title, self.canon, self.desc, self.ld, self._in, self.imgs_no_alt = [], 0, "", "", "", [], None, 0

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self._in = "title"
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in = "ld"
        if tag == "link" and a.get("rel") == "canonical":
            self.canon = a.get("href", "")
        if tag == "meta" and a.get("name") == "description":
            self.desc = a.get("content", "")
        if tag == "img" and not a.get("alt"):
            self.imgs_no_alt += 1

    def handle_endtag(self, tag):
        self._in = None

    def handle_data(self, data):
        if self._in == "title":
            self.title += data
        elif self._in == "ld":
            self.ld.append(data)


def main():
    pages = {}
    for dirpath, _, files in os.walk(OUT):
        for f in files:
            if f == "index.html":
                rel = os.path.relpath(dirpath, OUT).replace("\\", "/")
                pages["/" if rel == "." else f"/{rel}/"] = os.path.join(dirpath, f)
    issues, titles, inbound = [], {}, {u: 0 for u in pages}
    for u, path in pages.items():
        raw = open(path, encoding="utf-8").read()
        p = Page()
        p.feed(raw)
        if p.h1 != 1:
            issues.append(f"{u}: {p.h1} h1 tags")
        if not p.canon.endswith(u):
            issues.append(f"{u}: canonical {p.canon}")
        if not p.desc:
            issues.append(f"{u}: no description")
        if p.imgs_no_alt:
            issues.append(f"{u}: {p.imgs_no_alt} images without alt")
        for block in p.ld:
            try:
                json.loads(block)
            except ValueError:
                issues.append(f"{u}: bad JSON-LD")
        titles.setdefault(p.title, []).append(u)
        if re.search("[–—]", re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)):
            issues.append(f"{u}: em or en dash in page")
        for href in p.links:
            if href.startswith("/") and not href.startswith("//"):
                target = href.split("#")[0].split("?")[0]
                if target.startswith("/assets/"):
                    continue
                if not target.endswith("/"):
                    target += "/"
                if target in pages:
                    if target != u:
                        inbound[target] += 1
                else:
                    issues.append(f"{u}: broken link {href}")
        kb = os.path.getsize(path) / 1024
        if kb > 220:
            issues.append(f"{u}: page is {kb:.0f} KB")
    for t, us in titles.items():
        if len(us) > 1:
            issues.append(f"duplicate title '{t}': {us}")
    orphans = [u for u, n in inbound.items() if n == 0 and u != "/"]
    print(f"{len(pages)} pages audited")
    print(f"orphans (no internal links in): {orphans if orphans else 'none'}")
    weakest = sorted(inbound.items(), key=lambda x: x[1])[:8]
    print("fewest inbound links:", ", ".join(f"{u} {n}" for u, n in weakest))
    print(f"{len(issues)} issues")
    for i in issues[: int(sys.argv[1]) if len(sys.argv) > 1 else 200]:
        print("  " + i)


if __name__ == "__main__":
    main()

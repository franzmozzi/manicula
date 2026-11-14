"""Assemble the single-file prototype in each language.

src/template.html is the shared shell. For every language it gets:
  src/content/<lang>.html  article body (datalists, blocks, guide) -> {{CONTENT}}
  src/i18n/<lang>.json     UI strings: {{t:key}} in the markup, "js" -> {{STRINGS}} for the script
  src/svg/*.svg            the two figures -> {{SVG_LEFT}}, {{SVG_RIGHT}}
Each language comes in two variants:
  full  index.html / it/index.html       control bar, outline overlay, status lines
  bare  barebone.html / it/barebone.html  only the layout; size and spacing come from the mark attributes
Variant-only parts are wrapped in <!--full-->…<!--/full--> / <!--bare-->…<!--/bare--> (HTML) or
/*full*/…/*/full*/ / /*bare*/…/*/bare*/ (CSS, JS), in the template and in the content files.
"""
import html
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = {   # first language is the default
    "en": {"full": "index.html", "bare": "barebone.html"},
    "it": {"full": "it/index.html", "bare": "it/barebone.html"},
    "de": {"full": "de/index.html", "bare": "de/barebone.html"},
}
REGION = re.compile(r"(?:<!--|/\*)(full|bare)(?:-->|\*/)\n?(.*?)(?:<!--|/\*)/\1(?:-->|\*/)\n?", re.S)


def variant(text: str, keep: str) -> str:
    """Keep the regions of variant `keep`, drop the other variant's."""
    return REGION.sub(lambda m: m.group(2) if m.group(1) == keep else "", text)


template = (ROOT / "src" / "template.html").read_text()
svgs = {name: (ROOT / "src" / "svg" / f"{name}.svg").read_text().strip() for name in ("left", "right")}


def rel(src: str, dst: str) -> str:
    """Relative link from page `src` to page `dst` (both relative to ROOT); works over file:// too."""
    return os.path.relpath(dst, os.path.dirname(src) or ".")


for lang, outs in PAGES.items():
    strings = json.loads((ROOT / "src" / "i18n" / f"{lang}.json").read_text())
    content = (ROOT / "src" / "content" / f"{lang}.html").read_text().rstrip()
    for kind, out in outs.items():
        page = variant(template, kind).replace("{{LANG}}", lang)
        page = page.replace("{{CONTENT}}", variant(content, kind))
        page = page.replace("{{STRINGS}}", json.dumps(strings["js"], ensure_ascii=False))

        default = next(iter(PAGES.values()))[kind]
        alternates = [f'<link rel="alternate" hreflang="{l}" href="{rel(out, p[kind])}">' for l, p in PAGES.items()]
        alternates.append(f'<link rel="alternate" hreflang="x-default" href="{rel(out, default)}">')
        page = page.replace("{{ALTERNATES}}", "\n".join(alternates))

        other = "bare" if kind == "full" else "full"
        links = [f'<a class="version-link" href="{rel(out, outs[other])}">{{{{t:{other}Link}}}}</a>']
        switch = []
        for l, p in PAGES.items():
            current = ' aria-current="page"' if l == lang else ""
            switch.append(f'<a href="{rel(out, p[kind])}" hreflang="{l}" lang="{l}"{current}>{l.upper()}</a>')
        links.append(f'<nav class="lang-switch" aria-label="{{{{t:langSwitch}}}}">{"".join(switch)}</nav>')
        page = page.replace("{{PAGE_LINKS}}", "".join(links))

        page = re.sub(r"\{\{t:(\w+)\}\}", lambda m: html.escape(strings[m.group(1)]), page)
        for name, svg in svgs.items():
            page = page.replace("{{SVG_%s}}" % name.upper(), svg)
        left = re.findall(r"\{\{[^}]*\}\}|<!--/?(?:full|bare)-->|/\*/?(?:full|bare)\*/", page)
        assert not left, f"{out}: unresolved placeholders {left}"

        dest = ROOT / out
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page)
        print(f"{out}: {len(page) // 1024} KB")

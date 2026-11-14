"""Assemble the two single-file pages.

src/template.html is the shared shell. It gets:
  src/content.html   article body (datalists, blocks, guide) -> {{CONTENT}}
  src/strings.json   UI strings: {{t:key}} in the markup, "js" -> {{STRINGS}} for the script
  src/svg/*.svg      the two figures -> {{SVG_LEFT}}, {{SVG_RIGHT}}
There are two variants:
  full  index.html     control bar, outline overlay, status lines
  bare  barebone.html  only the layout; size and spacing come from the mark attributes
Variant-only parts are wrapped in <!--full-->…<!--/full--> / <!--bare-->…<!--/bare--> (HTML) or
/*full*/…/*/full*/ / /*bare*/…/*/bare*/ (CSS, JS), in the template and in the content file.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = {"full": "index.html", "bare": "barebone.html"}
REGION = re.compile(r"(?:<!--|/\*)(full|bare)(?:-->|\*/)\n?(.*?)(?:<!--|/\*)/\1(?:-->|\*/)\n?", re.S)


def variant(text: str, keep: str) -> str:
    """Keep the regions of variant `keep`, drop the other variant's."""
    return REGION.sub(lambda m: m.group(2) if m.group(1) == keep else "", text)


template = (ROOT / "src" / "template.html").read_text()
content = (ROOT / "src" / "content.html").read_text().rstrip()
strings = json.loads((ROOT / "src" / "strings.json").read_text())
svgs = {name: (ROOT / "src" / "svg" / f"{name}.svg").read_text().strip() for name in ("left", "right")}

for kind, out in PAGES.items():
    other = "bare" if kind == "full" else "full"
    page = variant(template, kind)
    page = page.replace("{{CONTENT}}", variant(content, kind))
    page = page.replace("{{STRINGS}}", json.dumps(strings["js"], ensure_ascii=False))
    page = page.replace("{{PAGE_LINKS}}", f'<a class="version-link" href="{PAGES[other]}">{{{{t:{other}Link}}}}</a>')
    page = re.sub(r"\{\{t:(\w+)\}\}", lambda m: html.escape(strings[m.group(1)]), page)
    for name, svg in svgs.items():
        page = page.replace("{{SVG_%s}}" % name.upper(), svg)
    left = re.findall(r"\{\{[^}]*\}\}|<!--/?(?:full|bare)-->|/\*/?(?:full|bare)\*/", page)
    assert not left, f"{out}: unresolved placeholders {left}"

    (ROOT / out).write_text(page)
    print(f"{out}: {len(page) // 1024} KB")

# Manicula

Illustrated maniculae (☞, the pointing hands of medieval margins) for the web. Each figure hangs
into the page margin and points at a marked word, and the text flows around the figure's real
outline, line by line. The layout is recomputed live with [Pretext](https://github.com/chenglou/pretext).

![Two pointing figures in the margins of an article, with the text wrapping around their outlines](docs/desktop.png)

It is a self-contained prototype: every page is a single HTML file with no framework and no build
step at runtime. Open `index.html` in a browser, or see the live demo:
**[franzmozzi.github.io/manicula](https://franzmozzi.github.io/manicula/)**.

## Pages

There are two versions of the same article:

- **[Full](https://franzmozzi.github.io/manicula/)** (`index.html`) has a control bar for experimenting live. You can change each block's target, the
  column width, the figure size and the finger gap, and show the traced outline. A status line
  under each block names the line the finger points at, and warns when it misses it.
- **[Barebone](https://franzmozzi.github.io/manicula/barebone.html)** (`barebone.html`) has only the article, with the defaults hard-coded in the stylesheet. Size and
  spacing change only through the attributes of each block's mark.
- Each page links to the other one from its top bar.

## How it works

1. **Outline.** Each figure is an inline SVG. On load it is drawn to a canvas, and its alpha
   channel gives the figure's horizontal extent for every pixel row. The fingertip is the point
   that reaches furthest toward the text.
2. **Line by line.** Pretext breaks the text one line at a time. Each line gets the width that is
   left beside the figure's outline at that height, minus a small gap, so it never touches the
   ink. The part of the figure that hangs into the margin takes no width from the text.
3. **Aiming.** The figure moves vertically until the fingertip sits on the middle of the line
   that holds the marked words. Moving the figure changes the line breaks, so this is repeated
   until it converges. If the target line keeps jumping between two positions, a line break is
   forced just before the marked words, as a compositor would do.
4. **Reflow.** A `ResizeObserver`, the font loading and the 820 px breakpoint trigger a new
   layout. Below 820 px the figures shrink and hang less into the margin.

<p align="center">
  <img src="docs/outline.png" width="640" alt="The same paragraph with the traced outline, the fingertip line and the line boxes drawn as dashed overlays">
  &nbsp;
  <img src="docs/mobile.png" width="220" alt="The barebone page on a phone, with a smaller figure pointing at the marked words">
</p>

*Left: "Show outline" on the full page draws the traced outline, the fingertip and the line boxes.
Right: the barebone page at phone width.*

## Markup

Mark the spot directly in the text. Each block contains exactly one element with
`data-manicula`:

```html
<section class="manicula-block">
  <h2>A hand between the lines</h2>
  <p>… a warning to the <mark data-manicula>careless reader</mark> who …</p>
</section>
```

- Put it on a `<mark>` around the words to point at. The figure points at exactly that
  occurrence, even if the same words appear again in the paragraph.
- In a list, put it on the whole entry: `<li data-manicula>`.
- The paragraph can sit inside a `<blockquote>`. The text keeps the quotation's size and
  leading.

| Attribute | Values | Default |
|---|---|---|
| `data-side` | `left`, `right` (also `sx`, `dx`) | opposite of the previous block, starting on the left |
| `data-scale` | figure size in %, 25–200 | 100 |
| `data-gap` | px between fingertip and text, 0–60 | 14 (10 below 820 px) |
| `data-bleed` | px the figure hangs into the margin, 0 up to the page bleed | 85 (15 below 820 px) |

Out-of-range values are clamped. `data-bleed` can only pull a figure inward, so a figure never
leaves the viewport on a phone. On the full page, the "Maniculae" slider multiplies
`data-scale`, and `data-gap` overrides the "Finger gap" slider for that block.

```html
<mark data-manicula data-side="right" data-scale="65" data-gap="24" data-bleed="40">where to look</mark>
```

The script generates everything else: the text column, the figure, the outline overlay and the
status line.

## Accessibility and SEO

- **Original text.** It stays in the DOM in its original element (`<p>`, `<ul>`, `<blockquote>`),
  only visually hidden, so screen readers and crawlers read normal text with its `<mark>`.
- **Visible lines.** They are absolutely positioned `<span>`s inside an `aria-hidden` container,
  and the figures are decorative.
- **Fallback.** Without JavaScript or network, each block is a plain paragraph with the words
  highlighted.

## Dependencies

The pages load two external resources:

- [`@chenglou/pretext`](https://github.com/chenglou/pretext) `1.0.0` as an ES module from
  esm.sh. It does the line breaking; the pages use `prepareWithSegments`, `layoutNextLine` and
  `clearCache`.
- Source Sans 3 (400, 600) from Google Fonts.

For production, serve both from your own domain instead of the CDNs.

The browser needs ES modules, Canvas 2D, `ResizeObserver`, `document.fonts` and
`Intl.Segmenter`. Current Chrome, Edge, Firefox and Safari have all of them.

## Performance

Lighthouse on the GitHub Pages demo scores 100 in all four categories on desktop. On mobile it
gives 96 for Performance and 100 for the rest. The missing points most likely come from the two third-party
requests on the critical path, which weigh more on the throttled mobile profile:

- The Google Fonts stylesheet blocks rendering and adds two extra origins (`fonts.googleapis.com`
  for the CSS, `fonts.gstatic.com` for the files) before the text can be painted.
- Pretext is fetched from esm.sh. The pages already shorten this path: they `preconnect` to
  esm.sh, ask for the `?bundle` build, which resolves to one file instead of seven modules, and
  start it early with `modulepreload`. It still takes two requests to a third-party origin, and
  the text cannot flow around the figures until the module has arrived.

To reach 100 on mobile, serve both from the same origin as the pages:

1. Download Source Sans 3 as WOFF2, regular and semibold, ideally subset to the Latin
   characters used. Declare it with `@font-face` and `font-display: swap` inside the page's
   `<style>`, and add `<link rel="preload" as="font" type="font/woff2" crossorigin>` for both
   files. Then remove the Google Fonts `<link>` and `preconnect` tags.
2. Bundle `@chenglou/pretext@1.0.0` into one local ES module, for example with
   `npx esbuild --bundle --format=esm --minify`. Import it with a relative path and announce it
   with `<link rel="modulepreload">`.
3. Rebuild and run Lighthouse again with the mobile profile.

This also stops the demo from depending on third-party services and from sending them data
about its visitors.

## Development

The pages are generated from `src/` and committed, so the repository can be served as is, for
example with GitHub Pages.

```
src/template.html        shared shell: styles, control bar, layout engine
src/content.html         article, usage guide and target suggestions
src/strings.json         UI labels and the status-line strings used by the script
src/svg/left.svg         the two figures
src/svg/right.svg
tools/build.py           src/ -> index.html and barebone.html
tools/test/check.py      headless Chromium: drives controls and viewport, measures alignment
tools/test/sweep.py      tries every word and list entry as target at 375, 830 and 1280 px
```

The template holds placeholders: `{{CONTENT}}`, `{{t:key}}`, `{{STRINGS}}` and `{{SVG_LEFT}}` /
`{{SVG_RIGHT}}`. Parts that belong to one variant only are wrapped in `<!--full-->…<!--/full-->`
or `<!--bare-->…<!--/bare-->` in HTML, and in `/*full*/…/*/full*/` in CSS and JS.

```sh
python3 tools/build.py                          # rebuild both pages (standard library only)

# tests: need `chromium` on PATH and websocket-client
python3 -m venv .venv
.venv/bin/pip install -r tools/requirements.txt
.venv/bin/python -I tools/test/check.py                              # index.html
.venv/bin/python -I tools/test/check.py "file://$PWD/barebone.html"
.venv/bin/python -I tools/test/sweep.py 100 barebone.html           # figure size %, page
```

On a barebone page `check.py` runs only the viewport steps, because there are no controls.

## Known limitations

- Each block has one figure and one target.
- Large figures in narrow columns can leave no room beside the fingertip. The page then reports
  that the finger covers the whole column.
- In rare cases the finger lands one line off, for example with some list entries as target at
  phone width (`sweep.py` lists them).
- A target in the first lines of a block pushes the text down, because the figure cannot rise
  above the block.

## Credits

- Line breaking by [Pretext](https://github.com/chenglou/pretext) by Cheng Lou.
- Typeface: [Source Sans 3](https://fonts.google.com/specimen/Source+Sans+3) by Paul D. Hunt for
  Adobe.
- The figures were traced with [vtracer](https://github.com/visioncortex/vtracer) from a
  hand-drawn illustration.

## License

Released into the public domain under [the Unlicense](LICENSE): code, content, figures and
screenshots alike. The figures are caricatures of the author, who places them in the public
domain too. Pretext and Source Sans 3 are not part of this repository; they are loaded from
their CDNs under their own licenses (MIT and SIL Open Font License).

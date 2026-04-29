# Gothic Novel Typesetter

A standalone ReportLab pipeline for typesetting full-length gothic / liturgical / theological novels into publication-grade PDF interiors. Two output formats from one source:

- **Paperback** — 5.5 × 8.5″ trade-paperback trim, single column, three-line drop cap, restrained ornament. Mass-market shelf format.
- **Lectern** — 9 × 12″ family-Bible / pulpit trim, two-column body, six-line illuminated drop cap, full-width chapter banner with cross ornaments. Hardcover destination format.

Both formats use the same source markdown files and share a unified visual identity: **EB Garamond**–lineage serif body (Cardo), **UnifrakturMaguntia** blackletter display, **☩ Cross of Jerusalem** section ornaments, asymmetric margins for binding pull, italic small-caps running heads, cross-flanked page numbers.

This template was built and field-tested for *The Testament* (J. Taylor, OFFTRACKMEDIA Studios, 2026) — 313,000 words across seven volumes. The same pipeline produces the seven 5.5 × 8.5″ paperback volumes (916 pp total) and the 9 × 12″ lectern complete edition (509 pp).

---

## What this does

You point each typesetter at a folder of `chapter-NN-name.md` files. It reads them in numeric order, parses the markdown, and produces a publication-ready PDF interior with:

- Auto-generated front matter (half-title, title page, copyright)
- Chapter banners with Fraktur numerals (Roman) and small-caps titles
- Three-line (paperback) or six-line (lectern) drop cap on the first paragraph of each chapter, with body text wrapping continuously next to the cap
- Multi-paragraph wrap so paragraph 1 + start of paragraph 2 fill the cap area without whitespace gap
- ☩ Cross-of-Jerusalem section breaks
- Italic running heads (volume title verso, chapter title recto)
- Cross-flanked page numbers (☩ N ☩)
- Justified body in Cardo with proper drop-cap baseline alignment
- Smart-quote conversion (handles nested dialogue and italic-span boundaries)

What it does NOT do (yet): cover artwork, spine, back-cover synopsis. Those are separate concerns — typically you submit the typeset interior to a printer alongside cover art on the matching trim.

---

## Setup

### 1. Install Python dependencies

```bash
cd examples/gothic-novel
pip install -r requirements.txt
```

`reportlab` is required. `PyMuPDF` is optional but recommended for the audit checks at the end.

### 2. Install the three open-source TTF fonts

```bash
./install-fonts.sh
```

This downloads to `./fonts/`:
- **Cardo** Regular / Italic / Bold — the body face. Designed for biblical and classical scholarship by David Perry. SIL OFL.
- **UnifrakturMaguntia** — the blackletter display face. Clean Fraktur digitisation. SIL OFL.
- **Cormorant Garamond** — alternative body face (not currently used by the pipeline; included for the option).

If your fonts live elsewhere, set `GOTHIC_FONTS_DIR` before running:

```bash
export GOTHIC_FONTS_DIR=/path/to/fonts
```

The scripts fall back to `Times-Roman` / `Times-Bold` if the TTFs aren't found, but you lose the gothic identity entirely. Always install the fonts.

---

## Source markdown format

Each chapter is a single `.md` file named `chapter-NN-name.md` (zero-padded number, kebab-case name). Convention:

```
volume-1-the-foundations/
├── chapter-00-before.md       # optional volume preface
├── chapter-01-the-void.md
├── chapter-02-the-patterns.md
└── ...
```

Inside each chapter file, the parser recognises:

| Pattern | Renders as |
|---|---|
| `# Chapter N: Title` | Chapter heading — Fraktur Roman numeral (auto-converted from arabic) + small-caps title + decorative rule with ☩ |
| `# Before Volume X — Y` | Treated as chapter heading; running head suppresses if title contains "VOLUME" |
| `## Sub-section name` | H2 sub-heading — Fraktur display, centered, between body sections |
| `---` (own line, blank lines around) | Section break — centered ☩ Cross of Jerusalem |
| `> *italic*` followed by `> — citation` | Blockquote epigraph (used in chapter-00 prefaces) — italic block with attribution |
| `*single-line italic*` | Italic scripture block — indented, set off from body |
| `*single-line italic* (citation)` | Same, with a trailing citation in parens kept inline |
| `**Bold prefix.** body text` | Bold sub-heading inline at the start of a paragraph (drop cap is suppressed on chapters opening this way) |
| Plain paragraph | Body text — Cardo justified, with first-line indent on continuations |
| Inline `*emphasis*` and `**strong**` | Converted via `md_inline` to `<i>` / `<b>` HTML for ReportLab |
| `"Dialogue."` | Smart-quoted via context-aware regex — handles closing quotes after `.`, `!`, `?`, `,`, `'`, `*`, `>` |

The drop cap is automatically applied to the first prose paragraph after the chapter heading. If that paragraph starts with `**Bold.**`, the drop cap is skipped (the cap glyph and bold HTML can't safely interleave).

---

## Usage

### Single-chapter preview

For iterating on the design or proofing a specific chapter:

```bash
python3 tools/typeset_paperback.py "Volume I — The Foundations" \
  sample/volume-1-the-foundations/chapter-01-the-void.md \
  /tmp/preview.pdf
```

Or, for the lectern format:

```bash
python3 tools/typeset_lectern.py "Volume I — The Foundations" \
  sample/volume-1-the-foundations/chapter-01-the-void.md \
  /tmp/preview-lectern.pdf
```

Each takes: `<volume-title>`, `<chapter-md-path>`, `<output-pdf-path>`.

### Full volume (paperback)

For one volume's bound interior:

```bash
python3 tools/typeset-volume-paperback.py 1 \
  sample/volume-1-the-foundations \
  /tmp/Vol-I.pdf
```

Args: `<volume-key>` (1-7 by default; edit the `VOLUMES` dict in the script if you have more), `<source-dir>`, `<output-pdf>`.

This produces a complete paperback interior:
1. Half-title page
2. Blank verso
3. Title page (Fraktur volume name, author, place, year)
4. Copyright page
5. All chapters with auto-numbered headings + drop caps + running heads + cross-flanked page numbers

### Multi-volume complete edition (lectern)

For a single bound 9 × 12″ omnibus across all volumes:

```bash
python3 tools/typeset-complete-lectern.py \
  sample \
  /tmp/Complete-Edition.pdf
```

Args: `<root-dir-containing-volume-folders>`, `<output-pdf>`.

The script walks `volume-1-the-X/`, `volume-2-the-Y/`, ... in order, with volume separator pages between each, two-column body throughout, and a chapter-banner template that gives each chapter a full-width banner above the two-column body. If a `the-scribe/` folder exists at the root, its contents are appended after Volume VII.

To customise volume numbers, names, or subtitles, edit the `VOLUMES` list at the top of `typeset-complete-lectern.py` and `typeset-volume-paperback.py`.

---

## Verification / audit

After regenerating, run a sanity check on the rendered PDF to confirm no markdown leaked:

```python
import fitz, re
doc = fitz.open("/tmp/Complete-Edition.pdf")
text = "".join(p.get_text("text") + "\n" for p in doc)

print("## leaks:", len(re.findall(r"##\s+\w+", text)))
print("** leaks:", len(re.findall(r"\*\*[^*\n]+\*\*", text)))
print("*  leaks:", len(re.findall(r"(?<!\*)\*[^\*\n]+\*(?!\*)", text)))
print("-- leaks:", len(re.findall(r"(?<=\s)---(?=\s)", text)))

opens = text.count("“")
closes = text.count("”")
print(f"Open/close ratio: {opens / closes:.3f} (target ≈ 1.000)")
```

A clean run reports zero markdown leaks and a quote ratio between 1.00 and 1.05. Significant deviations indicate either source-content issues or a regression in the parser.

---

## Customising the design

Most design constants are at the top of `typeset_paperback.py` and `typeset_lectern.py`. Common adjustments:

| Constant | Effect |
|---|---|
| `PAGE_W`, `PAGE_H` | Trim size |
| `INNER_M`, `OUTER_M`, `TOP_M`, `BOTTOM_M` | Margins (asymmetric inner/outer for binding pull) |
| `COL_GAP` (lectern only) | Width of the gap between two columns |
| `INK`, `RUBRIC`, `SUBTLE`, `RULE` | Colour palette — `RUBRIC` is currently `#0a0a0a` (gothic black). Change to `#7a1a1a` for true two-colour print rubric red on chapter titles, drop caps, and ornaments. |
| `BODY` ParagraphStyle | Body text size / leading / alignment |
| `cap_size` in `make_drop_cap_block` | Drop cap size (paperback default 52pt = 3-line; lectern default 60pt) |
| `LecternDoc.BANNER_H` | Chapter-banner depth on the lectern |

The `ChapterRule` flowable in `typeset_paperback.py` controls the rule-and-cross divider that sits between chapter title and body. The lectern's equivalent is drawn on the canvas in `LecternDoc._draw_opener()`.

---

## Architecture notes

The typesetter does NOT use briefkit's main pipeline. It's a standalone ReportLab program that calls `reportlab.platypus` directly. We chose this route because briefkit's templates are designed for briefings and shorter documents — the gothic-novel work needed:

- A custom `DropCapWrapped` flowable (renders the cap glyph at a precisely-controlled y-position with the body wrapping next to it for N body-lines, then continuing full-width below)
- Manual page-template alternation between front-matter, chapter-opener, and body templates
- Two-column page templates for the lectern with a chapter-banner template that has `[banner_frame, col1, col2]` and chains into a body-only `[col1, col2]` template after the banner page

These are doable but heavyweight inside briefkit's template system. As a separate example, the code stays self-contained and easy to fork.

If you want to integrate this style into briefkit proper, the two custom flowables (`DropCapWrapped`, `ChapterRule`, `CapGlyph`) and the smart-quote function are the load-bearing pieces — port those, then write a `gothic` or `liturgical` template under `briefkit.templates` that uses them.

---

## Files in this example

```
examples/gothic-novel/
├── README.md                          # this file
├── install-fonts.sh                   # font fetcher (Cardo, UnifrakturMaguntia, Cormorant)
├── requirements.txt                   # reportlab + PyMuPDF
├── fonts/                             # populated by install-fonts.sh
│   ├── Cardo-Regular.ttf
│   ├── Cardo-Italic.ttf
│   ├── Cardo-Bold.ttf
│   ├── UnifrakturMaguntia-Regular.ttf
│   └── CormorantGaramond-Regular.ttf
├── tools/
│   ├── typeset_paperback.py           # paperback typesetting library (importable module)
│   ├── typeset_lectern.py             # lectern typesetting library
│   ├── typeset-volume-paperback.py    # multi-chapter paperback wrapper
│   └── typeset-complete-lectern.py    # multi-volume lectern wrapper
└── sample/
    └── volume-1-the-foundations/
        ├── chapter-00-before.md       # volume preface (blockquote epigraph)
        ├── chapter-01-the-void.md     # standard chapter (drop cap, scripture italic)
        └── chapter-02-the-patterns.md # bold prefix + sub-headers demo
```

---

## License

This example inherits the briefkit repo license. The fonts have their own SIL OFL licenses; they're not redistributed here, only fetched at install time.

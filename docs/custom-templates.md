# Custom Templates

A template is a Python class that subclasses `BaseBriefingTemplate`, builds the story (the list of ReportLab flowables), and declares a few traits. Everything else, from extraction and document IDs to page geometry, metadata, the guard rails, bookmarks and the atomic write, is done once by the base class. Templates do not override `generate()`; a subclass that does still works but gets a `DeprecationWarning`.

## A minimal template that runs

```python
# my_templates.py
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, Spacer

from briefkit.elements.toc import build_toc
from briefkit.generator import BaseBriefingTemplate
from briefkit.styles import safe_para
from briefkit.templates import register_template


class MemoBookTemplate(BaseBriefingTemplate):
    """Chapters with a plain table of contents and a page-number footer."""

    pdf_subject = "Memo Book"
    design_page_size = "Letter"                 # used unless layout.page_size is set
    design_margins_mm = {"top": 25, "bottom": 22, "left": 25, "right": 25}
    supports_variants = False                   # fixed-format: no domain variant sections

    def build_story(self, content):
        story = [Paragraph(content["title"], self.styles["STYLE_TITLE"]), Spacer(1, 6 * mm)]
        chapters = content.get("subsystems", [])
        story.extend(build_toc([(1, f"{i}. {sub['name']}") for i, sub in enumerate(chapters, 1)], brand=self.brand))
        story.append(PageBreak())
        for i, sub in enumerate(chapters, 1):
            story.append(safe_para(f"{i}. {sub['name']}", self.styles["STYLE_H1"]))
            flowables, dropped = self.render_body_blocks(sub["blocks"])
            story.extend(flowables)
            if dropped:
                self.note_truncation(sub["filename"], dropped)
            story.append(PageBreak())
        return story

    def header_footer(self, content):
        def footer(canvas, doc):
            canvas.saveState()
            canvas.setFont(self.brand.get("font_body", "Helvetica"), 8)
            canvas.drawCentredString(doc.pagesize[0] / 2, 12 * mm, f"Page {doc.page}")
            canvas.restoreState()

        return None, footer                     # nothing on the first page, the footer after it


register_template("memo-book", MemoBookTemplate)
```

Use it from Python:

```python
import copy

import my_templates  # noqa: F401  (registers "memo-book")
from briefkit.config import DEFAULTS, load_config
from briefkit.templates import get_template

cfg = load_config()               # or copy.deepcopy(DEFAULTS)
cfg["doc_ids"]["enabled"] = False
get_template("memo-book")("docs/my-topic", config=cfg, output_path="build/memo.pdf").generate()
```

From the command line, import the module before BriefKit runs, for example through a `sitecustomize.py` on `PYTHONPATH`, then `briefkit generate docs/my-topic --template memo-book`. There is no plugin directory that is scanned automatically.

## Traits

| Attribute | Default | Meaning |
|---|---|---|
| `pdf_subject` | `None` | PDF `/Subject`; `metadata.subject` in the config wins |
| `design_page_size` | `None` | Page size the template was designed for (`"A4"`, `"Letter"`, ...); used unless the user set `layout.page_size` |
| `page_size_lock` | `None` | A page size that always applies (covers drawn at absolute coordinates) |
| `orientation_lock` | `None` | `"landscape"` for templates that are landscape by construction |
| `design_margins_mm` | 25 / 22 / 20 / 20 | Margins for any side the user did not set in `layout.margins` |
| `margin_overrides_mm` | `{}` | Margins that apply whatever the user set |
| `supports_variants` | `True` | Whether domain variants may add sections; fixed-format templates say `False` |
| `assigns_doc_id` | `True` | Whether a document ID is assigned |

## Hooks, in the order `generate()` calls them

| Hook | Purpose |
|---|---|
| `extract_content()` | Returns the content dict (`title`, `overview`, `subsystems`, `terms`, `bibliography`, `metrics`, ...). Rarely overridden. |
| `assign_doc_id(content)` | Returns the document ID or `""`. |
| `page_geometry()` | Returns a `PageGeometry` (page size, margins, `content_width`, `frame_height`). Override only for unusual geometry. |
| `prepare(content)` | Runs after geometry and the doc ID are known; stash what your page callbacks need in `self.hf_ctx`. |
| `doc_kwargs(content)` | Extra keyword arguments for the document (subject, author, ...). |
| `build_story(content)` | The flowables. Use `self.render_blocks(blocks)` and `self.render_body_blocks(blocks)` for Markdown content, `self.content_width` for widths, `self.styles["STYLE_H1"]` and friends for styles. |
| `body_toc_entries(content)` | `[(level, text), ...]` for a template whose body sections carry their own numbering; `None` for the default. |
| `before_build(story, content)` | Last chance to edit the story; the default applies variants when `supports_variants`. |
| `header_footer(content)` | `(first_page_callback, later_pages_callback)`; `None` draws nothing. The default draws BriefKit's running head and foot from `self.hf_ctx`. |

The base class then appends `self._pending_back_cover`, runs the orphan-protection and empty-page guard rails, bookmarks every H1/H2/H3 paragraph for the PDF outline, and builds the document atomically.

## Section builders you can reuse

Methods on `BaseBriefingTemplate`: `build_executive_summary(content)`, `build_at_a_glance(metrics, content)`, `build_body(content)`, `build_cross_references(refs, labels)`, `build_index(terms)`, `build_bibliography(sources, source_type)`, `build_back_cover()`.

Element builders in `briefkit.elements`: `build_cover_page`, `build_classification_banner`, `build_toc`, `build_callout_box`, `build_pull_quote`, `build_metric_dashboard`, `build_data_table`, `build_comparison_table`, `build_bar_chart`, `build_timeline`, `build_back_cover`. Each takes `brand=` and `content_width=`.

Text helpers in `briefkit.styles`: `safe_para(text, style, already_escaped=False)` builds a paragraph that never raises on bad markup (pass `already_escaped=True` for text that came out of the extractor); `esc(text)` escapes a data string completely; `slugify(text)` gives a heading's anchor name.

## Honoring the universal controls

Read `project.skip_<section>` through `briefkit.templates._helpers.should_skip(self.config, "preface")` and omit the section; build optional sections before the TOC so the TOC lists only what exists. The empty-page guard rail removes blank pages left by a skipped section.

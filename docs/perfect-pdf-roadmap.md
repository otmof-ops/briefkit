# briefkit — Roadmap to Perfectly Formatted PDFs

**Deep-research report. 2026-04-08.**

This document is the synthesized output of a four-track audit of briefkit's
entire PDF production pipeline — typography, layout/flow, PDF output
integrity, and content extraction / config ergonomics — cross-validated
against direct code reading. Every finding is file-grounded; every fix is
concrete; every item is ranked by severity and effort.

The report is a **roadmap**, not a shopping list. Sections are ordered so
that earlier phases unblock later ones and each phase is individually
shippable.

---

## Executive summary

briefkit produces readable PDFs today. It does not produce **publication-grade**
PDFs. The gap between "readable" and "publication-grade" breaks down into
five systemic classes of defect:

1. **Regressions in the guard-rail post-process I just landed** — 23 of 29
   templates override `generate()` with their own `doc.build()`, bypassing
   the universal orphan-protection and empty-page-collapse hooks I added in
   `BaseBriefingTemplate.generate()`. The "universal" guard rails I shipped
   yesterday are in fact only applied to 6 templates.
2. **Silent-failure paths** — zero-subsystem extraction returns a clean
   6-page empty PDF with exit code 0; markdown links have their URLs
   stripped before they reach ReportLab; skip-flag typos silently do nothing;
   `_strip_inline` emits `<font>` HTML over un-escaped user text and can
   corrupt the ReportLab XML parser.
3. **Only the 14 PDF base fonts** — no TTF registered anywhere in the
   codebase (`grep -r registerFont` returns zero hits), which means
   (a) no font is actually *embedded*, (b) all body text is rendered in
   Adobe Helvetica, (c) any character outside WinAnsi becomes a tofu box,
   and (d) print houses will reject or substitute.
4. **PDF standard features are entirely absent** — no document outline /
   bookmarks, no clickable TOC, no clickable URLs or bibliography
   citations, no `/Lang`, no page labels (so Acrobat's "go to page 5" means
   physical page 5, not body page 5), no determinism (every run has a
   different `/CreationDate` and `/ID`), no PDF/A compliance.
5. **Markdown fidelity is a subset of a subset** — hand-rolled regex
   tokenizer with no CommonMark compliance, zero image support, no nested
   lists, no footnotes, no front matter, no setext headings, no math, no
   inline HTML passthrough, no autolinks.

The roadmap below fixes all five classes in six phases, roughly 3–5 weeks
of focused work for a single contributor. The first phase alone — "
Correctness bedrock", one to two days — is the single highest-leverage
unit of work in the project's lifetime.

### At-a-glance roadmap

| Phase | Focus | Severity | Effort |
|---|---|---|---|
| 0 | Critical regressions (fix today) | BLOCKER | 1 day |
| 1 | Correctness bedrock | BLOCKER + MAJOR | 1–2 days |
| 2 | Typography upgrade | MAJOR + polish | 2–3 days |
| 3 | Layout rigor | MAJOR + polish | 2–3 days |
| 4 | PDF standard compliance | MAJOR | 3–5 days |
| 5 | Content features | MAJOR + feature | 1–2 weeks |
| 6 | Developer ergonomics | MAJOR + polish | 1 week |

---

## Phase 0 — Critical regressions (fix immediately)

These are either regressions I introduced in the yesterday's universal
guard rails commit or latent correctness bugs that make briefkit silently
produce broken output.

### P0-1. Guard-rail post-process is bypassed by 23 of 29 templates

**Severity: BLOCKER. Effort: M (2–3 hours).**

Yesterday's commit `21adf1f` added
`BaseBriefingTemplate._protect_section_headings` and
`_collapse_empty_page_runs`, wired into the generate pipeline at
`src/briefkit/generator.py:~1089`. The post-process runs before
`doc.build(story)` **in the base class**. But 23 of 29 templates override
`generate()` and build their own `SimpleDocTemplate` + `doc.build(story)`,
so the base-class post-process never runs on them:

```
$ grep -l "def generate" src/briefkit/templates/*.py
book.py certificate.py contract.py datasheet.py deck.py
deep_research.py evaluation.py guide.py invoice.py letter.py
magazine.py memo.py minimal.py minutes.py newsletter.py
playbook.py policy.py proposal.py quote.py register.py
resume.py sop.py whitepaper.py
```

`grep -c "_protect_section_headings" src/briefkit/templates/*.py`
returns **zero hits in every template**. The "universal" guard rails
are in fact only applied to: `academic.py`, `briefing.py`, `manual.py`,
`report.py`, and any template that does not override `generate()`.

**Fix.** Add a `BaseBriefingTemplate._finalize_story(story)` method that
wraps the two post-processes, and refactor every template's `generate()`
override to call it immediately before `doc.build(story, ...)`. One-line
edit per template:

```python
story = self._finalize_story(story)
doc.build(story, onFirstPage=hf, onLaterPages=hf)
```

Better: lift the `SimpleDocTemplate` construction itself into the base
class as `self._render_pdf(story, content)`, so no template ever calls
`doc.build()` directly. This also unblocks Phase 4 (metadata,
determinism, page labels) — every PDF-building site is in one place.

### P0-2. Zero-subsystem silent success

**Severity: BLOCKER. Effort: S (1–2 hours).**

`src/briefkit/extractor.py:355-359` globs `[0-9][0-9]-*.md`; if the user
has a flat directory of `intro.md`, `chapter-one.md`, the glob returns
empty, `result["subsystems"] = []`, and the CLI (`cli.py:104-156`)
never inspects the subsystem count. A clean 6-page empty PDF is
produced and the exit code is 0. I hit this myself during the
testament work and spent 20 minutes debugging.

**Fix.** In `cmd_generate`, after `_extract_doc_set_content`, if
`subsystems == []` AND `orientation == ""` AND `overview == ""`, raise a
friendly error:

```
No content extracted from {path}. briefkit looked for:
  - 00-what-is-*.md
  - [0-9][0-9]-*.md   (configurable via content.numbered_doc_pattern)
  - README.md
Found: (list of files actually present).
See `briefkit generate --help`, or set content.numbered_doc_pattern in briefkit.yml.
```

Exit code 2. Wire into batch's `failed` counter.

### P0-3. Markdown link URLs are stripped before reaching ReportLab

**Severity: BLOCKER. Effort: S (30 minutes).**

`src/briefkit/extractor.py:48,67` — `_RE_MD_LINK = r'\[([^\]]+)\]\([^\)]*\)'`
then `s = _RE_MD_LINK.sub(r'\1', s)`. **Every `[text](url)` becomes
plain `text`; the URL is discarded.** Combined with
`src/briefkit/styles.py:166` — `_safe_text` allowed tag whitelist
`['b','i','u','br/','br','super','sub','strike']`, **no `link` tag, no
`a` tag** — even if you restored the URL, it would be escaped.

**Fix.**
1. `extractor.py:67` → emit `<link href="\2" color="...">\1</link>`
   using capture group 2.
2. `styles.py:166` → add `link` to the allowed-tag list; preserve
   `href` and `color` attributes during XML-escape restoration.
3. `styles.py:170` — the restorer regex
   `<font ([^&]+)>` uses `[^&]+` which **forbids ampersands in attribute
   values**. A restored `<link>` with query-string `&` would be silently
   dropped. Widen the class.

### P0-4. Raw `&`, `<`, `>` in markdown body can corrupt ReportLab XML

**Severity: BLOCKER. Effort: S (1 hour).**

`_strip_inline` (`extractor.py:52-68`) emits HTML (`<b>`, `<i>`,
`<font name="Courier">`) for ReportLab's Paragraph mini-XML parser
**without first escaping literal `&`, `<`, `>` in the surrounding
prose**. A paragraph like `Compare A & B with <foo>` will either crash
ReportLab's XML parser or render mangled. Escaping is applied only
inside inline-code spans, not in regular text.

**Fix.** Rewrite `_strip_inline` to emit a structured token list (or
use placeholder sentinels like `\x00B\x00...\x00/B\x00`), then produce
final XML in a single `_safe_text` pass that escapes text nodes and
substitutes sentinels with real tags. This also removes the comment
at `generator.py:302-322` where `_safe_para` is bypassed for code
blocks because of this same mess.

### P0-5. Skip-flag typos silently do nothing

**Severity: BLOCKER. Effort: S (30 minutes).**

`should_skip()` (`templates/_helpers.py:165-178`) **does** raise
`ValueError` on unknown section names — but only when a template
*asks* for that section. A user typo like `project.skip_prefece: true`
in `briefkit.yml` is loaded into config, no template ever queries
`skip_prefece`, and `_validate_config` (`config.py:141-243`) does not
inspect `project.skip_*` keys at all. The typo is silently accepted
and has zero effect. This is exactly the failure mode the helper was
designed to prevent.

**Fix.** In `_validate_config`, iterate `project` keys. For any key
starting with `skip_` that is not in `SKIPPABLE_SECTIONS`, append an
error:

```python
from difflib import get_close_matches
suggestion = get_close_matches(bad, SKIPPABLE_SECTIONS, n=1)
errors.append(
    f"Unknown skip flag {bad!r}. "
    f"Did you mean skip_{suggestion[0]}?" if suggestion else
    f"Unknown skip flag {bad!r}. Valid sections: {', '.join(SKIPPABLE_SECTIONS)}"
)
```

### P0-6. Cover title auto-shrink is dead code

**Severity: BLOCKER (for long titles). Effort: S (15 minutes).**

`src/briefkit/elements/cover.py:100-102` computes a shrunk
`title_font_size` in a while-loop, then `cover.py:104` renders the
title with the unmodified `styles["STYLE_TITLE"]` (28 pt). The local
variable is never read. A 100-character title overflows horizontally
and blows past `Spacer(1, 30*mm)`, pushing the rest of the cover
off-page.

**Fix.** Build a `_ps("CoverTitleDyn", fontSize=title_font_size,
leading=title_font_size*1.2, ...)` and use it in the Paragraph call.

### P0-7. "(unspecified)" placeholder ships in three templates

**Severity: MAJOR. Effort: S (10 minutes).**

`templates/guide.py:431`, `templates/deep_research.py:344`,
`templates/magazine.py:420` all set
`creator="(unspecified)"` on SimpleDocTemplate. This is visibly broken
placeholder text in the PDF producer metadata.

**Fix.** Delete the literal; inherit from the proper metadata helper
introduced in Phase 4.

---

## Phase 1 — Correctness bedrock

Correctness-class fixes that are independent of the typography /
layout / PDF-integrity work. Ship these before anything cosmetic.

### P1-1. Centralise `SimpleDocTemplate` construction

**Severity: MAJOR. Effort: M (3–5 hours).**

30+ call sites construct `SimpleDocTemplate` directly (`generator.py:1174`
plus one per template override). Metadata, determinism, page labels,
language, and encryption all need to be set at this single point. As
long as each template constructs its own, any fix applied in one place
has to be duplicated 30 times and will regress.

**Fix.** Add `BaseBriefingTemplate._build_doc(content) -> SimpleDocTemplate`
returning a fully configured document with `invariant=True`,
`title/author/subject/keywords/creator/producer/lang` from
config, page size and margins from layout config. Replace every inline
construction with `doc = self._build_doc(content)`. This change is
mechanical but touches 30 files; do it in one PR.

### P1-2. Make `--dry-run` actually run extraction

**Severity: MAJOR. Effort: S (2 hours).**

`cli.py:143-145` — current `--dry-run` prints `(dry-run — no file written)`
and returns 0 **without running extraction**. It is a stub.

**Fix.** In dry-run mode: call `_extract_doc_set_content`, build the
story (but skip `doc.build`), then print:

```
Template: book (preset: royal)
Page size: A4 portrait
Level: 3
Subsystems: 10 (23,966 words)
Tables: 142
Terms: 40
Bibliography entries: 0
Sections to render (after skip_* filters):
  [x] Half-title
  [ ] Preface        (skipped: project.skip_preface)
  [x] TOC (10 entries)
  [x] Chapters (10)
  [ ] Colophon       (skipped: project.skip_colophon)
Total flowables: 402
Estimated pages: 74
```

This is the single most-valuable CI/debug affordance and currently
does not exist.

### P1-3. Introduce `logging` and retire ad-hoc `print`

**Severity: MAJOR. Effort: M (4–6 hours).**

Grep shows only `print(..., file=sys.stderr)` across `cli.py`,
`extractor.py:610`, `config.py`. There is no
`logging.getLogger("briefkit")`. `--verbose` exists but only affects
traceback printing on exceptions. There is no way to capture logs to
a file for CI triage.

**Fix.** Add `briefkit/_log.py` with a single `getLogger("briefkit")`,
map `--quiet` / `--verbose` to log level, add `--log-file PATH`.
Replace every `print` with `log.info/warn/error`. Cost is mostly
mechanical; the payoff is that every subsequent observability need
(extraction stats, flowable counts, sub-agent timing) has a place to
go.

### P1-4. Config schema validation with closest-match suggestions

**Severity: MAJOR. Effort: S–M (2–4 hours).**

Related to P0-5 but wider. `_validate_config` only inspects a
hand-picked subset (`page_size`, hex colors, ints, paths). Typos
anywhere else — `tempalte:`, `brnd:`, `licens:`, `contant:` — silently
create sibling keys and the real section keeps defaults.

**Fix.** Validate top-level keys against `set(DEFAULTS.keys())`,
recursively walk nested keys against the schema, raise with
`difflib.get_close_matches` suggestions. Small hand-rolled walker is
fine; jsonschema is overkill for this surface.

### P1-5. Drop `pyproject.toml` from root markers

**Severity: MAJOR. Effort: S (10 minutes).**

`config.py:273` — `_ROOT_MARKERS = ("briefkit.yml", "briefkit.yaml",
".briefkit", "pyproject.toml")`. Consequence: **any Python project
looks like a briefkit root**. briefkit will silently use defaults
instead of warning "no briefkit.yml found here".

**Fix.** Drop `pyproject.toml`. If none of the three briefkit-specific
markers is found, return `None` and force the caller to either pass
`-c` or print a clear "no briefkit.yml discovered" message.

### P1-6. Clear the `functools.lru_cache` on `find_project_root`

**Severity: POLISH. Effort: S (10 minutes).**

`config.py:287` — `@lru_cache(maxsize=128)` persists for the process
lifetime. In tests / watch mode, creating a new `briefkit.yml` won't
be picked up.

**Fix.** Expose `clear_cache()` and call it from the watch-mode
scaffolding when it lands.

---

## Phase 2 — Typography upgrade

### P2-1. Widow / orphan control on every paragraph style

**Severity: BLOCKER (one line away from being fixed). Effort: S (15 min).**

`styles.py:224-239` `_ps()` defaults set only
`fontName/textColor/spaceAfter/spaceBefore/leading`. **None of the 17
named styles set `allowWidows` or `allowOrphans`.** ReportLab defaults
are `allowWidows=1, allowOrphans=0` — widows are *permitted*. Last
lines of paragraphs strand at page tops.

**Fix.** Add `"allowWidows": 0, "allowOrphans": 0` to `_ps` defaults.
Single edit, immediate visible improvement.

### P2-2. Embed real fonts

**Severity: BLOCKER. Effort: M (4–6 hours).**

`grep -r "registerFont\|TTFont" src/briefkit/` — **zero hits**.
`DEFAULT_BRAND` (`styles.py:36-39`) hardcodes Helvetica everywhere.
`_SAFE_FONTS` (`styles.py:49-53`) is a frozen allowlist of the 14 PDF
base fonts only. The consequences: (a) no font is actually embedded,
(b) print houses will reject / substitute, (c) any non-Latin character
becomes a tofu box, (d) the output looks like a 1995 Word document.

**Fix.** Create `src/briefkit/fonts.py` with a `register_default_fonts()`
function. Ship an SIL-OFL family under `src/briefkit/assets/fonts/`:

- **Body serif**: Source Serif 4 (OFL)
- **Sans**: Inter (OFL)
- **Monospace**: JetBrains Mono (OFL)

Register via `pdfmetrics.registerFont(TTFont(...))` plus
`pdfmetrics.registerFontFamily(...)` for bold/italic/bold-italic
mapping so `<b>` / `<i>` resolve correctly. Call from
`BaseBriefingTemplate.__init__` before `_build_styles_cached`. Update
`DEFAULT_BRAND` to point at the new family names. Widen `_SAFE_FONTS`
to read from `pdfmetrics.getRegisteredFontNames()` at runtime.

This is the single biggest perceptual jump.

### P2-3. Baseline grid (4 pt rhythm)

**Severity: MAJOR. Effort: S (1 hour).**

`styles.py:273-425` — leadings are 34, 22, 18, 16, 15, 14, 13, 12, 11,
9. spaceBefore 18, 14, 10, 0. spaceAfter 12, 8, 6, 4, 2, 0. No common
divisor.

**Fix.** Adopt a 4-pt baseline. Body = 10/14. H3 = 12/16. H2 = 14/20.
H1 = 18/28. Title = 28/36. All spaceBefore/spaceAfter multiples of 4.
Document at the top of `styles.py`.

### P2-4. Line length (measure)

**Severity: MAJOR. Effort: S (30 minutes).**

`styles.py:85` — A4 with 20 mm side margins = 170 mm content width.
10-pt Helvetica averages ~96 characters per line. Professional
typography targets 45–75. Whitepaper at 11 pt is ~88.

**Fix.** Bump body to 11/16 and widen margins to 25 mm → ~70 cpc.
Touches `styles.py:81-86` and `STYLE_BODY`.

### P2-5. Smart punctuation

**Severity: MAJOR. Effort: M (2–3 hours).**

Zero references to `\u2019`, `\u2014`, "smart", "curly" in the repo.
Every straight quote, apostrophe, double-dash flows through unchanged.

**Fix.** Add `_smartypants(s)` to `extractor.py`:

```python
s = re.sub(r"(?<=\w)'(?=\w)", "\u2019", s)      # apostrophes
s = re.sub(r"(?<!\w)'(?=\w)", "\u2018", s)      # opening single
s = re.sub(r"(?<=\w)'(?!\w)", "\u2019", s)      # closing single
s = re.sub(r'(?<!\w)"(?=\w)', "\u201c", s)      # opening double
s = re.sub(r'(?<=\w)"(?!\w)', "\u201d", s)      # closing double
s = s.replace("---", "\u2014").replace("--", "\u2013")
s = s.replace("...", "\u2026")
s = re.sub(r"(\b[A-Z])\.\s+([A-Z][a-z])", r"\1.\u00a0\2", s)  # J. Smith
s = re.sub(r"(\d)\s*(mm|cm|kg|MHz|GHz|%|°)", r"\1\u202f\2", s)  # numbers + units
```

Run *after* link/code stripping but *before* inline markdown, with
code spans protected via sentinels.

### P2-6. Hyphenation + justification toggle

**Severity: MAJOR. Effort: S (1 hour).**

ReportLab supports `hyphenationLang` + `embeddedHyphenation=1` if
`pyphen` is installed. briefkit declares no Pyphen dependency. Only
`whitepaper.py:283` uses `alignment=TA_JUSTIFY` and ships without
hyphenation — **guaranteed rivers** in the one justified template.

**Fix.**
1. Add `pyphen` to `pyproject.toml` `[project.optional-dependencies]
   typography`.
2. In `_ps()` defaults add `"hyphenationLang": "en_US",
   "embeddedHyphenation": 1, "uriWasteReduce": 0.3`.
3. Provide `STYLE_BODY_JUSTIFIED`.
4. Graceful fallback when pyphen import fails.

### P2-7. List-item hanging indent

**Severity: MAJOR. Effort: S (20 minutes).**

`generator.py:295-300` builds `f"{bullet}{text}"` as a flat string.
`STYLE_LIST_ITEM` (`styles.py:436-444`) has `leftIndent=12` but no
`firstLineIndent=-12`. Wrapped lines hang *under the bullet*.

**Fix.** `STYLE_LIST_ITEM`: `leftIndent=18, firstLineIndent=-12,
bulletIndent=0`. Render with
`<bullet>&bull;</bullet>text` markup so Paragraph handles the hang.

### P2-8. Chapter-aware running heads

**Severity: MAJOR. Effort: M (3–4 hours).**

`elements/header_footer.py:39-50` — the header callback draws
unconditionally on every page. `_hf_state["section"]` is set once per
document, never per chapter. There is no verso/recto distinction, no
chapter-opening suppression, no per-page chapter-title lookup.

**Fix.** Extend `_hf_state` with `chapter_starts: set[int]` and
`chapter_titles: dict[int, str]`. In the header callback, early-return
the rule drawing when `doc.page in chapter_starts`; look up the running
head via `max(p for p in chapter_titles if p <= doc.page)`. For
verso/recto, branch on `doc.page % 2` and alternate the folio
position. Templates push chapter-start page numbers into `_hf_state`
from their chapter loop.

### P2-9. Code block and blockquote orphan protection

**Severity: POLISH. Effort: S (20 minutes).**

`generator.py:302-326` returns code/blockquote flowables individually.
A 2-line code block can split mid-line.

**Fix.** Wrap in `KeepTogether([...])` when content height is
predictable (< 1500 chars). Two one-line edits at `generator.py:319`
and `:326`.

### P2-10. `_safe_text` XML-escape bug with `&` in font attributes

**Severity: MAJOR. Effort: S (rolled into P0-4).**

`styles.py:170` restorer regex `<font ([^&]+)>` forbids `&` in
attributes. A font tag whose attributes were escaped to contain
`&quot;` or `&amp;` is silently dropped. Fix the regex when doing
P0-4.

---

## Phase 3 — Layout rigor

### P3-1. Universal table `wordWrap` + `splitByRow`

**Severity: MAJOR. Effort: S (30 minutes).**

`elements/tables.py:81,171` build cells via `_safe_para(cell,
STYLE_TABLE_BODY)`. `STYLE_TABLE_BODY` (`styles.py:341-349`) has no
`wordWrap`. Mitigation in `_safe_text` inserts zero-width spaces only
on runs > 60 chars; a 40-char URL in a 25-mm column still overflows.
`Table(..., splitByRow=1)` is never set; rows taller than the page
silently overflow.

**Fix.** Add `wordWrap="CJK"` to `STYLE_TABLE_BODY`/`STYLE_TABLE_HEADER`.
Add `splitByRow=1` to every `Table(...)` in `elements/tables.py`.
Truncate cell text > 1500 chars defensively.

### P3-2. Column-width clamp order

**Severity: MAJOR. Effort: S (15 minutes).**

`tables.py:93` applies `col_widths = [max(w, 15*mm) for w in col_widths]`
**after** rescaling. For a 12-column table, 12 × 15 = 180 mm > 170 mm
content width → right-edge clip.

**Fix.** Clamp first, then redistribute to fit content width.

### P3-3. Content-aware column widths

**Severity: MAJOR. Effort: M (2–3 hours).**

`tables.py:86` sizes columns from **header text only**. A "Qty"
header with 200-character body cells gets a 15 mm column; body wraps
to many lines.

**Fix.** Sample max body cell width per column (cap at 40 % of content
width); rebalance.

### P3-4. Code-block overflow

**Severity: BLOCKER. Effort: M (2–3 hours).**

`generator.py:302-322` converts spaces in code blocks to
`&nbsp;` (non-breaking). `STYLE_CODE` has no `wordWrap`, no
`splitLongWords`. A 200-character source line runs straight through
the right margin, off the page, and may clip the footer rule.

**Fix.** Hard-wrap source lines at ~85 chars before substituting
`&nbsp;`. Set `wordWrap="CJK"` and convert *leading-space runs* only
(preserve indentation, let trailing text wrap normally).

### P3-5. Lists: orphans and nesting

**Severity: MAJOR. Effort: M (3–4 hours).**

`generator.py:295-300` emits each item as an independent Paragraph.
No `keepWithNext` chaining, no nested lists (the parser has no `level`
field), no `ListFlowable` grouping.

**Fix.** In `render_blocks`, accumulate consecutive `list_item` blocks
into a single group and emit `KeepTogether` if total height < 0.4 ·
page; otherwise set `keepWithNext=True` on all but the last. Add a
`level` field to the parser for nesting. Use ReportLab `ListFlowable`
+ `ListItem`.

### P3-6. Callouts not `KeepTogether`'d at call sites

**Severity: MAJOR. Effort: S (15 minutes).**

`elements/callout.py:37-38` explicitly tells callers to wrap in
`KeepTogether`. But the 6+ call sites in `generator.py` (lines 326,
408, 478, 512, 681, ...) all append bare. A 6-line callout near the
page bottom splits and leaves half a colored left border on the
previous page.

**Fix.** Wrap inside `build_callout_box` itself with a
`KeepTogether` and a graceful-split fallback for boxes > 0.6 · page.

### P3-7. Caption pinning under tables and figures

**Severity: MAJOR. Effort: S (15 minutes).**

`elements/tables.py:58-60,109` — caption is a separate Paragraph
emitted *before* the Table. Caption can strand alone at the bottom of
a page with the table on the next.

**Fix.** Set `keepWithNext=True` on `STYLE_CAPTION`
(`styles.py:351-359`) *or* wrap caption + table in `KeepTogether`.

### P3-8. `CONTENT_WIDTH` is a module constant assuming A4

**Severity: MAJOR. Effort: M (3–4 hours).**

`styles.py:85` — `CONTENT_WIDTH = 170 * mm`. All element builders
default `cw = content_width or CONTENT_WIDTH`. On Letter (216 mm
wide, content ≈ 176 mm), the 170 mm default leaves a 6 mm white strip
on the right of every callout and table. 24 templates don't forward
`content_width=` to their element calls.

**Fix.** Kill the module constant. Require `content_width` argument,
or read from a thread-local / instance attribute set in
`BaseBriefingTemplate.__init__`. Audit every element call site.

### P3-9. Dashboard can overflow into the footer

**Severity: MAJOR. Effort: S (15 minutes).**

`elements/dashboard.py:44` returns a fixed 60-mm-tall Drawing. No
splitting, no `KeepInFrame`. If it lands 40 mm above page bottom it
overflows into the footer area.

**Fix.** Precede with `CondPageBreak(65*mm)` or wrap in `KeepInFrame`.

### P3-10. Footer bottom-margin clamp

**Severity: MAJOR. Effort: S (15 minutes).**

`header_footer.py:90` draws the copyright footer at `doc.bottomMargin
- 7.5 mm` from page bottom. If a user sets `margins.bottom: 10` (mm)
in config, the copyright lands at y = 2.5 mm — inside most printers'
no-print zone.

**Fix.** Enforce `bottomMargin >= 18 * mm` at layout resolution, or
scale footer offsets proportionally.

### P3-11. Cover robustness (Spacer→FrameBreak)

**Severity: MAJOR. Effort: M (2 hours).**

`cover.py:97,167,188` use fixed `Spacer(1, 30*mm)` etc. On Letter
(279 mm tall vs A4 297 mm) or with small `topMargin`, the cover's
footer bar can be pushed onto page 2, creating an empty page 2 with
just the footer.

**Fix.** Use `KeepInFrame` for the entire cover layout, or replace
fixed Spacers with `FrameBreak`.

---

## Phase 4 — PDF standard compliance

### P4-1. PDF document outline (bookmarks)

**Severity: BLOCKER. Effort: M (3–4 hours).**

Grep for `bookmarkPage`, `addOutlineEntry`, `outlineLevel`,
`bookmarkName`, `notifyBookmark` across the entire repo returns
**zero hits**. Every briefkit PDF has an empty sidebar in Acrobat /
Preview.

**Fix.** In `styles.py` add `outlineLevel=0/1/2` to STYLE_H1/H2/H3.
In `render_blocks`, emit each heading with a `<a name="sec-{slug}"/>`
anchor and call `doc.canv.bookmarkPage("sec-{slug}")` via a custom
Flowable, then `doc.addOutlineEntry(text, "sec-{slug}", level=N)`. Use
`slugify(heading_text)` for the name.

### P4-2. Clickable TOC

**Severity: BLOCKER. Effort: M (2–3 hours, after P4-1).**

`elements/toc.py:60` renders text-only Paragraphs with no `<link>`
tag. The TOC is not clickable.

**Fix.** Wire each entry's text through `<link href="#sec-{slug}">...</link>`,
matching bookmarks from P4-1. While you're there, add dot leaders
and real page numbers via ReportLab's two-pass TOC mechanism
(`BaseDocTemplate.multiBuild` + `TableOfContents` flowable).

### P4-3. Determinism (`invariant=True` + `SOURCE_DATE_EPOCH`)

**Severity: BLOCKER. Effort: S (1 hour).**

`SimpleDocTemplate(invariant=...)` is never set. ReportLab stamps a
random `/ID` and `now()` `/CreationDate` on every build.
`generator.py:221`, `extractor.py:294,732`, `newsletter.py:441` all
call `datetime.date.today()` into header/footer and back cover.

**Fix.** Wire through Phase 1's `_build_doc`: pass `invariant=True`,
read `SOURCE_DATE_EPOCH` env var and substitute for every
`datetime.date.today()` call. Expose `--reproducible` CLI flag.

### P4-4. Page labels (roman front matter, arabic body)

**Severity: MAJOR. Effort: S (1–2 hours).**

Grep for `pageLabel`, `PageLabels`, `setPageLabels` — zero hits.
Front matter and body share arabic numbering. Acrobat's "go to page
5" means physical page 5, not body page 5.

**Fix.** In `_build_doc`, after building the story, write a
`/PageLabels` dict to the catalogue assigning roman to front matter
(cover through TOC) and arabic restart at the first chapter. The
phase-1 refactor puts this in one place.

### P4-5. `/Lang` attribute and metadata config block

**Severity: MAJOR. Effort: S (30 minutes, rolled into P1-1).**

No `lang=` argument anywhere on SimpleDocTemplate. No per-project
metadata config.

**Fix.** Add a `metadata:` block in `briefkit.yml`:

```yaml
metadata:
  title: "..."
  author: "..."
  subject: "..."
  keywords: ["..."]
  creator: "..."
  producer: "briefkit"
  lang: "en-US"
```

Wire in `_build_doc`.

### P4-6. Doc-ID registry portability and locking

**Severity: MAJOR. Effort: S–M (2 hours).**

`doc_ids.py:170` — registry is `.briefkit/registry.json` resolved
against `find_project_root() or Path.cwd()`. Counters are read,
mutated, saved (`:199-203, :217`) with no file lock. Race condition
between parallel runs. Keys use **absolute** paths
(`target.resolve()`), so two checkouts of the same project produce
different keys and duplicate IDs.

**Fix.** Hash content (or project-root-relative path) for the key.
Wrap read-modify-write in `fcntl.flock`. Document that the registry
must be committed to the repo.

### P4-7. PDF/A-1b output mode

**Severity: MAJOR. Effort: L (1–2 days, after P2-2 + P4-5).**

Grep for `PDFA`, `pdfa`, `xmp` — empty. ReportLab supports PDF/A-1b
via `SimpleDocTemplate(pdfVersion=(1,4))` plus font embedding (P2-2),
ICC profile tagging, XMP metadata packet, no transparency, no
encryption.

**Fix.** After fonts (P2-2) and metadata (P4-5) land, add a
`template.pdfa: true` switch that: sets pdfVersion, embeds the sRGB
v4 ICC profile, writes an XMP metadata packet, and validates
no-transparency. Run the output through `verapdf` in CI.

### P4-8. Clickable bibliography citations and cross-refs

**Severity: POLISH. Effort: M (2–3 hours).**

`bibliography.py` grep returns zero `<link>` or `<a>` emissions. Same
for `cross_refs.py`. Cross-refs are string-matched path heuristics;
there's no anchor resolution.

**Fix.** After P4-1 lands, anchor each bibliography entry and emit
body citations as `<link href="#bib-{key}">text</link>`.

---

## Phase 5 — Content features

### P5-1. Replace `parse_markdown` with `markdown-it-py`

**Severity: BLOCKER. Effort: M (1 day).**

`extractor.py:75-233` is a hand-rolled regex tokenizer. No
CommonMark. Consequences cascade: no images, no nested lists, no
footnotes, no front matter, no setext headings, no autolinks, no
inline HTML, no math, fragile italic, no task lists.

**Fix.** Swap for `markdown-it-py` (pure Python, CommonMark + GFM
plugins). Adapt the block-dict shape via a small renderer plug-in.
This single swap fixes items P5-2 through P5-8 below in one stroke.

### P5-2. Image support

**Severity: MAJOR. Effort: M (after P5-1, 3–4 hours).**

`extractor.py:75` block-type list has no `image`. `render_blocks`
has no `image` branch. Markdown images are silently dropped (the `!`
survives as a literal).

**Fix.** After P5-1, add an `image` block type and an `image` branch
in `render_blocks` that builds a ReportLab `Image` flowable, scales
to `content_width`, handles DPI, pins caption via `KeepTogether`.

### P5-3. Front matter (YAML `---`)

**Severity: BLOCKER. Effort: S (1 hour).**

`---` matches `_RE_HRULE` and becomes an hrule. The `title: Foo` line
becomes a paragraph. There is zero front-matter handling.

**Fix.** Strip front matter before parse; parse with `pyyaml`; merge
into the `content` dict as metadata overrides.

### P5-4. Footnotes, definition lists, task lists, math, admonitions

**Severity: MAJOR. Effort: M each (unlocked by P5-1).**

After `markdown-it-py` lands, enable the relevant plugins:
`mdit-py-plugins.footnote`, `deflist`, `tasklists`, `dollarmath`,
`admon`. Each plugin ships a block emitter; write a small adapter to
the briefkit block-dict shape.

### P5-5. Nested list rendering

**Severity: MAJOR. Effort: S (after P5-1, 1 hour).**

`markdown-it-py` produces nested list tokens; map to `ListFlowable`
with nested `ListItem`.

### P5-6. Key terms: glossary.md ingestion

**Severity: POLISH. Effort: S (1 hour).**

`terms.py:28-30` greps bold text and H2/H3 with a 19-word generic
filter. Misses non-Title-Case domain terms.

**Fix.** Support a `glossary.md` file with pipe-table or YAML
format, use it authoritatively when present, fall back to bold-text
scrape otherwise.

### P5-7. Cross-references with anchor resolution

**Severity: POLISH. Effort: M (after P4-1, 2 hours).**

`cross_refs.py:6-13` is regex path-matching with no resolution.

**Fix.** After bookmarks exist (P4-1), add `[see §{slug}]` syntax
that resolves to a `<link href="#sec-{slug}">` in the renderer.

### P5-8. Unicode fallback font chain

**Severity: MAJOR. Effort: L (1 day).**

After P2-2, CJK / Arabic / Hebrew / emoji still won't render because
Source Serif covers Latin. ReportLab does not chain fallbacks per
glyph.

**Fix.** Ship Noto Sans + Noto Sans CJK SC subset. Add a pre-pass in
`_safe_text` that wraps runs of out-of-Latin-1 characters in
`<font name="NotoFallback">...</font>` using `unicodedata.script()`
lookups. For CJK specifically, use
`reportlab.pdfbase.cidfonts.UnicodeCIDFont("STSong-Light")` as a
no-extra-file fallback.

---

## Phase 6 — Developer ergonomics

### P6-1. Incremental builds

**Severity: MAJOR. Effort: M (half day).**

`batch.py._is_current` already does mtime-based skip-current for
`briefkit batch` and `briefkit status`. `briefkit generate` always
regenerates. For a 50-chapter doc set this is 200 ms vs 30 s.

**Fix.** Reuse `_is_current` in `cmd_generate` behind `--incremental`
(or default, with `--force` to override). Add a content-hash check
(SHA256 of concatenated source files) for correctness.

### P6-2. Watch mode

**Severity: POLISH. Effort: M (half day).**

**Fix.** `briefkit watch` using `watchdog`. On source change, call
`cmd_generate` with `--incremental`. Clear the config cache
(P1-6) on every rebuild.

### P6-3. CLI help epilogs with examples

**Severity: POLISH. Effort: S (1 hour).**

Individual subcommand `--help` outputs lack usage examples.

**Fix.** Add `epilog=` to each subparser with 2–3 realistic examples.

### P6-4. Golden-PDF visual regression

**Severity: MAJOR. Effort: M (half day, after P4-3 determinism).**

Once byte-reproducible builds land (P4-3), commit a small set of
"golden" PDFs under `tests/golden/` and add a pytest fixture that
rebuilds each and SHA256-compares. Any unintentional rendering change
fails CI.

### P6-5. `verapdf` PDF/A validation in CI

**Severity: POLISH. Effort: S (after P4-7).**

After PDF/A lands, run `verapdf` against a representative output in
CI. verapdf is a Java tool but ships containerised.

### P6-6. CMYK preset option and print-safety docs

**Severity: POLISH. Effort: M (half day).**

`templates/*.py` use `HexColor` (sRGB) exclusively. No `CMYKColor`.
For print workflows, add a parallel CMYK palette in each color
preset and document the sRGB assumption.

---

## Dependency additions

| Package | Purpose | Phase | Required / Optional |
|---|---|---|---|
| `markdown-it-py` | CommonMark parser | P5-1 | Required |
| `mdit-py-plugins` | Footnotes, deflist, tasklists, math | P5-4 | Required |
| `pyphen` | Hyphenation | P2-6 | Optional |
| `pyyaml` | Front matter | P5-3 | Already present |
| `watchdog` | Watch mode | P6-2 | Optional |
| `pygments` | Code syntax highlight | P5 (optional) | Optional |
| Font files | Source Serif / Inter / JetBrains Mono / Noto | P2-2 / P5-8 | Required (OFL, ship in-tree) |

---

## Success criteria for "perfectly formatted PDFs"

A briefkit output passes the bar when **every** one of the following
is true:

1. **325+ tests still pass** (current baseline after yesterday's
   guard-rail work).
2. **Byte-reproducible** — two runs of the same input with
   `SOURCE_DATE_EPOCH=0` produce byte-identical PDFs.
3. **Zero orphan titles** across all 29 templates, verified by a
   visual regression sweep of the golden-PDF set.
4. **Zero blank pages** — running every template with an aggressive
   `skip_*` manifest produces no empty pages.
5. **Clickable TOC + body URLs + bibliography citations** verified
   by a `pdfminer.six` link-extraction test.
6. **Document outline matches TOC** — Acrobat sidebar shows every
   chapter and section.
7. **PDF/A-1b validation passes** on at least the `book` and
   `academic` templates under `verapdf`.
8. **Embedded fonts** — `pdffonts output.pdf` shows only
   briefkit-bundled OFL fonts, all marked "emb".
9. **No tofu** — a sample CJK paragraph renders correctly.
10. **Fail-loud** on zero-subsystem extraction, skip-flag typos,
    unknown config keys, missing source files — each with a
    fix-suggesting error message and non-zero exit.
11. **`--dry-run` reports extraction stats and the full section
    manifest** without building the PDF.
12. **Incremental builds** — unchanged sources skip regeneration.

---

## Roadmap at a glance (ordered)

```
Phase 0  Critical regressions                         1 day
  P0-1   Universal guard rails bypassed by 23 templates
  P0-2   Zero-subsystem silent success
  P0-3   Markdown link URLs stripped
  P0-4   Raw &/</> can corrupt ReportLab XML
  P0-5   Skip-flag typo silently ignored
  P0-6   Cover title auto-shrink dead code
  P0-7   "(unspecified)" placeholder in 3 templates

Phase 1  Correctness bedrock                          1-2 days
  P1-1   Centralise SimpleDocTemplate construction
  P1-2   Make --dry-run actually run extraction
  P1-3   Introduce logging module
  P1-4   Config schema with closest-match suggestions
  P1-5   Drop pyproject.toml from root markers
  P1-6   Expose config-cache clear()

Phase 2  Typography upgrade                           2-3 days
  P2-1   Widow/orphan control on every style
  P2-2   Embed real fonts (Source Serif / Inter / JB Mono)
  P2-3   Baseline grid (4pt rhythm)
  P2-4   Line length → 70 cpc
  P2-5   Smart punctuation
  P2-6   Hyphenation + justification
  P2-7   List-item hanging indent
  P2-8   Chapter-aware running heads
  P2-9   Code block / blockquote orphan protection
  P2-10  _safe_text font-attr & regex

Phase 3  Layout rigor                                 2-3 days
  P3-1   Table wordWrap + splitByRow
  P3-2   Column-width clamp order
  P3-3   Content-aware column widths
  P3-4   Code block overflow
  P3-5   Lists: orphans and nesting
  P3-6   Callouts KeepTogether
  P3-7   Caption pinning
  P3-8   Kill CONTENT_WIDTH constant
  P3-9   Dashboard CondPageBreak
  P3-10  Footer bottom-margin clamp
  P3-11  Cover robustness

Phase 4  PDF standard compliance                      3-5 days
  P4-1   Document outline (bookmarks)
  P4-2   Clickable TOC with page numbers + dot leaders
  P4-3   Determinism (invariant + SOURCE_DATE_EPOCH)
  P4-4   Page labels (roman front matter, arabic body)
  P4-5   /Lang attribute + metadata config block
  P4-6   Doc-ID registry portability + locking
  P4-7   PDF/A-1b output mode
  P4-8   Clickable bibliography + cross-refs

Phase 5  Content features                             1-2 weeks
  P5-1   Replace parse_markdown with markdown-it-py
  P5-2   Image support
  P5-3   Front matter (YAML ---)
  P5-4   Footnotes, deflists, tasklists, math, admonitions
  P5-5   Nested lists
  P5-6   Glossary.md ingestion
  P5-7   Cross-references with anchor resolution
  P5-8   Unicode fallback font chain

Phase 6  Developer ergonomics                         1 week
  P6-1   Incremental builds
  P6-2   Watch mode
  P6-3   CLI help epilogs with examples
  P6-4   Golden-PDF visual regression
  P6-5   verapdf PDF/A validation in CI
  P6-6   CMYK preset option and print docs
```

**Total estimate**: 3–5 weeks of focused work for a single contributor.
Phase 0 + Phase 1 alone (2–3 days) would catch the regressions and
silent-failure paths that are the most dangerous — everything past
Phase 1 is upgrade, not repair.

---

## Appendix — Every finding, one-liner

| # | Finding | Sev | Effort | Phase |
|---|---|---|---|---|
| P0-1 | Guard rails bypassed by 23 templates | BLOCKER | M | 0 |
| P0-2 | Zero-subsystem silent success | BLOCKER | S | 0 |
| P0-3 | Markdown link URLs stripped | BLOCKER | S | 0 |
| P0-4 | `&`/`<`/`>` can corrupt ReportLab XML | BLOCKER | S | 0 |
| P0-5 | Skip-flag typo silently ignored | BLOCKER | S | 0 |
| P0-6 | Cover title auto-shrink dead code | BLOCKER | S | 0 |
| P0-7 | `(unspecified)` placeholder ships | MAJOR | S | 0 |
| P1-1 | Centralise SimpleDocTemplate | MAJOR | M | 1 |
| P1-2 | `--dry-run` is a stub | MAJOR | S | 1 |
| P1-3 | No `logging` module | MAJOR | M | 1 |
| P1-4 | Config schema has no unknown-key detection | MAJOR | S | 1 |
| P1-5 | `pyproject.toml` as root marker | MAJOR | S | 1 |
| P1-6 | Project-root `lru_cache` never cleared | POLISH | S | 1 |
| P2-1 | No widow/orphan control on any style | BLOCKER | S | 2 |
| P2-2 | Helvetica-only, no embedded fonts | BLOCKER | M | 2 |
| P2-3 | No baseline grid | MAJOR | S | 2 |
| P2-4 | Line length 96 cpc (target 45–75) | MAJOR | S | 2 |
| P2-5 | No smart punctuation | MAJOR | M | 2 |
| P2-6 | No hyphenation; whitepaper justified without | MAJOR | S | 2 |
| P2-7 | List items have no hanging indent | MAJOR | S | 2 |
| P2-8 | Header/footer not chapter-aware | MAJOR | M | 2 |
| P2-9 | Code/blockquote orphan risk | POLISH | S | 2 |
| P2-10 | `_safe_text` font-attr regex forbids `&` | MAJOR | S | 2 |
| P3-1 | No table `wordWrap` or `splitByRow` | MAJOR | S | 3 |
| P3-2 | Column-width clamp order | MAJOR | S | 3 |
| P3-3 | Columns sized from headers only | MAJOR | M | 3 |
| P3-4 | Code block overflow | BLOCKER | M | 3 |
| P3-5 | Lists orphaned, not nestable | MAJOR | M | 3 |
| P3-6 | Callouts not `KeepTogether`'d | MAJOR | S | 3 |
| P3-7 | Caption pinning missing | MAJOR | S | 3 |
| P3-8 | `CONTENT_WIDTH` hard-coded to A4 | MAJOR | M | 3 |
| P3-9 | Dashboard can overflow footer | MAJOR | S | 3 |
| P3-10 | Footer bottom-margin clamp | MAJOR | S | 3 |
| P3-11 | Cover fixed-Spacer fragility | MAJOR | M | 3 |
| P4-1 | No PDF document outline | BLOCKER | M | 4 |
| P4-2 | TOC not clickable, no page numbers | BLOCKER | M | 4 |
| P4-3 | Non-deterministic output | BLOCKER | S | 4 |
| P4-4 | No page labels (roman/arabic) | MAJOR | S | 4 |
| P4-5 | No `/Lang`, no metadata config | MAJOR | S | 4 |
| P4-6 | Doc-ID registry race + absolute keys | MAJOR | S | 4 |
| P4-7 | No PDF/A mode | MAJOR | L | 4 |
| P4-8 | Citations / cross-refs not hot | POLISH | M | 4 |
| P5-1 | Hand-rolled parser, not CommonMark | BLOCKER | M | 5 |
| P5-2 | No image support | MAJOR | M | 5 |
| P5-3 | No front-matter handling | BLOCKER | S | 5 |
| P5-4 | No footnotes / deflist / math / admonition | MAJOR | M | 5 |
| P5-5 | Nested lists unsupported | MAJOR | S | 5 |
| P5-6 | Glossary ingestion | POLISH | S | 5 |
| P5-7 | Cross-ref anchor resolution | POLISH | M | 5 |
| P5-8 | Unicode fallback font chain | MAJOR | L | 5 |
| P6-1 | No incremental build for `generate` | MAJOR | M | 6 |
| P6-2 | No watch mode | POLISH | M | 6 |
| P6-3 | CLI help epilogs thin | POLISH | S | 6 |
| P6-4 | No golden-PDF visual regression | MAJOR | M | 6 |
| P6-5 | No verapdf CI check | POLISH | S | 6 |
| P6-6 | No CMYK preset option | POLISH | M | 6 |

**54 findings. 11 BLOCKER. 29 MAJOR. 14 POLISH.**

---

*Produced by four parallel research agents + direct code reading,
cross-validated against the briefkit@21adf1f tree.*

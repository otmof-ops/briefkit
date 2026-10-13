# Changelog

All notable changes to BriefKit are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **A document outline.** Every H1, H2 and H3 heading in every template is bookmarked and listed in the PDF outline (the sidebar in Acrobat, Preview and browsers), nested by level, and the file opens with the outline showing. The viewer window bar shows the document title instead of the file name.
- **A clickable table of contents.** Each TOC entry is an internal link to the heading it names, in all 29 templates.
- **Resolvable `#anchors`.** A Markdown link such as `[see](#installation)` jumps to the heading whose slug matches (GitHub-style: lower-case, hyphens; a leading "3.1 " section number is ignored). Every anchor referenced in a document is pre-registered on page 1, so a link to a heading that does not exist lands on page 1 instead of aborting the build, which is what an unresolved destination used to do.

### Fixed

- **Variant auto-detection counts whole words, case-insensitively.** "loss" inside "Glossary" and "gradient" inside a preset description used to select the AI/ML variant for a getting-started guide, and upper-case keywords such as `EBITDA`, `REST` and `GET` could never match lower-cased text.
- **Cross-reference labels.** An authored link label (`[the sibling set](../sibling-set/README.md)`) was discarded in favour of a title-cased path; the label wins now, and the scan skips symlinks and oversized files like the extractor does.
- Two citation patterns (the "A, B, and C (2020)" author list and the legal variant's case-name scan) were quadratic on long capitalised lists (25 s on 100 kB); both are bounded.
- `briefkit generate` no longer extracts the source directory twice; the pre-check's extraction is reused by the template. `--version` reads the package version directly.
- The historical variant's timeline drawing uses the brand fonts.

### Security

- **Link targets are allowlisted.** Markdown links became PDF link actions whatever their scheme, so `[x](javascript:…)`, `[x](file:///…)`, `[x](smb://…)` and custom handlers such as `ms-msdt:` were live in the output. Only `http`, `https` and `mailto` are kept; everything else renders as its label text. The sanitiser in `styles._safe_text` re-validates every `<link>` on both escaping paths.
- **Titles and brand strings no longer reach the markup parser raw.** A README heading such as `# <img src="http://…"/> Quarterly` made ReportLab fetch the URL during the build (an outbound request from a tool documented as offline), `# Release <b>notes` aborted the build, and `Vec<T>` lost its type parameter. The cover, classification banner, table captions and the base section builders now escape every data string, and ReportLab is configured to trust no remote host as a backstop.
- **`output.filename` is validated.** It is joined onto the source directory, so `../../victim.txt` or an absolute path overwrote arbitrary files the user could write. It must now be a bare `.pdf` name; `output.output_dir` may not walk upwards; the resolved path is checked to stay inside the output directory.
- **The doc-ID registry path is contained.** An absolute `doc_ids.registry_path` bypassed the project-root check and could replace any JSON-looking file. Relative and absolute paths must both resolve inside the project root, and an unreadable registry is an error rather than a silent reset that would renumber every document.
- **PDFs are written atomically.** ReportLab opens the output for writing before it renders, so a build that failed part-way (an unresolved `#anchor` link was enough) left a 0-byte file where a good PDF had been. Output now goes to a sibling `.part` file that is moved into place only after a successful build.

### Changed

- **One `generate()` for all 29 templates.** `BaseBriefingTemplate.generate()` is final; templates describe themselves with traits (`pdf_subject`, `design_page_size`, `page_size_lock`, `orientation_lock`, `design_margins_mm`, `margin_overrides_mm`, `supports_variants`, `assigns_doc_id`) and hooks (`page_geometry`, `prepare`, `doc_kwargs`, `header_footer`, `before_build`, `body_toc_entries`). The 24 copies of the extraction / doc-ID / margin / build boilerplate are gone, and the guard rails, metadata, atomic write and variant policy apply identically everywhere. A subclass that still overrides `generate()` keeps working and gets a `DeprecationWarning`.
- **`layout.page_size` and `layout.orientation` are honoured by every template.** Fifteen templates were locked to A4 or Letter whatever the config said, orientation was validated and printed but applied by none, and eight templates sized their text for one page while building the frame for another (tables ran off both edges on A3). Geometry now has one owner (`PageGeometry`); a template's design size applies only when the user set none, and `guide`, `deep-research` and `magazine` (covers drawn at absolute A4 coordinates) stay on A4 by declaration.
- **Each template's margins are now real.** The per-template margin defaults (letter 25 mm sides, deck 15 mm top and bottom, witness 28 mm top, and so on) were dead code under the CLI because the config loader always supplied the global defaults first; they apply now wherever the user did not set that side. `memo` keeps its fixed 30 / 25 mm sides. `evaluation` is Letter by design, as its author intended.
- **Brand fonts reach every template.** 246 hard-coded `Helvetica` / `Courier` names in the templates (and a few in the base) are brand lookups, so the Times presets (`royal`, `ink`, `gothic`) finally render in Times. Default output is unchanged.
- **Variants stay where they always worked.** Only `briefing`, `report`, `manual` and `academic` add domain variant sections; fixed-format templates (decks, certificates, invoices, resumes) never did and now declare it. Variant sections come before the back cover instead of after it.
- **Chapter sub-headings are kept.** Every H2 and H3 inside a source document was dropped from the body by the chapter renderers; only the chapter's own H1 is consumed now.
- **The default briefing's table of contents matches its body.** The TOC said "3. Content Overview" while the body said "3. Context and Significance"; numbering was also fixed at 3 when a skipped executive summary had renumbered the TOC. Sections are numbered from the first free number and the TOC lists exactly the headings emitted.
- `/Subject` is set for every template (`Book`, `Deck`, `Deep Research Report`, ...) and `metadata.subject` from the config wins over it.
- **Every printed date follows `SOURCE_DATE_EPOCH`.** The cover, running head, back cover, colophon, doc-ID year and the extractor's year heuristic all read one clock (`briefkit._dates.today`), so a pinned build is byte-identical across days as well as runs. Without the variable the wall clock is used as before.
- **The cover prints a project-relative path.** The absolute source path leaked the machine's directory layout into every PDF and made the same document differ between two checkouts; the breadcrumb is now relative to the project root (or just the directory name).
- **`/Title` is the document title for every template.** Overriding templates used to stamp the project name; `metadata.title` now beats the README heading, which beats the project name, uniformly.
- **The quality gate measures structure, not bytes.** `briefkit quality` fails on a missing header, an unparseable file, zero pages or no extractable text; the byte and page thresholds warn unless `--strict`, are lower by default (output without embedded fonts is small), take `--level`, and read a `quality:` block from `briefkit.yml`. `--json` output is pure JSON.
- **`batch` staleness looks at everything that feeds the PDF.** README, engineering-brilliance, guide, preface, glossary, methodology, `.source-type` and the project's `briefkit.yml` now count; a changed README no longer leaves a current-looking stale PDF.
- **Unknown configuration keys are reported, not ignored.** `tempalte:` or `layout.pagesize` produce a warning with the closest valid name; the file still loads, so one stray line cannot abort a batch.
- `BUSL-1.1`, `Elastic-2.0` and `SSPL-1.0` are labelled `[use-restricted]` in `briefkit licenses`; they are not non-commercial licences.

### Fixed

- **`--title`, `--org`, `project.org`, `project.tagline`, `project.url`, `project.abn` and `project.copyright` reach the PDF.** The cover, running head, back cover and `/Author` read `brand.*`, which was never fed from `project.*`; it is now, with an explicit `brand.*` still winning. `--title` names the document everywhere it appears.
- **`--logo` and `brand.logo` are rendered** on the cover's top bar (PNG, JPEG or GIF, scaled to fit). A relative path is relative to the config file; a missing or SVG logo is a clear error in config and a warning on the command line.
- **Zero-config level detection.** A folder of numbered documents is a documentation set at any depth, so `briefkit generate ./chapters` with no `briefkit.yml` no longer produces a chapter-less briefing.
- **Concurrent runs no longer issue duplicate document IDs.** The registry's read-modify-write is serialised with a lock file (eight parallel writers issued 156 duplicates across 200 documents before).
- **A blockquote longer than a page no longer aborts the build** with `LayoutError`; it is rendered as indented paragraphs that may split.
- **A hard page break survives next to a conditional one** in the empty-page collapse; the stronger break is kept.
- `<br/>` is no longer counted as an open `<b>` (which appended a stray `</b>` and lost all markup in the fallback); the zero-width-space long-word breaker is gone (ReportLab wraps long words itself, and U+200B rendered as a black square); the sanitiser's fallback no longer double-escapes already-escaped text.
- `batch` honours `--no-ids` and `--variant`, treats `--output` as the mirror directory, reports "would be generated" for a dry run and names the exception type on failure. `init --dry-run` writes nothing and `init` on a missing directory is a clean error. `assign-ids` describes what it does (registry only) and reports checked / assigned / existing honestly. `templates` prints a description per template and `-q` lists names. `briefkit batch | head` ends quietly.
- `variants.auto_detect: false` is honoured. An empty YAML section (`brand:` with nothing under it) means defaults; an unquoted hex colour is a clear error that says to quote it; the copyright line has no trailing space when there is no organisation.
- **`--output`, `output.output_dir` and `preview` work.** The CLI printed the requested path, then wrote `<source dir>/executive-briefing.pdf` regardless, `batch` could never skip current output when `output_dir` was set, and `preview` reported its own file missing. One resolver (`briefkit.output.resolve_output_path`) now serves `generate`, `batch`, `status`, `preview` and every template; `--output` may name a directory.
- **`python -m briefkit` returns the CLI's exit code** instead of 0 on failure.
- **`selftest` leaves no trace and can fail.** It assigned real document IDs in whichever registry sat above the current directory and returned 0 without looking at the result. It now builds in a temporary project with IDs disabled and verifies the PDF (exists, has pages, carries the fixture text); `--json` reports the checks.
- **Long inline code and long URLs no longer break their own markup.** The zero-width-space breaker for 60+ character runs could split inside `</font>` or an `href`, corrupting the tag; it now only touches text between tags.
- **Link URLs may contain balanced parentheses** (`https://en.wikipedia.org/wiki/Foo_(bar)`), per CommonMark.
- Double-escaped ampersands in the executive summary, body headings, bibliography entries and source classification line (`R&amp;D`).

### Added

- 23 new templates brought the registry from 6 to 29 total: novel, letter, contract, proposal, policy, whitepaper, sop, resume, magazine, memo, invoice, quote, certificate, minutes, datasheet, evaluation, newsletter, deck, playbook, guide, deep-research, register, witness.
  - Most recent: **witness** — legal witness statement template (formal header, paragraph-numbered body, execution block; no briefing chrome).
- Universal template guard rails: skip flags, orphan protection, empty-page collapse.
- Novel template: `skip_preface` option; forced page break after volume preface; orphaned chapter-title fix.
- 10 additional colour presets (total 20): crimson, slate, royal, sunset, mono, midnight, and others.

### Changed

- Template registry auto-discovery now covers all 29 templates.
- Novel and book template typography reflow for long-form narrative flow.

### Added

- **`--variant none`** suppresses variant sections entirely. Previously the only way to avoid an unwanted variant was to name a different one, so a document matching no variant still received whichever one keyword-matched — a tax submission picking up the finance variant's investment-advice disclaimer and risk register, for instance. Omitting `--variant` still auto-detects.

### Fixed

- **XML entities no longer double-escape.** `extractor._strip_inline` escapes `&`, `<` and `>` and emits real `<b>` / `<i>` tags; `_safe_text` then escaped the result a second time, so `&amp;` became `&amp;amp;` and reached the page as literal text — "Pine Accounting &amp; Tax Services", "taxable income &lt; $250,000". `_safe_text` and `_safe_para` now take `already_escaped`, and `render_blocks` sets it for the block types the extractor pre-escapes (heading, paragraph, list_item, table, blockquote). Code blocks are unaffected, being deliberately raw. `build_data_table` and `build_callout_box` thread the same flag; table headers were escaping three times.
- **Markdown no longer leaks into generated prose.** The Abstract and Recommendations sections slice raw source and render it as sentences, so `**Taxpayer**` and `[label](url)` appeared verbatim. Both now pass through a new `extractor.markdown_to_plain()`, which strips emphasis rather than converting it.
- **Excerpts no longer break mid-word.** Derived text was cut with a bare `[:150]`, producing endings like `**Ac;`. New `extractor.truncate_words()` cuts on a word boundary and drops a trailing function word, so an excerpt does not end on a dangling "of…" or "the…".
- **Abstract key-findings no longer quote document frontmatter.** The heuristic took the first 40-character run from each source; documents commonly open with a metadata block ("Taxpayer  Jay Taylor", "Income year  1 July 2025 …") whose lines are long but never terminate, so they merged into the first real sentence once whitespace was collapsed. Extraction now considers only lines that end in terminal punctuation.

- **Long documents no longer lose their tail silently.** A source document past roughly six pages rendered its opening sections and then simply stopped, with nothing in the PDF or on stderr to say the rest had been dropped. A 41,000-word set of technical memoranda emitted 18,300 words across 50 pages; the same input now emits 40,700 across 105. Two layers were responsible:
  - `content.max_words_per_section` defaulted to **3000**. `extractor.py` already carried a 12000 fallback with a comment explaining the raise, but the value declared in `DEFAULTS` always won, so the fallback never applied. The default is now **12000**, and **0 means unlimited**.
  - Document-oriented templates capped the body at a hard-coded 80 (sometimes 100 or 60) rendered flowables per source document — `report.py` did this inside a method whose docstring read "full content". The ceiling is now read from `content.max_blocks_per_section`, which **defaults to 0 (unlimited)** for the 16 document templates. Fixed-format templates (deck, resume, certificate, invoice, quote, newsletter) keep their design caps, since a slide or a one-page resume genuinely cannot grow.
- **Truncation is now reported rather than silent.** Any document cut by the word budget is recorded in `metrics.truncated_sections` with the words kept against the words available, and the CLI names each one on stderr with the setting responsible. `BaseBriefingTemplate.render_body_blocks()` likewise returns the number of blocks it dropped instead of discarding them quietly.
- New `tests/test_truncation.py` covers both layers — default budgets, `0` as unlimited, the recording of what was dropped, and the precedence of config over a template's own ceiling.

- **Callouts no longer abort a whole document on wrapped emphasis.** `build_callout_box` splits its body on newlines and makes each line a separate `Paragraph`. Markdown emphasis is converted to ReportLab tags upstream (`**x**` → `<b>x</b>`), so a bold or italic span crossing a line break was torn in half — one line receiving `<b>`, the next `</b>` — and raw `Paragraph` raised `parse ended with 1 unclosed tags` at layout time, failing the entire build rather than degrading one callout. Callout bodies, pull-quote text and pull-quote attribution now route through the existing `_safe_para` sanitizer, which closes open tags and escapes bare `<`, `>` and `&`. Any source document with emphasis wrapping inside a blockquote was affected.
- New `tests/test_callout.py` covers the callout module, which previously had none. The tests force a layout pass (`wrap()` plus a real `doc.build()`) because `Paragraph` defers parsing until layout — assertions on construction alone pass even with the bug present.

### Docs

- `README.md` template count updated (28 → 29) with `briefkit templates` hint.
- `docs/templates-guide.md` summary table expanded from 10 to all 29 templates.
- `docs/templates.md` redirects to `templates-guide.md` for the full catalogue.

## [1.0.0] — 2026-03-31

### Added

- 6 built-in templates: briefing, book, report, manual, academic, minimal
- 12 domain-aware variants with auto-detection (AI/ML, legal, medical, engineering, research, API, gaming, finance, species, historical, hardware, religion)
- 10 color presets: navy, charcoal, ocean, forest, crimson, slate, royal, sunset, mono, midnight
- YAML configuration system with zero-config defaults
- Document ID system with persistent JSON registry
- Auto-extracted bibliography supporting 6 citation formats (APA, author-year, bracketed, legislation, RFC, case law)
- Version-tracked batch processing with skip-if-current logic
- Two-tier quality gates (hard minimum and soft target)
- Custom templates and variants via Python subclassing
- CLI commands: generate, batch, init, preview, status, assign-ids, quality, selftest, config, templates, presets

[Unreleased]: https://github.com/otmof-ops/briefkit/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/otmof-ops/briefkit/releases/tag/v1.0.0

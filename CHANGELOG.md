# Changelog

All notable changes to BriefKit are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-10-13

### Added

- **23 templates**, from 6 to 29: novel, letter, contract, proposal, policy, whitepaper, sop, resume, magazine, memo, invoice, quote, certificate, minutes, datasheet, evaluation, newsletter, deck, playbook, guide, deep-research, register and witness (a legal witness statement: formal header, paragraph-numbered body, execution block, no briefing chrome). `briefkit templates` prints a one-line description per template; `--quiet` lists the names.
- **10 color presets**, from 10 to 20: arctic, corporate, cyber, deep-research, emerald, gothic, ink, neon, neon-print and terracotta. The Times presets (`royal`, `ink`, `gothic`) and the Courier preset (`mono`) now render in their fonts in every template.
- **License presets.** `briefkit licenses` lists them by category with SPDX identifiers; `license.preset` prints the license on the back cover and fills `license.name`, `spdx`, `url` and `notice`. Without one the back cover says "All rights reserved" and every run warns. `BUSL-1.1`, `Elastic-2.0` and `SSPL-1.0` are labeled `[use-restricted]`.
- **A document outline.** Every H1, H2 and H3 heading in every template is bookmarked and listed in the PDF outline, nested by level, and the file opens with the outline showing. The viewer window bar shows the document title instead of the file name.
- **A clickable table of contents.** Each TOC entry is an internal link to the heading it names, in all 29 templates.
- **Resolvable `#anchors`.** A Markdown link such as `[see](#installation)` jumps to the heading whose slug matches (GitHub style: lower-case, hyphens; a leading "3.1 " section number is ignored). Every anchor referenced in a document is pre-registered on page 1, so a link to a heading that does not exist lands on page 1 instead of aborting the build.
- **`variants.rules`.** A list of `{pattern, variant}` entries; the first shell-glob pattern that matches the directory's path relative to the project root selects the variant. The key was documented and read by nothing before. Selection order is now `--variant`, then rules, then auto-detection.
- **`--variant none`** suppresses variant sections entirely. Previously the only way to avoid an unwanted variant was to name a different one, so a document matching no variant still received whichever one keyword-matched (a tax submission picking up the finance variant's investment-advice disclaimer, for instance).
- **`briefkit.templates.register_template(name, cls)`** and **`briefkit.variants.register_variant(cls)`** make a template or variant selectable by name without editing the package.
- **`briefkit status --check`** exits 1 when any briefing is stale or missing, for CI.
- **`briefkit quality` measures structure.** It fails on a missing `%PDF-` header, an unparseable file, zero pages or no extractable text; the size and page thresholds warn unless `--strict`, are lower by default (output without embedded fonts is small), take `--level {1,2,3,4}` and read a `quality:` block from `briefkit.yml`. `--json` is pure JSON. The read-back checks need pypdf: `pip install "briefkit[quality]"`.
- **Reproducible output.** Every printed date and the PDF timestamps follow `SOURCE_DATE_EPOCH` (the cover, running head, back cover, colophon, doc-ID year and the extractor's year heuristic read one clock), so a pinned build is byte-identical across days as well as runs.
- **Logo on the cover.** `brand.logo` or `--logo PATH` draws a PNG, JPEG or GIF on the cover's top bar, scaled to fit; a relative path is relative to the configuration file. A missing or SVG logo is a clear error.
- **Universal guard rails** in the base class for all templates: `project.skip_<section>` flags (30 sections), orphan protection, empty-page collapse, `section_break_mode`, spacing caps. A misspelled skip flag is a configuration error with a suggestion. The novel template gained `skip_preface`.
- **Unknown configuration keys are reported.** `tempalte:` or `layout.pagesize` produce a warning with the closest valid name; the file still loads.
- **Truncation is reported.** Any document cut by `content.max_words_per_section` is recorded in `metrics.truncated_sections` and named on stderr with the words kept against the words available and the setting responsible. The new `content.max_blocks_per_section` (default 0, unlimited) replaces the hard-coded 60 to 100 flowable ceilings that document templates applied silently.
- **Aggregates are recognized by content.** A directory whose children hold numbered documents is a subject, and one whose grandchildren do is a division, wherever it sits below the project root; before, the depth rule alone decided and a subject at the wrong depth was read as an empty documentation set.
- `briefkit init --dry-run` prints what would be written. `briefkit assign-ids` reports checked, assigned and existing counts. `briefkit batch --json` reports `total`, `generated`, `skipped`, `failed`, `dry_run`, `results` and `elapsed`.
- `briefkit --version`.

### Changed

- **One `generate()` for all 29 templates** ([ADR-006](docs/adr/006-template-hooks-over-generate-overrides.md)). `BaseBriefingTemplate.generate()` is final; templates describe themselves with traits (`pdf_subject`, `design_page_size`, `page_size_lock`, `orientation_lock`, `design_margins_mm`, `margin_overrides_mm`, `supports_variants`, `assigns_doc_id`) and hooks (`page_geometry`, `prepare`, `doc_kwargs`, `header_footer`, `before_build`, `body_toc_entries`). The 24 copies of the extraction, doc-ID, margin and build boilerplate are gone, and the guard rails, metadata, atomic write and variant policy apply identically everywhere.
- **`layout.page_size` and `layout.orientation` are honored by every template.** Fifteen templates were locked to A4 or Letter whatever the configuration said, orientation was validated and printed but applied by none, and eight templates sized their text for one page while building the frame for another. Geometry now has one owner (`PageGeometry`); a template's design size applies only when the user set none, and `guide`, `deep-research` and `magazine` (covers drawn at absolute A4 coordinates) stay on A4 by declaration.
- **Each template's margins are real.** The per-template margin defaults were dead code under the CLI because the configuration loader always supplied the global defaults first; they apply now wherever the user did not set that side. `evaluation`, `datasheet`, `memo`, `playbook`, `sop` and `whitepaper` are Letter by design.
- **Variants stay where they always worked.** Only `briefing`, `report`, `manual` and `academic` add domain variant sections; fixed-format templates never did and now declare it. Variant sections come before the back cover instead of after it. Keyword detection counts whole words, case-insensitively: "loss" inside "Glossary" no longer selects the AI/ML variant, and upper-case keywords such as `EBITDA`, `REST` and `GET` match.
- **Chapter sub-headings are kept.** Every H2 and H3 inside a source document was dropped from the body by the chapter renderers; only the chapter's own H1 is consumed now.
- **The default briefing's table of contents matches its body.** The TOC said "3. Content Overview" while the body said "3. Context and Significance", and numbering was fixed at 3 when a skipped executive summary had renumbered the TOC.
- **`/Title` is the document title for every template**: `metadata.title`, then the README heading, then the project name. `/Subject` is set per template (`Book`, `Deck`, `Deep Research Report`, ...) and `metadata.subject` wins over it. `/Author` is the organization.
- **The cover prints a project-relative path.** The absolute source path leaked the machine's directory layout into every PDF and made the same document differ between two checkouts.
- **`batch` staleness looks at everything that feeds the PDF**: README, the orientation document, `engineering-brilliance.md`, `guide.md`, `preface.md`, `glossary.md`, `methodology.md`, `.source-type` and the project's `briefkit.yml`.
- **Default `content.max_words_per_section` is 12000** (was 3000, and the cut was silent); `0` means unlimited.
- Novel and book typography reflow for long-form narrative; the novel template forces a page break after a volume preface and keeps chapter titles with their first lines.
- Cross-reference labels: an authored link label (`[the sibling set](../sibling-set/README.md)`) is kept instead of a title-cased path.
- Documentation rewritten against the code: README, CLI reference, configuration reference (every key with its default), custom templates and variants (examples that run), document IDs, CI integration, variants, examples, contributing, security and safety pages. Installation is from this repository (`pip install "git+https://github.com/otmof-ops/briefkit.git"`) until the first PyPI release. `tests/test_docs.py` parses every documented command, resolves every relative link, checks every template, preset and variant name and rejects British spellings.

- **License.** The code is licensed under the BSD 3-Clause License from this version; the documentation under CC BY 4.0 and the examples under CC0 1.0, recorded per path in [REUSE.toml](REUSE.toml), with the name policy in [TRADEMARKS.md](TRADEMARKS.md). Version 1.0.0 was published under CC BY-NC-SA 4.0 and that grant stands for copies of 1.0.0.

### Deprecated

- Overriding `BaseBriefingTemplate.generate()`. A subclass that does so still works and gets a `DeprecationWarning`; use the traits and hooks instead.

### Removed

- The configuration keys `layout.font_family`, `layout.font_size`, `template.sections`, `template.custom_sections`, `output.report_format` and `constraints`. Nothing read them; a file that still carries one gets an unknown-key warning. Fonts are `brand.font_*`; sections are suppressed with `project.skip_*`.
- `briefkit.version_check`, the only code path that made a network request.
- The module-level header/footer state (`briefkit.elements._hf_state`) and the bare `header_footer()` callback ([ADR-005](docs/adr/005-closure-based-header-footer.md), now complete). Templates keep page state in `self.hf_ctx`.
- The end-user license agreement (`EULA/`) and the non-commercial terms in `NOTICE.txt` and the README. The BSD 3-Clause License in `LICENSE` is the whole license for the code.

### Fixed

- **`--output`, `output.output_dir` and `preview` work.** The CLI printed the requested path, then wrote `<source dir>/executive-briefing.pdf` regardless; `batch` could never skip current output when `output_dir` was set; `preview` reported its own file missing. One resolver (`briefkit.output.resolve_output_path`) serves `generate`, `batch`, `status`, `preview` and every template; `--output` may name a file or a directory, and is the mirror directory for `batch`.
- **`--title`, `--org`, `project.org`, `project.tagline`, `project.url`, `project.abn` and `project.copyright` reach the PDF.** The cover, running head, back cover and `/Author` read `brand.*`, which was never fed from `project.*`; it is now, with an explicit `brand.*` still winning.
- **Zero-config level detection.** A folder of numbered documents is a documentation set at any depth, so `briefkit generate ./chapters` with no `briefkit.yml` no longer produces a chapter-less briefing.
- **Concurrent runs no longer issue duplicate document IDs.** The registry's read-modify-write is serialized with a lock file (eight parallel writers issued 156 duplicates across 200 documents before).
- **Long documents no longer lose their tail silently.** A source document past roughly six pages rendered its opening sections and then stopped, with nothing in the PDF or on stderr to say so: the 3000-word default and the templates' hard-coded flowable ceilings were both responsible (a 41,000-word set emitted 18,300 words across 50 pages; it now emits 40,700 across 105).
- **Callouts no longer abort a document on wrapped emphasis.** A bold or italic span crossing a line break inside a blockquote produced an unclosed tag and failed the whole build; callout bodies, pull quotes and attributions go through the sanitizer.
- **A blockquote longer than a page no longer aborts the build** with `LayoutError`; it is rendered as indented paragraphs that may split.
- **`generate` extracts the source directory once**; the pre-check's extraction is reused by the template. Two citation patterns (the "A, B, and C (2020)" author list and the legal variant's case-name scan) and the inline Markdown patterns were quadratic on long inputs (71 s on 200 kB); all are bounded.
- **`selftest` leaves no trace and can fail.** It assigned real document IDs in whichever registry sat above the current directory and returned 0 without looking at the result. It builds in a temporary project with IDs disabled and verifies the PDF.
- **`python -m briefkit` returns the CLI's exit code** instead of 0 on failure. `briefkit batch | head` ends quietly.
- **Markup and escaping.** `&`, `<` and `>` were escaped twice (`R&amp;D` on the page); Markdown leaked into the Abstract and Recommendations (`**Taxpayer**`); excerpts broke mid-word; key findings quoted document front matter; `<br/>` was counted as an open `<b>`; the zero-width-space long-word breaker could split inside a tag and rendered as a black square; link URLs may contain balanced parentheses, per CommonMark; emphasis follows the CommonMark flanking rule, so `snake_case_names` and `2 * 3 * 4` are left alone.
- `batch` honors `--no-ids` and `--variant`, says "would be generated" for a dry run and names the exception type on failure. `init` on a missing directory is a clean error. `variants.auto_detect: false` is honored. An empty YAML section means defaults; an unquoted hex color is a clear error that says to quote it; the copyright line has no trailing space without an organization.
- A hard page break survives next to a conditional one in the empty-page collapse. The historical variant's timeline uses the brand fonts.

### Security

- **Link targets are allowlisted.** Markdown links became PDF link actions whatever their scheme, so `[x](javascript:…)`, `[x](file:///…)`, `[x](smb://…)` and custom handlers such as `ms-msdt:` were live in the output. Only `http`, `https`, `mailto` and in-document `#anchors` are kept; everything else renders as its label text. The sanitizer in `styles._safe_text` re-validates every `<link>` on both escaping paths.
- **Titles and brand strings no longer reach the markup parser raw.** A README heading such as `# <img src="http://…"/> Quarterly` made ReportLab fetch the URL during the build (an outbound request from a tool documented as offline), `# Release <b>notes` aborted the build, and `Vec<T>` lost its type parameter. The cover, classification banner, table captions and the base section builders escape every data string, and ReportLab is configured to trust no remote host as a backstop.
- **`output.filename` is validated.** It is joined onto the source directory, so `../../victim.txt` or an absolute path overwrote arbitrary files the user could write. It must be a bare `.pdf` name; `output.output_dir` may not walk upwards; the resolved path is checked to stay inside the output directory.
- **The doc-ID registry path is contained.** An absolute `doc_ids.registry_path` bypassed the project-root check and could replace any JSON-looking file. Relative and absolute paths must both resolve inside the project root, and an unreadable registry is an error rather than a silent reset that would renumber every document.
- **PDFs are written atomically.** ReportLab opens the output for writing before it renders, so a build that failed part-way left a 0-byte file where a good PDF had been. Output goes to a sibling `.part` file that is moved into place only after a successful build.
- **Source files are read safely.** Symlinks are not followed and files over 10 MB are skipped by the extractor, the template readers and the cross-reference scan alike.

## [1.0.0] - 2026-03-31

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

[Unreleased]: https://github.com/otmof-ops/briefkit/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/otmof-ops/briefkit/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/otmof-ops/briefkit/releases/tag/v1.0.0

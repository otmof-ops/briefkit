# Changelog

All notable changes to BriefKit are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- 23 new templates brought the registry from 6 to 29 total: novel, letter, contract, proposal, policy, whitepaper, sop, resume, magazine, memo, invoice, quote, certificate, minutes, datasheet, evaluation, newsletter, deck, playbook, guide, deep-research, register, witness.
  - Most recent: **witness** — legal witness statement template (formal header, paragraph-numbered body, execution block; no briefing chrome).
- Universal template guard rails: skip flags, orphan protection, empty-page collapse.
- Novel template: `skip_preface` option; forced page break after volume preface; orphaned chapter-title fix.
- 10 additional colour presets (total 20): crimson, slate, royal, sunset, mono, midnight, and others.

### Changed

- Template registry auto-discovery now covers all 29 templates.
- Novel and book template typography reflow for long-form narrative flow.

### Fixed

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

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

# Changelog

All notable changes to BriefKit are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

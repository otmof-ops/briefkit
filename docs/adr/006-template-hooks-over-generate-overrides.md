# ADR-006: Template Hooks and Traits Instead of generate() Overrides

**Status:** Accepted
**Date:** 2026-10-13

## Context

By 1.0.x, 24 of the 29 templates overrode `BaseBriefingTemplate.generate()` with their own copy of the extraction, document-ID, page-geometry, metadata and `doc.build()` sequence. Every cross-cutting fix (the orphan-protection and empty-page guard rails, the atomic `.part` write, `SOURCE_DATE_EPOCH`, the `/Title` precedence, bookmarks for the outline) had to be applied 25 times and was in practice applied once, so most templates silently lacked it. Page size and orientation from `layout.*` were honored by none of them, and seven templates kept module-level state dictionaries for their page callbacks, which blocked any parallel batch.

## Decision

`generate()` is final. A template describes itself with class attributes (traits) and participates through hooks that `generate()` calls in a fixed order:

- Traits: `pdf_subject`, `design_page_size`, `page_size_lock`, `orientation_lock`, `design_margins_mm`, `margin_overrides_mm`, `supports_variants`, `assigns_doc_id`.
- Hooks: `extract_content`, `assign_doc_id`, `page_geometry`, `prepare`, `doc_kwargs`, `build_story`, `body_toc_entries`, `before_build`, `header_footer`.

Page callbacks receive their state through `self.hf_ctx`, bound with `functools.partial`, instead of a module dictionary. A subclass that still overrides `generate()` keeps working and gets a `DeprecationWarning`; the override path will be removed in a later major version.

## Consequences

- **Positive:** one implementation of extraction, geometry, metadata, guard rails, navigation and the atomic write; a template is its story plus a handful of declarations; `layout.page_size`, `layout.orientation` and per-template margins work everywhere; no shared mutable state.
- **Negative:** a template that needs an unusual document class or build sequence must express it through `page_geometry()`, `doc_kwargs()` and `before_build()` rather than by calling `doc.build()` itself; the hook order is a contract that `tests/test_template_contract.py` enforces.
- **Supersedes:** the remaining scope of ADR-005 (the module-level `_hf_state` is gone).

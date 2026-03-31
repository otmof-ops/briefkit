# ADR-003: ReportLab as Sole PDF Generation Library

**Status:** Accepted
**Date:** 2026-03-31

## Context

BriefKit needs to generate professional, multi-page PDFs with covers, tables of contents, tables, charts, and branded typography. Options considered:

- **ReportLab** (BSD-3): Mature Python-native library with Platypus layout engine, flowable model, and direct canvas access
- **WeasyPrint** (GPL): HTML/CSS-to-PDF; requires an HTML rendering intermediate layer and has a heavier dependency tree
- **fpdf2** (LGPL): Lightweight but lacks the Platypus-equivalent layout engine for complex multi-page documents
- **wkhtmltopdf**: Unmaintained, requires external binary, browser engine dependency

## Decision

Use ReportLab exclusively for all PDF generation. Accept the vendor lock-in as an intentional tradeoff for capability.

## Consequences

- **Positive:** Python-native with no external binaries; mature API with 20+ years of production use; direct canvas access for custom flowables; no HTML/CSS intermediate layer
- **Negative:** Memory-resident full story assembly (no streaming); XML markup in Paragraph() creates an injection surface that must be sanitized; HIGH vendor lock-in (migration would require rewriting all rendering code — 15+ person-days); no HTML output format without a separate renderer
- **Security implication:** ReportLab's Paragraph XML parser requires input sanitization via _safe_text()/_safe_para() for all user-derived content

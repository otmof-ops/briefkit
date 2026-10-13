"""
briefkit.quality
~~~~~~~~~~~~~~~~
Quality gates for generated PDFs.

Two kinds of check:

* **Structural** checks fail the gate: the file exists, is non-empty, carries
  a PDF header, and (when pypdf is available) parses, has at least one page
  and extractable text on its first page.
* **Size and page** thresholds are advisory by default: a valid eight-page
  briefing is often under 20 kB because no font is embedded, so a byte floor
  that fails it is a poor proxy for quality. They are reported as ``WARN``
  unless ``strict`` is set, in which case they fail the gate.

Thresholds come from ``quality:`` in ``briefkit.yml`` (``min_pages``,
``hard_min_bytes``, ``soft_min_bytes``, ``strict``), falling back to the
per-level defaults below.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Default thresholds by level. Byte floors are deliberately low: output
# without embedded fonts is small.
DEFAULT_THRESHOLDS: dict[int, dict[str, int]] = {
    1: {"hard_min_bytes": 20_000, "soft_min_bytes": 100_000, "min_pages": 5},
    2: {"hard_min_bytes": 10_000, "soft_min_bytes": 50_000, "min_pages": 3},
    3: {"hard_min_bytes": 5_000, "soft_min_bytes": 20_000, "min_pages": 2},
    4: {"hard_min_bytes": 20_000, "soft_min_bytes": 100_000, "min_pages": 5},
}


def resolve_thresholds(level: int = 3, config: dict | None = None, overrides: dict | None = None) -> dict[str, Any]:
    """Level defaults, then ``quality:`` from *config*, then explicit *overrides*."""
    out: dict[str, Any] = dict(DEFAULT_THRESHOLDS.get(level, DEFAULT_THRESHOLDS[3]))
    out["strict"] = False
    for source in ((config or {}).get("quality") or {}, overrides or {}):
        for key, value in source.items():
            if value is not None:
                out[key] = value
    return out


def run_quality_gates(pdf_path, level: int = 3, thresholds: dict | None = None, strict: bool | None = None):
    """
    Run quality gates on a generated PDF.

    Args:
        pdf_path: Path to the PDF file.
        level: Briefing level (1-4) for threshold selection.
        thresholds: Optional dict with hard_min_bytes, soft_min_bytes, min_pages,
            strict. Missing keys take the level defaults.
        strict: When True, size and page thresholds fail the gate instead of warning.

    Returns:
        tuple: (passed: bool, report: list[str])
    """
    pdf_path = Path(pdf_path)
    report: list[str] = []
    passed = True

    th = resolve_thresholds(level, overrides=thresholds)
    if strict is not None:
        th["strict"] = strict
    hard_min = int(th["hard_min_bytes"])
    soft_min = int(th["soft_min_bytes"])
    min_pages = int(th["min_pages"])
    is_strict = bool(th["strict"])
    advisory = "FAIL" if is_strict else "WARN"

    if not pdf_path.exists():
        return False, [f"FAIL: File does not exist: {pdf_path}"]

    size = pdf_path.stat().st_size
    if size == 0:
        return False, [f"FAIL: File is empty (0 bytes): {pdf_path}"]

    try:
        header = pdf_path.read_bytes()[:5]
    except OSError as exc:
        return False, [f"FAIL: Could not read file: {exc}"]
    if header != b"%PDF-":
        passed = False
        report.append("FAIL: Invalid PDF header (not a PDF file)")
    else:
        report.append("PASS: Valid PDF header")

    if size < hard_min:
        report.append(f"{advisory}: Below hard minimum size ({size:,} < {hard_min:,} bytes)")
        passed = passed and not is_strict
    elif size < soft_min:
        report.append(f"WARN: Below soft target size ({size:,} < {soft_min:,} bytes)")
    else:
        report.append(f"PASS: File size {size:,} bytes (target: {soft_min:,}+)")

    try:
        from pypdf import PdfReader
    except ImportError:
        report.append("SKIP: pypdf not installed; page and text checks skipped")
        return passed, report

    try:
        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)
        first_text = (reader.pages[0].extract_text() or "").strip() if page_count else ""
        info = reader.metadata
    except Exception as exc:  # noqa: BLE001 — pypdf raises many types on damaged files
        return False, [*report, f"FAIL: PDF could not be parsed ({type(exc).__name__}: {exc})"]

    if page_count < 1:
        passed = False
        report.append("FAIL: PDF has no pages")
    elif page_count < min_pages:
        report.append(f"{advisory}: Low page count ({page_count} < {min_pages} target)")
        passed = passed and not is_strict
    else:
        report.append(f"PASS: Page count {page_count} (target: {min_pages}+)")

    if page_count and not first_text:
        passed = False
        report.append("FAIL: No extractable text on the first page")
    elif page_count:
        report.append("PASS: Text present on the first page")

    title = None
    if info is not None:
        title = getattr(info, "title", None) or (info.get("/Title") if hasattr(info, "get") else None)
    if title:
        report.append("PASS: PDF metadata present")
    else:
        report.append("WARN: No title in PDF metadata")

    return passed, report

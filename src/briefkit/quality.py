"""Quality gates for generated PDFs — two-tier thresholds."""
from __future__ import annotations

from pathlib import Path

# Default thresholds by level
DEFAULT_THRESHOLDS = {
    1: {"hard_min_bytes": 100_000, "soft_min_bytes": 500_000, "min_pages": 5},
    2: {"hard_min_bytes": 50_000, "soft_min_bytes": 200_000, "min_pages": 3},
    3: {"hard_min_bytes": 20_000, "soft_min_bytes": 80_000, "min_pages": 2},
    4: {"hard_min_bytes": 200_000, "soft_min_bytes": 1_000_000, "min_pages": 10},
}


def run_quality_gates(pdf_path, level=3, thresholds=None):
    """
    Run quality gates on a generated PDF.

    Args:
        pdf_path: Path to the PDF file.
        level: Briefing level (1-4) for threshold selection.
        thresholds: Optional dict with hard_min_bytes, soft_min_bytes, min_pages.
            If None, defaults for the given level are used.

    Returns:
        tuple: (passed: bool, report: list[str])
    """
    pdf_path = Path(pdf_path)
    report = []
    passed = True

    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS.get(level, DEFAULT_THRESHOLDS[3])

    hard_min = thresholds.get("hard_min_bytes", 20_000)
    soft_min = thresholds.get("soft_min_bytes", 80_000)
    min_pages = thresholds.get("min_pages", 2)

    # Check file exists
    if not pdf_path.exists():
        return False, [f"FAIL: File does not exist: {pdf_path}"]

    # Check file size
    size = pdf_path.stat().st_size
    if size == 0:
        return False, [f"FAIL: File is empty (0 bytes): {pdf_path}"]

    if size < hard_min:
        passed = False
        report.append(f"FAIL: Hard minimum size not met ({size:,} < {hard_min:,} bytes)")
    elif size < soft_min:
        report.append(f"WARN: Soft target size not met ({size:,} < {soft_min:,} bytes)")
    else:
        report.append(f"PASS: File size {size:,} bytes (target: {soft_min:,}+)")

    # Check valid PDF header
    try:
        header = pdf_path.read_bytes()[:5]
        if header != b"%PDF-":
            passed = False
            report.append("FAIL: Invalid PDF header (not a PDF file)")
        else:
            report.append("PASS: Valid PDF header")
    except OSError as exc:
        passed = False
        report.append(f"FAIL: Could not read file: {exc}")

    # Check page count and metadata (if pypdf available)
    try:
        from pypdf import PdfReader
    except ImportError:
        report.append("SKIP: pypdf not installed, page count check skipped")
    else:
        try:
            reader = PdfReader(str(pdf_path))

            # Page count
            page_count = len(reader.pages)
            if page_count < min_pages:
                report.append(f"WARN: Low page count ({page_count} < {min_pages} target)")
            else:
                report.append(f"PASS: Page count {page_count} (target: {min_pages}+)")

            # Metadata
            info = reader.metadata
            if info and (getattr(info, "title", None) or (hasattr(info, "get") and info.get("/Title"))):
                report.append("PASS: PDF metadata present")
            else:
                report.append("WARN: No title in PDF metadata")
        except Exception:  # noqa: BLE001 — pypdf may raise various errors
            report.append("WARN: Could not read page count")

    return passed, report

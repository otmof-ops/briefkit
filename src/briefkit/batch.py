"""
briefkit.batch
~~~~~~~~~~~~~~
Batch runner: discover directories that contain numbered Markdown docs
and generate briefings for all of them.
"""

from __future__ import annotations

import fnmatch
import os
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Target discovery
# ---------------------------------------------------------------------------

def _has_numbered_docs(directory: Path, pattern: str) -> bool:
    """Return True if *directory* directly contains files matching *pattern*."""
    try:
        for entry in directory.iterdir():
            if entry.is_file() and fnmatch.fnmatch(entry.name, pattern):
                return True
    except PermissionError:
        pass
    return False


def find_targets(root: str | Path, config: dict[str, Any]) -> list[Path]:
    """
    Walk the directory tree rooted at *root* and return every directory that
    contains at least one numbered Markdown document matching the configured
    pattern (content.numbered_doc_pattern).

    Directories named '.briefkit', '.git', '__pycache__', 'node_modules',
    or starting with '.' are excluded from traversal.

    Returns a sorted list of absolute Path objects.
    """
    root = Path(root).resolve()
    pattern: str = (
        config.get("content", {}).get("numbered_doc_pattern", "[0-9][0-9]-*.md")
    )
    skip_dirs = {".briefkit", ".git", "__pycache__", "node_modules", ".venv", "venv"}

    targets: list[Path] = []

    for dirpath, dirnames, _filenames in os.walk(root):
        current = Path(dirpath)

        # Prune traversal in-place
        dirnames[:] = [
            d for d in sorted(dirnames)
            if d not in skip_dirs and not d.startswith(".")
        ]

        if _has_numbered_docs(current, pattern):
            targets.append(current)

    return sorted(targets)


# ---------------------------------------------------------------------------
# Staleness detection
# ---------------------------------------------------------------------------

def _output_path(directory: Path, config: dict[str, Any]) -> Path:
    """Resolve the expected PDF output path for *directory*."""
    output_cfg = config.get("output", {})
    filename: str = output_cfg.get("filename", "executive-briefing.pdf")
    output_dir: str = output_cfg.get("output_dir", "")

    if output_dir:
        base = Path(output_dir).resolve()
        # Mirror directory structure relative to project root when output_dir is set
        try:
            rel = directory.relative_to(Path.cwd())
            return base / rel / filename
        except ValueError:
            return base / filename

    return directory / filename


def _is_current(directory: Path, output_pdf: Path, config: dict[str, Any]) -> bool:
    """
    Return True if *output_pdf* exists and is newer than all source Markdown
    files in *directory*.
    """
    if not output_pdf.exists():
        return False

    pdf_mtime = output_pdf.stat().st_mtime
    pattern: str = config.get("content", {}).get("numbered_doc_pattern", "[0-9][0-9]-*.md")
    orientation_pattern: str = config.get("content", {}).get(
        "orientation_doc_pattern", "00-what-is-*.md"
    )

    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        if fnmatch.fnmatch(entry.name, pattern) or fnmatch.fnmatch(entry.name, orientation_pattern):
            if entry.stat().st_mtime > pdf_mtime:
                return False

    return True


# ---------------------------------------------------------------------------
# Generation stub
# ---------------------------------------------------------------------------

def _generate_one(directory: Path, config: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    """
    Generate the briefing PDF for a single *directory*.

    This function is the integration point for the PDF renderer.  When the
    renderer module is available it delegates to it; otherwise it records the
    attempt so the batch runner can report accurate stats even in environments
    where the full render stack is not installed.

    Returns a result dict::

        {
            "path": str,          # absolute path to the directory
            "output": str,        # absolute path to the output PDF
            "status": str,        # "generated" | "dry_run" | "error"
            "message": str,       # human-readable detail
            "elapsed": float,     # seconds taken
        }
    """
    t0 = time.monotonic()
    output_pdf = _output_path(directory, config)
    result: dict[str, Any] = {
        "path": str(directory),
        "output": str(output_pdf),
        "status": "error",
        "message": "",
        "elapsed": 0.0,
    }

    if dry_run:
        result["status"] = "dry_run"
        result["message"] = f"Would generate {output_pdf}"
        result["elapsed"] = time.monotonic() - t0
        return result

    try:
        from briefkit.templates import get_template  # noqa: PLC0415
        template_name = config.get("template", {}).get("preset", "briefing")
        TemplateClass = get_template(template_name)
        tmpl = TemplateClass(directory, config=config)
        tmpl.generate()
        result["status"] = "generated"
        result["message"] = str(output_pdf)
    except Exception as exc:  # noqa: BLE001
        result["status"] = "error"
        result["message"] = str(exc)

    result["elapsed"] = time.monotonic() - t0
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def batch_generate(
    root: str | Path,
    config: dict[str, Any],
    force: bool = False,
    dry_run: bool = False,
    quiet: bool = False,
) -> dict[str, Any]:
    """
    Discover and generate briefings for every eligible directory under *root*.

    Parameters
    ----------
    root:
        Root directory to search.
    config:
        Resolved briefkit config dict (from ``load_config()``).
    force:
        When True, regenerate even if the output PDF is current.
    dry_run:
        When True, discover targets and report what *would* be done without
        actually generating anything.
    quiet:
        Suppress progress output to stdout.

    Returns
    -------
    dict with keys:
        total       — number of eligible directories found
        generated   — number of briefings generated (or dry-run candidates)
        skipped     — number skipped because output was already current
        failed      — number that raised errors
        results     — list of per-directory result dicts
        elapsed     — total wall-clock seconds
    """
    root = Path(root).resolve()
    skip_current: bool = config.get("output", {}).get("skip_current", True)

    t_start = time.monotonic()

    targets = find_targets(root, config)

    stats: dict[str, Any] = {
        "total": len(targets),
        "generated": 0,
        "skipped": 0,
        "failed": 0,
        "results": [],
        "elapsed": 0.0,
    }

    if not targets:
        if not quiet:
            print(f"No eligible directories found under {root}", file=sys.stderr)
        stats["elapsed"] = time.monotonic() - t_start
        return stats

    width = len(str(len(targets)))

    for idx, directory in enumerate(targets, start=1):
        output_pdf = _output_path(directory, config)
        rel = _safe_relative(directory, root)

        if not force and skip_current and _is_current(directory, output_pdf, config):
            if not quiet:
                print(
                    f"  [{idx:{width}d}/{len(targets)}] SKIP     {rel}  (current)",
                    flush=True,
                )
            stats["skipped"] += 1
            stats["results"].append(
                {
                    "path": str(directory),
                    "output": str(output_pdf),
                    "status": "skipped",
                    "message": "Output is current",
                    "elapsed": 0.0,
                }
            )
            continue

        if not quiet:
            verb = "DRY-RUN" if dry_run else "GENERATE"
            print(f"  [{idx:{width}d}/{len(targets)}] {verb:<8} {rel}", flush=True)

        result = _generate_one(directory, config, dry_run=dry_run)
        stats["results"].append(result)

        if result["status"] in ("generated", "dry_run"):
            stats["generated"] += 1
            if not quiet:
                elapsed_str = f"{result['elapsed']:.1f}s"
                print(f"             -> {result['message']}  ({elapsed_str})", flush=True)
        else:
            stats["failed"] += 1
            if not quiet:
                print(
                    f"             ERROR: {result['message']}",
                    file=sys.stderr,
                    flush=True,
                )

    stats["elapsed"] = time.monotonic() - t_start

    if not quiet:
        _print_summary(stats)

    return stats


def _safe_relative(path: Path, base: Path) -> str:
    """Return a path relative to *base*, falling back to absolute if needed."""
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def _print_summary(stats: dict[str, Any]) -> None:
    total = stats["total"]
    generated = stats["generated"]
    skipped = stats["skipped"]
    failed = stats["failed"]
    elapsed = stats["elapsed"]

    print()
    print(f"  Batch complete in {elapsed:.1f}s")
    print(f"  {total} target(s) found — "
          f"{generated} generated, {skipped} skipped, {failed} failed")

    if failed:
        print(f"\n  Failed directories:")
        for r in stats["results"]:
            if r["status"] == "error":
                print(f"    - {r['path']}")
                print(f"      {r['message']}")

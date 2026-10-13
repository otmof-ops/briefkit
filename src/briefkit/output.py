"""
briefkit.output
~~~~~~~~~~~~~~~
Where a generated PDF goes, decided in one place.

Every path that writes a PDF (``generate``, ``batch``, ``status``, the
templates) resolves it through :func:`resolve_output_path`, so the path the
CLI prints is the path the file lands on, and a ``briefkit.yml`` from an
untrusted checkout cannot steer the write outside the directories briefkit
is meant to touch.
"""

from __future__ import annotations

from pathlib import Path, PurePath
from typing import Any

DEFAULT_FILENAME = "executive-briefing.pdf"


def validate_output_filename(name: Any) -> str | None:
    """
    Return an error message when *name* is not a bare ``.pdf`` file name.

    ``output.filename`` is joined onto the source directory, so anything that
    carries a directory part would escape it: ``../../x`` walks up and an
    absolute name replaces the directory outright.  Returns ``None`` when the
    name is acceptable.
    """
    if not isinstance(name, str) or not name:
        return "output.filename must be a non-empty string"
    if "\x00" in name:
        return "output.filename must not contain a NUL character"
    if name in (".", "..") or "/" in name or "\\" in name or PurePath(name).name != name:
        return f"output.filename must be a bare file name with no directory part, got: {name!r}"
    if not name.lower().endswith(".pdf"):
        return f"output.filename must end in .pdf, got: {name!r}"
    return None


def validate_output_dir(value: Any) -> str | None:
    """Return an error message when ``output.output_dir`` is unacceptable, else ``None``."""
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        return f"output.output_dir must be a string, got: {value!r}"
    if "\x00" in value:
        return "output.output_dir must not contain a NUL character"
    if ".." in PurePath(value).parts:
        return f"output.output_dir must not contain '..', got: {value!r}"
    return None


def _anchor(project_root: Path | None) -> Path:
    return (project_root or Path.cwd()).resolve()


def output_root(target: str | Path, config: dict, project_root: Path | None = None) -> Path:
    """
    The directory a PDF for *target* is confined to.

    ``output.output_dir`` when set (anchored at the project root, or the
    current directory when there is none); otherwise *target* itself.
    """
    out_cfg = config.get("output", {}) or {}
    output_dir = out_cfg.get("output_dir", "") or ""
    if output_dir:
        base = Path(output_dir)
        if not base.is_absolute():
            base = _anchor(project_root) / base
        return base.resolve()
    return Path(target).resolve()


def resolve_output_path(
    target: str | Path,
    config: dict,
    *,
    override: str | Path | None = None,
    project_root: Path | None = None,
) -> Path:
    """
    Decide the PDF path for *target*.

    1. *override* (the ``--output`` flag) is operator-supplied and used as
       given.  A path that names an existing directory, or ends in a path
       separator, receives ``output.filename`` inside it.
    2. ``output.output_dir`` mirrors *target*'s path relative to the project
       root beneath that directory, so ``docs/a`` becomes
       ``<output_dir>/docs/a/<filename>``.  A target outside the project root
       lands in ``<output_dir>/<target name>/``.
    3. Otherwise the PDF sits next to its sources: ``<target>/<filename>``.

    Cases 2 and 3 are checked to stay inside :func:`output_root`; a
    configuration that would write elsewhere raises ``ValueError``.
    """
    target = Path(target).resolve()
    out_cfg = config.get("output", {}) or {}
    filename = out_cfg.get("filename", DEFAULT_FILENAME) or DEFAULT_FILENAME
    problem = validate_output_filename(filename)
    if problem:
        raise ValueError(problem)

    if override is not None:
        raw = str(override)
        candidate = Path(raw).expanduser()
        if raw.endswith(("/", "\\")) or candidate.is_dir():
            candidate = candidate / filename
        return candidate.resolve()

    root = output_root(target, config, project_root)
    if out_cfg.get("output_dir"):
        anchor = _anchor(project_root)
        try:
            rel = target.relative_to(anchor)
        except ValueError:
            rel = Path(target.name)
        candidate = root / rel / filename
    else:
        candidate = target / filename

    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"output path {resolved} escapes the output directory {root}")
    return resolved


__all__ = [
    "DEFAULT_FILENAME",
    "output_root",
    "resolve_output_path",
    "validate_output_dir",
    "validate_output_filename",
]

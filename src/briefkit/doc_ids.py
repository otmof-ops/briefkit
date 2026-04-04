"""
briefkit.doc_ids
~~~~~~~~~~~~~~~~
Document ID registry — assign and look up stable identifiers for generated PDFs.

Extracted and generalized from generate-briefing-v2.py get_or_assign_doc_id()
(original lines 124-170).  All Codex-specific division codes replaced with
group_codes from config.doc_ids.

Public API
----------
  get_or_assign_doc_id(path, level, title, config)  ->  str
  assign(root, config, dry_run=False)               ->  int
  load_registry(path)                               ->  dict
  save_registry(registry, path)
"""

from __future__ import annotations

import datetime
import json
import re as _re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Registry I/O
# ---------------------------------------------------------------------------

def load_registry(registry_path: Path) -> dict:
    """Load the document ID registry from *registry_path*. Returns empty registry if missing."""
    if registry_path.exists():
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            # Build path index for O(1) lookups
            data["_index"] = {e["path"]: e["doc_id"] for e in data.get("entries", [])}
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"schema_version": 1, "counters": {}, "entries": [], "_index": {}}


def save_registry(registry: dict, registry_path: Path) -> None:
    """Write the registry atomically to *registry_path*."""
    import tempfile
    import os

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    # Strip internal index before persisting
    to_save = {k: v for k, v in registry.items() if k != "_index"}
    fd, tmp_path = tempfile.mkstemp(dir=str(registry_path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=2)
        os.replace(tmp_path, str(registry_path))
    except BaseException:
        os.unlink(tmp_path)
        raise


# ---------------------------------------------------------------------------
# ID format helpers
# ---------------------------------------------------------------------------

_ALLOWED_FORMAT_FIELDS = frozenset({"prefix", "type", "group", "level", "seq", "year"})
_FORMAT_FIELD_RE = _re.compile(r'\{(\w+)\}')

def _validate_format_string(fmt: str, allowed: frozenset[str]) -> None:
    """Raise ValueError if *fmt* contains field names outside *allowed*."""
    for m in _FORMAT_FIELD_RE.finditer(fmt):
        field = m.group(1)
        if field not in allowed:
            raise ValueError(
                f"Invalid format field {{{field}}} in doc_ids.format. "
                f"Allowed fields: {sorted(allowed)}"
            )


def _format_doc_id(
    level:    int,
    seq:      int,
    group:    str,
    config:   dict,
) -> str:
    """
    Format a document ID string from config.doc_ids format template.

    Template variables:
      {prefix}   — config.doc_ids.prefix (default "DOC")
      {type}     — config.doc_ids.type   (default "BRF")
      {group}    — division/group code derived from path
      {level}    — hierarchy level integer
      {seq}      — zero-padded sequence number
      {year}     — 2-digit (short) or 4-digit (full) year
    """
    doc_ids_cfg = config.get("doc_ids", {})
    fmt      = doc_ids_cfg.get("format", "{prefix}-{type}-{group}-{level}{seq}/{year}")
    prefix   = doc_ids_cfg.get("prefix", "DOC")
    type_    = doc_ids_cfg.get("type",   "BRF")
    digits   = doc_ids_cfg.get("sequence_digits", 4)
    yr_fmt   = doc_ids_cfg.get("year_format", "short")

    today = datetime.date.today()
    if yr_fmt == "full":
        year = today.strftime("%Y")
    else:
        year = today.strftime("%y")

    seq_str = str(seq).zfill(digits)

    _validate_format_string(fmt, _ALLOWED_FORMAT_FIELDS)
    return fmt.format(
        prefix=prefix,
        type=type_,
        group=group,
        level=level,
        seq=seq_str,
        year=year,
    )


def _derive_group_code(path: Path, config: dict) -> str:
    """
    Derive a short group code from *path* by checking config.doc_ids.group_codes.

    Falls back to the first non-hidden directory component not matching
    common project root names.
    """
    doc_ids_cfg = config.get("doc_ids", {})
    group_codes: dict[str, str] = doc_ids_cfg.get("group_codes", {})

    # Check each path part against the group_codes mapping
    for part in path.parts:
        code = group_codes.get(part)
        if code:
            return code

    # Fallback: uppercase first 3 chars of deepest meaningful component
    for part in reversed(path.parts):
        if part not in ("/", "\\", ".", "") and not part.startswith("."):
            return part[:3].upper().replace("-", "X")

    return "GEN"


# ---------------------------------------------------------------------------
# get_or_assign_doc_id
# ---------------------------------------------------------------------------

def get_or_assign_doc_id(
    target_path: str | Path,
    level:       int,
    title:       str,
    config:      dict | None = None,
) -> str:
    """
    Look up an existing doc ID for *target_path*, or assign the next sequential ID.

    The registry is stored at config.doc_ids.registry_path (relative to the
    project root, or as an absolute path).  Defaults to .briefkit/registry.json
    in CWD if config is not provided.

    Returns the doc ID string.
    """
    config = config or {}
    doc_ids_cfg = config.get("doc_ids", {})

    if not doc_ids_cfg.get("enabled", True):
        return ""

    registry_rel = doc_ids_cfg.get("registry_path", ".briefkit/registry.json")
    registry_path = Path(registry_rel)
    root = None
    if not registry_path.is_absolute():
        # Resolve relative to project root or CWD
        from briefkit.config import find_project_root
        root = find_project_root() or Path.cwd()
        registry_path = root / registry_rel

    resolved = registry_path.resolve()
    if root and not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"registry_path must be within project root, got: {registry_path}")

    target = Path(target_path).resolve()

    # Build a stable key from the output path
    out_filename = config.get("output", {}).get("filename", "executive-briefing.pdf")
    key = str(target / out_filename)

    registry = load_registry(registry_path)

    # Return existing ID if found (O(1) lookup via index)
    existing = registry.get("_index", {}).get(key)
    if existing:
        return existing

    # Assign new ID
    group = _derive_group_code(target, config)

    counters = registry.setdefault("counters", {})
    group_counters = counters.setdefault(group, {})
    level_key = f"L{level}"
    group_counters[level_key] = group_counters.get(level_key, 0) + 1
    seq = group_counters[level_key]

    doc_id = _format_doc_id(level, seq, group, config)

    registry.setdefault("entries", []).append({
        "doc_id":   doc_id,
        "path":     key,
        "group":    group,
        "level":    level,
        "title":    title,
        "assigned": datetime.date.today().isoformat(),
    })
    registry.setdefault("_index", {})[key] = doc_id

    save_registry(registry, registry_path)
    return doc_id


# ---------------------------------------------------------------------------
# assign — batch assignment for CLI
# ---------------------------------------------------------------------------

def assign(
    root:    str | Path,
    config:  dict,
    dry_run: bool = False,
) -> int:
    """
    Walk *root* and ensure every directory that contains a generated PDF has a
    doc ID assigned in the registry.

    Returns the count of IDs assigned (or that would be assigned in dry-run).
    """
    root = Path(root).resolve()
    out_filename = config.get("output", {}).get("filename", "executive-briefing.pdf")
    count = 0

    for pdf in sorted(root.rglob(out_filename)):
        if pdf.is_symlink():
            continue
        target = pdf.parent
        if dry_run:
            count += 1
            continue
        existing = get_or_assign_doc_id(target, level=3, title=target.name, config=config)
        if existing:
            count += 1

    return count

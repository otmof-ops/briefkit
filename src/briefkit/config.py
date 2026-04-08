"""
briefkit.config
~~~~~~~~~~~~~~~
YAML config loader with deep-merge, preset resolution, and validation.
Zero-config: every field has a sensible default.
"""

from __future__ import annotations

import copy
import functools
import re
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyYAML is required: pip install pyyaml") from exc

from briefkit.styles import DEFAULT_BRAND as _DEFAULT_BRAND

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULTS: dict[str, Any] = {
    "project": {
        "name": "",
        "org": "",
        "tagline": "",
        "url": "",
        "copyright": "© {year} {org}",
        "abn": "",
    },
    "brand": {
        **_DEFAULT_BRAND,
        "preset": "navy",
        "logo": "",
    },
    "doc_ids": {
        "enabled": True,
        "format": "{prefix}-{type}-{group}-{level}{seq}/{year}",
        "prefix": "DOC",
        "type": "BRF",
        "year_format": "short",
        "sequence_digits": 4,
        "registry_path": ".briefkit/registry.json",
        "group_codes": {},
    },
    "layout": {
        "page_size": "A4",
        "orientation": "portrait",
        "margins": {"top": 25, "bottom": 22, "left": 20, "right": 20},
        "font_family": "Helvetica",
        "font_size": {
            "body": 10,
            "h1": 16,
            "h2": 13,
            "h3": 11,
            "caption": 8,
            "code": 8.5,
        },
    },
    "content": {
        "max_words_per_section": 3000,
        "max_terms_in_index": 40,
        "max_bibliography_entries": 100,
        "max_cross_refs": 30,
        "citation_formats": [
            "apa",
            "author_year",
            "bracketed",
            "legislation",
            "rfc",
            "case_law",
        ],
        "generic_terms_filter": True,
        "orientation_doc_pattern": "00-what-is-*.md",
        "numbered_doc_pattern": "[0-9][0-9]-*.md",
    },
    "hierarchy": {
        "depth_to_level": {0: 1, 1: 2, 2: 3},
        "root_level": 4,
    },
    "template": {
        "preset": "briefing",
        "sections": {
            "cover": True,
            "classification_banner": True,
            "toc": True,
            "executive_summary": True,
            "at_a_glance": True,
            "body": True,
            "cross_references": True,
            "key_terms": True,
            "bibliography": True,
            "back_cover": True,
        },
        "custom_sections": [],
    },
    "license": {
        "preset": "",
        "name": "",
        "spdx": "",
        "url": "",
        "notice": "",
    },
    "variants": {
        "rules": [],
        "auto_detect": True,
    },
    "output": {
        "filename": "executive-briefing.pdf",
        "output_dir": "",
        "skip_current": True,
        "report_format": "markdown",
    },
    "constraints": [],
}

# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

_VALID_PAGE_SIZES = {"A4", "A3", "Letter", "Legal", "Tabloid"}
_VALID_ORIENTATIONS = {"portrait", "landscape"}
_VALID_REPORT_FORMATS = {"markdown", "json", "text"}
_VALID_YEAR_FORMATS = {"short", "full"}
_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

_COLOR_KEYS = frozenset({
    "primary", "secondary", "accent", "body_text", "caption", "background", "rule",
    "success", "warning", "danger", "code_bg", "table_alt",
})

_FONT_KEYS = frozenset({"font_body", "font_heading", "font_mono", "font_caption"})


def _validate_config(cfg: dict[str, Any]) -> list[str]:
    """Return a list of validation error messages (empty means valid)."""
    errors: list[str] = []

    layout = cfg.get("layout", {})
    if layout.get("page_size") not in _VALID_PAGE_SIZES:
        errors.append(
            f"layout.page_size must be one of {sorted(_VALID_PAGE_SIZES)}, "
            f"got: {layout.get('page_size')!r}"
        )
    if layout.get("orientation") not in _VALID_ORIENTATIONS:
        errors.append(
            f"layout.orientation must be 'portrait' or 'landscape', "
            f"got: {layout.get('orientation')!r}"
        )

    margins = layout.get("margins", {})
    for side in ("top", "bottom", "left", "right"):
        val = margins.get(side)
        if val is not None and not isinstance(val, (int, float)):
            errors.append(f"layout.margins.{side} must be a number, got: {val!r}")
        if isinstance(val, (int, float)) and val < 0:
            errors.append(f"layout.margins.{side} must be >= 0, got: {val}")

    brand = cfg.get("brand", {})
    for color_key in _COLOR_KEYS:
        val = brand.get(color_key, "")
        if val and not _HEX_COLOR_RE.match(val):
            errors.append(
                f"brand.{color_key} must be a 6-digit hex color (e.g. #1B2A4A), "
                f"got: {val!r}"
            )

    output = cfg.get("output", {})
    if output.get("report_format") not in _VALID_REPORT_FORMATS:
        errors.append(
            f"output.report_format must be one of {sorted(_VALID_REPORT_FORMATS)}, "
            f"got: {output.get('report_format')!r}"
        )

    doc_ids = cfg.get("doc_ids", {})
    digits = doc_ids.get("sequence_digits")
    if digits is not None and (not isinstance(digits, int) or digits < 1 or digits > 8):
        errors.append(f"doc_ids.sequence_digits must be an integer 1–8, got: {digits!r}")

    if doc_ids.get("year_format") not in _VALID_YEAR_FORMATS:
        errors.append(
            f"doc_ids.year_format must be 'short' or 'full', "
            f"got: {doc_ids.get('year_format')!r}"
        )

    content = cfg.get("content", {})
    for int_key in (
        "max_words_per_section",
        "max_terms_in_index",
        "max_bibliography_entries",
        "max_cross_refs",
    ):
        val = content.get(int_key)
        if val is not None and (not isinstance(val, int) or val < 0):
            errors.append(
                f"content.{int_key} must be a non-negative integer, got: {val!r}"
            )

    # Validate brand.logo path if set
    logo = brand.get("logo", "")
    if logo:
        logo_path = Path(logo)
        _ALLOWED_LOGO_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".gif"}
        if logo_path.suffix.lower() not in _ALLOWED_LOGO_EXTS:
            errors.append(
                f"brand.logo must have one of {sorted(_ALLOWED_LOGO_EXTS)} extension, "
                f"got: {logo_path.suffix!r}"
            )
        # Resolve relative paths before symlink check — prevents bypass
        try:
            resolved_logo = logo_path.resolve() if logo_path.is_absolute() else (Path.cwd() / logo_path)
            if resolved_logo.is_symlink():
                errors.append("brand.logo must not be a symlink")
        except (OSError, ValueError):
            pass

    # Validate output_dir is not an escape path
    output_dir = output.get("output_dir", "")
    if output_dir and ".." in str(output_dir):
        errors.append(f"output.output_dir must not contain '..', got: {output_dir!r}")

    # Validate glob patterns don't contain dangerous traversal
    for pat_key in ("orientation_doc_pattern", "numbered_doc_pattern"):
        pat = content.get(pat_key, "")
        if pat and (".." in pat or pat.startswith("/")):
            errors.append(f"content.{pat_key} must not contain '..' or start with '/', got: {pat!r}")

    # Validate doc_ids prefix and type are alphanumeric
    _SAFE_ID_RE = re.compile(r'^[A-Za-z0-9\-]*$')
    for id_key in ("prefix", "type"):
        val = doc_ids.get(id_key, "")
        if val and not _SAFE_ID_RE.match(val):
            errors.append(
                f"doc_ids.{id_key} must be alphanumeric/hyphens only, got: {val!r}"
            )

    # Skip-flag typo detection
    # ------------------------
    # Users can set project.skip_<section>: true to suppress optional
    # sections. A typo like `skip_prefece` silently does nothing because
    # no template ever queries it. Catch such typos here and suggest the
    # closest canonical section name.
    project_cfg = cfg.get("project", {}) or {}
    if isinstance(project_cfg, dict):
        try:
            from briefkit.templates._helpers import SKIPPABLE_SECTIONS
        except Exception:
            SKIPPABLE_SECTIONS = ()  # type: ignore
        from difflib import get_close_matches
        for key in list(project_cfg.keys()):
            if not key.startswith("skip_"):
                continue
            section = key[len("skip_"):]
            if section in SKIPPABLE_SECTIONS:
                continue
            suggestions = get_close_matches(section, SKIPPABLE_SECTIONS, n=1, cutoff=0.6)
            if suggestions:
                errors.append(
                    f"project.{key}: unknown section {section!r}. "
                    f"Did you mean 'skip_{suggestions[0]}'?"
                )
            else:
                errors.append(
                    f"project.{key}: unknown section {section!r}. "
                    f"Valid sections: {', '.join(SKIPPABLE_SECTIONS[:10])}..."
                )

    return errors


# ---------------------------------------------------------------------------
# Deep merge
# ---------------------------------------------------------------------------


def _deep_merge(base: dict, override: dict) -> dict:
    """
    Recursively merge *override* into a copy of *base*.
    Lists are replaced (not appended). Scalar values are replaced.
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


# ---------------------------------------------------------------------------
# Project root discovery
# ---------------------------------------------------------------------------

# briefkit-specific markers only. pyproject.toml was removed in 2026-04
# because it made ANY Python project look like a briefkit root, silently
# substituting defaults instead of warning "no briefkit.yml found".
_ROOT_MARKERS = ("briefkit.yml", "briefkit.yaml", ".briefkit")


def find_project_root(start_path: str | Path | None = None) -> Path | None:
    """
    Walk up the directory tree from *start_path* (defaults to CWD) looking
    for any of: briefkit.yml, briefkit.yaml, .briefkit/.

    Returns the first ancestor that contains a marker, or None if not found.
    """
    key = str(Path(start_path).resolve()) if start_path else None
    return _find_project_root_cached(key)


def clear_project_root_cache() -> None:
    """
    Clear the cached project-root lookups.

    Call this when a ``briefkit.yml`` has been created, moved, or
    deleted during the lifetime of a long-running process (tests,
    watch mode, IDE integrations). Without clearing, the process will
    keep returning the stale root.
    """
    _find_project_root_cached.cache_clear()


@functools.lru_cache(maxsize=128)
def _find_project_root_cached(start_key: str | None) -> Path | None:
    """Cached implementation of find_project_root."""
    current = Path(start_key) if start_key else Path.cwd().resolve()

    # Guard against infinite loop at filesystem root
    for _ in range(64):
        for marker in _ROOT_MARKERS:
            if (current / marker).exists():
                return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def _locate_config_file(config_path: str | Path | None) -> Path | None:
    """Resolve the briefkit.yml path to load, or None if not found."""
    if config_path is not None:
        p = Path(config_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {p}")
        return p

    root = find_project_root()
    if root is None:
        return None

    for name in ("briefkit.yml", "briefkit.yaml"):
        candidate = root / name
        if candidate.exists():
            return candidate

    return None


# ---------------------------------------------------------------------------
# Brand preset resolution
# ---------------------------------------------------------------------------


def resolve_brand(
    config: dict[str, Any],
    user_brand_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Apply the named color preset to the brand section of *config*.

    Resolution order (highest wins):
      1. Color preset values
      2. Explicit per-key overrides supplied in *user_brand_overrides*

    *user_brand_overrides* should contain only the color keys that the
    user explicitly set in their briefkit.yml (not defaults or previously
    resolved preset values).  ``load_config`` extracts this automatically.

    When brand.preset is "custom", no preset is applied and only
    *user_brand_overrides* (if any) are written to the brand section.

    Returns a new config dict; does not mutate in place.
    """
    from briefkit.presets.colors import PRESETS  # noqa: PLC0415

    cfg = copy.deepcopy(config)
    brand = cfg.setdefault("brand", {})
    preset_name = brand.get("preset", "navy")

    if preset_name != "custom":
        preset_colors = PRESETS.get(preset_name)
        if preset_colors is None:
            available = ", ".join(sorted(PRESETS))
            raise ValueError(
                f"Unknown color preset: {preset_name!r}. "
                f"Available presets: {available}"
            )
        brand.update(preset_colors)

    # Re-apply explicit user overrides so they win over the preset
    if user_brand_overrides:
        for k, v in user_brand_overrides.items():
            brand[k] = v

    return cfg


# ---------------------------------------------------------------------------
# Auto-populate dynamic defaults
# ---------------------------------------------------------------------------


def _apply_dynamic_defaults(cfg: dict[str, Any], root: Path | None) -> dict[str, Any]:
    """Fill in fields that derive from the runtime environment."""
    cfg = copy.deepcopy(cfg)

    project = cfg.setdefault("project", {})

    # Auto-detect project name from directory
    if not project.get("name"):
        if root is not None:
            project["name"] = root.name
        else:
            project["name"] = Path.cwd().name

    # Expand copyright template
    year = date.today().year
    org = project.get("org", "")
    copyright_tpl = project.get("copyright", "© {year} {org}")
    # Safe substitution — only {year} and {org} are allowed
    project["copyright"] = copyright_tpl.replace("{year}", str(year)).replace("{org}", org)

    return cfg


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """
    Load briefkit configuration.

    Resolution order:
      1. Built-in defaults (DEFAULTS)
      2. briefkit.yml found by walking up from CWD (or *config_path* if given)
      3. Dynamic defaults (project name, copyright year expansion)
      4. Brand preset color resolution

    The user's explicit color overrides (those present in the YAML file under
    ``brand:``) survive preset application — the preset fills in any unspecified
    colors, but does not clobber explicitly set values.

    Returns the fully resolved config dict.
    Raises ValueError if validation fails.
    """
    cfg = copy.deepcopy(DEFAULTS)
    root: Path | None = None
    user_brand_overrides: dict[str, str] = {}

    config_file = _locate_config_file(config_path)

    if config_file is not None:
        root = config_file.parent
        with config_file.open("r", encoding="utf-8") as fh:
            user_data = yaml.safe_load(fh)
        if user_data is not None:
            if not isinstance(user_data, dict):
                raise ValueError(
                    f"briefkit.yml must be a YAML mapping at the top level, "
                    f"got: {type(user_data).__name__}"
                )
            # Capture explicit color overrides before merging with defaults
            raw_brand = user_data.get("brand", {})
            user_brand_overrides = {
                k: v for k, v in raw_brand.items() if k in _COLOR_KEYS or k in _FONT_KEYS
            }
            cfg = _deep_merge(cfg, user_data)
    else:
        root = find_project_root()

    # Expand hierarchy depth_to_level keys — YAML loads integer keys as ints,
    # but if loaded from file they may be strings; normalise to int.
    h = cfg.get("hierarchy", {})
    dtl = h.get("depth_to_level", {})
    h["depth_to_level"] = {int(k): int(v) for k, v in dtl.items()}

    cfg = _apply_dynamic_defaults(cfg, root)
    cfg = resolve_brand(cfg, user_brand_overrides=user_brand_overrides)
    cfg = _resolve_license(cfg)

    errors = _validate_config(cfg)
    if errors:
        bullet_list = "\n  - ".join(errors)
        raise ValueError(f"Configuration errors:\n  - {bullet_list}")

    return cfg


def _resolve_license(config: dict[str, Any]) -> dict[str, Any]:
    """Apply the named license preset to the license section of *config*."""
    cfg = copy.deepcopy(config)
    lic = cfg.setdefault("license", {})
    preset_name = lic.get("preset", "")

    if not preset_name:
        return cfg

    from briefkit.presets.licenses import LICENSE_PRESETS  # noqa: PLC0415

    preset = LICENSE_PRESETS.get(preset_name)
    if preset is None:
        available = ", ".join(sorted(LICENSE_PRESETS))
        raise ValueError(
            f"Unknown license preset: {preset_name!r}. "
            f"Available presets: {available}"
        )

    # Fill in unset fields from preset
    for key in ("name", "spdx", "url", "notice"):
        if not lic.get(key):
            lic[key] = preset.get(key, "")

    return cfg

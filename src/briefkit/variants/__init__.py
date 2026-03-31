"""
briefkit.variants — Variant plugin system.

A variant adds domain-specific flowable sections on top of any template.
Each variant is a subclass of DocSetVariant that implements
``build_variant_sections(content, flowables, styles, brand)``.

Registry
--------
All built-in variants are registered by their ``name`` attribute.
Use ``get_variant(name)`` to retrieve a variant instance by name.
Use ``auto_detect_variant(text)`` to pick a variant based on content keywords.
"""

from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------


def collect_text(content: dict) -> str:
    """Aggregate all text content from a content dict for keyword matching."""
    parts = [content.get("overview", ""), content.get("title", "")]
    for sub in content.get("subsystems", []):
        parts.append(sub.get("content", ""))
        parts.append(sub.get("name", ""))
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class DocSetVariant:
    """
    Base class for all document-set variants.

    Subclasses must set a unique ``name`` and a non-empty
    ``auto_detect_keywords`` list, and must override
    ``build_variant_sections``.
    """

    name: str = "base"
    auto_detect_keywords: list[str] = []

    def matches_content(self, text: str) -> bool:
        """
        Return True when at least 2 of the variant's keywords are present in
        *text* (case-insensitive).  Override for custom matching logic.
        """
        text_lower = text.lower()
        matches = sum(1 for kw in self.auto_detect_keywords if kw in text_lower)
        return matches >= 2

    def build_variant_sections(
        self,
        content: dict,
        flowables: list,
        styles: dict,
        brand: dict | None,
    ) -> list:
        """
        Add domain-specific flowables to *flowables* and return the list.

        Parameters
        ----------
        content : dict
            Parsed document content dict (keys: title, overview, subsystems,
            tables, terms, metrics, …).
        flowables : list
            Existing list of ReportLab flowables to append to.
        styles : dict
            Style dict from ``briefkit.styles.build_styles(brand)``.
        brand : dict or None
            Brand config dict.

        Returns
        -------
        list
            The modified *flowables* list.
        """
        return flowables


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, DocSetVariant] = {}


def _register(variant_cls):
    """Register a variant class instance by its ``name`` attribute."""
    instance = variant_cls()
    _REGISTRY[instance.name] = instance
    return variant_cls


def get_variant(name: str) -> Optional[DocSetVariant]:
    """
    Return the registered variant with the given *name*, or None if unknown.

    Parameters
    ----------
    name : str
        Variant name, e.g. ``'aiml'``, ``'legal'``, ``'medical'``.
    """
    _ensure_registry_populated()
    return _REGISTRY.get(name)


def list_variants() -> list[str]:
    """Return a sorted list of all registered variant names."""
    _ensure_registry_populated()
    return sorted(_REGISTRY.keys())


def auto_detect_variant(text: str) -> Optional[DocSetVariant]:
    """
    Scan *text* against every registered variant's ``auto_detect_keywords``.

    Returns the variant with the highest keyword match count (minimum 2),
    or None if no variant reaches the threshold.

    Parameters
    ----------
    text : str
        Raw document text used for keyword scoring.
    """
    _ensure_registry_populated()
    text_lower = text.lower()
    best: Optional[DocSetVariant] = None
    best_count = 1  # require at least 2 to beat this seed

    for variant in _REGISTRY.values():
        count = sum(1 for kw in variant.auto_detect_keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best = variant

    return best


# ---------------------------------------------------------------------------
# Lazy import — populate registry on first use
# ---------------------------------------------------------------------------

_registry_populated = False


def _ensure_registry_populated() -> None:
    global _registry_populated
    if _registry_populated:
        return
    _registry_populated = True

    # Import all built-in variants so their @_register decorators fire.
    # Import order is irrelevant; all end up in _REGISTRY.
    from briefkit.variants import (  # noqa: F401
        aiml,
        legal,
        medical,
        engineering,
        research,
        api,
        gaming,
        finance,
        species,
        historical,
        hardware,
        religion,
    )

"""
briefkit.presets
~~~~~~~~~~~~~~~~
Public API for color scheme presets.
"""

from __future__ import annotations

from briefkit.presets.colors import PRESETS


def get_preset(name: str) -> dict[str, str]:
    """
    Return the color dict for *name*.

    Raises KeyError if the preset does not exist — use list_presets() to
    enumerate valid names.
    """
    try:
        return dict(PRESETS[name])
    except KeyError:
        available = ", ".join(sorted(PRESETS))
        raise KeyError(
            f"Color preset {name!r} not found. "
            f"Available presets: {available}"
        ) from None


def list_presets() -> list[str]:
    """Return a sorted list of all available preset names."""
    return sorted(PRESETS.keys())


__all__ = ["get_preset", "list_presets", "PRESETS"]

"""Tests for briefkit color presets."""
from __future__ import annotations

import pytest

from briefkit.presets import get_preset, list_presets


class TestPresets:

    def test_list_presets_non_empty(self):
        names = list_presets()
        assert len(names) > 0

    def test_list_presets_includes_navy(self):
        assert "navy" in list_presets()

    def test_get_preset_navy(self):
        preset = get_preset("navy")
        assert isinstance(preset, dict)
        assert "primary" in preset

    def test_get_preset_unknown_raises(self):
        with pytest.raises(KeyError):
            get_preset("nonexistent_preset_xyz")

    def test_all_presets_have_primary(self):
        for name in list_presets():
            preset = get_preset(name)
            assert "primary" in preset, f"Preset {name} missing 'primary' key"

    def test_preset_colors_are_hex(self):
        import re
        hex_re = re.compile(r'^#[0-9A-Fa-f]{6}$')
        for name in list_presets():
            preset = get_preset(name)
            for key, val in preset.items():
                if key.startswith("font_") or key in ("logo", "org", "tagline", "abn", "url", "copyright"):
                    continue
                assert hex_re.match(val), f"Preset {name}.{key} = {val!r} is not a valid hex color"

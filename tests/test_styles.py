"""Tests for briefkit styles module."""
from __future__ import annotations

from briefkit.styles import (
    DEFAULT_BRAND,
    _get_brand,
    _safe_text,
    build_styles,
    truncate_to_width,
)


class TestSafeText:

    def test_empty_string(self):
        assert _safe_text("") == ""

    def test_none_returns_empty(self):
        assert _safe_text(None) == ""

    def test_plain_text_unchanged(self):
        result = _safe_text("Hello world")
        assert "Hello world" in result

    def test_escapes_bare_angle_brackets(self):
        result = _safe_text("a < b > c")
        assert "&lt;" in result or "<" not in result.replace("<b>", "").replace("<i>", "")

    def test_preserves_bold_tags(self):
        result = _safe_text("<b>bold</b>")
        assert "<b>bold</b>" in result

    def test_preserves_italic_tags(self):
        result = _safe_text("<i>italic</i>")
        assert "<i>italic</i>" in result

    def test_sanitizes_font_name(self):
        result = _safe_text('<font name="Helvetica">text</font>')
        assert 'name="Helvetica"' in result

    def test_rejects_unsafe_font_name(self):
        result = _safe_text('<font name="EvilFont">text</font>')
        assert "EvilFont" not in result
        assert 'name="Courier"' in result


class TestGetBrand:

    def test_default_brand_returned_when_none(self):
        b = _get_brand(None)
        assert b["primary"] == DEFAULT_BRAND["primary"]

    def test_custom_brand_overrides(self):
        b = _get_brand({"primary": "#FF0000"})
        assert b["primary"] == "#FF0000"
        assert b["secondary"] == DEFAULT_BRAND["secondary"]


class TestBuildStyles:

    def test_returns_dict(self):
        styles = build_styles()
        assert isinstance(styles, dict)

    def test_contains_required_keys(self):
        styles = build_styles()
        required = ["STYLE_TITLE", "STYLE_H1", "STYLE_H2", "STYLE_BODY", "STYLE_CODE"]
        for key in required:
            assert key in styles, f"Missing style key: {key}"

    def test_caches_identical_brand(self):
        s1 = build_styles({"primary": "#123456"})
        s2 = build_styles({"primary": "#123456"})
        assert s1 is s2  # Same object from cache


class TestTruncateToWidth:

    def test_short_text_unchanged(self):
        result = truncate_to_width("Hi", "Helvetica", 10, 500)
        assert result == "Hi"

    def test_none_text_returns_none(self):
        result = truncate_to_width(None, "Helvetica", 10, 500)
        assert result is None

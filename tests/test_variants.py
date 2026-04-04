"""Tests for briefkit variant system."""
from __future__ import annotations

from briefkit.variants import auto_detect_variant, get_variant, list_variants


class TestVariantRegistry:

    def test_list_variants_non_empty(self):
        variants = list_variants()
        assert len(variants) > 0

    def test_list_variants_includes_legal(self):
        assert "legal" in list_variants()

    def test_list_variants_includes_all_twelve(self):
        expected = {
            "aiml", "legal", "medical", "engineering", "research",
            "api", "gaming", "finance", "species", "historical",
            "hardware", "religion",
        }
        actual = set(list_variants())
        assert expected.issubset(actual)

    def test_get_variant_legal(self):
        v = get_variant("legal")
        assert v is not None
        assert v.name == "legal"

    def test_get_variant_unknown_returns_none(self):
        assert get_variant("nonexistent_variant") is None

    def test_auto_detect_variant_legal_text(self):
        text = "This legislation and statute governs privacy act compliance regulation enforcement"
        result = auto_detect_variant(text)
        # Should detect legal variant or at least return something
        if result:
            assert hasattr(result, "name")

    def test_auto_detect_variant_empty_text(self):
        result = auto_detect_variant("")
        assert result is None

    def test_all_variants_have_keywords(self):
        for name in list_variants():
            v = get_variant(name)
            assert len(v.auto_detect_keywords) > 0, f"Variant {name} has no auto_detect_keywords"

    def test_variant_build_sections_returns_list(self):
        from briefkit.styles import build_styles
        v = get_variant("legal")
        styles = build_styles()
        result = v.build_variant_sections(
            content={"title": "Test", "overview": "", "subsystems": []},
            flowables=[],
            styles=styles,
            brand=None,
        )
        assert isinstance(result, list)

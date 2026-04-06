"""Tests for briefkit template registry and generation."""
from __future__ import annotations

import copy

import pytest

from briefkit.config import DEFAULTS
from briefkit.presets import get_preset, list_presets
from briefkit.templates import get_template, list_templates

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALL_TEMPLATE_NAMES = list_templates()

_PRESET_REQUIRED_KEYS = {
    "primary", "secondary", "accent", "body_text", "caption",
    "background", "rule", "success", "warning", "danger",
    "code_bg", "table_alt",
    "font_body", "font_heading", "font_mono", "font_caption",
}


def _make_config(output_dir: str) -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    cfg["output"]["filename"] = "test-output.pdf"
    cfg["output"]["output_dir"] = output_dir
    cfg["doc_ids"]["enabled"] = False
    return cfg


# ===========================================================================
# TestTemplateRegistry — unchanged from original
# ===========================================================================


class TestTemplateRegistry:
    """Tests for the template registry."""

    def test_list_templates_returns_non_empty(self):
        templates = list_templates()
        assert len(templates) > 0

    def test_list_templates_includes_briefing(self):
        names = [t["name"] if isinstance(t, dict) else t for t in list_templates()]
        assert "briefing" in names

    def test_list_templates_includes_all_twenty_five(self):
        names = [t["name"] if isinstance(t, dict) else t for t in list_templates()]
        expected = {
            "briefing", "report", "book", "manual", "academic",
            "minimal", "letter", "contract", "register", "minutes", "novel",
            "proposal", "policy", "invoice", "quote", "certificate", "resume",
            "evaluation", "newsletter", "sop", "memo", "whitepaper", "datasheet",
            "playbook", "deck",
        }
        assert expected.issubset(set(names))

    def test_get_template_briefing(self):
        cls = get_template("briefing")
        assert cls is not None

    def test_get_template_minimal(self):
        cls = get_template("minimal")
        assert cls is not None

    def test_get_template_unknown_raises(self):
        with pytest.raises(ValueError):
            get_template("nonexistent_template_xyz")

    @pytest.mark.parametrize("name", [
        "briefing", "report", "book", "manual", "academic",
        "minimal", "letter", "contract", "register", "minutes", "novel",
        "proposal", "policy", "invoice", "quote", "certificate", "resume",
        "evaluation", "newsletter", "sop", "memo", "whitepaper", "datasheet",
        "playbook", "deck",
    ])
    def test_get_template_returns_class(self, name):
        cls = get_template(name)
        assert cls is not None
        assert hasattr(cls, "__name__")


# ===========================================================================
# TestTemplateGeneration — original two tests preserved, parametrized suite added
# ===========================================================================


class TestTemplateGeneration:
    """Tests that templates can generate PDFs from fixtures."""

    def test_briefing_generates_pdf(self, basic_fixture, tmp_output, default_config):
        default_config["output"]["filename"] = "test-output.pdf"
        default_config["output"]["output_dir"] = str(tmp_output)
        default_config["doc_ids"]["enabled"] = False

        cls = get_template("briefing")
        tmpl = cls(basic_fixture, config=default_config)
        result = tmpl.generate()
        assert result.exists()
        assert result.stat().st_size > 0

    def test_minimal_generates_pdf(self, basic_fixture, tmp_output, default_config):
        default_config["output"]["filename"] = "test-output.pdf"
        default_config["output"]["output_dir"] = str(tmp_output)
        default_config["doc_ids"]["enabled"] = False

        cls = get_template("minimal")
        tmpl = cls(basic_fixture, config=default_config)
        result = tmpl.generate()
        assert result.exists()
        assert result.stat().st_size > 0

    # -----------------------------------------------------------------------
    # Parametrized: all 28 templates — PDF exists, size, extension
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize("template_name", _ALL_TEMPLATE_NAMES)
    def test_all_templates_generate_valid_pdf(
        self, template_name, basic_fixture, tmp_path
    ):
        """Every registered template must produce a non-empty .pdf file."""
        cfg = _make_config(str(tmp_path))
        cls = get_template(template_name)
        tmpl = cls(basic_fixture, config=cfg)
        result = tmpl.generate()

        assert result.exists(), f"{template_name}: output file not found at {result}"
        assert result.suffix.lower() == ".pdf", (
            f"{template_name}: output extension is {result.suffix!r}, expected '.pdf'"
        )
        assert result.stat().st_size > 0, f"{template_name}: output PDF is empty"

    # -----------------------------------------------------------------------
    # Parametrized: all 28 templates — pypdf page count and metadata types
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize("template_name", _ALL_TEMPLATE_NAMES)
    def test_all_templates_pdf_readable_with_pages(
        self, template_name, basic_fixture, tmp_path
    ):
        """Every generated PDF must be readable by pypdf and have >= 1 page."""
        from pypdf import PdfReader

        cfg = _make_config(str(tmp_path))
        cls = get_template(template_name)
        tmpl = cls(basic_fixture, config=cfg)
        result = tmpl.generate()

        reader = PdfReader(str(result))
        assert len(reader.pages) >= 1, (
            f"{template_name}: PDF has {len(reader.pages)} pages, expected >= 1"
        )

    @pytest.mark.parametrize("template_name", _ALL_TEMPLATE_NAMES)
    def test_all_templates_pdf_metadata_are_strings(
        self, template_name, basic_fixture, tmp_path
    ):
        """Title, author, and creator metadata fields must be strings (not None)."""
        from pypdf import PdfReader

        cfg = _make_config(str(tmp_path))
        cls = get_template(template_name)
        tmpl = cls(basic_fixture, config=cfg)
        result = tmpl.generate()

        reader = PdfReader(str(result))
        meta = reader.metadata

        assert meta is not None, f"{template_name}: PDF has no metadata object"

        for field_name, value in (
            ("title", meta.title),
            ("author", meta.author),
            ("creator", meta.creator),
        ):
            assert isinstance(value, str), (
                f"{template_name}: metadata.{field_name} is {type(value).__name__!r}, "
                f"expected str (value={value!r})"
            )


# ===========================================================================
# TestColorPresets — verify all 20 presets have all required keys
# ===========================================================================


class TestColorPresets:
    """Tests for color preset completeness."""

    def test_preset_count_is_twenty(self):
        assert len(list_presets()) == 20

    @pytest.mark.parametrize("preset_name", list_presets())
    def test_preset_has_all_required_keys(self, preset_name):
        """Every preset must contain all keys in _PRESET_REQUIRED_KEYS."""
        preset = get_preset(preset_name)
        missing = _PRESET_REQUIRED_KEYS - set(preset.keys())
        assert not missing, (
            f"Preset {preset_name!r} is missing required keys: {sorted(missing)}"
        )

    @pytest.mark.parametrize("preset_name", list_presets())
    def test_preset_color_values_are_strings(self, preset_name):
        """All color values must be non-empty strings."""
        preset = get_preset(preset_name)
        for key in _PRESET_REQUIRED_KEYS:
            val = preset[key]
            assert isinstance(val, str) and val, (
                f"Preset {preset_name!r} key {key!r} = {val!r} is not a non-empty string"
            )

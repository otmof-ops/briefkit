"""Tests for briefkit template registry and generation."""
from __future__ import annotations

import pytest

from briefkit.templates import get_template, list_templates


class TestTemplateRegistry:
    """Tests for the template registry."""

    def test_list_templates_returns_non_empty(self):
        templates = list_templates()
        assert len(templates) > 0

    def test_list_templates_includes_briefing(self):
        names = [t["name"] if isinstance(t, dict) else t for t in list_templates()]
        assert "briefing" in names

    def test_list_templates_includes_all_eleven(self):
        names = [t["name"] if isinstance(t, dict) else t for t in list_templates()]
        expected = {
            "briefing", "report", "book", "manual", "academic",
            "minimal", "letter", "contract", "register", "minutes", "novel",
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
    ])
    def test_get_template_returns_class(self, name):
        cls = get_template(name)
        assert cls is not None
        assert hasattr(cls, "__name__")


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

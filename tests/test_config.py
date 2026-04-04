"""Tests for the configuration system."""

import pytest

from briefkit.config import DEFAULTS, find_project_root, load_config, resolve_brand


class TestDefaults:
    def test_defaults_has_all_sections(self):
        assert "project" in DEFAULTS
        assert "brand" in DEFAULTS
        assert "doc_ids" in DEFAULTS
        assert "layout" in DEFAULTS
        assert "content" in DEFAULTS
        assert "hierarchy" in DEFAULTS
        assert "template" in DEFAULTS
        assert "variants" in DEFAULTS
        assert "output" in DEFAULTS

    def test_default_preset_is_navy(self):
        assert DEFAULTS["brand"]["preset"] == "navy"

    def test_default_template_is_briefing(self):
        assert DEFAULTS["template"]["preset"] == "briefing"

    def test_default_doc_ids_enabled(self):
        assert DEFAULTS["doc_ids"]["enabled"] is True


class TestLoadConfig:
    def test_load_with_no_config_file(self, tmp_path):
        # Loading with no config file should return defaults
        config = load_config()
        assert config["template"]["preset"] == "briefing"

    def test_load_with_partial_config(self, tmp_path):
        config_file = tmp_path / "briefkit.yml"
        config_file.write_text("project:\n  name: Test Project\n")
        config = load_config(config_path=config_file)
        assert config["project"]["name"] == "Test Project"

    def test_load_with_brand_override(self, tmp_path):
        config_file = tmp_path / "briefkit.yml"
        config_file.write_text("brand:\n  preset: ocean\n")
        config = load_config(config_path=config_file)
        assert config["brand"]["preset"] == "ocean"


class TestResolveBrand:
    def test_resolve_navy_preset(self):
        config = {"brand": {"preset": "navy"}}
        resolved = resolve_brand(config)
        assert resolved["brand"]["primary"] == "#1B2A4A"

    def test_resolve_custom_preset(self):
        config = {"brand": {"preset": "custom", "primary": "#FF0000"}}
        resolved = resolve_brand(config, user_brand_overrides={"primary": "#FF0000"})
        assert resolved["brand"]["primary"] == "#FF0000"

    def test_resolve_unknown_preset_raises(self):
        config = {"brand": {"preset": "nonexistent"}}
        with pytest.raises(ValueError, match="Unknown color preset"):
            resolve_brand(config)


class TestFindProjectRoot:
    def test_finds_root_with_briefkit_yml(self, tmp_path):
        (tmp_path / "briefkit.yml").touch()
        sub = tmp_path / "a" / "b"
        sub.mkdir(parents=True)
        root = find_project_root(sub)
        assert root == tmp_path

    def test_finds_root_with_dot_briefkit(self, tmp_path):
        (tmp_path / ".briefkit").mkdir()
        sub = tmp_path / "deep" / "nested"
        sub.mkdir(parents=True)
        root = find_project_root(sub)
        assert root == tmp_path

    def test_returns_none_when_no_marker(self, tmp_path):
        root = find_project_root(tmp_path)
        # Returns None if no markers found
        assert root is None

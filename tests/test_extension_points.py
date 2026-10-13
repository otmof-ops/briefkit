# SPDX-FileCopyrightText: 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)
# SPDX-License-Identifier: BSD-3-Clause
"""Registering templates and variants from outside the package, and selecting variants by path rule."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from briefkit.cli import main
from briefkit.config import DEFAULTS
from briefkit.extractor import extract_content
from briefkit.generator import BaseBriefingTemplate


class TestRegisterTemplate:
    def test_round_trip_through_the_registry(self):
        from briefkit.templates import _REGISTRY, get_template, list_templates, register_template, template_descriptions

        class Dummy(BaseBriefingTemplate):
            """A template registered from outside the package."""

        register_template("Dummy-Test", Dummy)
        try:
            assert get_template("dummy-test") is Dummy
            assert get_template("DUMMY-TEST") is Dummy
            assert "dummy-test" in list_templates()
            assert template_descriptions()["dummy-test"] == "A template registered from outside the package"
        finally:
            _REGISTRY.pop("dummy-test", None)
        with pytest.raises(ValueError):
            get_template("dummy-test")

    def test_empty_name_is_rejected(self):
        from briefkit.templates import register_template

        with pytest.raises(ValueError):
            register_template("   ", BaseBriefingTemplate)

    def test_registered_template_is_usable_from_the_cli(self, basic_fixture, monkeypatch):
        from briefkit.templates import _REGISTRY, register_template

        class Plain(BaseBriefingTemplate):
            pdf_subject = "Plain Test"

        register_template("plain-test", Plain)
        monkeypatch.chdir(basic_fixture.parents[1])
        try:
            assert main(["generate", str(basic_fixture), "--template", "plain-test", "--no-ids", "--quiet"]) == 0
        finally:
            _REGISTRY.pop("plain-test", None)
        assert (basic_fixture / "executive-briefing.pdf").exists()


class TestRegisterVariant:
    def test_decorator_registers_an_instance(self):
        from briefkit.variants import _REGISTRY, DocSetVariant, get_variant, list_variants, register_variant

        @register_variant
        class DevOps(DocSetVariant):
            name = "devops-test"
            auto_detect_keywords = ["kubernetes", "terraform"]

            def build_variant_sections(self, content, flowables, styles, brand):
                flowables.append("devops-marker")
                return flowables

        try:
            variant = get_variant("devops-test")
            assert variant is not None
            assert "devops-test" in list_variants()
            assert variant.keyword_hits("Kubernetes clusters and Terraform plans") == 2
            assert variant.build_variant_sections({}, [], {}, {}) == ["devops-marker"]
            # The built-ins are still there: registering did not replace the registry.
            assert get_variant("legal") is not None
        finally:
            _REGISTRY.pop("devops-test", None)
        assert get_variant("devops-test") is None


def _template(target, rules, *, cli_variant=None, auto_detect=True):
    cfg = copy.deepcopy(DEFAULTS)
    cfg["doc_ids"]["enabled"] = False
    cfg["variants"]["rules"] = rules
    cfg["variants"]["auto_detect"] = auto_detect
    cfg["_cli"] = {"variant": cli_variant, "verbose": True}
    return BaseBriefingTemplate(target, level=3, config=cfg)


class TestVariantRules:
    """``variants.rules`` match the directory's path relative to the project root; the first match wins."""

    def test_first_matching_rule_wins(self, legal_fixture):
        tmpl = _template(
            legal_fixture,
            [
                {"pattern": "docs/nothing-here/**", "variant": "api"},
                {"pattern": "docs/*", "variant": "hardware"},
                {"pattern": "docs/legal", "variant": "legal"},
            ],
        )
        assert Path(tmpl._display_path()) == Path("docs/legal")  # separators differ on Windows
        assert tmpl._variant_from_rules() == "hardware"

    def test_double_star_matches_the_directory_itself(self, legal_fixture):
        tmpl = _template(legal_fixture, [{"pattern": "docs/legal/**", "variant": "legal"}])
        assert tmpl._variant_from_rules() == "legal"

    def test_no_match_and_malformed_entries(self, legal_fixture):
        tmpl = _template(
            legal_fixture,
            [
                "not a dict",
                {"pattern": "", "variant": "api"},
                {"pattern": "elsewhere/**"},
                {"pattern": "x/**", "variant": "api"},
            ],
        )
        assert tmpl._variant_from_rules() is None

    def test_rule_beats_auto_detection(self, legal_fixture, capsys):
        tmpl = _template(legal_fixture, [{"pattern": "docs/**", "variant": "research"}])
        content = extract_content(legal_fixture, 3, tmpl.config)
        tmpl.apply_variants([], content)
        assert "Variant detected: research" in capsys.readouterr().err

    def test_auto_detection_runs_when_no_rule_matches(self, legal_fixture, capsys):
        tmpl = _template(legal_fixture, [{"pattern": "docs/other/**", "variant": "research"}])
        content = extract_content(legal_fixture, 3, tmpl.config)
        tmpl.apply_variants([], content)
        assert "Variant detected: legal" in capsys.readouterr().err

    def test_cli_flag_beats_rule(self, legal_fixture, capsys):
        tmpl = _template(legal_fixture, [{"pattern": "docs/**", "variant": "research"}], cli_variant="api")
        content = extract_content(legal_fixture, 3, tmpl.config)
        tmpl.apply_variants([], content)
        assert "Variant detected: api" in capsys.readouterr().err

    def test_none_suppresses_rules_and_detection(self, legal_fixture, capsys):
        tmpl = _template(legal_fixture, [{"pattern": "docs/**", "variant": "research"}], cli_variant="none")
        content = extract_content(legal_fixture, 3, tmpl.config)
        story = tmpl.apply_variants([], content)
        assert story == []
        assert "Variant detected" not in capsys.readouterr().err

    def test_rules_from_the_project_file_reach_the_build(self, legal_fixture, monkeypatch, capsys):
        root = legal_fixture.parents[1]
        (root / "briefkit.yml").write_text(
            "doc_ids:\n  enabled: false\nvariants:\n  auto_detect: false\n  rules:\n"
            '    - pattern: "docs/legal/**"\n      variant: "hardware"\n',
            encoding="utf-8",
        )
        monkeypatch.chdir(root)
        assert main(["generate", str(legal_fixture), "--verbose"]) == 0
        assert "Variant detected: hardware" in capsys.readouterr().err

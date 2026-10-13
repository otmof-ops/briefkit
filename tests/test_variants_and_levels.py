"""Every variant renders; every briefing level renders; the matcher counts whole words."""

from __future__ import annotations

import copy
import time
from pathlib import Path

import pytest
from pypdf import PdfReader

from briefkit.config import DEFAULTS
from briefkit.templates import get_template
from briefkit.variants import auto_detect_variant, get_variant, list_variants


def _text(pdf: Path) -> str:
    return "\n".join((p.extract_text() or "") for p in PdfReader(str(pdf)).pages)


def _cfg(**cli) -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    cfg["doc_ids"]["enabled"] = False
    cfg["_cli"] = dict(cli)
    return cfg


class TestVariants:
    @pytest.mark.parametrize("name", list_variants())
    def test_every_variant_renders_its_sections(self, name, full_fixture, tmp_path):
        out = tmp_path / f"{name}.pdf"
        get_template("report")(full_fixture, level=3, config=_cfg(variant=name), output_path=out).generate()
        text = _text(out)
        assert "Variant Sections" in text, f"{name} added no variant section"

    @pytest.mark.parametrize("name", list_variants())
    def test_every_variant_renders_on_the_default_template(self, name, legal_fixture, tmp_path):
        out = tmp_path / f"{name}.pdf"
        get_template("briefing")(legal_fixture, level=3, config=_cfg(variant=name), output_path=out).generate()
        assert PdfReader(str(out)).pages

    def test_keywords_match_whole_words_case_insensitively(self):
        api = get_variant("api")
        assert api is not None
        assert api.keyword_hits("The REST API returns 200 OK on GET and POST.") >= 2
        assert api.keyword_hits("respirator restaurant posture") == 0, "substrings must not count"

    def test_glossary_alone_does_not_trip_the_aiml_variant(self):
        text = "A Glossary of terms used in the project. Blue-teal gradient preset for tech startups."
        detected = auto_detect_variant(text)
        assert detected is None or detected.name != "aiml"

    def test_upper_case_keywords_are_matched(self):
        finance = get_variant("finance")
        assert finance is not None
        assert finance.keyword_hits("Revenue and EBITDA rose while the balance sheet held.") >= 2


class TestBriefingLevels:
    def _tree(self, tmp_path: Path) -> Path:
        root = tmp_path / "project"
        (root / "docs").mkdir(parents=True)
        (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n", encoding="utf-8")
        (root / "README.md").write_text(
            "# Knowledge Library\n\nA library of structured documentation sets grouped by subject and division, "
            "with enough text here to pass the overview threshold comfortably.\n",
            encoding="utf-8",
        )
        for division in ("computing", "biology"):
            d = root / "docs" / division
            d.mkdir()
            (d / "README.md").write_text(
                f"# {division.title()} Division\n\nAn overview of the {division} division written in 1998 and revised in 2015 with plenty of words.\n"
            )
            for subject in ("alpha", "beta"):
                sdir = d / subject
                sdir.mkdir()
                (sdir / "README.md").write_text(
                    f"# {subject.title()} Subject\n\nThe {subject} subject groups documentation sets about {division}, first published 2003 and updated 2021.\n"
                )
                for n in (1, 2):
                    ds = sdir / f"set-{n}"
                    ds.mkdir()
                    (ds / "README.md").write_text(
                        f"# Set {n} of {subject}\n\nA documentation set with an overview paragraph that is long enough to count in 2019.\n"
                    )
                    (ds / "01-intro.md").write_text(
                        f"# Intro\n\nBody text for set {n}.\n\n| Metric | Value |\n|---|---|\n| Speed | 12x faster |\n| Size | 4 GB |\n"
                    )
                    (ds / "02-detail.md").write_text(
                        "# Detail\n\n> Key insight: the detail matters a great deal here.\n\nMore body text.\n"
                    )
        return root

    @pytest.mark.parametrize("level", [1, 2, 4])
    def test_briefing_renders_each_aggregate_level(self, level, tmp_path):
        root = self._tree(tmp_path)
        target = {1: root / "docs" / "computing", 2: root / "docs" / "computing" / "alpha", 4: root}[level]
        out = tmp_path / f"level{level}.pdf"
        cfg = copy.deepcopy(DEFAULTS)
        cfg["doc_ids"]["enabled"] = False
        tpl = get_template("briefing")(target, level=level, config=cfg, output_path=out)
        tpl.generate()
        text = _text(out)
        assert len(PdfReader(str(out)).pages) >= 3
        expected = {1: "Division Overview", 2: "Subject Map", 4: "Dashboard"}[level]
        assert expected in text

    def test_level_is_detected_from_the_tree_without_a_root(self, tmp_path):
        from briefkit.generator import detect_level

        root = self._tree(tmp_path)
        (root / "briefkit.yml").unlink()
        cfg = copy.deepcopy(DEFAULTS)
        assert detect_level(root / "docs" / "computing" / "alpha" / "set-1", None, cfg) == 3
        assert detect_level(root / "docs" / "computing" / "alpha", None, cfg) == 2
        assert detect_level(root / "docs" / "computing", None, cfg) == 1


class TestRegexBounds:
    def test_citation_patterns_stay_linear_on_capitalised_lists(self):
        from briefkit.bibliography import extract_bibliography

        text = ", ".join(f"Word{i}" for i in range(12000))  # ~100 kB of capitalised, comma-separated words
        start = time.perf_counter()
        extract_bibliography(text)
        assert time.perf_counter() - start < 3.0

    def test_legal_variant_stays_linear_on_capitalised_runs(self, tmp_path):
        legal = get_variant("legal")
        assert legal is not None
        words = " ".join(f"Alpha{i} Beta" for i in range(8000))
        content = {
            "title": "T",
            "overview": words,
            "subsystems": [{"name": "s", "content": words, "blocks": [], "tables": [], "insights": []}],
        }
        from briefkit.styles import build_styles

        start = time.perf_counter()
        legal.build_variant_sections(content, [], build_styles(), None)
        assert time.perf_counter() - start < 3.0


def test_sections_module_re_exports_the_public_surface():
    import briefkit.sections as sections

    for name in ("BaseBriefingTemplate", "safe_para", "build_cover_page", "build_toc", "build_data_table"):
        assert hasattr(sections, name), name


def test_version_flag_matches_the_package(capsys):
    import briefkit
    from briefkit.cli import main

    with pytest.raises(SystemExit):
        main(["--version"])
    assert briefkit.__version__ in capsys.readouterr().out


def test_generate_reuses_the_precheck_extraction(basic_fixture, tmp_path, monkeypatch):
    """The CLI extracts once for its pre-check; the template must not read the sources again."""
    import briefkit.generator as gen
    from briefkit.cli import main

    calls = {"n": 0}
    real = gen._extract_content

    def counting(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(gen, "_extract_content", counting)
    out = tmp_path / "once.pdf"
    assert main(["generate", str(basic_fixture), "--no-ids", "--quiet", "--output", str(out)]) == 0
    assert calls["n"] == 0, "the template re-extracted content the CLI had already extracted"

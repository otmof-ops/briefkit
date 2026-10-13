"""The template layer's architectural contract: traits and hooks, not generate() overrides."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from pypdf import PdfReader

from briefkit.config import DEFAULTS
from briefkit.generator import BaseBriefingTemplate
from briefkit.templates import get_template, list_templates

ALL = list_templates()
VARIANT_TEMPLATES = {"academic", "briefing", "manual", "report"}
LOCKED_A4 = {"guide", "deep-research", "magazine"}
LANDSCAPE = {"deck", "certificate"}
LETTER_DESIGN = {"datasheet", "memo", "playbook", "sop", "whitepaper", "evaluation"}


def _cfg(user: dict | None = None, **top) -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    cfg["doc_ids"]["enabled"] = False
    for key, value in top.items():
        cfg[key].update(value)
    cfg["_user"] = copy.deepcopy(user or {})
    return cfg


def _build(name: str, source: Path, out: Path, cfg: dict) -> Path:
    get_template(name)(source, level=3, config=cfg, output_path=out).generate()
    return out


def _mediabox(pdf: Path) -> tuple[float, float]:
    box = PdfReader(str(pdf)).pages[0].mediabox
    return round(float(box.width)), round(float(box.height))


def _fonts(pdf: Path) -> set[str]:
    names: set[str] = set()
    for page in PdfReader(str(pdf)).pages:
        resources = page.get("/Resources") or {}
        fonts = resources.get("/Font") or {}
        for key in fonts:
            font = fonts[key].get_object()
            names.add(str(font.get("/BaseFont", "")).lstrip("/"))
    return names


class TestContract:
    @pytest.mark.parametrize("name", ALL)
    def test_no_template_overrides_generate(self, name):
        cls = get_template(name)
        for klass in cls.__mro__:
            if klass is BaseBriefingTemplate:
                break
            assert "generate" not in klass.__dict__, f"{klass.__name__} overrides generate()"

    def test_variants_only_where_they_always_ran(self):
        for name in ALL:
            assert get_template(name).supports_variants is (name in VARIANT_TEMPLATES), name

    def test_witness_has_no_doc_id(self):
        assert get_template("witness").assigns_doc_id is False

    def test_every_template_has_a_subject(self):
        for name in ALL:
            assert get_template(name).pdf_subject or name in VARIANT_TEMPLATES, name


class TestGeometry:
    @pytest.mark.parametrize("name", ALL)
    def test_user_page_size_is_honoured_unless_locked(self, name, basic_fixture, tmp_path):
        cfg = _cfg(user={"layout": {"page_size": "Letter"}}, layout={"page_size": "Letter"})
        pdf = _build(name, basic_fixture, tmp_path / f"{name}.pdf", cfg)
        w, h = _mediabox(pdf)
        if name in LOCKED_A4:
            assert sorted((w, h)) == [595, 842], f"{name} is locked to A4 by design"
        elif name in LANDSCAPE:
            assert (w, h) == (792, 612)
        else:
            assert (w, h) == (612, 792), f"{name} ignored layout.page_size"

    @pytest.mark.parametrize("name", ALL)
    def test_design_page_size_applies_when_the_user_set_none(self, name, basic_fixture, tmp_path):
        pdf = _build(name, basic_fixture, tmp_path / f"{name}.pdf", _cfg())
        w, h = _mediabox(pdf)
        expected = (612, 792) if name in LETTER_DESIGN else (595, 842)
        if name in LANDSCAPE:
            expected = (expected[1], expected[0])
        assert (w, h) == expected, f"{name}: {(w, h)}"

    @pytest.mark.parametrize("name", ["briefing", "book", "minimal", "datasheet", "report"])
    def test_user_orientation_is_honoured(self, name, basic_fixture, tmp_path):
        cfg = _cfg(user={"layout": {"orientation": "landscape"}}, layout={"orientation": "landscape"})
        pdf = _build(name, basic_fixture, tmp_path / f"{name}.pdf", cfg)
        w, h = _mediabox(pdf)
        assert w > h, f"{name} ignored layout.orientation"

    def test_locked_orientation_ignores_the_user(self, basic_fixture, tmp_path):
        cfg = _cfg(user={"layout": {"orientation": "portrait"}}, layout={"orientation": "portrait"})
        w, h = _mediabox(_build("deck", basic_fixture, tmp_path / "deck.pdf", cfg))
        assert w > h

    @pytest.mark.parametrize("name", ["register", "minimal", "invoice", "witness", "sop"])
    def test_content_width_matches_the_frame(self, name, basic_fixture, tmp_path):
        """A3 output must lay text out for A3, not for a literal A4 frame."""
        cfg = _cfg(user={"layout": {"page_size": "A3"}}, layout={"page_size": "A3"})
        tpl = get_template(name)(basic_fixture, level=3, config=cfg, output_path=tmp_path / f"{name}.pdf")
        tpl.generate()
        g = tpl.geometry
        assert abs(tpl.content_width - (g.pagesize[0] - g.margins.left - g.margins.right)) < 0.01
        assert _mediabox(tmp_path / f"{name}.pdf")[0] == 842

    def test_user_margins_beat_design_margins(self, basic_fixture, tmp_path):
        cfg = _cfg(
            user={"layout": {"margins": {"left": 40}}},
            layout={"margins": {"left": 40, "right": 20, "top": 25, "bottom": 22}},
        )
        tpl = get_template("letter")(basic_fixture, level=3, config=cfg, output_path=tmp_path / "l.pdf")
        assert round(tpl.geometry.margins.left / 2.834645) == 40
        assert round(tpl.geometry.margins.right / 2.834645) == 25, "the unset side keeps the template's design margin"

    def test_margin_override_beats_the_user(self, basic_fixture, tmp_path):
        cfg = _cfg(
            user={"layout": {"margins": {"left": 10}}},
            layout={"margins": {"left": 10, "right": 20, "top": 25, "bottom": 22}},
        )
        tpl = get_template("memo")(basic_fixture, level=3, config=cfg, output_path=tmp_path / "m.pdf")
        assert round(tpl.geometry.margins.left / 2.834645) == 30


class TestFonts:
    @pytest.mark.parametrize("name", ALL)
    def test_brand_fonts_reach_every_page(self, name, basic_fixture, tmp_path):
        """With a Times preset no page may fall back to Helvetica."""
        cfg = _cfg(
            brand={
                "font_body": "Times-Roman",
                "font_heading": "Times-Bold",
                "font_mono": "Courier",
                "font_caption": "Times-Italic",
            }
        )
        pdf = _build(name, basic_fixture, tmp_path / f"{name}.pdf", cfg)
        fonts = _fonts(pdf)
        # ReportLab registers plain Helvetica as every canvas's initial font, so
        # its presence proves nothing; a bold or oblique Helvetica does.
        helvetica = {f for f in fonts if f.startswith("Helvetica-")}
        assert not helvetica, f"{name} still hard-codes {sorted(helvetica)}"
        assert any(f.startswith("Times") for f in fonts), f"{name} never used the brand font"


class TestNumberingAndStructure:
    def _text(self, pdf: Path) -> str:
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(pdf)).pages)

    def test_briefing_toc_matches_the_body(self, full_fixture, tmp_path):
        pdf = _build("briefing", full_fixture, tmp_path / "b.pdf", _cfg())
        text = self._text(pdf)
        assert "Content Overview" not in text
        assert text.count("3. Context and Significance") >= 2, "the TOC and the body must both carry the heading"
        assert "4. Technical Deep-Dive" in text and "7. Practical Applications" in text

    def test_briefing_numbering_follows_skipped_sections(self, full_fixture, tmp_path):
        cfg = _cfg()
        cfg["project"]["skip_executive_summary"] = True
        cfg["project"]["skip_dashboard"] = True
        pdf = _build("briefing", full_fixture, tmp_path / "b.pdf", cfg)
        text = self._text(pdf)
        assert "1. Context and Significance" in text
        assert "3. Context and Significance" not in text

    @pytest.mark.parametrize("name", ["briefing", "report", "manual", "academic", "book", "minimal"])
    def test_chapter_sub_headings_are_kept(self, name, tmp_path):
        root = tmp_path / "project"
        docs = root / "docs" / "set"
        docs.mkdir(parents=True)
        (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n")
        (docs / "README.md").write_text(
            "# Structured Set\n\nAn overview paragraph long enough to be picked up by the extractor here.\n"
        )
        (docs / "01-chapter.md").write_text(
            "# Chapter One\n\nIntro text.\n\n## Unmistakable Subheading\n\nMore text.\n\n### Deeper Heading\n\nEnd.\n"
        )
        pdf = _build(name, docs, tmp_path / f"{name}.pdf", _cfg())
        text = self._text(pdf)
        assert "Unmistakable Subheading" in text, f"{name} dropped the chapter's H2"
        assert "Deeper Heading" in text

    def test_variant_sections_precede_the_back_cover(self, tmp_path):
        root = tmp_path / "project"
        docs = root / "docs" / "set"
        docs.mkdir(parents=True)
        (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n")
        (docs / "README.md").write_text(
            "# Quarterly Review\n\nRevenue, EBITDA, cash flow, portfolio risk exposure, investment return and balance sheet analysis.\n"
        )
        (docs / "01-summary.md").write_text(
            "# Summary\n\nRevenue and EBITDA rose. Portfolio risk exposure fell. Investment return improved against the balance sheet forecast.\n"
        )
        pdf = _build("briefing", docs, tmp_path / "v.pdf", _cfg())
        pages = [(p.extract_text() or "") for p in PdfReader(str(pdf)).pages]
        variant_page = next(i for i, t in enumerate(pages) if "Finance Variant Sections" in t)
        back_cover_page = next(i for i, t in enumerate(pages) if "This document was generated on" in t)
        assert variant_page < back_cover_page

    @pytest.mark.parametrize("name", sorted(set(ALL) - VARIANT_TEMPLATES))
    def test_fixed_format_templates_never_gain_variant_sections(self, name, tmp_path):
        root = tmp_path / "project"
        docs = root / "docs" / "set"
        docs.mkdir(parents=True)
        (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n")
        (docs / "README.md").write_text(
            "# Quarterly Review\n\nRevenue, EBITDA, cash flow, portfolio risk exposure, investment return and balance sheet analysis.\n"
        )
        (docs / "01-summary.md").write_text(
            "# Summary\n\nRevenue and EBITDA rose. Portfolio risk exposure fell. Investment return improved against the balance sheet forecast.\n"
        )
        pdf = _build(name, docs, tmp_path / f"{name}.pdf", _cfg())
        assert "Finance Variant Sections" not in self._text(pdf)

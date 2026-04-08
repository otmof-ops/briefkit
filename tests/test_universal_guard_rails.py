"""
Tests for universal story post-processing:
- _protect_section_headings (orphan-title guard)
- _collapse_empty_page_runs (empty-page collapse)

These live at the generator level so every template (including user
custom templates) inherits the same guard rails without per-template
instrumentation.
"""

from __future__ import annotations

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import CondPageBreak, KeepTogether, PageBreak, Paragraph, Spacer
from reportlab.lib.units import mm


# ---------------------------------------------------------------------------
# Minimal stub template exposing just enough surface for the two methods
# ---------------------------------------------------------------------------

class _StubTemplate:
    """Only carries the pieces the two post-process methods need."""

    def __init__(self, config=None):
        self.config = config or {}
        self.styles = {
            "STYLE_H1": ParagraphStyle(
                "STYLE_H1",
                fontSize=18,
                leading=22,
                keepWithNext=True,
            ),
            "STYLE_BODY": ParagraphStyle("STYLE_BODY", fontSize=10, leading=14),
        }

    # Bind the real implementations from BaseBriefingTemplate so we test
    # the exact code path that runs in production.
    from briefkit.generator import BaseBriefingTemplate

    _protect_section_headings = BaseBriefingTemplate._protect_section_headings
    _collapse_empty_page_runs = BaseBriefingTemplate._collapse_empty_page_runs


def _h1(text: str) -> Paragraph:
    return Paragraph(text, ParagraphStyle(
        "STYLE_H1", fontSize=18, leading=22, keepWithNext=True,
    ))


def _body(text: str) -> Paragraph:
    return Paragraph(text, ParagraphStyle("STYLE_BODY", fontSize=10, leading=14))


# ---------------------------------------------------------------------------
# Orphan-title protection
# ---------------------------------------------------------------------------

class TestOrphanProtection:
    def test_wraps_bare_h1_with_next_flowable(self):
        tpl = _StubTemplate()
        story = [_h1("Chapter 1"), _body("first line")]
        out = tpl._protect_section_headings(story)
        assert len(out) == 1
        assert isinstance(out[0], KeepTogether)

    def test_skips_when_next_is_pagebreak(self):
        tpl = _StubTemplate()
        story = [_h1("Chapter 1"), PageBreak(), _body("later")]
        out = tpl._protect_section_headings(story)
        assert isinstance(out[0], Paragraph)
        assert isinstance(out[1], PageBreak)

    def test_skips_when_next_is_keep_together(self):
        tpl = _StubTemplate()
        existing_kt = KeepTogether([_body("already wrapped")])
        story = [_h1("Chapter 1"), existing_kt]
        out = tpl._protect_section_headings(story)
        # The H1 stays as a bare Paragraph, the KT is untouched
        assert isinstance(out[0], Paragraph)
        assert out[1] is existing_kt

    def test_skips_two_headings_in_a_row(self):
        tpl = _StubTemplate()
        story = [_h1("Part 1"), _h1("Chapter 1"), _body("content")]
        out = tpl._protect_section_headings(story)
        # First H1 should remain bare (next is another H1); second H1
        # should be wrapped with body.
        assert isinstance(out[0], Paragraph)
        assert isinstance(out[1], KeepTogether)

    def test_allows_spacer_between_h1_and_body(self):
        tpl = _StubTemplate()
        spacer = Spacer(1, 2 * mm)
        story = [_h1("Chapter"), spacer, _body("content")]
        out = tpl._protect_section_headings(story)
        assert len(out) == 1
        kt = out[0]
        assert isinstance(kt, KeepTogether)
        # KeepTogether should contain [H1, spacer, body]
        assert len(kt._content) == 3

    def test_clears_keepwithnext_on_wrapped_neighbour(self):
        tpl = _StubTemplate()
        body_para = _body("content")
        body_para.keepWithNext = True
        story = [_h1("Chapter"), body_para]
        tpl._protect_section_headings(story)
        assert body_para.keepWithNext is False

    def test_idempotent(self):
        tpl = _StubTemplate()
        story = [_h1("Chapter 1"), _body("first")]
        once = tpl._protect_section_headings(story)
        twice = tpl._protect_section_headings(list(once))
        # Running twice must not double-wrap
        assert len(once) == len(twice) == 1
        assert isinstance(twice[0], KeepTogether)

    def test_escape_hatch(self):
        tpl = _StubTemplate(config={"project": {"disable_orphan_protection": True}})
        story = [_h1("Chapter"), _body("content")]
        out = tpl._protect_section_headings(story)
        assert out is story
        assert isinstance(out[0], Paragraph)
        assert isinstance(out[1], Paragraph)

    def test_preserves_non_heading_flowables(self):
        tpl = _StubTemplate()
        story = [_body("intro"), _body("more"), _h1("Chapter"), _body("body")]
        out = tpl._protect_section_headings(story)
        assert isinstance(out[0], Paragraph)
        assert isinstance(out[1], Paragraph)
        assert isinstance(out[2], KeepTogether)

    def test_h1_at_end_of_story(self):
        tpl = _StubTemplate()
        story = [_body("content"), _h1("Dangling")]
        out = tpl._protect_section_headings(story)
        # Nothing follows the H1 — leave it bare
        assert isinstance(out[-1], Paragraph)


# ---------------------------------------------------------------------------
# Empty-page collapse
# ---------------------------------------------------------------------------

class TestEmptyPageCollapse:
    def test_collapses_adjacent_page_breaks(self):
        tpl = _StubTemplate()
        story = [_body("a"), PageBreak(), PageBreak(), _body("b")]
        out = tpl._collapse_empty_page_runs(story)
        assert len(out) == 3
        assert sum(isinstance(f, PageBreak) for f in out) == 1

    def test_collapses_break_spacer_break(self):
        tpl = _StubTemplate()
        story = [_body("a"), PageBreak(), Spacer(1, 4 * mm), PageBreak(), _body("b")]
        out = tpl._collapse_empty_page_runs(story)
        assert sum(isinstance(f, PageBreak) for f in out) == 1

    def test_collapses_cond_and_hard_breaks(self):
        tpl = _StubTemplate()
        story = [_body("a"), CondPageBreak(80 * mm), PageBreak(), _body("b")]
        out = tpl._collapse_empty_page_runs(story)
        assert sum(isinstance(f, (PageBreak, CondPageBreak)) for f in out) == 1

    def test_single_page_break_untouched(self):
        tpl = _StubTemplate()
        story = [_body("a"), PageBreak(), _body("b")]
        out = tpl._collapse_empty_page_runs(story)
        assert len(out) == 3

    def test_escape_hatch(self):
        tpl = _StubTemplate(config={"project": {"disable_empty_page_collapse": True}})
        story = [_body("a"), PageBreak(), PageBreak(), _body("b")]
        out = tpl._collapse_empty_page_runs(story)
        assert out is story
        assert sum(isinstance(f, PageBreak) for f in out) == 2

    def test_three_breaks_in_a_row(self):
        tpl = _StubTemplate()
        story = [_body("a"), PageBreak(), PageBreak(), PageBreak(), _body("b")]
        out = tpl._collapse_empty_page_runs(story)
        assert sum(isinstance(f, PageBreak) for f in out) == 1

    def test_leading_and_trailing_untouched(self):
        tpl = _StubTemplate()
        story = [PageBreak(), _body("a"), PageBreak()]
        out = tpl._collapse_empty_page_runs(story)
        assert len(out) == 3

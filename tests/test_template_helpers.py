"""
Tests for briefkit.templates._helpers — universal architectural controls.
"""

from __future__ import annotations

import pytest
from reportlab.lib.units import mm
from reportlab.platypus import CondPageBreak, KeepTogether, PageBreak, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle

from briefkit.templates._helpers import (
    DEFAULT_MAX_SPACER_MM,
    DEFAULT_MIN_SECTION_SPACE_MM,
    SKIPPABLE_SECTIONS,
    SPACING,
    capped_spacer,
    chapter_opener,
    max_spacer_mm,
    min_section_space,
    optional_section,
    section_break,
    section_break_mode,
    should_skip,
)


# ---------------------------------------------------------------------------
# should_skip
# ---------------------------------------------------------------------------

class TestShouldSkip:
    def test_default_false_for_every_section(self):
        for section in SKIPPABLE_SECTIONS:
            assert should_skip({}, section) is False
            assert should_skip(None, section) is False

    def test_returns_true_when_flag_set(self):
        cfg = {"project": {"skip_preface": True}}
        assert should_skip(cfg, "preface") is True

    def test_other_sections_unaffected(self):
        cfg = {"project": {"skip_preface": True}}
        assert should_skip(cfg, "glossary") is False

    def test_unknown_section_raises(self):
        with pytest.raises(ValueError, match="Unknown skippable section"):
            should_skip({}, "not_a_real_section")

    def test_every_canonical_section_recognised(self):
        # Every entry in SKIPPABLE_SECTIONS must be queryable
        for section in SKIPPABLE_SECTIONS:
            should_skip({}, section)  # must not raise


# ---------------------------------------------------------------------------
# section_break_mode / min_section_space / max_spacer_mm
# ---------------------------------------------------------------------------

class TestConfigReaders:
    def test_section_break_mode_default(self):
        assert section_break_mode({}) == "auto"
        assert section_break_mode(None) == "auto"

    def test_section_break_mode_valid(self):
        assert section_break_mode({"project": {"section_break_mode": "hard"}}) == "hard"
        assert section_break_mode({"project": {"section_break_mode": "flow"}}) == "flow"

    def test_section_break_mode_invalid_falls_back_to_auto(self):
        assert section_break_mode({"project": {"section_break_mode": "nonsense"}}) == "auto"

    def test_min_section_space_default(self):
        assert min_section_space({}) == DEFAULT_MIN_SECTION_SPACE_MM

    def test_min_section_space_override(self):
        assert min_section_space({"project": {"min_section_space_mm": 120}}) == 120.0

    def test_min_section_space_invalid_falls_back(self):
        assert min_section_space({"project": {"min_section_space_mm": "abc"}}) == DEFAULT_MIN_SECTION_SPACE_MM

    def test_max_spacer_default(self):
        assert max_spacer_mm({}) == DEFAULT_MAX_SPACER_MM

    def test_max_spacer_override(self):
        assert max_spacer_mm({"project": {"max_spacer_mm": 30}}) == 30.0


# ---------------------------------------------------------------------------
# section_break
# ---------------------------------------------------------------------------

class TestSectionBreak:
    def test_auto_emits_cond_page_break(self):
        story = []
        section_break(story, config={})
        assert len(story) == 1
        assert isinstance(story[0], CondPageBreak)

    def test_hard_emits_page_break(self):
        story = []
        section_break(story, config={"project": {"section_break_mode": "hard"}})
        assert len(story) == 1
        assert isinstance(story[0], PageBreak)

    def test_flow_emits_nothing(self):
        story = []
        section_break(story, config={"project": {"section_break_mode": "flow"}})
        assert story == []

    def test_force_overrides_mode(self):
        story = []
        section_break(story, config={"project": {"section_break_mode": "flow"}}, force=True)
        assert isinstance(story[0], PageBreak)

    def test_explicit_min_space_mm(self):
        story = []
        section_break(story, config={}, min_space_mm=120)
        assert isinstance(story[0], CondPageBreak)
        # CondPageBreak stores height in points (mm * mm)
        assert abs(story[0].height - 120 * mm) < 0.01


# ---------------------------------------------------------------------------
# optional_section
# ---------------------------------------------------------------------------

class TestOptionalSection:
    def test_appends_when_not_skipped(self):
        story = []
        flowables = [Paragraph("hi", ParagraphStyle("x"))]
        added = optional_section(story, {}, "preface", flowables)
        assert added is True
        assert len(story) == 1

    def test_skipped_when_flag_true(self):
        story = []
        flowables = [Paragraph("hi", ParagraphStyle("x"))]
        added = optional_section(story, {"project": {"skip_preface": True}}, "preface", flowables)
        assert added is False
        assert story == []

    def test_empty_flowables_early_exit(self):
        story = []
        added = optional_section(story, {}, "preface", [])
        assert added is False
        assert story == []

    def test_break_before_and_after(self):
        story = []
        flowables = [Paragraph("hi", ParagraphStyle("x"))]
        optional_section(story, {}, "preface", flowables, break_before=True, break_after=True)
        assert isinstance(story[0], CondPageBreak)
        assert isinstance(story[-1], CondPageBreak)
        assert len(story) == 3

    def test_skipped_section_does_not_emit_break(self):
        story = []
        flowables = [Paragraph("hi", ParagraphStyle("x"))]
        optional_section(
            story, {"project": {"skip_preface": True}},
            "preface", flowables,
            break_before=True, break_after=True,
        )
        assert story == []


# ---------------------------------------------------------------------------
# chapter_opener
# ---------------------------------------------------------------------------

class TestChapterOpener:
    def _style(self):
        return ParagraphStyle("H1", fontSize=18, leading=22, keepWithNext=True)

    def test_wraps_title_and_first_flowable_in_keeptogether(self):
        story = []
        body = [
            Paragraph("first", self._style()),
            Paragraph("second", self._style()),
            Paragraph("third", self._style()),
        ]
        chapter_opener(story, "Chapter 1", body, self._style())
        assert isinstance(story[0], KeepTogether)
        # First element is the KeepTogether, then remaining 2 body flowables
        assert len(story) == 3

    def test_clears_keepwithnext_on_first_body_flowable(self):
        style = self._style()
        first = Paragraph("first", style)
        first.keepWithNext = True
        chapter_opener([], "Chapter", [first], style)
        assert first.keepWithNext is False

    def test_empty_body(self):
        story = []
        chapter_opener(story, "Solo", [], self._style())
        assert len(story) == 2  # title + spacer
        assert isinstance(story[0], Paragraph)
        assert isinstance(story[1], Spacer)

    def test_single_body_flowable(self):
        story = []
        body = [Paragraph("only", self._style())]
        chapter_opener(story, "Ch", body, self._style())
        assert len(story) == 1
        assert isinstance(story[0], KeepTogether)


# ---------------------------------------------------------------------------
# capped_spacer
# ---------------------------------------------------------------------------

class TestCappedSpacer:
    def test_under_cap_passes_through(self):
        sp = capped_spacer(20, config={})
        assert abs(sp.height - 20 * mm) < 0.01

    def test_over_cap_clamped(self):
        sp = capped_spacer(200, config={})
        assert abs(sp.height - DEFAULT_MAX_SPACER_MM * mm) < 0.01

    def test_allow_large_bypasses_cap(self):
        sp = capped_spacer(200, config={}, allow_large=True)
        assert abs(sp.height - 200 * mm) < 0.01

    def test_custom_cap(self):
        sp = capped_spacer(100, config={"project": {"max_spacer_mm": 40}})
        assert abs(sp.height - 40 * mm) < 0.01


# ---------------------------------------------------------------------------
# Registry integrity
# ---------------------------------------------------------------------------

class TestRegistries:
    def test_skippable_sections_unique(self):
        assert len(SKIPPABLE_SECTIONS) == len(set(SKIPPABLE_SECTIONS))

    def test_skippable_sections_snake_case(self):
        for s in SKIPPABLE_SECTIONS:
            assert s == s.lower()
            assert " " not in s
            assert "-" not in s

    def test_spacing_tokens_positive(self):
        for name, val in SPACING.items():
            assert val > 0, f"SPACING[{name!r}] must be positive"

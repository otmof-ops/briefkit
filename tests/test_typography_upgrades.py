"""
Tests for the Phase 0–4 typography and correctness upgrades:
- smart punctuation
- link URL preservation with straight-quoted href attributes
- XML special character escaping in prose
- skip-flag typo detection
- widow/orphan defaults in _ps()
"""

from __future__ import annotations

import pytest

from briefkit.extractor import _strip_inline, parse_markdown


# ---------------------------------------------------------------------------
# Smart punctuation
# ---------------------------------------------------------------------------

class TestSmartPunctuation:
    def test_straight_double_quotes_become_curly(self):
        out = _strip_inline('She said "hello" to me.')
        assert "\u201c" in out  # left double quote
        assert "\u201d" in out  # right double quote

    def test_apostrophe_becomes_curly(self):
        out = _strip_inline("don't stop")
        assert "don\u2019t" in out

    def test_triple_dash_becomes_em_dash(self):
        out = _strip_inline("yes --- and no")
        assert "\u2014" in out

    def test_double_dash_becomes_en_dash(self):
        out = _strip_inline("pages 10--20")
        assert "\u2013" in out

    def test_three_dots_become_ellipsis(self):
        out = _strip_inline("wait...")
        assert "\u2026" in out

    def test_initials_get_nbsp(self):
        out = _strip_inline("J. Smith wrote")
        assert "J.\u00a0Smith" in out


# ---------------------------------------------------------------------------
# Link URL preservation
# ---------------------------------------------------------------------------

class TestLinkPreservation:
    def test_url_survives_into_link_tag(self):
        out = _strip_inline("See [docs](https://example.com) here.")
        assert "https://example.com" in out
        assert "<link" in out
        assert "docs</link>" in out

    def test_href_uses_straight_quotes_not_smart(self):
        # Regression: an earlier iteration ran smart-punctuation AFTER
        # the link substitution, turning href="..." into href=“...”.
        out = _strip_inline('Click [here](https://x.com) for details.')
        assert 'href="https://x.com"' in out
        # The curly quotes should appear around nothing here (no
        # double-quoted prose), so the only " characters in the output
        # belong to link attributes.
        assert "\u201c" not in out
        assert "\u201d" not in out

    def test_link_url_does_not_become_smart_punctuated(self):
        out = _strip_inline("Open [a](https://a.b/--and---stuff).")
        # The `--` and `---` inside the URL must survive unchanged
        assert "--and---stuff" in out


# ---------------------------------------------------------------------------
# XML escaping of prose
# ---------------------------------------------------------------------------

class TestProseEscaping:
    def test_ampersand_escaped(self):
        out = _strip_inline("Compare A & B")
        assert "&amp;" in out

    def test_angle_brackets_escaped(self):
        out = _strip_inline("Generic <foo> here")
        assert "&lt;foo&gt;" in out

    def test_code_span_preserves_and_escapes_internal_ampersand(self):
        out = _strip_inline("Use `a & b` as key")
        assert '<font name="Courier">a &amp; b</font>' in out


# ---------------------------------------------------------------------------
# Skip-flag typo detection
# ---------------------------------------------------------------------------

class TestSkipFlagTypoDetection:
    def test_unknown_skip_flag_raises_validation_error(self, tmp_path):
        from briefkit.config import load_config
        cfg_file = tmp_path / "briefkit.yml"
        cfg_file.write_text(
            "project:\n"
            "  name: test\n"
            "  skip_prefece: true\n"  # typo!
        )
        with pytest.raises(ValueError, match=r"skip_prefece"):
            load_config(cfg_file)

    def test_skip_flag_suggests_closest_match(self, tmp_path):
        from briefkit.config import load_config
        cfg_file = tmp_path / "briefkit.yml"
        cfg_file.write_text(
            "project:\n"
            "  name: test\n"
            "  skip_prefece: true\n"
        )
        try:
            load_config(cfg_file)
        except ValueError as exc:
            assert "skip_preface" in str(exc)
        else:
            pytest.fail("expected ValueError")

    def test_valid_skip_flag_accepted(self, tmp_path):
        from briefkit.config import load_config
        cfg_file = tmp_path / "briefkit.yml"
        cfg_file.write_text(
            "project:\n"
            "  name: test\n"
            "  skip_preface: true\n"
        )
        cfg = load_config(cfg_file)
        assert cfg["project"]["skip_preface"] is True


# ---------------------------------------------------------------------------
# Paragraph style defaults
# ---------------------------------------------------------------------------

class TestParagraphStyleDefaults:
    def test_default_style_has_widow_orphan_control(self):
        from briefkit.styles import _ps
        style = _ps("TestDefault")
        # allowWidows=0 means a single line widow at the top of the
        # next page is NOT permitted; allowOrphans=0 means the last
        # line of a paragraph cannot be stranded alone at page bottom.
        assert style.allowWidows == 0
        assert style.allowOrphans == 0

    def test_default_style_has_word_wrap(self):
        from briefkit.styles import _ps
        style = _ps("TestDefault2")
        assert getattr(style, "wordWrap", None) in ("LTR", "CJK")

    def test_h1_has_outline_level(self):
        from briefkit.styles import build_styles
        styles = build_styles()
        assert getattr(styles["STYLE_H1"], "outlineLevel", None) == 0
        assert getattr(styles["STYLE_H2"], "outlineLevel", None) == 1
        assert getattr(styles["STYLE_H3"], "outlineLevel", None) == 2


# ---------------------------------------------------------------------------
# Table separator detection (regression: em-dash smart-punct broke separator)
# ---------------------------------------------------------------------------

class TestTableSeparatorRobustness:
    def test_basic_table_still_parses_after_smart_punct(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        blocks = parse_markdown(md)
        assert len(blocks) == 1
        assert blocks[0]["type"] == "table"
        assert blocks[0]["headers"] == ["A", "B"]
        assert blocks[0]["rows"] == [["1", "2"]]

    def test_table_with_alignment_separator(self):
        md = "| A | B |\n|:---|---:|\n| 1 | 2 |"
        blocks = parse_markdown(md)
        assert blocks[0]["type"] == "table"

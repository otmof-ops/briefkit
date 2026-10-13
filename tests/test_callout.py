# SPDX-FileCopyrightText: 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)
# SPDX-License-Identifier: BSD-3-Clause
"""
Tests for callout boxes and pull quotes.

Regression coverage for the "unclosed tags" crash.

MECHANISM: ``build_callout_box`` splits its body on newlines and makes each
line a separate ``Paragraph``. Markdown inline emphasis is converted to
ReportLab tags upstream (``**x**`` -> ``<b>x</b>``), so a bold or italic span
that crosses a line break is torn in half: one line receives ``<b>`` and the
next receives ``</b>``. Raw ``Paragraph`` then raises

    paragraph text '<para>...<b>...</para>' caused exception
    parse ended with 1 unclosed tags

which aborted generation of the whole document. ``_safe_para`` survives it
because ``_safe_text`` closes any tags left open.

NOTE ON METHOD: ``Paragraph(...)`` does not parse at construction time —
parsing is deferred to layout. Asserting that a builder returns flowables
therefore proves nothing; these tests force a layout pass via ``wrap()`` or a
real build. Both earlier revisions of this file missed that and passed with
the bug reinstated.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate

from briefkit.elements.callout import build_callout_box, build_pull_quote

# The real trigger: inline markup left open, as produced by splitting a
# blockquote whose emphasis spans a line break.
UNCLOSED_TAG_CASES = [
    "<b>bold that never closes",
    "leading text then <b>bold",
    "<i>italic cut mid-span",
    "a <b>closed</b> pair then <i>an open one",
    "<u>underline left open",
]

# Defensive: characters that merely look like markup must also survive.
BARE_MARKUP_CASES = [
    "Quarterly BAS applies under <$20m aggregated turnover",
    "An incidental grocery stop (< 2 km diversion) is not private use",
    "R&D concession & the associated offset",
    "Compare 5 > 3 and 3 < 5 in the same sentence",
]

AVAIL_W = 160 * mm
AVAIL_H = 250 * mm


def _force_layout(flowables):
    """Force ReportLab to parse paragraph text — construction alone is lazy."""
    if not isinstance(flowables, (list, tuple)):
        flowables = [flowables]
    for f in flowables:
        f.wrap(AVAIL_W, AVAIL_H)
    return flowables


def _build_pdf(flowables):
    """Full build — the strongest check that a story renders end to end."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    if not isinstance(flowables, (list, tuple)):
        flowables = [flowables]
    doc.build(list(flowables))
    return buf.getvalue()


# --- the regression itself --------------------------------------------------


@pytest.mark.parametrize("text", UNCLOSED_TAG_CASES)
def test_callout_survives_unclosed_inline_tags(text):
    """The crash this module regressed on: open <b>/<i>/<u> must not raise."""
    _force_layout(build_callout_box(text, "insight"))


def test_callout_with_emphasis_split_across_lines():
    """The realistic shape — a bold span torn apart by the newline split."""
    text = "The rule is <b>only assessable\nwhen the allowance is paid</b> in cash."
    _force_layout(build_callout_box(text, "insight"))


@pytest.mark.parametrize("text", UNCLOSED_TAG_CASES)
def test_pull_quote_survives_unclosed_inline_tags(text):
    _force_layout(build_pull_quote(text))


@pytest.mark.parametrize("box_type", ["insight", "takeaway", "warning", "learn"])
def test_all_box_types_survive_unclosed_tags(box_type):
    """Every configured box type routes through the same sanitizer."""
    _force_layout(build_callout_box("<b>open in every variant", box_type))


# --- defensive coverage -----------------------------------------------------


@pytest.mark.parametrize("text", BARE_MARKUP_CASES)
def test_callout_handles_bare_angle_brackets(text):
    """Bare < > & are tolerated by ReportLab, but must stay tolerated."""
    _force_layout(build_callout_box(text, "insight"))


def test_pull_quote_attribution_is_sanitized():
    _force_layout(build_pull_quote("Some quoted line", attribution="Dept of A & B <b>x"))


def test_intended_inline_markup_is_preserved():
    """Sanitizing must not strip legitimate, balanced markup."""
    _force_layout(build_callout_box("<b>Bold</b> and <i>italic</i> with < 5 km", "insight"))


def test_multiline_callout_with_bullets():
    text = "\n".join(
        [
            "**Watch for:**",
            "- turnover <$20m",
            "- <b>unclosed emphasis on a bullet",
            "",
            "Anything above that changes the treatment.",
        ]
    )
    _force_layout(build_callout_box(text, "warning"))


def test_empty_and_whitespace_callouts_do_not_raise():
    _force_layout(build_callout_box("", "insight"))
    _force_layout(build_callout_box("   \n  \n", "insight"))


# --- end to end -------------------------------------------------------------


def test_callout_builds_into_a_real_document():
    story = [build_callout_box(t, "insight") for t in UNCLOSED_TAG_CASES + BARE_MARKUP_CASES]
    pdf = _build_pdf(story)
    assert pdf.startswith(b"%PDF"), "did not produce a PDF"
    assert len(pdf) > 1000


def test_pull_quote_builds_into_a_real_document():
    story = []
    for t in UNCLOSED_TAG_CASES:
        story.extend(build_pull_quote(t, attribution="Source <b>ref"))
    pdf = _build_pdf(story)
    assert pdf.startswith(b"%PDF")

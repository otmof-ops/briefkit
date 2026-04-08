"""
briefkit.templates._helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Universal architectural controls shared across every briefkit template.

This module is the single source of truth for the "guard rails" and
"switches" that every template honours, so that a user's config behaves
identically regardless of which template they pick.

Design goals
------------
1. **Every optional section is suppressible.** Users can turn off any
   non-essential front-matter or back-matter section by setting a
   ``project.skip_<section>: true`` flag in ``briefkit.yml``. Mandatory
   structural elements (cover, title page, body, chapters, procedures)
   are never suppressible — if you don't want them, pick a different
   template.

2. **No orphaned titles.** The ``chapter_opener`` helper wraps any
   ``H1 title + first content flowable`` pair in a ``KeepTogether`` so
   a large opening table/figure cannot strand the title alone on an
   otherwise-empty page.

3. **No unjustified big gaps.** The ``section_break`` helper prefers
   ``CondPageBreak`` over ``PageBreak`` for transitions between small
   or medium sections, so a one-paragraph preface followed by a one-row
   revision history does not produce two half-empty pages. Templates
   that genuinely need a recto page break (chapter openers in a bound
   book, etc.) can still call ``PageBreak`` directly.

4. **Spacing caps.** The ``capped_spacer`` helper clamps any accidental
   ``Spacer(1, 100*mm)`` to a configurable maximum so a tweak to one
   template doesn't silently leave a blank page in another.

Public API
----------
- ``should_skip(config, section)`` — read ``project.skip_<section>``
- ``optional_section(story, config, section, flowables, *, break_before=False, break_after=False)``
- ``chapter_opener(story, title_text, body_flowables, style, *, spacer_mm=2)``
- ``section_break(story, *, min_space_mm=80)``
- ``capped_spacer(height_mm, *, max_mm=60)``
- ``SKIPPABLE_SECTIONS`` — canonical list of suppressible section names
- ``SPACING`` — canonical spacing tokens (in mm)

Config surface
--------------
::

    project:
      skip_preface:          false   # book, novel, academic, manual, report
      skip_foreword:         false   # book, novel
      skip_acknowledgments:  false   # book, academic, proposal, whitepaper
      skip_abstract:         false   # academic, report, whitepaper, deep_research
      skip_executive_summary: false  # briefing, report, proposal, policy, evaluation
      skip_dashboard:        false   # briefing, evaluation
      skip_glossary:         false   # book, novel, manual, academic, policy, guide
      skip_bibliography:     false   # almost every template
      skip_references:       false   # academic, deep_research, whitepaper
      skip_index:            false   # book, manual
      skip_appendices:       false   # academic, report, manual, whitepaper
      skip_revision_history: false   # manual, sop, policy, playbook
      skip_safety_warnings:  false   # manual, sop
      skip_colophon:         false   # book, novel
      skip_back_cover:       false   # briefing, report, manual, proposal, evaluation
      skip_toc:              false   # every template with a TOC
      skip_copyright_page:   false   # book, novel
      skip_half_title:       false   # book, novel

      # Spacing controls
      section_break_mode:    "auto"  # auto | hard | flow
                                      #   auto — CondPageBreak between small sections,
                                      #          PageBreak between large ones
                                      #   hard — always PageBreak
                                      #   flow — never PageBreak (continuous flow)
      min_section_space_mm:  80      # CondPageBreak threshold
      max_spacer_mm:         60      # cap on any single Spacer

All flags default to ``false`` (= show the section). Flags that name a
section a template does not build are silently ignored. This means a
single ``briefkit.yml`` can carry a full skip_* manifest and work
across every template without error.
"""

from __future__ import annotations

from typing import Any, Iterable

from reportlab.lib.units import mm
from reportlab.platypus import CondPageBreak, KeepTogether, PageBreak, Paragraph, Spacer


# ---------------------------------------------------------------------------
# Canonical registries
# ---------------------------------------------------------------------------

#: Every section name that may appear after ``skip_`` in project config.
#: Templates SHOULD consult this registry via :func:`should_skip` rather
#: than reading config directly, so the surface stays consistent.
SKIPPABLE_SECTIONS: tuple[str, ...] = (
    "half_title",
    "title_page",
    "copyright_page",
    "toc",
    "foreword",
    "preface",
    "acknowledgments",
    "abstract",
    "executive_summary",
    "dashboard",
    "introduction",
    "scope",
    "methodology",
    "literature_review",
    "results",
    "discussion",
    "findings",
    "recommendations",
    "conclusion",
    "references",
    "bibliography",
    "glossary",
    "index",
    "appendices",
    "revision_history",
    "safety_warnings",
    "troubleshooting",
    "reference_tables",
    "colophon",
    "back_cover",
)

#: Canonical spacing tokens in millimetres. Use these instead of raw
#: numbers so a single site-wide tweak reflows every template.
SPACING: dict[str, float] = {
    "tight":    1.0,
    "small":    2.0,
    "medium":   4.0,
    "large":    8.0,
    "xlarge":  12.0,
    "section": 16.0,
    "page":    24.0,
}

#: Default CondPageBreak threshold in mm — if less than this remains on
#: the page, start a new page; otherwise keep flowing.
DEFAULT_MIN_SECTION_SPACE_MM: float = 80.0

#: Hard cap on any single Spacer flowable, to prevent accidental
#: massive gaps when a template is tuned for one page size and used
#: on another. Cover / title / half-title / colophon pages are allowed
#: to bypass this via the ``allow_large`` flag on :func:`capped_spacer`.
DEFAULT_MAX_SPACER_MM: float = 60.0


# ---------------------------------------------------------------------------
# Config readers
# ---------------------------------------------------------------------------

def _project_cfg(config: dict | None) -> dict:
    if not config:
        return {}
    return config.get("project", {}) or {}


def should_skip(config: dict | None, section: str) -> bool:
    """
    Return True if the user has asked to suppress *section*.

    Reads ``project.skip_<section>`` from the config. Unknown section
    names raise a ``ValueError`` so typos surface immediately rather
    than silently doing nothing.
    """
    if section not in SKIPPABLE_SECTIONS:
        raise ValueError(
            f"Unknown skippable section {section!r}. "
            f"Valid names: {', '.join(SKIPPABLE_SECTIONS)}"
        )
    return bool(_project_cfg(config).get(f"skip_{section}", False))


def section_break_mode(config: dict | None) -> str:
    """Return the configured section-break mode: ``auto``, ``hard``, or ``flow``."""
    mode = str(_project_cfg(config).get("section_break_mode", "auto")).lower()
    if mode not in ("auto", "hard", "flow"):
        mode = "auto"
    return mode


def min_section_space(config: dict | None) -> float:
    """Return the CondPageBreak threshold in mm."""
    try:
        return float(_project_cfg(config).get(
            "min_section_space_mm", DEFAULT_MIN_SECTION_SPACE_MM
        ))
    except (TypeError, ValueError):
        return DEFAULT_MIN_SECTION_SPACE_MM


def max_spacer_mm(config: dict | None) -> float:
    """Return the Spacer cap in mm."""
    try:
        return float(_project_cfg(config).get(
            "max_spacer_mm", DEFAULT_MAX_SPACER_MM
        ))
    except (TypeError, ValueError):
        return DEFAULT_MAX_SPACER_MM


# ---------------------------------------------------------------------------
# Flowable builders
# ---------------------------------------------------------------------------

def section_break(
    story: list,
    *,
    config: dict | None = None,
    min_space_mm: float | None = None,
    force: bool = False,
) -> None:
    """
    Insert a section break between two sections of a story.

    Honours ``project.section_break_mode``:

    - ``auto`` (default): ``CondPageBreak`` — only breaks if less than
      ``min_space_mm`` remains on the page. Prevents half-empty pages
      when one small section follows another.
    - ``hard``: always ``PageBreak`` — classic recto-start behaviour.
    - ``flow``: no break at all — continuous flow (use a rule or
      spacer upstream if you need a visual divider).

    Pass ``force=True`` to override the mode and emit an unconditional
    PageBreak. This is for cases where the template genuinely needs a
    new page (e.g. between the half-title and the full title in a
    printed book) regardless of user preference.
    """
    if force:
        story.append(PageBreak())
        return

    mode = section_break_mode(config)
    if mode == "hard":
        story.append(PageBreak())
    elif mode == "flow":
        # No break — caller is expected to insert its own visual
        # separator if desired.
        return
    else:  # auto
        threshold = min_space_mm if min_space_mm is not None else min_section_space(config)
        story.append(CondPageBreak(threshold * mm))


def optional_section(
    story: list,
    config: dict | None,
    section: str,
    flowables: Iterable[Any],
    *,
    break_before: bool = False,
    break_after: bool = False,
    force_break_before: bool = False,
    force_break_after: bool = False,
) -> bool:
    """
    Append *flowables* for *section* to *story* iff the user has not
    asked to skip it AND the flowables are non-empty.

    Returns True if the section was appended, False if it was skipped.

    This is the single entry point templates should use for every
    suppressible section. It handles:

    - ``project.skip_<section>`` check
    - empty-flowable early-exit (so a skipped-but-not-configured
      empty bibliography doesn't emit a page break)
    - optional section break before / after (honouring
      ``section_break_mode``)

    Example::

        preface_flowables = self._build_preface(content)
        optional_section(
            story, self.config, "preface", preface_flowables,
            break_after=True,
        )
    """
    flowables = list(flowables) if flowables else []
    if not flowables:
        return False
    if should_skip(config, section):
        return False

    if break_before:
        section_break(story, config=config, force=force_break_before)
    story.extend(flowables)
    if break_after:
        section_break(story, config=config, force=force_break_after)
    return True


def chapter_opener(
    story: list,
    title_text: str,
    body_flowables: list,
    style,
    *,
    spacer_mm: float = 2.0,
) -> None:
    """
    Append a chapter/section opener that is safe against orphaned titles.

    When a chapter's first body flowable is large (a wide table, a full
    figure, a long block of code), a bare ``PageBreak → H1 → body``
    sequence can strand the H1 alone on an otherwise-empty page because
    the H1's ``keepWithNext`` chain breaks at the intervening ``Spacer``
    and the body flowable is pushed to the next page without pulling
    the title with it.

    This helper fixes that by wrapping ``[H1, small spacer, first body
    flowable]`` in a ``KeepTogether``. It also clears ``keepWithNext``
    on that first body flowable so the ``KeepTogether`` container is
    not itself dragged into a split with a still-larger following
    flowable (which would re-orphan the title).

    Parameters
    ----------
    story : list
        The flowable story the opener will be appended to.
    title_text : str
        The H1 text (already escaped / safe for Paragraph).
    body_flowables : list
        The full body flowable list for the chapter. May be empty.
    style : ParagraphStyle
        The H1 style (typically ``self.styles["STYLE_H1"]``).
    spacer_mm : float, optional
        Vertical space between the title and the first body flowable.
        Defaults to 2 mm.
    """
    title_para = Paragraph(title_text, style)

    if body_flowables:
        first = body_flowables[0]
        if hasattr(first, "keepWithNext"):
            # Clearing this prevents the KeepTogether from being dragged
            # into a split with an oversized *following* flowable.
            first.keepWithNext = False
        story.append(KeepTogether(
            [title_para, Spacer(1, spacer_mm * mm), first]
        ))
        story.extend(body_flowables[1:])
    else:
        story.append(title_para)
        story.append(Spacer(1, spacer_mm * mm))


def capped_spacer(
    height_mm: float,
    *,
    config: dict | None = None,
    allow_large: bool = False,
) -> Spacer:
    """
    Return a ``Spacer`` whose height is clamped to the configured cap.

    Pass ``allow_large=True`` on cover / title / half-title / colophon
    pages where a 100 mm spacer is legitimately part of the layout.
    Everywhere else, large spacers are almost always a bug or a
    page-size mismatch, so they are clamped to ``project.max_spacer_mm``
    (default 60 mm).
    """
    if allow_large:
        return Spacer(1, height_mm * mm)
    cap = max_spacer_mm(config)
    return Spacer(1, min(height_mm, cap) * mm)


__all__ = [
    "SKIPPABLE_SECTIONS",
    "SPACING",
    "DEFAULT_MIN_SECTION_SPACE_MM",
    "DEFAULT_MAX_SPACER_MM",
    "should_skip",
    "section_break_mode",
    "min_section_space",
    "max_spacer_mm",
    "section_break",
    "optional_section",
    "chapter_opener",
    "capped_spacer",
]

"""
briefkit.templates
~~~~~~~~~~~~~~~~~~
Template registry — all built-in briefing templates and a get_template() factory.


Available templates
-------------------
  briefing   BriefingTemplate   — default executive briefing (cover, TOC, exec summary,
                                   dashboard, body chapters, cross-refs, index, bibliography,
                                   back cover)
  report     ReportTemplate     — formal report (cover, TOC, abstract, methodology, findings,
                                   discussion, recommendations, appendices, bibliography, back cover)
  book       BookTemplate       — long-form book (half-title, title page, copyright, TOC,
                                   preface, chapters, glossary, bibliography, index, colophon)
  novel      NovelTemplate      — narrative-aware novel (extends book with pattern-based
                                   styling for system commands, error tags, corrupted text,
                                   entity voices, and metafictional intrusions)
  manual     ManualTemplate     — technical manual (cover, revision history, TOC, safety
                                   warnings, scope, procedures, reference tables, troubleshooting,
                                   bibliography, back cover)
  academic   AcademicTemplate   — academic paper (title page, abstract, TOC, introduction,
                                   literature review, body, results, discussion, conclusion,
                                   references, appendices)
  minimal    MinimalTemplate    — stripped-down output (title, TOC, body, bibliography)
  letter     LetterTemplate     — formal correspondence (letterhead, date, body, signature)
  contract   ContractTemplate   — legal agreement (title page, recitals, definitions, clauses,
                                   schedules, execution block)
  register   RegisterTemplate   — table-dominant register (title, consolidated table,
                                   summary stats — risk registers, data dictionaries,
                                   compliance matrices)
  minutes    MinutesTemplate    — meeting minutes (header, attendees, agenda items,
                                   action items, resolutions, closing)
"""
from __future__ import annotations

from briefkit.templates.academic import AcademicTemplate
from briefkit.templates.book import BookTemplate
from briefkit.templates.briefing import BriefingTemplate
from briefkit.templates.contract import ContractTemplate
from briefkit.templates.letter import LetterTemplate
from briefkit.templates.manual import ManualTemplate
from briefkit.templates.minimal import MinimalTemplate
from briefkit.templates.minutes import MinutesTemplate
from briefkit.templates.novel import NovelTemplate
from briefkit.templates.register import RegisterTemplate
from briefkit.templates.report import ReportTemplate

_REGISTRY: dict[str, type] = {
    "briefing":  BriefingTemplate,
    "report":    ReportTemplate,
    "book":      BookTemplate,
    "manual":    ManualTemplate,
    "academic":  AcademicTemplate,
    "minimal":   MinimalTemplate,
    "letter":    LetterTemplate,
    "contract":  ContractTemplate,
    "register":  RegisterTemplate,
    "minutes":   MinutesTemplate,
    "novel":     NovelTemplate,
}


def get_template(name: str) -> type:
    """
    Return the template class for the given *name*.

    Parameters
    ----------
    name : str
        Template name, case-insensitive.  One of:
        briefing, report, book, manual, academic, minimal, letter, contract,
        register, minutes.

    Returns
    -------
    type
        The template class (subclass of BaseBriefingTemplate).

    Raises
    ------
    ValueError
        If *name* is not found in the registry.
    """
    key = name.lower().strip()
    if key not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(
            f"Unknown template: {name!r}.  Available templates: {available}"
        )
    return _REGISTRY[key]


def list_templates() -> list[str]:
    """Return a sorted list of all registered template names."""
    return sorted(_REGISTRY.keys())


__all__ = [
    "BriefingTemplate",
    "ReportTemplate",
    "BookTemplate",
    "ManualTemplate",
    "AcademicTemplate",
    "MinimalTemplate",
    "LetterTemplate",
    "ContractTemplate",
    "RegisterTemplate",
    "MinutesTemplate",
    "NovelTemplate",
    "get_template",
    "list_templates",
]

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
  proposal   ProposalTemplate   — business proposal (cover, TOC, exec summary, scope,
                                   deliverables, timeline, pricing, terms, acceptance, back cover)
  policy     PolicyTemplate     — policy document (cover, doc control, TOC, purpose, definitions,
                                   policy statements, compliance, review, approvals, version history)
  register   RegisterTemplate   — table-dominant register (title, consolidated table,
                                   summary stats — risk registers, data dictionaries,
                                   compliance matrices)
  minutes    MinutesTemplate    — meeting minutes (header, attendees, agenda items,
                                   action items, resolutions, closing)
  evaluation EvaluationTemplate — evaluation report (cover, summary, rubric table,
                                   detailed findings, statistics, recommendations,
                                   back cover)
  newsletter NewsletterTemplate — newsletter (banner, feature article, article sections,
                                   pull quotes, callout boxes, footer)
  invoice    InvoiceTemplate    — professional invoice (header, metadata, bill-to,
                                   line items table, totals, payment terms)
  quote      QuoteTemplate      — quote/estimate (header, metadata, client info,
                                   scope of work, pricing table, terms, acceptance)
  certificate CertificateTemplate — single-page landscape certificate (decorative border,
                                   title, recipient, description, signature)
  resume     ResumeTemplate     — professional CV/resume (centered name, education,
                                   work experience, skills — monochrome, single page)
"""
from __future__ import annotations

from briefkit.templates.academic import AcademicTemplate
from briefkit.templates.book import BookTemplate
from briefkit.templates.briefing import BriefingTemplate
from briefkit.templates.certificate import CertificateTemplate
from briefkit.templates.contract import ContractTemplate
from briefkit.templates.evaluation import EvaluationTemplate
from briefkit.templates.invoice import InvoiceTemplate
from briefkit.templates.letter import LetterTemplate
from briefkit.templates.manual import ManualTemplate
from briefkit.templates.minimal import MinimalTemplate
from briefkit.templates.minutes import MinutesTemplate
from briefkit.templates.newsletter import NewsletterTemplate
from briefkit.templates.novel import NovelTemplate
from briefkit.templates.policy import PolicyTemplate
from briefkit.templates.proposal import ProposalTemplate
from briefkit.templates.quote import QuoteTemplate
from briefkit.templates.register import RegisterTemplate
from briefkit.templates.report import ReportTemplate
from briefkit.templates.resume import ResumeTemplate

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
    "proposal":  ProposalTemplate,
    "policy":    PolicyTemplate,
    "evaluation": EvaluationTemplate,
    "newsletter": NewsletterTemplate,
    "invoice":      InvoiceTemplate,
    "quote":        QuoteTemplate,
    "certificate":  CertificateTemplate,
    "resume":       ResumeTemplate,
}


def get_template(name: str) -> type:
    """
    Return the template class for the given *name*.

    Parameters
    ----------
    name : str
        Template name, case-insensitive.  One of:
        briefing, report, book, manual, academic, minimal, letter, contract,
        register, minutes, evaluation, newsletter, proposal, policy, invoice, quote.

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
    "NewsletterTemplate",
    "NovelTemplate",
    "EvaluationTemplate",
    "ProposalTemplate",
    "PolicyTemplate",
    "InvoiceTemplate",
    "QuoteTemplate",
    "CertificateTemplate",
    "ResumeTemplate",
    "get_template",
    "list_templates",
]

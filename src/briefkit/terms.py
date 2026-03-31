"""Key terms extraction and filtering."""
import re

_GENERIC_TERMS = frozenset([
    "introduction", "overview", "summary", "contents", "references", "notes",
    "section", "chapter", "table", "figure", "appendix", "conclusion",
    "background", "abstract", "results", "discussion", "methods", "methodology",
    "acknowledgements", "acknowledgments", "bibliography", "index", "preface",
])


def extract_terms(text, title="", max_terms=40, filter_generic=True):
    """
    Extract key terms from text content.

    Scans for bold phrases, H2/H3 headings, and table headers.

    Args:
        text: Full text to scan.
        title: Document title (terms matching title are excluded).
        max_terms: Maximum number of terms to return.
        filter_generic: If True, filter out generic section headings.

    Returns:
        dict: Mapping of term -> "" (empty definition placeholder).
    """
    # Bold terms
    bold_terms = re.findall(r'\*\*([A-Z][a-zA-Z\s\-]{3,40})\*\*', text)
    # Heading terms (H2/H3)
    heading_terms = re.findall(r'^#{2,3}\s+(.{4,50})\s*$', text, re.MULTILINE)

    all_candidate_terms = (
        [t.strip() for t in bold_terms] +
        [t.strip() for t in heading_terms]
    )

    title_lower = title.lower() if title else ""
    seen_lower = set()
    terms = {}

    for term_raw in all_candidate_terms:
        term_clean = re.sub(r'[#\*`]', '', term_raw).strip()
        term_lower = term_clean.lower()

        if (term_clean
                and len(term_clean) >= 4
                and (not filter_generic or term_lower not in _GENERIC_TERMS)
                and term_lower not in seen_lower
                and term_lower not in title_lower
                and not re.match(r'^\d+', term_clean)):
            terms[term_clean] = ""
            seen_lower.add(term_lower)

    if len(terms) > max_terms:
        sorted_terms = sorted(terms.keys(), key=str.lower)[:max_terms]
        terms = {t: "" for t in sorted_terms}

    return terms

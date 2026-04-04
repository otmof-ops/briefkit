"""
Bibliography and citation extraction.

Extracts citations from text using multiple patterns:
  - APA style: Author et al. (YYYY)
  - Author (YYYY)
  - Author and Author (YYYY)
  - [Author YYYY] bracketed
  - Legislation: Something Act YYYY (Cth)
  - RFC references: RFC NNNN
  - Case law: Name v Name
"""
from __future__ import annotations

import re
from pathlib import Path

KNOWN_PUBLISHERS = {
    "world-bank": "World Bank",
    "alrc": "ALRC",
    "oecd": "OECD",
    "oaic": "OAIC",
    "law-council": "Law Council",
    "judicial-college": "Judicial College",
    "nist": "NIST",
    "iso": "ISO",
    "iec": "IEC",
    "ieee": "IEEE",
    "ietf": "IETF",
    "rfc": "RFC",
    "un": "United Nations",
    "who": "WHO",
    "imf": "IMF",
    "ecb": "ECB",
    "bis": "BIS",
    "sec": "SEC",
    "fdic": "FDIC",
    "cat": "Caterpillar",
    "ti": "Texas Instruments",
    "intel": "Intel",
    "amd": "AMD",
    "nvidia": "NVIDIA",
    "stm": "STMicroelectronics",
    "nxp": "NXP",
    "oscola": "OSCOLA",
    "accc": "ACCC",
    "fca": "FCA",
    "ftc": "FTC",
    "ico": "ICO",
    "cnil": "CNIL",
    "ansi": "ANSI",
    "osha": "OSHA",
}

_KNOWN_PUBLISHERS_SORTED = sorted(KNOWN_PUBLISHERS.keys(), key=len, reverse=True)

# Pre-compiled citation patterns (moved to module level to avoid re-compilation per call)
_CITE_PATTERNS = [
    re.compile(r'([A-Z][a-z]+(?:\s+et\s+al\.?))\s*\(\s*((?:19|20)\d{2})\s*(?:,\s*p\.?\s*\d+)?\s*\)'),
    re.compile(r'([A-Z][a-z]+)\s+\(\s*((?:19|20)\d{2})\s*(?:,\s*p\.?\s*\d+)?\s*\)'),
    re.compile(r'([A-Z][a-z]+\s+and\s+[A-Z][a-z]+)\s*\(\s*((?:19|20)\d{2})\s*\)'),
    re.compile(r'([A-Z][a-z]+(?:,\s+[A-Z][a-z]+)+,?\s+and\s+[A-Z][a-z]+)\s*\(\s*((?:19|20)\d{2})\s*\)'),
    re.compile(r'\[([A-Z][a-z]+)\s+((?:19|20)\d{2})\]'),
    re.compile(r'\(([A-Z][a-z]+),\s*((?:19|20)\d{2})\s*\)'),
]
_ACT_PATTERN = re.compile(r'\b([A-Z][A-Za-z]*(?:\s+[A-Za-z]+){0,8}\s+Act\s+(?:19|20)\d{2})\b')
_RFC_PATTERN = re.compile(r'RFC\s+(\d{3,5})', re.IGNORECASE)
_CASE_PATTERN = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,5})\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,5})\b')


def _parse_kebab_bibliography(stem):
    """Parse a kebab-case PDF stem into (authors, title, year)."""
    stem = stem.replace("_", "-").lower()
    stem = re.sub(r'-v\d+(\.\d+)*$', '', stem)
    stem = re.sub(r'-rev-\d+$', '', stem)

    matched_publisher = None
    remainder = stem
    for prefix in _KNOWN_PUBLISHERS_SORTED:
        if stem.startswith(prefix + "-") or stem == prefix:
            matched_publisher = KNOWN_PUBLISHERS[prefix]
            remainder = stem[len(prefix):].lstrip("-")
            break

    parts = remainder.split("-") if remainder else []
    year_parts = [p for p in parts if re.match(r'^(19|20)\d{2}[a-z]?$', p)]
    name_parts = [p for p in parts if not re.match(r'^(19|20)\d{2}[a-z]?$', p)
                  and not re.match(r'^\d+$', p)]

    year_str = year_parts[0][:4] if year_parts else ""

    if matched_publisher:
        author = matched_publisher
        title_str = " ".join(name_parts).title() if name_parts else matched_publisher
    else:
        if len(name_parts) >= 3 and re.match(r'^[a-z]+$', name_parts[-1]):
            author = name_parts[-1].title()
            title_str = " ".join(name_parts[:-1]).title()
        elif name_parts:
            author = name_parts[0].title()
            title_str = " ".join(name_parts[1:]).title() if len(name_parts) > 1 else name_parts[0].title()
        else:
            author = ""
            title_str = stem

    return author, title_str, year_str


def extract_bibliography(text, pdf_dir=None):
    """
    Extract bibliography entries from text and optional PDF directory.

    Args:
        text: Full text content to scan for inline citations.
        pdf_dir: Optional Path to directory containing source PDFs.

    Returns:
        list[dict]: Each dict has keys: title, authors, year, type, doi.
    """
    bibliography = []

    def _normalise_author(a):
        return re.sub(r'\.$', '', a.strip()).lower().replace("et al.", "et al")

    existing_keys = set()

    # Source 1: PDF filenames
    if pdf_dir:
        pdf_path = Path(pdf_dir)
        if pdf_path.is_dir():
            for pdf in sorted(pdf_path.glob("*.pdf")):
                if pdf.name == "executive-briefing.pdf":
                    continue
                stem = pdf.stem
                arxiv_match = re.match(r'^(\d{4}\.\d{4,5})(v\d+)?$', stem)
                if arxiv_match:
                    bibliography.append({
                        "title": f"arXiv:{arxiv_match.group(1)}",
                        "authors": "",
                        "year": ("20" if arxiv_match.group(1)[:2] < "50" else "19") + arxiv_match.group(1)[:2],
                        "type": "paper", "doi": "",
                    })
                else:
                    author, title_str, year_str = _parse_kebab_bibliography(stem)
                    if author or title_str:
                        bibliography.append({
                            "title": title_str or stem,
                            "authors": author,
                            "year": year_str,
                            "type": "paper",
                            "doi": "",
                        })
                        existing_keys.add((_normalise_author(author), year_str))

    if not text:
        return bibliography

    for pat in _CITE_PATTERNS:
        for match in pat.finditer(text):
            author, year = match.group(1).strip(), match.group(2)
            norm = (_normalise_author(author), year)
            if norm not in existing_keys:
                bibliography.append({
                    "title": "", "authors": author, "year": year,
                    "type": "paper", "doi": "",
                })
                existing_keys.add(norm)

    for match in _ACT_PATTERN.finditer(text):
        title_act = match.group(1).strip()
        year_m = re.search(r'((?:19|20)\d{2})', title_act)
        year = year_m.group(1) if year_m else ""
        norm = ("government", year)
        if norm not in existing_keys:
            bibliography.append({
                "title": title_act, "authors": "Government",
                "year": year, "type": "legislation", "doi": "",
            })
            existing_keys.add(norm)

    for match in _RFC_PATTERN.finditer(text):
        rfc_num = match.group(1)
        title_rfc = f"RFC {rfc_num}"
        norm = ("ietf", rfc_num)
        if norm not in existing_keys:
            bibliography.append({
                "title": title_rfc, "authors": "IETF",
                "year": "", "type": "specification", "doi": "",
            })
            existing_keys.add(norm)

    for match in _CASE_PATTERN.finditer(text):
        case_title = f"{match.group(1).strip()} v {match.group(2).strip()}"
        if (match.group(1)[0].isupper() and match.group(2)[0].isupper()
                and len(case_title) < 80):
            norm = ("case", case_title.lower())
            if norm not in existing_keys:
                bibliography.append({
                    "title": case_title, "authors": "",
                    "year": "", "type": "case", "doi": "",
                })
                existing_keys.add(norm)

    return bibliography

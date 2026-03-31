"""
briefkit.variants.legal — Legal document variant.

Adds: jurisdiction reference table, legislation index, case citation table,
regulatory bodies reference.
"""

from __future__ import annotations

import re

from reportlab.platypus import PageBreak, Spacer

from briefkit.styles import _safe_para, build_styles
from briefkit.elements.tables import build_data_table
from briefkit.variants import DocSetVariant, _register, collect_text

from reportlab.lib.units import mm


@_register
class LegalVariant(DocSetVariant):
    """Legal domain variant."""

    name = "legal"
    auto_detect_keywords = [
        "statute", "jurisdiction", "court", "plaintiff",
        "regulation", "legislation", "judicial",
    ]

    # Known jurisdiction names for quick scan
    _JURISDICTIONS = [
        "Australia", "United States", "United Kingdom", "European Union",
        "Canada", "New Zealand", "Germany", "France", "Singapore",
        "India", "Japan", "China", "South Africa", "Brazil",
    ]

    # Known regulatory body abbreviations
    _REG_BODIES = [
        "OAIC", "ACCC", "FCA", "SEC", "FTC", "ICO", "CNIL", "ASIC", "APRA",
        "AUSTRAC", "ACMA", "TGA", "AFCA", "AFP", "FIRB", "ABCC",
        "CFPB", "DOJ", "NLRB", "EEOC", "EPA", "FDA", "FCC", "CFTC",
        "FINRA", "OCC", "FDIC", "PCAOB",
    ]

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        all_content = collect_text(content)

        flowables.append(PageBreak())
        flowables.append(_safe_para("Law Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Jurisdiction reference ---
        flowables.append(_safe_para("Jurisdiction Reference", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        found_jurisdictions = []
        for jur in self._JURISDICTIONS:
            if re.search(r'\b' + re.escape(jur) + r'\b', all_content, re.IGNORECASE):
                found_jurisdictions.append([jur, "Covered", ""])

        if found_jurisdictions:
            flowables.extend(build_data_table(
                ["Jurisdiction", "Coverage", "Notes"],
                found_jurisdictions,
                title="Jurisdictions Covered",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Jurisdiction information not found — see source documents.", s_body
            ))

        # --- Legislation index ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Legislation Index", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        # Pattern: "Something Act 1234" or "Something Act 1234 (Cth)"
        leg_pat = re.compile(
            r'([A-Z][a-zA-Z\s]{3,50}Act\s+((?:19|20)\d{2}))\s*(?:\([A-Za-z]{2,6}\))?'
        )
        found_leg = []
        seen_leg = set()
        for m in leg_pat.finditer(all_content):
            title_str = m.group(1).strip()
            year = m.group(2)
            key = title_str.lower()
            if key not in seen_leg:
                found_leg.append([title_str, year, ""])
                seen_leg.add(key)

        if found_leg:
            flowables.extend(build_data_table(
                ["Legislation", "Year", "Jurisdiction"],
                found_leg[:15],
                title="Legislation Index",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "No legislation citations found — see source documents.", s_body
            ))

        # --- Case citation table ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Case Reference", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        # Pattern: "Plaintiff v Defendant" (both title-cased)
        case_pat = re.compile(
            r'([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)'
        )
        found_cases = []
        seen_cases = set()
        for m in case_pat.finditer(all_content):
            p1 = m.group(1).strip()
            p2 = m.group(2).strip()
            case_name = f"{p1} v {p2}"
            if (
                case_name not in seen_cases
                and len(case_name) < 80
                and p1[0].isupper()
                and p2[0].isupper()
            ):
                found_cases.append([case_name, "—", ""])
                seen_cases.add(case_name)

        if found_cases:
            flowables.extend(build_data_table(
                ["Case", "Citation", "Relevance"],
                found_cases[:15],
                title="Case Law Reference",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "No case citations found — see source documents.", s_body
            ))

        # --- Regulatory bodies ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Regulatory Bodies", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        found_regs = []
        for reg in self._REG_BODIES:
            if re.search(r'\b' + re.escape(reg) + r'\b', all_content):
                found_regs.append([reg, "Mentioned", ""])

        if found_regs:
            flowables.extend(build_data_table(
                ["Body", "Status", "Notes"],
                found_regs,
                title="Regulatory Bodies Referenced",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "No regulatory bodies identified — see source documents.", s_body
            ))

        return flowables

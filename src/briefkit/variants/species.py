"""
briefkit.variants.species — Species profile variant.

Adds: taxonomic classification table, conservation status, key
characteristics quick-reference.
"""

from __future__ import annotations

import re

from reportlab.platypus import PageBreak, Spacer

from briefkit.styles import _safe_para, build_styles
from briefkit.elements.tables import build_data_table
from briefkit.elements.callout import build_callout_box
from briefkit.variants import DocSetVariant, _register, collect_text

from reportlab.lib.units import mm

_TAXONOMIC_RANKS = ["Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species"]

_CONSERVATION_STATUSES = [
    "Extinct",
    "Extinct in the Wild",
    "Critically Endangered",
    "Endangered",
    "Vulnerable",
    "Near Threatened",
    "Least Concern",
    "Data Deficient",
    "Not Evaluated",
]

# Key characteristic extraction patterns (attribute → list of regex patterns)
_CHAR_PATTERNS = {
    "Diet": [
        r'\bdiet\b[:\s]+([^.\n]{5,60})',
        r'\bfeeds?\s+on\s+([^.\n]{5,60})',
        r'\b(herbivore|carnivore|omnivore|insectivore|detritivore)\b',
    ],
    "Habitat": [
        r'\bhabitat[:\s]+([^.\n]{5,60})',
        r'\bnative\s+to\s+([^.\n]{5,60})',
        r'\bdistributed\s+(?:across|throughout|in)\s+([^.\n]{5,60})',
        r'\bfound\s+in\s+([^.\n]{5,60})',
    ],
    "Lifespan": [
        r'\blifespan[:\s]+([^.\n]{5,40})',
        r'\blives?\s+for\s+([^.\n]{5,40})',
        r'\baverage\s+(?:age|lifespan)[:\s]+([^.\n]{5,40})',
    ],
    "Size / Mass": [
        r'\bweight[:\s]+([^.\n]{5,40})',
        r'\bmass[:\s]+([^.\n]{5,40})',
        r'\blength[:\s]+([^.\n]{5,40})',
        r'\bwingspan[:\s]+([^.\n]{5,40})',
    ],
    "Reproduction": [
        r'\bgestation[:\s]+([^.\n]{5,40})',
        r'\bclutch\s+size[:\s]+([^.\n]{5,30})',
        r'\bbrood[:\s]+([^.\n]{5,30})',
        r'\bincubation[:\s]+([^.\n]{5,40})',
    ],
}


@_register
class SpeciesVariant(DocSetVariant):
    """Species profile domain variant."""

    name = "species"
    auto_detect_keywords = [
        "species", "genus", "habitat", "conservation",
        "morphology", "taxonomy", "specimen",
    ]

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        all_content = collect_text(content)

        flowables.append(PageBreak())
        flowables.append(_safe_para("Species Profile Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Taxonomic classification ---
        flowables.append(_safe_para("Taxonomic Classification", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        taxonomy_rows = self._extract_taxonomy(content, all_content)
        if taxonomy_rows:
            flowables.extend(build_data_table(
                ["Rank", "Taxon"],
                taxonomy_rows,
                title="Taxonomy",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Taxonomic classification not found in source documents — see numbered docs.",
                s_body,
            ))

        # --- Conservation status ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Conservation Status", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        status_found, status_note = self._extract_conservation_status(all_content)
        if status_found:
            box_type = "warning" if status_found in (
                "Critically Endangered", "Endangered", "Extinct in the Wild", "Extinct"
            ) else "insight"
            flowables.append(build_callout_box(
                f"IUCN Status: {status_found}\n{status_note}",
                box_type,
                brand,
            ))
        else:
            flowables.append(_safe_para(
                "Conservation status not found — see source documents.", s_body
            ))

        # --- Key characteristics ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Key Characteristics", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        char_rows = self._extract_characteristics(all_content, status_found)
        flowables.extend(build_data_table(
            ["Attribute", "Value"],
            char_rows,
            title="Species Quick Reference",
            brand=brand,
        ))

        # --- Morphology notes ---
        morphology_content = self._extract_morphology(content, all_content)
        if morphology_content:
            flowables.append(Spacer(1, 4 * mm))
            flowables.append(_safe_para("Morphological Notes", s_h2))
            flowables.append(Spacer(1, 2 * mm))
            for note in morphology_content[:5]:
                flowables.append(_safe_para(note, styles["STYLE_BODY"]))

        return flowables

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_taxonomy(self, content, all_content):
        rows = []

        for rank in _TAXONOMIC_RANKS:
            m = re.search(
                rf'\b{rank}\s*[:\-]\s*([A-Za-z][a-z]+(?:\s+[a-z]+)?)',
                all_content, re.IGNORECASE,
            )
            if m:
                rows.append([rank, m.group(1).strip()])
                continue

            # Try structured tables
            for sub in content.get("subsystems", []):
                for tbl in sub.get("tables", []):
                    headers_low = [h.lower() for h in tbl.get("headers", [])]
                    if rank.lower() in headers_low:
                        col_i = headers_low.index(rank.lower())
                        for row in tbl.get("rows", []):
                            if col_i < len(row) and row[col_i].strip():
                                rows.append([rank, row[col_i].strip()])
                                break

        # Scientific name (italicised binomial *Genus species*)
        binomial_m = re.search(r'\*([A-Z][a-z]+\s+[a-z]+)\*', all_content)
        if binomial_m and not any(r[0] == "Species" for r in rows):
            rows.append(["Scientific Name", binomial_m.group(1)])

        return rows

    def _extract_conservation_status(self, all_content):
        for status in _CONSERVATION_STATUSES:
            if re.search(re.escape(status), all_content, re.IGNORECASE):
                # Grab context sentence
                m = re.search(
                    r'([^.\n]{0,80}' + re.escape(status) + r'[^.\n]{0,80})',
                    all_content, re.IGNORECASE,
                )
                note = m.group(1).strip() if m else ""
                return status, note
        return "", ""

    def _extract_characteristics(self, all_content, conservation_status):
        rows = []
        for attr, patterns in _CHAR_PATTERNS.items():
            found_val = "See source documents"
            for pat in patterns:
                m = re.search(pat, all_content, re.IGNORECASE)
                if m:
                    found_val = (m.group(1).strip() if m.lastindex else m.group(0).strip())[:80]
                    break
            rows.append([attr, found_val])
        rows.append(["Conservation Status", conservation_status or "See source documents"])
        return rows

    def _extract_morphology(self, content, all_content):
        notes = []
        morph_pat = re.compile(
            r'(?:^|\n)\s*(?:morph(?:ology|ological)?|plumage|colou?ration|pelage'
            r'|scale|fin|wing|tail|beak|bill)[:\s]+([^\n]{15,200})',
            re.IGNORECASE | re.MULTILINE,
        )
        seen = set()
        for m in morph_pat.finditer(all_content):
            txt = m.group(1).strip()
            key = txt[:40].lower()
            if key not in seen:
                notes.append(txt)
                seen.add(key)
        return notes

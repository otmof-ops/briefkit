"""
briefkit.variants.medical — Medical / clinical variant.

Adds: medical disclaimer banner, drug interaction table, dosage reference,
contraindications warning section, evidence quality table.
"""

from __future__ import annotations

import re

from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Spacer

from briefkit.elements.callout import build_callout_box
from briefkit.elements.tables import build_data_table
from briefkit.styles import _safe_para
from briefkit.variants import DocSetVariant, _register, collect_text

_MEDICAL_DISCLAIMER = (
    "MEDICAL INFORMATION — This document is for educational and research purposes only. "
    "Nothing in this briefing constitutes medical advice. Always consult a qualified "
    "healthcare professional before making any medical decisions."
)

_EVIDENCE_KEYWORDS = [
    (r'\brandomized?\s+controlled\s+trial\b|RCT\b',    "Randomized Controlled Trial (RCT)", "High"),
    (r'\bmeta-analysis\b',                              "Meta-Analysis",                     "Very High"),
    (r'\bsystematic\s+review\b',                        "Systematic Review",                 "Very High"),
    (r'\bcohort\s+study\b',                             "Cohort Study",                      "Moderate-High"),
    (r'\bcase.control\b',                               "Case-Control Study",                "Moderate"),
    (r'\bcase\s+series\b',                              "Case Series",                       "Low-Moderate"),
    (r'\bcase\s+report\b',                              "Case Report",                       "Low"),
    (r'\b(?:NICE|WHO|FDA|TGA|EMA)\s+guideline',         "Clinical Guideline",                "High"),
    (r'\blevel\s+of\s+evidence\b',                      "Level of Evidence referenced",      "Variable"),
]


@_register
class MedicalVariant(DocSetVariant):
    """Medical / clinical domain variant."""

    name = "medical"
    auto_detect_keywords = [
        "patient", "dosage", "clinical", "diagnosis",
        "treatment", "contraindication", "pharmacology",
    ]

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        # Prepend medical disclaimer at the very top
        flowables.insert(0, build_callout_box(_MEDICAL_DISCLAIMER, "warning", brand))

        all_content = collect_text(content)

        flowables.append(PageBreak())
        flowables.append(_safe_para("Medical Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Dosage reference ---
        flowables.append(_safe_para("Dosage Reference", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        dosage_rows = self._extract_dosage_table(content, all_content)
        if dosage_rows:
            flowables.extend(build_data_table(
                ["Drug / Substance", "Dosage", "Route", "Notes"],
                dosage_rows[:12],
                title="Dosage Quick Reference",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Dosage information not found in structured form — see numbered documents.",
                s_body,
            ))

        # --- Drug interactions ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Drug Interactions", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        interaction_rows = self._extract_interactions(content, all_content)
        if interaction_rows:
            flowables.extend(build_data_table(
                ["Drug A", "Drug B", "Interaction", "Severity"],
                interaction_rows[:12],
                title="Drug Interaction Reference",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Drug interaction data not found in structured form — see numbered documents.",
                s_body,
            ))

        # --- Contraindications warning ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Contraindications", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        contra_items = self._extract_contraindications(all_content)
        if contra_items:
            warn_text = "\n".join(f"- {c[:150]}" for c in contra_items[:10])
            flowables.append(build_callout_box(warn_text, "warning", brand))
        else:
            flowables.append(_safe_para(
                "No structured contraindication data found — see source documents.",
                s_body,
            ))

        # --- Evidence quality ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Clinical Relevance and Evidence Quality", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        evidence_rows = self._extract_evidence(all_content)
        flowables.extend(build_data_table(
            ["Evidence Type", "Quality Level", "Notes"],
            evidence_rows,
            title="Evidence Quality Indicator",
            brand=brand,
        ))

        return flowables

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_dosage_table(self, content, all_content):
        rows = []
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_low = [h.lower() for h in tbl.get("headers", [])]
                if any(k in " ".join(headers_low) for k in ("dosage", "dose", "mg", "mcg", "route")):
                    for row in tbl.get("rows", [])[:8]:
                        padded = (list(row) + ["", "", "", ""])[:4]
                        rows.append(padded)
        if not rows:
            # Scan for inline dosage patterns: "10 mg", "500 mcg", "1–2 tablets"
            dose_pat = re.compile(
                r'([A-Za-z][a-zA-Z\s]{2,30})\s+(?:at\s+)?(\d+(?:\.\d+)?\s*(?:mg|mcg|g|mL|units?|IU))',
                re.IGNORECASE,
            )
            seen = set()
            for m in dose_pat.finditer(all_content):
                drug = m.group(1).strip()
                dose = m.group(2).strip()
                key = drug.lower()
                if key not in seen and len(drug) < 50:
                    rows.append([drug, dose, "—", ""])
                    seen.add(key)
        return rows

    def _extract_interactions(self, content, all_content):
        rows = []
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_low = [h.lower() for h in tbl.get("headers", [])]
                if any(k in " ".join(headers_low) for k in ("interaction", "combination", "contraindicated")):
                    for row in tbl.get("rows", [])[:8]:
                        padded = (list(row) + ["", "", "", ""])[:4]
                        rows.append(padded)
        if not rows:
            inter_pat = re.compile(
                r'([A-Za-z][a-zA-Z]{2,20})\s+(?:and|with|plus|\+)\s+([A-Za-z][a-zA-Z]{2,20})'
                r'(?:[^\.\n]{0,60}(?:interact|contraindicated|avoid|incompatible))?',
                re.IGNORECASE,
            )
            seen = set()
            for m in inter_pat.finditer(all_content):
                a, b = m.group(1).strip(), m.group(2).strip()
                key = tuple(sorted([a.lower(), b.lower()]))
                if key not in seen:
                    rows.append([a, b, "See source", "—"])
                    seen.add(key)
        return rows

    def _extract_contraindications(self, all_content):
        items = []
        seen = set()
        # Explicit pattern blocks
        contra_pat = re.compile(
            r'(?:^|\n)\s*(?:CONTRAINDICATION[S]?|contraindicated\s+in|do\s+not\s+use)'
            r'[:\s]+([^\n]{10,200})',
            re.IGNORECASE | re.MULTILINE,
        )
        for m in contra_pat.finditer(all_content):
            txt = m.group(1).strip()
            key = txt[:40].lower()
            if key not in seen:
                items.append(txt)
                seen.add(key)
        # WARNING / CAUTION patterns as fallback
        warn_pat = re.compile(
            r'(?:^|\n)\s*(?:WARNING|CAUTION)[:\s]+([^\n]{10,200})',
            re.IGNORECASE | re.MULTILINE,
        )
        for m in warn_pat.finditer(all_content):
            txt = m.group(1).strip()
            key = txt[:40].lower()
            if key not in seen:
                items.append(txt)
                seen.add(key)
        return items

    def _extract_evidence(self, all_content):
        found_evidence = []
        for pat, label, quality in _EVIDENCE_KEYWORDS:
            m = re.search(pat, all_content, re.IGNORECASE)
            if m:
                start = max(0, m.start() - 40)
                context = all_content[start:m.start() + 60].replace("\n", " ").strip()[:60]
                found_evidence.append([label, quality, context or "Referenced in source"])
        if not found_evidence:
            found_evidence = [
                ["Primary research",  "Variable", "See source papers"],
                ["Review articles",   "—",        "Check numbered docs"],
                ["Clinical guidelines", "—",      "Check numbered docs"],
            ]
        return found_evidence

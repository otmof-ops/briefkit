"""
briefkit.variants.engineering — Mechanical / structural engineering variant.

Adds: safety warnings callout, specifications quick-reference table,
standards reference table.
"""

from __future__ import annotations

import re

from reportlab.platypus import PageBreak, Spacer

from briefkit.styles import _safe_para, build_styles
from briefkit.elements.tables import build_data_table
from briefkit.elements.callout import build_callout_box
from briefkit.variants import DocSetVariant, _register, collect_text

from reportlab.lib.units import mm

# Regex for engineering unit values
_UNIT_PAT = re.compile(
    r'\b\d+(?:\.\d+)?\s*(?:kPa|PSI|psi|Nm|ft.?lb|mm|bar|°C|°F|MPa|kN|rpm|kW|W|V|A|Hz|kg|lb|N)\b',
    re.IGNORECASE,
)

# Standards citation pattern
_STD_PAT = re.compile(
    r'\b(AS/?NZS\s+\d[\d.\-:]+|ISO\s+\d[\d.\-:]+|IEC\s+\d[\d.\-:]+|'
    r'ANSI\s+\w[\w.\-]+|OSHA\s+\d[\d.\-]+|EN\s+\d[\d.\-:]+|'
    r'ASTM\s+[A-Z]\d+(?:-\d+)?|API\s+\d+(?:[A-Z])?|NFPA\s+\d+)',
    re.IGNORECASE,
)

# Safety warning pattern
_SAFETY_PAT = re.compile(
    r'(?:^|\n)\s*(?:⚠️|WARNING|CAUTION|DANGER|Safety:)\s*([^\n]{10,200})',
    re.IGNORECASE | re.MULTILINE,
)


@_register
class EngineeringVariant(DocSetVariant):
    """Mechanical / structural engineering domain variant."""

    name = "engineering"
    auto_detect_keywords = [
        "tolerance", "specification", "PSI", "torque",
        "assembly", "calibration", "load",
    ]

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        all_content = collect_text(content)

        flowables.append(PageBreak())
        flowables.append(_safe_para("Engineering Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Safety warnings ---
        flowables.append(_safe_para("Safety Warnings Summary", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        found_warnings = []
        seen_warnings = set()
        for m in _SAFETY_PAT.finditer(all_content):
            txt = m.group(1).strip()
            key = txt[:40].lower()
            if key not in seen_warnings:
                found_warnings.append(txt)
                seen_warnings.add(key)

        if found_warnings:
            warn_text = "\n".join(f"- {w[:150]}" for w in found_warnings[:10])
            flowables.append(build_callout_box(warn_text, "warning", brand))
        else:
            flowables.append(_safe_para(
                "No structured safety warnings found — always consult source documentation "
                "and relevant standards before performing engineering work.",
                s_body,
            ))

        # --- Specifications quick-reference ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Specifications Quick-Reference", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        spec_rows = []
        seen_specs = set()
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                rows = tbl.get("rows", [])
                for row in rows[:10]:
                    row_str = " ".join(str(c) for c in row)
                    if _UNIT_PAT.search(row_str):
                        key = str(row[0])[:30].lower() if row else ""
                        if key and key not in seen_specs:
                            padded = (list(row) + ["", ""])[:3]
                            spec_rows.append(padded)
                            seen_specs.add(key)

        if spec_rows:
            flowables.extend(build_data_table(
                ["Parameter", "Value", "Notes"],
                spec_rows[:15],
                title="Engineering Specifications",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Structured specifications not found — see numbered documents.", s_body
            ))

        # --- Standards reference ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Standards Reference", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        found_stds = []
        seen_stds = set()
        for m in _STD_PAT.finditer(all_content):
            std_name = m.group(1).strip()
            key = std_name.lower()
            if key not in seen_stds:
                found_stds.append([std_name, "Referenced", ""])
                seen_stds.add(key)

        if found_stds:
            flowables.extend(build_data_table(
                ["Standard", "Status", "Notes"],
                found_stds[:15],
                title="Standards Referenced",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "No standards citations found — see source documents.", s_body
            ))

        return flowables

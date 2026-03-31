"""
briefkit.variants.finance — Finance and investment variant.

Adds: key metrics dashboard table, risk summary table, compliance notes.
"""

from __future__ import annotations

import re

from reportlab.platypus import PageBreak, Spacer

from briefkit.styles import _safe_para, build_styles
from briefkit.elements.tables import build_data_table
from briefkit.elements.callout import build_callout_box
from briefkit.variants import DocSetVariant, _register, collect_text

from reportlab.lib.units import mm

_FINANCE_DISCLAIMER = (
    "FINANCIAL INFORMATION — This document is for informational and educational "
    "purposes only. Nothing herein constitutes financial, investment, or legal advice. "
    "Past performance is not indicative of future results. Consult a qualified financial "
    "professional before making any investment decisions."
)

# Financial metric patterns: label → regex
_METRIC_PATTERNS = {
    "Revenue":          r'revenue[:\s]+([^\n,;]{3,40})',
    "EBITDA":           r'EBITDA[:\s]+([^\n,;]{3,30})',
    "Net Income":       r'net\s+income[:\s]+([^\n,;]{3,30})',
    "Gross Margin":     r'gross\s+margin[:\s]+([^\n,;]{3,30})',
    "Operating Margin": r'operating\s+margin[:\s]+([^\n,;]{3,30})',
    "EPS":              r'(?:earnings\s+per\s+share|EPS)[:\s]+([^\n,;]{3,30})',
    "P/E Ratio":        r'P/?E\s+ratio[:\s]+([^\n,;]{3,30})',
    "Market Cap":       r'market\s+cap(?:italiz(?:ation)?)?[:\s]+([^\n,;]{3,40})',
    "Total Assets":     r'total\s+assets[:\s]+([^\n,;]{3,40})',
    "Total Liabilities": r'total\s+liabilities[:\s]+([^\n,;]{3,40})',
    "Debt/Equity":      r'debt.to.equity[:\s]+([^\n,;]{3,30})',
    "ROE":              r'return\s+on\s+equity|ROE[:\s]+([^\n,;]{3,30})',
    "ROA":              r'return\s+on\s+assets|ROA[:\s]+([^\n,;]{3,30})',
}

_RISK_FACTORS = [
    (r'\bmarket\s+risk\b',      "Market Risk"),
    (r'\bcredit\s+risk\b',      "Credit Risk"),
    (r'\bliquidity\s+risk\b',   "Liquidity Risk"),
    (r'\boperational\s+risk\b', "Operational Risk"),
    (r'\bcurrency\s+risk\b|\bFX\s+risk\b', "Currency / FX Risk"),
    (r'\binterest\s+rate\s+risk\b', "Interest Rate Risk"),
    (r'\bregulatory\s+risk\b',  "Regulatory Risk"),
    (r'\bcounterparty\s+risk\b', "Counterparty Risk"),
    (r'\bconcentration\s+risk\b', "Concentration Risk"),
    (r'\bsystemic\s+risk\b',    "Systemic Risk"),
    (r'\bgeopolitical\s+risk\b', "Geopolitical Risk"),
    (r'\breputational\s+risk\b', "Reputational Risk"),
]

_COMPLIANCE_FRAMEWORKS = [
    ("SOX",      r'\bSarbanes.Oxley\b|\bSOX\b'),
    ("Basel III", r'\bBasel\s+III\b|\bBasel\s+3\b'),
    ("MiFID",    r'\bMiFID\b'),
    ("GDPR",     r'\bGDPR\b'),
    ("AML",      r'\banti.money\s+laundering\b|\bAML\b'),
    ("KYC",      r'\bknow\s+your\s+customer\b|\bKYC\b'),
    ("IFRS",     r'\bIFRS\b'),
    ("GAAP",     r'\bGAAP\b'),
    ("APRA",     r'\bAPRA\b'),
    ("ASIC",     r'\bASIC\b'),
    ("SEC",      r'\bSEC\b'),
    ("FCA",      r'\bFCA\b'),
]


@_register
class FinanceVariant(DocSetVariant):
    """Finance and investment domain variant."""

    name = "finance"
    auto_detect_keywords = [
        "revenue", "EBITDA", "portfolio", "risk",
        "compliance", "asset", "liability",
    ]

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        all_content = collect_text(content)

        # Prepend financial disclaimer
        flowables.insert(0, build_callout_box(_FINANCE_DISCLAIMER, "warning", brand))

        flowables.append(PageBreak())
        flowables.append(_safe_para("Finance Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Key metrics dashboard ---
        flowables.append(_safe_para("Key Financial Metrics", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        metric_rows = self._extract_metrics(content, all_content)
        if metric_rows:
            flowables.extend(build_data_table(
                ["Metric", "Value", "Period / Notes"],
                metric_rows[:12],
                title="Financial Metrics Dashboard",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Financial metrics not found in structured form — see numbered documents.",
                s_body,
            ))

        # --- Risk table ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Risk Summary", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        risk_rows = self._extract_risks(content, all_content)
        if risk_rows:
            flowables.extend(build_data_table(
                ["Risk Category", "Status", "Mitigation / Notes"],
                risk_rows[:12],
                title="Risk Register",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "No structured risk data found — see source documents.", s_body
            ))

        # --- Compliance notes ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Compliance Frameworks", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        compliance_rows = []
        for framework, pat in _COMPLIANCE_FRAMEWORKS:
            if re.search(pat, all_content, re.IGNORECASE):
                compliance_rows.append([framework, "Referenced", ""])

        if compliance_rows:
            flowables.extend(build_data_table(
                ["Framework", "Status", "Notes"],
                compliance_rows,
                title="Compliance Frameworks Referenced",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "No compliance frameworks identified — see source documents.", s_body
            ))

        return flowables

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_metrics(self, content, all_content):
        rows = []
        seen = set()

        # Check structured tables
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_low = [h.lower() for h in tbl.get("headers", [])]
                if any(k in " ".join(headers_low) for k in (
                    "revenue", "ebitda", "metric", "financial", "income",
                    "asset", "liability", "earnings",
                )):
                    for row in tbl.get("rows", [])[:8]:
                        padded = (list(row) + ["", "", ""])[:3]
                        key = str(padded[0]).lower()
                        if key not in seen:
                            rows.append(padded)
                            seen.add(key)

        if rows:
            return rows

        # Extract from prose
        for label, pattern in _METRIC_PATTERNS.items():
            if label.lower() in seen:
                continue
            m = re.search(pattern, all_content, re.IGNORECASE)
            if m:
                try:
                    value = m.group(1).strip()[:40]
                except IndexError:
                    value = m.group(0).strip()[:40]
                rows.append([label, value, ""])
                seen.add(label.lower())

        return rows

    def _extract_risks(self, content, all_content):
        rows = []
        seen = set()

        # Check structured risk tables
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_low = [h.lower() for h in tbl.get("headers", [])]
                if any(k in " ".join(headers_low) for k in ("risk", "likelihood", "impact", "mitigation")):
                    for row in tbl.get("rows", [])[:10]:
                        padded = (list(row) + ["", "", ""])[:3]
                        key = str(padded[0]).lower()
                        if key not in seen:
                            rows.append(padded)
                            seen.add(key)

        if rows:
            return rows

        # Detect risk factor keywords
        for pat, label in _RISK_FACTORS:
            if re.search(pat, all_content, re.IGNORECASE) and label not in seen:
                rows.append([label, "Identified", ""])
                seen.add(label)

        return rows

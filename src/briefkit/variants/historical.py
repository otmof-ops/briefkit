"""
briefkit.variants.historical — Historical / archaeological variant.

Adds: event timeline, primary source reference table, key figures table,
period/dynasty overview.
"""

from __future__ import annotations

import re
import sys

from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Spacer

from briefkit.elements.tables import build_data_table
from briefkit.styles import _safe_para
from briefkit.variants import DocSetVariant, _register, collect_text

# Title patterns that indicate historical figures of authority
_RULER_TITLE_PAT = re.compile(
    r'\b(?:Emperor|King|Queen|Sultan|Caliph|Pharaoh|Tsar|Khan|Shogun|Caesar|'
    r'Pope|Prince|Duke|Empress|Regent|Chancellor|Vizier)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    re.IGNORECASE,
)

_REIGN_FULL_PAT = re.compile(
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\(?\s*(\d{3,4})\s*[–\-—]+\s*(\d{3,4})\s*\)?'
)

# Date / event extraction
_RANGE_PAT = re.compile(
    r'(\d{1,4})\s*(?:BC|BCE|AD|CE)?\s*[–\-—]+\s*(\d{1,4})\s*(?:BC|BCE|AD|CE)?'
)
_EVENT_PAT = re.compile(
    r'\b(founded|established|fell|collapsed|dissolved|conquered|unified|'
    r'invaded|captured|signed|declared|abolished|annexed)\b[^.]{0,30}?\b(\d{3,4})\b',
    re.IGNORECASE,
)
_REIGN_PAT = re.compile(r'ruled?\s+(?:from\s+)?(\d{3,4})\s+to\s+(\d{3,4})', re.IGNORECASE)

# Primary source type patterns
_SOURCE_PATTERNS = [
    (r'\bchronicle\b',        "Chronicle"),
    (r'\bannals?\b',          "Annals"),
    (r'\binscription\b',      "Inscription"),
    (r'\bpapyrus\b|\bpapyri\b', "Papyrus"),
    (r'\bmanuscript\b',       "Manuscript"),
    (r'\bcoin(?:age)?\b',     "Numismatic Evidence"),
    (r'\barchaeological\s+(?:site|evidence|record)\b', "Archaeological Record"),
    (r'\btablet\b',           "Clay Tablet"),
    (r'\bstele\b|\bstela\b',  "Stele"),
    (r'\btomb\b|\bburial\b',  "Funerary Evidence"),
    (r'\bcensus\b',           "Census Record"),
    (r'\btreaty\b',           "Treaty / Diplomatic Document"),
    (r'\bcodex\b',            "Codex"),
    (r'\bsaga\b',             "Saga"),
]


@_register
class HistoricalVariant(DocSetVariant):
    """Historical / archaeological domain variant."""

    name = "historical"
    auto_detect_keywords = [
        "century", "dynasty", "empire", "reign",
        "archaeological", "medieval", "ancient",
    ]

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        all_content = collect_text(content)

        flowables.append(PageBreak())
        flowables.append(_safe_para("Historical / Empire Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Timeline ---
        flowables.append(_safe_para("Event Timeline", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        timeline_rows = self._extract_timeline_rows(all_content)
        if timeline_rows:
            flowables.extend(build_data_table(
                ["Year / Period", "Event"],
                timeline_rows[:12],
                title="Historical Timeline",
                brand=brand,
            ))
            # Also render a visual timeline drawing if enough events
            events = self._extract_timeline_events(all_content)
            if len(events) >= 2:
                chart = _build_timeline_drawing(events[:8])
                if chart is not None:
                    flowables.append(chart)
        else:
            flowables.append(_safe_para(
                "No structured timeline data found — see source documents.", s_body
            ))

        # --- Key rulers / figures ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Key Rulers and Figures", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        ruler_rows = self._extract_rulers(all_content)
        if ruler_rows:
            flowables.extend(build_data_table(
                ["Name / Title", "Reign / Period", "Key Achievement"],
                ruler_rows[:10],
                title="Rulers and Key Figures",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Key figures not found in structured form — see source documents.", s_body
            ))

        # --- Primary source table ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Primary Source Types", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        source_rows = []
        for pat, label in _SOURCE_PATTERNS:
            if re.search(pat, all_content, re.IGNORECASE):
                source_rows.append([label, "Referenced", ""])

        if source_rows:
            flowables.extend(build_data_table(
                ["Source Type", "Status", "Notes"],
                source_rows,
                title="Primary Source Evidence",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "No primary source types identified — see source documents.", s_body
            ))

        return flowables

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_timeline_events(self, all_content):
        """Return sorted list of (year_int, label) for the drawing."""
        timeline_events = []

        for m in _RANGE_PAT.finditer(all_content):
            try:
                y1, y2 = int(m.group(1)), int(m.group(2))
                if y1 < 3000 and y2 < 3000:
                    timeline_events.extend([(y1, "Start"), (y2, "End")])
            except ValueError:
                pass

        for m in _EVENT_PAT.finditer(all_content):
            try:
                y = int(m.group(2))
                if y < 3000:
                    timeline_events.append((y, m.group(1).title()))
            except ValueError:
                pass

        for m in _REIGN_PAT.finditer(all_content):
            try:
                timeline_events.extend([
                    (int(m.group(1)), "Reign start"),
                    (int(m.group(2)), "Reign end"),
                ])
            except ValueError:
                pass

        if len(timeline_events) < 2:
            year_matches = re.findall(r'\b([1-9][0-9]{2,3})\b', all_content)
            years = sorted(set(int(y) for y in year_matches if int(y) < 3000))[:8]
            timeline_events = [(y, "Event") for y in years]

        unique = sorted({(y, d) for y, d in timeline_events}, key=lambda x: x[0])
        return unique[:8]

    def _extract_timeline_rows(self, all_content):
        """Return rows for a table: [[period_str, event_label], ...]"""
        rows = []
        seen = set()

        # Range pattern with context
        range_ctx = re.compile(
            r'(\d{1,4})\s*(?:BC|BCE|AD|CE)?\s*[–\-—]+\s*(\d{1,4})\s*(?:BC|BCE|AD|CE)?'
            r'[:\s]*([A-Za-z][^.\n]{3,60})?'
        )
        for m in range_ctx.finditer(all_content):
            y1, y2 = m.group(1), m.group(2)
            label = (m.group(3) or "").strip()[:60]
            period = f"{y1}–{y2}"
            if period not in seen:
                rows.append([period, label or "Period"])
                seen.add(period)

        # Single year + event verb
        for m in _EVENT_PAT.finditer(all_content):
            year = m.group(2)
            verb = m.group(1).title()
            key = year + verb
            if key not in seen:
                # Grab a little context
                start = max(0, m.start() - 5)
                ctx = all_content[start:m.end() + 60].replace("\n", " ").strip()[:80]
                rows.append([year, ctx or verb])
                seen.add(key)

        return rows

    def _extract_rulers(self, all_content):
        ruler_rows = []
        seen = set()

        for m in _RULER_TITLE_PAT.finditer(all_content):
            name = m.group(1).strip()
            if name not in seen:
                ruler_rows.append([name, "—", ""])
                seen.add(name)

        for m in _REIGN_FULL_PAT.finditer(all_content):
            name = m.group(1).strip()
            if name not in seen and len(name) < 40:
                ruler_rows.append([name, f"{m.group(2)}–{m.group(3)}", ""])
                seen.add(name)

        return ruler_rows


def _build_timeline_drawing(events):
    """Attempt to build a visual horizontal timeline; returns None on failure."""
    try:
        from reportlab.graphics.shapes import Drawing, Line, String
        from reportlab.lib.colors import HexColor

        from briefkit.styles import CONTENT_WIDTH

        chart_width  = float(CONTENT_WIDTH)
        chart_height = 40 * mm
        axis_y       = chart_height * 0.55
        tick_h       = 5 * mm
        n            = len(events)
        if n < 2:
            return None

        d = Drawing(chart_width, chart_height)

        # Axis line
        d.add(Line(10, axis_y, chart_width - 10, axis_y,
                   strokeColor=HexColor("#1B2A4A"), strokeWidth=1.5))

        for i, (year, desc) in enumerate(events):
            x = 10 + i * (chart_width - 20) / max(n - 1, 1)
            # Tick
            d.add(Line(x, axis_y - tick_h / 2, x, axis_y + tick_h / 2,
                       strokeColor=HexColor("#2E86AB"), strokeWidth=1.2))
            # Year label (alternating above/below)
            y_offset = tick_h + 2 if i % 2 == 0 else -(tick_h + 10)
            d.add(String(x, axis_y + y_offset, str(year),
                         fontName="Helvetica-Bold", fontSize=7,
                         fillColor=HexColor("#1B2A4A"), textAnchor="middle"))
            d.add(String(x, axis_y + y_offset - 9, str(desc)[:14],
                         fontName="Helvetica", fontSize=6.5,
                         fillColor=HexColor("#666666"), textAnchor="middle"))
        return d
    except Exception as exc:
        print(f"Warning: Variant section error: {exc}", file=sys.stderr)
        return None

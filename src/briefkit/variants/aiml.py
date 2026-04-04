"""
briefkit.variants.aiml — AI / ML variant.

Adds: hyperparameter table, benchmark bar chart, model architecture section.
"""

from __future__ import annotations

import re
import sys

from reportlab.platypus import PageBreak, Spacer

from briefkit.elements.tables import build_data_table
from briefkit.styles import _safe_para, build_styles
from briefkit.variants import DocSetVariant, _register

try:
    from reportlab.graphics.shapes import Drawing, Line, Rect, String  # noqa: F401
    from reportlab.lib.colors import HexColor, white  # noqa: F401
    from reportlab.lib.units import mm  # noqa: F401

    from briefkit.styles import CONTENT_WIDTH  # noqa: F401
    _HAS_DRAWING = True
except ImportError:
    _HAS_DRAWING = False


@_register
class AIMLVariant(DocSetVariant):
    """AI / ML domain variant."""

    name = "aiml"
    auto_detect_keywords = [
        "neural", "transformer", "training", "epoch", "loss",
        "gradient", "attention", "embedding",
    ]

    # Taxonomy of known hyperparameter / configuration terms
    _AI_TAXONOMY = {
        "learning rate", "batch size", "epochs", "layers", "heads",
        "hidden size", "dropout", "optimizer", "weight decay", "momentum",
        "sequence length", "vocabulary", "embedding", "attention", "ffn",
        "temperature", "top-k", "top-p", "beam", "context",
        "learning_rate", "batch_size", "hidden_dim", "num_layers",
        "num_heads", "max_length", "vocab_size",
    }

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        flowables.append(PageBreak())
        flowables.append(_safe_para("AI / ML Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Hyperparameter table ---
        flowables.append(_safe_para("Model Configuration and Hyperparameters", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        hp_rows = self._extract_hyperparameters(content)

        if hp_rows:
            flowables.extend(build_data_table(
                ["Parameter", "Value", "Notes"],
                [r + [""] * max(0, 3 - len(r)) for r in hp_rows[:12]],
                title="Hyperparameter Reference",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Hyperparameter data not structured in source documents. "
                "See numbered deep-dive files for model configuration details.",
                s_body,
            ))

        # --- Benchmark bar chart ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Benchmark Results", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        bench_data, bench_axis_label = self._extract_benchmarks(content)

        if bench_data:
            flowables.extend(
                _build_bar_chart(bench_data[:10], f"Benchmark Comparison — {bench_axis_label}", brand)
            )
        else:
            flowables.append(_safe_para("No structured benchmark data found.", s_body))

        # --- Model architecture section ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Model Architecture", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        subsystem_names = [s["name"][:24] for s in content.get("subsystems", [])[:8]]
        title_name = content.get("title", "Model")[:24]

        if subsystem_names:
            arch_rows = [[comp, "Component", ""] for comp in subsystem_names]
            flowables.extend(build_data_table(
                ["Component", "Type", "Notes"],
                arch_rows,
                title=f"Architecture Components — {title_name}",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Architecture components — see numbered deep-dive documents.",
                s_body,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_hyperparameters(self, content):
        hp_rows = []
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers = tbl.get("headers", [])
                headers_low = [h.lower() for h in headers]
                if any(h in ("parameter", "hyperparameter", "config", "setting",
                             "configuration", "model", "architecture")
                       for h in headers_low):
                    hp_rows.extend(tbl.get("rows", [])[:6])
                    break
                elif len(headers) in (2, 3):
                    rows = tbl.get("rows", [])
                    tech_rows = [
                        r for r in rows
                        if r and r[0].lower().strip() in self._AI_TAXONOMY
                    ]
                    if len(tech_rows) >= 2:
                        hp_rows.extend(tech_rows[:6])
                        break
            if hp_rows:
                break
        return hp_rows

    def _extract_benchmarks(self, content):
        bench_data = []
        bench_axis_label = "Score"
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers = tbl.get("headers", [])
                rows = tbl.get("rows", [])
                if not headers or not rows:
                    continue
                best_col_idx = None
                best_col_count = 0
                best_col_header = ""
                for col_i in range(1, len(headers)):
                    parseable = 0
                    for row in rows:
                        if col_i < len(row):
                            try:
                                float(re.sub(r'[^\d.]', '', str(row[col_i])))
                                parseable += 1
                            except (ValueError, TypeError):
                                pass
                    if parseable > best_col_count:
                        best_col_count = parseable
                        best_col_idx = col_i
                        best_col_header = headers[col_i] if col_i < len(headers) else "Score"
                if best_col_idx is not None and best_col_count >= 2:
                    for row in rows:
                        if len(row) > best_col_idx:
                            try:
                                val = float(re.sub(r'[^\d.]', '', str(row[best_col_idx])))
                                bench_data.append((str(row[0])[:25], val))
                                bench_axis_label = best_col_header
                            except (ValueError, TypeError):
                                pass
                if bench_data:
                    break
        return bench_data, bench_axis_label


def _build_bar_chart(data, title="", brand=None):
    """Horizontal bar chart as a ReportLab Drawing, or fallback table."""
    from reportlab.lib.units import mm

    from briefkit.styles import CONTENT_WIDTH, _get_brand, _hex

    b = _get_brand(brand)
    styles = build_styles(b)
    s_caption = styles["STYLE_CAPTION"]

    flowables = []
    if title:
        flowables.append(_safe_para(title, s_caption))

    if not data:
        return flowables

    try:
        from reportlab.graphics.shapes import Drawing, Rect, String

        chart_width  = float(CONTENT_WIDTH)
        bar_height   = 10 * mm
        gap          = 4 * mm
        label_width  = 50 * mm
        value_width  = chart_width - label_width - 10 * mm
        chart_height = len(data) * (bar_height + gap) + 10 * mm

        d = Drawing(chart_width, chart_height)
        bg_grey = styles["_bg_grey"]
        bg = Rect(0, 0, chart_width, chart_height, fillColor=bg_grey, strokeColor=None)
        d.add(bg)

        _hex(b, "primary")
        secondary = _hex(b, "secondary")
        body_text = _hex(b, "body_text")

        max_val = max((v for _, v in data if isinstance(v, (int, float))), default=1)
        if max_val == 0:
            max_val = 1

        for i, (label, value) in enumerate(reversed(data)):
            y = gap + i * (bar_height + gap)
            try:
                numeric_val = float(value)
            except (ValueError, TypeError):
                numeric_val = 0.0
            bar_w = (numeric_val / max_val) * value_width

            bar = Rect(label_width, y, bar_w, bar_height, fillColor=secondary, strokeColor=None)
            d.add(bar)

            lbl = String(
                label_width - 4, y + bar_height * 0.35,
                str(label)[:28],
                fontName="Helvetica", fontSize=8,
                fillColor=body_text, textAnchor="end",
            )
            d.add(lbl)

            val_lbl = String(
                label_width + bar_w + 4, y + bar_height * 0.35,
                str(value),
                fontName="Helvetica-Bold", fontSize=8,
                fillColor=secondary, textAnchor="start",
            )
            d.add(val_lbl)

        flowables.append(d)
    except Exception as exc:
        print(f"Warning: Variant section error: {exc}", file=sys.stderr)
        # Fallback: plain data table
        rows = [[label, str(value)] for label, value in data]
        flowables.extend(build_data_table(["Model / System", "Score"], rows, brand=brand))

    return flowables

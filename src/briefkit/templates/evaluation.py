"""
briefkit.templates.evaluation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Evaluation report template — criteria-based scoring with rubric tables.

Build order:
  Cover → Summary (overall score) → Criteria Rubric Table →
  Detailed Findings (per criterion) → Summary Statistics →
  Recommendations → Back Cover

Design norms (JotForm evaluation/survey patterns):
  - Cover page with "EVALUATION REPORT" subtitle
  - Summary section with overall score/rating
  - Criteria table rendered as evaluation rubric with colored scoring
  - Detailed findings per criterion (each subsystem = one evaluation criterion)
  - Summary statistics (total score, average, pass/fail)
  - Recommendations section from blockquotes/insights
  - Back cover

Suitable for: evaluation forms, survey results, audit assessments,
compliance checks, performance reviews, grading rubrics.
"""

from __future__ import annotations

import re

from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from briefkit.extractor import parse_markdown
from briefkit.generator import (
    BaseBriefingTemplate,
    build_callout_box,
    build_cover_page,
)
from briefkit.styles import (
    _hex,
    _ps,
    _safe_para,
    _safe_text,
    build_styles,
)

# ---------------------------------------------------------------------------
# Score extraction helpers
# ---------------------------------------------------------------------------

_SCORE_RE = re.compile(
    r"(?:score|rating|grade|result|mark)[:\s]*(\d+(?:\.\d+)?)\s*(?:/\s*(\d+))?",
    re.IGNORECASE,
)

_PASS_FAIL_RE = re.compile(
    r"\b(pass|fail|met|not met|compliant|non-compliant|yes|no)\b",
    re.IGNORECASE,
)


def _extract_score(text: str) -> tuple[float | None, float | None]:
    """Extract a numeric score and optional maximum from text."""
    m = _SCORE_RE.search(text)
    if m:
        score = float(m.group(1))
        maximum = float(m.group(2)) if m.group(2) else None
        return score, maximum
    return None, None


def _score_color(score: float, maximum: float, brand: dict) -> HexColor:
    """Return green/yellow/red HexColor based on score percentage."""
    pct = score / maximum if maximum else 0
    if pct >= 0.75:
        return HexColor(brand.get("success", "#00b894"))
    elif pct >= 0.50:
        return HexColor(brand.get("warning", "#fdcb6e"))
    return HexColor(brand.get("danger", "#d63031"))


def _pass_fail_color(text: str, brand: dict) -> HexColor | None:
    """Return a color if text contains pass/fail language."""
    m = _PASS_FAIL_RE.search(text)
    if not m:
        return None
    word = m.group(1).lower()
    if word in {"pass", "met", "compliant", "yes"}:
        return HexColor(brand.get("success", "#00b894"))
    return HexColor(brand.get("danger", "#d63031"))


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------

class EvaluationTemplate(BaseBriefingTemplate):
    """
    Evaluation report template.

    Treats each subsystem as an evaluation criterion.  Extracts numeric
    scores from content where possible and renders a colored rubric table
    followed by detailed per-criterion findings and recommendations.
    """

    # ------------------------------------------------------------------
    # build_body — evaluation-specific sections
    # ------------------------------------------------------------------

    def build_body(self, content: dict) -> list:
        """
        Build evaluation body:
          Summary → Rubric table → Detailed findings → Stats → Recommendations
        """
        flowables: list = []
        subsystems = content.get("subsystems", [])

        # -- Evaluate each criterion --
        criteria = self._evaluate_criteria(subsystems)

        # 1. Summary section
        flowables.extend(self._build_summary(content, criteria))
        flowables.append(Spacer(1, 6 * mm))

        # 2. Criteria rubric table
        if criteria:
            flowables.extend(self._build_rubric_table(criteria))
            flowables.append(PageBreak())

        # 3. Detailed findings
        flowables.extend(self._build_detailed_findings(subsystems, criteria))
        flowables.append(PageBreak())

        # 4. Summary statistics
        flowables.extend(self._build_summary_stats(criteria))
        flowables.append(Spacer(1, 6 * mm))

        # 5. Recommendations
        flowables.extend(self._build_recommendations(subsystems, content))

        return flowables

    # ------------------------------------------------------------------
    # Criteria evaluation
    # ------------------------------------------------------------------

    def _evaluate_criteria(self, subsystems: list[dict]) -> list[dict]:
        """Build a list of criterion dicts from subsystems."""
        criteria: list[dict] = []
        for sub in subsystems:
            text = sub.get("content", "")
            blocks = sub.get("blocks") or parse_markdown(text)
            full_text = " ".join(
                b.get("text", "") for b in blocks if b.get("type") == "paragraph"
            )

            score, maximum = _extract_score(full_text)
            if score is None:
                # Try table cells
                for tbl in sub.get("tables", []):
                    for row in tbl.get("rows", []):
                        for cell in row:
                            score, maximum = _extract_score(str(cell or ""))
                            if score is not None:
                                break
                        if score is not None:
                            break
                    if score is not None:
                        break

            # Collect insights/blockquotes for recommendations
            insights = sub.get("insights", [])
            blockquotes = [
                b.get("text", "")
                for b in blocks
                if b.get("type") == "blockquote"
            ]

            criteria.append({
                "name": sub.get("name", "Unnamed Criterion"),
                "score": score,
                "maximum": maximum or 10.0,
                "insights": insights,
                "blockquotes": blockquotes,
                "full_text": full_text,
            })
        return criteria

    # ------------------------------------------------------------------
    # Summary section
    # ------------------------------------------------------------------

    def _build_summary(self, content: dict, criteria: list[dict]) -> list:
        """Build the overall summary with aggregate score."""
        flowables: list = []

        flowables.append(Paragraph("1. Evaluation Summary", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        overview = content.get("overview", "")
        if overview:
            for block in parse_markdown(overview[:2000])[:20]:
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
            flowables.append(Spacer(1, 3 * mm))

        # Aggregate score
        scored = [c for c in criteria if c["score"] is not None]
        if scored:
            total = sum(c["score"] for c in scored)
            max_total = sum(c["maximum"] for c in scored)
            avg = total / len(scored)
            pct = (total / max_total * 100) if max_total else 0

            summary_style = _ps(
                "EvalSummaryScore", brand=self.brand,
                fontSize=14, fontName="Helvetica-Bold",
                textColor=_hex(self.brand, "primary"),
                alignment=1, spaceAfter=6,
            )
            flowables.append(Paragraph(
                f"Overall Score: {total:.1f} / {max_total:.1f} ({pct:.0f}%)",
                summary_style,
            ))

            detail_style = _ps(
                "EvalSummaryDetail", brand=self.brand,
                fontSize=10, textColor=_hex(self.brand, "caption"),
                alignment=1, spaceAfter=4,
            )
            flowables.append(Paragraph(
                f"Criteria evaluated: {len(scored)} | Average per criterion: {avg:.1f}",
                detail_style,
            ))
        else:
            note_style = _ps(
                "EvalNote", brand=self.brand,
                fontSize=10, textColor=_hex(self.brand, "caption"),
                alignment=1, spaceAfter=4,
            )
            flowables.append(Paragraph(
                "No numeric scores were detected. See detailed findings below.",
                note_style,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Rubric table
    # ------------------------------------------------------------------

    def _build_rubric_table(self, criteria: list[dict]) -> list:
        """Build a colored rubric table from criteria."""
        flowables: list = []
        styles = build_styles(self.brand)
        primary = _hex(self.brand, "primary")
        rule_c = _hex(self.brand, "rule")

        flowables.append(Paragraph("2. Evaluation Rubric", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        headers = ["#", "Criterion", "Score", "Max", "Rating", "Status"]
        col_widths = [
            self.content_width * 0.06,
            self.content_width * 0.34,
            self.content_width * 0.12,
            self.content_width * 0.12,
            self.content_width * 0.18,
            self.content_width * 0.18,
        ]

        header_row = [
            _safe_para(
                f"<b>{_safe_text(h)}</b>",
                styles["STYLE_TABLE_HEADER"],
            )
            for h in headers
        ]
        table_data = [header_row]

        row_colors: list[tuple[int, HexColor | None]] = []
        for idx, c in enumerate(criteria, 1):
            score = c["score"]
            maximum = c["maximum"]

            score_str = f"{score:.1f}" if score is not None else "\u2014"
            max_str = f"{maximum:.1f}" if maximum else "\u2014"

            if score is not None and maximum:
                pct = score / maximum * 100
                rating_str = f"{pct:.0f}%"
                if pct >= 75:
                    status_str = "PASS"
                elif pct >= 50:
                    status_str = "MARGINAL"
                else:
                    status_str = "FAIL"
                color = _score_color(score, maximum, self.brand)
            else:
                rating_str = "\u2014"
                status_str = "N/A"
                color = None

            row_colors.append((idx, color))
            table_data.append([
                _safe_para(str(idx), styles["STYLE_TABLE_BODY"]),
                _safe_para(_safe_text(c["name"][:60]), styles["STYLE_TABLE_BODY"]),
                _safe_para(score_str, styles["STYLE_TABLE_BODY"]),
                _safe_para(max_str, styles["STYLE_TABLE_BODY"]),
                _safe_para(rating_str, styles["STYLE_TABLE_BODY"]),
                _safe_para(f"<b>{status_str}</b>", styles["STYLE_TABLE_BODY"]),
            ])

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        base_style = [
            ("BACKGROUND", (0, 0), (-1, 0), primary),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.4, rule_c),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f8f9fa")]),
        ]

        # Color the status column per row
        for row_idx, color in row_colors:
            if color is not None:
                base_style.append(("TEXTCOLOR", (5, row_idx), (5, row_idx), color))

        t.setStyle(TableStyle(base_style))
        flowables.append(t)
        flowables.append(Spacer(1, 4 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Detailed findings
    # ------------------------------------------------------------------

    def _build_detailed_findings(
        self, subsystems: list[dict], criteria: list[dict],
    ) -> list:
        """Build detailed per-criterion findings."""
        flowables: list = []

        flowables.append(Paragraph("3. Detailed Findings", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        flowables.append(Paragraph(
            "Each evaluation criterion is examined in detail below.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 4 * mm))

        for idx, (sub, crit) in enumerate(zip(subsystems, criteria), 1):
            section: list = []

            # Criterion heading
            score_tag = ""
            if crit["score"] is not None:
                pct = crit["score"] / crit["maximum"] * 100 if crit["maximum"] else 0
                score_tag = f" \u2014 {crit['score']:.1f}/{crit['maximum']:.1f} ({pct:.0f}%)"
            section.append(Paragraph(
                f"3.{idx} {_safe_text(crit['name'])}{score_tag}",
                self.styles["STYLE_H2"],
            ))
            section.append(Spacer(1, 2 * mm))

            # Score indicator bar
            if crit["score"] is not None and crit["maximum"]:
                color = _score_color(crit["score"], crit["maximum"], self.brand)
                bar_style = _ps(
                    f"EvalBar{idx}", brand=self.brand,
                    fontSize=9, fontName="Helvetica-Bold",
                    textColor=color,
                    spaceAfter=4,
                )
                pct = crit["score"] / crit["maximum"] * 100 if crit["maximum"] else 0
                if pct >= 75:
                    label = "PASS"
                elif pct >= 50:
                    label = "MARGINAL"
                else:
                    label = "FAIL"
                section.append(Paragraph(f"Rating: {label}", bar_style))
                section.append(Spacer(1, 2 * mm))

            # Findings text
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered = 0
            for block in blocks:
                if block.get("type") == "heading" and block.get("level", 1) <= 2:
                    continue
                for fl in self.render_blocks([block]):
                    section.append(fl)
                    rendered += 1
                if rendered >= 40:
                    break

            # Tables within the criterion
            for tbl in sub.get("tables", []):
                if tbl.get("headers") and tbl.get("rows"):
                    from briefkit.generator import build_data_table
                    section.extend(build_data_table(
                        tbl["headers"], tbl["rows"],
                        brand=self.brand,
                        content_width=self.content_width,
                    ))
                    section.append(Spacer(1, 2 * mm))

            # Recommendations from insights/blockquotes
            recs = crit["insights"] + crit["blockquotes"]
            if recs:
                rec_heading = _ps(
                    f"EvalRecHead{idx}", brand=self.brand,
                    fontSize=10, fontName="Helvetica-Bold",
                    textColor=_hex(self.brand, "secondary"),
                    spaceAfter=2, spaceBefore=4,
                )
                section.append(Paragraph("Recommendations:", rec_heading))
                rec_style = _ps(
                    f"EvalRecItem{idx}", brand=self.brand,
                    fontSize=9, textColor=_hex(self.brand, "body_text"),
                    leading=13, leftIndent=12,
                )
                for rec in recs[:5]:
                    section.append(_safe_para(f"\u2022 {rec[:300]}", rec_style))

            section.append(Spacer(1, 6 * mm))
            flowables.append(KeepTogether(section[:6]))
            flowables.extend(section[6:])

        return flowables

    # ------------------------------------------------------------------
    # Summary statistics
    # ------------------------------------------------------------------

    def _build_summary_stats(self, criteria: list[dict]) -> list:
        """Build aggregate statistics block."""
        flowables: list = []

        flowables.append(Paragraph("4. Summary Statistics", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        scored = [c for c in criteria if c["score"] is not None]
        total_criteria = len(criteria)

        stat_style = _ps(
            "EvalStat", brand=self.brand,
            fontSize=10, textColor=_hex(self.brand, "body_text"),
            leading=14, spaceAfter=2,
        )

        flowables.append(Paragraph(
            f"Total criteria evaluated: {total_criteria}", stat_style,
        ))

        if scored:
            total_score = sum(c["score"] for c in scored)
            max_score = sum(c["maximum"] for c in scored)
            avg_score = total_score / len(scored)
            pct = (total_score / max_score * 100) if max_score else 0

            pass_count = sum(
                1 for c in scored
                if c["maximum"] and (c["score"] / c["maximum"]) >= 0.75
            )
            fail_count = sum(
                1 for c in scored
                if c["maximum"] and (c["score"] / c["maximum"]) < 0.50
            )
            marginal_count = len(scored) - pass_count - fail_count

            flowables.append(Paragraph(
                f"Criteria with scores: {len(scored)}", stat_style,
            ))
            flowables.append(Paragraph(
                f"Total score: {total_score:.1f} / {max_score:.1f} ({pct:.0f}%)",
                stat_style,
            ))
            flowables.append(Paragraph(
                f"Average score per criterion: {avg_score:.1f}", stat_style,
            ))
            flowables.append(Spacer(1, 3 * mm))

            # Pass/fail summary table
            styles = build_styles(self.brand)
            summary_data = [
                [
                    _safe_para("<b>Status</b>", styles["STYLE_TABLE_HEADER"]),
                    _safe_para("<b>Count</b>", styles["STYLE_TABLE_HEADER"]),
                    _safe_para("<b>Percentage</b>", styles["STYLE_TABLE_HEADER"]),
                ],
                [
                    _safe_para("PASS", styles["STYLE_TABLE_BODY"]),
                    _safe_para(str(pass_count), styles["STYLE_TABLE_BODY"]),
                    _safe_para(
                        f"{pass_count / len(scored) * 100:.0f}%",
                        styles["STYLE_TABLE_BODY"],
                    ),
                ],
                [
                    _safe_para("MARGINAL", styles["STYLE_TABLE_BODY"]),
                    _safe_para(str(marginal_count), styles["STYLE_TABLE_BODY"]),
                    _safe_para(
                        f"{marginal_count / len(scored) * 100:.0f}%",
                        styles["STYLE_TABLE_BODY"],
                    ),
                ],
                [
                    _safe_para("FAIL", styles["STYLE_TABLE_BODY"]),
                    _safe_para(str(fail_count), styles["STYLE_TABLE_BODY"]),
                    _safe_para(
                        f"{fail_count / len(scored) * 100:.0f}%",
                        styles["STYLE_TABLE_BODY"],
                    ),
                ],
            ]
            col_w = self.content_width * 0.5
            t = Table(
                summary_data,
                colWidths=[col_w * 0.4, col_w * 0.3, col_w * 0.3],
                repeatRows=1,
            )
            primary = _hex(self.brand, "primary")
            rule_c = _hex(self.brand, "rule")
            success_c = _hex(self.brand, "success")
            warning_c = _hex(self.brand, "warning")
            danger_c = _hex(self.brand, "danger")
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), primary),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.4, rule_c),
                ("TEXTCOLOR", (0, 1), (0, 1), success_c),
                ("TEXTCOLOR", (0, 2), (0, 2), warning_c),
                ("TEXTCOLOR", (0, 3), (0, 3), danger_c),
            ]))
            flowables.append(t)
        else:
            flowables.append(Paragraph(
                "No numeric scores were available for statistical analysis.",
                stat_style,
            ))

        flowables.append(Spacer(1, 2 * mm))
        flowables.append(Paragraph(
            f"Generated: {self.date_str}", stat_style,
        ))

        return flowables

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def _build_recommendations(
        self, subsystems: list[dict], content: dict,
    ) -> list:
        """Aggregate recommendations from blockquotes and insights."""
        flowables: list = []

        flowables.append(Paragraph("5. Recommendations", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        all_recs: list[str] = []
        for sub in subsystems:
            all_recs.extend(sub.get("insights", []))
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            for block in blocks:
                if block.get("type") == "blockquote":
                    all_recs.append(block.get("text", ""))

        if all_recs:
            flowables.append(Paragraph(
                "The following recommendations are derived from the evaluation findings:",
                self.styles["STYLE_BODY"],
            ))
            flowables.append(Spacer(1, 3 * mm))
            for i, rec in enumerate(all_recs[:15], 1):
                flowables.append(build_callout_box(
                    f"{i}. {rec[:400]}",
                    "insight",
                    brand=self.brand,
                    content_width=self.content_width,
                ))
                flowables.append(Spacer(1, 2 * mm))
        else:
            flowables.append(Paragraph(
                "No specific recommendations were extracted from the source material. "
                "Review the detailed findings above for qualitative guidance.",
                self.styles["STYLE_BODY"],
            ))

        return flowables

    # ------------------------------------------------------------------
    # Override build_story for evaluation structure
    # ------------------------------------------------------------------

    def build_story(self, content: dict) -> list:
        """
        Assemble the evaluation report:
          Cover → Body (summary, rubric, findings, stats, recs) → Back cover
        """
        story: list = []
        title = content.get("title", self.target_path.name.replace("-", " ").title())

        # Cover page with "EVALUATION REPORT" subtitle
        story.extend(build_cover_page(
            title=title,
            subtitle="Evaluation Report",
            path=str(self.target_path),
            level=self.level,
            date=self.date,
            doc_id=self.doc_id,
            brand=self.brand,
            content_width=self.content_width,
        ))

        # Body
        story.extend(self.build_body(content))
        story.append(PageBreak())

        # Back cover
        story.extend(self.build_back_cover())

        return story

    # ------------------------------------------------------------------
    # Suppress unused base section builders
    # ------------------------------------------------------------------

    def build_at_a_glance(self, *args, **kwargs) -> list:
        return []

    def build_executive_summary(self, *args, **kwargs) -> list:
        return []

    def build_cross_references(self, *args, **kwargs) -> list:
        return []

    def build_index(self, *args, **kwargs) -> list:
        return []

    def build_bibliography(self, *args, **kwargs) -> list:
        return []

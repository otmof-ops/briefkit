"""
briefkit.templates.briefing
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Default executive briefing template — the current Codex behavior generalized.

Build order:
  Cover → Classification Banner → TOC → Executive Summary →
  At a Glance Dashboard → Body (chapter-per-section) →
  Cross-References → Key Terms → Bibliography → Back Cover
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.platypus import Paragraph, Spacer, PageBreak, KeepTogether

from briefkit.generator import (
    BaseBriefingTemplate,
    build_callout_box,
    build_classification_banner,
    build_cover_page,
    build_data_table,
    build_metric_dashboard,
    build_toc,
    build_timeline,
    build_bar_chart,
    build_pull_quote,
    HierarchyTreeFlowable,
)
from reportlab.lib.units import mm
from briefkit.styles import _safe_para, _ps, _hex, CONTENT_WIDTH
from briefkit.extractor import parse_markdown


class BriefingTemplate(BaseBriefingTemplate):
    """
    Default executive briefing template.

    Produces a full executive briefing with level-specific body sections:
      Level 3 (doc set)  — Technical deep-dive, key results, engineering brilliance,
                           practical applications
      Level 2 (subject)  — Subject map, doc set directory, thematic analysis,
                           historical timeline, reading recommendations
      Level 1 (division) — Division overview, dashboard chart, division map,
                           subject summaries, cross-division connections, reading paths
      Level 4 (root)     — Root overview, library dashboard, top-level summary
    """

    def build_body(self, content: dict) -> list:
        """
        Build the body section dispatched by level.
        """
        if self.level == 3:
            return self._build_doc_set_body(content)
        elif self.level == 2:
            return self._build_subject_body(content)
        elif self.level == 1:
            return self._build_division_body(content)
        else:
            return self._build_root_body(content)

    # ------------------------------------------------------------------
    # Level 3 — Documentation set
    # ------------------------------------------------------------------

    def _build_doc_set_body(self, content: dict) -> list:
        flowables = []

        # 3. Context and Significance
        flowables.append(Paragraph("3. Context and Significance", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))  # ~3mm in points
        flowables.append(Paragraph(
            "Understanding where this work fits within the broader field — what existed "
            "before it, why it was needed, and what changed because of it.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 3 * mm))

        overview = content.get("overview", "")
        year_matches = re.findall(r'\b(19[5-9]\d|20[0-3]\d)\b', overview)
        if len(year_matches) >= 2:
            unique_years = sorted(set(int(y) for y in year_matches))[:8]
            events = [(y, "Key event") for y in unique_years]
            flowables.extend(build_timeline(events, brand=self.brand, content_width=self.content_width))
            flowables.append(Spacer(1, 3 * mm))

        # 4. Technical Deep-Dive
        subsystems = content.get("subsystems", [])
        flowables.append(Paragraph("4. Technical Deep-Dive", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))
        if subsystems:
            flowables.append(Paragraph(
                "Detailed analysis of each major subsystem, component, or topic "
                "covered in this documentation set.",
                self.styles["STYLE_BODY"],
            ))
            flowables.append(Spacer(1, 3 * mm))

            for idx, sub in enumerate(subsystems, start=1):
                flowables.append(Paragraph(f"4.{idx} {sub['name']}", self.styles["STYLE_H2"]))
                flowables.append(Spacer(1, 2 * mm))

                blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
                rendered = 0
                for block in blocks:
                    if block["type"] == "heading" and block["level"] <= 2:
                        continue
                    for fl in self.render_blocks([block]):
                        flowables.append(fl)
                        rendered += 1
                        if rendered >= 80:
                            break
                    if rendered >= 80:
                        break

                insights = sub.get("insights", [])
                if insights:
                    flowables.append(build_callout_box(
                        insights[0][:500], "insight", brand=self.brand, content_width=self.content_width
                    ))

                flowables.append(Spacer(1, 4 * mm))
        else:
            pdfs = list(self.target_path.glob("*.pdf"))
            if pdfs:
                flowables.append(Paragraph(
                    "No analysis documents found. The following source PDFs are present:",
                    self.styles["STYLE_BODY"],
                ))
                list_style = _ps(
                    "PDFList", brand=self.brand,
                    fontSize=9, textColor=_hex(self.brand, "body_text"),
                    leading=13, leftIndent=12,
                )
                for pdf in pdfs[:10]:
                    flowables.append(_safe_para(f"\u2022 {pdf.name}", list_style))
            else:
                flowables.append(Paragraph(
                    "No analysis documents were found in this documentation set.",
                    self.styles["STYLE_BODY"],
                ))

        # 5. Key Results and Data
        flowables.append(Paragraph("5. Key Results and Data", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        all_result_tables = []
        for sub in subsystems:
            for tbl in sub.get("tables", []):
                if tbl.get("headers"):
                    all_result_tables.append((sub["name"], tbl))

        if all_result_tables:
            flowables.append(Paragraph(
                "Consolidated data tables extracted from the source documentation.",
                self.styles["STYLE_BODY"],
            ))
            flowables.append(Spacer(1, 3 * mm))
            for sub_name, tbl in all_result_tables[:5]:
                flowables.append(Paragraph(sub_name, self.styles["STYLE_H3"]))
                flowables.extend(build_data_table(
                    tbl["headers"], tbl["rows"], brand=self.brand, content_width=self.content_width
                ))
                flowables.append(Spacer(1, 2 * mm))
        else:
            flowables.append(Paragraph(
                "No structured results tables were found in the source material. "
                "See the technical deep-dive sections above for qualitative findings.",
                self.styles["STYLE_BODY"],
            ))

        flowables.append(PageBreak())

        # 6. Engineering Brilliance
        brilliance = content.get("brilliance_summary", "")
        flowables.append(Paragraph("6. Engineering Brilliance", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        if brilliance:
            flowables.append(Paragraph(
                "The key insight, the core constraint, and the lasting impact of this work.",
                self.styles["STYLE_BODY"],
            ))
            flowables.append(Spacer(1, 3 * mm))
            brill_blocks = parse_markdown(brilliance)
            rendered = 0
            pull_count = 0
            for block in brill_blocks:
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
                    rendered += 1
                if rendered % 10 == 0 and pull_count < 2 and block["type"] == "paragraph":
                    text = block.get("text", "")
                    if len(text) > 60:
                        flowables.extend(build_pull_quote(
                            text[:200], "Engineering Brilliance Essay", brand=self.brand, content_width=self.content_width
                        ))
                        pull_count += 1
                if rendered >= 50:
                    break
        else:
            flowables.append(Paragraph(
                "The engineering-brilliance.md essay was not found for this documentation set.",
                self.styles["STYLE_BODY"],
            ))

        flowables.append(PageBreak())

        # 7. Practical Applications
        flowables.append(Paragraph("7. Practical Applications", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        flowables.append(Paragraph(
            "How this knowledge is applied in practice across industry, academia, "
            "and cross-disciplinary domains.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 3 * mm))

        guide = content.get("guide_content", "")
        if guide:
            rendered = 0
            for block in parse_markdown(guide)[:30]:
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
                    rendered += 1
        else:
            flowables.append(build_callout_box(
                "For practical application guidance, consult the guide.md file "
                "and the subject-level reading recommendations.",
                "learn",
                brand=self.brand,
                content_width=self.content_width,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Level 2 — Subject
    # ------------------------------------------------------------------

    def _build_subject_body(self, content: dict) -> list:
        flowables = []
        doc_sets = content.get("doc_sets", [])

        # 3. Subject Map
        flowables.append(Paragraph("3. Subject Map", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        flowables.append(Paragraph(
            "Visual overview of all documentation sets within this subject.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 3 * mm))

        if doc_sets:
            tree_data = [(0, f"{content.get('title', 'Subject')} ({len(doc_sets)} doc sets)")]
            for ds in doc_sets[:20]:
                tree_data.append((1, (ds.get("title") or ds.get("name") or "Unknown")[:40]))
            flowables.append(HierarchyTreeFlowable(tree_data, brand=self.brand))
            flowables.append(Spacer(1, 4 * mm))

        # 4. Doc Set Directory
        flowables.append(Paragraph("4. Doc Set Directory", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        if doc_sets:
            dir_rows = []
            for ds in doc_sets:
                name  = (ds.get("name") or "")[:30].replace("-", " ").title()
                title = (ds.get("title") or "")[:40]
                meta  = ds.get("metrics", {})
                year  = meta.get("year", "\u2014")
                words = f"{meta.get('word_count', 0):,}" if meta.get("word_count") else "\u2014"
                dir_rows.append([name, title, str(year), words])
            flowables.extend(build_data_table(
                ["Directory", "Title", "Year", "Words"], dir_rows,
                title="Documentation Sets in This Subject",
                brand=self.brand,
                content_width=self.content_width,
            ))
            flowables.append(Spacer(1, 4 * mm))
            for ds in doc_sets[:12]:
                title_txt = ds.get("title") or ds.get("name") or "Unknown"
                flowables.append(Paragraph(title_txt, self.styles["STYLE_H3"]))
                overview = ds.get("overview", "")
                if overview:
                    flowables.append(Paragraph(overview[:400], self.styles["STYLE_BODY"]))
                flowables.append(Spacer(1, 2 * mm))

        # 5. Thematic Analysis
        flowables.append(PageBreak())
        flowables.append(Paragraph("5. Thematic Analysis", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        flowables.append(Paragraph(
            "Analysis of the major themes and conceptual clusters within this subject.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 3 * mm))

        if doc_sets:
            clusters: dict[str, list] = {}
            for ds in doc_sets:
                name = ds.get("name", "")
                parts = name.split("/")
                ck = (parts[0] if len(parts) > 1 else "General").replace("-", " ").title()
                clusters.setdefault(ck, []).append(ds)

            bullet_style = _ps(
                "ThemeItem", brand=self.brand,
                fontSize=10, textColor=_hex(self.brand, "body_text"),
                leading=14, leftIndent=12,
            )
            for i, (cluster, items) in enumerate(list(clusters.items())[:6], start=1):
                flowables.append(Paragraph(f"5.{i} {cluster}", self.styles["STYLE_H2"]))
                flowables.append(Spacer(1, 2 * mm))
                flowables.append(Paragraph(
                    f"This thematic cluster contains {len(items)} documentation set(s) "
                    f"covering related aspects of {cluster.lower()}.",
                    self.styles["STYLE_BODY"],
                ))
                for item in items[:6]:
                    title_txt = (item.get("title") or item.get("name") or "")[:50]
                    flowables.append(_safe_para(f"\u2022 {title_txt}", bullet_style))
                flowables.append(Spacer(1, 3 * mm))

        # 6. Historical Timeline
        flowables.append(Paragraph("6. Historical Timeline", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        all_years: list[int] = []
        for ds in doc_sets:
            all_years.extend(
                int(y) for y in re.findall(r'\b(19[5-9]\d|20[0-3]\d)\b', ds.get("overview", ""))
            )
        if all_years:
            events = [(y, "Event") for y in sorted(set(all_years))[:8]]
            flowables.extend(build_timeline(events, brand=self.brand, content_width=self.content_width))
        else:
            flowables.append(Paragraph("Chronological data was not available.", self.styles["STYLE_BODY"]))
        flowables.append(Spacer(1, 4 * mm))

        # 7. Reading Recommendations
        flowables.append(Paragraph("7. Reading Recommendations", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        guide = content.get("guide_content", "")
        if guide:
            for block in parse_markdown(guide)[:40]:
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
        else:
            rec_style = _ps(
                "RecItem", brand=self.brand,
                fontSize=10, textColor=_hex(self.brand, "body_text"),
                leading=14, leftIndent=12,
            )
            for aud_label in ["For Practitioners", "For Researchers", "For Students"]:
                flowables.append(Paragraph(aud_label, self.styles["STYLE_H2"]))
                for ds in doc_sets[:3]:
                    title_txt = (ds.get("title") or ds.get("name") or "")[:50]
                    flowables.append(_safe_para(f"\u2022 {title_txt}", rec_style))
                flowables.append(Spacer(1, 3 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Level 1 — Division
    # ------------------------------------------------------------------

    def _build_division_body(self, content: dict) -> list:
        flowables = []
        subjects = content.get("subjects", [])

        # 3. Division Overview
        flowables.append(Paragraph("3. Division Overview", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        overview = content.get("overview", "")
        if overview:
            for block in parse_markdown(overview[:3000])[:30]:
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
        flowables.append(Spacer(1, 4 * mm))

        total_doc_sets = sum(s.get("doc_count", 0) for s in subjects)
        flowables.append(build_callout_box(
            f"This division contains {len(subjects)} subject areas and approximately "
            f"{total_doc_sets} documentation sets.",
            "learn",
            brand=self.brand,
            content_width=self.content_width,
        ))

        # 4. Division Dashboard
        flowables.append(PageBreak())
        flowables.append(Paragraph("4. Division Dashboard", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        if subjects:
            chart_data = [
                (s.get("name", "?")[:25], s.get("doc_count", 0))
                for s in subjects if s.get("doc_count", 0) > 0
            ]
            if chart_data:
                flowables.extend(build_bar_chart(chart_data, "Doc Sets per Subject", brand=self.brand, content_width=self.content_width))
            flowables.append(Spacer(1, 4 * mm))
            subj_rows = [
                [s.get("name", "")[:35], str(s.get("doc_count", 0)), s.get("overview", "")[:80]]
                for s in subjects
            ]
            flowables.extend(build_data_table(
                ["Subject", "Doc Sets", "Overview"], subj_rows,
                title="Subject Areas in This Division",
                brand=self.brand,
                content_width=self.content_width,
            ))

        # 5. Division Map
        flowables.append(PageBreak())
        flowables.append(Paragraph("5. Division Map", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        if subjects:
            tree_data = [(0, content.get("title", "Division"))]
            for s in subjects:
                tree_data.append((1, f"{s.get('name', '?')[:35]} ({s.get('doc_count', 0)} sets)"))
            flowables.append(HierarchyTreeFlowable(tree_data, brand=self.brand))
            flowables.append(Spacer(1, 6 * mm))

        # 6. Subject Summaries
        flowables.append(PageBreak())
        flowables.append(Paragraph("6. Subject Summaries", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        for i, subj in enumerate(subjects, start=1):
            flowables.append(Paragraph(
                f"6.{i} {subj.get('name', 'Unknown')}", self.styles["STYLE_H2"]
            ))
            flowables.append(Spacer(1, 2 * mm))
            subj_overview = subj.get("overview", "")
            if subj_overview:
                for block in parse_markdown(subj_overview[:1500])[:20]:
                    for fl in self.render_blocks([block]):
                        flowables.append(fl)
            flowables.append(Paragraph(
                f"Contains {subj.get('doc_count', 0)} documentation set(s).",
                self.styles["STYLE_BODY"],
            ))
            flowables.append(Spacer(1, 4 * mm))

        # 7. Reading Paths
        flowables.append(PageBreak())
        flowables.append(Paragraph("7. Reading Paths", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        path_style = _ps(
            "PathItem", brand=self.brand,
            fontSize=10, textColor=_hex(self.brand, "body_text"),
            leading=14, leftIndent=12,
        )
        for audience, desc in [
            ("For Students",     "Start with foundational subjects before specialisations."),
            ("For Practitioners","Focus on applied and engineering-focused documentation."),
            ("For Researchers",  "Begin with primary source papers and experimental results."),
            ("For Educators",    "Use division and subject briefings as curriculum frameworks."),
        ]:
            flowables.append(Paragraph(audience, self.styles["STYLE_H2"]))
            flowables.append(Paragraph(desc, self.styles["STYLE_BODY"]))
            for s in subjects[:3]:
                flowables.append(_safe_para(f"\u2022 {s.get('name', '')}", path_style))
            flowables.append(Spacer(1, 3 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Level 4 — Root / Special
    # ------------------------------------------------------------------

    def _build_root_body(self, content: dict) -> list:
        flowables = []

        flowables.append(Paragraph("3. Overview", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        overview = content.get("overview", "")
        if overview:
            for block in parse_markdown(overview[:4000])[:40]:
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
        else:
            flowables.append(Paragraph(
                "This is a root-level briefing. See individual division briefings "
                "for detailed coverage.",
                self.styles["STYLE_BODY"],
            ))

        flowables.append(PageBreak())
        flowables.append(Paragraph("4. Dashboard", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        metrics = content.get("metrics", {})
        dashboard = build_metric_dashboard([
            (str(metrics.get("doc_count", "\u2014")), "Doc Sets"),
            (str(metrics.get("file_count", "\u2014")), "Files"),
            (f"{metrics.get('word_count', 0):,}" if metrics.get("word_count") else "\u2014", "Words"),
        ], brand=self.brand, content_width=self.content_width)
        flowables.append(dashboard)
        flowables.append(Spacer(1, 4 * mm))

        guide = content.get("guide_content", "")
        if guide:
            flowables.append(PageBreak())
            flowables.append(Paragraph("5. Guide", self.styles["STYLE_H1"]))
            flowables.append(Spacer(1, 3 * mm))
            for block in parse_markdown(guide[:3000])[:30]:
                for fl in self.render_blocks([block]):
                    flowables.append(fl)

        return flowables

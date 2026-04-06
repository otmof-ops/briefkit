"""
briefkit.generator
~~~~~~~~~~~~~~~~~~
Core BaseBriefingTemplate class — orchestrates PDF generation for any
content hierarchy level.

Extracted and generalized from generate-briefing-v2.py BaseBriefingTemplate
(original lines 1992-3074).  All Codex-specific references removed;
brand colors, doc IDs, and hierarchy config are driven by the config dict.
"""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A3, A4, legal, letter
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from briefkit.doc_ids import get_or_assign_doc_id
from briefkit.elements.callout import build_callout_box, build_pull_quote  # noqa: F401 — re-exported
from briefkit.elements.charts import build_bar_chart, build_timeline  # noqa: F401 — re-exported
from briefkit.elements.cover import build_cover_page  # noqa: F401 — re-exported
from briefkit.elements.dashboard import build_metric_dashboard  # noqa: F401 — re-exported

# ---------------------------------------------------------------------------
# Page size lookup
# ---------------------------------------------------------------------------
# Re-export _hf_state for templates that mutate section headers directly
from briefkit.elements.header_footer import (  # noqa: F401 — re-exported
    _hf_state,  # noqa: F401, E402
    build_classification_banner,
    make_header_footer,
)
from briefkit.elements.tables import build_data_table  # noqa: F401 — re-exported
from briefkit.elements.toc import build_toc  # noqa: F401 — re-exported
from briefkit.extractor import extract_content as _extract_content
from briefkit.extractor import parse_markdown
from briefkit.styles import (
    CONTENT_WIDTH,  # noqa: F401 — re-exported
    GUTTER,  # noqa: F401 — re-exported
    MARGIN_BOTTOM,  # noqa: F401 — re-exported
    MARGIN_LEFT,  # noqa: F401 — re-exported
    MARGIN_RIGHT,  # noqa: F401 — re-exported
    MARGIN_TOP,  # noqa: F401 — re-exported
    _get_brand,
    _hex,
    _ps,
    _safe_para,
    _safe_text,
    build_styles,
    compute_content_width,
)
from briefkit.variants import auto_detect_variant, get_variant

_PAGE_SIZES = {
    "A4": A4,
    "A3": A3,
    "Letter": letter,
    "Legal": legal,
    "Tabloid": (792, 1224),
}

# ---------------------------------------------------------------------------
# Helper flowables
# ---------------------------------------------------------------------------

class HierarchyTreeFlowable(Flowable):
    """Indented hierarchy tree drawn directly on the canvas."""

    def __init__(self, tree_data, width=None, brand=None):
        super().__init__()
        self._width = width
        self.tree_data = tree_data
        self._brand = _get_brand(brand)

    def wrap(self, avail_w, avail_h):
        self.width = self._width or avail_w
        self.height = max(30, len(self.tree_data) * 14 + 4)
        return self.width, self.height

    def draw(self):
        b = self._brand
        primary  = HexColor(b.get("primary",   "#1B2A4A"))
        body_c   = HexColor(b.get("body_text", "#2C2C2C"))
        c = self.canv
        y = self.height - 4
        for level, label in self.tree_data:
            indent = level * 14 + 2
            prefix = "\u2022 " if level > 0 else ""
            font   = "Helvetica-Bold" if level == 0 else "Helvetica"
            size   = 10 if level == 0 else 9
            col    = primary if level == 0 else body_c
            c.setFillColor(col)
            c.setFont(font, size)
            c.drawString(indent, y, f"{prefix}{str(label)}")
            y -= 14



# ---------------------------------------------------------------------------
# Level detection
# ---------------------------------------------------------------------------

def detect_level(
    target_path: str | Path,
    project_root: str | Path | None,
    config: dict,
) -> int:
    """
    Determine the briefing level for *target_path* from the hierarchy config.

    The hierarchy.depth_to_level dict maps depth-from-project-root to level:
      {0: 1, 1: 2, 2: 3}
    Anything deeper than the deepest key gets the deepest level value.
    hierarchy.root_level is returned when no project root can be determined.

    Returns an integer level (1-4).
    """
    hier = config.get("hierarchy", {})
    root_level = hier.get("root_level", 4)
    depth_to_level = hier.get("depth_to_level", {0: 1, 1: 2, 2: 3})

    target = Path(target_path).resolve()

    if project_root is None:
        return root_level

    root = Path(project_root).resolve()

    try:
        rel = target.relative_to(root)
        depth = len(rel.parts)
    except ValueError:
        # target is not under root
        return root_level

    # Sort keys so we always pick the deepest matched level
    sorted_depths = sorted(depth_to_level.keys())
    assigned = root_level
    for d in sorted_depths:
        if depth >= d:
            assigned = depth_to_level[d]
    return assigned



# ---------------------------------------------------------------------------
# BaseBriefingTemplate
# ---------------------------------------------------------------------------

class BaseBriefingTemplate:
    """
    Orchestrates the generation of a full briefing PDF.

    Subclasses override build_story() to assemble a different section order,
    or override individual section builders.

    Parameters
    ----------
    target_path : str or Path
        Directory being briefed.
    level : int or None
        Hierarchy level (1-4).  Auto-detected from hierarchy config if None.
    config : dict or None
        Fully resolved briefkit config dict (from briefkit.config.load_config).
        Falls back to a minimal default if None.
    output_path : str or Path or None
        Where to write the PDF.  Defaults to target_path/<output.filename>.
    """

    def __init__(
        self,
        target_path: str | Path,
        level: int | None = None,
        config: dict | None = None,
        output_path: str | Path | None = None,
    ):
        self.target_path = Path(target_path).resolve()
        self.config      = config or {}
        self.brand       = self.config.get("brand", {})

        # Store license notice separately — not in brand dict to avoid
        # polluting the build_styles() LRU cache key
        license_cfg = self.config.get("license", {})
        self.license_notice = license_cfg.get("notice", "")

        # Resolve project root from config
        self._project_root: Path | None = None
        from briefkit.config import find_project_root
        pr = find_project_root(self.target_path)
        if pr:
            self._project_root = pr

        if level is not None:
            self.level = level
        else:
            self.level = detect_level(self.target_path, self._project_root, self.config)

        output_filename = self.config.get("output", {}).get("filename", "executive-briefing.pdf")
        if output_path:
            self.output_path = Path(output_path)
        else:
            self.output_path = self.target_path / output_filename

        self.content:   dict = {}
        self.date:      datetime.date = datetime.date.today()
        self.date_str:  str = self.date.strftime("%d %B %Y")
        self.doc_id:    str = ""

        # Compute dynamic content width
        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        page_size = _PAGE_SIZES.get(layout.get("page_size", "A4"), A4)
        self.content_width = compute_content_width(page_size, margins)

        # Pre-build styles dict for use by section builders
        self.styles = build_styles(self.brand)

    # ------------------------------------------------------------------
    # Content extraction
    # ------------------------------------------------------------------

    def extract_content(self) -> dict:
        """
        Extract structured content from target_path based on level.

        Delegates to briefkit.extractor.extract_content().
        Caches the result in self.content.
        """
        self.content = _extract_content(
            self.target_path,
            level=self.level,
            config=self.config,
        )
        return self.content

    # ------------------------------------------------------------------
    # Block renderer
    # ------------------------------------------------------------------

    def render_blocks(self, blocks: list[dict]) -> list:
        """
        Convert parsed markdown block dicts into ReportLab flowables.

        Each block is a dict with at minimum a 'type' key.

        Supported types:
          heading    — Paragraph with H1/H2/H3 style depending on block level
          paragraph  — Paragraph with body style
          table      — build_data_table() list
          code       — Paragraph with code style (escaped, monospace)
          list_item  — Paragraph with bullet or number prefix
          blockquote — build_callout_box()
          rule       — horizontal rule Drawing

        Returns a flat list of flowables (tables are already lists; they are
        extended in-place).
        """
        flowables = []
        rule_c = HexColor(self.brand.get("rule", "#CCCCCC"))

        for block in blocks:
            btype = block.get("type")

            if btype == "heading":
                level = block["level"]
                text  = block["text"]
                if level == 1:
                    flowables.append(_safe_para(text, self.styles["STYLE_H1"]))
                elif level == 2:
                    flowables.append(_safe_para(text, self.styles["STYLE_H2"]))
                else:
                    flowables.append(_safe_para(text, self.styles["STYLE_H3"]))

            elif btype == "paragraph":
                text = block.get("text", "").strip()
                if text:
                    flowables.append(_safe_para(text, self.styles["STYLE_BODY"]))

            elif btype == "list_item":
                text    = block.get("text", "")
                ordered = block.get("ordered", False)
                idx     = block.get("index", 0)
                bullet  = f"{idx}. " if ordered else "\u2022 "
                flowables.append(_safe_para(f"{bullet}{text}", self.styles["STYLE_LIST_ITEM"]))

            elif btype == "code":
                text = block.get("text", "")
                text = (
                    text
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("\n", "<br/>")
                    .replace(" ", "&nbsp;")
                )
                flowables.append(_safe_para(text, self.styles["STYLE_CODE"]))

            elif btype == "blockquote":
                text = block.get("text", "")
                flowables.append(build_callout_box(text, "insight", brand=self.brand, content_width=self.content_width))

            elif btype == "table":
                headers = block.get("headers", [])
                rows    = block.get("rows", [])
                flowables.extend(build_data_table(headers, rows, brand=self.brand, content_width=self.content_width))

            elif btype == "rule":
                rule_data = [[""]]
                rule_tbl  = Table(rule_data, colWidths=[self.content_width], rowHeights=[1])
                rule_tbl.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), rule_c),
                    ("TOPPADDING",    (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]))
                flowables.append(rule_tbl)

        return flowables

    # ------------------------------------------------------------------
    # Individual section builders
    # ------------------------------------------------------------------

    def build_executive_summary(self, content: dict) -> list:
        """
        Build the Executive Summary section flowables.

        Includes: overview text, orientation-doc integration,
        Key Takeaways callout, and What You'll Learn callout.
        """
        flowables = []
        flowables.append(Paragraph("1. Executive Summary", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        overview    = content.get("overview", "")
        orientation = content.get("orientation", "")
        title       = content.get("title", "the selected documentation")

        what_para = ""
        why_para  = ""
        who_para  = ""
        if orientation:
            ori_blocks  = parse_markdown(orientation)
            current_sec = None
            section_texts: dict[str, str] = {}
            for blk in ori_blocks:
                if blk["type"] == "heading":
                    txt_low = blk["text"].lower()
                    if "what is" in txt_low or "what are" in txt_low:
                        current_sec = "what"
                    elif "why" in txt_low:
                        current_sec = "why"
                    elif "who" in txt_low:
                        current_sec = "who"
                    else:
                        current_sec = None
                elif blk["type"] == "paragraph" and current_sec:
                    if current_sec not in section_texts:
                        section_texts[current_sec] = blk["text"]
            what_para = section_texts.get("what", "")
            why_para  = section_texts.get("why", "")
            who_para  = section_texts.get("who", "")

        if what_para:
            flowables.append(_safe_para(what_para, self.styles["STYLE_BODY"]))
            flowables.append(Spacer(1, 3 * mm))
            if overview:
                flowables.append(_safe_para(overview[:600], self.styles["STYLE_BODY"]))
        elif overview:
            blocks = parse_markdown(overview)
            for block in blocks[:20]:
                rendered = self.render_blocks([block])
                flowables.extend(rendered)
        else:
            flowables.append(_safe_para(
                f"This briefing covers {_safe_text(title)}. "
                f"See numbered documents for full content.",
                self.styles["STYLE_BODY"],
            ))

        if who_para:
            flowables.append(Spacer(1, 2 * mm))
            flowables.append(build_callout_box(
                f"Target Audience: {who_para}", "insight", brand=self.brand, content_width=self.content_width
            ))

        flowables.append(Spacer(1, 4 * mm))

        # Key Takeaways
        subsystems = content.get("subsystems", [])
        doc_sets   = content.get("doc_sets", [])
        subjects   = content.get("subjects", [])
        takeaway_lines: list[str] = []

        if why_para:
            for s in re.split(r'(?<=[.!?])\s+', why_para):
                s = s.strip()
                if len(s) > 30:
                    takeaway_lines.append(f"- {s[:200]}")
                    if len(takeaway_lines) >= 3:
                        break

        if overview and not takeaway_lines:
            numbered = re.findall(r'^\d+\.\s+(.{30,200})', overview, re.MULTILINE)
            for s in numbered[:5]:
                takeaway_lines.append(f"- {s.strip()[:200]}")

        if subsystems and not takeaway_lines:
            for sub in subsystems[:6]:
                insights = sub.get("insights", [])
                if insights and len(insights[0]) > 20:
                    takeaway_lines.append(
                        f"- <b>{_safe_text(sub['name'])}</b>: {insights[0][:150]}"
                    )
                else:
                    raw = sub.get("content", "")
                    for s in re.split(r'(?<=[.!?])\s+', raw.replace("\n", " ")):
                        s = s.strip().lstrip("#- *>`|")
                        if (len(s) > 30
                                and not s.startswith("```")
                                and not s.startswith("#")
                                and not re.match(r'^\d{2}-', s)):
                            s_words = s.split()
                            if len(s_words) > 100:
                                s = " ".join(s_words[:100]) + "\u2026"
                            takeaway_lines.append(
                                f"- <b>{_safe_text(sub['name'])}</b>: {s[:200]}"
                            )
                            break

        elif doc_sets and not takeaway_lines:
            for ds in doc_sets[:5]:
                ov = ds.get("overview", "")[:120]
                name = _safe_text(ds.get("title") or ds.get("name") or "")
                takeaway_lines.append(f"- <b>{name}</b>: {ov}" if ov else f"- {name}")

        elif subjects and not takeaway_lines:
            for subj in subjects[:5]:
                name = _safe_text(subj.get("name", ""))
                takeaway_lines.append(
                    f"- <b>{name}</b>: {subj.get('doc_count', 0)} doc sets."
                )

        if not takeaway_lines:
            for s in re.split(r'(?<=[.!?])\s+', (overview or "").replace("\n", " ")):
                s = s.strip()
                if len(s) > 30:
                    takeaway_lines.append(f"- {s[:200]}")
            if not takeaway_lines:
                takeaway_lines = [f"- See numbered documents for full analysis of {title}."]

        flowables.append(
            build_callout_box("\n".join(takeaway_lines), "takeaway", brand=self.brand, content_width=self.content_width)
        )
        flowables.append(Spacer(1, 3 * mm))

        # What You'll Learn
        if subsystems:
            names = [sub["name"] for sub in subsystems[:6]]
            if len(names) == 1:
                topics_str = names[0]
            elif len(names) == 2:
                topics_str = f"{names[0]} and {names[1]}"
            else:
                topics_str = ", ".join(names[:-1]) + f", and {names[-1]}"
            learn_text = (
                f"After reading this briefing you will understand {topics_str}, "
                f"and how they connect to {title}. "
                f"Each section includes technical detail, key data tables, and citations."
            )
        elif doc_sets:
            ds_names = [
                ds.get("title") or ds.get("name") or ""
                for ds in doc_sets[:4]
            ]
            ds_str = ", ".join(n for n in ds_names if n)
            learn_text = (
                f"After reading this briefing you will understand the scope of {title}"
                + (f", covering: {ds_str}." if ds_str else ".")
            )
        else:
            learn_text = (
                f"After reading this briefing on {title}, you will understand its "
                f"core concepts, key results, practical applications, and related content."
            )

        flowables.append(build_callout_box(learn_text, "learn", brand=self.brand, content_width=self.content_width))
        return flowables

    def build_at_a_glance(self, metrics: dict, content: dict | None = None) -> list:
        """
        Build the At a Glance section with metric dashboard.

        metrics: dict with keys doc_count, word_count, file_count, year, etc.
        content: optional full content dict for extracting key numbers.
        """
        if content is None:
            content = self.content

        flowables = []
        flowables.append(Paragraph("2. At a Glance", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        flowables.append(Paragraph(
            "Key metrics and quantitative overview for this briefing.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 4 * mm))

        key_numbers = metrics.get("key_numbers", [])
        if not key_numbers:
            all_text = ""
            for sub in content.get("subsystems", []):
                all_text += " ".join(sub.get("insights", []))
            number_patterns = re.findall(
                r'(\d+(?:\.\d+)?(?:x|%|\xd7|X)\s*\w+(?:\s+\w+)?'
                r'|[\d,]+\s*(?:TFLOPs?/s|GB/s|TB/s|MB|GB|KB|ms|ns|\xb5s)'
                r'|\d+(?:\.\d+)?[BMK]\s+parameters'
                r'|O\([^)]+\))',
                all_text,
            )
            for np_str in number_patterns[:4]:
                parts = np_str.strip().split(None, 1)
                if len(parts) == 2:
                    key_numbers.append((parts[0], parts[1]))
                elif parts:
                    key_numbers.append((parts[0], ""))

        if key_numbers and len(key_numbers) >= 2:
            metric_data = [(str(n), str(lbl)) for n, lbl in key_numbers[:4]]
        else:
            word_count = metrics.get("word_count", 0)
            chapters   = len(content.get("subsystems", []))
            pdf_count  = metrics.get("pdf_count", metrics.get("file_count", 0))
            year       = metrics.get("year", "\u2014")
            metric_data = []
            if chapters:
                metric_data.append((str(chapters), "Chapters"))
            if pdf_count:
                metric_data.append((str(pdf_count), "Source Files"))
            if year and year != str(datetime.date.today().year):
                metric_data.append((str(year), "Year"))
            if word_count:
                metric_data.append((f"{word_count:,}", "Words Analysed"))
            if not metric_data:
                metric_data = [("\u2014", "Metrics"), ("\u2014", "Not Available")]

        dashboard = build_metric_dashboard(metric_data, brand=self.brand, content_width=self.content_width)
        flowables.append(dashboard)
        flowables.append(Spacer(1, 4 * mm))

        source_type = metrics.get("source_type", "")
        if source_type:
            flowables.append(_safe_para(
                f"<b>Source Classification:</b> {_safe_text(source_type)}",
                self.styles["STYLE_BODY"],
            ))
            flowables.append(Spacer(1, 2 * mm))

        return flowables

    def build_body(self, content: dict) -> list:
        """
        Build the main body content section.

        Default implementation renders each subsystem as an H2 section.
        Subclasses override this method for different layouts.
        """
        flowables = []
        flowables.append(Paragraph("3. Content Overview", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        subsystems = content.get("subsystems", [])
        if not subsystems:
            overview = content.get("overview", "No detailed content available.")
            flowables.append(_safe_para(overview[:2000], self.styles["STYLE_BODY"]))
            return flowables

        for idx, sub in enumerate(subsystems, start=1):
            heading = _safe_para(
                f"3.{idx} {_safe_text(sub['name'])}", self.styles["STYLE_H2"]
            )

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered_count = 0
            first_flowable = None
            sub_flowables: list = []

            for block in blocks:
                if block["type"] == "heading" and block["level"] <= 2:
                    continue
                rendered = self.render_blocks([block])
                for fl in rendered:
                    if first_flowable is None:
                        first_flowable = fl
                    sub_flowables.append(fl)
                    rendered_count += 1
                    if rendered_count >= 80:
                        break
                if rendered_count >= 80:
                    break

            if first_flowable and sub_flowables:
                flowables.append(KeepTogether([heading, sub_flowables[0]]))
                flowables.extend(sub_flowables[1:])
            else:
                flowables.append(heading)
                flowables.extend(sub_flowables)

            flowables.append(Spacer(1, 5 * mm))

        brilliance = content.get("brilliance_summary", "")
        if brilliance:
            flowables.append(Paragraph("Engineering Brilliance", self.styles["STYLE_H1"]))
            for block in parse_markdown(brilliance)[:30]:
                flowables.extend(self.render_blocks([block]))

        return flowables

    def build_cross_references(self, refs: list[str], ref_labels: dict | None = None) -> list:
        """
        Build the Cross-Reference Map section.

        Returns empty list if refs is empty (section is omitted per §3.2).
        """
        if not refs:
            return []
        if ref_labels is None:
            ref_labels = {}

        flowables = []
        flowables.append(Paragraph("Cross-Reference Map", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        flowables.append(Paragraph(
            "The following sections are directly related to this content "
            "and are recommended for further reading.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 3 * mm))

        rows = []
        for ref in refs[:30]:
            ref_clean = ref.strip("/")
            label = ref_labels.get(ref_clean) or ref_labels.get(ref)
            if not label:
                label = ref_clean.split("/")[-1].replace("-", " ").title()
            rows.append([label, ref_clean, "Related"])

        flowables.extend(build_data_table(
            ["Topic", "Path", "Relationship"],
            rows,
            title="Related Content",
            brand=self.brand,
            content_width=self.content_width,
        ))
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(build_callout_box(
            "Follow the paths above to deepen your understanding of the connected topics. "
            "Start with the most closely related entries.",
            "insight",
            brand=self.brand,
            content_width=self.content_width,
        ))
        return flowables

    def build_index(self, terms: dict | list) -> list:
        """
        Build the Key Terms Index in a 2-column layout.

        Returns empty list if terms is empty (section omitted per §3.2).
        """
        if not terms:
            return []

        flowables = []
        flowables.append(Paragraph("Key Terms Index", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        flowables.append(Paragraph(
            "Alphabetical index of key technical terms used in this briefing.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 4 * mm))

        if isinstance(terms, dict):
            sorted_items = sorted(terms.items(), key=lambda x: x[0].lower())
        else:
            sorted_items = [(t, "") for t in sorted(set(terms), key=str.lower)]

        half = (len(sorted_items) + 1) // 2
        left_items  = sorted_items[:half]
        right_items = sorted_items[half:]

        primary = _hex(self.brand, "primary")

        def _render_col(items):
            col_flowables: list = []
            current_letter = ""
            for term, defn in items:
                first = term[0].upper() if term else ""
                if first != current_letter:
                    current_letter = first
                    col_flowables.append(
                        Paragraph(
                            f"<b>{first}</b>",
                            _ps(f"IndexLetter_{first}", brand=self.brand,
                                fontName="Helvetica-Bold", fontSize=9,
                                textColor=primary, spaceBefore=6, spaceAfter=2),
                        )
                    )
                entry = f"<b>{_safe_text(term)}</b>"
                if defn:
                    entry += f" \u2014 {_safe_text(defn[:80])}"
                col_flowables.append(
                    Paragraph(entry, self.styles["STYLE_INDEX_TERM"])
                )
            return col_flowables

        left_col  = _render_col(left_items)
        right_col = _render_col(right_items)

        max_len = max(len(left_col), len(right_col))
        left_col  += [Spacer(1, 1)] * (max_len - len(left_col))
        right_col += [Spacer(1, 1)] * (max_len - len(right_col))

        col_w = (self.content_width - GUTTER) / 2
        row_data = [[left_col[i], right_col[i]] for i in range(max_len)]
        if row_data:
            index_table = Table(row_data, colWidths=[col_w, col_w])
            index_table.setStyle(TableStyle([
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
                ("TOPPADDING",    (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            flowables.append(index_table)

        return flowables

    def build_bibliography(
        self,
        sources: list[dict],
        source_type: str = "ACADEMIC",
    ) -> list:
        """
        Build the Source Bibliography section grouped by type.

        Returns empty list if sources is empty (section omitted per §3.2).
        """
        if not sources:
            return []

        header_map = {
            "ACADEMIC":      "Source Bibliography \u2014 Research Papers",
            "GOVERNMENT":    "Source Bibliography \u2014 Government Documents",
            "PRIMARY-TEXT":  "Source Bibliography \u2014 Primary Texts",
            "PROPRIETARY":   "Source References (not redistributable \u2014 see .source-type for access)",
            "MANUFACTURER":  "Source References \u2014 Manufacturer Documentation",
            "DOCUMENTATION": "Source References \u2014 Official Documentation",
        }
        section_header = header_map.get(source_type.upper(), "Source Bibliography")

        flowables = []
        flowables.append(Paragraph(section_header, self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        flowables.append(Paragraph(
            "All primary sources, papers, books, and references cited in or "
            "supporting this briefing, grouped by type.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 4 * mm))

        type_order  = ["paper", "book", "specification", "case", "data", "web", "other"]
        type_labels = {
            "paper":         "Academic Papers",
            "book":          "Books and Monographs",
            "specification": "Technical Specifications and Standards",
            "case":          "Case Law",
            "data":          "Data Sets and Databases",
            "web":           "Web and Online Sources",
            "other":         "Other References",
        }

        grouped: dict[str, list] = {}
        for src in sources:
            t = src.get("type", "other").lower()
            grouped.setdefault(t, []).append(src)

        body_c = _hex(self.brand, "body_text")

        for type_key in type_order:
            if type_key not in grouped:
                continue
            items = grouped[type_key]
            label = type_labels.get(type_key, type_key.title())

            flowables.append(Paragraph(label, self.styles["STYLE_H2"]))
            flowables.append(Spacer(1, 2 * mm))

            for src in items:
                authors = src.get("authors", "Unknown Author") or "Unknown Author"
                year    = src.get("year", "n.d.") or "n.d."
                title   = src.get("title", "Untitled") or "Untitled"
                doi     = src.get("doi", "")

                citation = f"<b>{_safe_text(authors)}</b> ({year}). <i>{_safe_text(title)}</i>."
                if doi:
                    citation += f" DOI: {_safe_text(doi)}"

                flowables.append(_safe_para(citation, _ps(
                    f"BibEntry_{type_key}",
                    brand=self.brand,
                    fontSize=9,
                    textColor=body_c,
                    leading=13,
                    leftIndent=12,
                    firstLineIndent=-12,
                    spaceAfter=4,
                )))

            flowables.append(Spacer(1, 3 * mm))

        return flowables

    def build_back_cover(self) -> list:
        """Build the back cover page flowables — delegates to elements.back_cover."""
        from briefkit.elements.back_cover import build_back_cover as _build_back_cover
        # Pass license notice via a shallow copy — keeps self.brand clean for LRU cache
        back_brand = dict(self.brand)
        if self.license_notice:
            back_brand["_license_notice"] = self.license_notice
        return _build_back_cover(
            date=self.date,
            generator_note="Generated by briefkit",
            brand=back_brand,
            content_width=self.content_width,
        )

    def _derive_subtitle(self, content: dict) -> str:
        """Derive a subtitle string for the cover page from content metadata."""
        level_subtitles = {
            1: "Division Overview",
            2: "Subject Overview",
            3: "Documentation Set Briefing",
            4: "Special Briefing",
        }
        base = level_subtitles.get(self.level, "Executive Briefing")
        doc_count = content.get("metrics", {}).get("doc_count", 0)
        if doc_count:
            return f"{base} \u2014 {doc_count} Documentation Sets"
        return base

    # ------------------------------------------------------------------
    # build_story — override in subclasses for different section orders
    # ------------------------------------------------------------------

    def build_story(self, content: dict) -> list:
        """
        Assemble the complete flowables list for the PDF.

        Default order:
          1.  Cover page
          2.  Classification banner
          3.  Table of contents
          4.  Executive summary
          5.  At a glance
          6.  Body content
          7.  Cross-reference map (omitted if empty)
          8.  Key terms index (omitted if empty)
          9.  Bibliography (omitted if empty)
          10. Back cover

        Subclasses override this method to change the order or insert
        template-specific sections.
        """
        story = []

        # Cover
        story.extend(build_cover_page(
            title    = content.get("title", self.target_path.name.replace("-", " ").title()),
            subtitle = self._derive_subtitle(content),
            path     = str(self.target_path),
            level    = self.level,
            date     = self.date,
            doc_id   = self.doc_id,
            brand    = self.brand,
            content_width = self.content_width,
        ))

        # Classification banner
        story.append(build_classification_banner(
            self.level, str(self.target_path), brand=self.brand, content_width=self.content_width
        ))
        story.append(Spacer(1, 6 * mm))

        # Pre-build optional sections to drive dynamic TOC
        source_type = content.get("metrics", {}).get("source_type", "ACADEMIC")
        ref_labels  = content.get("cross_ref_labels", {})
        cross_ref_flowables = self.build_cross_references(
            content.get("cross_refs", []), ref_labels=ref_labels
        )
        index_flowables = self.build_index(content.get("terms", {}))
        bib_flowables   = self.build_bibliography(
            content.get("bibliography", []), source_type=source_type
        )

        # Table of contents
        story.append(_safe_para("Table of Contents", self.styles["STYLE_H1"]))
        story.append(Spacer(1, 2 * mm))

        toc_entries = [
            (1, "1. Executive Summary"),
            (1, "2. At a Glance"),
            (1, "3. Content Overview"),
        ]
        for i, sub in enumerate(content.get("subsystems", []), 1):
            toc_entries.append((2, f"  3.{i} {sub.get('name', f'Section {i}')}"))

        if cross_ref_flowables:
            toc_entries.append((1, "Cross-Reference Map"))
        if index_flowables:
            toc_entries.append((1, "Key Terms Index"))
        if bib_flowables:
            toc_entries.append((1, "Source Bibliography"))

        story.extend(build_toc(toc_entries, brand=self.brand, content_width=self.content_width))
        story.append(PageBreak())

        # Executive summary
        story.extend(self.build_executive_summary(content))
        story.append(Spacer(1, 4 * mm))

        # At a glance
        story.append(KeepTogether(self.build_at_a_glance(content.get("metrics", {}))))
        story.append(PageBreak())

        # Body
        story.extend(self.build_body(content))
        story.append(PageBreak())

        # Optional sections
        if cross_ref_flowables:
            story.extend(cross_ref_flowables)
            story.append(PageBreak())

        if index_flowables:
            story.extend(index_flowables)
            story.append(PageBreak())

        if bib_flowables:
            story.extend(bib_flowables)

        # Back cover
        story.extend(self.build_back_cover())

        return story

    # ------------------------------------------------------------------
    # generate — main entry point
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """
        Orchestrate the full PDF generation.

        Steps:
          1. Ensure output directory exists.
          2. Extract content from target_path.
          3. Assign or retrieve a document ID.
          4. Update header/footer state.
          5. Build the ReportLab document template.
          6. Call build_story() to assemble all flowables.
          7. Build the PDF with header/footer callbacks.

        Returns the output path as a Path object.
        """
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.extract_content()
        verbose = self.config.get("_cli", {}).get("verbose", False)

        if verbose:
            print(f"  Extracted: {len(content.get('subsystems', []))} subsystems, {content.get('metrics', {}).get('word_count', 0)} words", file=sys.stderr)

        # Document ID
        doc_ids_cfg = self.config.get("doc_ids", {})
        if doc_ids_cfg.get("enabled", True):
            self.doc_id = get_or_assign_doc_id(
                self.target_path,
                self.level,
                content.get("title", ""),
                config=self.config,
            )
        else:
            self.doc_id = ""

        # Build header/footer state dict and callback
        hf_state = {
            "section": content.get("title", self.target_path.name),
            "date": self.date_str,
            "doc_id": self.doc_id,
        }
        hf = make_header_footer(hf_state, brand=self.brand)

        # Note: _hf_state sync removed for thread safety — use closure via make_header_footer()

        # Page size
        layout    = self.config.get("layout", {})
        page_size = _PAGE_SIZES.get(layout.get("page_size", "A4"), A4)
        margins   = layout.get("margins", {})
        top_m     = margins.get("top",    25) * mm
        bottom_m  = margins.get("bottom", 22) * mm
        left_m    = margins.get("left",   20) * mm
        right_m   = margins.get("right",  20) * mm

        b       = self.brand
        org     = b.get("org", "briefkit")

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=content.get("title", "Briefing"),
            author=org,
            subject=f"Level {self.level} Briefing",
            creator="briefkit",
            keywords=self.doc_id or "briefkit",
        )

        story = self.build_story(content)

        # Apply variant-specific sections if detected
        variant_name = self.config.get("_cli", {}).get("variant")
        if not variant_name:
            # Auto-detect from content text
            parts = [content.get("overview", ""), content.get("title", "")]
            parts.extend(sub.get("content", "") for sub in content.get("subsystems", []))
            all_text = " ".join(parts)
            detected = auto_detect_variant(all_text)
            if detected:
                variant_name = detected.name
        if verbose and variant_name:
            print(f"  Variant detected: {variant_name}", file=sys.stderr)

        if variant_name:
            variant_obj = get_variant(variant_name)
            if variant_obj:
                story = variant_obj.build_variant_sections(content, story, self.styles, self.brand)

        if verbose:
            print(f"  Building PDF: {len(story)} flowables", file=sys.stderr)

        doc.build(story, onFirstPage=hf, onLaterPages=hf)

        return self.output_path

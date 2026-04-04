"""
briefkit.templates.newsletter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Newsletter-style template — visually rich, article-based layout.

Build order:
  Header Banner → Date/Issue → Feature Article → Article Sections →
  Pull Quotes / Callouts → Footer

Design norms (JotForm newsletter patterns):
  - Header banner with org name and newsletter title (brand primary bg, white text)
  - Date and issue number (from doc_id)
  - Feature article (first subsystem — larger text, prominent placement)
  - Article sections (remaining subsystems — each as a distinct article)
  - Sidebar-style callout boxes for key stats/quotes (from blockquotes)
  - Divider rules between articles
  - Footer with org info and "unsubscribe" style note
  - NO TOC, NO bibliography, NO formal structure
  - Visually rich — colored headings, accent bars, pull quotes

Suitable for: newsletters, bulletins, digests, announcements,
internal comms, update summaries.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from briefkit.extractor import parse_markdown
from briefkit.generator import (
    BaseBriefingTemplate,
    _hf_state,
    build_callout_box,
    build_pull_quote,
    make_header_footer,
)
from briefkit.styles import (
    _hex,
    _ps,
    _safe_para,
    _safe_text,
)

# ---------------------------------------------------------------------------
# Divider flowable helper
# ---------------------------------------------------------------------------


def _build_divider_rule(brand: dict, content_width: float) -> list:
    """Build a colored divider rule between articles."""
    accent = _hex(brand, "accent")
    rule_data = [["", ""]]
    col_w = content_width / 2
    t = Table(rule_data, colWidths=[col_w, col_w], rowHeights=[1])
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 2, accent),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [Spacer(1, 6 * mm), t, Spacer(1, 6 * mm)]


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------

class NewsletterTemplate(BaseBriefingTemplate):
    """
    Newsletter template.

    Produces a visually rich, article-based PDF with colored banners,
    accent rules, pull quotes, and a relaxed editorial layout.
    No TOC, no bibliography, no formal academic structure.
    """

    # ------------------------------------------------------------------
    # build_story — completely overridden for newsletter layout
    # ------------------------------------------------------------------

    def build_story(self, content: dict) -> list:
        """
        Assemble the newsletter:
          Banner → Date → Feature → Articles → Footer
        """
        story: list = []
        title = content.get("title", self.target_path.name.replace("-", " ").title())
        subsystems = content.get("subsystems", [])

        # -- Header banner --
        story.extend(self._build_banner(title))
        story.append(Spacer(1, 3 * mm))

        # -- Date and issue line --
        story.extend(self._build_date_line())
        story.append(Spacer(1, 6 * mm))

        # -- Overview / editorial intro --
        overview = content.get("overview", "")
        if overview:
            intro_style = _ps(
                "NLIntro", brand=self.brand,
                fontSize=11, textColor=_hex(self.brand, "body_text"),
                leading=16, spaceAfter=4,
                fontName=self.brand.get("font_body", "Helvetica"),
            )
            for block in parse_markdown(overview[:1500])[:10]:
                if block.get("type") == "paragraph":
                    story.append(_safe_para(block.get("text", ""), intro_style))
            story.extend(_build_divider_rule(self.brand, self.content_width))

        # -- Feature article (first subsystem) --
        if subsystems:
            story.extend(self._build_feature_article(subsystems[0]))
            story.extend(_build_divider_rule(self.brand, self.content_width))

        # -- Remaining articles --
        for idx, sub in enumerate(subsystems[1:], 2):
            story.extend(self._build_article(sub, idx))
            # Divider between articles (not after the last)
            if idx <= len(subsystems):
                story.extend(_build_divider_rule(self.brand, self.content_width))

        # -- Footer --
        story.append(PageBreak())
        story.extend(self._build_footer())

        return story

    # ------------------------------------------------------------------
    # Header banner
    # ------------------------------------------------------------------

    def _build_banner(self, title: str) -> list:
        """Build a full-width colored banner with org name and title."""
        flowables: list = []
        primary = _hex(self.brand, "primary")

        org = self.brand.get("org", "")
        banner_text = f"<b>{_safe_text(org)}</b>" if org else ""
        title_text = _safe_text(title)

        # Banner table — single row, primary background, white text
        banner_style = _ps(
            "NLBannerOrg", brand=self.brand,
            fontSize=20, fontName="Helvetica-Bold",
            textColor=white, alignment=1,
            spaceAfter=2,
        )
        title_style = _ps(
            "NLBannerTitle", brand=self.brand,
            fontSize=14, fontName="Helvetica",
            textColor=white, alignment=1,
            spaceBefore=2, spaceAfter=2,
        )

        cells = []
        if org:
            cells.append(Paragraph(banner_text, banner_style))
        cells.append(Paragraph(title_text, title_style))

        # Use a table for the colored background
        banner_data = [[cells[0] if cells else Paragraph("", banner_style)]]
        if len(cells) > 1:
            banner_data = [[c] for c in cells]

        t = Table(
            banner_data,
            colWidths=[self.content_width],
            rowHeights=None,
        )
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), primary),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 15),
            ("RIGHTPADDING", (0, 0), (-1, -1), 15),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        flowables.append(t)

        # Accent bar below banner
        accent = _hex(self.brand, "accent")
        accent_data = [[""]]
        at = Table(accent_data, colWidths=[self.content_width], rowHeights=[3])
        at.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), accent),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        flowables.append(at)

        return flowables

    # ------------------------------------------------------------------
    # Date / issue line
    # ------------------------------------------------------------------

    def _build_date_line(self) -> list:
        """Build the date and issue number line."""
        flowables: list = []

        issue = self.doc_id if self.doc_id else ""
        date_parts = [self.date_str]
        if issue:
            date_parts.append(f"Issue: {issue}")

        date_style = _ps(
            "NLDate", brand=self.brand,
            fontSize=9, textColor=_hex(self.brand, "caption"),
            alignment=2, spaceAfter=2,
            fontName=self.brand.get("font_caption", "Helvetica-Oblique"),
        )
        flowables.append(Paragraph(" | ".join(date_parts), date_style))

        return flowables

    # ------------------------------------------------------------------
    # Feature article (first subsystem — prominent)
    # ------------------------------------------------------------------

    def _build_feature_article(self, sub: dict) -> list:
        """Build the feature article with larger text and prominent heading."""
        flowables: list = []

        # Colored heading
        heading_style = _ps(
            "NLFeatureHead", brand=self.brand,
            fontSize=18, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "primary"),
            spaceAfter=6, spaceBefore=4,
        )
        flowables.append(Paragraph(
            _safe_text(sub.get("name", "Feature")), heading_style,
        ))

        # Accent bar under heading
        accent = _hex(self.brand, "secondary")
        bar_data = [[""]]
        bar = Table(bar_data, colWidths=[self.content_width * 0.3], rowHeights=[2])
        bar.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), accent),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        flowables.append(bar)
        flowables.append(Spacer(1, 4 * mm))

        # Feature body — slightly larger text
        feature_style = _ps(
            "NLFeatureBody", brand=self.brand,
            fontSize=11, textColor=_hex(self.brand, "body_text"),
            leading=16, spaceAfter=4,
        )

        blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
        rendered = 0
        pull_quote_added = False
        for block in blocks:
            if block.get("type") == "heading" and block.get("level", 1) <= 2:
                continue

            if block.get("type") == "blockquote" and not pull_quote_added:
                # Render as pull quote
                flowables.extend(build_pull_quote(
                    block.get("text", "")[:250],
                    sub.get("name", ""),
                    brand=self.brand,
                    content_width=self.content_width,
                ))
                pull_quote_added = True
                rendered += 1
                continue

            if block.get("type") == "paragraph":
                flowables.append(_safe_para(
                    block.get("text", ""), feature_style,
                ))
                rendered += 1
            else:
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
                    rendered += 1

            if rendered >= 30:
                break

        # Callout box for insights
        insights = sub.get("insights", [])
        if insights:
            flowables.append(Spacer(1, 3 * mm))
            flowables.append(build_callout_box(
                insights[0][:400],
                "insight",
                brand=self.brand,
                content_width=self.content_width,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Regular article
    # ------------------------------------------------------------------

    def _build_article(self, sub: dict, idx: int) -> list:
        """Build a regular article section."""
        flowables: list = []

        # Colored heading
        heading_style = _ps(
            f"NLArticleHead{idx}", brand=self.brand,
            fontSize=14, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "primary"),
            spaceAfter=4, spaceBefore=2,
        )
        flowables.append(Paragraph(
            _safe_text(sub.get("name", f"Article {idx}")), heading_style,
        ))

        # Thin accent bar
        accent = _hex(self.brand, "secondary")
        bar_data = [[""]]
        bar = Table(bar_data, colWidths=[self.content_width * 0.2], rowHeights=[1.5])
        bar.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), accent),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        flowables.append(bar)
        flowables.append(Spacer(1, 3 * mm))

        # Article body
        blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
        rendered = 0
        has_pull_quote = False
        for block in blocks:
            if block.get("type") == "heading" and block.get("level", 1) <= 2:
                continue

            # Convert blockquotes to callout boxes
            if block.get("type") == "blockquote" and not has_pull_quote:
                flowables.extend(build_pull_quote(
                    block.get("text", "")[:200],
                    sub.get("name", ""),
                    brand=self.brand,
                    content_width=self.content_width,
                ))
                has_pull_quote = True
                rendered += 1
                continue

            for fl in self.render_blocks([block]):
                flowables.append(fl)
                rendered += 1

            if rendered >= 40:
                break

        # Key stats callout from insights
        insights = sub.get("insights", [])
        if insights:
            flowables.append(Spacer(1, 2 * mm))
            flowables.append(build_callout_box(
                insights[0][:300],
                "learn",
                brand=self.brand,
                content_width=self.content_width,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------

    def _build_footer(self) -> list:
        """Build the newsletter footer with org info."""
        flowables: list = []

        # Footer rule
        primary = _hex(self.brand, "primary")
        rule_data = [[""]]
        t = Table(rule_data, colWidths=[self.content_width], rowHeights=[2])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), primary),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        flowables.append(t)
        flowables.append(Spacer(1, 4 * mm))

        # Org info
        org = self.brand.get("org", "")
        url = self.brand.get("url", "")
        footer_style = _ps(
            "NLFooterInfo", brand=self.brand,
            fontSize=8, textColor=_hex(self.brand, "caption"),
            alignment=1, leading=12,
        )

        footer_parts = []
        if org:
            footer_parts.append(f"<b>{_safe_text(org)}</b>")
        footer_parts.append(self.date_str)
        if url:
            footer_parts.append(_safe_text(url))
        flowables.append(Paragraph(
            " | ".join(footer_parts), footer_style,
        ))
        flowables.append(Spacer(1, 3 * mm))

        # "Unsubscribe" style note
        unsub_style = _ps(
            "NLUnsub", brand=self.brand,
            fontSize=7, textColor=_hex(self.brand, "rule"),
            alignment=1,
        )
        flowables.append(Paragraph(
            "You are receiving this because you are part of the distribution list. "
            "To unsubscribe, contact the editor.",
            unsub_style,
        ))

        # Copyright
        copyright_text = self.brand.get("copyright", "")
        if copyright_text:
            import datetime
            year = datetime.date.today().year
            cr_text = copyright_text.replace("{year}", str(year))
            cr_style = _ps(
                "NLCopyright", brand=self.brand,
                fontSize=7, textColor=_hex(self.brand, "rule"),
                alignment=1, spaceBefore=2,
            )
            flowables.append(Paragraph(_safe_text(cr_text), cr_style))

        return flowables

    # ------------------------------------------------------------------
    # Override generate() for custom header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the newsletter PDF with minimal header/footer."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.extract_content()
        title = content.get("title", self.target_path.name.replace("-", " ").title())

        # Doc ID (optional)
        doc_ids_cfg = self.config.get("doc_ids", {})
        if doc_ids_cfg.get("enabled", True):
            from briefkit.doc_ids import get_or_assign_doc_id
            self.doc_id = get_or_assign_doc_id(
                self.target_path, self.level,
                title, config=self.config,
            )

        # Populate header/footer state
        _hf_state["section"] = title
        _hf_state["date"] = self.date_str
        _hf_state["doc_id"] = self.doc_id
        _hf_state["brand"] = self.brand

        hf = make_header_footer(
            {"section": title, "date": self.date_str, "doc_id": self.doc_id},
            brand=self.brand,
        )

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 20) * mm
        bottom_m = margins.get("bottom", 18) * mm
        left_m = margins.get("left", 18) * mm
        right_m = margins.get("right", 18) * mm

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=title,
            author=self.brand.get("org", "briefkit"),
            subject="Newsletter",
            creator="briefkit",
        )

        story = self.build_story(content)
        doc.build(story, onFirstPage=hf, onLaterPages=hf)

        return self.output_path

    # ------------------------------------------------------------------
    # Suppress unused base section builders
    # ------------------------------------------------------------------

    def build_body(self, content: dict) -> list:
        return []

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

    def build_back_cover(self) -> list:
        return []

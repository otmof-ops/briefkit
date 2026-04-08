"""
briefkit.templates.policy
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Policy document template.

Build order:
  Cover Page → Document Control Block → Table of Contents →
  Purpose & Scope → Definitions → Policy Statements →
  Compliance & Enforcement → Review Schedule →
  Approval Signatures → Version History

Key differences:
  - Cover page with "POLICY DOCUMENT" subtitle and effective date
  - Document control block (version, effective date, review date, owner, approver)
  - Definitions section auto-extracted from bold terms or definition-style lists
  - Policy statements numbered from subsystems
  - Compliance and enforcement section
  - Review schedule
  - Formal approval signatures block
  - Version history table if available
  - No dashboard, no at-a-glance
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A3, A4, legal, letter
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
from briefkit.generator import BaseBriefingTemplate
from briefkit.styles import (
    _hex,
    _ps,
    _safe_para,
)
from briefkit.templates._helpers import should_skip

# ---------------------------------------------------------------------------
# Page sizes
# ---------------------------------------------------------------------------

_PAGE_SIZES = {
    "A4": A4,
    "A3": A3,
    "Letter": letter,
    "Legal": legal,
}

# ---------------------------------------------------------------------------
# Bold term extraction for definitions
# ---------------------------------------------------------------------------

_BOLD_TERM_PATTERN = re.compile(
    r'\*\*([A-Z][A-Za-z\s]{2,40}?)\*\*',
)

_DEFINITION_LIST_PATTERN = re.compile(
    r'^[-*]\s+\*\*(.+?)\*\*\s*[:–—-]\s*(.+)',
    re.MULTILINE,
)


def _extract_definitions(content: dict) -> list[tuple[str, str]]:
    """
    Extract definitions from bold terms and definition-style lists.
    Returns sorted (term, definition) pairs.
    """
    all_text = content.get("overview", "")
    for sub in content.get("subsystems", []):
        all_text += "\n" + sub.get("content", "")

    seen: set[str] = set()
    definitions: list[tuple[str, str]] = []

    # First pass: definition-style lists (- **Term**: definition)
    for match in _DEFINITION_LIST_PATTERN.finditer(all_text):
        term = match.group(1).strip()
        defn = match.group(2).strip()
        term_lower = term.lower()
        if term_lower not in seen and len(defn) > 5:
            seen.add(term_lower)
            definitions.append((term, defn[:200]))
            if len(definitions) >= 30:
                break

    # Second pass: standalone bold terms with surrounding context
    for match in _BOLD_TERM_PATTERN.finditer(all_text):
        term = match.group(1).strip()
        term_lower = term.lower()
        if term_lower in seen:
            continue
        seen.add(term_lower)

        start = max(0, match.start() - 10)
        end = min(len(all_text), match.end() + 120)
        context = all_text[start:end].strip()
        context = re.sub(r'\*\*', '', context)
        context = re.sub(r'\n+', ' ', context)
        context = context[:150]

        definitions.append((term, context))
        if len(definitions) >= 30:
            break

    definitions.sort(key=lambda x: x[0].lower())
    return definitions


def _extract_doc_control(content: dict) -> dict[str, str]:
    """
    Extract document control metadata from the first table in content
    or from README metadata patterns.
    """
    control: dict[str, str] = {}

    # Check first table for control-like fields
    for sub in content.get("subsystems", []):
        for tbl in sub.get("tables", []):
            headers = [h.lower() for h in tbl.get("headers", [])]
            rows = tbl.get("rows", [])
            control_keywords = {"version", "date", "owner", "approver", "author", "status"}
            if any(kw in " ".join(headers) for kw in control_keywords):
                for row in rows[:1]:
                    for i, header in enumerate(headers):
                        if i < len(row):
                            if "version" in header:
                                control["version"] = str(row[i])
                            elif "date" in header or "effective" in header:
                                control["effective_date"] = str(row[i])
                            elif "review" in header:
                                control["review_date"] = str(row[i])
                            elif "owner" in header or "author" in header:
                                control["owner"] = str(row[i])
                            elif "approver" in header or "approved" in header:
                                control["approver"] = str(row[i])
                if control:
                    return control

    return control


class PolicyTemplate(BaseBriefingTemplate):
    """
    Policy document template.

    Produces a formal policy PDF with document control block, purpose
    and scope, definitions, numbered policy statements, compliance
    section, review schedule, and approval signatures.  Suitable for
    organizational policies, governance documents, and compliance frameworks.
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the policy document story:
          Cover, Document Control, TOC, Purpose & Scope, Definitions,
          Policy Statements, Compliance, Review Schedule, Approvals,
          Version History.
        """
        story = []
        b = self.brand
        title = content.get("title", self.target_path.name.replace("-", " ").title())

        # ============================================================
        # Cover Page
        # ============================================================
        story.extend(self._build_cover_page(content, title))
        story.append(PageBreak())

        # ============================================================
        # Pre-build sections for TOC
        # ============================================================
        cfg = self.config
        doc_control = self._build_document_control(content)
        purpose = [] if should_skip(cfg, "scope") else self._build_purpose_scope(content)
        definitions = self._build_definitions(content)
        statements = self._build_policy_statements(content)
        compliance = self._build_compliance(content)
        review_schedule = self._build_review_schedule()
        approvals = self._build_approval_signatures()
        version_history = [] if should_skip(cfg, "revision_history") else self._build_version_history(content)

        # ============================================================
        # Document Control Block
        # ============================================================
        story.extend(doc_control)
        story.append(Spacer(1, 6 * mm))

        # ============================================================
        # Table of Contents
        # ============================================================
        if not should_skip(cfg, "toc"):
            story.append(_safe_para("Table of Contents", self.styles["STYLE_H1"]))
            story.append(Spacer(1, 2 * mm))

            toc_entries = []
            if purpose:
                toc_entries.append((1, "Purpose & Scope"))
            if definitions:
                toc_entries.append((1, "Definitions"))
            toc_entries.append((1, "Policy Statements"))
            for i, sub in enumerate(content.get("subsystems", []), 1):
                toc_entries.append((2, f"  {i}. {sub.get('name', f'Section {i}')}"))
            toc_entries.append((1, "Compliance & Enforcement"))
            toc_entries.append((1, "Review Schedule"))
            toc_entries.append((1, "Approval Signatures"))
            if version_history:
                toc_entries.append((1, "Version History"))

            from briefkit.generator import build_toc
            story.extend(build_toc(toc_entries, brand=b, content_width=self.content_width))
            story.append(PageBreak())

        # ============================================================
        # Body Sections
        # ============================================================
        if purpose:
            story.extend(purpose)
            story.append(Spacer(1, 6 * mm))

        if definitions:
            story.extend(definitions)
            story.append(PageBreak())

        story.extend(statements)
        story.append(PageBreak())

        story.extend(compliance)
        story.append(Spacer(1, 6 * mm))

        story.extend(review_schedule)
        story.append(PageBreak())

        story.extend(approvals)

        if version_history:
            story.append(Spacer(1, 8 * mm))
            story.extend(version_history)

        return story

    # ------------------------------------------------------------------
    # Cover Page
    # ------------------------------------------------------------------

    def _build_cover_page(self, content: dict, title: str) -> list:
        """Build cover page with POLICY DOCUMENT subtitle and effective date."""
        flowables: list = []
        b = self.brand
        primary = _hex(b, "primary")
        body_c = _hex(b, "body_text")
        caption_c = _hex(b, "caption")
        org = b.get("org", "")

        flowables.append(Spacer(1, 35 * mm))

        # Org name
        if org:
            org_style = _ps(
                "PolicyCoverOrg", brand=b, fontSize=14, textColor=primary,
                fontName="Helvetica-Bold", alignment=1, spaceAfter=6,
            )
            flowables.append(Paragraph(org, org_style))
            flowables.append(Spacer(1, 8 * mm))

        # POLICY DOCUMENT subtitle
        sub_style = _ps(
            "PolicyCoverSub", brand=b, fontSize=12, textColor=caption_c,
            fontName="Helvetica", alignment=1, spaceAfter=6,
        )
        flowables.append(Paragraph("POLICY DOCUMENT", sub_style))

        # Divider
        flowables.append(Spacer(1, 4 * mm))
        divider = Table([[""]], colWidths=[self.content_width * 0.5], rowHeights=[2])
        divider.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, -1), 2, HexColor(b.get("primary", "#1B2A4A"))),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        divider.hAlign = "CENTER"
        flowables.append(divider)
        flowables.append(Spacer(1, 8 * mm))

        # Policy title
        title_style = _ps(
            "PolicyCoverTitle", brand=b, fontSize=24, textColor=primary,
            fontName="Helvetica-Bold", alignment=1, spaceAfter=8,
        )
        flowables.append(Paragraph(title, title_style))

        # Effective date
        flowables.append(Spacer(1, 15 * mm))
        date_style = _ps(
            "PolicyCoverDate", brand=b, fontSize=10, textColor=body_c,
            alignment=1,
        )
        flowables.append(Paragraph(f"Effective Date: {self.date_str}", date_style))

        return flowables

    # ------------------------------------------------------------------
    # Document Control Block
    # ------------------------------------------------------------------

    def _build_document_control(self, content: dict) -> list:
        """Build the document control metadata block."""
        flowables: list = []
        b = self.brand
        rule_c = HexColor(b.get("rule", "#CCCCCC"))

        flowables.append(Paragraph("Document Control", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        control = _extract_doc_control(content)

        # Build control table
        fields = [
            ("Document Title", content.get("title", "Untitled Policy")),
            ("Version", control.get("version", "1.0")),
            ("Effective Date", control.get("effective_date", self.date_str)),
            ("Review Date", control.get("review_date", "To be determined")),
            ("Document Owner", control.get("owner", b.get("org", "To be assigned"))),
            ("Approver", control.get("approver", "To be assigned")),
        ]

        if self.doc_id:
            fields.insert(1, ("Document ID", self.doc_id))

        data = [[f[0], f[1]] for f in fields]
        tbl = Table(data, colWidths=[45 * mm, self.content_width - 45 * mm])
        tbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), HexColor(b.get("primary", "#1B2A4A"))),
            ("TEXTCOLOR", (1, 0), (1, -1), HexColor(b.get("body_text", "#333333"))),
            ("GRID", (0, 0), (-1, -1), 0.5, rule_c),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("BACKGROUND", (0, 0), (0, -1), HexColor(b.get("bg_alt", "#F5F5F5"))),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        flowables.append(tbl)

        return flowables

    # ------------------------------------------------------------------
    # Purpose & Scope
    # ------------------------------------------------------------------

    def _build_purpose_scope(self, content: dict) -> list:
        """Build purpose and scope section from overview."""
        flowables: list = []

        flowables.append(Paragraph("Purpose &amp; Scope", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        overview = content.get("overview", "")
        if overview:
            for block in parse_markdown(overview)[:20]:
                flowables.extend(self.render_blocks([block]))
        else:
            title = content.get("title", "this policy")
            fallback = (
                f"This document establishes the policy framework for {title}. "
                f"It applies to all personnel and stakeholders within the scope "
                f"of the organization's operations."
            )
            flowables.append(Paragraph(fallback, self.styles["STYLE_BODY"]))

        return flowables

    # ------------------------------------------------------------------
    # Definitions
    # ------------------------------------------------------------------

    def _build_definitions(self, content: dict) -> list:
        """Build definitions section from bold terms and definition-style lists."""
        defs = _extract_definitions(content)
        if not defs:
            return []

        flowables: list = []
        b = self.brand

        flowables.append(Paragraph("Definitions", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        intro_style = _ps(
            "PolicyDefsIntro", brand=b, fontSize=10,
            textColor=_hex(b, "body_text"), spaceAfter=6,
        )
        flowables.append(Paragraph(
            "For the purposes of this policy, the following terms apply:",
            intro_style,
        ))

        term_style = _ps(
            "PolicyDefTerm", brand=b, fontSize=10,
            textColor=_hex(b, "body_text"), leading=14,
            leftIndent=12, spaceAfter=4,
        )

        for term, defn in defs:
            flowables.append(_safe_para(
                f"<b>{term}</b> \u2014 {defn}",
                term_style,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Policy Statements
    # ------------------------------------------------------------------

    def _build_policy_statements(self, content: dict) -> list:
        """Build numbered policy statements from subsystems."""
        flowables: list = []

        flowables.append(Paragraph("Policy Statements", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        subsystems = content.get("subsystems", [])
        if not subsystems:
            overview = content.get("overview", "Policy statements to be defined.")
            flowables.append(Paragraph(overview[:2000], self.styles["STYLE_BODY"]))
            return flowables

        for idx, sub in enumerate(subsystems, start=1):
            name = sub.get("name", f"Section {idx}")
            flowables.append(Paragraph(f"{idx}. {name}", self.styles["STYLE_H2"]))
            flowables.append(Spacer(1, 1.5 * mm))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered = 0
            for block in blocks:
                btype = block.get("type", "")
                if btype == "heading" and block.get("level", 1) <= 1:
                    continue
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
                    rendered += 1
                    if rendered >= 80:
                        break
                if rendered >= 80:
                    break

            flowables.append(Spacer(1, 3 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Compliance & Enforcement
    # ------------------------------------------------------------------

    def _build_compliance(self, content: dict) -> list:
        """Build compliance and enforcement section."""
        flowables: list = []
        title = content.get("title", "this policy")

        flowables.append(Paragraph("Compliance &amp; Enforcement", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        compliance_text = (
            f"All personnel within the scope of {title} are required to comply "
            f"with the provisions set forth in this document. Non-compliance may "
            f"result in disciplinary action in accordance with the organization's "
            f"established procedures."
        )
        flowables.append(Paragraph(compliance_text, self.styles["STYLE_BODY"]))

        flowables.append(Spacer(1, 2 * mm))
        reporting_text = (
            "Any breaches or concerns regarding compliance with this policy "
            "should be reported to the Document Owner or through the "
            "organization's established reporting channels."
        )
        flowables.append(Paragraph(reporting_text, self.styles["STYLE_BODY"]))

        return flowables

    # ------------------------------------------------------------------
    # Review Schedule
    # ------------------------------------------------------------------

    def _build_review_schedule(self) -> list:
        """Build the review schedule section."""
        flowables: list = []

        flowables.append(Paragraph("Review Schedule", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        review_text = (
            "This policy shall be reviewed at least annually or whenever "
            "significant changes occur that may affect its applicability. "
            "The Document Owner is responsible for initiating the review "
            "process and ensuring that all amendments are approved by the "
            "designated Approver."
        )
        flowables.append(Paragraph(review_text, self.styles["STYLE_BODY"]))

        flowables.append(Spacer(1, 2 * mm))
        process_text = (
            "Proposed amendments should be submitted in writing to the "
            "Document Owner. All revisions shall be recorded in the "
            "Version History section of this document."
        )
        flowables.append(Paragraph(process_text, self.styles["STYLE_BODY"]))

        return flowables

    # ------------------------------------------------------------------
    # Approval Signatures
    # ------------------------------------------------------------------

    def _build_approval_signatures(self) -> list:
        """Build formal approval signature block."""
        flowables: list = []
        b = self.brand
        primary = _hex(b, "primary")
        rule_c = HexColor(b.get("rule", "#CCCCCC"))

        flowables.append(Paragraph("Approval Signatures", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        intro_style = _ps(
            "PolicyApprovalIntro", brand=b, fontSize=10,
            textColor=_hex(b, "body_text"), spaceAfter=8,
        )
        flowables.append(Paragraph(
            "By signing below, the undersigned confirm that this policy has "
            "been reviewed and approved for implementation.",
            intro_style,
        ))
        flowables.append(Spacer(1, 4 * mm))

        def _sig_block(role_label: str) -> list:
            """Generate a single approval signature block."""
            block: list = []
            role_h = _ps(
                "PolicyRoleH", brand=b, fontSize=11, textColor=primary,
                fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=4,
            )
            block.append(Paragraph(role_label, role_h))
            block.append(Spacer(1, 3 * mm))

            for field in ["Name:", "Title:", "Signature:", "Date:"]:
                data = [[field, ""]]
                tbl = Table(data, colWidths=[22 * mm, 80 * mm])
                tbl.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (0, 0), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, 0), HexColor(b.get("caption", "#666666"))),
                    ("LINEBELOW", (1, 0), (1, 0), 0.5, rule_c),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ]))
                block.append(tbl)

            block.append(Spacer(1, 6 * mm))
            return block

        flowables.extend(_sig_block("Document Owner"))
        flowables.extend(_sig_block("Approver"))

        return flowables

    # ------------------------------------------------------------------
    # Version History
    # ------------------------------------------------------------------

    def _build_version_history(self, content: dict) -> list:
        """Build version history table if available from content tables."""
        # Look for a table with version-like headers
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers = [h.lower() for h in tbl.get("headers", [])]
                if any("version" in h for h in headers):
                    rows = tbl.get("rows", [])
                    if rows:
                        flowables: list = []
                        flowables.append(
                            Paragraph("Version History", self.styles["STYLE_H1"])
                        )
                        flowables.append(Spacer(1, 2 * mm))

                        from briefkit.elements.tables import build_data_table
                        flowables.extend(build_data_table(
                            tbl["headers"], rows,
                            brand=self.brand,
                            content_width=self.content_width,
                        ))
                        return flowables

        return []

    # ------------------------------------------------------------------
    # Override generate() for policy header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the policy PDF with document title header and page footer."""
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

        # Header/footer state

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m = margins.get("left", 22) * mm
        right_m = margins.get("right", 22) * mm

        page_size = _PAGE_SIZES.get(layout.get("page_size", "A4"), A4)

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=title,
            author=self.brand.get("org", "briefkit"),
            subject="Policy Document",
            creator="briefkit",
        )

        story = self.build_story(content)

        policy_title = title
        brand = self.brand
        doc_id = self.doc_id or ""

        def _policy_first_page(canvas, doc_inner):
            """No header on cover page."""
            canvas.saveState()
            canvas.restoreState()

        def _policy_later_pages(canvas, doc_inner):
            """Header with policy title and doc ID; footer with page number."""
            canvas.saveState()
            page_w, page_h = doc_inner.pagesize

            # Header: policy title left, doc ID right
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(HexColor(brand.get("caption", "#666666")))
            canvas.drawString(
                left_m, page_h - 15 * mm,
                policy_title,
            )
            if doc_id:
                canvas.drawRightString(
                    page_w - right_m, page_h - 15 * mm,
                    doc_id,
                )

            # Footer: page number centered
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(HexColor(brand.get("caption", "#666666")))
            canvas.drawCentredString(
                page_w / 2, 10 * mm,
                f"Page {doc_inner.page}",
            )
            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=_policy_first_page,
            onLaterPages=_policy_later_pages,
        )

        return self.output_path

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

    def build_back_cover(self) -> list:
        return []

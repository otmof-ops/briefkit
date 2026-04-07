"""
briefkit.templates.novel
~~~~~~~~~~~~~~~~~~~~~~~~~
Narrative-aware novel template.

Extends BookTemplate with pattern-based detection and custom styling
for meta-narrative elements common in literary and horror fiction:
system commands, error tags, corrupted text, entity voices,
narrative erasure, and metafictional intrusions.

Build order:
  Half Title -> Title Page -> Copyright Page -> TOC -> Preface ->
  Chapters (with narrative-aware block styling) -> Glossary -> Colophon

Design origin:
  Built for long-form literary and horror fiction with meta-narrative
  elements (system commands, entity voices, erasure, metafictional
  intrusions) that require distinct visual treatment from the prose.
"""

from __future__ import annotations

import re

from reportlab.lib.units import mm
from reportlab.platypus import CondPageBreak, PageBreak, Paragraph, Spacer

from briefkit.extractor import parse_markdown
from briefkit.generator import build_toc
from briefkit.styles import CONTENT_WIDTH, _hex, _ps, _safe_para
from briefkit.templates.book import BookTemplate

# Pattern categories
_CAT_SYSTEM_COMMAND = "system_command"
_CAT_SYSTEM_TAG = "system_tag"
_CAT_SYSTEM_LOG = "system_log"
_CAT_CORRUPTED = "corrupted"
_CAT_ARROW_SEQ = "arrow_sequence"
_CAT_ITALIC_VOICE = "italic_voice"
_CAT_ERASURE = "erasure"

# Regex for detecting all-caps system commands (after HTML tag stripping)
_RE_ALL_CAPS = re.compile(r'^[A-Z][A-Z\s:.\-!,]+$')
# Regex for all-caps with apostrophes/digits (mixed-case system commands)
_RE_MOSTLY_CAPS = re.compile(r"^[A-Z][A-Z\s:.,!'\-0-9]+$")
# Regex for detecting full-italic paragraphs (after inline formatting)
_RE_FULL_ITALIC = re.compile(r'^<i>.+</i>$', re.DOTALL)
# Regex for stripping HTML tags (for pattern matching on plain text)
_RE_STRIP_TAGS = re.compile(r'<[^>]+>')
# Regex for italic content that is all-caps (erasure commands)
_RE_ITALIC_ALL_CAPS = re.compile(r'^[A-Z][A-Z\s\d\u2014:.\-!]+$')
# Erasure phrases that should be rendered as devastating structural blows
_ERASURE_PHRASES = [
    "was never here",
    "never met",
    "never existed",
    "does not need them",
    "never left",
    "never happened",
    "protagonist never",
]


class NovelTemplate(BookTemplate):
    """
    Narrative-aware novel template.

    Detects meta-narrative elements in prose and applies distinct
    typographic treatment:

    - ERASURE: Large centered Courier-Bold — narrative commands that
      erase characters or declare nonexistence. Devastating.
    - SYSTEM_COMMAND: Centered Courier-Bold — the architecture speaking.
    - SYSTEM_TAG: Monospace on tinted background — error codes.
    - SYSTEM_LOG: Indented monospace — diagnostic output.
    - CORRUPTED: Italic monospace — glitched text.
    - ITALIC_VOICE: Indented serif italic — entity whispers, notebook.

    All normal prose passes through unchanged.
    """

    def _build_novel_styles(self):
        """Create and cache the custom narrative styles."""
        if hasattr(self, '_novel_styles'):
            return self._novel_styles

        b = self.brand
        accent = _hex(b, "accent")
        caption = _hex(b, "caption")
        body_text = _hex(b, "body_text")
        primary = _hex(b, "primary")
        code_bg = b.get("code_bg", "#F0EDE6")

        styles = {
            _CAT_ERASURE: _ps(
                "NovelErasure", brand=b,
                fontName="Courier-Bold",
                fontSize=12,
                textColor=primary,
                alignment=1,
                spaceBefore=20,
                spaceAfter=20,
                leading=16,
            ),
            _CAT_SYSTEM_COMMAND: _ps(
                "NovelSystemCmd", brand=b,
                fontName="Courier-Bold",
                fontSize=11,
                textColor=accent,
                alignment=1,
                spaceBefore=18,
                spaceAfter=18,
                leading=15,
            ),
            _CAT_SYSTEM_TAG: _ps(
                "NovelSystemTag", brand=b,
                fontName="Courier",
                fontSize=9,
                textColor=caption,
                backColor=code_bg,
                alignment=0,
                spaceBefore=8,
                spaceAfter=8,
                leftIndent=0,
                leading=13,
            ),
            _CAT_SYSTEM_LOG: _ps(
                "NovelSystemLog", brand=b,
                fontName="Courier",
                fontSize=9,
                textColor=caption,
                backColor=code_bg,
                alignment=0,
                leftIndent=20,
                rightIndent=20,
                spaceBefore=6,
                spaceAfter=6,
                leading=13,
            ),
            _CAT_CORRUPTED: _ps(
                "NovelCorrupted", brand=b,
                fontName="Courier-Oblique",
                fontSize=9,
                textColor=caption,
                alignment=0,
                spaceBefore=6,
                spaceAfter=6,
                leading=13,
            ),
            _CAT_ITALIC_VOICE: _ps(
                "NovelItalicVoice", brand=b,
                fontName=b.get("font_caption", "Times-Italic"),
                fontSize=9.5,
                textColor=body_text,
                leftIndent=18,
                rightIndent=18,
                spaceBefore=8,
                spaceAfter=8,
                leading=13,
            ),
        }

        self._novel_styles = styles
        return styles

    def _classify_block(self, block):
        """
        Classify a parsed block into a narrative category.

        Returns a category string or None (render normally).
        Detection order matters — more specific patterns first.
        """
        btype = block.get("type", "")
        text = block.get("text", "")

        # Blockquotes are always system logs in a novel context
        if btype == "blockquote":
            return _CAT_SYSTEM_LOG

        # Only classify paragraphs
        if btype != "paragraph":
            return None

        if not text or not text.strip():
            return None

        # Strip HTML tags for plain-text pattern matching
        plain = _RE_STRIP_TAGS.sub('', text).strip()

        if not plain:
            return None

        stripped = text.strip()

        # 1. ERASURE: Full italic text that is either all-caps or contains
        #    erasure phrases — the narrative destroying its own characters
        if _RE_FULL_ITALIC.match(stripped):
            italic_content = _RE_STRIP_TAGS.sub('', stripped).strip()

            # All-caps inside italic = chapter markers, structural commands
            if _RE_ITALIC_ALL_CAPS.match(italic_content):
                return _CAT_ERASURE

            # Erasure phrases inside italic = character deletion
            lower = italic_content.lower()
            for phrase in _ERASURE_PHRASES:
                if phrase in lower:
                    return _CAT_ERASURE

            # Otherwise it's a regular italic voice (whisper, notebook)
            return _CAT_ITALIC_VOICE

        # 2. System tags: starts with [ and contains ]
        if plain.startswith('[') and ']' in plain:
            return _CAT_SYSTEM_TAG

        # 3. Corrupted text: contains block character
        if '\u2591' in plain or '\u2591' in text or '░' in text:
            return _CAT_CORRUPTED

        # 4. Arrow sequences: contains ->
        if '->' in plain:
            return _CAT_ARROW_SEQ

        # 5. System commands: entirely uppercase (min 3 chars)
        if len(plain) >= 3 and _RE_ALL_CAPS.match(plain):
            return _CAT_SYSTEM_COMMAND

        # 6. Mixed-case system commands: mostly uppercase with apostrophes/digits
        #    Catches "IF YOU'RE READING THIS, IT'S NOT LEVEL 0."
        if len(plain) >= 10 and _RE_MOSTLY_CAPS.match(plain):
            return _CAT_SYSTEM_COMMAND

        return None

    def _render_novel_block(self, block, category):
        """
        Render a classified block with its narrative style.

        Returns a list of flowables.
        """
        styles = self._build_novel_styles()
        text = block.get("text", "")

        # Arrow sequences use the system command style
        if category == _CAT_ARROW_SEQ:
            category = _CAT_SYSTEM_COMMAND

        style = styles.get(category)
        if style is None:
            return self.render_blocks([block])

        flowables = []

        if category == _CAT_ERASURE:
            # Erasure gets maximum dramatic isolation — the void opening
            flowables.append(Spacer(1, 6 * mm))
            flowables.append(_safe_para(text, style))
            flowables.append(Spacer(1, 6 * mm))
        elif category == _CAT_SYSTEM_COMMAND:
            # System commands get dramatic spacing
            flowables.append(Spacer(1, 3 * mm))
            flowables.append(_safe_para(text, style))
            flowables.append(Spacer(1, 3 * mm))
        else:
            flowables.append(_safe_para(text, style))

        return flowables

    def _build_chapters(self, content):
        """
        Build chapters with narrative-aware block styling.

        Intercepts blocks before render_blocks() and routes
        meta-narrative elements to custom styles. Normal prose
        passes through unchanged.
        """
        subsystems = content.get("subsystems", [])
        chapters = []

        for sub in subsystems:
            chapter_title = sub.get("name", "Chapter")
            chap_flowables = []

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))

            # Extract chapter title from first H1
            for block in blocks:
                if block["type"] == "heading" and block["level"] == 1:
                    chapter_title = block["text"]
                    break

            for block in blocks:
                # Skip H1 headings — rendered by build_story
                if block["type"] == "heading" and block["level"] == 1:
                    continue

                # Classify the block
                category = self._classify_block(block)

                if category is not None:
                    rendered_items = self._render_novel_block(block, category)
                else:
                    rendered_items = self.render_blocks([block])

                # Keep headings with following content
                if block["type"] == "heading":
                    for fl in rendered_items:
                        fl.keepWithNext = True

                chap_flowables.extend(rendered_items)

            chapters.append((chapter_title, chap_flowables))

        return chapters

    def build_story(self, content):
        """
        Override build_story to use continuous flow between Parts.

        Instead of forcing a PageBreak after every Part (which creates
        half-empty pages), the novel template uses CondPageBreak —
        only breaks to a new page if less than 80mm remains. Otherwise
        it inserts a visual separator (rule + spacer) and continues
        flowing on the same page.
        """
        # Delegate front matter to parent
        story = []

        title = content.get("title", self.target_path.name.replace("-", " ").title())
        b = self.brand
        primary = _hex(b, "primary")
        secondary = _hex(b, "secondary")
        caption_c = _hex(b, "caption")
        org = b.get("org", "")
        year = self.date.year
        copyright_str = b.get("copyright", f"\u00a9 {year}")

        from reportlab.pdfbase.pdfmetrics import stringWidth

        # --- Half-title page ---
        cw = getattr(self, 'content_width', CONTENT_WIDTH)
        ht_size = 24
        while stringWidth(title, "Helvetica-Bold", ht_size) > cw * 0.85 and ht_size > 16:
            ht_size -= 1
        half_title_style = _ps(
            "HalfTitle", brand=b,
            fontSize=ht_size, textColor=primary,
            fontName="Helvetica-Bold", alignment=1,
        )
        story.append(Spacer(1, 80 * mm))
        story.append(Paragraph(title, half_title_style))
        story.append(PageBreak())

        # --- Full title page ---
        ft_size = 32
        while stringWidth(title, "Helvetica-Bold", ft_size) > cw * 0.80 and ft_size > 18:
            ft_size -= 1
        title_style = _ps(
            "BookTitle", brand=b,
            fontSize=ft_size, textColor=primary,
            fontName="Helvetica-Bold", alignment=1,
            leading=ft_size + 8,
            spaceAfter=6 * mm,
        )
        subtitle_text = self.config.get("project", {}).get("tagline", "")
        sub_style = _ps(
            "BookSubtitle", brand=b,
            fontSize=16, textColor=secondary,
            fontName="Helvetica-Oblique", alignment=1,
        )
        author_style = _ps(
            "BookAuthor", brand=b,
            fontSize=14, textColor=caption_c, alignment=1,
        )
        story.append(Spacer(1, 50 * mm))
        story.append(Paragraph(title, title_style))
        if subtitle_text:
            story.append(Paragraph(subtitle_text, sub_style))
        story.append(Spacer(1, 20 * mm))
        if org:
            story.append(Paragraph(org, author_style))
        story.append(Spacer(1, 30 * mm))
        story.append(Paragraph(str(year), author_style))
        story.append(PageBreak())

        # --- Copyright page ---
        cp_style = _ps(
            "CopyrightPage", brand=b,
            fontSize=9, textColor=caption_c, leading=14,
        )
        story.append(Spacer(1, 100 * mm))
        story.append(Paragraph(f"First published {year}", cp_style))
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(copyright_str, cp_style))
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(
            "All rights reserved. No part of this publication may be reproduced, "
            "stored in a retrieval system, or transmitted in any form or by any means, "
            "electronic, mechanical, photocopying, recording, or otherwise, without "
            "the prior written permission of the publisher.",
            cp_style,
        ))
        story.append(PageBreak())

        # Pre-build sections
        preface_flowables = self._build_preface(content)
        chapters = self._build_chapters(content)
        glossary_flowables = self._build_glossary(content)

        # --- TOC ---
        story.append(_safe_para("Contents", self.styles["STYLE_H1"]))
        story.append(Spacer(1, 2 * mm))
        toc_entries = [(1, "Preface")]
        for chapter_title, _ in chapters:
            toc_entries.append((1, chapter_title))
        if glossary_flowables:
            toc_entries.append((1, "Glossary"))
        story.extend(build_toc(toc_entries, brand=b, content_width=self.content_width))
        story.append(PageBreak())

        # --- Preface ---
        story.extend(preface_flowables)
        story.append(PageBreak())

        # --- Chapters (continuous flow, no forced page breaks) ---
        for idx, (chapter_title, chapter_flowables) in enumerate(chapters):
            if hasattr(self, '_hf_state'):
                self._hf_state["section"] = chapter_title

            # First chapter: no separator needed (starts after preface)
            # Subsequent chapters: conditional page break — only if less
            # than 80mm remains on the page. Otherwise, visual separator.
            if idx > 0:
                story.append(CondPageBreak(80 * mm))

            story.append(Paragraph(chapter_title, self.styles["STYLE_H1"]))
            story.append(Spacer(1, 2 * mm))
            story.extend(chapter_flowables)

        # Reset running header
        if hasattr(self, '_hf_state'):
            self._hf_state["section"] = content.get("title", "")

        # --- Glossary ---
        if glossary_flowables:
            story.append(PageBreak())
            story.extend(glossary_flowables)

        # --- Colophon ---
        story.append(PageBreak())
        story.extend(self._build_colophon(title, org, year, copyright_str))

        return story

    def _build_colophon(self, title, org, year, copyright_str):
        """
        Build a proper closing page for a novel.
        """
        b = self.brand
        primary = _hex(b, "primary")
        caption = _hex(b, "caption")
        accent = _hex(b, "accent")

        title_style = _ps(
            "ColophonTitle", brand=b,
            fontSize=14, textColor=primary,
            fontName=b.get("font_heading", "Times-Bold"),
            leading=18, alignment=1,
        )
        body_style = _ps(
            "ColophonBody", brand=b,
            fontSize=9, textColor=caption,
            fontName=b.get("font_body", "Times-Roman"),
            leading=14, alignment=1,
        )
        rule_style = _ps(
            "ColophonRule", brand=b,
            fontSize=6, textColor=accent,
            alignment=1,
        )

        flowables = []
        flowables.append(Spacer(1, 60 * mm))
        flowables.append(Paragraph(title, title_style))
        flowables.append(Spacer(1, 8 * mm))
        if org:
            flowables.append(Paragraph(org, body_style))
            flowables.append(Spacer(1, 4 * mm))
        flowables.append(Paragraph(
            "\u2014 \u2014 \u2014",
            rule_style,
        ))
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(Paragraph(copyright_str, body_style))
        flowables.append(Spacer(1, 8 * mm))
        flowables.append(Paragraph(
            f"First edition {year}",
            body_style,
        ))
        return flowables

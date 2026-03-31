"""
briefkit.templates.novel
~~~~~~~~~~~~~~~~~~~~~~~~~
Narrative-aware novel template.

Extends BookTemplate with pattern-based detection and custom styling
for meta-narrative elements common in literary and horror fiction:
system commands, error tags, corrupted text, entity voices, and
metafictional intrusions.

Build order:
  Half Title -> Title Page -> Copyright Page -> TOC -> Preface ->
  Chapters (with narrative-aware block styling) -> Glossary -> Colophon

Design origin:
  Created for The Backrooms: A Jcore Adaptation — a 50,000-word
  metafictional horror novel with 120+ meta-narrative elements
  that require distinct visual treatment from the prose.
"""

from __future__ import annotations

import re

from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import mm

from briefkit.templates.book import BookTemplate
from briefkit.styles import _safe_para, _ps, _hex
from briefkit.extractor import parse_markdown


# Pattern categories
_CAT_SYSTEM_COMMAND = "system_command"
_CAT_SYSTEM_TAG = "system_tag"
_CAT_SYSTEM_LOG = "system_log"
_CAT_CORRUPTED = "corrupted"
_CAT_ARROW_SEQ = "arrow_sequence"
_CAT_ITALIC_VOICE = "italic_voice"

# Regex for detecting all-caps system commands (after HTML tag stripping)
_RE_ALL_CAPS = re.compile(r'^[A-Z][A-Z\s:.\-!,]+$')
# Regex for detecting full-italic paragraphs (after inline formatting)
_RE_FULL_ITALIC = re.compile(r'^<i>.+</i>$', re.DOTALL)
# Regex for stripping HTML tags (for pattern matching on plain text)
_RE_STRIP_TAGS = re.compile(r'<[^>]+>')


class NovelTemplate(BookTemplate):
    """
    Narrative-aware novel template.

    Detects meta-narrative elements in prose and applies distinct
    typographic treatment: system commands in centered monospace,
    error tags with background tint, corrupted text in italic
    monospace, entity voices indented in serif italic.

    All normal prose passes through to the parent BookTemplate's
    render_blocks() unchanged.
    """

    def _build_novel_styles(self):
        """Create and cache the custom narrative styles."""
        if hasattr(self, '_novel_styles'):
            return self._novel_styles

        b = self.brand
        accent = _hex(b, "accent")
        caption = _hex(b, "caption")
        body_text = _hex(b, "body_text")
        code_bg = b.get("code_bg", "#F0EDE6")

        styles = {
            _CAT_SYSTEM_COMMAND: _ps(
                "NovelSystemCmd", brand=b,
                fontName="Courier-Bold",
                fontSize=9,
                textColor=accent,
                alignment=1,
                spaceBefore=14,
                spaceAfter=14,
                leading=14,
            ),
            _CAT_SYSTEM_TAG: _ps(
                "NovelSystemTag", brand=b,
                fontName="Courier",
                fontSize=8,
                textColor=caption,
                backColor=code_bg,
                alignment=0,
                spaceBefore=6,
                spaceAfter=6,
                leftIndent=0,
                leading=12,
            ),
            _CAT_SYSTEM_LOG: _ps(
                "NovelSystemLog", brand=b,
                fontName="Courier",
                fontSize=8,
                textColor=caption,
                backColor=code_bg,
                alignment=0,
                leftIndent=24,
                rightIndent=24,
                spaceBefore=4,
                spaceAfter=4,
                leading=12,
            ),
            _CAT_CORRUPTED: _ps(
                "NovelCorrupted", brand=b,
                fontName="Courier-Oblique",
                fontSize=9,
                textColor=caption,
                alignment=0,
                spaceBefore=4,
                spaceAfter=4,
                leading=13,
            ),
            _CAT_ITALIC_VOICE: _ps(
                "NovelItalicVoice", brand=b,
                fontName=b.get("font_caption", "Times-Italic"),
                fontSize=9.5,
                textColor=body_text,
                leftIndent=18,
                rightIndent=18,
                spaceBefore=4,
                spaceAfter=4,
                leading=13,
            ),
        }

        self._novel_styles = styles
        return styles

    def _classify_block(self, block):
        """
        Classify a parsed block into a narrative category.

        Returns a category string or None (render normally).
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

        # 1. System tags: starts with [ and contains ]
        if plain.startswith('[') and ']' in plain:
            return _CAT_SYSTEM_TAG

        # 2. Corrupted text: contains block character
        if '\u2591' in plain or '░' in text:
            return _CAT_CORRUPTED

        # 3. Arrow sequences: contains ->
        if '->' in plain:
            return _CAT_ARROW_SEQ

        # 4. System commands: entirely uppercase (min 3 chars, not just "I")
        if len(plain) >= 3 and _RE_ALL_CAPS.match(plain):
            return _CAT_SYSTEM_COMMAND

        # 5. Full italic voice: entire paragraph wrapped in <i>...</i>
        stripped = text.strip()
        if _RE_FULL_ITALIC.match(stripped):
            return _CAT_ITALIC_VOICE

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

        # System commands get extra spacing for dramatic pause
        if category == _CAT_SYSTEM_COMMAND:
            flowables.append(Spacer(1, 2 * mm))
            flowables.append(_safe_para(text, style))
            flowables.append(Spacer(1, 2 * mm))
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

    def _build_colophon(self, title, org, year, copyright_str):
        """
        Build the colophon without tooling attribution.

        Novels should end with publisher/copyright only,
        not "Typeset by briefkit."
        """
        cp_style = _ps(
            "Colophon", brand=self.brand,
            fontSize=9, textColor=_hex(self.brand, "caption"),
            leading=14, alignment=1,
        )
        flowables = []
        flowables.append(Spacer(1, 100 * mm))
        flowables.append(Paragraph(title, cp_style))
        if org:
            flowables.append(Paragraph(org, cp_style))
        flowables.append(Paragraph(copyright_str, cp_style))
        return flowables

#!/usr/bin/env python3
"""Complete-edition lectern typesetter — 9 × 12" two-column hardcover.

Renders all 7 volumes + The Scribe into a single lectern Bible:
  - Volume separators (half-title page per volume)
  - Each chapter starts on chapter-banner page
  - Two-column body throughout
  - Asymmetric margins for hardcover binding
  - Full Gothic Orthodox treatment

Usage: typeset-complete-lectern.py <testament-root> <out.pdf>
  where <testament-root> = .../JcoreVerse/The Testament/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from typeset_lectern import (  # noqa: E402
    PAGE_W, PAGE_H, INNER_M, OUTER_M, TOP_M, BOTTOM_M, COL_W, COL_GAP,
    INK, RUBRIC, SUBTLE, RULE,
    FONT_BODY, FONT_BODY_ITALIC, FONT_BODY_BOLD, FONT_FRAKTUR,
    LecternDoc, chapter_to_flowables, smart_quotes, ChapterTitleParagraph,
)
from reportlab.platypus import (
    Paragraph, Spacer, PageBreak, NextPageTemplate,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import mm

VOLUMES = [
    ("1", "I", "The Foundations", "foundations", "Genesis to the descent into Egypt"),
    ("2", "II", "The Liberation", "liberation", "Exodus to the threshold of Canaan"),
    ("3", "III", "The Conquest", "conquest", "Joshua, Judges, Ruth, Samuel"),
    ("4", "IV", "The Kingdom", "kingdom", "David, Solomon, the divided kingdom, Job"),
    ("5", "V", "The Exile", "exile", "Prophets, fall of Jerusalem, return, the silence"),
    ("6", "VI", "The Gospel", "gospel", "The incarnation, the ministry, the cross, the empty tomb"),
    ("7", "VII", "The Fire", "fire", "Pentecost, the church, the apocalypse, the new creation"),
]

# Front matter / volume separator styles
FM_TITLE_STYLE = ParagraphStyle(
    "FMTitle", fontName=FONT_FRAKTUR, fontSize=44, leading=52,
    textColor=INK, alignment=TA_CENTER,
)
FM_VOLNUM_STYLE = ParagraphStyle(
    "FMVolNum", fontName=FONT_FRAKTUR, fontSize=36, leading=44,
    textColor=INK, alignment=TA_CENTER, spaceBefore=20,
)
FM_VOLNAME_STYLE = ParagraphStyle(
    "FMVolName", fontName=FONT_FRAKTUR, fontSize=28, leading=34,
    textColor=INK, alignment=TA_CENTER, spaceBefore=8,
)
FM_SUB_STYLE = ParagraphStyle(
    "FMSub", fontName=FONT_BODY_ITALIC, fontSize=12, leading=16,
    textColor=SUBTLE, alignment=TA_CENTER, spaceBefore=14,
)
FM_AUTHOR_STYLE = ParagraphStyle(
    "FMAuthor", fontName=FONT_BODY, fontSize=12, leading=16,
    textColor=INK, alignment=TA_CENTER, spaceBefore=40,
)
FM_TINY_STYLE = ParagraphStyle(
    "FMTiny", fontName=FONT_BODY, fontSize=9, leading=12,
    textColor=SUBTLE, alignment=TA_LEFT, spaceAfter=4,
)


def build_complete_front_matter():
    """Title page + copyright for the complete edition."""
    fl = []
    # Half-title (recto, page 1)
    fl.append(Spacer(1, PAGE_H * 0.30))
    fl.append(Paragraph("THE TESTAMENT", FM_TITLE_STYLE))
    fl.append(PageBreak())
    # Blank verso (page 2)
    fl.append(Spacer(1, 1)); fl.append(PageBreak())
    # Title page (recto, page 3)
    fl.append(Spacer(1, PAGE_H * 0.20))
    fl.append(Paragraph("THE TESTAMENT", FM_TITLE_STYLE))
    fl.append(Spacer(1, 8))
    fl.append(Paragraph("Complete Edition", FM_SUB_STYLE))
    fl.append(Paragraph("Genesis to Revelation, retold in the first person.", FM_SUB_STYLE))
    fl.append(Paragraph("J. TAYLOR", FM_AUTHOR_STYLE))
    fl.append(Paragraph("PERTH · MMXXVI", FM_SUB_STYLE))
    fl.append(PageBreak())
    # Copyright (verso, page 4)
    fl.append(Spacer(1, PAGE_H * 0.50))
    fl.append(Paragraph("First published 2026 by OFFTRACKMEDIA Studios.", FM_TINY_STYLE))
    fl.append(Paragraph("© 2026 J. Taylor / OFFTRACKMEDIA Studios.", FM_TINY_STYLE))
    fl.append(Paragraph("ABN 84 290 819 896.", FM_TINY_STYLE))
    fl.append(Spacer(1, 8))
    fl.append(Paragraph(
        "All rights reserved. No part of this publication may be reproduced, "
        "stored in a retrieval system, or transmitted in any form or by any "
        "means, electronic, mechanical, photocopying, recording, or otherwise, "
        "without the prior written permission of the publisher.",
        FM_TINY_STYLE,
    ))
    fl.append(Spacer(1, 8))
    fl.append(Paragraph("Set in EB Garamond and Cardo. Display in UnifrakturMaguntia.", FM_TINY_STYLE))
    fl.append(Paragraph("Printed in Australia.", FM_TINY_STYLE))
    fl.append(PageBreak())
    return fl


def build_volume_separator(roman, name, subtitle):
    """Volume divider page content — full-width, centered. Caller appends PageBreaks."""
    fl = []
    fl.append(Spacer(1, PAGE_H * 0.28))
    fl.append(Paragraph(roman, FM_VOLNUM_STYLE))
    fl.append(Paragraph(smart_quotes(name).upper(), FM_VOLNAME_STYLE))
    fl.append(Paragraph(smart_quotes(subtitle), FM_SUB_STYLE))
    return fl


def build_complete_lectern(testament_root, out_path):
    testament_root = Path(testament_root)
    doc = LecternDoc(out_path, volume_title="The Testament — Complete Edition")
    story = [NextPageTemplate(["FrontRecto", "FrontVerso"])
             if hasattr(doc, "_frontmatter_template") else NextPageTemplate("ChapterOpenRecto")]

    # Add no-decoration front-matter templates if not already present
    # Otherwise the front matter pages would have running headers
    # For now, use the chapter-opener template for front matter (no header drawn anyway)
    story = []  # Reset; we'll build properly below

    # Front matter — full-width frames, no decoration
    story.append(NextPageTemplate(["FrontRecto", "FrontVerso"]))
    story.extend(build_complete_front_matter())

    # For each volume: separator + all chapters
    for vol_num, roman, name, folder, subtitle in VOLUMES:
        # Volume separator page — switch to FrontRecto BEFORE the page break
        story.append(NextPageTemplate(["FrontRecto", "FrontVerso"]))
        story.append(PageBreak())  # close current page, start new on FrontRecto
        story.extend(build_volume_separator(roman, name, subtitle))

        # Chapters in this volume — switch to ChapterOpenRecto for the next page
        chapters = sorted((testament_root / f"volume-{vol_num}-the-{folder}").glob("chapter-*.md"))
        for idx, chapter_path in enumerate(chapters):
            banner, body = chapter_to_flowables(chapter_path)
            # Switch to chapter-opener template, then break to a new page for it
            story.append(NextPageTemplate("ChapterOpenRecto"))
            story.append(PageBreak())
            story.append(Spacer(1, 6 * mm))
            story.extend(banner)
            # Switch to body template — body content will flow into body pages after this
            story.append(NextPageTemplate(["BodyRecto", "BodyVerso"]))
            # body already contains cap_flow + overflow + subsequent paragraphs
            # appended by chapter_to_flowables — don't re-process overflow here
            story.extend(body)

    # The Scribe
    scribe_dir = testament_root / "the-scribe"
    if scribe_dir.exists():
        # Scribe section break page
        story.append(NextPageTemplate(["FrontRecto", "FrontVerso"]))
        story.append(PageBreak())
        story.append(Spacer(1, PAGE_H * 0.30))
        story.append(Paragraph("THE SCRIBE", FM_VOLNAME_STYLE))
        # Process scribe files
        scribe_files = sorted(scribe_dir.glob("*.md"))
        for scribe_file in scribe_files:
            banner, body = chapter_to_flowables(scribe_file)
            story.append(NextPageTemplate("ChapterOpenRecto"))
            story.append(PageBreak())
            story.append(Spacer(1, 6 * mm))
            story.extend(banner)
            story.append(NextPageTemplate(["BodyRecto", "BodyVerso"]))
            # body already contains cap_flow + overflow + subsequent paragraphs
            # appended by chapter_to_flowables — don't re-process overflow here
            story.extend(body)

    doc.build(story)


def main():
    if len(sys.argv) != 3:
        print("Usage: typeset-complete-lectern.py <testament-root> <out.pdf>")
        sys.exit(1)
    testament_root, out_path = sys.argv[1:]
    build_complete_lectern(testament_root, out_path)
    print(f"Built {out_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Multi-chapter paperback typesetter — renders a full volume at 5.5 × 8.5".

Imports the per-chapter rendering logic from typeset-paperback.py but adds:
  - Multi-chapter support (list of chapter paths)
  - Each chapter starts on a recto page
  - Front matter: half-title, title page, copyright

Usage:
  typeset-volume-paperback.py <volume-key> <volume-source-dir> <out.pdf>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from typeset_paperback import (  # noqa: E402
    PAGE_W, PAGE_H, INNER_M, OUTER_M, TOP_M, BOTTOM_M,
    INK, RUBRIC, SUBTLE,
    FONT_BODY, FONT_BODY_ITALIC, FONT_BODY_BOLD, FONT_FRAKTUR,
    PaperbackDoc, chapter_to_flowables, smart_quotes,
)
from reportlab.platypus import (
    Paragraph, Spacer, PageBreak, NextPageTemplate,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import mm

# Volume metadata
VOLUMES = {
    "1": ("I", "The Foundations", "Genesis to the descent into Egypt"),
    "2": ("II", "The Liberation", "Exodus to the threshold of Canaan"),
    "3": ("III", "The Conquest", "Joshua, Judges, Ruth, Samuel"),
    "4": ("IV", "The Kingdom", "David, Solomon, the divided kingdom, Job"),
    "5": ("V", "The Exile", "Prophets, fall of Jerusalem, return, the silence"),
    "6": ("VI", "The Gospel", "The incarnation, the ministry, the cross, the empty tomb"),
    "7": ("VII", "The Fire", "Pentecost, the church, the apocalypse, the new creation"),
}

# Front matter styles
HALFTITLE_STYLE = ParagraphStyle(
    "Halftitle", fontName=FONT_FRAKTUR, fontSize=28, leading=34,
    textColor=INK, alignment=TA_CENTER,
)
HALFTITLE_NAME_STYLE = ParagraphStyle(
    "HalftitleName", fontName=FONT_BODY, fontSize=14, leading=18,
    textColor=INK, alignment=TA_CENTER, spaceBefore=8,
)
TITLE_BOOK_STYLE = ParagraphStyle(
    "TitleBook", fontName=FONT_FRAKTUR, fontSize=32, leading=38,
    textColor=INK, alignment=TA_CENTER,
)
TITLE_VOL_STYLE = ParagraphStyle(
    "TitleVol", fontName=FONT_FRAKTUR, fontSize=24, leading=28,
    textColor=INK, alignment=TA_CENTER, spaceBefore=18,
)
TITLE_NAME_STYLE = ParagraphStyle(
    "TitleName", fontName=FONT_BODY, fontSize=14, leading=18,
    textColor=INK, alignment=TA_CENTER, spaceBefore=6,
)
TITLE_SUB_STYLE = ParagraphStyle(
    "TitleSub", fontName=FONT_BODY_ITALIC, fontSize=11, leading=14,
    textColor=SUBTLE, alignment=TA_CENTER, spaceBefore=8,
)
TITLE_AUTHOR_STYLE = ParagraphStyle(
    "TitleAuthor", fontName=FONT_BODY, fontSize=11, leading=14,
    textColor=INK, alignment=TA_CENTER, spaceBefore=24,
)
COPYRIGHT_STYLE = ParagraphStyle(
    "Copyright", fontName=FONT_BODY, fontSize=8.5, leading=12,
    textColor=SUBTLE, alignment=TA_LEFT, spaceAfter=4,
)


def build_front_matter(roman, name, subtitle):
    """Build front-matter flowables: half-title, title page, copyright."""
    fl = []
    # Half-title page (recto)
    fl.append(Spacer(1, PAGE_H * 0.30))
    fl.append(Paragraph(roman, HALFTITLE_STYLE))
    fl.append(Paragraph(smart_quotes(name).upper(), HALFTITLE_NAME_STYLE))
    fl.append(PageBreak())
    # Verso blank (page 2)
    fl.append(Spacer(1, 1))
    fl.append(PageBreak())
    # Title page (page 3, recto)
    fl.append(Spacer(1, PAGE_H * 0.18))
    fl.append(Paragraph("THE TESTAMENT", TITLE_SUB_STYLE))
    fl.append(Spacer(1, 8))
    fl.append(Paragraph(roman, TITLE_BOOK_STYLE))
    fl.append(Paragraph(smart_quotes(name).upper(), TITLE_VOL_STYLE))
    fl.append(Spacer(1, 14))
    if subtitle:
        fl.append(Paragraph(smart_quotes(subtitle), TITLE_SUB_STYLE))
    fl.append(Paragraph("J. TAYLOR", TITLE_AUTHOR_STYLE))
    fl.append(Paragraph("PERTH · MMXXVI", TITLE_SUB_STYLE))
    fl.append(PageBreak())
    # Copyright page (page 4, verso)
    fl.append(Spacer(1, PAGE_H * 0.55))
    fl.append(Paragraph("First published 2026 by OFFTRACKMEDIA Studios.", COPYRIGHT_STYLE))
    fl.append(Spacer(1, 4))
    fl.append(Paragraph("© 2026 J. Taylor / OFFTRACKMEDIA Studios.", COPYRIGHT_STYLE))
    fl.append(Paragraph("ABN 84 290 819 896.", COPYRIGHT_STYLE))
    fl.append(Spacer(1, 8))
    fl.append(Paragraph(
        "All rights reserved. No part of this publication may be reproduced, "
        "stored in a retrieval system, or transmitted in any form or by any "
        "means, electronic, mechanical, photocopying, recording, or otherwise, "
        "without the prior written permission of the publisher.",
        COPYRIGHT_STYLE,
    ))
    fl.append(Spacer(1, 8))
    fl.append(Paragraph("Set in EB Garamond and Cardo. Display in UnifrakturMaguntia.",
                        COPYRIGHT_STYLE))
    fl.append(Paragraph("Printed in Australia.", COPYRIGHT_STYLE))
    fl.append(PageBreak())
    return fl


def build_volume_pdf(volume_key, source_dir, out_path):
    roman, name, subtitle = VOLUMES[volume_key]
    volume_title_full = f"Volume {roman} — {name}"

    chapters = sorted(Path(source_dir).glob("chapter-*.md"))
    if not chapters:
        raise SystemExit(f"No chapter-*.md files in {source_dir}")

    doc = PaperbackDoc(out_path, volume_title=volume_title_full)
    story = [NextPageTemplate(["FrontRecto", "FrontVerso"])]
    story.extend(build_front_matter(roman, name, subtitle))
    # Body — switch to body template
    story.append(NextPageTemplate(["BodyRecto", "BodyVerso"]))
    for idx, chapter_path in enumerate(chapters):
        flowables = chapter_to_flowables(str(chapter_path))
        story.extend(flowables)
        if idx < len(chapters) - 1:
            story.append(PageBreak())
    doc.build(story)


def main():
    if len(sys.argv) != 4:
        print("Usage: typeset-volume-paperback.py <volume-key> <source-dir> <out.pdf>")
        sys.exit(1)
    volume_key, source_dir, out_path = sys.argv[1:]
    build_volume_pdf(volume_key, source_dir, out_path)
    print(f"Built {out_path}")


if __name__ == "__main__":
    main()

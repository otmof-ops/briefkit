"""
briefkit.presets.colors
~~~~~~~~~~~~~~~~~~~~~~~~
All built-in color scheme presets.

Each preset defines seven hex color values:
  primary     — dominant brand color (headers, cover, accents)
  secondary   — supporting brand color (sub-headers, links)
  accent      — highlight / call-out color
  body_text   — main body copy color
  caption     — captions, footnotes, supporting text
  background  — page / panel background
  rule        — horizontal rules, table borders, dividers
"""

from __future__ import annotations

PRESETS: dict[str, dict[str, str]] = {
    "navy": {
        "primary": "#1B2A4A",
        "secondary": "#2E86AB",
        "accent": "#E8C547",
        "body_text": "#2C2C2C",
        "caption": "#666666",
        "background": "#FFFFFF",
        "rule": "#CCCCCC",
    },
    "charcoal": {
        "primary": "#2D2D2D",
        "secondary": "#5C8A97",
        "accent": "#D4A853",
        "body_text": "#333333",
        "caption": "#777777",
        "background": "#FFFFFF",
        "rule": "#DDDDDD",
    },
    "ocean": {
        "primary": "#0A2463",
        "secondary": "#1E96FC",
        "accent": "#FFC600",
        "body_text": "#1A1A2E",
        "caption": "#5A5A7A",
        "background": "#FFFFFF",
        "rule": "#D0D0E0",
    },
    "forest": {
        "primary": "#1B4332",
        "secondary": "#40916C",
        "accent": "#D4A373",
        "body_text": "#2D3A2D",
        "caption": "#6B7F6B",
        "background": "#FFFFFF",
        "rule": "#C8D5C8",
    },
    "crimson": {
        "primary": "#590D22",
        "secondary": "#A4133C",
        "accent": "#FFCCD5",
        "body_text": "#2B2B2B",
        "caption": "#6D6D6D",
        "background": "#FFFFFF",
        "rule": "#D4D4D4",
    },
    "slate": {
        "primary": "#37474F",
        "secondary": "#607D8B",
        "accent": "#80CBC4",
        "body_text": "#263238",
        "caption": "#78909C",
        "background": "#FFFFFF",
        "rule": "#CFD8DC",
    },
    "royal": {
        "primary": "#2D1B69",
        "secondary": "#7B2FBE",
        "accent": "#FFD700",
        "body_text": "#1A1A2E",
        "caption": "#6A6A8A",
        "background": "#FFFFFF",
        "rule": "#D8D0E8",
    },
    "sunset": {
        "primary": "#3D1C02",
        "secondary": "#E85D04",
        "accent": "#FAA307",
        "body_text": "#2C1810",
        "caption": "#7A6A5A",
        "background": "#FFFCF7",
        "rule": "#E0D4C4",
    },
    "mono": {
        "primary": "#000000",
        "secondary": "#333333",
        "accent": "#F0F0F0",
        "body_text": "#000000",
        "caption": "#555555",
        "background": "#FFFFFF",
        "rule": "#AAAAAA",
    },
    "midnight": {
        "primary": "#E0E0E0",
        "secondary": "#64B5F6",
        "accent": "#FFE082",
        "body_text": "#D0D0D0",
        "caption": "#909090",
        "background": "#121212",
        "rule": "#333333",
    },
}

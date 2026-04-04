"""
briefkit.variants.gaming — Game reverse-engineering / game development variant.

Adds: engine architecture relationship diagram (or component table),
file format reference table, renderer pipeline summary.
"""

from __future__ import annotations

import re

from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Spacer

from briefkit.elements.tables import build_data_table
from briefkit.styles import _safe_para
from briefkit.variants import DocSetVariant, _register, collect_text

# Known game engine / graphics file extensions
_FILE_EXTENSIONS = [
    ".pak", ".bsa", ".esm", ".esp", ".esl", ".ba2",
    ".nif", ".dds", ".tga", ".png", ".ktx",
    ".psa", ".psk", ".upk", ".uasset", ".umap",
    ".fbx", ".obj", ".gltf", ".glb",
    ".bak", ".sav", ".dat", ".bin",
    ".shader", ".hlsl", ".glsl", ".vert", ".frag",
]

# Known game engines
_ENGINE_PATTERNS = [
    (r'\bUnreal\s+Engine\b|\bUE[45]\b', "Unreal Engine"),
    (r'\bUnity\b',                       "Unity"),
    (r'\bGodot\b',                       "Godot"),
    (r'\bCreation\s+Engine\b|\bGamebryo\b', "Creation Engine / Gamebryo"),
    (r'\bFrostbite\b',                   "Frostbite"),
    (r'\bCryEngine\b|\bCRY\b',           "CryEngine"),
    (r'\bSource\s+Engine\b|\bSource\s+2\b', "Source Engine"),
    (r'\bIDTech\b|id\s+Tech\b',          "id Tech"),
    (r'\bAnvil(?:\s+Next)?\b',           "Anvil / AnvilNext"),
    (r'\bREDengine\b',                   "REDengine"),
]


@_register
class GamingVariant(DocSetVariant):
    """Game reverse-engineering / game development variant."""

    name = "gaming"
    auto_detect_keywords = [
        "engine", "shader", "mesh", "texture",
        ".pak", ".bsa", "renderer", "polygon",
    ]

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        all_content = collect_text(content)

        flowables.append(PageBreak())
        flowables.append(_safe_para("Game Reverse Engineering Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Engine identification ---
        flowables.append(_safe_para("Engine Identification", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        engine_rows = []
        for pattern, engine_name in _ENGINE_PATTERNS:
            if re.search(pattern, all_content, re.IGNORECASE):
                engine_rows.append([engine_name, "Detected", ""])

        if engine_rows:
            flowables.extend(build_data_table(
                ["Engine", "Status", "Notes"],
                engine_rows,
                title="Detected Engines",
                brand=brand,
            ))

        # --- Engine architecture ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Engine Architecture", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        subsystem_names = [s["name"][:24] for s in content.get("subsystems", [])[:8]]
        title_name = content.get("title", "Engine")[:24]

        if subsystem_names:
            # Relationship diagram as a component table
            arch_rows = [[comp, "Subsystem", ""] for comp in subsystem_names]
            flowables.extend(build_data_table(
                ["Component", "Type", "Notes"],
                arch_rows,
                title=f"Architecture Components — {title_name}",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Subsystem architecture — see numbered deep-dive files.", s_body
            ))

        # --- File formats ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("File Formats and Data Structures", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        format_rows = self._extract_file_formats(content, all_content)
        if format_rows:
            flowables.extend(build_data_table(
                ["Format / Extension", "Description", "Notes"],
                format_rows[:15],
                title="Data Format Reference",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "File format information not found in structured form — see numbered deep-dive files.",
                s_body,
            ))

        # --- Renderer pipeline ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Renderer Pipeline", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        pipeline_rows = self._extract_pipeline(all_content)
        if pipeline_rows:
            flowables.extend(build_data_table(
                ["Stage", "Description"],
                pipeline_rows,
                title="Renderer Pipeline Stages",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Renderer pipeline details — see numbered deep-dive files.", s_body
            ))

        return flowables

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_file_formats(self, content, all_content):
        found = []
        seen = set()
        all_lower = all_content.lower()

        # Scan known extensions
        for ext in _FILE_EXTENSIONS:
            if ext.lower() in all_lower and ext not in seen:
                found.append([ext, "Game data file", ""])
                seen.add(ext)

        # Scan subsystem tables for format data
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_low = [h.lower() for h in tbl.get("headers", [])]
                if any(k in " ".join(headers_low) for k in ("format", "extension", "file type", "filetype")):
                    for row in tbl.get("rows", [])[:8]:
                        if row and row[0] not in seen:
                            padded = (list(row) + ["", "", ""])[:3]
                            found.append(padded)
                            seen.add(row[0])

        return found

    def _extract_pipeline(self, all_content):
        pipeline_kw_map = [
            (r'\bvertex\s+shader\b',           "Vertex Shader"),
            (r'\btessellation\b',               "Tessellation"),
            (r'\bgeometry\s+shader\b',          "Geometry Shader"),
            (r'\brasteriz(?:ation|er)\b',       "Rasterization"),
            (r'\bfragment\s+shader\b|\bpixel\s+shader\b', "Fragment / Pixel Shader"),
            (r'\bdepth\s+(?:buffer|test)\b',    "Depth Test"),
            (r'\bstencil\b',                    "Stencil Test"),
            (r'\bblend(?:ing)?\b',              "Blending"),
            (r'\bpost.?process(?:ing)?\b',      "Post-Processing"),
            (r'\bcompute\s+shader\b',           "Compute Shader"),
            (r'\bray\s+trac(?:ing|er)\b',       "Ray Tracing"),
            (r'\bdeferred\s+render(?:ing)?\b',  "Deferred Rendering"),
            (r'\bforward\s+render(?:ing)?\b',   "Forward Rendering"),
        ]
        rows = []
        seen = set()
        for pat, label in pipeline_kw_map:
            if re.search(pat, all_content, re.IGNORECASE) and label not in seen:
                rows.append([label, "Detected in source"])
                seen.add(label)
        return rows

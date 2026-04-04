"""
briefkit.variants.hardware — Embedded hardware / microcontroller variant.

Adds: pin/GPIO reference table, register map, electrical specifications,
boot sequence (from firmware keywords).
"""

from __future__ import annotations

import re

from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Spacer

from briefkit.elements.tables import build_data_table
from briefkit.styles import _safe_para
from briefkit.variants import DocSetVariant, _register, collect_text

# Electrical unit pattern
_ELEC_UNIT_PAT = re.compile(
    r'\b\d+(?:\.\d+)?\s*(?:V|mV|A|mA|µA|uA|W|mW|Ω|ohm|kΩ|MHz|kHz|GHz|pF|nF|µF|uF)\b',
    re.IGNORECASE,
)

# Hex address pattern
_HEX_PAT = re.compile(r'(0x[0-9a-fA-F]{4,8})\s+([A-Za-z][A-Za-z0-9_\s]{2,30})')

# Memory region keywords
_REGION_KW = re.compile(
    r'\b(?:SRAM|DRAM|Flash|ROM|EEPROM|SDRAM|IRAM|Cache|Peripheral|Register|CSR)\b',
    re.IGNORECASE,
)

# GPIO / pin header keywords
_PIN_HEADERS = {"pin", "gpio", "port", "signal", "function", "direction", "io", "pad"}

# Register map header keywords
_REG_HEADERS = {"register", "offset", "address", "bit", "field", "mask", "reg", "csr"}

# Boot sequence keyword map
_BOOT_KW_MAP = [
    (r'\b(?:BIOS|UEFI)\b',                 "BIOS / UEFI Initialisation"),
    (r'\bsecure\s*boot\b',                 "Secure Boot Verification"),
    (r'\bSPL\b|secondary\s+program\s+loader', "SPL (Secondary Program Loader)"),
    (r'\bTPL\b|tertiary\s+program\s+loader',  "TPL (Tertiary Program Loader)"),
    (r'\b(?:U-Boot|u-boot)\b',             "U-Boot Bootloader"),
    (r'\bGRUB\b',                          "GRUB Bootloader"),
    (r'\bstage\s+1\b',                     "Stage 1 Bootloader"),
    (r'\bstage\s+2\b',                     "Stage 2 Bootloader"),
    (r'\binitramfs\b',                     "initramfs Loading"),
    (r'\bkernel\b',                        "Kernel Handoff"),
    (r'\bsystemd\b|\binit\b',              "System Init (systemd / init)"),
    (r'\bdevice\s+tree\b|\bDTB\b',         "Device Tree Blob (DTB)"),
    (r'\bpower.on\s+reset\b|\bPOR\b',      "Power-On Reset"),
]


@_register
class HardwareVariant(DocSetVariant):
    """Embedded hardware / microcontroller domain variant."""

    name = "hardware"
    auto_detect_keywords = [
        "register", "GPIO", "voltage", "datasheet",
        "pinout", "microcontroller", "firmware",
    ]

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        all_content = collect_text(content)

        flowables.append(PageBreak())
        flowables.append(_safe_para("Hardware Profile Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Pin / GPIO reference ---
        flowables.append(_safe_para("Pin and GPIO Reference", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        pin_rows = self._extract_pin_table(content, all_content)
        if pin_rows:
            flowables.extend(build_data_table(
                ["Pin / GPIO", "Signal / Function", "Direction", "Notes"],
                pin_rows[:20],
                title="Pin Reference",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Pin / GPIO reference not found in structured form — see datasheet.", s_body
            ))

        # --- Register map ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Register Map", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        reg_rows = self._extract_register_map(content, all_content)
        if reg_rows:
            flowables.extend(build_data_table(
                ["Register / Region", "Base Address", "Size", "Description"],
                reg_rows[:12],
                title="Memory / Register Map",
                brand=brand,
            ))
        else:
            flowables.extend(build_data_table(
                ["Register / Region", "Base Address", "Size", "Description"],
                [["See source documentation", "—", "—", ""]],
                title="Memory / Register Map",
                brand=brand,
            ))

        # --- Electrical specifications ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Electrical Specifications", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        elec_rows = self._extract_electrical_specs(content, all_content)
        if elec_rows:
            flowables.extend(build_data_table(
                ["Parameter", "Value", "Notes"],
                elec_rows[:12],
                title="Electrical Specifications",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Electrical specifications not found in structured form — see datasheet.", s_body
            ))

        # --- Boot sequence ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Boot Sequence", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        boot_stages = self._extract_boot_sequence(all_content)
        if boot_stages:
            boot_rows = [[f"{i + 1}. {stage}", ""] for i, stage in enumerate(boot_stages)]
            flowables.extend(build_data_table(
                ["Boot Stage", "Notes"],
                boot_rows,
                title="Detected Boot Sequence",
                brand=brand,
            ))
        else:
            flowables.extend(build_data_table(
                ["Boot Stage", "Notes"],
                [
                    ["1. Power On / Reset", ""],
                    ["2. Stage 1 Bootloader", ""],
                    ["3. Hardware Initialisation", ""],
                    ["4. Stage 2 Bootloader", ""],
                    ["5. Kernel / OS Handoff", ""],
                ],
                title="Generic Boot Sequence — see source documents for device specifics",
                brand=brand,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_pin_table(self, content, all_content):
        rows = []
        seen = set()

        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_low = [h.lower() for h in tbl.get("headers", [])]
                if any(h in _PIN_HEADERS for h in headers_low):
                    for row in tbl.get("rows", [])[:16]:
                        padded = (list(row) + ["", "", "", ""])[:4]
                        key = str(padded[0]).lower()
                        if key not in seen:
                            rows.append(padded)
                            seen.add(key)

        if rows:
            return rows

        # Scan inline for GPIO pin patterns: "PA5", "GPIO5", "Pin 10"
        pin_pat = re.compile(
            r'\b(?:GPIO|PA|PB|PC|PD|PE|PF|PG|P[0-9])[\s_]?([0-9]{1,2})\b|'
            r'\bPin\s+(\d{1,3})\b',
            re.IGNORECASE,
        )
        for m in pin_pat.finditer(all_content):
            (m.group(1) or m.group(2) or "").strip()
            matched = m.group(0).strip()
            if matched not in seen:
                rows.append([matched, "—", "—", ""])
                seen.add(matched)

        return rows

    def _extract_register_map(self, content, all_content):
        rows = []
        seen = set()

        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_low = [h.lower() for h in tbl.get("headers", [])]
                if any(h in _REG_HEADERS for h in headers_low):
                    for row in tbl.get("rows", [])[:10]:
                        padded = (list(row) + ["", "", "", ""])[:4]
                        key = str(padded[0]).lower()
                        if key not in seen:
                            rows.append(padded)
                            seen.add(key)

        if rows:
            return rows

        # Scan for hex address + region name
        for m in _HEX_PAT.finditer(all_content):
            addr, label = m.group(1), m.group(2).strip()
            if addr not in seen and _REGION_KW.search(label):
                rows.append([label, addr, "—", ""])
                seen.add(addr)

        return rows

    def _extract_electrical_specs(self, content, all_content):
        rows = []
        seen = set()

        # Structured tables with electrical units
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                rows_tbl = tbl.get("rows", [])
                for row in rows_tbl[:10]:
                    row_str = " ".join(str(c) for c in row)
                    if _ELEC_UNIT_PAT.search(row_str):
                        key = str(row[0])[:30].lower() if row else ""
                        if key and key not in seen:
                            padded = (list(row) + ["", ""])[:3]
                            rows.append(padded)
                            seen.add(key)

        if rows:
            return rows

        # Scan inline
        spec_pat = re.compile(
            r'([A-Za-z][A-Za-z\s_]{2,30})\s*[:\=]\s*'
            r'(\d+(?:\.\d+)?\s*(?:V|mV|A|mA|W|mW|MHz|kHz|GHz|pF|nF|µF))',
            re.IGNORECASE,
        )
        for m in spec_pat.finditer(all_content):
            param = m.group(1).strip()
            value = m.group(2).strip()
            key = param.lower()
            if key not in seen and len(param) < 50:
                rows.append([param, value, ""])
                seen.add(key)

        return rows

    def _extract_boot_sequence(self, all_content):
        stages = []
        seen = set()
        for pat, label in _BOOT_KW_MAP:
            if re.search(pat, all_content, re.IGNORECASE) and label not in seen:
                stages.append(label)
                seen.add(label)
        return stages

"""
briefkit.variants.religion — Religious tradition variant.

Adds: key concepts table, branches and denominations table,
theological positions comparison (neutral, descriptive framing).
"""

from __future__ import annotations

import re

from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Spacer

from briefkit.elements.callout import build_callout_box
from briefkit.elements.tables import build_data_table
from briefkit.styles import _safe_para
from briefkit.variants import DocSetVariant, _register, collect_text

_NEUTRALITY_NOTICE = (
    "This section presents religious traditions in descriptive, neutral terms for "
    "educational purposes only. All traditions are treated with equal scholarly respect. "
    "Descriptions reflect academic literature; doctrinal claims are attributed to "
    "the relevant tradition rather than asserted as fact."
)

# Religion-relevant concept keywords
_RELIGION_KW = {
    "theology", "scripture", "ritual", "sacred", "prayer", "worship",
    "salvation", "dharma", "karma", "samsara", "nirvana", "torah", "quran",
    "bible", "hadith", "sutra", "prophet", "saint", "deity", "monotheism",
    "polytheism", "denomination", "sect", "schism", "doctrine", "dogma",
    "faith", "creed", "covenant", "church", "mosque", "temple", "synagogue",
    "pilgrimage", "sacrament", "meditation", "enlightenment", "resurrection",
    "revelation", "incarnation", "trinity", "communion", "baptism",
    "afterlife", "soul", "sin", "grace", "reincarnation", "nirvana",
    "purgatory", "heaven", "hell", "ordained", "clergy", "laity",
}

# Known denomination / branch names
_DENOM_PAT = re.compile(
    r'\b(Protestant|Catholic|Orthodox|Sunni|Shia|Sufi|Theravada|Mahayana|'
    r'Vajrayana|Ashkenazi|Sephardi|Hasidic|Reform|Conservative|Baptist|'
    r'Methodist|Lutheran|Anglican|Presbyterian|Evangelical|Pentecostal|'
    r'Wahhabi|Salafi|Ismaili|Ahmadiyya|Druze|Alawi|Quaker|Mennonite|'
    r'Coptic|Syriac|Maronite|Chaldean|Armenian|Ethiopian)\b',
    re.IGNORECASE,
)

# Canonical / scripture names
_SCRIPTURE_PAT = re.compile(
    r'\b(Bible|Quran|Torah|Talmud|Tanakh|Vedas?|Upanishads?|Bhagavad\s+Gita|'
    r'Pali\s+Canon|Tripitaka|Guru\s+Granth\s+Sahib|Book\s+of\s+Mormon|'
    r'Avesta|Dao\s+De\s+Jing|Analects|Hadith|Mishnah)\b',
    re.IGNORECASE,
)

# Major tradition names
_TRADITION_PAT = re.compile(
    r'\b(Christianity|Islam|Judaism|Buddhism|Hinduism|Sikhism|Zoroastrianism|'
    r'Jainism|Taoism|Confucianism|Shinto|Baha\'i|Animism|Paganism)\b',
    re.IGNORECASE,
)


@_register
class ReligionVariant(DocSetVariant):
    """Religious tradition domain variant."""

    name = "religion"
    auto_detect_keywords = [
        "theology", "scripture", "doctrine", "worship",
        "denomination", "liturgy", "canon",
    ]

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        all_content = collect_text(content)
        all_terms = content.get("terms", {})

        # Prepend neutrality notice
        flowables.insert(0, build_callout_box(_NEUTRALITY_NOTICE, "insight", brand))

        flowables.append(PageBreak())
        flowables.append(_safe_para("Religious Tradition Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Traditions identified ---
        flowables.append(_safe_para("Traditions Covered", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        tradition_rows = []
        seen_traditions = set()
        for m in _TRADITION_PAT.finditer(all_content):
            name = m.group(1).title()
            if name not in seen_traditions:
                tradition_rows.append([name, "Referenced", ""])
                seen_traditions.add(name)

        if tradition_rows:
            flowables.extend(build_data_table(
                ["Tradition", "Status", "Notes"],
                tradition_rows,
                title="Religious Traditions Referenced",
                brand=brand,
            ))

        # --- Key concepts ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Key Concepts", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        religion_terms = self._extract_key_concepts(all_content, all_terms)
        if religion_terms:
            flowables.extend(build_data_table(
                ["Concept", "Description"],
                [[t, "—"] for t in religion_terms],
                title="Core Concepts and Terminology",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para("Key concepts — see source documents.", s_body))

        # --- Branches and denominations ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Branches and Denominations", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        denom_rows = []
        seen_denoms = set()
        for m in _DENOM_PAT.finditer(all_content):
            name = m.group(1).title()
            if name not in seen_denoms:
                denom_rows.append([name, "—", "—"])
                seen_denoms.add(name)

        if denom_rows:
            flowables.extend(build_data_table(
                ["Branch / Denomination", "Key Distinction", "Geographic Spread"],
                denom_rows[:12],
                title="Branches Overview",
                brand=brand,
            ))
        else:
            flowables.extend(build_data_table(
                ["Branch / Denomination", "Key Distinction", "Geographic Spread"],
                [["See source documents", "—", ""]],
                title="Branches Overview",
                brand=brand,
            ))

        # --- Scripture reference ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Scripture and Canonical Texts", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        scripture_rows = []
        seen_scripts = set()
        for m in _SCRIPTURE_PAT.finditer(all_content):
            name = m.group(1).strip()
            if name not in seen_scripts:
                scripture_rows.append([name, "Referenced", ""])
                seen_scripts.add(name)

        if scripture_rows:
            flowables.extend(build_data_table(
                ["Text", "Status", "Notes"],
                scripture_rows,
                title="Canonical Texts Referenced",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "No canonical texts identified — see source documents.", s_body
            ))

        return flowables

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_key_concepts(self, all_content, all_terms):
        religion_terms = []
        # From the content's term glossary (if populated)
        for t in all_terms:
            if any(kw in t.lower() for kw in _RELIGION_KW):
                religion_terms.append(t)

        # Supplement with direct keyword matches from prose
        for kw in _RELIGION_KW:
            if re.search(r'\b' + re.escape(kw) + r'\b', all_content, re.IGNORECASE):
                cap_kw = kw.title()
                if cap_kw not in religion_terms:
                    religion_terms.append(cap_kw)

        return religion_terms[:12]

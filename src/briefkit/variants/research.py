"""
briefkit.variants.research — Academic research variant.

Adds: methodology summary table, dataset description table,
reproducibility checklist callout.
"""

from __future__ import annotations

import re

from reportlab.platypus import PageBreak, Spacer

from briefkit.styles import _safe_para, build_styles
from briefkit.elements.tables import build_data_table
from briefkit.elements.callout import build_callout_box
from briefkit.variants import DocSetVariant, _register, collect_text

from reportlab.lib.units import mm

# Common research methodology terms
_METHODOLOGY_TERMS = {
    "qualitative", "quantitative", "mixed methods", "ethnography",
    "grounded theory", "phenomenology", "case study", "survey",
    "experiment", "quasi-experimental", "longitudinal", "cross-sectional",
    "randomized controlled trial", "systematic review", "meta-analysis",
    "content analysis", "discourse analysis", "thematic analysis",
}

# Dataset / corpus markers
_DATASET_HEADERS = {"dataset", "corpus", "data source", "benchmark", "collection", "training set"}

# Reproducibility checklist items
_REPRO_CHECKLIST = [
    "Source code available (link or repository referenced in document)",
    "Dataset available or access instructions provided",
    "Random seeds and initialisation conditions documented",
    "Hardware and software environment described",
    "Statistical tests and significance thresholds stated",
    "Pre-registration or registered report protocol noted",
    "Data preprocessing steps documented",
    "Evaluation metrics defined with formulae or citations",
]


@_register
class ResearchVariant(DocSetVariant):
    """Academic research domain variant."""

    name = "research"
    auto_detect_keywords = [
        "hypothesis", "methodology", "sample size", "p-value",
        "dataset", "reproducibility",
    ]

    def build_variant_sections(self, content, flowables, styles, brand):
        s_h1   = styles["STYLE_H1"]
        s_h2   = styles["STYLE_H2"]
        s_body = styles["STYLE_BODY"]

        all_content = collect_text(content)

        flowables.append(PageBreak())
        flowables.append(_safe_para("Research Variant Sections", s_h1))
        flowables.append(Spacer(1, 3 * mm))

        # --- Methodology summary ---
        flowables.append(_safe_para("Methodology Summary", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        meth_rows = self._extract_methodology(content, all_content)
        if meth_rows:
            flowables.extend(build_data_table(
                ["Aspect", "Detail"],
                meth_rows,
                title="Methodology Overview",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Methodology details not found in structured form — see numbered documents.",
                s_body,
            ))

        # --- Dataset description ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Dataset Description", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        dataset_rows = self._extract_datasets(content, all_content)
        if dataset_rows:
            flowables.extend(build_data_table(
                ["Dataset / Corpus", "Size / Split", "Source", "Notes"],
                dataset_rows[:10],
                title="Datasets Referenced",
                brand=brand,
            ))
        else:
            flowables.append(_safe_para(
                "Dataset information not found in structured form — see numbered documents.",
                s_body,
            ))

        # --- Reproducibility checklist ---
        flowables.append(Spacer(1, 4 * mm))
        flowables.append(_safe_para("Reproducibility Checklist", s_h2))
        flowables.append(Spacer(1, 2 * mm))

        found_items, missing_items = self._check_reproducibility(all_content)

        if found_items or missing_items:
            lines = []
            for item in found_items:
                lines.append(f"- [present] {item}")
            for item in missing_items:
                lines.append(f"- [not detected] {item}")
            flowables.append(build_callout_box("\n".join(lines), "insight", brand))
        else:
            checklist_text = "\n".join(f"- {item}" for item in _REPRO_CHECKLIST)
            flowables.append(build_callout_box(
                "Verify the following for reproducibility:\n" + checklist_text,
                "insight",
                brand,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_methodology(self, content, all_content):
        rows = []

        # Check structured tables first
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_low = [h.lower() for h in tbl.get("headers", [])]
                if any(k in " ".join(headers_low) for k in ("methodology", "method", "approach", "design")):
                    for row in tbl.get("rows", [])[:6]:
                        padded = (list(row) + [""])[:2]
                        rows.append(padded)

        if rows:
            return rows

        # Detect methodology terms from prose
        detected_methods = []
        for term in _METHODOLOGY_TERMS:
            if term in all_content.lower():
                detected_methods.append(term.title())

        # Sample size
        sample_m = re.search(r'n\s*=\s*(\d[\d,]+)', all_content, re.IGNORECASE)
        if sample_m:
            rows.append(["Sample Size", f"n = {sample_m.group(1)}"])

        # p-value threshold
        p_m = re.search(r'(?:p\s*[<>=]\s*)(0\.\d+)', all_content, re.IGNORECASE)
        if p_m:
            rows.append(["Significance Threshold", f"p {p_m.group(0).split('p')[-1].strip()}"])

        # Research design
        if detected_methods:
            rows.append(["Research Design", ", ".join(detected_methods[:4])])

        # Duration / follow-up
        dur_m = re.search(
            r'(?:follow.?up|duration|study\s+period)[:\s]+(\d[\d\s]*(?:weeks?|months?|years?))',
            all_content, re.IGNORECASE,
        )
        if dur_m:
            rows.append(["Study Duration", dur_m.group(1).strip()])

        return rows

    def _extract_datasets(self, content, all_content):
        rows = []
        seen = set()

        # Scan structured tables
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_low = [h.lower() for h in tbl.get("headers", [])]
                if any(h in _DATASET_HEADERS for h in headers_low):
                    for row in tbl.get("rows", [])[:8]:
                        padded = (list(row) + ["", "", "", ""])[:4]
                        key = str(padded[0]).lower()
                        if key not in seen:
                            rows.append(padded)
                            seen.add(key)

        if rows:
            return rows

        # Scan inline for named datasets (common patterns)
        ds_pat = re.compile(
            r'\b([A-Z][A-Za-z0-9\-]+(?:\s+[A-Za-z0-9]+)?)\s+'
            r'(?:dataset|corpus|benchmark|database|collection)',
            re.IGNORECASE,
        )
        for m in ds_pat.finditer(all_content):
            name = m.group(1).strip()
            key = name.lower()
            if key not in seen and len(name) < 50:
                rows.append([name, "—", "—", ""])
                seen.add(key)

        return rows

    def _check_reproducibility(self, all_content):
        repro_patterns = {
            "Source code available (link or repository referenced in document)": [
                r'github\.com|gitlab\.com|bitbucket\.org|source\s+code|repository',
            ],
            "Dataset available or access instructions provided": [
                r'dataset\s+available|data\s+available|download\s+at|access\s+at',
            ],
            "Random seeds and initialisation conditions documented": [
                r'random\s+seed|seed\s*=\s*\d|torch\.manual_seed|numpy\.random\.seed',
            ],
            "Hardware and software environment described": [
                r'GPU|NVIDIA|CPU|RAM|Python\s+\d|PyTorch|TensorFlow|CUDA',
            ],
            "Statistical tests and significance thresholds stated": [
                r'p\s*[<>=]\s*0\.\d|t-test|chi-square|ANOVA|Mann.Whitney',
            ],
            "Pre-registration or registered report protocol noted": [
                r'pre.?registr|registered\s+report|OSF|ClinicalTrials\.gov',
            ],
            "Data preprocessing steps documented": [
                r'preprocessing|pre-processing|normaliz|standardiz|tokeniz|clean',
            ],
            "Evaluation metrics defined with formulae or citations": [
                r'accuracy|F1\s+score|BLEU|ROUGE|precision|recall|AUC|ROC',
            ],
        }

        found = []
        missing = []
        for item, patterns in repro_patterns.items():
            detected = any(re.search(p, all_content, re.IGNORECASE) for p in patterns)
            if detected:
                found.append(item)
            else:
                missing.append(item)

        return found, missing

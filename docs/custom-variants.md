# Custom Variants

A variant adds domain-specific sections to a template's story. It subclasses `DocSetVariant`, declares `auto_detect_keywords`, and implements `build_variant_sections`. Variants are applied by the `briefing`, `report`, `manual` and `academic` templates (the fixed-format templates declare `supports_variants = False`).

## An example that runs

```python
# my_variants.py
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Spacer

from briefkit.elements.tables import build_data_table
from briefkit.styles import safe_para
from briefkit.variants import DocSetVariant, register_variant


@register_variant
class DevOpsVariant(DocSetVariant):
    name = "devops"
    auto_detect_keywords = ["kubernetes", "docker", "pipeline", "deploy", "terraform"]

    def build_variant_sections(self, content, flowables, styles, brand):
        tables = [
            table
            for sub in content.get("subsystems", [])
            for table in sub.get("tables", [])
            if any(h.lower() in ("service", "port", "container") for h in table.get("headers", []))
        ]
        if not tables:
            return flowables
        flowables.append(PageBreak())
        flowables.append(safe_para("DevOps Variant Sections", styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        for table in tables:
            # table cells from the extractor are already escaped
            flowables.extend(
                build_data_table(
                    table["headers"], table["rows"], title="Infrastructure Services", brand=brand, already_escaped=True
                )
            )
        return flowables
```

Import the module before BriefKit runs (in Python, or through a `sitecustomize.py` on `PYTHONPATH` for the CLI). The variant is then selectable three ways:

```bash
briefkit generate infra/cluster/ --variant devops          # by flag
```

```yaml
variants:
  rules:                                                   # by path, relative to the project root
    - pattern: "infra/**"
      variant: "devops"
  auto_detect: true                                        # by keywords: two whole-word hits trigger it
```

Selection order is flag, then the first matching rule, then auto-detection; `--variant none` suppresses all variants.

## Keyword matching

`keyword_hits(text)` counts the variant's keywords present in the text as whole words, case-insensitively, so `"loss"` does not match inside `"Glossary"` and an upper-case keyword such as `"GPIO"` matches ordinary prose. `auto_detect_variant(text)` picks the variant with the most hits (at least two); ties go to the first registered.

## What `build_variant_sections` receives

- `content`: the extracted content dict (`title`, `overview`, `subsystems` with `name`, `filename`, `content`, `blocks`, `tables`, `insights`; `terms`, `bibliography`, `metrics`).
- `flowables`: the story so far; append to it (or insert) and return it. The back cover is appended by the template after variants run, so anything you append lands before it.
- `styles`: the brand's named styles (`STYLE_H1`, `STYLE_BODY`, `STYLE_TABLE_BODY`, ...).
- `brand`: the brand dict (colors, fonts, organization).

Text that came from the extractor (block text, table cells, insights) is already escaped for the PDF engine; pass `already_escaped=True` to `safe_para`, `build_data_table` and `build_callout_box` for it, and escape your own data strings with `briefkit.styles.esc`.

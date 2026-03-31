# Custom Variants

Create custom variants to add domain-specific sections to any template.

## Setup

1. Create `.briefkit/variants/` in your project root
2. Add a Python file with your variant class
3. Configure path rules or rely on auto-detection

## Example

```python
# .briefkit/variants/devops.py
from briefkit.variants import DocSetVariant
from briefkit.elements.tables import build_data_table

class DevOpsVariant(DocSetVariant):
    name = "devops"
    auto_detect_keywords = ["kubernetes", "docker", "pipeline", "deploy", "terraform"]

    def build_variant_sections(self, content, flowables, styles, brand):
        # Extract service tables from content
        for sub in content.get("subsystems", []):
            for table in sub.get("tables", []):
                headers = [h.lower() for h in table.get("headers", [])]
                if any(kw in headers for kw in ["service", "port", "container"]):
                    flowables.extend(build_data_table(
                        table["headers"], table["rows"],
                        title="Infrastructure Services", brand=brand
                    ))
        return flowables
```

Configure:

```yaml
variants:
  rules:
    - pattern: "infra/**"
      variant: "devops"
```

## Auto-detection

Set `auto_detect_keywords` on your variant class. BriefKit activates the variant when 2+ keywords appear in the content text.

## Available Utilities

Import from `briefkit.elements`:
- `build_data_table(headers, rows, title, brand)`
- `build_callout_box(text, box_type, brand)`
- `build_metric_dashboard(metrics, brand)`
- `build_comparison_table(headers, rows, brand)`

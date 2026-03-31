# Configuration Reference

BriefKit uses a `briefkit.yml` file in your project root. Every field is optional — sensible defaults apply when omitted.

## Project Identity

```yaml
project:
  name: "My Project"          # Used on cover pages (default: directory name)
  org: ""                      # Organisation name (header bar)
  tagline: ""                  # Shown on back cover
  url: ""                      # Project URL (back cover)
  copyright: "© {year} {org}" # Copyright template
  abn: ""                      # Australian Business Number (optional)
```

## Brand / Color Scheme

```yaml
brand:
  preset: "navy"               # Built-in preset name OR "custom"
  primary: "#1B2A4A"           # Header bar, cover, accent
  secondary: "#2E86AB"         # Links, callout borders
  accent: "#E8C547"            # Callout backgrounds, badges
  body_text: "#2C2C2C"         # Body text
  caption: "#666666"           # Captions, metadata
  background: "#FFFFFF"        # Page background
  rule: "#CCCCCC"              # Rules, borders
  logo: ""                     # Path to logo image (PNG/SVG)
```

When `preset` is set to anything other than `"custom"`, manual color values are ignored.

## Document IDs

```yaml
doc_ids:
  enabled: true
  format: "{prefix}-{type}-{group}-{level}{seq}/{year}"
  prefix: "DOC"
  type: "BRF"
  year_format: "short"         # "short" = 26, "full" = 2026
  sequence_digits: 4
  registry_path: ".briefkit/registry.json"
  group_codes: {}              # e.g., {"src": "SRC", "docs": "DOC"}
```

## Page Layout

```yaml
layout:
  page_size: "A4"              # A4, Letter, Legal
  orientation: "portrait"
  margins:
    top: 25
    bottom: 22
    left: 20
    right: 20
  font_family: "Helvetica"
  font_size:
    body: 10
    h1: 16
    h2: 13
    h3: 11
    caption: 8
    code: 8.5
```

## Content Settings

```yaml
content:
  max_words_per_section: 3000
  max_terms_in_index: 40
  max_bibliography_entries: 100
  max_cross_refs: 30
  citation_formats:
    - apa
    - author_year
    - bracketed
    - legislation
    - rfc
    - case_law
  generic_terms_filter: true
  orientation_doc_pattern: "00-what-is-*.md"
  numbered_doc_pattern: "[0-9][0-9]-*.md"
```

## Hierarchy

```yaml
hierarchy:
  depth_to_level:
    0: 1    # Root children = Level 1
    1: 2    # Two deep = Level 2
    2: 3    # Three deep = Level 3
  root_level: 4
```

## Template

```yaml
template:
  preset: "briefing"           # briefing, book, report, manual, academic, minimal
  sections:
    cover: true
    classification_banner: true
    toc: true
    executive_summary: true
    at_a_glance: true
    body: true
    cross_references: true
    key_terms: true
    bibliography: true
    back_cover: true
  custom_sections: []
```

## Variants

```yaml
variants:
  rules:
    - pattern: "docs/api/**"
      variant: "api"
    - pattern: "docs/legal/**"
      variant: "legal"
  auto_detect: true
```

## Output

```yaml
output:
  filename: "executive-briefing.pdf"
  output_dir: ""
  skip_current: true
  log_dir: ".briefkit/logs"
  report_format: "markdown"
```

## Content Constraints

```yaml
constraints:
  - path: "docs/legal/**"
    rule: "Cite specific legislation by full title, year, and jurisdiction."
  - path: "docs/medical/**"
    rule: "Include safety warnings. Do not provide dosage advice."
```

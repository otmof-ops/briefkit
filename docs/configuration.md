# Configuration Reference

BriefKit works with no configuration file. To customize, put a `briefkit.yml` (or `briefkit.yaml`) at your project root. Every key is optional; the defaults below apply when a key is omitted.

**How the file is found.** Commands walk upward from the directory you run them in until they meet `briefkit.yml`, `briefkit.yaml` or a `.briefkit/` directory; that directory is the project root. `--config FILE` uses a specific file instead. The document-ID registry and the `output_dir` mirror are anchored at the project root that owns the directory being generated.

**Precedence.** Command-line flags override the file; the file overrides the defaults. An explicit `brand.*` color or font in the file survives the preset. Unknown keys are reported as warnings with the closest valid name; they never abort a run. Only keys listed here are read.

## project

```yaml
project:
  name: ""                     # default: the project root's directory name; `--title` overrides it per run
  org: ""                      # cover, running head, back cover, PDF /Author (also brand.org)
  tagline: ""                  # back cover (also brand.tagline)
  url: ""                      # back cover (also brand.url)
  copyright: "© {year} {org}"  # {year} and {org} are expanded; running foot and back cover
  abn: ""                      # Australian Business Number, cover and back cover (also brand.abn)
  lang: "en"                   # PDF /Lang (metadata.lang wins)
```

`project.org`, `tagline`, `url`, `abn` and `copyright` feed the matching `brand.*` key unless you set that `brand.*` key yourself.

### Universal controls under `project`

```yaml
project:
  skip_preface: true           # suppress an optional section; see universal-controls.md for all 30 names
  section_break_mode: auto     # auto | hard | flow
  min_section_space_mm: 80
  max_spacer_mm: 60
  disable_orphan_protection: false
  disable_empty_page_collapse: false
  disable_determinism: false   # wall-clock PDF timestamps instead of reproducible ones
```

A `skip_*` typo is rejected with a suggestion. Details: [universal-controls.md](universal-controls.md).

## brand

```yaml
brand:
  preset: "navy"               # one of 20 (`briefkit presets --quiet`), or "custom"
  # Twelve colors (6-digit hex, quoted) and four fonts; each overrides the preset
  primary: "#1B2A4A"
  secondary: "#2E86AB"
  accent: "#E8C547"
  body_text: "#2C2C2C"
  caption: "#666666"
  background: "#FFFFFF"
  rule: "#CCCCCC"
  success: "#00b894"
  warning: "#fdcb6e"
  danger: "#d63031"
  code_bg: "#f5f6fa"
  table_alt: "#f8f9fa"
  font_body: "Helvetica"       # a PDF base-14 font name
  font_heading: "Helvetica-Bold"
  font_mono: "Courier"
  font_caption: "Helvetica-Oblique"
  logo: ""                     # PNG, JPEG or GIF, relative to this file; drawn on the cover's top bar
  org: ""                      # normally supplied through project.*
  tagline: ""
  url: ""
  abn: ""
  copyright: ""
```

`preset: custom` applies no preset; only your own keys and the defaults are used. The `--preset` flag re-applies a preset over the file's colors. An unquoted hex color (`primary: 123456`) is an error that says to quote it; a missing logo file is an error; SVG is not accepted because the PDF engine cannot rasterize it.

## template

```yaml
template:
  preset: "briefing"           # one of 29 (`briefkit templates`)
```

Each template declares a design page size (A4, or Letter for `datasheet`, `memo`, `playbook`, `sop`, `whitepaper`, `evaluation`) and design margins. They apply unless you set the matching `layout.*` key. Which sections a template has, and how to suppress them, is in [templates-guide.md](templates-guide.md) and [universal-controls.md](universal-controls.md).

## layout

```yaml
layout:
  page_size: "A4"              # A4, A3, Letter, Legal, Tabloid
  orientation: "portrait"      # portrait, landscape
  margins:                     # millimetres; only the sides you set override the template's design margins
    top: 25
    bottom: 22
    left: 20
    right: 20
```

`guide`, `deep-research` and `magazine` draw their covers at absolute A4 coordinates and always use A4. `deck` and `certificate` are always landscape.

## metadata

```yaml
metadata:
  title: ""                    # default: the document title (README heading), then project.name
  author: ""                   # default: brand.org
  subject: ""                  # default: the template's subject
  creator: "briefkit"
  producer: "briefkit"
  keywords: []                 # list or string; default: the document ID
  lang: "en"
```

## content

```yaml
content:
  max_words_per_section: 12000 # per source document; 0 = unlimited; anything cut is reported on stderr
  max_blocks_per_section: 0    # rendered flowables per document in the body; 0 = unlimited
  max_terms_in_index: 40
  max_cross_refs: 30
  orientation_doc_pattern: "00-what-is-*.md"
  numbered_doc_pattern: "[0-9][0-9]-*.md"
  citation_formats: [apa, author_year, bracketed, legislation, rfc, case_law]
  generic_terms_filter: true
```

## hierarchy

```yaml
hierarchy:
  depth_to_level: {0: 1, 1: 2, 2: 3}   # depth below the project root -> briefing level
  root_level: 4                        # level for the project root itself
```

A directory that holds numbered documents is a documentation set (level 3) whatever its depth. Without a project root the tree is read instead: children that are documentation sets make a directory a subject (2), grandchildren make it a division (1).

## variants

```yaml
variants:
  auto_detect: true            # whole-word, case-insensitive keyword detection, 2 hits to trigger
  rules:                       # path pattern -> variant, matched against the directory's path relative to the project root
    - pattern: "docs/legal/**"
      variant: "legal"
```

Selection order: `--variant`, then the first matching rule, then auto-detection. `--variant none` suppresses variants. Variants are added by the `briefing`, `report`, `manual` and `academic` templates. Details: [variants.md](variants.md).

## doc_ids

```yaml
doc_ids:
  enabled: true
  format: "{prefix}-{type}-{group}-{level}{seq}/{year}"   # placeholders must be exactly these names
  prefix: "DOC"
  type: "BRF"
  year_format: "short"         # short = 26, full = 2026
  sequence_digits: 4
  registry_path: ".briefkit/registry.json"   # relative to the project root; must stay inside it
  group_codes: {}              # path component -> code, e.g. {docs: DOC, api: API}
```

Details: [document-ids.md](document-ids.md).

## license

```yaml
license:
  preset: ""                   # e.g. MIT, Apache-2.0, CC-BY-4.0; `briefkit licenses` lists them
  name: ""                     # the preset fills these four unless you set them
  spdx: ""
  url: ""
  notice: ""                   # printed on the back cover
```

Without a preset the back cover says "All rights reserved" and every run prints a warning.

## output

```yaml
output:
  filename: "executive-briefing.pdf"   # a bare .pdf name, no directory part
  output_dir: ""                       # mirror the tree beneath this directory (relative to the project root); empty = next to the sources
  skip_current: true                   # batch skips directories whose PDF is newer than its inputs
```

## quality

```yaml
quality:
  strict: false                # size and page thresholds fail instead of warn
  min_pages: null              # null = the level default
  hard_min_bytes: null
  soft_min_bytes: null
```

## Template-specific blocks

A few templates read their own block: `guide:` (`subtitle_keywords`, `spec_table`, `classification`, `version`, `header_right`, `subject`, `author`), `deep_research:` (`report_type`, `topics`, `subtitle`, `header_title`, `author`, `subject`, `pdf_title`) and `magazine:` (`edition`, `accent_word`, `sidebar_text`, `subtitle`, `bottom_colors`, `footer_text`, `header_title`, `author`, `subject`). The `minutes` template reads `project.location`, `chair`, `secretary` and `next_meeting`. See [templates-guide.md](templates-guide.md).

## Environment

`SOURCE_DATE_EPOCH` (a Unix time) pins every printed date and the PDF timestamps, so the same input gives byte-identical output.

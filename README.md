<div align="center">

# BriefKit

**Generate professional PDF briefings from markdown. One command. Zero config.**

[![CI](https://github.com/otmof-ops/briefkit/actions/workflows/test.yml/badge.svg)](https://github.com/otmof-ops/briefkit/actions/workflows/test.yml)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-blue.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[Documentation](https://github.com/otmof-ops/briefkit/tree/main/docs) · [Report a Bug](https://github.com/otmof-ops/briefkit/issues/new?template=bug-report.md) · [Request a Feature](https://github.com/otmof-ops/briefkit/issues/new?template=feature-request.md)

</div>

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Templates](#templates)
- [Color Presets](#color-presets)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [CLI Reference](#cli-reference)
- [CI Integration](#ci-integration)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Safety](#safety)
- [Security](#security)
- [License](#license)

---

## Guides

| Guide | Description |
|-------|-------------|
| [Quick Start](docs/quick-start.md) | Zero to PDF in 60 seconds |
| [Directory Structure](docs/directory-structure.md) | How to organize source files for each template |
| [Templates Guide](docs/templates-guide.md) | What each template produces and when to use it |
| [Presets Guide](docs/presets-guide.md) | Color presets, fonts, and custom branding |
| [CLI Reference](docs/cli-reference.md) | Every command and flag with examples |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and debugging steps |

---

## About

**OFFTRACKMEDIA Studios** — ABN 84 290 819 896
*"Building Empires, Not Just Brands."*

BriefKit turns a folder of markdown files into a branded, structured PDF in one command. It was extracted from [The Codex](https://github.com/otmof-ops/the-codex) — a 45,000-file knowledge infrastructure built for structured documentation at scale.

Unlike general-purpose converters like Pandoc or WeasyPrint, BriefKit is purpose-built for **structured briefings** — executive summaries, compliance reports, technical manuals, and academic papers — with auto-extracted bibliographies, cross-references, key term indexes, and metric dashboards out of the box.

**Who is this for?**

- **Technical writers** generating branded, consistent deliverables across teams
- **Engineering teams** producing compliance, audit, and assessment documentation
- **Researchers** converting markdown into thesis-format PDFs with citations and references
- **Ops teams** batch-generating SOPs, runbooks, and procedure manuals at scale

---

## Features

- **29 built-in templates** — briefing, report, book, manual, academic, minimal, novel, letter, contract, proposal, policy, witness, and 17 more (run `briefkit templates` for the full list)
- **12 domain-aware variants** — AI/ML, legal, medical, engineering, research, API, gaming, finance, species, historical, hardware, religion — auto-detected or configured
- **20 color presets** — switch the entire look with one line
- **Auto-extracted bibliography** — 6 citation formats + legislation + RFCs + case law
- **Document ID system** — persistent registry with configurable format
- **Version-tracked batch processing** — skip what is current, regenerate what is stale
- **Quality gates** — two-tier thresholds (hard minimum + soft target)
- **Custom templates and variants** — extend in ~100 lines of Python
- **Fully offline** — two dependencies (ReportLab, PyYAML), no AI APIs, no telemetry
- **274 tests passing** — CI on Python 3.10 and 3.12

---

## Templates

| Template | Best For | Sections |
|----------|----------|----------|
| `briefing` | Technical docs, research analysis, knowledge bases | Cover, TOC, Executive Summary, Dashboard, Body, Cross-Refs, Key Terms, Bibliography |
| `report` | Audit reports, compliance, assessments | Cover, TOC, Abstract, Methodology, Findings, Recommendations, Bibliography |
| `book` | Manuals, textbooks, comprehensive guides | Half Title, Title Page, Copyright, TOC, Preface, Chapters, Glossary, Index |
| `manual` | SOPs, equipment manuals, runbooks | Cover, Revision History, TOC, Safety Warnings, Procedures, Troubleshooting |
| `academic` | Research papers, white papers, theses | Title Page, Abstract, TOC, Literature Review, Body, References, Appendices |
| `minimal` | Quick exports, internal notes | Title, TOC, Body, Bibliography |

---

## Color Presets

| Preset | Style |
|--------|-------|
| `navy` | Professional, institutional (default) |
| `charcoal` | Dark neutral — consulting, finance |
| `ocean` | Blue-teal — tech, startups |
| `forest` | Green-earth — environment, sustainability |
| `crimson` | Red-dark — law, government |
| `slate` | Cool grey — minimal, engineering |
| `royal` | Purple-gold — academic, research |
| `sunset` | Warm orange — creative, media |
| `mono` | Pure black and white — print-first |
| `midnight` | Dark mode — screen reading |

---

## Installation

### Requirements

| Dependency | Minimum Version | Notes |
|---|---|---|
| Python | 3.10 | Required |
| ReportLab | 3.6 | Installed automatically |
| PyYAML | 6.0 | Installed automatically |

### From PyPI

```bash
pip install briefkit
```

### From Source

```bash
git clone https://github.com/otmof-ops/briefkit.git
cd briefkit
pip install -e ".[dev]"
```

### Verify Installation

```bash
briefkit selftest
```

---

## Quick Start

Get up and running in under five minutes.

**Step 1: Install**

```bash
pip install briefkit
```

**Step 2: Generate a briefing from a directory of markdown files**

```bash
briefkit generate docs/api/authentication/
```

**Step 3: Batch-generate all briefings under a root**

```bash
briefkit batch docs/
```

**Step 4: Preview (generate and open)**

```bash
briefkit preview docs/api/authentication/
```

For a detailed walkthrough, see the [Getting Started guide](docs/getting-started.md).

---

## Usage

### CLI Examples

```bash
# Generate with a specific template and color preset
briefkit generate docs/ --template report --preset charcoal

# Force regeneration even if version matches
briefkit batch docs/ --force

# Dry run — show what would be generated
briefkit batch docs/ --dry-run

# Assign document IDs without generating PDFs
briefkit assign-ids docs/
```

### Python API

```python
from briefkit.config import load_config
from briefkit.generator import BaseBriefingTemplate
from briefkit.extractor import extract_content

config = load_config("briefkit.yml")
content = extract_content("docs/api/authentication/")
```

### Custom Templates

```python
# .briefkit/templates/my_template.py
from briefkit.generator import BaseBriefingTemplate

class MyTemplate(BaseBriefingTemplate):
    name = "my_template"

    def build_story(self, content):
        return [
            *self.build_cover(content),
            *self.build_toc(content),
            *self.build_executive_summary(content),
            *self.build_body(content),
            *self.build_bibliography(content),
        ]
```

### Custom Variants

```python
# .briefkit/variants/devops.py
from briefkit.variants import DocSetVariant

class DevOpsVariant(DocSetVariant):
    name = "devops"
    auto_detect_keywords = ["kubernetes", "docker", "pipeline", "deploy"]

    def build_variant_sections(self, content, flowables, styles, brand):
        return flowables
```

---

## Configuration

BriefKit works with zero config. Drop a `briefkit.yml` in your project root to customize:

```yaml
project:
  name: "My Project"
  org: "My Company"

brand:
  preset: "ocean"

template:
  preset: "report"
```

Full configuration reference: [docs/configuration.md](docs/configuration.md)

### Quality Gates

Every generated PDF passes two-tier quality gates before being written to disk.

| Gate | Behavior |
|------|----------|
| Hard minimum (file size by level) | Aborts generation |
| Soft target (file size by level) | Warning only |

```bash
briefkit quality docs/api/authentication/
```

---

## CLI Reference

```
briefkit generate <path>        Generate briefing(s) for a directory
briefkit batch <root>           Generate all briefings under a root
briefkit init                   Create a briefkit.yml with defaults
briefkit preview <path>         Generate and open in PDF viewer
briefkit status <path>          Show briefing status (current/stale/missing)
briefkit assign-ids <path>      Assign document IDs without regenerating
briefkit quality <path>         Run quality gates on existing PDF
briefkit selftest               Generate from built-in test fixture
briefkit config                 Print resolved configuration
briefkit templates              List available templates
briefkit presets                List color presets with hex values
```

### Key Flags

```
--template / -t    Override template (any of 29 — see `briefkit templates` for the full list)
--preset / -p      Override color preset (navy, charcoal, ocean, etc.)
--variant / -v     Force a specific variant (aiml, legal, medical, etc.)
--output / -o      Output path override
--force / -f       Regenerate even if version matches
--dry-run          Show what would be generated without writing
--no-ids           Skip document ID assignment
--config / -c      Path to config file
--quiet / -q       Suppress progress output
--verbose          Show detailed extraction info
```

---

## CI Integration

```yaml
# .github/workflows/docs.yml
name: Generate Briefings
on: [push]
jobs:
  briefings:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install briefkit
      - run: briefkit batch docs/ --force
      - uses: actions/upload-artifact@v4
        with:
          name: briefings
          path: "**/*executive-briefing.pdf"
```

---

## FAQ

**Q: Is BriefKit production-ready?**

A: Yes. BriefKit is at v1.0.0 with 73 passing tests, two-tier quality gates, and CI on Python 3.10 and 3.12.

---

**Q: Does it need an internet connection?**

A: No. BriefKit is fully offline — no external APIs, no telemetry, no cloud dependencies. It reads local markdown and writes local PDFs.

---

**Q: Can I use custom branding?**

A: Yes. Choose from 20 built-in color presets or define custom colors with 12 color keys (primary, secondary, accent, body text, caption, background, rule, success, warning, danger, code_bg, table_alt). Add a logo via config.

---

**Q: How does BriefKit compare to Pandoc or WeasyPrint?**

A: Pandoc and WeasyPrint are general-purpose document converters. BriefKit is purpose-built for structured briefings — it auto-extracts bibliographies, generates executive summaries, builds metric dashboards, and applies domain-aware formatting. If you need a branded executive briefing from a folder of markdown, BriefKit does it in one command.

---

**Q: Can I create my own templates?**

A: Yes. Subclass `BaseBriefingTemplate` in ~100 lines of Python. See [Custom Templates](docs/custom-templates.md).

---

## Roadmap

Major items planned for upcoming releases:

- [ ] PyPI publishing (trusted publishing via GitHub Actions)
- [ ] HTML output format
- [ ] Custom font support
- [ ] Plugin system for third-party templates and variants
- [ ] PDF/A compliance for archival

---

## Contributing

Contributions of all kinds are welcome — code, documentation, bug reports, feature ideas.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. All contributors must agree to the Contributor License Agreement.

---

## Safety

BriefKit reads markdown files from the local filesystem and generates PDFs. Before processing directories containing sensitive, regulated, or third-party content, read [SAFETY.md](SAFETY.md). This is a condition of use under the [EULA](EULA/OFFTRACKMEDIA_EULA_2025.txt).

---

## Security

We take security seriously. If you discover a vulnerability, please **do not open a public GitHub issue**.

Instead, report it following the process in [SECURITY.md](SECURITY.md). We will acknowledge your report within 7 business days.

---

## License

Copyright (c) 2026 OFFTRACKMEDIA Studios. All rights reserved.
ABN 84 290 819 896.

This work is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/).

Commercial use, redistribution, and derivative works for commercial purposes require prior written consent. See the [EULA](EULA/OFFTRACKMEDIA_EULA_2025.txt) and [NOTICE.txt](NOTICE.txt) for full terms.

---

<div align="center">

Made with care by [OFFTRACKMEDIA Studios](https://github.com/otmof-ops) and [contributors](https://github.com/otmof-ops/briefkit/graphs/contributors).

Extracted from [The Codex](https://github.com/otmof-ops/the-codex) — 45,000+ files of structured knowledge.

If BriefKit has been useful to you, consider [starring the repository](https://github.com/otmof-ops/briefkit).

</div>

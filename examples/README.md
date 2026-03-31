# BriefKit Examples

Complete examples demonstrating every BriefKit template with real education content sourced from [The Codex](https://github.com/otmof-ops/the-codex).

---

## Prerequisites

```bash
pip install briefkit
```

## Quick Start

Generate your first PDF in 30 seconds:

```bash
cd examples/briefing-template
briefkit generate docs/cognitive-load-theory/
```

Open `docs/cognitive-load-theory/executive-briefing.pdf` to see the result.

---

## Template Showcase

Each example uses a different template with content that naturally fits its format:

| Example | Template | Topic | Preset | Generate Command |
|---------|----------|-------|--------|------------------|
| [briefing-template/](briefing-template/) | `briefing` | Cognitive Load Theory | navy | `briefkit generate docs/cognitive-load-theory/` |
| [report-template/](report-template/) | `report` | Curriculum Effectiveness | charcoal | `briefkit generate docs/curriculum-effectiveness/` |
| [academic-template/](academic-template/) | `academic` | Learning Theory Review | royal | `briefkit generate docs/learning-theory-review/` |
| [manual-template/](manual-template/) | `manual` | LMS Administration | slate | `briefkit generate docs/lms-administration/` |
| [book-template/](book-template/) | `book` | Education Foundations | forest | `briefkit generate docs/education-foundations/` |
| [minimal-template/](minimal-template/) | `minimal` | Assessment Quick Reference | mono | `briefkit generate docs/assessment-quick-reference/` |
| [legal-writing/](legal-writing/) | `briefing` | Legal Writing Principles | crimson | `briefkit generate docs/legal-writing/` |
| [legal-templates/](legal-templates/) | `manual` | Legal Document Templates | crimson | `briefkit generate docs/document-templates/` |
| [letter-template/](letter-template/) | `letter` | Engagement Letter | charcoal | `briefkit generate docs/engagement-letter/` |
| [contract-template/](contract-template/) | `contract` | Services Agreement | navy | `briefkit generate docs/services-agreement/` |
| [register-template/](register-template/) | `register` | Project Risk Register | slate | `briefkit generate docs/risk-register/` |
| [minutes-template/](minutes-template/) | `minutes` | Board Meeting Minutes | charcoal | `briefkit generate docs/board-meeting/` |

---

## New Template Showcase (v1.1)

Four new structurally distinct templates added beyond the original 6:

- **`letter`** — formal correspondence with letterhead, addressee block, salutation, and signature. No cover page, no TOC.
- **`contract`** — legal agreements with party identification, recitals, numbered clauses, definitions, schedules, and execution/signature blocks.
- **`register`** — table-dominant layout for risk registers, compliance matrices, data dictionaries. Persistent column headers across pages.
- **`minutes`** — meeting minutes with attendees, agenda items, auto-extracted action items and resolutions.

---

## Legal Variant Showcase

The `legal-writing/` and `legal-templates/` examples demonstrate BriefKit's legal variant with real multi-jurisdictional content sourced from [The Codex](https://github.com/otmof-ops/the-codex) law division.

The legal variant auto-detects and adds:
- **Jurisdiction Reference** — countries and legal systems covered
- **Legislation Index** — statutes extracted from content (Privacy Act 1988, Consumer Rights Act 2015, etc.)
- **Case Reference** — case law citations (Donoghue v Stevenson, etc.)
- **Regulatory Bodies** — ACCC, OAIC, FCA, ICO, and others detected from text

Compare the legal-writing briefing (analytical, principle-focused) with the legal-templates manual (procedural, template-focused) to see how the same variant produces different results depending on the template.

---

## Step-by-Step Tutorial

### Step 1: Generate a Briefing (Default Template)

The briefing template produces an executive briefing with cover page, table of contents, executive summary, metrics dashboard, body content, cross-references, key terms index, and bibliography.

```bash
cd briefing-template
briefkit generate docs/cognitive-load-theory/
```

### Step 2: Try a Different Template

The report template organizes the same kind of content into methodology, findings, and recommendations:

```bash
cd ../report-template
briefkit generate docs/curriculum-effectiveness/
```

Compare the two PDFs — same input format, completely different output structure.

### Step 3: Change the Color Preset

Override the color preset from the command line:

```bash
briefkit generate docs/curriculum-effectiveness/ --preset crimson
```

Available presets: `navy`, `charcoal`, `ocean`, `forest`, `crimson`, `slate`, `royal`, `sunset`, `mono`, `midnight`.

### Step 4: Use a Configuration File

Each example includes a `briefkit.yml` that configures the template and branding. Open any of them to see how configuration works:

```yaml
# report-template/briefkit.yml
project:
  name: "Curriculum Effectiveness Assessment"
  org: "National Education Board"

brand:
  preset: "charcoal"

template:
  preset: "report"
```

When `briefkit.yml` is present, you don't need CLI flags — just run `briefkit generate <path>`.

### Step 5: Batch Generate Everything

Generate all examples at once:

```bash
cd /path/to/briefkit/examples
for dir in briefing-template report-template academic-template manual-template book-template minimal-template; do
  echo "=== Generating $dir ==="
  cd $dir && briefkit generate docs/*/ && cd ..
done
```

---

## Configuration Examples

### Basic (Zero Config)

```yaml
# basic/briefkit.yml
project:
  name: "BriefKit Getting Started"
  org: "BriefKit"
```

Uses all defaults: briefing template, navy preset, no document IDs.

### Corporate Branding

```yaml
# corporate/briefkit.yml
project:
  name: "ACME Engineering"
  org: "ACME Corporation"
  tagline: "Engineering Excellence Since 1952"

brand:
  preset: "charcoal"

doc_ids:
  prefix: "ACME-ENG"

template:
  preset: "report"
```

Full branding with document ID tracking and the report template.

### Academic Research

```yaml
# research/briefkit.yml
project:
  name: "Machine Learning Research"
  org: "University of Melbourne"

brand:
  preset: "royal"

template:
  preset: "academic"

variants:
  rules:
    - pattern: "papers/ml/**"
      variant: "aiml"
```

Academic template with variant rules for domain-specific formatting.

---

## Next Steps

- [Configuration Reference](../docs/configuration.md) — Every available setting
- [Templates Guide](../docs/templates.md) — Detailed template descriptions
- [Color Presets](../docs/color-presets.md) — All presets with hex values
- [Custom Templates](../docs/custom-templates.md) — Build your own template
- [CI Integration](../docs/ci-integration.md) — Automate PDF generation in CI/CD

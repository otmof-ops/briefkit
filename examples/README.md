# BriefKit Examples

Everything under `examples/` is dedicated to the public domain under [CC0 1.0](../LICENSES/CC0-1.0.txt), so you can paste it into your own project with no attribution, with the exceptions recorded in [REUSE.toml](../REUSE.toml): the two legal sets (`legal-templates/`, `legal-writing/`) are Codex content under [CC BY-NC-SA 4.0](../LICENSES/CC-BY-NC-SA-4.0.txt), and the two narrative samples (`novel-template/docs/`, `gothic-novel/sample/`) are under [CC BY-NC-ND 4.0](../LICENSES/CC-BY-NC-ND-4.0.txt).

Complete example projects, one per directory. Each holds a `briefkit.yml` and a documentation set you can generate straight away.

---

## Prerequisites

```bash
pip install "git+https://github.com/otmof-ops/briefkit.git"
```

## Quick Start

```bash
cd examples/briefing-template
briefkit generate docs/cognitive-load-theory/
```

Open `docs/cognitive-load-theory/executive-briefing.pdf` to see the result.

---

## The Examples

Run each command from inside the example's directory so its `briefkit.yml` is picked up.

| Example | Template | Preset | Content | Generate Command |
|---------|----------|--------|---------|------------------|
| [basic/](basic/) | `briefing` | navy | Getting started guide (zero configuration, no document IDs) | `briefkit generate docs/getting-started/` |
| [briefing-template/](briefing-template/) | `briefing` | navy | Cognitive Load Theory | `briefkit generate docs/cognitive-load-theory/` |
| [report-template/](report-template/) | `report` | charcoal | Curriculum Effectiveness | `briefkit generate docs/curriculum-effectiveness/` |
| [academic-template/](academic-template/) | `academic` | royal | Learning Theory Review | `briefkit generate docs/learning-theory-review/` |
| [manual-template/](manual-template/) | `manual` | slate | LMS Administration | `briefkit generate docs/lms-administration/` |
| [workshop-manual-template/](workshop-manual-template/) | `manual` | navy | Vehicle Rebuild Workshop Manual, with a license preset | `briefkit generate docs/vehicle-rebuild/` |
| [book-template/](book-template/) | `book` | forest | Education Foundations | `briefkit generate docs/education-foundations/` |
| [novel-template/](novel-template/) | `novel` | gothic | The Backrooms (fiction) | `briefkit generate docs/backrooms-novel/` |
| [minimal-template/](minimal-template/) | `minimal` | mono | Assessment Quick Reference | `briefkit generate docs/assessment-quick-reference/` |
| [legal-writing/](legal-writing/) | `briefing` | crimson | Legal Writing Principles, legal variant by rule | `briefkit generate docs/legal-writing/` |
| [legal-templates/](legal-templates/) | `manual` | crimson | Legal Document Templates, legal variant by rule | `briefkit generate docs/document-templates/` |
| [letter-template/](letter-template/) | `letter` | charcoal | Engagement Letter | `briefkit generate docs/engagement-letter/` |
| [contract-template/](contract-template/) | `contract` | navy | Services Agreement | `briefkit generate docs/services-agreement/` |
| [register-template/](register-template/) | `register` | slate | Project Risk Register | `briefkit generate docs/risk-register/` |
| [minutes-template/](minutes-template/) | `minutes` | charcoal | Board Meeting Minutes | `briefkit generate docs/board-meeting/` |
| [corporate/](corporate/) | `report` | charcoal | Infrastructure audit with a custom document-ID prefix | `briefkit generate docs/infrastructure-audit/` |
| [research/](research/) | `academic` | royal | Transformer architecture, AI/ML variant by rule | `briefkit generate papers/ml/transformer-architecture/` |
| [gothic-novel/](gothic-novel/) | scripts | gothic | A typesetting workflow built on BriefKit for a multi-volume novel; see its own README | see [gothic-novel/README.md](gothic-novel/README.md) |

These are 12 of the 29 templates. `briefkit templates` lists them all with a one-line description each; [docs/templates-guide.md](../docs/templates-guide.md) describes every one.

---

## The Legal Variant

`legal-writing/` and `legal-templates/` select the legal variant with a `variants.rules` entry, so every document under the matching path gets it without a flag:

```yaml
variants:
  rules:
    - pattern: "docs/legal-writing/**"
      variant: "legal"
```

The legal variant adds a jurisdiction reference, a legislation index (statutes found in the text), a case table and a regulatory-bodies list. Compare the legal-writing briefing (analytical) with the legal-templates manual (procedural) to see how the same variant reads in two templates. [docs/variants.md](../docs/variants.md) describes all twelve variants and how one is chosen.

---

## Step-by-Step Tutorial

### Step 1: Generate a Briefing (Default Template)

The briefing template produces an executive briefing with a cover page, table of contents, executive summary, metrics dashboard, body content, cross-references, key terms index and bibliography.

```bash
cd briefing-template
briefkit generate docs/cognitive-load-theory/
```

### Step 2: Try a Different Template

The report template organizes the same kind of content into methodology, findings and recommendations:

```bash
cd ../report-template
briefkit generate docs/curriculum-effectiveness/
```

Compare the two PDFs: same input format, different output structure.

### Step 3: Change the Color Preset

Override the preset from the command line:

```bash
briefkit generate docs/curriculum-effectiveness/ --preset crimson
```

`briefkit presets --quiet` lists all 20; [docs/color-presets.md](../docs/color-presets.md) shows their values.

### Step 4: Use a Configuration File

Each example's `briefkit.yml` sets the template and branding:

```yaml
# report-template/briefkit.yml
project:
  name: "Curriculum Effectiveness Assessment"
  org: "Example Education Board"

brand:
  preset: "charcoal"

template:
  preset: "report"
```

With the file in place no flags are needed: `briefkit generate <path>` from inside the example directory is enough.

### Step 5: Generate Every Example

```bash
cd /path/to/briefkit/examples
for dir in */; do
  [ -f "$dir/briefkit.yml" ] || continue
  echo "=== $dir ==="
  ( cd "$dir" && briefkit batch . --quiet )
done
```

`batch` finds every documentation set under the example and skips any whose PDF is already current.

---

## Configuration Examples

### Basic

```yaml
# basic/briefkit.yml
project:
  name: "BriefKit Getting Started"
  org: "BriefKit"

doc_ids:
  enabled: false
```

Everything else is a default: briefing template, navy preset.

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

Full branding, document IDs with a custom prefix, the report template.

### Academic Research

```yaml
# research/briefkit.yml
project:
  name: "Machine Learning Research"
  org: "Example University"

brand:
  preset: "royal"

template:
  preset: "academic"

variants:
  rules:
    - pattern: "papers/ml/**"
      variant: "aiml"
```

The academic template, with the AI/ML variant applied to everything under `papers/ml/`.

---

## Next Steps

- [Configuration Reference](../docs/configuration.md): every setting
- [Templates Guide](../docs/templates-guide.md): all 29 templates
- [Color Presets](../docs/color-presets.md): all 20 presets with their values
- [Custom Templates](../docs/custom-templates.md): build your own template
- [CI Integration](../docs/ci-integration.md): generate PDFs in CI

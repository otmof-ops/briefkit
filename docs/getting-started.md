# Getting Started

## Installation

```bash
pip install briefkit
```

## Your First Briefing

1. Navigate to a project with markdown documentation:

```bash
cd my-project
```

2. Generate a briefing from a documentation directory:

```bash
briefkit generate docs/api/authentication/
```

This produces `docs/api/authentication/executive-briefing.pdf` with:
- Professional cover page
- Table of contents
- Executive summary extracted from README
- Metric dashboard (word count, file count, etc.)
- Body content from numbered markdown files
- Auto-extracted bibliography
- Key terms index

## Batch Generation

Generate briefings for every documentation directory:

```bash
briefkit batch docs/
```

BriefKit finds all directories containing numbered markdown files (`01-*.md`, `02-*.md`, etc.) and generates a briefing for each.

## Configuration

Create `briefkit.yml` in your project root:

```bash
briefkit init
```

Edit to customize:

```yaml
project:
  name: "My Project"
  org: "My Company"

brand:
  preset: "ocean"
```

## Next Steps

- [Configuration Reference](configuration.md)
- [Templates](templates.md)
- [Color Presets](color-presets.md)
- [Custom Templates](custom-templates.md)

# Getting Started

The [Quick Start](quick-start.md) takes you from install to a first PDF in a few minutes. This page covers what comes next: a whole documentation tree, keeping output current, and a first configuration file.

## Installation

```bash
pip install "git+https://github.com/otmof-ops/briefkit.git"
briefkit --version
briefkit selftest
```

## Your First Briefing

Point `generate` at a directory of numbered Markdown files:

```bash
briefkit generate docs/api/authentication/
```

This produces `docs/api/authentication/executive-briefing.pdf` with, for the default `briefing` template:

- A cover page, with the title from the README's first heading
- A clickable table of contents and a PDF outline
- An executive summary from the README
- A metric dashboard (word count, document count, tables)
- The body: each numbered file is a chapter
- Cross-references, key terms and an auto-extracted bibliography

Each run also prints the output path and, until you set `license.preset`, a warning that the back cover says "All rights reserved".

## Batch Generation

```bash
briefkit batch docs/
```

BriefKit finds every directory under `docs/` that directly contains numbered Markdown files (`01-*.md`, `02-*.md`, ...) and generates a briefing for each. A directory whose PDF is newer than all of its inputs is skipped; `--force` rebuilds everything.

```bash
briefkit status docs/            # CURRENT / STALE / MISSING per directory
briefkit status docs/ --check    # exit 1 if anything is stale or missing
```

## Configuration

Create `briefkit.yml` in your project root:

```bash
briefkit init
```

Then edit it:

```yaml
project:
  name: "My Project"
  org: "My Company"

brand:
  preset: "ocean"

template:
  preset: "report"

license:
  preset: "CC-BY-4.0"
```

The file is found by walking upward from the directory you run the command in, so `briefkit generate docs/api/authentication/` from the project root picks it up without flags. Every key: [configuration.md](configuration.md).

## Next Steps

- [Directory Structure](directory-structure.md): how sources are read
- [Templates Guide](templates-guide.md): all 29 templates
- [Presets Guide](presets-guide.md) and [Color Presets](color-presets.md)
- [CLI Reference](cli-reference.md)
- [Custom Templates](custom-templates.md)

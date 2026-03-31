# Your First Briefing

## What BriefKit Expects

BriefKit generates PDFs from directories containing numbered markdown files. The naming convention is simple:

| File | Purpose |
|------|---------|
| `README.md` | Title and executive summary (extracted for cover page) |
| `01-topic-name.md` | First section of the document body |
| `02-another-topic.md` | Second section |
| `03-yet-another.md` | Third section, and so on |

BriefKit reads the files in numerical order, extracts the first `# heading` from README.md as the document title, and uses the first substantial paragraph as the executive overview.

## Generate a Briefing

Navigate to any example directory and run:

```bash
cd examples/briefing-template
briefkit generate docs/cognitive-load-theory/
```

This produces `docs/cognitive-load-theory/executive-briefing.pdf` containing:

- A professional cover page with the project name, organization, and generation date
- A table of contents with clickable section links
- An executive summary extracted from the README
- A metrics dashboard showing word count, file count, and document statistics
- The full body content from each numbered markdown file
- An auto-extracted bibliography from any citations found in the text
- A key terms index of technical vocabulary detected in the content

## Preview Mode

Generate and immediately open the PDF in your system's default viewer:

```bash
briefkit preview docs/cognitive-load-theory/
```

## Batch Generation

Generate briefings for every documentation directory under a root:

```bash
briefkit batch docs/
```

BriefKit recursively discovers all directories containing numbered markdown files and generates a briefing for each one. Directories that are already up-to-date are skipped automatically.

## Check Status

See which briefings are current, stale, or missing:

```bash
briefkit status docs/
```

> A briefing is "stale" when any source markdown file has been modified since the PDF was last generated. Use `--force` to regenerate even if the briefing is current.

# Directory Structure Guide

This is the most important guide in the docs. BriefKit's output quality depends entirely on how you structure your source directory.

---

## The Core Rule

BriefKit expects a **flat directory** containing:

1. `README.md` (optional but recommended) -- sets title and overview
2. Numbered markdown files (`01-*.md`, `02-*.md`, ...) -- becomes chapters/sections
3. Optionally: `00-what-is-*.md` -- orientation document (special handling)
4. Optionally: `engineering-brilliance.md`, `guide.md` -- supplementary content

**Each numbered file becomes one subsystem (chapter/section) in the PDF.**

---

## Minimum Viable Directory

```
my-topic/
  01-introduction.md
```

That is it. One numbered file is enough. BriefKit will:
- Derive the title from the directory name (`my-topic` becomes "My Topic")
- Extract content from `01-introduction.md`
- Generate a full PDF with cover, TOC, body, and bibliography

## Recommended Directory

```
my-topic/
  README.md
  01-introduction.md
  02-core-concepts.md
  03-implementation.md
```

With `README.md`, BriefKit:
- Uses the first `# Heading` as the document title
- Uses the first paragraph (80+ characters) as the overview/executive summary
- Both appear on the cover page and in the executive summary section

---

## File Naming Convention

### Numbered Documents

Files must match the pattern `[0-9][0-9]-*.md`:

```
01-introduction.md        -- good
02-core-concepts.md       -- good
03-advanced-topics.md     -- good
10-appendix.md            -- good
1-intro.md                -- WILL NOT BE DETECTED (single digit)
introduction.md           -- WILL NOT BE DETECTED (no number prefix)
chapter-01.md             -- WILL NOT BE DETECTED (number not at start)
```

The number controls sort order. Gaps are fine (01, 03, 07).

### How Numbers Map to PDF Sections

The number prefix is stripped for display. The remaining kebab-case name is title-cased:

| Filename | Display Name in PDF |
|----------|-------------------|
| `01-introduction.md` | Introduction |
| `02-core-concepts.md` | Core Concepts |
| `03-api-reference.md` | Api Reference |
| `10-appendix-data.md` | Appendix Data |

### Orientation Document

Files matching `00-what-is-*.md` receive special treatment:

```
00-what-is-neural-networks.md
```

- Extracted separately from numbered docs
- Appears as orientation/context content
- Not counted as a regular chapter
- Sets `metrics.has_orientation = True`

### Supplementary Files

| File | Purpose |
|------|---------|
| `README.md` | Title, overview, context. First `# Heading` = title. First long paragraph = overview. |
| `engineering-brilliance.md` | Additional summary content (appears in brilliance section) |
| `guide.md` | Guide/tutorial content |
| `.source-type` | Marker file with `type: ACADEMIC` or similar metadata |

---

## How the Extractor Maps Directories to Content

Understanding this mapping is critical for getting good output.

### Level 3: Doc Set (Most Common)

This is what you use 90% of the time. One directory = one PDF.

```
my-topic/                          --> title: "My Topic" (from README or dir name)
  README.md                        --> overview, title override
  01-working-memory.md             --> subsystems[0]
  02-schema-theory.md              --> subsystems[1]
  03-instructional-design.md       --> subsystems[2]
  reference-paper.pdf              --> bibliography entry (parsed from filename)
```

The extractor:
1. Reads `README.md` for title and overview
2. Reads each `[0-9][0-9]-*.md` file (sorted by name)
3. For each file: parses markdown into blocks (headings, paragraphs, tables, code, lists, blockquotes)
4. Extracts tables, blockquote insights, and citation counts per file
5. Extracts cross-references, key terms, and bibliography from all content
6. Counts metrics (word count, file count, doc count, table count)

Each numbered file becomes a `subsystem` dict:

```python
{
    "name": "Working Memory",        # from filename, title-cased
    "filename": "01-working-memory.md",
    "content": "raw markdown text",
    "blocks": [...],                  # parsed markdown blocks
    "tables": [...],                  # extracted tables
    "insights": [...],               # blockquote text
}
```

### Level 2: Subject (Aggregation)

A directory of doc sets. Each subdirectory with numbered docs is aggregated.

```
education/                         --> Subject-level briefing
  README.md
  cognitive-load-theory/           --> doc set 1
    README.md
    01-working-memory.md
    02-schema-theory.md
  assessment-methods/              --> doc set 2
    README.md
    01-formative.md
    02-summative.md
```

### Level 1: Division (Higher Aggregation)

A directory of subjects.

```
sciences/                          --> Division-level briefing
  README.md
  education/                       --> subject 1
    cognitive-load-theory/
    assessment-methods/
  psychology/                      --> subject 2
    behavioral/
    cognitive/
```

### Level 4: Root

The project root. Aggregates divisions.

---

## Examples by Template

### Briefing Template

The default. Best for technical docs, research analysis, knowledge bases.

```
cognitive-load-theory/
  README.md                        # "Cognitive Load Theory" as title
  01-working-memory.md             # Chapter: Working Memory
  02-schema-theory.md              # Chapter: Schema Theory
  03-instructional-design.md       # Chapter: Instructional Design
```

Produces: Cover, TOC, Executive Summary, Dashboard, Body (3 chapters), Cross-Refs, Key Terms, Bibliography.

### Report Template

Best for audits, compliance, assessments.

```
curriculum-effectiveness/
  README.md
  01-methodology.md                # Methodology section
  02-findings.md                   # Findings section
  03-recommendations.md            # Recommendations section
```

Produces: Cover, TOC, Abstract, Methodology, Findings, Discussion, Recommendations, Appendices, Bibliography.

### Book Template

Best for manuals, textbooks, comprehensive guides.

```
education-foundations/
  README.md
  01-behaviorism.md                # Chapter 1
  02-cognitivism.md                # Chapter 2
  03-constructivism.md             # Chapter 3
  04-connectivism.md               # Chapter 4
```

Produces: Half Title, Title Page, Copyright, TOC, Preface, Chapters (4), Glossary, Bibliography, Index, Colophon.

### Manual Template

Best for SOPs, equipment manuals, runbooks.

```
lms-administration/
  README.md
  01-setup.md                      # Procedure 1
  02-user-management.md            # Procedure 2
  03-troubleshooting.md            # Procedure 3
```

Produces: Cover, Revision History, TOC, Safety Warnings, Scope, Procedures, Reference Tables, Troubleshooting, Bibliography.

### Academic Template

Best for research papers, white papers, theses.

```
learning-theory-review/
  README.md
  01-literature-review.md
  02-methodology.md
  03-results.md
```

Produces: Title Page, Abstract, TOC, Introduction, Literature Review, Body, Results, Discussion, Conclusion, References, Appendices.

### Minimal Template

Best for quick exports, internal notes.

```
assessment-quick-reference/
  README.md
  01-overview.md
  02-checklist.md
```

Produces: Title, TOC, Body, Bibliography.

### Letter Template

Best for formal correspondence. No cover page, no TOC.

```
engagement-letter/
  README.md
  01-scope-and-fees.md
```

Produces: Letterhead, date, body, signature block.

### Contract Template

Best for legal agreements.

```
services-agreement/
  README.md
  01-services-and-deliverables.md
  02-terms-and-conditions.md
```

Produces: Title page, recitals, definitions, numbered clauses, schedules, execution/signature block.

### Register Template

Best for risk registers, compliance matrices, data dictionaries. Table-dominant layout.

```
risk-register/
  README.md
  01-risk-entries.md
```

Produces: Title, consolidated table with persistent headers, summary statistics.

### Minutes Template

Best for meeting minutes.

```
board-meeting/
  README.md
  01-financial-report.md
  02-erp-project-update.md
```

Produces: Header, attendees, agenda items, action items, resolutions, closing.

---

## PDF Files as Bibliography Sources

Any `.pdf` files in the source directory (other than the output file) are parsed as bibliography entries:

```
my-topic/
  01-analysis.md
  smith-2023-machine-learning.pdf    --> Bibliography: "Machine Learning" by Smith (2023)
  2401.12345.pdf                     --> Bibliography: arXiv:2401.12345
```

The filename is parsed using kebab-case conventions:
- `author-year-title.pdf` format is preferred
- ArXiv IDs (`YYMM.NNNNN`) are detected automatically

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| No numbered files | "0 subsystems", nearly empty PDF | Add at least one `01-*.md` file |
| Single-digit prefix | Files not detected | Use two digits: `01-`, not `1-` |
| Subdirectories with content | Content not extracted at Level 3 | Move `.md` files to the top level of the doc set |
| README.md only | No body content | Add numbered markdown files |
| Wrong directory passed to CLI | "0 words extracted" | Pass the directory containing the `.md` files, not a parent |

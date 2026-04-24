# Templates Guide

BriefKit ships with 29 built-in templates. Each produces a structurally different PDF from the same input format (numbered markdown files in a directory).

Run `briefkit templates` at the CLI to list the currently available templates at any time.

---

## Template Summary

| Template Name | CLI Value | Best For | Sections |
|--------------|-----------|----------|----------|
| Briefing | `briefing` | Technical docs, research analysis, knowledge bases | Cover, TOC, Executive Summary, Dashboard, Body, Cross-Refs, Key Terms, Bibliography, Back Cover |
| Report | `report` | Audit reports, compliance, assessments | Cover, TOC, Abstract, Methodology, Findings, Discussion, Recommendations, Appendices, Bibliography, Back Cover |
| Book | `book` | Manuals, textbooks, comprehensive guides | Half Title, Title Page, Copyright, TOC, Preface, Chapters, Glossary, Bibliography, Index, Colophon |
| Novel | `novel` | Narrative fiction, literary works, long-form prose | Half Title, Title Page, Copyright, TOC, Chapters, Colophon |
| Manual | `manual` | SOPs, equipment manuals, runbooks | Cover, Revision History, TOC, Safety Warnings, Scope, Procedures, Reference Tables, Troubleshooting, Bibliography, Back Cover |
| Academic | `academic` | Research papers, white papers, theses | Title Page, Abstract, TOC, Introduction, Literature Review, Body, Results, Discussion, Conclusion, References, Appendices |
| Minimal | `minimal` | Quick exports, internal notes | Title, TOC, Body, Bibliography |
| Magazine | `magazine` | Long-form feature journalism, definitive guides | Cover, TOC, Feature Articles, Sidebars, Back Cover |
| Whitepaper | `whitepaper` | Thought leadership, vendor whitepapers | Cover, Abstract, TOC, Body, Conclusions, Bibliography |
| Deep Research | `deep-research` | AI / ML research reports | Cover, Abstract, TOC, Findings, Experiments, Discussion, References |
| Policy | `policy` | Corporate policies, governance documents | Title Page, TOC, Scope, Definitions, Policy Statements, Compliance, Revision History |
| Proposal | `proposal` | Business proposals, RFP responses | Cover, Executive Summary, Problem Statement, Solution, Pricing, Timeline, Terms |
| Guide | `guide` | Step-by-step technical guides | Cover, TOC, Prerequisites, Steps, Troubleshooting, References |
| Playbook | `playbook` | Incident response, operational playbooks | Cover, TOC, Triggers, Procedures, Escalation, References |
| SOP | `sop` | Standard operating procedures (WSU-style) | Cover, Revision History, Scope, Definitions, Procedures, References |
| Datasheet | `datasheet` | Technical specifications, product datasheets | Header, Specs Tables, Dimensions, Safety, Contact |
| Evaluation | `evaluation` | Performance reviews, rating matrices | Subject, Rating Matrix, Narrative Assessment, Signature Block |
| Newsletter | `newsletter` | Periodic newsletters | Masthead, Lead Story, Sidebars, Events, Footer |
| Deck | `deck` | Slide-style presentations | Title Slide, Content Slides, End Slide |
| Letter | `letter` | Formal correspondence | Letterhead, Date, Body, Signature |
| Memo | `memo` | Internal memoranda (DEQ-style) | Header Block, Body, Distribution |
| Minutes | `minutes` | Meeting minutes | Header, Attendees, Agenda Items, Action Items, Resolutions, Closing |
| Contract | `contract` | Legal agreements | Title Page, Recitals, Definitions, Clauses, Schedules, Execution Block |
| Witness | `witness` | Legal witness statements | Header Block, Paragraph-Numbered Body, Execution Block |
| Resume | `resume` | Professional CV / resume | Header, Summary, Experience, Education, Skills, References |
| Invoice | `invoice` | Professional invoices | Header, Line Items, Totals, Payment Terms |
| Quote | `quote` | Professional quotes / estimates | Header, Scope, Pricing, Terms, Acceptance |
| Certificate | `certificate` | Awards, completions, credentials (landscape) | Decorative Border, Recipient, Authority, Date |
| Register | `register` | Risk registers, data dictionaries, compliance matrices | Title, Consolidated Table, Summary Stats |

---

## How to Select a Template

### Via CLI Flag

```bash
briefkit generate docs/my-topic/ --template report
briefkit generate docs/my-topic/ -t academic
```

### Via Config File

```yaml
# briefkit.yml
template:
  preset: report
```

### Default

If no template is specified, BriefKit uses `briefing`.

---

## Template Details

### `briefing` (Default)

The executive briefing template. Designed for knowledge base entries, technical deep-dives, and research analysis.

**Sections produced:**
1. **Cover Page** -- title, organization, date, document ID, metrics summary
2. **Classification Banner** -- document classification header
3. **Table of Contents** -- auto-generated
4. **Executive Summary** -- extracted from README overview + orientation doc
5. **At-a-Glance Dashboard** -- word count, doc count, file count, year, source type
6. **Body Chapters** -- one section per numbered markdown file, with full rendering of headings, paragraphs, tables, code blocks, lists, blockquotes
7. **Cross-References** -- auto-detected references to other doc sets
8. **Key Terms Index** -- extracted technical terms with definitions
9. **Bibliography** -- from PDF filenames + inline citations (APA, author-year, bracketed, legislation, RFC, case law)
10. **Back Cover** -- organization branding

**Use when:** You want a comprehensive executive-ready document.

```bash
briefkit generate docs/cognitive-load-theory/ --template briefing
```

---

### `report`

Formal report structure. Organizes content into methodology, findings, and recommendations.

**Sections produced:**
1. Cover Page
2. Table of Contents
3. Abstract
4. Methodology
5. Findings
6. Discussion
7. Recommendations
8. Appendices
9. Bibliography
10. Back Cover

**Use when:** You need a structured assessment, audit report, or compliance document.

```bash
briefkit generate docs/curriculum-effectiveness/ --template report
```

---

### `book`

Long-form book layout with front matter, chapters, and back matter.

**Sections produced:**
1. Half Title Page
2. Title Page
3. Copyright Page
4. Table of Contents
5. Preface
6. Chapters (one per numbered file)
7. Glossary
8. Bibliography
9. Index
10. Colophon

**Use when:** You are producing a manual, textbook, or comprehensive guide that feels like a printed book.

```bash
briefkit generate docs/education-foundations/ --template book --preset forest
```

---

### `manual`

Technical manual layout with revision tracking, safety warnings, and procedures.

**Sections produced:**
1. Cover Page
2. Revision History
3. Table of Contents
4. Safety Warnings
5. Scope
6. Procedures (one per numbered file)
7. Reference Tables
8. Troubleshooting
9. Bibliography
10. Back Cover

**Use when:** You are writing SOPs, equipment guides, runbooks, or process documentation.

```bash
briefkit generate docs/lms-administration/ --template manual --preset slate
```

---

### `academic`

Academic paper layout with literature review, methodology, results, and formal references.

**Sections produced:**
1. Title Page
2. Abstract
3. Table of Contents
4. Introduction
5. Literature Review
6. Body
7. Results
8. Discussion
9. Conclusion
10. References
11. Appendices

**Use when:** You are writing a research paper, thesis, white paper, or literature review.

```bash
briefkit generate docs/learning-theory-review/ --template academic --preset royal
```

---

### `minimal`

Stripped-down output. Title, table of contents, body, bibliography. Nothing else.

**Sections produced:**
1. Title
2. Table of Contents
3. Body
4. Bibliography

**Use when:** You want a quick export, internal memo, or draft without the full briefing structure.

```bash
briefkit generate docs/assessment-quick-reference/ --template minimal --preset mono
```

---

### `letter`

Formal correspondence. No cover page, no table of contents.

**Sections produced:**
1. Letterhead (organization name, logo)
2. Date
3. Body
4. Signature Block

**Use when:** You are writing engagement letters, formal correspondence, or notices.

```bash
briefkit generate docs/engagement-letter/ --template letter --preset charcoal
```

---

### `contract`

Legal agreement with structured clauses.

**Sections produced:**
1. Title Page
2. Recitals
3. Definitions
4. Numbered Clauses
5. Schedules
6. Execution / Signature Block

**Use when:** You are drafting service agreements, NDAs, or other legal contracts.

```bash
briefkit generate docs/services-agreement/ --template contract --preset navy
```

---

### `register`

Table-dominant layout. Persistent column headers across pages.

**Sections produced:**
1. Title
2. Consolidated Table (merged from all numbered files)
3. Summary Statistics

**Use when:** Your content is primarily tabular -- risk registers, compliance matrices, data dictionaries, asset inventories.

```bash
briefkit generate docs/risk-register/ --template register --preset slate
```

---

### `minutes`

Meeting minutes with auto-extracted action items and resolutions.

**Sections produced:**
1. Header
2. Attendees
3. Agenda Items
4. Action Items (auto-extracted)
5. Resolutions
6. Closing

**Use when:** You are recording board meetings, team standups, or committee sessions.

```bash
briefkit generate docs/board-meeting/ --template minutes --preset charcoal
```

---

## Comparing Templates

Generate the same content with different templates to see the structural differences:

```bash
briefkit generate docs/my-topic/ --template briefing --output briefing.pdf
briefkit generate docs/my-topic/ --template report   --output report.pdf
briefkit generate docs/my-topic/ --template academic  --output academic.pdf
briefkit generate docs/my-topic/ --template minimal   --output minimal.pdf
```

---

## Custom Templates

Create your own template by subclassing `BaseBriefingTemplate`:

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

Each `build_*` method returns a list of ReportLab flowables. Override any of them to customize output.

---

## Section Toggles

Disable individual sections in `briefkit.yml`:

```yaml
template:
  preset: briefing
  sections:
    cover: true
    toc: true
    executive_summary: true
    at_a_glance: false          # disable the metrics dashboard
    body: true
    cross_references: false     # disable cross-refs section
    key_terms: true
    bibliography: true
    back_cover: false           # disable back cover
```

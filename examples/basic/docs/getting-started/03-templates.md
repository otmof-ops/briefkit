# Templates

BriefKit includes six built-in templates, each designed for a specific document type. Every template produces a different PDF structure with sections tailored to its purpose.

## Template Comparison

| Template | Best For | Key Sections | When to Use |
|----------|----------|-------------|-------------|
| `briefing` | Executive briefings, technical docs | Cover, TOC, Executive Summary, Dashboard, Body, Cross-Refs, Key Terms, Bibliography | Default choice for most documentation |
| `report` | Formal assessments, audits | Cover, TOC, Abstract, Methodology, Findings, Recommendations, Bibliography | When you need a structured findings report |
| `academic` | Research papers, literature reviews | Title Page, Abstract, TOC, Literature Review, Body, References, Appendices | For scholarly or research-oriented content |
| `manual` | SOPs, equipment manuals, runbooks | Cover, Revision History, TOC, Safety Warnings, Procedures, Troubleshooting | For procedural documentation with warnings |
| `book` | Textbooks, comprehensive guides | Half Title, Title Page, Copyright, TOC, Preface, Chapters, Glossary, Index | For long-form, multi-chapter content |
| `minimal` | Quick exports, reference cards | Title, TOC, Body, Bibliography | When you need a clean, no-frills PDF |

## Selecting a Template

### Via Command Line

```bash
briefkit generate docs/my-content/ --template report
```

### Via Configuration File

```yaml
# briefkit.yml
template:
  preset: "report"
```

## Try Each Template

This examples directory includes one complete doc-set for each template. Generate them all to compare:

```bash
# Default briefing template
cd ../briefing-template && briefkit generate docs/cognitive-load-theory/

# Formal report
cd ../report-template && briefkit generate docs/curriculum-effectiveness/

# Academic paper
cd ../academic-template && briefkit generate docs/learning-theory-review/

# Technical manual
cd ../manual-template && briefkit generate docs/lms-administration/

# Book format
cd ../book-template && briefkit generate docs/education-foundations/

# Minimal output
cd ../minimal-template && briefkit generate docs/assessment-quick-reference/
```

> Each template interprets the same markdown input differently. The briefing template extracts an executive summary and metrics dashboard. The report template organizes content into methodology, findings, and recommendations. The academic template adds a literature review and formal references section.

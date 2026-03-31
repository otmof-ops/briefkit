# Templates

BriefKit ships with 6 built-in templates. Select one via config or CLI flag.

## briefing (default)

The executive briefing format. Professional, structured, data-rich.

```
Cover → Classification Banner → TOC → Executive Summary → At a Glance →
Body → Cross-References → Key Terms → Bibliography → Back Cover
```

Best for: Technical documentation, research analysis, knowledge bases, API docs.

## report

Formal report format. Less visual flair, more structured analysis.

```
Cover → TOC → Abstract → Methodology → Findings →
Discussion → Recommendations → Appendices → Bibliography → Back Cover
```

Best for: Audit reports, compliance reports, incident reports, assessments.

## book

Long-form book/manual format. Chapter-based, designed for 100+ pages.

```
Half Title → Title Page → Copyright Page → TOC → Preface →
Chapters → Glossary → Bibliography → Index → Colophon
```

Best for: Technical manuals, textbooks, comprehensive guides.

## manual

Technical manual / SOP format. Procedure-focused, reference-heavy.

```
Cover → Revision History → TOC → Safety Warnings →
Scope → Procedures → Reference Tables → Troubleshooting → Bibliography → Back Cover
```

Best for: SOPs, equipment manuals, runbooks, playbooks.

## academic

Academic paper / thesis format. Citation-heavy, formal structure.

```
Title Page → Abstract → TOC → Introduction → Literature Review →
Body → Results → Discussion → Conclusion → References → Appendices
```

Best for: Research papers, white papers, theses, conference submissions.

## minimal

Stripped-down format. Content only, minimal chrome.

```
Title → TOC → Body → Bibliography
```

Best for: Quick exports, internal notes, simple PDF output from markdown.

## Usage

```bash
# CLI
briefkit generate docs/ --template report

# Config
template:
  preset: "report"
```

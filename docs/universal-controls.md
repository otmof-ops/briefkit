# Universal Template Controls

Every briefkit template honours the same set of architectural switches
and guard rails, so your `briefkit.yml` config behaves identically
regardless of which template you choose. This is the reference for
those universal controls.

If you previously found a feature you liked in the `novel` or `book`
template and wondered why it was not available in your chosen template,
it probably is now. These controls are baked into the base class and
apply to all 29 built-in templates (plus any custom templates you
author — they inherit the guard rails for free).

---

## Skip flags

Suppress any optional front-matter or back-matter section by setting
a `project.skip_<section>: true` flag. The section drops out of both
the table of contents and the final PDF, and any page break that would
have surrounded it is collapsed, so you never see a blank page where
a skipped section used to live.

All skip flags default to `false` (= render the section). Flags that
name a section the current template does not build are silently
ignored — this means a single `briefkit.yml` can carry a full skip
manifest and work across every template without error.

### Front matter

| Flag | Suppresses | Templates that honour it |
|---|---|---|
| `skip_half_title` | Half-title page | book, novel |
| `skip_title_page` | Full title page | book, novel, academic, whitepaper |
| `skip_copyright_page` | Copyright / colophon front-page | book, novel |
| `skip_toc` | Table of contents | every template with a TOC |
| `skip_foreword` | Foreword | book, novel |
| `skip_preface` | Preface | book, novel, academic, manual, report |
| `skip_acknowledgments` | Acknowledgments | book, academic, proposal, whitepaper |
| `skip_abstract` | Abstract | academic, report, whitepaper, deep_research |
| `skip_executive_summary` | Executive summary | briefing, report, proposal, policy, evaluation |
| `skip_dashboard` | At-a-glance / metric dashboard | briefing, evaluation |
| `skip_introduction` | Numbered introduction section | academic, whitepaper |
| `skip_scope` | Scope statement | manual, sop, policy |

### Body sections

| Flag | Suppresses | Templates |
|---|---|---|
| `skip_methodology` | Methodology section | academic, report |
| `skip_literature_review` | Literature review | academic |
| `skip_results` | Results section | academic, report, evaluation |
| `skip_discussion` | Discussion section | academic, report |
| `skip_findings` | Findings section | report, evaluation |
| `skip_recommendations` | Recommendations | report, proposal, evaluation |
| `skip_conclusion` | Conclusion | academic, report, whitepaper |

### Back matter

| Flag | Suppresses | Templates |
|---|---|---|
| `skip_references` | References section | academic, deep_research, whitepaper |
| `skip_bibliography` | Bibliography | almost every template |
| `skip_glossary` | Glossary | book, novel, manual, academic, policy, guide |
| `skip_index` | Key terms index | book, manual |
| `skip_appendices` | Appendices | academic, report, manual, whitepaper |
| `skip_revision_history` | Revision / version history | manual, sop, policy, playbook |
| `skip_safety_warnings` | Safety warnings section | manual, sop |
| `skip_troubleshooting` | Troubleshooting | manual |
| `skip_reference_tables` | Reference tables | manual |
| `skip_colophon` | Closing colophon | book, novel |
| `skip_back_cover` | Back cover page | briefing, report, manual, proposal, evaluation |

### Example

```yaml
# briefkit.yml
project:
  name: "Q1 Engineering Review"

  # Trim a noisy briefing down to the essentials
  skip_half_title: true
  skip_copyright_page: true
  skip_preface: true
  skip_acknowledgments: true
  skip_bibliography: true
  skip_colophon: true
  skip_back_cover: true
```

Any flag you set but the chosen template doesn't build is a no-op, so
you can keep a single "lean" skip manifest and reuse it across book,
report, and academic output.

---

## Spacing and page-break controls

### `section_break_mode`

Controls how briefkit transitions between major sections.

| Value | Behaviour |
|---|---|
| `auto` *(default)* | `CondPageBreak` — only forces a new page when less than `min_section_space_mm` of vertical space remains. Small sections flow onto the same page; large ones start fresh. |
| `hard` | Always `PageBreak`. Classic recto-start behaviour. Produces more pages but every section begins on a fresh one. |
| `flow` | No automatic break. Sections flow continuously; insert your own visual separators upstream if needed. |

```yaml
project:
  section_break_mode: "auto"     # default — no unnecessary blank pages
  min_section_space_mm: 80       # CondPageBreak threshold
```

The `auto` default fixes the "big gaps between sections that make no
sense" problem — a one-paragraph abstract followed by a one-row
revision history no longer produces two half-empty pages.

### `max_spacer_mm`

Hard cap on any single `Spacer` flowable, applied anywhere a template
uses the `capped_spacer` helper. Prevents accidental massive gaps when
a template tuned for one page size is used on another.

```yaml
project:
  max_spacer_mm: 60              # default: 60 mm
```

Cover, title, half-title, and colophon pages explicitly opt out of
this cap since their layouts legitimately use large spacers as design
elements.

---

## Orphan-title protection

Every template is automatically protected against orphaned chapter /
section titles. When briefkit renders the final story, it walks the
flowable list and wraps every bare `H1` paragraph with its next
content flowable in a `KeepTogether` block. This prevents the
scenario where an `H1` title is stranded alone on an otherwise-empty
page because the chapter's first table / figure / code block was too
large to fit on the remaining space.

This is enforced in `BaseBriefingTemplate._protect_section_headings`
and runs on every template, including custom templates you author.

### Escape hatch

If you genuinely want the raw unprotected story (e.g. for debugging
a layout bug, or because your template expects specific orphaning
behaviour):

```yaml
project:
  disable_orphan_protection: true
```

---

## Empty-page collapse

Skipped optional sections often leave behind adjacent `PageBreak`
flowables (`PageBreak → (skipped section) → PageBreak`), which
ReportLab renders as a blank page. briefkit automatically collapses
any run of adjacent page-break flowables into a single break, so
aggressive use of the skip flags never produces mystery blank pages.

### Escape hatch

```yaml
project:
  disable_empty_page_collapse: true
```

---

## Full configuration surface

```yaml
project:
  # Skip flags (all default false)
  skip_half_title:              false
  skip_title_page:              false
  skip_copyright_page:          false
  skip_toc:                     false
  skip_foreword:                false
  skip_preface:                 false
  skip_acknowledgments:         false
  skip_abstract:                false
  skip_executive_summary:       false
  skip_dashboard:               false
  skip_introduction:            false
  skip_scope:                   false
  skip_methodology:             false
  skip_literature_review:       false
  skip_results:                 false
  skip_discussion:              false
  skip_findings:                false
  skip_recommendations:         false
  skip_conclusion:              false
  skip_references:              false
  skip_bibliography:            false
  skip_glossary:                false
  skip_index:                   false
  skip_appendices:              false
  skip_revision_history:        false
  skip_safety_warnings:         false
  skip_troubleshooting:         false
  skip_reference_tables:        false
  skip_colophon:                false
  skip_back_cover:              false

  # Spacing
  section_break_mode:           "auto"   # auto | hard | flow
  min_section_space_mm:         80
  max_spacer_mm:                60

  # Escape hatches
  disable_orphan_protection:    false
  disable_empty_page_collapse:  false
```

---

## See also

- [Directory Structure Guide](directory-structure.md) — how to organise source files
- [Templates Guide](templates-guide.md) — which template produces which sections
- [Configuration](configuration.md) — full `briefkit.yml` reference
- [Custom Templates](custom-templates.md) — authoring your own template (inherits guard rails automatically)

# Turning a Novel Manuscript into a Book PDF

## Overview

BriefKit's book template generates professional book PDFs from structured markdown: half-title, title page, copyright page, table of contents, preface, chapters, glossary, and colophon. This tutorial walks through the complete process of converting a single-file markdown novel into a finished book.

This process was validated by generating a 113-page PDF from a 50,000-word horror novel (*The Backrooms: A Jcore Adaptation*). Every section below reflects lessons learned from that real production run.

---

## Prerequisites

- Python 3.10+
- BriefKit installed (`pip install briefkit` or from source)
- A markdown novel manuscript (single file or already split)

---

## Step 1: Understand the Directory Structure

BriefKit's book template expects a flat directory of numbered markdown files:

```
my-book/
  briefkit.yml          # Config (at project root, NOT inside docs/)
  docs/
    my-novel/
      README.md         # Title + brief description
      preface.md        # Optional: preface content
      glossary.md       # Optional: term definitions
      01-part-one.md    # First chapter/part
      02-part-two.md    # Second chapter/part
      ...
```

Key rules:
- Each `NN-name.md` file becomes one "chapter" in the PDF
- The H1 heading (`# ...`) in each file becomes the chapter title
- H2 headings (`## ...`) become sub-sections within the chapter
- `README.md` provides the book title and overview
- `preface.md` is used as the preface if present (otherwise BriefKit generates one from README)
- `glossary.md` is rendered as a proper glossary if present (otherwise BriefKit auto-extracts terms from headings, which produces junk for novels)

### File naming conventions

Use zero-padded two-digit prefixes to control chapter order:

```
01-opening.md
02-descent.md
03-the-levels.md
...
12-final-chapter.md
```

BriefKit sorts files lexicographically. Zero-padding ensures correct order up to 99 chapters. If you have more, use three digits (`001-`, `002-`, ...).

Avoid spaces in filenames. Use hyphens. Keep names short and descriptive — they are not displayed in the PDF, but they help you navigate the source.

---

## Step 2: Split Your Manuscript

If your novel is a single markdown file, split it at major structural breaks.

### Choosing split points

For a novel with Parts/Acts: one file per Part.
For a novel with only chapters: group into logical sections of 3-8 chapters each, or one file per chapter if chapters are short.

Split points to consider:
- Part/Act boundaries (strongest option)
- Major time jumps or POV shifts
- Scene breaks that already function as structural markers
- Natural pacing beats (inciting incident, midpoint, climax)

Avoid splitting mid-scene or mid-chapter. The PDF will work, but it makes the source harder to manage.

### Heading conversion

BriefKit uses H1 for chapter titles. If your manuscript uses a different heading hierarchy, convert before splitting:

| Original | Convert To | Role in PDF |
|----------|-----------|-------------|
| `## Part 1 — The Beginning` | `# Part 1 — The Beginning` | Chapter title |
| `### Chapter 1: First Light` | `## Chapter 1: First Light` | Sub-section heading |
| `#### Scene header` | `### Scene header` | Sub-sub-section (renders smaller) |

If your manuscript has no structural headings at all (prose only), add H1 headings to the top of each file you create. The template requires at least one H1 per chapter file.

### Example Python split script

This script splits a manuscript at Part headers and writes numbered chapter files:

```python
import re
import os

src = "manuscript.md"
out = "docs/my-novel/"
os.makedirs(out, exist_ok=True)

with open(src, encoding="utf-8") as f:
    content = f.read()

# Split at Part headers (adjust regex to match your heading style)
parts = re.split(r'(?=## Part \d+)', content)

for i, part in enumerate(parts[1:], 1):  # skip front matter before first Part
    # Convert heading levels
    part = re.sub(r'^## (Part \d+)', r'# \1', part, count=1, flags=re.MULTILINE)
    part = re.sub(r'^### (Chapter \d+)', r'## \1', part, flags=re.MULTILINE)

    # Generate filename from H1 title
    title_match = re.match(r'# (.+)', part)
    if not title_match:
        continue
    title_text = title_match.group(1)
    name = re.sub(r'[^a-z0-9]+', '-', title_text.lower()).strip('-')
    filename = f"{i:02d}-{name}.md"

    filepath = os.path.join(out, filename)
    with open(filepath, 'w', encoding="utf-8") as f:
        f.write(part.rstrip() + "\n")
    print(f"Wrote: {filename}  ({len(part.split()):,} words approx)")
```

Run it:

```bash
python split_manuscript.py
```

Check the output:

```bash
ls -lh docs/my-novel/
wc -w docs/my-novel/*.md
```

### Splitting at chapter level instead of part level

If you want one file per chapter rather than one per part, adjust the regex:

```python
# Split at any Chapter header
parts = re.split(r'(?=### Chapter \d+)', content)
```

Then convert `### Chapter N` to `# Chapter N` in each chunk.

### What to strip during splitting

Remove the following content during or after splitting — it either breaks the PDF renderer or produces duplicate content:

- **Rewrite notes and craft logs** — editorial scaffolding like "REWRITE: tighten this scene" should not appear in the final PDF
- **HTML entities** (`&nbsp;`, `&mdash;`, `&hellip;`) — ReportLab (BriefKit's PDF engine) does not interpret HTML entities; they render as literal text (e.g., `&nbsp;` appears as-is in the PDF)
- **Back matter** — END markers, manual copyright lines, "The End" banners, acknowledgments that duplicate what the template generates
- **Draft headers** — lines like "Rewritten Chapters 1-10" or "DRAFT 3" at the top of sections
- **Markdown comments** — `<!-- editor note -->` blocks (these are invisible in web rendering but may cause issues in PDF)

Strip HTML entities with a quick Python pass:

```python
import html

with open("docs/my-novel/01-opening.md", encoding="utf-8") as f:
    content = f.read()

# Unescape HTML entities to plain Unicode
content = html.unescape(content)

# Or strip &nbsp; specifically
content = content.replace("&nbsp;", " ")

with open("docs/my-novel/01-opening.md", "w", encoding="utf-8") as f:
    f.write(content)
```

Apply this to all chapter files after splitting.

---

## Step 3: Create Supporting Files

### README.md

The README provides the book title and a brief description. Keep it short — it is used internally by BriefKit, not displayed as a page in the PDF.

```markdown
# My Novel Title

A brief description of the book for internal reference. One or two sentences is enough.
```

Do not put the full synopsis or author bio here. Those belong in `preface.md`.

### preface.md (optional but recommended)

Write your actual preface. This is the content that appears in the Preface section of the PDF, before Chapter 1.

```markdown
# Preface

This novel began as a short story in 2024, a single hallway extending forever in both
directions. What you hold now is that hallway made into a world.

The Backrooms mythology — the shared folklore of liminal spaces — belongs to everyone who
has contributed to it. This adaptation draws from that collective imagination while telling
a specific story about one person's journey through it.

Read slowly. The spaces between scenes matter.
```

If you omit `preface.md`, BriefKit generates a generic preface from the README description. This works but produces a thin, generic page. Write your own.

### glossary.md (optional but important for genre fiction)

For horror, fantasy, science fiction, or any genre with invented terminology, a glossary adds polish and prevents a broken auto-generated one.

```markdown
# Glossary

**The Backrooms** — A vast non-Euclidean space existing outside normal reality, accessible
by "noclipping" through the geometry of the physical world. Consists of numbered Levels,
each with distinct properties and dangers.

**Level 0** — The entry point. An infinite expanse of yellow-wallpapered rooms under
humming fluorescent lights. Smell of wet carpet. No exits visible.

**Level 1** — Concrete warehouse. Industrial shelving, flickering lights. Supplies appear
occasionally. Considered relatively safe.

**Noclip** — The act of passing through solid geometry into the Backrooms, typically
by accident. Named after the video game cheat code that disables collision detection.

**The Wanderers** — Term for humans trapped in the Backrooms, whether recent arrivals or
long-term survivors who have adapted to its rules.

**Smilers** — An entity type found primarily on lower levels. Characterized by a luminous
smile visible in darkness. Avoid direct eye contact.
```

If you do not create a `glossary.md`, BriefKit auto-extracts "terms" from your H2 headings. For a novel, this means chapter sub-section titles appear as glossary entries — which is meaningless and looks unprofessional. Always create a `glossary.md` for novels, even if it only has a few entries.

To suppress the glossary entirely, leave `glossary.md` empty or omit it and note that the auto-generated glossary will still appear. The cleanest solution is to provide real terms.

---

## Step 4: Configure briefkit.yml

Place the config file at your **project root** (not inside `docs/`). This is a common mistake — if briefkit.yml is inside the docs directory, BriefKit will not find it without an explicit `--config` flag pointing to it, and if it does find it, hierarchy detection breaks.

```yaml
project:
  name: "My Novel Title"
  org: "Publisher Name"
  tagline: "A Subtitle or Genre Tag"

brand:
  preset: "gothic"                    # or: ink, charcoal, mono, crimson
  org: "Publisher Name"
  copyright: "(c) 2026 Publisher · CC BY-NC-SA 4.0"

template:
  preset: "book"

content:
  max_words_per_section: 10000        # Default 3000 is too low for novels

hierarchy:
  root_level: 3                       # Treats the docs dir as a doc-set
  depth_to_level:
    0: 3
```

### Critical config notes

**`hierarchy.root_level: 3` is REQUIRED.** This is the most common source of broken output for novels. Without it, BriefKit's document hierarchy detector examines the project root, finds no doc-sets there, and reports "Extracted: 0 subsystems, 0 words." Setting `root_level: 3` tells BriefKit that your `docs/my-novel/` directory IS the document set, not a subdirectory within one.

**`content.max_words_per_section: 10000` prevents truncation.** The default value of 3000 words cuts off any chapter longer than roughly 12 pages. A typical horror novel chapter runs 2,000-5,000 words. Set this to 10000 to be safe. For very long chapters (10,000+ words), go higher.

**`template.preset: "book"` is required.** Without this, BriefKit defaults to its technical documentation template, which produces a corporate report layout instead of a book layout.

**The `--config` flag must point to the right file.** If you run BriefKit from a different working directory, use an absolute path:

```bash
briefkit generate /home/jay/my-book/docs/my-novel/ \
  --config /home/jay/my-book/briefkit.yml \
  --force --no-ids
```

### Full annotated config

```yaml
project:
  # Internal name. Appears in metadata, not prominently in the PDF itself.
  name: "The Backrooms: A Jcore Adaptation"

  # Organization or author name. Appears on title page and colophon.
  org: "Jcore Universe"

  # Subtitle or genre tag. Appears on title page beneath the main title.
  tagline: "A Liminal Horror Novel"

brand:
  # Visual preset. Controls fonts, colors, and accent styles.
  # Options: gothic, ink, charcoal, mono, crimson
  preset: "gothic"

  # Overrides the project.org for branding purposes (can be same value).
  org: "Jcore Universe"

  # Copyright string. Appears on the copyright page and in the colophon footer.
  copyright: "(c) 2026 Jcore Universe · All Rights Reserved"

template:
  # Use the book template. Without this, you get a technical docs layout.
  preset: "book"

content:
  # Maximum words extracted per section before truncation.
  # Default is 3000, which cuts off novel-length chapters.
  max_words_per_section: 10000

hierarchy:
  # root_level: 3 tells BriefKit the docs/my-novel/ directory IS the doc-set.
  # Without this, extraction yields 0 subsystems.
  root_level: 3
  depth_to_level:
    0: 3
```

---

## Step 5: Choose a Preset

BriefKit ships with several visual presets. For fiction, these are the most relevant:

| Preset | Typography | Background | Accents | Best For |
|--------|-----------|------------|---------|----------|
| `gothic` | Times-Roman serif | Warm off-white (#FAFAF5) | Muted brown (#8B7355) | Horror, literary fiction, atmospheric prose |
| `ink` | Times-Roman serif | Pure white | Dark navy | Literary fiction, general novels |
| `charcoal` | Helvetica sans-serif | White | Dark neutral gray | Contemporary fiction, thrillers |
| `mono` | Courier monospace | White | Black | Experimental, print-first, noir |
| `crimson` | Helvetica sans-serif | White | Deep red | Dark fiction, crime, gothic romance |

The `gothic` preset was purpose-built for horror fiction. It uses Times-Roman for readability, warm off-white paper to reduce eye strain over long reading sessions, and muted brown accents that evoke aged parchment without being ornate.

### Overriding individual brand values

You can use a preset as a base and override specific values:

```yaml
brand:
  preset: "gothic"

  # Override body font (must be a ReportLab built-in or registered font)
  font_body: "Times-Roman"

  # Override heading font
  font_heading: "Times-Bold"

  # Override body text color (hex)
  body_text: "#1C1C1C"

  # Override page background color
  background: "#FAFAF5"

  # Override accent color (used for rules, chapter number styling)
  accent: "#8B7355"

  # Override divider/rule color
  rule_color: "#C0B8A8"
```

### Font availability

BriefKit uses ReportLab for PDF generation. The available built-in fonts are:

- `Helvetica`, `Helvetica-Bold`, `Helvetica-Oblique`, `Helvetica-BoldOblique`
- `Times-Roman`, `Times-Bold`, `Times-Italic`, `Times-BoldItalic`
- `Courier`, `Courier-Bold`, `Courier-Oblique`, `Courier-BoldOblique`

Custom fonts (TTF/OTF) can be registered if you need them, but that requires code changes. The built-in fonts cover most fiction typography needs.

---

## Step 6: Generate the PDF

From your project root:

```bash
briefkit generate docs/my-novel/ --config briefkit.yml --force --no-ids
```

### What each flag does

| Flag | Effect |
|------|--------|
| `--force` | Regenerates even if output already exists. Always use this during iteration. |
| `--no-ids` | Skips document ID assignment (OTM-style IDs are for technical documentation, not novels). |
| `--verbose` | Prints extraction statistics. Useful for debugging missing content. |
| `--config PATH` | Explicitly points to briefkit.yml. Required if not running from project root. |

### Expected output (verbose mode)

When running correctly, you should see output similar to:

```
BriefKit v1.0.0 — Book Template
Loading config: briefkit.yml
Scanning: docs/my-novel/
  Found: README.md, preface.md, glossary.md
  Found: 12 chapter files (01-opening.md ... 12-finale.md)
Extracting content...
  Extracted: 12 chapters, 49,847 words
  Chapter word range: 2,100 – 5,900 words
Rendering PDF...
  Pages: 113
  Output: docs/my-novel/executive-briefing.pdf
Done.
```

Key things to verify in verbose output:
- Chapter count matches your file count
- Total word count is close to your manuscript word count (minor differences are normal due to stripping)
- No chapters show 0 words (indicates a parsing problem with that file)

### Rename the output

The book template always outputs to `executive-briefing.pdf` (a BriefKit convention). Rename it:

```bash
mv docs/my-novel/executive-briefing.pdf "My_Novel.pdf"
```

Or to a versioned name during drafts:

```bash
cp docs/my-novel/executive-briefing.pdf "My_Novel_$(date +%Y%m%d).pdf"
```

---

## Step 7: What the PDF Contains

The book template generates these pages in order:

### 1. Half-title page
The book title, centered, alone on the page. No author, no subtitle. Traditional book printing convention.

### 2. Title page
Full title, subtitle/tagline (from `project.tagline`), organization/author name (from `brand.org`), and publication year. This is the main title page.

### 3. Copyright page
Copyright notice (from `brand.copyright`), rights statement, and any additional legal text. Generated automatically.

### 4. Table of contents
Auto-generated from your chapter H1 headings with page numbers. If a chapter title is long, it wraps cleanly. Page numbers are right-aligned with dot leaders.

### 5. Preface
Content from `preface.md`. If not present, generated from README description.

### 6. Chapters
Each chapter starts on a new page. The H1 heading becomes the chapter title (rendered large, with an optional chapter number if you choose). H2 headings become section headers within the chapter. Body text is set in the preset's body font.

Chapter flow:
- Chapter title (H1) — large, centered or left-aligned depending on preset
- Optional decorative rule beneath the title
- Body text
- H2 sub-sections with styled headers
- Continued body text

### 7. Glossary
From `glossary.md` if present. Each bolded term becomes a definition entry. The glossary renders in a two-column layout by default: term on the left, definition on the right.

If `glossary.md` is absent, BriefKit auto-generates a glossary from H2 headings. For novels, this produces a useless list of chapter sub-headings. Always provide a real `glossary.md` or accept that the glossary page will look wrong.

### 8. Colophon
Final page. Includes: typeset date, organization name, copyright notice, and BriefKit attribution. The colophon signals the end of the book.

---

## Troubleshooting

### "Extracted: 0 subsystems, 0 words"

Your hierarchy config is wrong, or briefkit.yml is in the wrong location.

Fix:
1. Set `hierarchy.root_level: 3` in briefkit.yml
2. Set `hierarchy.depth_to_level: {0: 3}`
3. Ensure briefkit.yml is at the project root, NOT inside `docs/`
4. Run with `--config path/to/briefkit.yml` to be explicit

Verify with:
```bash
briefkit generate docs/my-novel/ --config briefkit.yml --force --no-ids --verbose
```

If you still see 0 words, check that your chapter files have H1 headings and non-empty body text.

---

### Chapters are truncated or missing

Symptoms: PDF generates, but some chapters end abruptly mid-sentence, or entire chapters after a certain point are absent.

Cause: `content.max_words_per_section` is set too low (default: 3000).

Fix:
```yaml
content:
  max_words_per_section: 10000
```

For very long chapters (10,000+ words each), increase to 15000 or 20000.

---

### HTML entities render as literal text

Symptom: Words like `&nbsp;`, `&mdash;`, or `&hellip;` appear verbatim in the PDF.

Cause: ReportLab does not parse HTML entities. BriefKit passes your markdown content through to ReportLab, which treats `&nbsp;` as the five characters `&`, `n`, `b`, `s`, `p`.

Fix — strip entities before generating:

```python
import html, os, glob

for path in glob.glob("docs/my-novel/*.md"):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    content = html.unescape(content)
    # Also catch any remaining naked & sequences that aren't real HTML
    content = content.replace("&nbsp;", "\u00a0")   # non-breaking space
    content = content.replace("&mdash;", "\u2014")  # em dash
    content = content.replace("&hellip;", "\u2026") # ellipsis
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
```

---

### Chapter numbers are doubled

Symptom: Chapter headings display as "Chapter 1 Part 1 — The Opening" when the file already starts with "# Part 1 — The Opening".

Cause: An older BriefKit version prepended its own "Chapter N" label before using your H1 heading as the title.

Fix: Update to BriefKit v1.0.0+. The template now uses your H1 heading verbatim as the chapter title without adding a prefix.

Workaround for older versions: Remove your own "Part N" / "Chapter N" labels and let BriefKit generate the numbers, or rename your H1 headings to avoid duplication.

---

### Footer text overlaps or is truncated

Symptom: Page number and copyright text overlap on the footer line, or the copyright string is cut off.

Cause: A layout bug in pre-1.0.0 versions where page number and footer text were placed on the same baseline.

Fix: Update to BriefKit v1.0.0+. Page number and copyright now render on separate lines within the footer.

Workaround for older versions: Shorten your `brand.copyright` string to under 60 characters.

---

### Chapter headings appear alone on empty pages

Symptom: A chapter title appears at the bottom of a page with no content following it. The actual content begins on the next page.

Cause: A page break occurs between the heading and its following paragraph.

Fix: Update to BriefKit v1.0.0+. The template now applies `keepWithNext` to all chapter headings, preventing orphaned titles.

---

### Glossary is just a list of chapter titles

Symptom: The Glossary section contains entries like "The Descent," "Into the Dark," "Awakening" — which are your chapter sub-headings, not glossary terms.

Cause: No `glossary.md` file was provided. BriefKit auto-extracts H2 headings as glossary terms.

Fix: Create `docs/my-novel/glossary.md` with real term definitions. See Step 3 for format.

---

### Duplicate content from back matter

Symptom: The PDF contains duplicate copyright notices, "The End" text, or repeated colophon content from the manuscript source.

Cause: The original manuscript contained back matter (copyright page, acknowledgments, "THE END" banner) that was not stripped during splitting.

Fix: Strip all back matter from your chapter files. The book template generates its own copyright page and colophon. Anything you leave in the source will appear in addition to the template's generated content.

Common things to strip:
- `---\n\n**THE END**`
- Manual copyright blocks
- "Thank you for reading..." acknowledgment text
- Dedication pages (unless you want them — but format them as a proper `dedication.md` file)

---

### PDF is much shorter than expected

Symptom: You have a 50,000-word manuscript but the PDF is only 30 pages.

Possible causes:

1. **Truncation** — Check `content.max_words_per_section`. Increase it.
2. **0 words extracted** — Run `--verbose` and check per-chapter word counts. A chapter showing 0 words likely has a malformed heading.
3. **Only first file rendered** — If BriefKit is treating your `docs/my-novel/` as a single document rather than a set, it may only read `README.md`. Check the hierarchy config.
4. **Wrong template** — Ensure `template.preset: "book"` is set.

---

### PDF file not generated / no output

Check for Python errors in the terminal output. Common causes:
- Missing required field in briefkit.yml
- A chapter file contains malformed markdown that crashes the parser
- Insufficient disk space
- Permissions issue on the output directory

Run with `--verbose` to narrow down where the failure occurs.

---

## Full Example

The `examples/novel-template/` directory contains a working example using the gothic preset with sample content from a horror novel. Use it as a reference or starting point.

```bash
cd /home/jay/briefkit
briefkit generate examples/novel-template/docs/backrooms-novel/ \
  --config examples/novel-template/briefkit.yml \
  --force --no-ids --verbose
```

Expected output: `examples/novel-template/docs/backrooms-novel/executive-briefing.pdf`

### Minimal working example from scratch

```bash
# 1. Create directory structure
mkdir -p my-book/docs/my-novel

# 2. Write config
cat > my-book/briefkit.yml << 'EOF'
project:
  name: "My Novel"
  org: "My Press"
  tagline: "A Novel"
brand:
  preset: "gothic"
  org: "My Press"
  copyright: "(c) 2026 My Press"
template:
  preset: "book"
content:
  max_words_per_section: 10000
hierarchy:
  root_level: 3
  depth_to_level:
    0: 3
EOF

# 3. Write README
cat > my-book/docs/my-novel/README.md << 'EOF'
# My Novel

A horror novel about liminal spaces.
EOF

# 4. Write a preface
cat > my-book/docs/my-novel/preface.md << 'EOF'
# Preface

This book began as a thought experiment. It became something else.
EOF

# 5. Write a chapter
cat > my-book/docs/my-novel/01-the-beginning.md << 'EOF'
# Part 1 — The Beginning

## Chapter 1: The Door

The door was always there. Most people never noticed it.

She noticed it on a Tuesday, which is the sort of day when such things happen.
The hallway behind it stretched further than it should have, lit by fluorescent tubes
that hummed at a frequency just below conscious hearing.

She stepped through.
EOF

# 6. Write a glossary
cat > my-book/docs/my-novel/glossary.md << 'EOF'
# Glossary

**The Liminal** — Spaces that exist between defined places; thresholds, waiting rooms,
empty hallways. In folk tradition, sites of transition and potential transformation.

**The Door** — Not a specific door, but a door. Recognizable by the way it seems
to be waiting for you.
EOF

# 7. Generate
briefkit generate my-book/docs/my-novel/ \
  --config my-book/briefkit.yml \
  --force --no-ids --verbose

# 8. Rename output
mv my-book/docs/my-novel/executive-briefing.pdf my-book/My_Novel.pdf
echo "Done. PDF at: my-book/My_Novel.pdf"
```

---

## The Gothic Preset

The `gothic` preset was designed specifically for horror and literary fiction. It prioritizes readability and atmosphere over corporate branding.

### Design values

| Property | Value | Rationale |
|----------|-------|-----------|
| Body font | Times-Roman | Literary tradition; easier to read than sans-serif in long prose |
| Heading font | Times-Bold | Consistent with body; authoritative without being corporate |
| Body text color | `#1C1C1C` (near-black) | Readable without the harshness of pure black on white |
| Page background | `#FAFAF5` (warm off-white) | Easier on the eyes than pure white; reduces glare in digital reading |
| Accent color | `#8B7355` (muted brown) | Aged parchment; appropriate for horror and Gothic fiction |
| Rule/divider color | `#C0B8A8` (warm gray) | Subtle; does not compete with text |
| Chapter title style | Large, centered | Classic book typography |

### Where it came from

The gothic preset was created during production of *The Backrooms: A Jcore Adaptation*, a 50,000-word liminal horror novel that became the first BriefKit book. The design brief: readable for long sittings, atmospheric without being theatrical, and appropriate for digital distribution.

### When to use gothic

Use gothic for:
- Horror fiction (obviously)
- Gothic romance
- Literary fiction with atmospheric or dark themes
- Historical fiction
- Anything where "old book" aesthetics serve the story

Do not use gothic for:
- Contemporary fiction that should feel modern (use `ink` or `charcoal`)
- Children's books or light comedy
- Science fiction with a technological aesthetic (use `mono`)

### Customizing gothic

```yaml
brand:
  preset: "gothic"

  # Make it darker and more intense
  body_text: "#0D0D0D"
  background: "#F5F0E8"
  accent: "#6B4F2A"

  # Or lighter and more readable
  body_text: "#2A2A2A"
  background: "#FFFFFF"
  accent: "#A09070"
```

---

## Production Checklist

Before generating your final PDF, verify:

- [ ] All chapter files are zero-padded and in correct order
- [ ] Every chapter file has an H1 heading as its first heading
- [ ] HTML entities stripped from all chapter files
- [ ] Back matter stripped from all chapter files
- [ ] `README.md` present with book title
- [ ] `preface.md` written (not auto-generated)
- [ ] `glossary.md` created with real terms
- [ ] `briefkit.yml` at project root (not inside `docs/`)
- [ ] `hierarchy.root_level: 3` set in config
- [ ] `content.max_words_per_section: 10000` set in config
- [ ] `template.preset: "book"` set in config
- [ ] Run with `--verbose` to verify all chapters extracted
- [ ] Total word count in verbose output close to manuscript word count
- [ ] Renamed output from `executive-briefing.pdf` to final filename
- [ ] Opened PDF and verified: title page, TOC, all chapters present, no truncation

---

## Reference

### briefkit.yml full schema for books

```yaml
project:
  name: string               # Book title (required)
  org: string                # Author or publisher (required)
  tagline: string            # Subtitle or genre tag (optional)

brand:
  preset: string             # gothic | ink | charcoal | mono | crimson
  org: string                # Display org on title page
  copyright: string          # Copyright notice string
  font_body: string          # ReportLab font name (optional override)
  font_heading: string       # ReportLab font name (optional override)
  body_text: string          # Hex color for body text (optional override)
  background: string         # Hex color for page background (optional override)
  accent: string             # Hex color for accents (optional override)
  rule_color: string         # Hex color for rules/dividers (optional override)

template:
  preset: "book"             # Required for book output

content:
  max_words_per_section: int # Truncation limit per chapter (default: 3000)

hierarchy:
  root_level: 3              # Required for docs/ directory structure
  depth_to_level:
    0: 3                     # Required alongside root_level
```

### CLI reference for novel generation

```bash
# Standard generate command
briefkit generate DOCSET_PATH --config CONFIG_PATH --force --no-ids

# With verbose output for debugging
briefkit generate DOCSET_PATH --config CONFIG_PATH --force --no-ids --verbose

# Check BriefKit version
briefkit --version

# List available presets
briefkit presets

# Validate config without generating
briefkit validate --config CONFIG_PATH
```

### File structure quick reference

```
project-root/
  briefkit.yml               ← Config here (REQUIRED at root)
  docs/
    my-novel/
      README.md              ← Book title + description (REQUIRED)
      preface.md             ← Preface content (recommended)
      glossary.md            ← Term definitions (recommended for genre fiction)
      01-chapter-one.md      ← Chapter files (at least 1 required)
      02-chapter-two.md
      ...
      NN-chapter-last.md
```

Output after generation:
```
  docs/
    my-novel/
      executive-briefing.pdf ← Generated PDF (rename this)
```


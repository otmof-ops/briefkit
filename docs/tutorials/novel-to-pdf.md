# Tutorial: Turning a Markdown Novel into a BriefKit PDF

This tutorial walks through the complete process of converting a novel manuscript — whether a single file or a collection of files — into a professionally typeset PDF using BriefKit's `novel` template. It covers directory structure, configuration, heading conventions, the split script, preset selection, the generate command, and every known issue encountered during the production of a full-length novel PDF, including the Backrooms session that originated the `novel` template.

By the end you will be able to take any markdown manuscript and produce a print-ready book with a half-title page, title page, copyright page, table of contents, preface, narrative-aware chapter content, glossary, and colophon.

---

## 1. Prerequisites

- BriefKit installed (`pip install briefkit`). Verify with `briefkit --version`.
- A markdown novel manuscript. This can be a single `.md` file or a collection of files you have already begun to split. The manuscript should be in plain markdown — no HTML entities such as `&nbsp;` or `&amp;`, no embedded HTML tags. BriefKit uses ReportLab, not a browser, and HTML entities render as literal strings.
- A plain text editor or IDE.

---

## 2. Understanding BriefKit's Novel Template

The `novel` template is purpose-built for fiction. It extends the `book` template with two major improvements: continuous flow pagination and automatic narrative formatting for meta-textual elements common in literary fiction and genre prose.

### What the novel template generates

The novel template produces the following pages in order:

1. Half-title page (title centered, nothing else)
2. Full title page (title, tagline/subtitle, organization, year)
3. Copyright page
4. Table of contents
5. Preface (from `preface.md` if present, otherwise from README overview)
6. Chapters (continuous flow, with narrative-aware formatting applied automatically)
7. Glossary (from `glossary.md` if present, otherwise auto-extracted terms — see section 8g)
8. Colophon (title, organization, decorative rule, copyright, fiction disclaimer, first edition date)

### The novel template versus the book template

The critical difference between `novel` and `book` is how page breaks between Parts are handled.

The `book` template forces a `PageBreak` after every chapter file. This mirrors the behavior of academic and technical document templates, where each chapter starts on a fresh page regardless of where the previous chapter ended. For fiction, this creates half-empty pages whenever a Part ends mid-page — an artifact that wastes space and looks typographically wrong.

The `novel` template replaces forced page breaks with `CondPageBreak(80mm)`: a conditional break that only inserts a new page if fewer than 80mm remain on the current page. Parts flow continuously with their heading providing the visual separation. In the Backrooms novel, this change alone reduced the PDF from 117 pages to 109 pages.

### Directory structure

BriefKit reads from a flat directory. The novel template expects the following layout:

```
your-project/
  briefkit.yml             # Config file at project root
  docs/
    your-novel/
      README.md            # Title and brief description
      preface.md           # Preface content (optional but recommended)
      glossary.md          # Glossary page (optional but recommended)
      01-part-one.md       # Part / chapter files, numbered
      02-part-two.md
      03-part-three.md
      ...
```

The `README.md` file sets the document title (from its first `# Heading`) and the project description. The numbered files — any file matching the pattern `[0-9][0-9]-*.md` — become the chapters of the book, rendered in numeric order.

### How headings map to the PDF

Within each numbered chapter file, heading levels map directly to the PDF structure:

- `# H1` — the Part or chapter title, rendered as the large chapter header; appears in the table of contents
- `## H2` — a chapter heading within a Part, rendered as a section heading in the body
- `### H3` — a sub-section, rendered smaller

The convention for a novel structured by Parts and Chapters is:

```markdown
# Part 1 — Level 0: The Lobby

## Chapter 1: The First Step

Prose content here...

## Chapter 2: The Sound

More prose content...
```

Each numbered file has exactly one `# H1` at the top. Subsequent headings within the file are `## H2` or lower.

---

## 3. Splitting a Single Manuscript into BriefKit Format

Most novel manuscripts start as a single file. The following steps convert a single-file manuscript into the directory structure BriefKit expects. A Python split script that automates the majority of this work is provided in section 3.3.

### 3.1 Manual split steps

**Step 1: Create the source directory.**

```bash
mkdir -p my-novel/docs/novel-name
```

The outer directory (`my-novel/`) will hold `briefkit.yml`. The inner directory (`my-novel/docs/novel-name/`) is where the markdown files live and where BriefKit will write the PDF.

**Step 2: Identify structural breaks.**

Open your manuscript and identify the major structural divisions. For a novel these are typically Parts, Acts, or Books. Each major division becomes one numbered file. Chapters within each Part become `## H2` headings within that file.

**Step 3: Create the numbered files.**

For each Part or major section, create a numbered file with a two-digit prefix controlling sort order and a kebab-case name:

```
01-part-one.md
02-part-two.md
99-coda.md
```

**Step 4: Convert heading levels.**

BriefKit reads your `# H1` as the chapter/Part title. Adjust heading levels accordingly:

| Original in manuscript | Convert to in BriefKit file | Role in PDF |
|------------------------|----------------------------|------------|
| `## Part I` or `# Part I` | `# Part I — Subtitle` | Chapter title (appears in TOC) |
| `### Chapter 1` or `## Chapter 1` | `## Chapter 1: Name` | Section heading in body |
| `#### Scene` | `### Scene` | Minor sub-section |

**Step 5: Strip back matter.**

If your manuscript file includes back matter — an END marker, copyright notice, acknowledgments, author biography — strip it before splitting. BriefKit generates its own copyright page and colophon. Including a manuscript copyright block in the body content will result in duplicate copyright text appearing in the chapter content.

**Step 6: Strip HTML entities.**

If your manuscript was written in or exported from a tool that uses HTML entities, replace them before importing:

```bash
sed -i 's/&nbsp;/ /g; s/&amp;/\&/g; s/&lt;/</g; s/&gt;/>/g; s/&mdash;/—/g; s/&ndash;/–/g' manuscript.md
```

BriefKit uses ReportLab for PDF generation, not a browser or HTML renderer. HTML entities are not interpreted — they render as the literal string `&nbsp;` in the PDF.

**Step 7: Create README.md.**

Create `README.md` in the docs directory with the novel's title as an `# H1` heading and a brief description as the first paragraph:

```markdown
# The Backrooms

A horror novel set in the labyrinthine spaces that exist between the walls of the known world.
```

**Step 8: Create preface.md (optional but recommended).**

Create `preface.md` in the docs directory. BriefKit uses it verbatim as the preface page:

```markdown
# Preface

Your preface content here.
```

If you skip this file, BriefKit generates a generic preface from the README overview text. For a novel, writing an actual preface produces a far better result.

**Step 9: Create glossary.md (optional but recommended for fiction).**

If your novel has world-specific terminology, create `glossary.md`:

```markdown
# Glossary

**term** — Definition of the term.

**another term** — Definition of another term.
```

If you skip this file, BriefKit's automatic term extractor will attempt to derive glossary terms from H2 headings in your chapter files. For fiction, this extracts chapter names as glossary entries, which is not useful. Always provide a real `glossary.md` for novel projects.

### 3.2 Strikethrough support

BriefKit supports the `~~strikethrough~~` markdown convention. It renders as `<strike>text</strike>` in the PDF output. This is active in all templates.

### 3.3 Automated split script (v2)

The following Python script automates the split for a single-file manuscript structured with `## Part N` and `### Chapter N` headings. It:

- Extracts the main content starting from Part 1
- Stops before the Coda (writes it as a separate `99-coda.md`)
- Strips END markers and raw copyright blocks from the body text
- Converts heading levels (`## Part` to `# Part`, `### Chapter` to `## Chapter`)

Save this as `split.py` at your project root and adjust the `src`, `out`, and `title` variables:

```python
import re, os

src = "manuscript.md"
out = "docs/my-novel/"
title = "My Novel Title"
os.makedirs(out, exist_ok=True)

with open(src) as f:
    content = f.read()

# Find structural boundaries
front_end = content.find("## Part 1")
coda_start = content.find("## Coda")
end_marker = content.find("\nEND\n")

# Main content without Coda and back matter
main = content[front_end:coda_start].rstrip() if coda_start > 0 else content[front_end:]

# README
with open(os.path.join(out, "README.md"), 'w') as f:
    f.write(f"# {title}\n\nBrief description.\n")

# Split at Part headers
parts = re.split(r'(?=## Part \d+)', main)
for i, part in enumerate([p for p in parts if p.strip()], 1):
    part = re.sub(r'^## (Part \d+)', r'# \1', part, count=1)
    part = re.sub(r'### (Chapter \d+)', r'## \1', part)
    title_match = re.match(r'# (.+)', part)
    name = re.sub(r'[^a-z0-9]+', '-', title_match.group(1).lower()).strip('-')
    with open(os.path.join(out, f"{i:02d}-{name}.md"), 'w') as f:
        f.write(part.rstrip() + "\n")

# Coda
if coda_start > 0:
    coda = content[coda_start:end_marker].strip() if end_marker > 0 else content[coda_start:].strip()
    coda = re.sub(r'^## Coda', '# Coda', coda)
    with open(os.path.join(out, "99-coda.md"), 'w') as f:
        f.write(coda.rstrip() + "\n")
```

Run it from the project root:

```bash
python split.py
```

After running, add `preface.md` and `glossary.md` to the docs directory manually.

---

## 4. Configuration (briefkit.yml)

The configuration file controls the project identity, visual preset, template selection, and content extraction settings. It must be placed at the project root — the directory that contains the `docs/` folder — not inside the docs directory itself.

Below is the complete configuration for a novel project:

```yaml
project:
  name: "My Novel Title"
  org: "Publisher Name"
  tagline: "A Subtitle or Genre Tag"

brand:
  preset: "gothic"
  org: "Publisher Name"
  copyright: "(c) 2026 Publisher · CC BY-NC-SA 4.0"

template:
  preset: "novel"

content:
  max_words_per_section: 10000

hierarchy:
  root_level: 3
  depth_to_level:
    0: 3
```

### Key configuration fields explained

**`project.name`** — The novel's title as it appears on the title page, half-title page, and running headers. Separate from the `# H1` in `README.md` — if both are present, `project.name` takes precedence for cover and title display.

**`project.org`** — Publisher or author name. Appears on the title page and in the colophon.

**`project.tagline`** — Subtitle or tagline. Appears beneath the title on the full title page.

**`brand.preset`** — The visual theme. See section 5 for fiction-appropriate choices and a full breakdown of the gothic preset.

**`brand.copyright`** — The copyright notice used on the copyright page and in the colophon.

**`template.preset`** — Must be `"novel"` for the novel template. Using `"book"` will lose continuous flow pagination and narrative formatting.

**`content.max_words_per_section`** — BriefKit's default is 3000 words per section. A single chapter of a novel can easily exceed this, causing content truncation mid-chapter. Set this to 10000 or higher for novel projects. There is no practical upper limit.

**`hierarchy.root_level`** — Tells BriefKit to treat the docs directory as a Level 3 (doc set) rather than attempting to resolve it as a higher-level aggregate. Without this, BriefKit will attempt to recurse into subdirectories and extract 0 subsystems from the flat novel directory.

**`hierarchy.depth_to_level`** — Maps directory depth (0 = root of the path you pass to `generate`) to BriefKit level. Setting `0: 3` ensures BriefKit treats the directory you pass directly as a doc set.

### Config file location and the --config flag

BriefKit searches for `briefkit.yml` by walking up from the current working directory. If you run `briefkit generate` from inside the project root, it will find the config automatically. If you run from a different directory, pass the config explicitly:

```bash
briefkit generate docs/novel-name/ --config /path/to/project/briefkit.yml
```

The config must not be inside the docs directory. If `briefkit.yml` is at `docs/novel-name/briefkit.yml`, BriefKit will ignore hierarchy settings and may extract 0 subsystems.

---

## 5. Choosing a Preset

BriefKit ships with 15 color presets. The following presets work well for fiction:

| Preset | Character | Best for |
|--------|-----------|---------|
| `gothic` | Near-black ink on warm off-white; muted brown accents; serif body font | Horror, literary fiction, atmospheric prose |
| `ink` | Dark charcoal on white; orange accent; serif body font | Literary fiction, narrative non-fiction, memoir |
| `charcoal` | Dark neutral grey on white; sans-serif | Dark literary fiction, thriller |
| `mono` | Pure black on white; monospace throughout | Print-first output, ARCs, manuscript drafts |
| `royal` | Deep purple with gold accent; serif | Fantasy, epic fiction, academic-adjacent literary works |

### The gothic preset — design philosophy

The `gothic` preset was designed for horror novels and atmospheric literary prose. Its full color palette:

```
primary:    "#1A1A1A"
secondary:  "#4A4A4A"
accent:     "#8B7355"
body_text:  "#1C1C1C"
caption:    "#555555"
background: "#FAFAF5"
rule:       "#C0B8A8"
code_bg:    "#F0EDE6"
font_body:    "Times-Roman"
font_heading: "Times-Bold"
font_caption: "Times-Italic"
```

**Typography.** Both body and heading fonts are Times-Roman variants, the traditional serif typeface of printed books. Times-Roman at 10-11pt with generous leading reads cleanly and carries the historical weight appropriate to literary fiction.

**Color.** Body text is `#1C1C1C` rather than pure black. The difference is subtle on screen but visible in print: near-black is warmer and less clinical than `#000000`. The page background `#FAFAF5` is a warm off-white that reduces the harshness of pure white and gives the page the quality of aged stock.

**Accent.** The accent color `#8B7355` is a muted warm brown — the color of old bindings, dried ink, and aged paper. It appears in section rules, callout borders, and decoration. It recedes rather than competing with the prose.

**Code background.** The `code_bg` value `#F0EDE6` gives monospace elements a warm parchment tone rather than the stark grey of technical document presets. This matters for the novel template's narrative formatting categories (see section 6), which use monospace for system tags, logs, and corrupted text.

**Intent.** The overall effect is a page that looks typeset by a human rather than generated by software, which is appropriate for fiction where the design must serve the prose and not compete with it.

To use gothic for any novel project:

```yaml
brand:
  preset: "gothic"
```

To override individual values while keeping the rest of the palette:

```yaml
brand:
  preset: "gothic"
  body_text: "#000000"    # Pure black instead of near-black
  background: "#FFFFFF"   # Pure white instead of warm off-white
```

---

## 6. Narrative Formatting — The Novel Template's Core Feature

The novel template automatically detects and styles seven categories of meta-narrative text common in literary fiction, horror, and experimental prose. Detection is based on the content and formatting of each paragraph — you write plain markdown and the template applies the appropriate styling.

### The seven categories

| Category | Detection rule | Style applied |
|----------|---------------|---------------|
| ERASURE | Italic text that is all-caps, OR italic text containing erasure phrases ("was never here", "never met", "does not exist", etc.) | Courier-Bold 12pt, centered, 6mm spacing above and below — visually devastating |
| SYSTEM_COMMAND | All-caps text (e.g. RETURN TO STREAM, RUN, ERASE), or mostly-caps text with apostrophes (e.g. IF YOU'RE READING THIS) | Courier-Bold 11pt, centered, 3mm spacing |
| SYSTEM_TAG | Paragraph that starts with `[` and contains `]` (e.g. `[NO SOUND]`, `[LOADING ERROR]`) | Courier 9pt on tinted background |
| SYSTEM_LOG | Blockquote paragraphs (lines starting with `>`) | Courier 9pt on tinted background, indented — renders as monospace log, not a "KEY INSIGHT" callout box |
| CORRUPTED | Contains the `░` block character | Courier-Oblique 9pt |
| ITALIC_VOICE | Entire paragraph wrapped in `*italic*` (entity whispers, notebook entries, interior voice) | Times-Italic 9.5pt, indented 18pt on both sides |
| Normal prose | Everything else | Passes through unchanged in the body font |

### How to use these categories in your manuscript

You do not configure or annotate these categories. Write your manuscript naturally:

- For a system command, write it in all caps: `RETURN TO STREAM`
- For a system tag, write it in brackets: `[NO SOUND]`
- For corrupted text, include the `░` character in the line
- For blockquote logs, use standard markdown blockquote syntax: `> LOG ENTRY 4412`
- For an entity voice or notebook entry, wrap the entire paragraph in `*asterisks*`
- For an erasure (redacted text that implies a presence), write in all-caps italic: `*SHE WAS NEVER HERE*`

The template detects the category and styles accordingly. All other paragraphs are treated as normal prose.

### Why SYSTEM_LOG matters

The `book` template renders blockquotes as "KEY INSIGHT" callout boxes — a design element appropriate for technical documentation and executive briefings, not for in-world log entries, found footage, or system readouts. The `novel` template overrides this behavior. Blockquotes render as indented monospace text on a tinted background, functioning as a visual log panel rather than a highlight box.

---

## 7. Generating the PDF

Once your directory is structured and your config is in place, generate the PDF with:

```bash
briefkit generate docs/novel-name/ --config briefkit.yml --force --no-ids --template novel
```

### Flag explanation

**`docs/novel-name/`** — The path to the directory containing the numbered chapter files and `README.md`. This is the directory that holds the `.md` files, not the project root.

**`--config briefkit.yml`** — Explicitly points to the config file at the project root. Passing it explicitly is safer than relying on automatic discovery and avoids ambiguity when running from different working directories.

**`--force`** — Regenerate the PDF even if BriefKit determines the output is already current. During writing and editing, sources change frequently; `--force` ensures every run produces a fresh PDF.

**`--no-ids`** — Skip document ID assignment. BriefKit's document ID system is designed for technical documentation sets and is not useful for novels. Skipping it keeps chapter files clean.

**`--template novel`** — Explicitly select the novel template. This supplements the `template.preset: "novel"` in `briefkit.yml`. If `briefkit.yml` already specifies the novel preset, the flag is redundant but harmless. Passing it explicitly prevents accidental use of the wrong template if the config is missing or misconfigured.

### Output location

BriefKit writes the PDF to `executive-briefing.pdf` inside the docs directory you passed:

```
docs/novel-name/executive-briefing.pdf
```

Rename it after generation:

```bash
mv docs/novel-name/executive-briefing.pdf "My Novel Title.pdf"
```

### Verbose mode

If the output is not what you expected, run with `--verbose` to see what BriefKit extracted:

```bash
briefkit generate docs/novel-name/ --config briefkit.yml --force --no-ids --template novel --verbose
```

Verbose output shows the number of subsystems (chapters) detected, the word count per chapter, and the config values in effect. If you see 0 subsystems, the chapter files were not detected — check the numbered file naming pattern and the hierarchy settings.

---

## 8. Common Issues and Fixes

### a) 0 subsystems extracted — no chapters in the PDF

**Symptom:** BriefKit generates a PDF with a title page and TOC but no chapter content. The verbose output reports "0 subsystems extracted."

**Cause:** BriefKit is not finding the numbered chapter files. This is almost always caused by one of two things:

1. The `briefkit.yml` is missing the `hierarchy` settings, or the hierarchy settings are wrong for a flat novel directory.
2. The `briefkit.yml` is inside the docs directory rather than at the project root.

**Fix:** Ensure `briefkit.yml` is at the project root (the directory that contains `docs/`), not inside `docs/novel-name/`. Ensure the config contains:

```yaml
hierarchy:
  root_level: 3
  depth_to_level:
    0: 3
```

### b) Content truncated — chapters cut off mid-scene

**Symptom:** Chapters appear in the PDF but end abruptly before the actual content ends.

**Cause:** BriefKit's default `max_words_per_section` is 3000 words. A single chapter file for a novel frequently exceeds this.

**Fix:** Set the limit higher in `briefkit.yml`:

```yaml
content:
  max_words_per_section: 10000
```

For very long chapters, increase this further. There is no practical upper limit.

### c) `&nbsp;` or other HTML entities rendering as literal text

**Symptom:** The PDF contains the string `&nbsp;` or `&amp;` or `&mdash;` in the body text.

**Cause:** BriefKit uses ReportLab for PDF generation, not an HTML renderer. HTML character entities are treated as plain text and are not decoded.

**Fix:** Strip HTML entities from your source markdown before generating:

```bash
sed -i 's/&nbsp;/ /g; s/&amp;/\&/g; s/&mdash;/—/g; s/&ndash;/–/g; s/&ldquo;/"/g; s/&rdquo;/"/g' docs/novel-name/*.md
```

### d) Doubled chapter numbers in the PDF

**Symptom:** The PDF renders chapter headings as "Chapter 1 Chapter 1: The First Step" — the number appears twice.

**Cause:** An older version of the book template added its own "Chapter N" prefix before the H1 content. This was a template bug.

**Fix:** Update BriefKit to the current version. The novel template uses the H1 heading from your content directly as the chapter title, with no prefix added.

```bash
pip install --upgrade briefkit
```

### e) Footer copyright text truncated

**Symptom:** The copyright notice in the page footer is cut off mid-sentence.

**Cause:** An earlier version of the book template allocated insufficient width to the footer text field.

**Fix:** Update BriefKit. The current footer uses 85% of page width and places the page number and copyright notice on separate lines to prevent collision.

### f) Orphaned chapter headings

**Symptom:** A chapter title (`## H2`) appears alone at the bottom of a page with no body text following it.

**Cause:** ReportLab placed the heading at the bottom of one page and the paragraph content at the top of the next, splitting the heading from its content.

**Fix:** Update BriefKit. The novel template applies `keepWithNext` to H2 headings, which instructs ReportLab to keep the heading on the same page as the content that follows it.

### g) Auto-generated glossary contains chapter names

**Symptom:** The glossary page in the PDF lists "Chapter 1: The First Step", "Chapter 2: The Sound", etc. rather than actual glossary terms.

**Cause:** If no `glossary.md` file is present, BriefKit's automatic term extractor treats H2 headings throughout the body content as glossary terms. For fiction, H2 headings are chapter names, not terms to define.

**Fix:** Create `glossary.md` in the docs directory with genuine definitions. When BriefKit finds `glossary.md`, it uses it instead of the auto-extractor. See section 3.1, step 9.

### h) Duplicate content from the manuscript split

**Symptom:** The PDF includes an "END" marker, a raw copyright block, or author notes that were in the original manuscript but should not appear in the typeset PDF.

**Cause:** The manuscript was split without stripping back matter. BriefKit renders everything it finds in the numbered chapter files.

**Fix:** Edit the chapter files to remove any end-of-manuscript markers, raw copyright text, or notes. Alternatively, use the v2 split script in section 3.3, which strips END markers and back matter automatically. BriefKit generates its own copyright page and colophon — the manuscript's originals must not appear in the body chapters.

### i) Generic preface rather than the novel's actual preface

**Symptom:** The preface page contains generic text derived from the README rather than the preface you wrote.

**Cause:** BriefKit generates a preface from the README overview if no `preface.md` file is present in the docs directory.

**Fix:** Create `preface.md` in the docs directory. See section 3.1, step 8.

### j) Half-empty pages between Parts

**Symptom:** Each Part in the PDF ends on a half-empty page, leaving a large block of whitespace before the next Part begins.

**Cause:** You are using the `book` template. The `book` template forces a `PageBreak` after every chapter file regardless of how much space remains on the current page.

**Fix:** Use the `novel` template instead. Set `template.preset: "novel"` in `briefkit.yml` and pass `--template novel` on the command line. The novel template uses `CondPageBreak(80mm)`, which only inserts a page break if fewer than 80mm remain on the current page. Parts flow continuously and the Part heading provides the visual separation.

### k) Meta-narrative elements render as plain text

**Symptom:** System commands, erasure text, in-world tags, and other meta-narrative elements appear in the same body font as normal prose, with no visual distinction.

**Cause:** You are using the `book` template. The `book` template has no narrative formatting categories and passes all paragraph text through unchanged.

**Fix:** Use the `novel` template. Set `template.preset: "novel"` in `briefkit.yml` and pass `--template novel` on the command line. The novel template auto-detects and styles all seven narrative formatting categories described in section 6.

### l) Blockquotes render as "KEY INSIGHT" callout boxes

**Symptom:** In-world log entries, found footage transcripts, and system readouts written as blockquotes (`>`) render as highlighted callout boxes with a "KEY INSIGHT" label, styled as executive document pull-quotes.

**Cause:** You are using the `book` template. The `book` template renders all blockquotes as callout boxes, which is appropriate for technical documents but not for fiction.

**Fix:** Use the `novel` template. The novel template renders blockquotes as indented monospace text on a tinted background — visually a log panel, not a highlight box.

### m) Colophon says "Typeset by briefkit"

**Symptom:** The colophon page ends with "Typeset by briefkit" rather than a proper publisher colophon.

**Cause:** You are using the `book` template. The `book` template generates a generic colophon with a "Typeset by BriefKit" line.

**Fix:** Use the `novel` template. The novel template generates a proper closing colophon containing the title, organization, a decorative rule, the copyright notice, a fiction disclaimer, and the first edition date. There is no "Typeset by briefkit" line.

---

## 9. Full Example: The Backrooms

The `examples/novel-template/` directory in this repository demonstrates the complete setup described in this tutorial, using a Backrooms horror novel as the sample project.

The `novel` template was developed during the production of this novel. The Backrooms manuscript — a multi-Part horror novel with system commands, erasure text, in-world tags, corrupted passages, and entity voice narration — exposed all of the formatting limitations of the `book` template described in issues j through m above. The `novel` template was built specifically to address them.

### Example directory structure

```
examples/novel-template/
  briefkit.yml
  docs/
    backrooms-novel/
      README.md
      preface.md
      glossary.md
      01-level-0-the-lobby.md
      02-level-1-pipe-dreams.md
      03-the-descent.md
      executive-briefing.pdf
```

The `briefkit.yml` at `examples/novel-template/briefkit.yml` uses the `novel` template and `gothic` preset:

```yaml
project:
  name: "The Backrooms"
  org: "Offtrack Media"
  tagline: "There are places the map does not show."

brand:
  preset: "gothic"
  org: "Offtrack Media"
  copyright: "(c) 2024 Offtrack Media"

template:
  preset: "novel"

content:
  max_words_per_section: 10000

hierarchy:
  root_level: 3
  depth_to_level:
    0: 3
```

### Generating the example PDF

From the repository root:

```bash
cd examples/novel-template
briefkit generate docs/backrooms-novel/ --config briefkit.yml --force --no-ids --template novel
```

The PDF is written to `examples/novel-template/docs/backrooms-novel/executive-briefing.pdf`.

### Applying this setup to your own novel

1. Copy `examples/novel-template/briefkit.yml` to your project root.
2. Update `project.name`, `project.org`, `project.tagline`, and `brand.copyright`.
3. Create your docs directory and split your manuscript into numbered files following the heading conventions in section 3.
4. Add `preface.md` and `glossary.md` to the docs directory.
5. Run the generate command pointing at your docs directory.

---

## 10. Reference: Pages the Novel Template Generates

| Page | Content | Source |
|------|---------|--------|
| Half-title page | Novel title, centered, nothing else | `project.name` in `briefkit.yml` |
| Full title page | Title, tagline, organization, year | `project.name`, `project.tagline`, `project.org` |
| Copyright page | Copyright notice, rights reserved statement | `brand.copyright` |
| Table of contents | Auto-generated from chapter H1 headings | Numbered `.md` files |
| Preface | Full preface text | `preface.md` if present, otherwise README overview |
| Chapters | Continuous flow, narrative-aware formatting | `01-*.md`, `02-*.md`, etc. |
| Glossary | Term definitions | `glossary.md` if present, otherwise auto-extracted H2 headings |
| Colophon | Title, org, decorative rule, copyright, fiction disclaimer, edition | Auto-generated from `brand` and `project` config |

The novel template does not produce a cover or back cover. These are features of briefing-template document types, not the novel template. The novel template produces front matter, body, and back matter in the tradition of printed fiction.

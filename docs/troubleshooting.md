# Troubleshooting

Common messages and what to do about them.

---

## "No content was extracted"

**Symptom:**

```
Error: No content was extracted from /path/to/docs.
  briefkit looked for:
    - 00-what-is-*.md  (orientation doc)
    - [0-9][0-9]-*.md      (numbered chapters, configurable via content.numbered_doc_pattern)
    - README.md        (overview / title fallback)
  Present .md files: (no .md files)
```

The command exits 2.

**Cause:** The directory you passed holds no numbered Markdown files, and none of its children or grandchildren do either.

**Fix:**

1. Pass the directory that contains the numbered files directly, or a parent whose children are such directories (that builds a subject overview instead):

   ```bash
   # a documentation set
   briefkit generate docs/my-topic/

   # every documentation set under docs/, one PDF each
   briefkit batch docs/
   ```

2. Check that your files match the `[0-9][0-9]-*.md` pattern:

   ```bash
   ls docs/my-topic/[0-9][0-9]-*.md
   ```

   If nothing shows up, rename them:

   ```
   1-intro.md           # single digit: not detected
   introduction.md      # no number prefix: not detected
   chapter-01.md        # number not at the start: not detected

   01-introduction.md   # detected
   02-details.md        # detected
   ```

   or change the pattern in `briefkit.yml` (`content.numbered_doc_pattern: "*.md"`).

3. Run with `--dry-run` to see what the extractor finds without building anything, and `--verbose` to see the extraction while it builds:

   ```bash
   briefkit generate docs/my-topic/ --dry-run
   briefkit generate docs/my-topic/ --verbose
   ```

---

## The PDF Is Not Where You Expected

1. **Default:** inside the source directory:

   ```
   docs/my-topic/executive-briefing.pdf
   ```

2. **With `--output`:** the file you named, or `executive-briefing.pdf` inside the directory you named:

   ```bash
   briefkit generate docs/my-topic/ --output ./output/report.pdf
   briefkit generate docs/my-topic/ --output ./output/
   ```

3. **With `output.output_dir`:** the source tree is mirrored beneath that directory, relative to the project root:

   ```yaml
   output:
     output_dir: "build"
   ```

   puts `docs/my-topic` at `build/docs/my-topic/executive-briefing.pdf`.

4. **Check the command's output.** BriefKit prints the path it wrote:

   ```
   Generating briefing for: /home/user/project/docs/my-topic
   Output: /home/user/project/docs/my-topic/executive-briefing.pdf
   Done in 0.4s
   ```

---

## "Unknown template"

**Symptom:**

```
Error: ValueError: Unknown template: 'summary'.  Available templates: academic, book, briefing, certificate, contract, datasheet, deck, deep-research, evaluation, guide, invoice, letter, magazine, manual, memo, minimal, minutes, newsletter, novel, playbook, policy, proposal, quote, register, report, resume, sop, whitepaper, witness
```

**Fix:** Use one of the names in the message; `briefkit templates` prints them with a description each. Names are lower-case and hyphenated (`deep-research`, not `deep_research`).

---

## "Unknown color preset"

**Symptom:**

```
Error: Unknown color preset: 'blue'. Available presets: arctic, charcoal, corporate, crimson, cyber, deep-research, emerald, forest, gothic, ink, midnight, mono, navy, neon, neon-print, ocean, royal, slate, sunset, terracotta
```

**Fix:** Use one of those names, or `custom` with your own `brand.*` colors. `briefkit presets --quiet` lists them.

---

## "Config file not found"

**Symptom:**

```
Error: Config file not found: /path/to/briefkit.yml
Run with --verbose for a full traceback.
```

**Fix:**

1. If you passed `--config`, check the path.
2. Without `--config`, BriefKit walks upward from the directory you run the command in looking for `briefkit.yml`, `briefkit.yaml` or a `.briefkit/` directory. Run the command from inside your project, or pass `--config` explicitly. With no file at all, the defaults apply and this message never appears.

---

## "Warning: unknown setting"

**Symptom:**

```
Warning: unknown setting 'tempalte' in briefkit.yml (did you mean 'template'?)
Warning: unknown setting layout.pagesize in briefkit.yml (did you mean 'page_size'?)
```

**Cause:** A key in `briefkit.yml` is not one BriefKit reads. The file still loads; the misspelled setting has no effect.

**Fix:** Rename the key as suggested. Every key is listed in [configuration.md](configuration.md). Keys that older versions documented but never read (`layout.font_family`, `layout.font_size`, `template.sections`, `template.custom_sections`, `output.report_format`, `constraints`) warn too; fonts are `brand.font_*` and sections are suppressed with `project.skip_*`.

---

## "Configuration errors"

**Symptom:**

```
Error: Configuration errors:
  - brand.primary must be a 6-digit hex color (e.g. #1B2A4A), got: 'blue'
  - layout.page_size must be one of ['A3', 'A4', 'Legal', 'Letter', 'Tabloid'], got: 'B5'
  - project.skip_prefece: unknown section 'prefece'. Did you mean 'skip_preface'?
```

**Fix:** Correct the values. Common mistakes:

| Field | Valid Values |
|-------|-------------|
| `brand.primary` (and the other eleven colors) | 6-digit hex, quoted: `"#1B2A4A"` (an unquoted `#` starts a YAML comment) |
| `layout.page_size` | `A4`, `A3`, `Letter`, `Legal`, `Tabloid` |
| `layout.orientation` | `portrait`, `landscape` |
| `doc_ids.sequence_digits` | integer 1 to 8 |
| `doc_ids.year_format` | `short`, `full` |
| `project.skip_*` | one of the 30 section names in [universal-controls.md](universal-controls.md) |
| `output.filename` | a bare `.pdf` file name, no directory part |
| `brand.logo` | an existing PNG, JPEG or GIF; SVG is not accepted |

`briefkit config` prints the resolved configuration (`--json` for machine reading).

---

## Quality Check Failed

**Symptom:**

```
Running quality gates on: /path/to/docs/my-topic/executive-briefing.pdf
  PASS: Valid PDF header
  WARN: File size 3,912 bytes (target: 20,000+)
  WARN: Page count 1 (target: 2+)
  PASS: Text present on the first page
  PASS: PDF metadata present
quality: PASS
```

**Cause:** The structural checks (header, parse, pages, text) decide pass or fail; size and page counts against the level's thresholds only warn, unless `--strict` turns them into failures. A small result usually means little source content.

**Fix:**

1. Add content, or more numbered files, to the directory.
2. If the document is intentionally short, lower the thresholds in `briefkit.yml`:

   ```yaml
   quality:
     min_pages: 1
     hard_min_bytes: 2000
     soft_min_bytes: 2000
   ```

3. If the parse or text check fails, open the PDF in a viewer; the build is otherwise atomic, so a corrupt file means a bug worth reporting.

The parse, page and text checks need pypdf (`pip install "briefkit[quality]"`); without it only the header and size are checked.

---

## "Skipping oversized file" or a Missing Chapter

**Cause:** The extractor skips files larger than 10 MB and does not follow symlinks.

**Fix:** Split the file, or replace the symlink with the file.

---

## Truncated Section Content

**Symptom:** A chapter in the PDF seems to cut off part way, and the command printed a line naming the file, the words kept against the words available, and `content.max_words_per_section`.

**Cause:** Each source file is cut at `content.max_words_per_section` (default 12000 words; tables and blockquotes are preserved through the cut) and document templates cap the rendered body at `content.max_blocks_per_section` flowables per file (default 0, unlimited).

**Fix:** Raise or remove the limit in `briefkit.yml`; `0` means unlimited:

```yaml
content:
  max_words_per_section: 0
  max_blocks_per_section: 0
```

Or split the file into several numbered files.

> **Carrying an older `briefkit.yml`?** `max_words_per_section` used to default to 3000 and the cut was silent. A file that still pins 3000 keeps the old limit, though it now warns. Remove the line or set it to 0.

---

## No Bibliography or Missing Citations

**Cause:** BriefKit recognizes these forms:

- APA: `(Author, 2020)`
- Author-year: `Author (2020)`
- Bracketed: `[1]`, `[Source: ...]`
- Legislation: `Something Act 1988`
- RFC: `RFC 1234`
- Case law: `Plaintiff v Defendant`
- PDF file names in the source directory: `author-year-title.pdf` (the files are not opened)

**Fix:**

1. Write citations in one of those forms.
2. Place reference PDFs in the source directory; their file names become entries.
3. Run with `--verbose` to see what the extractor found.

---

## Variant Not Detected, or the Wrong One

**Cause:** A variant is chosen in this order: `--variant`, the first matching `variants.rules` entry, then auto-detection, which needs at least two of the variant's keywords present as whole words.

**Fix:**

1. Name it:

   ```bash
   briefkit generate docs/ml-research/ --variant aiml
   ```

2. Or select it by path in `briefkit.yml`:

   ```yaml
   variants:
     rules:
       - pattern: "docs/ml-research/**"
         variant: "aiml"
   ```

3. To suppress an unwanted variant: `--variant none`, or `variants.auto_detect: false` in the configuration.

Variants are added only by the `briefing`, `report`, `manual` and `academic` templates. Available: `aiml`, `legal`, `medical`, `engineering`, `research`, `api`, `gaming`, `finance`, `species`, `historical`, `hardware`, `religion`.

---

## Debugging Checklist

1. **Verify the installation:**

   ```bash
   briefkit --version
   briefkit selftest
   ```

2. **Check the directory:**

   ```bash
   ls docs/my-topic/[0-9][0-9]-*.md
   briefkit generate docs/my-topic/ --dry-run
   ```

3. **Inspect the resolved configuration:**

   ```bash
   briefkit config --json
   ```

4. **Check what `batch` would do:**

   ```bash
   briefkit status docs/
   briefkit batch docs/ --dry-run
   ```

5. **Build with details:**

   ```bash
   briefkit generate docs/my-topic/ --verbose
   ```

6. **Check the result:**

   ```bash
   briefkit quality docs/my-topic/
   ```

---

## Getting Help

```bash
briefkit --help
briefkit generate --help
briefkit batch --help
briefkit --version
```

Bugs: https://github.com/otmof-ops/briefkit/issues (not for security reports; see [SECURITY.md](../SECURITY.md)).

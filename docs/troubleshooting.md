# Troubleshooting

Common issues and how to fix them.

---

## "0 words extracted" / Nearly Empty PDF

**Symptom:** The PDF generates but has almost no content. The metrics dashboard shows 0 words, 0 subsystems.

**Cause:** The extractor did not find any numbered markdown files in the directory you passed.

**Fix:**

1. Check that you are passing the correct directory -- it must contain the `.md` files directly:

   ```bash
   # WRONG: passing a parent directory
   briefkit generate docs/

   # RIGHT: passing the directory with the numbered files
   briefkit generate docs/my-topic/
   ```

2. Check that your files match the `[0-9][0-9]-*.md` pattern:

   ```bash
   ls docs/my-topic/[0-9][0-9]-*.md
   ```

   If nothing shows up, rename your files:

   ```bash
   # Wrong names
   1-intro.md           # single digit
   introduction.md      # no number prefix
   chapter-01.md        # number not at start

   # Correct names
   01-introduction.md
   02-details.md
   ```

3. Run with `--verbose` to see exactly what the extractor finds:

   ```bash
   briefkit generate docs/my-topic/ --verbose
   ```

---

## "0 subsystems" in the Output

**Symptom:** The PDF has a cover page and TOC but the body section says "0 subsystems" or has no chapter content.

**Cause:** Same as above -- no numbered files detected.

**Fix:** See the "0 words extracted" section above.

---

## Wrong Output Location

**Symptom:** You cannot find the generated PDF.

**Where to look:**

1. **Default:** The PDF is written inside the source directory:

   ```
   docs/my-topic/executive-briefing.pdf
   ```

2. **With `--output`:** Wherever you specified:

   ```bash
   briefkit generate docs/my-topic/ --output ./output/report.pdf
   # PDF at: ./output/report.pdf
   ```

3. **With `output.output_dir` in config:**

   ```yaml
   output:
     output_dir: "./build"
   ```

   PDF goes to `./build/executive-briefing.pdf`.

4. **Check the CLI output.** BriefKit prints the output path:

   ```
   Generating briefing for: /home/user/docs/my-topic
   Output: /home/user/docs/my-topic/executive-briefing.pdf
   ```

---

## "Unknown template" Error

**Symptom:**

```
Error: Unknown template: 'summary'. Available templates: academic, book, briefing, contract, letter, manual, minimal, minutes, register, report
```

**Fix:** Use one of the exact template names listed in the error. The valid names are:

```
academic, book, briefing, contract, letter, manual, minimal, minutes, register, report
```

---

## "Unknown color preset" Error

**Symptom:**

```
ValueError: Unknown color preset: 'blue'. Available presets: arctic, charcoal, corporate, ...
```

**Fix:** Use one of the valid preset names. List them with:

```bash
briefkit presets --quiet
```

---

## "Config file not found" Error

**Symptom:**

```
Error: Config file not found: /path/to/briefkit.yml
```

**Fix:**

1. If using `--config`, verify the path exists.
2. If not using `--config`, BriefKit walks up from CWD looking for `briefkit.yml`, `briefkit.yaml`, or `.briefkit/`. Make sure you run the command from within your project, or pass `--config` explicitly.

---

## Configuration Validation Errors

**Symptom:**

```
ValueError: Configuration errors:
  - brand.primary must be a 6-digit hex color (e.g. #1B2A4A), got: 'blue'
  - layout.page_size must be one of ['A3', 'A4', 'Legal', 'Letter', 'Tabloid'], got: 'B5'
```

**Fix:** Correct the invalid values in your `briefkit.yml`. Common mistakes:

| Field | Valid Values |
|-------|-------------|
| `brand.primary` (and other colors) | 6-digit hex like `#1B2A4A` |
| `layout.page_size` | `A4`, `A3`, `Letter`, `Legal`, `Tabloid` |
| `layout.orientation` | `portrait`, `landscape` |
| `doc_ids.sequence_digits` | Integer 1-8 |
| `doc_ids.year_format` | `short`, `full` |

Run `briefkit config --json` to see the fully resolved config and spot issues.

---

## PDF is Too Small / Quality Gate Failure

**Symptom:**

```
FAIL: Hard minimum size not met (12,345 < 20,000 bytes)
```

**Cause:** The generated PDF is smaller than the quality threshold, usually because there is not enough source content.

**Fix:**

1. Add more content to your markdown files.
2. Add more numbered files to the directory.
3. If the content is intentionally small, the quality gate is informational -- the PDF was still generated.

Check quality manually:

```bash
briefkit quality docs/my-topic/
```

---

## "Warning: Skipping oversized file"

**Symptom:**

```
Warning: Skipping oversized file (15000000 bytes): docs/my-topic/01-huge.md
```

**Cause:** The extractor skips files larger than 10 MB as a safety measure.

**Fix:** Split large files into smaller ones:

```
01-part-one.md    (under 10 MB)
02-part-two.md    (under 10 MB)
```

---

## Truncated Section Content

**Symptom:** A chapter in the PDF seems to cut off mid-way.

**Cause:** The extractor truncates individual files to `max_words_per_section` (default: 3000 words). Tables and blockquotes are preserved through truncation.

**Fix:** Increase the limit in `briefkit.yml`:

```yaml
content:
  max_words_per_section: 5000
```

Or split large files into multiple numbered files.

---

## No Bibliography / Missing Citations

**Symptom:** The bibliography section is empty even though you have citations in your markdown.

**Cause:** BriefKit detects citations in these formats:
- APA style: `(Author, Year)`
- Author-year: `Author (Year)`
- Bracketed: `[1]`, `[Source: ...]`
- Legislation: `Something Act 1988`
- RFC: `RFC 1234`
- Case law: `Plaintiff v Defendant`
- PDF filenames: `author-year-title.pdf` in the source directory

**Fix:**

1. Check that your citations use one of the supported formats.
2. Place reference PDFs in the source directory (filenames are parsed as bibliography entries).
3. Use `--verbose` to see what the extractor detected.

---

## Variant Not Detected

**Symptom:** You expected domain-specific sections (e.g., AI/ML hyperparameter table) but they did not appear.

**Cause:** Auto-detection requires at least 2 matching keywords in the content.

**Fix:**

1. Force the variant with the CLI flag:

   ```bash
   briefkit generate docs/ml-research/ --variant aiml
   ```

2. Or configure variant rules in `briefkit.yml`:

   ```yaml
   variants:
     rules:
       - pattern: "papers/ml/**"
         variant: "aiml"
   ```

Available variants: `aiml`, `legal`, `medical`, `engineering`, `research`, `api`, `gaming`, `finance`, `species`, `historical`, `hardware`, `religion`.

---

## Debugging Checklist

When something is not working as expected, run through these steps:

1. **Verify installation:**

   ```bash
   briefkit selftest
   ```

2. **Check your directory structure:**

   ```bash
   ls docs/my-topic/[0-9][0-9]-*.md
   ```

3. **Run verbose generation:**

   ```bash
   briefkit generate docs/my-topic/ --verbose
   ```

4. **Inspect resolved config:**

   ```bash
   briefkit config --json
   ```

5. **Check target discovery (for batch):**

   ```bash
   briefkit status docs/
   ```

6. **Check the output location:**

   ```bash
   briefkit generate docs/my-topic/ --dry-run
   ```

7. **Check quality gates:**

   ```bash
   briefkit quality docs/my-topic/
   ```

---

## Getting Help

```bash
# General help
briefkit --help

# Command-specific help
briefkit generate --help
briefkit batch --help

# Version
briefkit --version
```

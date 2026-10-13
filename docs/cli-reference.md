# CLI Reference

Every BriefKit command, flag, exit code and message.

Flags go **after** the subcommand (`briefkit generate docs/ --quiet`); only `--version` belongs to the top-level command.

---

## Commands

| Command | Purpose |
|---------|---------|
| `briefkit generate <path>` | Generate a PDF from one directory |
| `briefkit batch <root>` | Generate PDFs for every eligible directory under a root |
| `briefkit init [path]` | Write `briefkit.yml` with defaults (and a `.briefkit/` directory) |
| `briefkit preview <path>` | Generate and open the PDF in the system viewer |
| `briefkit status [path]` | Report which briefings are current, stale or missing |
| `briefkit assign-ids <path>` | Register document IDs for directories whose PDF already exists |
| `briefkit quality <path>` | Check an existing PDF |
| `briefkit selftest` | Build and verify a fixture in a temporary directory |
| `briefkit config` | Print the resolved configuration |
| `briefkit templates` | List templates with a one-line description each |
| `briefkit presets` | List color presets with hex values |
| `briefkit licenses` | List license presets for generated documents |

---

## `briefkit generate`

```bash
briefkit generate <path> [flags]
```

Generates one PDF from the directory `<path>`. The directory is read for numbered Markdown files, a `README.md`, an orientation document and companion files (see [directory-structure.md](directory-structure.md)); a directory holding numbered files is a documentation set whatever its depth.

```bash
briefkit generate docs/my-topic/                                   # PDF next to the sources
briefkit generate docs/my-topic/ --template report --preset charcoal
briefkit generate docs/my-topic/ --output build/my-briefing.pdf    # a file
briefkit generate docs/my-topic/ --output build/                   # a directory: output.filename inside it
briefkit generate docs/my-topic/ --title "Q4 Security Assessment" --org "ACME Corp"
briefkit generate docs/my-topic/ --logo logo.png                   # PNG, JPEG or GIF on the cover
briefkit generate docs/ml-research/ --variant aiml                 # force a variant; `none` suppresses them
briefkit generate docs/my-topic/ --no-ids                          # no document ID
briefkit generate docs/my-topic/ --dry-run                         # extraction report, no PDF
briefkit generate docs/my-topic/ --json                            # result as JSON on stdout
briefkit generate docs/my-topic/ --verbose                         # extraction and build details on stderr
briefkit generate docs/my-topic/ --config path/to/briefkit.yml
```

**Where the PDF goes.** `--output` wins; otherwise `output.output_dir` from the configuration mirrors the source tree beneath that directory (`build/docs/my-topic/executive-briefing.pdf`); otherwise `<path>/<output.filename>`. The PDF is written to a temporary file beside the target and moved into place when the build succeeds, so a failed build never destroys the previous PDF.

**Before the build.** The directory is extracted once and checked: if nothing can be extracted (no numbered files, no README) the command prints what it looked for, what it found, and three fixes, and exits 2. Documents cut by `content.max_words_per_section` are named on stderr with the words kept and the setting responsible. A missing `license.preset` prints a warning on stderr (the back cover then says "All rights reserved").

---

## `briefkit batch`

```bash
briefkit batch <root> [flags]
```

Walks `<root>` and generates every **eligible** directory: one that directly contains a file matching `content.numbered_doc_pattern` (default `[0-9][0-9]-*.md`). A directory holding only a `README.md` is not eligible. `.briefkit`, `.git`, `__pycache__`, `node_modules`, `.venv`, `venv` and every dot-directory are skipped.

```bash
briefkit batch docs/
briefkit batch docs/ --force                 # rebuild everything
briefkit batch docs/ --dry-run               # list what would be generated
briefkit batch docs/ --json                  # {total, generated, skipped, failed, dry_run, results, elapsed}
briefkit batch docs/ --template report --preset charcoal
briefkit batch docs/ --no-ids --variant none
briefkit batch docs/ --output build/         # mirror the tree beneath build/
```

Sample output:

```
  [1/5] GENERATE education/cognitive-load-theory
             -> /path/to/education/cognitive-load-theory/executive-briefing.pdf  (1.2s)
  [2/5] SKIP     education/assessment-methods  (current)
  ...

  Batch complete in 4.1s
  5 target(s) found — 3 generated, 2 skipped, 0 failed
```

**Skip-if-current.** A directory is skipped when its PDF is newer than every numbered file, the orientation document, `README.md`, `engineering-brilliance.md`, `guide.md`, `preface.md`, `glossary.md`, `methodology.md`, `.source-type`, and the project's `briefkit.yml`. Changing the template or preset by flag does not make output stale; use `--force` for that. `--title` is ignored by `batch` (it names a single document) and says so.

Exit code is 1 when any directory failed; the failures are listed with the exception type.

---

## `briefkit init`

```bash
briefkit init [path] [flags]
```

Writes `briefkit.yml` with every setting present and commented, plus a `.briefkit/` directory (with a `.gitkeep`) that marks the project root. Refuses to overwrite an existing file unless `--force`. `--dry-run` prints what would be written and writes nothing. A path that is not an existing directory is an error.

---

## `briefkit preview`

```bash
briefkit preview <path> [flags]
```

Runs `generate` with the same flags, then opens the PDF with `open` (macOS), `xdg-open` (Linux) or the file association (Windows).

---

## `briefkit status`

```bash
briefkit status [path] [flags]
```

```bash
briefkit status docs/
briefkit status docs/ --json       # [{path, output, status}, ...]
briefkit status docs/ --check      # exit 1 if anything is stale or missing (for CI)
```

```
  CURRENT  /path/to/docs/education/cognitive-load-theory
  STALE    /path/to/docs/education/assessment-methods
  MISSING  /path/to/docs/education/instructional-design

  3 total — 1 current, 1 stale, 1 missing
```

Without `--check` the exit code is always 0.

---

## `briefkit assign-ids`

```bash
briefkit assign-ids <path> [flags]
```

Records a document ID in the registry for every directory under `<path>` that already holds a generated PDF; Markdown files are never modified. IDs are normally assigned during `generate`, so this is for trees whose PDFs were built with `--no-ids`.

```bash
briefkit assign-ids docs/
briefkit assign-ids docs/ --dry-run     # "would be assigned"
briefkit assign-ids docs/ --json        # {checked, assigned, existing, dry_run}
```

---

## `briefkit quality`

```bash
briefkit quality <path> [flags]
```

Checks an existing PDF (`<path>` is a `.pdf` file or a directory holding `output.filename`).

| Check | Result |
|------|----------|
| File exists, is not empty, starts with `%PDF-` | FAIL otherwise |
| Parses, has at least one page, text on the first page | FAIL otherwise (needs pypdf: `pip install "briefkit[quality]"`) |
| Title in the metadata | WARN if absent |
| Size below the level's hard minimum, or pages below the minimum | WARN, or FAIL with `--strict` |
| Size below the level's soft target | WARN |

Thresholds come from `quality:` in `briefkit.yml`, then from the level defaults (level 3: 5 KB hard, 20 KB soft, 2 pages). Options: `--level {1,2,3,4}`, `--strict`, `--json` (the banner goes to stderr, stdout is pure JSON). Exit 0 on pass, 1 on fail or when the PDF is missing.

---

## `briefkit selftest`

```bash
briefkit selftest [flags]
```

Builds a two-file document set in a temporary directory with document IDs off, then checks that the PDF exists, has at least one page and carries the fixture text (the last two need pypdf). Honors `--template`, `--preset`, `--variant`, `--json`, `--quiet`. Writes nothing into the current project. Exit 1 on any failed check.

---

## `briefkit config`, `templates`, `presets`, `licenses`

```bash
briefkit config                 # resolved configuration as YAML
briefkit config --json
briefkit templates              # name and description per template
briefkit templates --quiet      # names only
briefkit templates --json
briefkit presets                # every preset with its 16 brand keys
briefkit presets --quiet        # names only
briefkit licenses               # license presets by category, with SPDX identifiers
briefkit licenses --quiet
```

`config` prints warnings for unknown keys in `briefkit.yml` (with the closest valid name) on stderr.

---

## Flags by command

| Flag | Applies to | Effect |
|------|-----------|--------|
| `--config FILE`, `-c` | every subcommand | Use this `briefkit.yml` instead of discovering one upward from the current directory |
| `--quiet`, `-q` | every subcommand | Suppress progress output (`templates -q` and `presets -q` list names only) |
| `--verbose` | generate, batch, preview, selftest | Extraction, variant and build details on stderr; elsewhere, a full traceback on error |
| `--json` | generate, batch, status, assign-ids, quality, selftest, config, templates, presets, licenses | Pure JSON on stdout |
| `--dry-run` | every subcommand (acted on by generate, batch, init, assign-ids) | Report without writing |
| `--template NAME`, `-t` | generate, batch, preview, selftest | Any name from `briefkit templates` |
| `--preset NAME`, `-p` | generate, batch, preview, selftest | Any name from `briefkit presets --quiet` |
| `--variant NAME`, `-v` | generate, batch, preview, selftest | A variant name, or `none` |
| `--output PATH`, `-o` | generate, preview | File, or directory to receive `output.filename`; for `batch`, the mirror directory |
| `--force`, `-f` | batch, init (accepted and ignored by generate, preview, selftest) | batch: rebuild current output too; init: overwrite an existing `briefkit.yml` |
| `--no-ids` | generate, batch, preview, selftest | No document ID |
| `--logo PATH` | generate, batch, preview | PNG, JPEG or GIF on the cover |
| `--org NAME` | generate, batch, preview | Organization on cover, running head, back cover and PDF author |
| `--title TEXT` | generate, preview | Document title (ignored by batch) |
| `--check` | status | Exit 1 when anything is stale or missing |
| `--level N`, `--strict` | quality | Threshold level; thresholds fail instead of warn |
| `--version` | top level | Print the version |

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | An error (not a directory, unknown template or preset, a failed build, a failed quality check, a failed selftest, a batch with failures, `status --check` with stale or missing output) |
| 2 | `generate` or `generate --dry-run` could not extract anything from the directory; also argparse's own usage errors |
| 130 | Interrupted with Ctrl-C |

Uncaught errors print `Error: <message>` and `Run with --verbose for a full traceback.` and exit 1.

---

## Environment

| Variable | Effect |
|---|---|
| `SOURCE_DATE_EPOCH` | Every printed date and the PDF timestamps come from this Unix time, so the same input produces byte-identical PDFs |

---

## Common workflows

```bash
briefkit generate docs/my-topic/                 # one briefing
briefkit batch docs/                             # everything, skipping current output
briefkit status docs/ && briefkit batch docs/ --dry-run
briefkit batch docs/ --force                     # after changing template, preset or margins
briefkit preview docs/my-topic/                  # edit, run again
SOURCE_DATE_EPOCH=0 briefkit batch docs/ --force --quiet; echo $?   # CI: reproducible, 0 = success
briefkit status docs/ --check                    # CI: fail on stale output
briefkit config --json > resolved-config.json
```

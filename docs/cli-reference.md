# CLI Reference

Every BriefKit command, flag, and option with practical examples.

---

## Commands Overview

| Command | Purpose |
|---------|---------|
| `briefkit generate <path>` | Generate a PDF from one directory |
| `briefkit batch <root>` | Generate PDFs for all eligible directories under root |
| `briefkit init [path]` | Create `briefkit.yml` with defaults |
| `briefkit preview <path>` | Generate and open PDF in system viewer |
| `briefkit status [path]` | Show which briefings are current, stale, or missing |
| `briefkit assign-ids <path>` | Assign document IDs without generating PDFs |
| `briefkit quality <path>` | Run quality gates on an existing PDF |
| `briefkit selftest` | Generate from built-in test fixture to verify installation |
| `briefkit config` | Print the resolved configuration |
| `briefkit templates` | List available templates |
| `briefkit presets` | List color presets with hex values |

---

## `briefkit generate`

Generate a briefing PDF from a directory of markdown files.

```bash
briefkit generate <path> [flags]
```

### Examples

```bash
# Basic generation
briefkit generate docs/my-topic/

# With a specific template and color preset
briefkit generate docs/my-topic/ --template report --preset charcoal

# Override output location
briefkit generate docs/my-topic/ --output ./output/my-briefing.pdf

# Override the document title
briefkit generate docs/my-topic/ --title "Q4 Security Assessment"

# Override organization name
briefkit generate docs/my-topic/ --org "ACME Corp"

# Add a logo
briefkit generate docs/my-topic/ --logo logo.png

# Force a specific domain variant
briefkit generate docs/ml-research/ --variant aiml

# Skip document ID assignment
briefkit generate docs/my-topic/ --no-ids

# Dry run (show what would be generated without writing)
briefkit generate docs/my-topic/ --dry-run

# Verbose mode (show extraction details)
briefkit generate docs/my-topic/ --verbose

# Quiet mode (errors only)
briefkit generate docs/my-topic/ --quiet

# Use a specific config file
briefkit generate docs/my-topic/ --config /path/to/briefkit.yml
```

### Output

The PDF is written to `<path>/executive-briefing.pdf` by default. Override with `--output` or the `output.filename` config key.

---

## `briefkit batch`

Recursively find and generate briefings for all eligible directories.

```bash
briefkit batch <root> [flags]
```

A directory is "eligible" if it contains at least one file matching the numbered doc pattern (default: `[0-9][0-9]-*.md`).

### Examples

```bash
# Generate all briefings under docs/
briefkit batch docs/

# Force regeneration of everything (even if current)
briefkit batch docs/ --force

# Dry run -- show what would be generated
briefkit batch docs/ --dry-run

# JSON output for scripting
briefkit batch docs/ --json

# With template and preset overrides (applied to all)
briefkit batch docs/ --template report --preset charcoal

# Quiet mode
briefkit batch docs/ --quiet
```

### Output

```
  [1/5] GENERATE  education/cognitive-load-theory
             -> /path/to/education/cognitive-load-theory/executive-briefing.pdf  (1.2s)
  [2/5] SKIP      education/assessment-methods  (current)
  [3/5] GENERATE  education/instructional-design
             -> /path/to/education/instructional-design/executive-briefing.pdf  (0.8s)
  ...

  Batch complete in 4.1s
  5 target(s) found -- 3 generated, 2 skipped, 0 failed
```

### Staleness Detection

By default, batch mode skips directories where the output PDF is newer than all source markdown files. Use `--force` to regenerate everything.

---

## `briefkit init`

Create a `briefkit.yml` configuration file with sensible defaults.

```bash
briefkit init [path] [flags]
```

### Examples

```bash
# Create briefkit.yml in current directory
briefkit init

# Create in a specific directory
briefkit init /path/to/project

# Overwrite existing config
briefkit init --force
```

Also creates a `.briefkit/` directory with a `.gitkeep`.

---

## `briefkit preview`

Generate the PDF and open it with the system default PDF viewer.

```bash
briefkit preview <path> [flags]
```

### Examples

```bash
# Generate and open
briefkit preview docs/my-topic/

# With template override
briefkit preview docs/my-topic/ --template academic
```

Uses `open` on macOS, `xdg-open` on Linux, and `os.startfile` on Windows.

---

## `briefkit status`

Show whether briefings are current, stale, or missing.

```bash
briefkit status [path] [flags]
```

### Examples

```bash
# Check all directories under current path
briefkit status

# Check a specific root
briefkit status docs/

# JSON output
briefkit status docs/ --json
```

### Output

```
  CURRENT  docs/education/cognitive-load-theory
  STALE    docs/education/assessment-methods
  MISSING  docs/education/instructional-design

  3 total -- 1 current, 1 stale, 1 missing
```

---

## `briefkit assign-ids`

Assign document IDs to markdown files without regenerating PDFs.

```bash
briefkit assign-ids <path> [flags]
```

### Examples

```bash
# Assign IDs
briefkit assign-ids docs/my-topic/

# Dry run
briefkit assign-ids docs/my-topic/ --dry-run
```

---

## `briefkit quality`

Run quality gates on an existing PDF.

```bash
briefkit quality <path> [flags]
```

### Examples

```bash
# Check a directory (looks for executive-briefing.pdf inside it)
briefkit quality docs/my-topic/

# Check a specific PDF file
briefkit quality docs/my-topic/executive-briefing.pdf

# JSON output
briefkit quality docs/my-topic/ --json
```

### Quality Gates

| Gate | Behavior |
|------|----------|
| Hard minimum (file size by level) | Fails the check |
| Soft target (file size by level) | Warning only |
| Valid PDF header | Fails if not a valid PDF |

Default thresholds (Level 3 doc set):
- Hard minimum: 20 KB
- Soft target: 80 KB
- Minimum pages: 2

---

## `briefkit selftest`

Run a selftest using a built-in fixture to verify the installation.

```bash
briefkit selftest [flags]
```

### Examples

```bash
# Run selftest
briefkit selftest

# With verbose output
briefkit selftest --verbose
```

---

## `briefkit config`

Print the fully resolved configuration (defaults + YAML file + dynamic values).

```bash
briefkit config [flags]
```

### Examples

```bash
# Print as YAML (if PyYAML installed)
briefkit config

# Print as JSON
briefkit config --json

# Use a specific config file
briefkit config --config /path/to/briefkit.yml
```

---

## `briefkit templates`

List all available templates.

```bash
briefkit templates [flags]
```

### Examples

```bash
briefkit templates
briefkit templates --json
```

---

## `briefkit presets`

List all color presets with their hex values.

```bash
briefkit presets [flags]
```

### Examples

```bash
# Full output with all color keys
briefkit presets

# Names only
briefkit presets --quiet

# JSON output
briefkit presets --json
```

---

## Global Flags

These flags work with all commands:

| Flag | Short | Description |
|------|-------|-------------|
| `--config FILE` | `-c` | Path to `briefkit.yml` (default: auto-discover from CWD upward) |
| `--quiet` | `-q` | Suppress non-error output |
| `--verbose` | | Show detailed extraction and debug info |
| `--json` | | Output results as JSON |
| `--dry-run` | | Show what would be done without writing files |
| `--version` | | Print version and exit |

## Generation Flags

These flags work with `generate`, `batch`, `preview`, and `selftest`:

| Flag | Short | Description |
|------|-------|-------------|
| `--template NAME` | `-t` | Template preset (`briefing`, `report`, `book`, `manual`, `academic`, `minimal`, `letter`, `contract`, `register`, `minutes`) |
| `--preset NAME` | `-p` | Color preset (`navy`, `charcoal`, `ocean`, `forest`, `crimson`, `slate`, `royal`, `sunset`, `mono`, `midnight`, `emerald`, `corporate`, `arctic`, `terracotta`, `ink`) |
| `--variant NAME` | `-v` | Force a domain variant (`aiml`, `legal`, `medical`, `engineering`, `research`, `api`, `gaming`, `finance`, `species`, `historical`, `hardware`, `religion`) |
| `--output PATH` | `-o` | Override output PDF path |
| `--force` | `-f` | Regenerate even if output is current |
| `--no-ids` | | Skip document ID assignment |
| `--logo PATH` | | Path to logo image file |
| `--org NAME` | | Override organization name |
| `--title TEXT` | | Override document title |

---

## Common Workflows

### Generate a Single Briefing

```bash
briefkit generate docs/my-topic/
```

### Generate Everything in a Project

```bash
briefkit batch docs/
```

### Check What Needs Regeneration

```bash
briefkit status docs/
briefkit batch docs/ --dry-run
```

### Force Regeneration After Config Change

```bash
briefkit batch docs/ --force
```

### Quick Preview Cycle

```bash
briefkit preview docs/my-topic/
# Edit markdown...
briefkit preview docs/my-topic/ --force
```

### CI Pipeline

```bash
briefkit batch docs/ --force --quiet
echo $?  # 0 = success, 1 = failures
```

### Export Config for Debugging

```bash
briefkit config --json > resolved-config.json
```

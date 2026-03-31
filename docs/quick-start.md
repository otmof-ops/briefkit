# Quick Start

Get from zero to PDF in 60 seconds.

---

## Step 1: Install

```bash
pip install briefkit
```

Verify it worked:

```bash
briefkit selftest
```

This generates a test PDF from a built-in fixture. If it succeeds, everything is working.

## Step 2: Create a Source Directory

BriefKit reads numbered markdown files from a directory. Create one:

```bash
mkdir -p my-project/docs/my-topic
```

Add a `README.md` (sets the title and overview):

```bash
cat > my-project/docs/my-topic/README.md << 'EOF'
# My First Briefing

This briefing covers the key points of my topic.
It demonstrates how BriefKit converts markdown to PDF.
EOF
```

Add numbered content files:

```bash
cat > my-project/docs/my-topic/01-introduction.md << 'EOF'
# Introduction

This is the first section of the briefing.

## Background

BriefKit turns structured markdown into professional PDFs with one command.

## Key Points

- Auto-generated table of contents
- Executive summary
- Bibliography extraction
- Cross-reference detection
EOF
```

```bash
cat > my-project/docs/my-topic/02-details.md << 'EOF'
# Technical Details

This section covers implementation specifics.

| Feature | Status | Notes |
|---------|--------|-------|
| PDF Generation | Complete | Uses ReportLab |
| Markdown Parsing | Complete | Built-in parser |
| Bibliography | Complete | 6 citation formats |
EOF
```

## Step 3: Generate

```bash
cd my-project
briefkit generate docs/my-topic/
```

Output:

```
Generating briefing for: /path/to/my-project/docs/my-topic
Output: /path/to/my-project/docs/my-topic/executive-briefing.pdf
Done in 1.2s
```

## Step 4: Find the Output

The PDF is written **inside the source directory** by default:

```
my-project/docs/my-topic/executive-briefing.pdf
```

To change the output location:

```bash
briefkit generate docs/my-topic/ --output ./output/my-briefing.pdf
```

## Step 5: Customize (Optional)

Change the template:

```bash
briefkit generate docs/my-topic/ --template report
```

Change the color scheme:

```bash
briefkit generate docs/my-topic/ --preset ocean
```

Combine both:

```bash
briefkit generate docs/my-topic/ --template academic --preset royal
```

## Step 6: Add a Config File (Optional)

Drop a `briefkit.yml` in your project root to avoid typing flags:

```bash
briefkit init
```

This creates a `briefkit.yml` with sensible defaults. Edit it:

```yaml
project:
  name: "My Project"
  org: "My Company"

brand:
  preset: ocean

template:
  preset: report
```

Now just run:

```bash
briefkit generate docs/my-topic/
```

The config is picked up automatically.

---

## What Next

- [Directory Structure Guide](directory-structure.md) -- how to organize source files
- [Templates Guide](templates-guide.md) -- what each template produces
- [CLI Reference](cli-reference.md) -- every command and flag
- [Troubleshooting](troubleshooting.md) -- fixing common issues

# Installation

## Requirements

BriefKit requires Python 3.10 or later and has only two runtime dependencies (ReportLab for PDF rendering, PyYAML for configuration parsing). It runs entirely offline with no external API calls.

| Dependency | Minimum Version | Installed Automatically | Notes |
|-----------|----------------|------------------------|-------|
| Python | 3.10 | No | Install from python.org or your system package manager |
| ReportLab | 4.0 | Yes | PDF generation engine |
| PyYAML | 6.0.1 | Yes | YAML configuration parser |

## Install from PyPI

```bash
pip install briefkit
```

## Install from Source

For development or to run the latest unreleased version:

```bash
git clone https://github.com/otmof-ops/briefkit.git
cd briefkit
pip install -e ".[dev]"
```

The `[dev]` extra installs pytest, pytest-cov, and pypdf for running the test suite.

## Verify Installation

Run the built-in self-test to confirm everything works:

```bash
briefkit selftest
```

You should see output like:

```
Generating briefing for: /tmp/briefkit-selftest-XXXXXXXX
Output: /tmp/briefkit-selftest-XXXXXXXX/executive-briefing.pdf
```

If the self-test produces a PDF without errors, BriefKit is ready to use.

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Linux | Full support | Recommended for CI/CD integration |
| macOS | Full support | Intel and Apple Silicon |
| Windows | Full support | Native Python, no WSL required |

> BriefKit is a pure Python package with no compiled extensions. It runs anywhere Python 3.10+ runs.

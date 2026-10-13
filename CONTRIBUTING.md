# Contributing to BriefKit

Copyright (c) 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)

---

## Contributor License Agreement

By submitting a contribution to this repository (including but not limited to pull requests, patches, code, documentation, or any other materials), You represent, warrant, and agree to the following:

1. **Grant of Rights.** You hereby grant to OFFTRACKMEDIA Studios a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable license to use, reproduce, modify, prepare derivative works of, publicly display, publicly perform, sublicense, and distribute Your contribution and any derivative works thereof, in any medium and for any purpose.

2. **Original Work.** You represent that Your contribution is Your original work and does not infringe, misappropriate, or otherwise violate any intellectual property rights or other rights of any third party.

3. **Authority.** You represent that You have the legal authority to grant the rights described herein, and that You are not subject to any agreement or obligation that would prevent You from making the contribution.

4. **No Obligation.** OFFTRACKMEDIA Studios is under no obligation to accept, merge, or use any contribution, and may reject contributions at its sole discretion.

---

## How to Contribute

### 1. Fork and Branch

```bash
git clone https://github.com/YOUR-USERNAME/briefkit.git
cd briefkit
git checkout -b feat/your-feature-name
```

### 2. Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install          # optional: ruff and ruff-format on every commit
```

Verify:

```bash
make check                  # ruff check, ruff format --check, pytest, briefkit selftest
```

The `Makefile` targets are `install`, `test`, `lint`, `format`, `format-check`, `check`, `selftest`, `audit` (pip-audit), `build` and `clean`.

### 3. Make Changes

- Follow the coding standards below
- Write tests for new functionality
- Update documentation if behavior changes

### 4. Commit

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat(scope): add new feature description"
```

### 5. Submit a Pull Request

```bash
git push origin feat/your-feature-name
```

Open a Pull Request on GitHub against the `main` branch. Fill out the PR template completely. CI runs ruff, the test suite on Linux, macOS and Windows across Python 3.10 to 3.13 (3.14 is informational), a package build, pip-audit and a clean-tree check, and fails if coverage drops below the floor set in `.github/workflows/test.yml`.

---

## What We Accept

| Contribution Type | Notes |
|-------------------|-------|
| Bug fixes | Must include a regression test |
| New templates | Must include a test and a section in `docs/templates-guide.md` |
| New variants | Must include `auto_detect_keywords` and a row in `docs/variants.md` |
| New color presets | All 16 keys, 6-digit hex colors; regenerate `docs/color-presets.md` |
| Documentation fixes | American English spelling required; `tests/test_docs.py` checks commands, links and spelling |
| Test improvements | Coverage increases are always welcome |
| Performance improvements | Must include a benchmark comparison |

## What We Do Not Accept

| Contribution Type | Reason |
|-------------------|--------|
| External API dependencies | Offline operation is a design requirement |
| Hardcoded secrets or credentials | Security policy violation |
| Contributions without tests | Quality gate requirement |
| British English spelling | Project standard is American English |
| Large-scale reformatting PRs | Must justify the churn in an issue first |
| Features duplicating existing functionality | Open an issue to discuss first |
| A third-party CLI framework or logging framework | See `docs/adr/001` and `docs/adr/004` |

---

## Running Tests

```bash
pytest                          # All tests
pytest --cov=briefkit           # With coverage
pytest tests/test_parser.py     # Single module
briefkit selftest               # Smoke test in a temporary directory
```

Tests never write into the source tree: fixtures are copied into a temporary project with document IDs disabled (see `tests/conftest.py`). Set `SOURCE_DATE_EPOCH` when a test compares PDF bytes.

---

## Adding Templates

1. Create a module in `src/briefkit/templates/` (snake_case file name)
2. Subclass `BaseBriefingTemplate`; implement `build_story()`; declare traits (`pdf_subject`, `design_page_size`, `design_margins_mm`, `supports_variants`) and any hooks you need (`prepare`, `header_footer`, `before_build`). Do not override `generate()`; it is final and a subclass that overrides it gets a `DeprecationWarning`.
3. Use brand lookups (`self.brand["font_body"]`, `self.styles["STYLE_H1"]`) rather than font or color literals, so presets apply
4. Register it in the `_REGISTRY` dict in `src/briefkit/templates/__init__.py` and export the class in `__all__`
5. Add a test in `tests/test_templates.py` (every registered template is built once by the contract tests) and a section in `docs/templates-guide.md`

The hook and trait API: [docs/custom-templates.md](docs/custom-templates.md).

## Adding Variants

1. Create a module in `src/briefkit/variants/`
2. Subclass `DocSetVariant`; set `name` and `auto_detect_keywords`; implement `build_variant_sections()`; decorate the class with `@_register`
3. Add the module to the import list in `_ensure_registry_populated()` in `src/briefkit/variants/__init__.py`
4. Add a row to `docs/variants.md` and a test in `tests/test_variants.py`

## Adding Color Presets

Add an entry to the `PRESETS` dict in `src/briefkit/presets/colors.py`. All sixteen keys are required: twelve colors (`primary`, `secondary`, `accent`, `body_text`, `caption`, `background`, `rule`, `success`, `warning`, `danger`, `code_bg`, `table_alt`) as 6-digit hex codes, and four fonts (`font_body`, `font_heading`, `font_mono`, `font_caption`) from the PDF base fourteen. Then add the preset to `docs/presets-guide.md` and regenerate `docs/color-presets.md`.

---

## Code Style

| Rule | Standard |
|------|----------|
| Formatting and lint | `ruff format` and `ruff check` (configured in `pyproject.toml`); CI fails on either |
| File naming | snake_case for Python modules, kebab-case for documentation |
| Spelling | American English in code, documentation and user-facing strings |
| Imports | stdlib, third-party, local, separated by blank lines (ruff's isort rules) |
| Output | `print()` to stdout for results and stderr for warnings; no logging framework (ADR-004) |
| Data strings in PDF markup | Escape with `briefkit.styles.esc` or build paragraphs with `safe_para`; never interpolate raw text into ReportLab markup |
| Secrets | None; no hardcoded API keys or passwords |
| Input validation | At all system boundaries (configuration, paths, Markdown) |

---

## Commit Conventions

| Type | When to Use |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `refactor` | Code restructuring, no behavior change |
| `test` | Adding or correcting tests |
| `build` | Build system or dependency changes |
| `ci` | CI configuration changes |

---

## Pull Request Checklist

- [ ] `make check` passes (lint, format, tests, selftest)
- [ ] Coverage does not decrease
- [ ] New public API has docstrings
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] American English spelling throughout
- [ ] CLA confirmed (first-time contributors)

---

## Code of Conduct

All contributors are expected to behave professionally and respectfully. We do not tolerate harassment, discrimination, or abusive behavior of any kind.

---

## Security Vulnerabilities

**Do not file public GitHub issues for security vulnerabilities.** See [SECURITY.md](SECURITY.md) for the responsible disclosure process.

---

## Governance Documents

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview and quickstart |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [LICENSE](LICENSE) | BSD 3-Clause license text (the code) |
| [LICENSES/](LICENSES/) | The CC BY 4.0, CC0 1.0, CC BY-NC-SA 4.0 and CC BY-NC-ND 4.0 texts that REUSE.toml maps to paths |
| [REUSE.toml](REUSE.toml) | Which license applies to which path |
| [NOTICE.txt](NOTICE.txt) | Copyright line, license map, third-party components |
| [TRADEMARKS.md](TRADEMARKS.md) | Name policy: what forks may be called |
| [SAFETY.md](SAFETY.md) | Safety framework |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting policy |
| [CONTRIBUTING.md](CONTRIBUTING.md) | This document |
| [docs/adr/](docs/adr/) | Architecture decision records |

---

Copyright (c) 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)

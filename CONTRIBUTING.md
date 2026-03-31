# Contributing to BriefKit

Copyright (c) 2026 OFFTRACKMEDIA Studios. All rights reserved.

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
```

Verify:

```bash
pytest --tb=short
briefkit selftest
```

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

Open a Pull Request on GitHub against the `main` branch. Fill out the PR template completely.

---

## What We Accept

| Contribution Type | Notes |
|-------------------|-------|
| Bug fixes | Must include a regression test |
| New templates | Must include selftest fixture and documentation |
| New variants | Must include `auto_detect_keywords` list |
| New color presets | Must pass hex validation; all 7 keys required |
| Documentation fixes | American English spelling required |
| Test improvements | Coverage increases are always welcome |
| Performance improvements | Must include benchmark comparison |

## What We Do Not Accept

| Contribution Type | Reason |
|-------------------|--------|
| External API dependencies | Offline operation is a design requirement |
| Hardcoded secrets or credentials | Security policy violation |
| Contributions without tests | Quality gate requirement |
| British English spelling | Project standard is American English |
| Large-scale reformatting PRs | Must justify the churn in an issue first |
| Features duplicating existing functionality | Open an issue to discuss first |

---

## Running Tests

```bash
pytest                          # All tests
pytest --cov=briefkit           # With coverage
pytest tests/test_parser.py     # Single module
briefkit selftest               # Smoke test
```

---

## Adding Templates

1. Create a new file in `src/briefkit/templates/`
2. Subclass `BaseBriefingTemplate`
3. Override `build_story()` to define section order
4. Register in `src/briefkit/templates/__init__.py`
5. Add a test fixture under `tests/fixtures/`

## Adding Variants

1. Create a new file in `src/briefkit/variants/`
2. Subclass `DocSetVariant`
3. Set `name`, `auto_detect_keywords`, implement `build_variant_sections()`
4. Register in `src/briefkit/variants/__init__.py`

## Adding Color Presets

Add a new entry to the `PRESETS` dict in `src/briefkit/presets/colors.py`. All seven keys are required: `primary`, `secondary`, `accent`, `body_text`, `caption`, `background`, `rule`. Values must be 6-digit hex codes (e.g., `#1B2A4A`).

---

## Code Style

| Rule | Standard |
|------|----------|
| File naming | Kebab-case |
| Spelling | American English |
| Imports | stdlib, third-party, local — separated by blank lines |
| Secrets | None — no hardcoded API keys or passwords |
| Input validation | At all system boundaries |

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

- [ ] All tests pass (`pytest`)
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
| [LICENSE](LICENSE) | CC BY-NC-SA 4.0 license text |
| [NOTICE.txt](NOTICE.txt) | Copyright, trademarks, third-party acknowledgments |
| [EULA](EULA/OFFTRACKMEDIA_EULA_2025.txt) | End User License Agreement |
| [SAFETY.md](SAFETY.md) | Safety framework |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting policy |
| [CONTRIBUTING.md](CONTRIBUTING.md) | This document |

---

(c) 2026 OFFTRACKMEDIA Studios · ABN 84 290 819 896

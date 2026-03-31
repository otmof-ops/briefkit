# CI Integration

## GitHub Actions

```yaml
name: Generate Briefings
on:
  push:
    paths:
      - 'docs/**/*.md'

jobs:
  briefings:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - run: pip install briefkit

      - run: briefkit batch docs/ --force

      - uses: actions/upload-artifact@v4
        with:
          name: briefings
          path: '**/executive-briefing.pdf'
```

## GitLab CI

```yaml
generate-briefings:
  image: python:3.12
  script:
    - pip install briefkit
    - briefkit batch docs/ --force
  artifacts:
    paths:
      - '**/executive-briefing.pdf'
  only:
    changes:
      - docs/**/*.md
```

## Skip-if-current

By default, `briefkit batch` skips directories where the existing PDF version matches the current template version. Use `--force` to regenerate everything.

## Status Check

Use `briefkit status` in CI to verify all briefings are current:

```bash
briefkit status docs/ --json
```

Returns exit code 1 if any briefings are stale or missing.

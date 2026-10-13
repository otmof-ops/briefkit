# CI Integration

Install from Git, build, upload the PDFs. Set `SOURCE_DATE_EPOCH` so an unchanged tree produces byte-identical artifacts.

## GitHub Actions

```yaml
name: Generate Briefings
on:
  push:
    paths:
      - 'docs/**'
      - 'briefkit.yml'

jobs:
  briefings:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - run: pip install "git+https://github.com/otmof-ops/briefkit.git"

      - run: briefkit batch docs/ --force --quiet
        env:
          SOURCE_DATE_EPOCH: "0"

      - uses: actions/upload-artifact@v4
        with:
          name: briefings
          path: '**/executive-briefing.pdf'
```

## GitLab CI

```yaml
generate-briefings:
  image: python:3.12
  variables:
    SOURCE_DATE_EPOCH: "0"
  script:
    - pip install "git+https://github.com/otmof-ops/briefkit.git"
    - briefkit batch docs/ --force --quiet
  artifacts:
    paths:
      - '**/executive-briefing.pdf'
  only:
    changes:
      - docs/**
      - briefkit.yml
```

## Skip-if-current

Without `--force`, `briefkit batch` skips a directory whose PDF is newer than every input it depends on: the numbered documents, the orientation document, `README.md`, the companion files (`engineering-brilliance.md`, `guide.md`, `preface.md`, `glossary.md`, `methodology.md`, `.source-type`) and the project's `briefkit.yml`. A template or preset chosen by flag is not an input; use `--force` after changing it.

## Failing a pipeline on stale output

```bash
briefkit status docs/ --check     # exit 1 if any briefing is stale or missing
```

`briefkit batch` itself exits 1 when any directory fails to build.

## Checking the result

```bash
briefkit quality docs/my-topic/ --strict
```

The structural checks (header, parse, pages, text) need pypdf: `pip install "briefkit[quality]"`.

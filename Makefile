.PHONY: install test lint format format-check check selftest audit build clean

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

format-check:
	ruff format --check src/ tests/

check: lint format-check test selftest

selftest:
	briefkit selftest --no-ids

audit:
	pip-audit --skip-editable --progress-spinner off

build:
	python -m build

clean:
	rm -rf dist/ build/ src/*.egg-info .coverage coverage.xml

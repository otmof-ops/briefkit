.PHONY: install test lint format typecheck audit build clean

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

audit:
	pip-audit

build:
	python -m build

clean:
	rm -rf dist/ build/ src/*.egg-info .coverage coverage.xml

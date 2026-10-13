"""
Shared test fixtures for BriefKit tests.

Every fixture directory is copied into a fresh temporary project before a
test sees it, so that (a) nothing a test generates lands in the source tree
and (b) the briefing level is deterministic: the copy sits two levels below
a ``briefkit.yml`` project root, which the default hierarchy maps to
level 3, whatever ``.briefkit`` directory may exist above the checkout on a
developer's machine. Document IDs are disabled in that project so no test
can touch a real registry.
"""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _project_copy(tmp_path: Path, name: str) -> Path:
    root = tmp_path / "project"
    root.mkdir(exist_ok=True)
    (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n", encoding="utf-8")
    dest = root / "docs" / name
    shutil.copytree(FIXTURES_DIR / name, dest)
    return dest


@pytest.fixture(autouse=True)
def _fresh_project_root_cache():
    """Project-root discovery is cached per process; never let one test's CWD leak into the next."""
    from briefkit.config import clear_project_root_cache

    clear_project_root_cache()
    yield
    clear_project_root_cache()


@pytest.fixture
def basic_fixture(tmp_path):
    """Copy of the basic fixture (README + 2 numbered docs) inside a temporary project."""
    return _project_copy(tmp_path, "basic")


@pytest.fixture
def full_fixture(tmp_path):
    """Copy of the full fixture (README + orientation + 3 numbered + guide + brilliance)."""
    return _project_copy(tmp_path, "full")


@pytest.fixture
def legal_fixture(tmp_path):
    """Copy of the legal domain fixture for variant testing."""
    return _project_copy(tmp_path, "legal")


@pytest.fixture
def empty_fixture(tmp_path):
    """Copy of the empty fixture for edge case testing."""
    return _project_copy(tmp_path, "empty")


@pytest.fixture
def default_config():
    """Default BriefKit configuration dict."""
    from briefkit.config import DEFAULTS

    return copy.deepcopy(DEFAULTS)


@pytest.fixture
def tmp_output(tmp_path):
    """Temporary output directory for generated PDFs."""
    out = tmp_path / "out"
    out.mkdir()
    return out

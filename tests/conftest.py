"""Shared test fixtures for BriefKit tests."""
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def basic_fixture():
    """Path to the basic test fixture (README + 2 numbered docs)."""
    return FIXTURES_DIR / "basic"


@pytest.fixture
def full_fixture():
    """Path to the full test fixture (README + orientation + 3 numbered + guide + brilliance)."""
    return FIXTURES_DIR / "full"


@pytest.fixture
def legal_fixture():
    """Path to the legal domain fixture for variant testing."""
    return FIXTURES_DIR / "legal"


@pytest.fixture
def empty_fixture():
    """Path to the empty fixture for edge case testing."""
    return FIXTURES_DIR / "empty"


@pytest.fixture
def default_config():
    """Default BriefKit configuration dict."""
    from briefkit.config import DEFAULTS
    import copy
    return copy.deepcopy(DEFAULTS)


@pytest.fixture
def tmp_output(tmp_path):
    """Temporary output directory for generated PDFs."""
    return tmp_path

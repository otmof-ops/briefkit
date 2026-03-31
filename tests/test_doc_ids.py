"""Tests for the document ID system."""
import pytest
import json
from pathlib import Path
from briefkit.doc_ids import get_or_assign_doc_id, load_registry


@pytest.fixture
def doc_id_config(tmp_path):
    """Config with temporary registry path."""
    registry = tmp_path / ".briefkit" / "registry.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    return {
        "doc_ids": {
            "enabled": True,
            "prefix": "DOC",
            "type": "BRF",
            "year_format": "short",
            "sequence_digits": 4,
            "registry_path": str(registry),
            "group_codes": {"docs": "DOC", "api": "API"},
            "format": "{prefix}-{type}-{group}-{level}{seq}/{year}",
        },
        "output": {"filename": "executive-briefing.pdf"},
    }


class TestAssignment:
    def test_assigns_new_id(self, tmp_path, doc_id_config):
        target = tmp_path / "docs" / "getting-started"
        target.mkdir(parents=True)
        doc_id = get_or_assign_doc_id(target, level=3, title="Getting Started", config=doc_id_config)
        assert "DOC" in doc_id or "BRF" in doc_id
        assert "/" in doc_id  # has year suffix

    def test_returns_existing_id(self, tmp_path, doc_id_config):
        target = tmp_path / "docs" / "getting-started"
        target.mkdir(parents=True)
        id1 = get_or_assign_doc_id(target, level=3, title="Getting Started", config=doc_id_config)
        id2 = get_or_assign_doc_id(target, level=3, title="Getting Started", config=doc_id_config)
        assert id1 == id2

    def test_sequential_ids(self, tmp_path, doc_id_config):
        t1 = tmp_path / "docs" / "alpha"
        t2 = tmp_path / "docs" / "beta"
        t1.mkdir(parents=True)
        t2.mkdir(parents=True)
        id1 = get_or_assign_doc_id(t1, level=3, title="Alpha", config=doc_id_config)
        id2 = get_or_assign_doc_id(t2, level=3, title="Beta", config=doc_id_config)
        assert id1 != id2

    def test_disabled_returns_empty(self, tmp_path):
        target = tmp_path / "item"
        target.mkdir(parents=True)
        config = {"doc_ids": {"enabled": False}}
        doc_id = get_or_assign_doc_id(target, level=3, title="Item", config=config)
        assert doc_id == ""


class TestPersistence:
    def test_registry_persisted(self, tmp_path, doc_id_config):
        target = tmp_path / "docs" / "item"
        target.mkdir(parents=True)
        get_or_assign_doc_id(target, level=3, title="Item", config=doc_id_config)
        registry_path = Path(doc_id_config["doc_ids"]["registry_path"])
        data = json.loads(registry_path.read_text())
        assert len(data["entries"]) == 1
        assert data["entries"][0]["title"] == "Item"

    def test_counters_tracked(self, tmp_path, doc_id_config):
        target = tmp_path / "docs" / "item"
        target.mkdir(parents=True)
        get_or_assign_doc_id(target, level=3, title="Item", config=doc_id_config)
        registry_path = Path(doc_id_config["doc_ids"]["registry_path"])
        data = json.loads(registry_path.read_text())
        assert "L3" in str(data.get("counters", {}))

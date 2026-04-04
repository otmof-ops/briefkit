"""Tests for briefkit cross-reference extraction."""
from __future__ import annotations

from briefkit.cross_refs import extract_cross_refs


class TestExtractCrossRefs:

    def test_empty_directory(self, tmp_path):
        refs, labels = extract_cross_refs(tmp_path)
        assert isinstance(refs, list)
        assert isinstance(labels, dict)
        assert len(refs) == 0

    def test_no_markdown_files(self, tmp_path):
        (tmp_path / "data.txt").write_text("no markdown here")
        refs, labels = extract_cross_refs(tmp_path)
        assert len(refs) == 0

    def test_returns_tuple(self, tmp_path):
        result = extract_cross_refs(tmp_path)
        assert isinstance(result, tuple)
        assert len(result) == 2

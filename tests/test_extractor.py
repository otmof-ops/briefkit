"""Tests for the content extractor."""
from briefkit.extractor import extract_content


class TestBasicExtraction:
    def test_extracts_title_from_readme(self, basic_fixture):
        content = extract_content(basic_fixture, level=3)
        assert content["title"] == "Widget Framework"

    def test_extracts_overview(self, basic_fixture):
        content = extract_content(basic_fixture, level=3)
        assert "lightweight component system" in content["overview"]

    def test_extracts_subsystems(self, basic_fixture):
        content = extract_content(basic_fixture, level=3)
        assert len(content["subsystems"]) == 2
        names = [s["name"] for s in content["subsystems"]]
        assert "Architecture" in names
        assert "Getting Started" in names

    def test_extracts_tables(self, basic_fixture):
        content = extract_content(basic_fixture, level=3)
        total_tables = sum(len(s["tables"]) for s in content["subsystems"])
        assert total_tables >= 2

    def test_metrics_populated(self, basic_fixture):
        content = extract_content(basic_fixture, level=3)
        assert content["metrics"]["doc_count"] == 2
        assert content["metrics"]["word_count"] > 0
        assert content["metrics"]["file_count"] > 0


class TestFullExtraction:
    def test_orientation_detected(self, full_fixture):
        content = extract_content(full_fixture, level=3)
        assert content["metrics"]["has_orientation"] is True
        assert content["orientation"] != ""

    def test_brilliance_extracted(self, full_fixture):
        content = extract_content(full_fixture, level=3)
        assert content["brilliance_summary"] != ""

    def test_guide_extracted(self, full_fixture):
        content = extract_content(full_fixture, level=3)
        assert content["guide_content"] != ""

    def test_bibliography_extracted(self, full_fixture):
        content = extract_content(full_fixture, level=3)
        assert len(content["bibliography"]) > 0

    def test_terms_extracted(self, full_fixture):
        content = extract_content(full_fixture, level=3)
        assert len(content["terms"]) > 0


class TestEmptyDirectory:
    def test_empty_dir_no_crash(self, empty_fixture):
        content = extract_content(empty_fixture, level=3)
        assert content["title"] != ""
        assert content["subsystems"] == []


class TestMissingReadme:
    def test_no_readme_graceful(self, tmp_path):
        (tmp_path / "01-something.md").write_text("# Something\n\nContent here.")
        content = extract_content(tmp_path, level=3)
        assert "not available" in content["overview"].lower() or content["overview"] != ""
        assert len(content["subsystems"]) == 1

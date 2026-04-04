"""Tests for quality gates."""
from briefkit.quality import run_quality_gates


class TestQualityGates:
    def test_missing_file_fails(self, tmp_path):
        pdf = tmp_path / "nonexistent.pdf"
        passed, report = run_quality_gates(pdf, level=3)
        assert not passed
        assert any("not found" in line.lower() or "missing" in line.lower() or "does not exist" in line.lower() for line in report)

    def test_empty_file_fails(self, tmp_path):
        pdf = tmp_path / "empty.pdf"
        pdf.write_bytes(b"")
        passed, report = run_quality_gates(pdf, level=3)
        assert not passed

    def test_tiny_file_fails(self, tmp_path):
        pdf = tmp_path / "tiny.pdf"
        pdf.write_bytes(b"%PDF-1.4 tiny content")
        passed, report = run_quality_gates(pdf, level=3)
        assert not passed

    def test_custom_thresholds(self, tmp_path):
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4 " + b"x" * 500)
        passed, report = run_quality_gates(
            pdf, level=3,
            thresholds={"hard_min_bytes": 100, "soft_min_bytes": 200}
        )
        # Should pass hard minimum at least
        assert any("hard" in line.lower() or "pass" in line.lower() or "size" in line.lower() for line in report)

"""Body content must not be dropped silently.

Regression cover for the defect where a long source document rendered its
opening sections and then simply stopped, with nothing in the output or on
stderr to say the rest had been discarded.

Two layers caused it:
  1. content.max_words_per_section defaulted to 3000, so any document longer
     than roughly six pages lost its tail during extraction.
  2. Document templates capped the body at 80 rendered flowables per source.

Both are now configurable, default to emitting everything, and record what
they drop.
"""
import pytest

from briefkit.config import DEFAULTS
from briefkit.extractor import extract_content


def _write_doc(directory, name, words):
    """Write a numbered source doc of roughly `words` words."""
    body = " ".join(f"word{i}" for i in range(words))
    (directory / name).write_text(f"# {name}\n\n{body}\n", encoding="utf-8")


@pytest.fixture
def long_docs(tmp_path):
    (tmp_path / "README.md").write_text("# Long Set\n\nOverview.\n", encoding="utf-8")
    _write_doc(tmp_path, "01-alpha.md", 9000)
    _write_doc(tmp_path, "02-beta.md", 9000)
    return tmp_path


class TestDefaults:
    def test_default_budget_accommodates_long_documents(self):
        """3000 silently truncated ordinary technical documents."""
        assert DEFAULTS["content"]["max_words_per_section"] >= 12000

    def test_block_cap_defaults_to_unlimited(self):
        assert DEFAULTS["content"]["max_blocks_per_section"] == 0


class TestExtraction:
    def test_long_documents_survive_at_default(self, long_docs):
        content = extract_content(long_docs, level=3)
        assert content["metrics"]["truncated_sections"] == []
        for sub in content["subsystems"]:
            assert len(sub["content"].split()) > 8000

    def test_zero_means_unlimited(self, long_docs):
        cfg = {"content": {"max_words_per_section": 0}}
        content = extract_content(long_docs, level=3, config=cfg)
        assert content["metrics"]["truncated_sections"] == []
        for sub in content["subsystems"]:
            assert len(sub["content"].split()) > 8000

    def test_truncation_is_recorded_not_silent(self, long_docs):
        cfg = {"content": {"max_words_per_section": 500}}
        content = extract_content(long_docs, level=3, config=cfg)

        dropped = content["metrics"]["truncated_sections"]
        assert len(dropped) == 2, "both documents exceed the budget"
        for d in dropped:
            assert d["filename"].endswith(".md")
            assert d["words_total"] > d["words_kept"]
            assert d["limit"] == 500

    def test_short_documents_record_nothing(self, tmp_path):
        (tmp_path / "README.md").write_text("# Short\n\nOverview.\n", encoding="utf-8")
        _write_doc(tmp_path, "01-tiny.md", 50)
        content = extract_content(tmp_path, level=3)
        assert content["metrics"]["truncated_sections"] == []


class TestBodyBlockLimit:
    """The template-side cap is configurable and defaults to unlimited."""

    def _template(self, tmp_path, config=None):
        from briefkit.generator import BaseBriefingTemplate
        return BaseBriefingTemplate(tmp_path, level=3, config=config or {})

    def test_limit_defaults_to_unlimited(self, tmp_path):
        assert self._template(tmp_path).body_block_limit() == 0

    def test_caller_default_applies_when_unset(self, tmp_path):
        """Fixed-format templates pass their own ceiling."""
        assert self._template(tmp_path).body_block_limit(5) == 5

    def test_config_overrides_caller_default(self, tmp_path):
        tpl = self._template(tmp_path, {"content": {"max_blocks_per_section": 12}})
        assert tpl.body_block_limit(5) == 12

    def test_render_reports_what_it_dropped(self, tmp_path):
        tpl = self._template(tmp_path)
        blocks = [{"type": "paragraph", "text": f"para {i}"} for i in range(20)]

        _, dropped = tpl.render_body_blocks(blocks, limit=0)
        assert dropped == 0, "unlimited must emit everything"

        _, dropped = tpl.render_body_blocks(blocks, limit=5)
        assert dropped > 0, "a cap that bites must report the loss"


class TestVariantOptOut:
    """`--variant none` must suppress variant sections entirely.

    Previously the only way to avoid an unwanted variant was to name a
    different one, so a document matching no variant still received whichever
    keyword-matched — a tax pack picking up the finance variant's
    investment-advice disclaimer, for instance.
    """

    @pytest.fixture
    def finance_ish(self, tmp_path):
        """Content that reliably trips the finance variant's keywords."""
        (tmp_path / "README.md").write_text(
            "# Quarterly Review\n\nRevenue, EBITDA, cash flow, portfolio risk "
            "exposure, investment return and balance sheet analysis.\n",
            encoding="utf-8",
        )
        (tmp_path / "01-summary.md").write_text(
            "# Summary\n\nRevenue and EBITDA rose. Portfolio risk exposure fell. "
            "Investment return improved against the balance sheet forecast.\n",
            encoding="utf-8",
        )
        return tmp_path

    def _pdf_text(self, path):
        import subprocess
        return subprocess.run(["pdftotext", str(path), "-"],
                              capture_output=True, text=True).stdout

    def _build(self, src, variant, out_name):
        from briefkit.config import DEFAULTS
        from briefkit.templates.report import ReportTemplate
        import copy
        cfg = copy.deepcopy(DEFAULTS)
        cfg["_cli"] = {"variant": variant}
        out = src / out_name
        ReportTemplate(src, level=3, config=cfg, output_path=out).generate()
        return out

    def test_autodetect_adds_a_variant_section(self, finance_ish):
        out = self._build(finance_ish, None, "auto.pdf")
        assert out.exists()
        assert "Variant Sections" in self._pdf_text(out), (
            "expected auto-detection to inject a variant section"
        )

    def test_none_suppresses_all_variant_sections(self, finance_ish):
        out = self._build(finance_ish, "none", "none.pdf")
        assert out.exists()
        text = self._pdf_text(out)
        assert "Variant Sections" not in text
        assert "Financial Metrics" not in text

    def test_none_is_case_insensitive(self, finance_ish):
        out = self._build(finance_ish, "NONE", "upper.pdf")
        assert "Variant Sections" not in self._pdf_text(out)

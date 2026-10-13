"""Rendering and configuration fixes that each had a reproducible failure."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from pypdf import PdfReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import CondPageBreak, PageBreak, Paragraph, Spacer

from briefkit.config import DEFAULTS, load_config
from briefkit.styles import _safe_para, _safe_text
from briefkit.templates import get_template


def _set(
    tmp_path: Path, body: str, readme: str = "# Set\n\nAn overview paragraph that is long enough to be picked up.\n"
) -> Path:
    root = tmp_path / "project"
    docs = root / "docs" / "set"
    docs.mkdir(parents=True)
    (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n", encoding="utf-8")
    (docs / "README.md").write_text(readme, encoding="utf-8")
    (docs / "01-body.md").write_text(body, encoding="utf-8")
    return docs


def _build(docs: Path, template: str = "briefing") -> Path:
    cfg = copy.deepcopy(DEFAULTS)
    cfg["doc_ids"]["enabled"] = False
    out = docs.parent.parent / f"{template}.pdf"
    get_template(template)(docs, level=3, config=cfg, output_path=out).generate()
    return out


def _text(pdf: Path) -> str:
    return "\n".join((p.extract_text() or "") for p in PdfReader(str(pdf)).pages)


class TestSafeText:
    def test_br_is_not_counted_as_an_open_b(self):
        out = _safe_text("line one<br/>line two")
        assert out.count("</b>") == 0
        Paragraph(out, ParagraphStyle("s"))

    def test_long_words_are_left_to_reportlab_no_zero_width_space(self):
        out = _safe_text("x" * 300)
        assert "&#8203;" not in out and "​" not in out

    def test_fallback_keeps_entities_of_already_escaped_text(self):
        # A mis-nested tag forces the fallback; the ampersand must stay single.
        para = _safe_para("R&amp;D <b><i>mis</b></i>", ParagraphStyle("s"), already_escaped=True)
        assert "&amp;amp;" not in para.text and "R&amp;D" in para.text


class TestStoryPostProcessing:
    def test_hard_page_break_survives_next_to_a_conditional_one(self):
        from briefkit.generator import BaseBriefingTemplate

        tpl = BaseBriefingTemplate.__new__(BaseBriefingTemplate)
        tpl.config = {}
        story = [
            Paragraph("a", ParagraphStyle("s")),
            CondPageBreak(100),
            Spacer(1, 4),
            PageBreak(),
            Paragraph("b", ParagraphStyle("s")),
        ]
        out = tpl._collapse_empty_page_runs(story)
        breaks = [f for f in out if isinstance(f, (PageBreak, CondPageBreak))]
        assert len(breaks) == 1 and isinstance(breaks[0], PageBreak)

    def test_blockquote_longer_than_a_page_builds(self, tmp_path):
        quote = "> " + ("A very long quotation that goes on and on across the page. " * 120)
        docs = _set(tmp_path, f"# Chapter\n\n{quote}\n\nAfter the quote.\n")
        pdf = _build(docs, "minimal")
        text = _text(pdf)
        assert "After the quote" in text and "goes on and on" in text


class TestConfig:
    def test_empty_section_means_defaults(self, tmp_path):
        (tmp_path / "briefkit.yml").write_text("brand:\nproject:\n  org: X\n", encoding="utf-8")
        cfg = load_config(tmp_path / "briefkit.yml")
        assert cfg["brand"]["preset"] == "navy" and cfg["brand"]["org"] == "X"

    def test_unquoted_hex_colour_is_a_clear_error(self, tmp_path):
        (tmp_path / "briefkit.yml").write_text("brand:\n  primary: 123456\n", encoding="utf-8")
        with pytest.raises(ValueError, match="quote it"):
            load_config(tmp_path / "briefkit.yml")

    def test_brand_text_wins_over_project_text(self, tmp_path):
        (tmp_path / "briefkit.yml").write_text("project:\n  org: P\nbrand:\n  org: B\n", encoding="utf-8")
        cfg = load_config(tmp_path / "briefkit.yml")
        assert cfg["brand"]["org"] == "B"

    def test_copyright_has_no_trailing_space_without_an_org(self, tmp_path):
        (tmp_path / "briefkit.yml").write_text("project:\n  name: x\n", encoding="utf-8")
        cfg = load_config(tmp_path / "briefkit.yml")
        assert cfg["project"]["copyright"] == cfg["project"]["copyright"].strip()
        assert cfg["brand"]["copyright"] == cfg["project"]["copyright"]

    def test_relative_logo_is_resolved_against_the_config_file(self, tmp_path):
        from PIL import Image

        Image.new("RGB", (8, 8)).save(tmp_path / "logo.png")
        (tmp_path / "briefkit.yml").write_text("brand:\n  logo: logo.png\n", encoding="utf-8")
        cfg = load_config(tmp_path / "briefkit.yml")
        assert cfg["brand"]["logo"] == str(tmp_path / "logo.png")

    def test_missing_logo_in_config_is_an_error(self, tmp_path):
        (tmp_path / "briefkit.yml").write_text("brand:\n  logo: nope.png\n", encoding="utf-8")
        with pytest.raises(ValueError, match="not found"):
            load_config(tmp_path / "briefkit.yml")

    def test_svg_logo_is_rejected(self, tmp_path):
        (tmp_path / "logo.svg").write_text("<svg/>")
        (tmp_path / "briefkit.yml").write_text("brand:\n  logo: logo.svg\n", encoding="utf-8")
        with pytest.raises(ValueError, match="brand.logo must be one of"):
            load_config(tmp_path / "briefkit.yml")

    def test_metadata_title_beats_the_readme_heading(self, basic_fixture, tmp_path):
        cfg = copy.deepcopy(DEFAULTS)
        cfg["doc_ids"]["enabled"] = False
        cfg["metadata"] = {"title": "Configured Title", "subject": "Configured Subject"}
        out = tmp_path / "m.pdf"
        get_template("briefing")(basic_fixture, level=3, config=cfg, output_path=out).generate()
        meta = PdfReader(str(out)).metadata
        assert meta.title == "Configured Title"

    def test_pdf_title_is_the_document_title_for_overriding_templates(self, basic_fixture, tmp_path):
        cfg = copy.deepcopy(DEFAULTS)
        cfg["doc_ids"]["enabled"] = False
        out = tmp_path / "m.pdf"
        get_template("minimal")(basic_fixture, level=3, config=cfg, output_path=out).generate()
        assert PdfReader(str(out)).metadata.title not in ("Briefing", "", None)

    def test_variants_auto_detect_can_be_switched_off(self, tmp_path):
        body = (
            "# Summary\n\nRevenue and EBITDA rose. Portfolio risk exposure fell. "
            "Investment return improved against the balance sheet forecast.\n"
        )
        docs = _set(
            tmp_path,
            body,
            "# Quarterly Review\n\nRevenue, EBITDA, cash flow, portfolio risk exposure, investment return and balance sheet analysis.\n",
        )
        cfg = copy.deepcopy(DEFAULTS)
        cfg["doc_ids"]["enabled"] = False
        cfg["variants"]["auto_detect"] = False
        out = docs.parent.parent / "nv.pdf"
        get_template("report")(docs, level=3, config=cfg, output_path=out).generate()
        assert "Variant Sections" not in _text(out)


class TestRegistryLock:
    def test_concurrent_writers_issue_unique_ids(self, tmp_path):
        import subprocess
        import sys

        root = tmp_path / "project"
        root.mkdir()
        (root / "briefkit.yml").touch()
        targets = [root / "docs" / f"set-{i:02d}" for i in range(12)]
        for t in targets:
            t.mkdir(parents=True)
        script = (
            "import sys, json\n"
            "from pathlib import Path\n"
            "from briefkit.doc_ids import get_or_assign_doc_id\n"
            "from briefkit.config import DEFAULTS\n"
            "import copy\n"
            "cfg = copy.deepcopy(DEFAULTS)\n"
            "print(json.dumps([get_or_assign_doc_id(Path(p), 3, Path(p).name, config=cfg) for p in sys.argv[1:]]))\n"
        )
        (tmp_path / "w.py").write_text(script)
        half = len(targets) // 2
        procs = [
            subprocess.Popen(
                [sys.executable, str(tmp_path / "w.py"), *map(str, group)],
                cwd=root,
                stdout=subprocess.PIPE,
                text=True,
            )
            for group in (targets[:half], targets[half:], targets[:half], targets[half:])
        ]
        outputs = [p.communicate()[0] for p in procs]
        assert all(p.returncode == 0 for p in procs)
        import json as _json

        ids_by_target: dict[str, set[str]] = {}
        for out, group in zip(outputs, (targets[:half], targets[half:], targets[:half], targets[half:])):
            for target, doc_id in zip(group, _json.loads(out)):
                ids_by_target.setdefault(str(target), set()).add(doc_id)
        assert all(len(ids) == 1 for ids in ids_by_target.values()), "a target must keep one ID across processes"
        all_ids = [next(iter(ids)) for ids in ids_by_target.values()]
        assert len(all_ids) == len(set(all_ids)), "every target must get a distinct ID"
        assert not list((root / ".briefkit").glob("*.lock"))

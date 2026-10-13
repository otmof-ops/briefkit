# SPDX-FileCopyrightText: 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)
# SPDX-License-Identifier: BSD-3-Clause
"""Trust boundaries: untrusted Markdown and configuration cannot steer the build."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Flowable, Paragraph

from briefkit.config import DEFAULTS
from briefkit.extractor import _strip_inline, parse_markdown
from briefkit.generator import BriefkitDocTemplate
from briefkit.styles import _safe_text, esc, safe_href
from briefkit.templates import get_template


def _write_set(root: Path, readme: str, body: str) -> Path:
    (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n", encoding="utf-8")
    docs = root / "docs" / "set"
    docs.mkdir(parents=True)
    (docs / "README.md").write_text(readme, encoding="utf-8")
    (docs / "01-body.md").write_text(body, encoding="utf-8")
    return docs


def _build(docs: Path, template: str = "briefing") -> Path:
    cfg = copy.deepcopy(DEFAULTS)
    cfg["doc_ids"]["enabled"] = False
    out = docs.parent.parent / f"{template}.pdf"
    get_template(template)(docs, level=3, config=cfg, output_path=out).generate()
    return out


def _uris(pdf: Path) -> list[str]:
    found = []
    for page in PdfReader(str(pdf)).pages:
        for annot in page.get("/Annots") or []:
            obj = annot.get_object()
            action = obj.get("/A")
            if action is not None and "/URI" in action:
                found.append(str(action["/URI"]))
    return found


def _text(pdf: Path) -> str:
    return "\n".join((page.extract_text() or "") for page in PdfReader(str(pdf)).pages)


class TestLinkSchemes:
    @pytest.mark.parametrize(
        "url",
        [
            "javascript:alert(1)",
            "file:///etc/passwd",
            "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
            "\\\\attacker\\share\\x.exe",
            "smb://attacker/share/x",
            "ms-msdt:/id%20PCWDiagnostic",
            "cmd:calc",
            "other-doc.md",
            "//evil.example/x",
        ],
    )
    def test_disallowed_targets_are_not_clickable(self, url):
        assert safe_href(url) is None
        html = _strip_inline(f"See [the label]({url}) here.")
        assert "<link" not in html
        assert "the label" in html

    @pytest.mark.parametrize(
        "url", ["https://example.org/a?b=1&c=2", "http://example.org", "mailto:a@example.org", "#installation"]
    )
    def test_allowed_targets_become_links(self, url):
        assert safe_href(url) == url
        html = _strip_inline(f"See [the label]({url}) here.")
        assert "<link href=" in html and "the label</link>" in html

    def test_only_allowlisted_schemes_reach_the_pdf(self, tmp_path):
        body = "\n".join(
            [
                "# Links",
                "",
                "[js](javascript:alert(1)) [file](file:///etc/passwd) [smb](smb://x/y) [msdt](ms-msdt:/id)",
                "[ok](https://example.org/ok) [mail](mailto:a@example.org) [anchor](#top)",
            ]
        )
        docs = _write_set(
            tmp_path, "# Link Set\n\nA document set with many links in it, more than eighty characters long.\n", body
        )
        pdf = _build(docs, "minimal")
        uris = _uris(pdf)
        assert sorted(uris) == ["https://example.org/ok", "mailto:a@example.org"]

    def test_anchor_links_do_not_abort_the_build(self, tmp_path):
        docs = _write_set(
            tmp_path,
            "# Anchors\n\nA document set whose body links to a section with a hash anchor, as handwritten TOCs do.\n",
            "# Chapter\n\nSee [the section](#section-1) below.\n\n## Section 1\n\nText.\n",
        )
        pdf = _build(docs, "minimal")
        assert pdf.stat().st_size > 1000
        assert "the section" in _text(pdf)
        # the anchor is a real internal link now, resolved to the heading's page
        dests = [a.get_object().get("/Dest") for p in PdfReader(str(pdf)).pages for a in (p.get("/Annots") or [])]
        assert any(d is not None for d in dests)

    def test_parenthesised_urls_survive(self):
        html = _strip_inline("[w](https://en.wikipedia.org/wiki/Foo_(bar)) tail")
        assert 'href="https://en.wikipedia.org/wiki/Foo_(bar)"' in html
        assert html.endswith("</link> tail")

    def test_safe_text_revalidates_links_on_both_paths(self):
        pre = '<link href="javascript:x">a</link> <link href="https://e.org/?x=1&amp;y=2">b</link>'
        out = _safe_text(pre, already_escaped=True)
        assert "javascript" not in out and 'href="https://e.org/?x=1&amp;y=2"' in out and "a </link>" not in out
        raw = 'see <link href="file:///etc/passwd">leak</link>'
        assert "<link" not in _safe_text(raw) and "leak" in _safe_text(raw)


class TestMarkupEscaping:
    def test_esc_neutralises_every_tag(self):
        assert esc('<img src="http://x/y"/> & "q"') == "&lt;img src=&quot;http://x/y&quot;/&gt; &amp; &quot;q&quot;"

    def test_long_inline_code_keeps_its_tags(self):
        token = "x" * 70
        out = _safe_text(f'<font name="Courier">{token}</font>', already_escaped=True)
        assert out.endswith("</font>") and out.startswith('<font name="Courier">')
        Paragraph(out, ParagraphStyle("t"))  # must parse

    def test_long_href_is_not_broken(self):
        url = "https://example.org/" + "a" * 80
        out = _safe_text(f'<link href="{url}">label</link>', already_escaped=True)
        assert f'href="{url}"' in out

    def test_readme_title_markup_is_printed_not_fetched(self, tmp_path, monkeypatch):
        import reportlab.lib.utils as rl_utils

        def _no_network(*args, **kwargs):
            raise AssertionError("ReportLab tried to fetch a URL during the build")

        monkeypatch.setattr(rl_utils, "rlUrlRead", _no_network)
        readme = (
            '# <img src="http://127.0.0.1:9/beacon.png" width="10" height="10"/> Vec<T> & AT&T Release <b>notes\n\n'
            "An overview paragraph that is comfortably longer than eighty characters so it is picked up.\n"
        )
        docs = _write_set(tmp_path, readme, "# Body\n\nSome body text for the briefing.\n")
        pdf = _build(docs, "briefing")
        text = _text(pdf)
        assert "Vec<T>" in text
        assert "AT&T" in text
        assert "<img" in text
        assert "&amp;" not in text and "&lt;" not in text

    def test_subsystem_names_with_ampersands_are_not_double_escaped(self, tmp_path):
        docs = _write_set(
            tmp_path,
            "# R&D Set\n\nA documentation set about research and development spending plans and the like.\n",
            "# R&D Pipeline\n\n> Spend on R&D < 5% of revenue & rising.\n\nBody text about the R&D pipeline.\n",
        )
        (docs / "01-body.md").rename(docs / "01-r&d-pipeline.md")
        pdf = _build(docs, "briefing")
        text = _text(pdf)
        assert "&amp;" not in text and "&lt;" not in text
        assert "R&D" in text


class _Exploding(Flowable):
    def wrap(self, availWidth, availHeight):
        raise RuntimeError("layout failed on purpose")


class TestAtomicOutput:
    def test_failed_build_keeps_the_previous_pdf_and_no_part_file(self, tmp_path):
        out = tmp_path / "doc.pdf"
        BriefkitDocTemplate(str(out)).build([Paragraph("good", ParagraphStyle("s"))])
        good = out.read_bytes()
        assert good.startswith(b"%PDF")

        with pytest.raises(RuntimeError):
            BriefkitDocTemplate(str(out)).build([_Exploding()])

        assert out.read_bytes() == good, "a failed build must not truncate the previous output"
        assert not list(tmp_path.glob(".*.part"))

    def test_successful_build_replaces_atomically(self, tmp_path):
        out = tmp_path / "doc.pdf"
        out.write_bytes(b"old")
        BriefkitDocTemplate(str(out)).build([Paragraph("new", ParagraphStyle("s"))])
        assert out.read_bytes().startswith(b"%PDF")
        assert not list(tmp_path.glob(".*.part"))

    def test_metadata_lang_and_producer_are_native(self, tmp_path, basic_fixture):
        cfg = copy.deepcopy(DEFAULTS)
        cfg["doc_ids"]["enabled"] = False
        cfg["metadata"] = {"lang": "en-AU", "producer": "briefkit-tests", "author": "QA"}
        out = tmp_path / "meta.pdf"
        get_template("minimal")(basic_fixture, level=3, config=cfg, output_path=out).generate()
        reader = PdfReader(str(out))
        assert reader.metadata.producer == "briefkit-tests"
        assert reader.metadata.author == "QA"
        assert str(reader.trailer["/Root"].get("/Lang")) == "en-AU"


class TestRegistryContainment:
    def test_absolute_registry_outside_the_project_is_refused(self, tmp_path):
        from briefkit.doc_ids import get_or_assign_doc_id

        root = tmp_path / "project"
        target = root / "docs" / "a"
        target.mkdir(parents=True)
        (root / "briefkit.yml").touch()
        outside = tmp_path / "elsewhere" / "registry.json"
        cfg = {"doc_ids": {"enabled": True, "registry_path": str(outside)}, "output": {"filename": "x.pdf"}}
        with pytest.raises(ValueError, match="inside the project root"):
            get_or_assign_doc_id(target, 3, "A", config=cfg)
        assert not outside.exists()

    def test_relative_registry_escapes_are_refused(self, tmp_path):
        from briefkit.doc_ids import get_or_assign_doc_id

        root = tmp_path / "project"
        target = root / "docs" / "a"
        target.mkdir(parents=True)
        (root / "briefkit.yml").touch()
        cfg = {"doc_ids": {"enabled": True, "registry_path": "../../escape.json"}, "output": {"filename": "x.pdf"}}
        with pytest.raises(ValueError, match="inside the project root"):
            get_or_assign_doc_id(target, 3, "A", config=cfg)

    def test_registry_is_anchored_at_the_targets_project(self, tmp_path, monkeypatch):
        from briefkit.doc_ids import get_or_assign_doc_id

        root = tmp_path / "project"
        target = root / "docs" / "a"
        target.mkdir(parents=True)
        (root / "briefkit.yml").touch()
        elsewhere = tmp_path / "cwd"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)
        cfg = {"doc_ids": {"enabled": True}, "output": {"filename": "x.pdf"}}
        doc_id = get_or_assign_doc_id(target, 3, "A", config=cfg)
        assert doc_id
        assert (root / ".briefkit" / "registry.json").exists()
        assert not (elsewhere / ".briefkit").exists()

    def test_corrupt_registry_is_an_error_not_a_reset(self, tmp_path):
        from briefkit.doc_ids import load_registry

        reg = tmp_path / "registry.json"
        reg.write_text("{not json", encoding="utf-8")
        with pytest.raises(ValueError, match="not valid JSON"):
            load_registry(reg)
        assert reg.read_text() == "{not json"


class TestEntryPoints:
    def test_module_entry_point_propagates_the_exit_code(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "briefkit", "generate", str(tmp_path / "does-not-exist")],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "not a directory" in result.stderr

    def test_selftest_passes_and_leaves_no_trace(self, tmp_path, monkeypatch, capsys):
        from briefkit.cli import main

        monkeypatch.chdir(tmp_path)
        rc = main(["selftest", "--json"])
        report = json.loads(capsys.readouterr().out)
        assert rc == 0 and report["passed"] is True
        assert {c["name"] for c in report["checks"]} >= {"generate", "pdf written", "pages", "content"}
        assert list(tmp_path.iterdir()) == [], "selftest must write nothing into the working directory"

    def test_parse_markdown_is_unaffected_by_nul_sentinel_lookalikes(self):
        blocks = parse_markdown("Text with \x00\x01CODE_OPEN\x000\x00\x01CODE_CLOSE\x00 inside.")
        assert blocks and blocks[0]["type"] == "paragraph"
        Paragraph(blocks[0]["text"], ParagraphStyle("s"))

"""PDF navigation: a document outline, a clickable table of contents, resolvable #anchors."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from pypdf import PdfReader

from briefkit.config import DEFAULTS
from briefkit.styles import safe_href, slugify
from briefkit.templates import get_template


def _build(name: str, source: Path, out: Path) -> PdfReader:
    cfg = copy.deepcopy(DEFAULTS)
    cfg["doc_ids"]["enabled"] = False
    get_template(name)(source, level=3, config=cfg, output_path=out).generate()
    return PdfReader(str(out))


def _outline_titles(reader: PdfReader) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []

    def walk(items, depth):
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
            else:
                out.append((depth, item.title))

    walk(reader.outline, 0)
    return out


def _internal_links(reader: PdfReader) -> list[tuple[int, int]]:
    """(source page, destination page) for every internal link annotation."""
    links = []
    for i, page in enumerate(reader.pages):
        for annot in page.get("/Annots") or []:
            obj = annot.get_object()
            dest = obj.get("/Dest")
            if dest is None:
                continue
            target = dest[0] if isinstance(dest, list) else dest
            for j, candidate in enumerate(reader.pages):
                if (
                    candidate.indirect_reference == target.indirect_reference
                    if hasattr(target, "indirect_reference")
                    else False
                ):
                    links.append((i, j))
                    break
            else:
                page_number = reader.get_destination_page_number(dest) if not isinstance(dest, list) else None
                if page_number is not None:
                    links.append((i, page_number))
    return links


class TestSlugs:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Installation", "installation"),
            ("3.1 Installation &amp; Setup", "3-1-installation-setup"),
            ("<b>Bold</b> heading!", "bold-heading"),
            ("   ", "section"),
        ],
    )
    def test_slugify(self, text, expected):
        assert slugify(text) == expected

    def test_slugify_can_drop_numbering(self):
        assert slugify("3.1 Installation", drop_numbering=True) == "installation"
        assert slugify("7. Practical Applications", drop_numbering=True) == "practical-applications"

    def test_fragment_links_are_normalised_anchors(self):
        assert safe_href("#My Section") == "#my-section"
        assert safe_href("#installation") == "#installation"


class TestOutline:
    @pytest.mark.parametrize("name", ["briefing", "report", "book", "minimal", "manual", "academic"])
    def test_outline_lists_the_headings(self, name, full_fixture, tmp_path):
        reader = _build(name, full_fixture, tmp_path / f"{name}.pdf")
        titles = [t for _, t in _outline_titles(reader)]
        assert len(titles) >= 3, f"{name}: outline has {titles}"
        joined = " | ".join(titles)
        assert "Search Strategies" in joined or "Benchmarks" in joined, f"{name}: {titles}"
        assert str(reader.trailer["/Root"].get("/PageMode")) == "/UseOutlines"

    def test_outline_is_nested(self, full_fixture, tmp_path):
        reader = _build("book", full_fixture, tmp_path / "book.pdf")
        depths = {depth for depth, _ in _outline_titles(reader)}
        assert depths >= {0, 1}, "chapter headings and their sub-headings must nest"

    def test_outline_entries_point_at_increasing_pages(self, full_fixture, tmp_path):
        reader = _build("briefing", full_fixture, tmp_path / "b.pdf")
        pages = []
        for item in reader.outline:
            if not isinstance(item, list):
                pages.append(reader.get_destination_page_number(item))
        assert pages == sorted(pages)
        assert pages[-1] > 1

    def test_display_doc_title_is_set(self, basic_fixture, tmp_path):
        reader = _build("minimal", basic_fixture, tmp_path / "m.pdf")
        prefs = reader.trailer["/Root"].get("/ViewerPreferences")
        assert prefs is not None and bool(prefs.get("/DisplayDocTitle")) is True


class TestClickableToc:
    @pytest.mark.parametrize(
        "name", ["briefing", "report", "book", "minimal", "academic", "manual", "policy", "proposal"]
    )
    def test_toc_entries_are_internal_links_to_later_pages(self, name, full_fixture, tmp_path):
        reader = _build(name, full_fixture, tmp_path / f"{name}.pdf")
        links = _internal_links(reader)
        assert len(links) >= 3, f"{name}: expected TOC links, found {links}"
        assert any(dst > src for src, dst in links), f"{name}: TOC links must jump forward: {links}"

    def test_markdown_anchor_resolves_to_the_heading(self, tmp_path):
        root = tmp_path / "project"
        docs = root / "docs" / "set"
        docs.mkdir(parents=True)
        (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n")
        (docs / "README.md").write_text(
            "# Anchors\n\nAn overview paragraph long enough to be picked up by the extractor here.\n"
        )
        (docs / "01-body.md").write_text(
            "# Chapter\n\nSee [the appendix](#appendix-notes) at the end.\n\n"
            + "\n\n".join(f"Paragraph {i} of filler text that pushes the appendix to a later page." for i in range(90))
            + "\n\n## Appendix Notes\n\nHere.\n"
        )
        reader = _build("minimal", docs, tmp_path / "a.pdf")
        links = _internal_links(reader)
        assert links, "the markdown anchor must become an internal link"
        src, dst = links[-1] if len(links) == 1 else max(links, key=lambda sd: sd[1])
        assert dst > 0, "the anchor must resolve to the heading's page, not the fallback"

    def test_unknown_anchor_does_not_abort_and_falls_back_to_page_one(self, tmp_path):
        root = tmp_path / "project"
        docs = root / "docs" / "set"
        docs.mkdir(parents=True)
        (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n")
        (docs / "README.md").write_text(
            "# Anchors\n\nAn overview paragraph long enough to be picked up by the extractor here.\n"
        )
        (docs / "01-body.md").write_text("# Chapter\n\nSee [nowhere](#does-not-exist) for nothing.\n")
        reader = _build("minimal", docs, tmp_path / "u.pdf")
        links = _internal_links(reader)
        body_links = [(src, dst) for src, dst in links if src >= 1]
        assert body_links and all(dst == 0 for _, dst in body_links), links

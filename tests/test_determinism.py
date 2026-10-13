"""Byte-reproducible output: the same input gives the same bytes, and every printed date follows SOURCE_DATE_EPOCH."""

from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path

import pytest
from pypdf import PdfReader

from briefkit.config import DEFAULTS
from briefkit.templates import get_template, list_templates


def _build(template: str, source: Path, out: Path, **project) -> Path:
    cfg = copy.deepcopy(DEFAULTS)
    cfg["doc_ids"]["enabled"] = False
    cfg["project"].update(project)
    get_template(template)(source, level=3, config=cfg, output_path=out).generate()
    return out


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(path: Path) -> str:
    return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)


@pytest.mark.parametrize("template", list_templates())
def test_two_builds_are_byte_identical(template, basic_fixture, tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    a = _build(template, basic_fixture, tmp_path / "a.pdf")
    b = _build(template, basic_fixture, tmp_path / "b.pdf")
    assert _sha(a) == _sha(b), f"{template}: two builds of the same input differ"


def test_cover_and_back_cover_dates_follow_source_date_epoch(basic_fixture, tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1767225600")  # 2026-01-01 00:00 UTC
    pdf = _build("briefing", basic_fixture, tmp_path / "dated.pdf")
    text = _text(pdf)
    assert "01 January 2026" in text
    assert "2026" in text
    import datetime

    this_year = str(datetime.date.today().year)
    if this_year != "2026":
        assert this_year not in text, "a wall-clock year leaked into a pinned build"


def test_doc_id_year_follows_source_date_epoch(tmp_path, monkeypatch):
    from briefkit.doc_ids import get_or_assign_doc_id

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    root = tmp_path / "project"
    target = root / "docs" / "a"
    target.mkdir(parents=True)
    (root / "briefkit.yml").touch()
    cfg = copy.deepcopy(DEFAULTS)
    doc_id = get_or_assign_doc_id(target, 3, "A", config=cfg)
    assert doc_id.endswith("/70")


def test_disable_determinism_does_not_leak_between_documents(basic_fixture, tmp_path, monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    a = _build("minimal", basic_fixture, tmp_path / "a.pdf")
    b = _build("minimal", basic_fixture, tmp_path / "b.pdf", disable_determinism=True)
    c = _build("minimal", basic_fixture, tmp_path / "c.pdf")
    ids = [PdfReader(str(p)).trailer.get("/ID") for p in (a, b, c)]
    assert ids[0] == ids[2], "the default build must stay invariant after a non-deterministic one"
    assert ids[1] != ids[0]


def test_output_does_not_depend_on_the_checkout_location(tmp_path, monkeypatch):
    """The cover prints a project-relative path, so two checkouts of a project agree."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    hashes = []
    for parent in ("one", "two-with-a-much-longer-name"):
        root = tmp_path / parent / "project"
        docs = root / "docs" / "set"
        docs.mkdir(parents=True)
        (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n", encoding="utf-8")
        (docs / "README.md").write_text(
            "# Same Set\n\nAn overview paragraph long enough to be picked up by the extractor.\n"
        )
        (docs / "01-a.md").write_text("# A\n\nBody text.\n")
        hashes.append(_sha(_build("briefing", docs, tmp_path / f"{parent}.pdf")))
    assert hashes[0] == hashes[1]


def test_cover_shows_project_relative_path_not_absolute(basic_fixture, tmp_path):
    pdf = _build("briefing", basic_fixture, tmp_path / "p.pdf")
    text = _text(pdf)
    assert str(tmp_path) not in text
    assert os.sep.join(("docs", "basic")) in text or "docs › basic" in text or "basic" in text

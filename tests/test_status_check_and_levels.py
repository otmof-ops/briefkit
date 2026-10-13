"""``briefkit status --check`` for CI, and aggregate directories recognized by their contents."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from briefkit.cli import main
from briefkit.config import DEFAULTS
from briefkit.generator import detect_level


def _project(tmp_path: Path, *sets: str, readme: bool = True) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n", encoding="utf-8")
    for name in sets:
        directory = root / "docs" / "subject" / name
        directory.mkdir(parents=True)
        if readme:
            (directory / "README.md").write_text(
                f"# {name.title()}\n\nAn overview of {name} that is long enough to serve as the executive summary.\n",
                encoding="utf-8",
            )
        (directory / "01-one.md").write_text(f"# Chapter One\n\nBody text for {name}, chapter one.\n", encoding="utf-8")
        (directory / "02-two.md").write_text(f"# Chapter Two\n\nBody text for {name}, chapter two.\n", encoding="utf-8")
    return root


class TestStatusCheck:
    def test_exit_codes_follow_the_tree(self, tmp_path, monkeypatch, capsys):
        root = _project(tmp_path, "alpha", "beta")
        docs = root / "docs"
        monkeypatch.chdir(root)

        assert main(["status", str(docs), "--quiet"]) == 0, "without --check the exit code is always 0"
        assert main(["status", str(docs), "--check", "--quiet"]) == 1, "both PDFs are missing"

        assert main(["batch", str(docs), "--quiet"]) == 0
        assert main(["status", str(docs), "--check", "--quiet"]) == 0

        stale = docs / "subject" / "alpha" / "executive-briefing.pdf"
        old = time.time() - 1000
        os.utime(stale, (old, old))
        capsys.readouterr()
        assert main(["status", str(docs), "--check", "--json"]) == 1
        rows = json.loads(capsys.readouterr().out)
        assert {Path(r["path"]).name: r["status"] for r in rows} == {"alpha": "stale", "beta": "current"}

    def test_check_with_nothing_to_check(self, tmp_path, monkeypatch):
        root = tmp_path / "empty"
        root.mkdir()
        monkeypatch.chdir(root)
        assert main(["status", str(root), "--check", "--quiet"]) == 0


class TestAggregateLevels:
    def test_levels_are_read_from_the_tree(self, tmp_path):
        root = _project(tmp_path, "alpha", "beta")
        cfg = DEFAULTS
        assert detect_level(root / "docs" / "subject" / "alpha", root, cfg) == 3
        assert detect_level(root / "docs" / "subject", root, cfg) == 2, "children hold numbered docs: a subject"
        assert detect_level(root / "docs", root, cfg) == 1, "grandchildren hold numbered docs: a division"
        empty = root / "docs" / "subject" / "notes"
        empty.mkdir()
        assert detect_level(empty, root, cfg) == 3, "nothing in the tree: the depth rule decides"

    def test_depth_rule_still_applies_to_a_bare_root(self, tmp_path):
        root = tmp_path / "bare"
        root.mkdir()
        assert detect_level(root, root, DEFAULTS) == 1
        assert detect_level(root, None, DEFAULTS) == DEFAULTS["hierarchy"]["root_level"]

    @pytest.mark.parametrize("readme", [True, False], ids=["with-readme", "without-readme"])
    def test_subject_directory_builds_an_overview(self, tmp_path, monkeypatch, readme):
        pypdf = pytest.importorskip("pypdf")
        root = _project(tmp_path, "alpha", "beta", readme=readme)
        subject = root / "docs" / "subject"
        monkeypatch.chdir(root)

        assert main(["generate", str(subject), "--dry-run", "--quiet"]) == 0
        assert main(["generate", str(subject), "--quiet"]) == 0

        pdf = subject / "executive-briefing.pdf"
        assert pdf.exists()
        reader = pypdf.PdfReader(str(pdf))
        assert len(reader.pages) >= 1
        assert reader.metadata.title == "Subject"

"""Cross-references: extracted from relative links, rendered as a map, never read through symlinks."""

from __future__ import annotations

import copy
import os
from pathlib import Path

from pypdf import PdfReader

from briefkit.config import DEFAULTS
from briefkit.cross_refs import extract_cross_refs
from briefkit.templates import get_template


def _set(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    docs = root / "docs" / "alpha" / "this-set"
    docs.mkdir(parents=True)
    (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n", encoding="utf-8")
    (docs / "README.md").write_text(
        "# This Set\n\nAn overview paragraph that is long enough to be picked up by the extractor on its own.\n",
        encoding="utf-8",
    )
    (docs / "01-body.md").write_text(
        "# Body\n\nSee [the sibling set](../sibling-set/README.md) and the archive (../../beta/old-set/executive-briefing.pdf).\n"
        "Also [another](../sibling-set/01-x.md) link to the same set.\n",
        encoding="utf-8",
    )
    return docs


def test_relative_links_become_cross_references(tmp_path):
    docs = _set(tmp_path)
    refs, labels = extract_cross_refs(docs)
    assert refs == ["sibling-set", "beta/old-set"]
    assert labels["sibling-set"] == "the sibling set"
    assert labels["beta/old-set"] == "Old Set"


def test_cross_reference_map_is_rendered(tmp_path):
    docs = _set(tmp_path)
    cfg = copy.deepcopy(DEFAULTS)
    cfg["doc_ids"]["enabled"] = False
    out = tmp_path / "x.pdf"
    get_template("briefing")(docs, level=3, config=cfg, output_path=out).generate()
    text = "\n".join((p.extract_text() or "") for p in PdfReader(str(out)).pages)
    assert "Cross-Reference Map" in text
    assert "sibling" in text.lower()


def test_symlinked_markdown_is_not_scanned(tmp_path):
    docs = _set(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("[leak](../leaked-set/README.md)\n", encoding="utf-8")
    try:
        os.symlink(outside, docs / "02-link.md")
    except (OSError, NotImplementedError):
        return  # platforms without symlink support
    refs, _ = extract_cross_refs(docs)
    assert "leaked-set" not in refs

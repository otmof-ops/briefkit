"""Where a generated PDF goes: one resolver, validated, honoured by every command."""

from __future__ import annotations

import copy
import json

import pytest

from briefkit.config import DEFAULTS, load_config
from briefkit.output import resolve_output_path, validate_output_dir, validate_output_filename


def _cfg(**output):
    cfg = copy.deepcopy(DEFAULTS)
    cfg["output"].update(output)
    cfg["doc_ids"]["enabled"] = False
    return cfg


class TestFilenameValidation:
    @pytest.mark.parametrize(
        "bad",
        [
            "../x.pdf",
            "../../victim.txt",
            "/tmp/x.pdf",
            "a/b.pdf",
            "a\\b.pdf",
            "x.txt",
            "x\x00.pdf",
            "",
            ".",
            "..",
            None,
            42,
        ],
    )
    def test_rejects_anything_but_a_bare_pdf_name(self, bad):
        assert validate_output_filename(bad) is not None

    @pytest.mark.parametrize("good", ["executive-briefing.pdf", "Report.PDF", "a b.pdf", "r&d.pdf"])
    def test_accepts_bare_pdf_names(self, good):
        assert validate_output_filename(good) is None

    @pytest.mark.parametrize("bad", ["../out", "out/../../x", "a\x00b"])
    def test_output_dir_rejects_upward_walks(self, bad):
        assert validate_output_dir(bad) is not None

    @pytest.mark.parametrize("good", ["", None, "out", "build/pdfs", "/tmp/somewhere"])
    def test_output_dir_accepts_plain_paths(self, good):
        assert validate_output_dir(good) is None

    def test_load_config_refuses_a_traversal_filename(self, tmp_path):
        (tmp_path / "briefkit.yml").write_text('output:\n  filename: "../../victim.txt"\n', encoding="utf-8")
        with pytest.raises(ValueError, match="bare file name"):
            load_config(tmp_path / "briefkit.yml")

    def test_load_config_refuses_an_absolute_filename(self, tmp_path):
        (tmp_path / "briefkit.yml").write_text('output:\n  filename: "/tmp/x.pdf"\n', encoding="utf-8")
        with pytest.raises(ValueError, match="bare file name"):
            load_config(tmp_path / "briefkit.yml")


class TestResolver:
    def test_default_sits_next_to_the_sources(self, tmp_path):
        target = tmp_path / "docs" / "a"
        target.mkdir(parents=True)
        assert resolve_output_path(target, _cfg()) == (target / "executive-briefing.pdf").resolve()

    def test_output_dir_mirrors_the_project_tree(self, tmp_path):
        root = tmp_path / "project"
        target = root / "docs" / "a"
        target.mkdir(parents=True)
        (root / "briefkit.yml").touch()
        out = resolve_output_path(target, _cfg(output_dir="build"), project_root=root)
        assert out == (root / "build" / "docs" / "a" / "executive-briefing.pdf").resolve()

    def test_absolute_output_dir(self, tmp_path):
        root = tmp_path / "project"
        target = root / "docs" / "a"
        target.mkdir(parents=True)
        dest = tmp_path / "elsewhere"
        out = resolve_output_path(target, _cfg(output_dir=str(dest)), project_root=root)
        assert out == (dest / "docs" / "a" / "executive-briefing.pdf").resolve()

    def test_target_outside_the_project_root_uses_its_name(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        target = tmp_path / "other" / "set"
        target.mkdir(parents=True)
        out = resolve_output_path(target, _cfg(output_dir="build"), project_root=root)
        assert out == (root / "build" / "set" / "executive-briefing.pdf").resolve()

    def test_override_file(self, tmp_path):
        target = tmp_path / "docs"
        target.mkdir()
        out = resolve_output_path(target, _cfg(), override=tmp_path / "nested" / "x.pdf")
        assert out == (tmp_path / "nested" / "x.pdf").resolve()

    def test_override_directory_receives_the_configured_filename(self, tmp_path):
        target = tmp_path / "docs"
        target.mkdir()
        dest = tmp_path / "outdir"
        dest.mkdir()
        out = resolve_output_path(target, _cfg(filename="brief.pdf"), override=dest)
        assert out == (dest / "brief.pdf").resolve()

    def test_escaping_filename_is_refused_even_without_load_config(self, tmp_path):
        target = tmp_path / "docs"
        target.mkdir()
        with pytest.raises(ValueError):
            resolve_output_path(target, _cfg(filename="../x.pdf"))


class TestCommandsHonourTheResolver:
    def test_generate_writes_to_the_output_flag(self, basic_fixture, tmp_path):
        from briefkit.cli import main

        out = tmp_path / "deep" / "nested" / "basic.pdf"
        rc = main(["generate", str(basic_fixture), "--no-ids", "--quiet", "--output", str(out)])
        assert rc == 0
        assert out.exists() and out.stat().st_size > 0
        assert not (basic_fixture / "executive-briefing.pdf").exists(), "must not also write into the source dir"
        assert not list(out.parent.glob(".*.part")), "no temporary part file may remain"

    def test_generate_json_reports_the_real_output(self, basic_fixture, tmp_path, capsys):
        from briefkit.cli import main

        out = tmp_path / "r.pdf"
        rc = main(["generate", str(basic_fixture), "--no-ids", "--json", "--output", str(out)])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "generated"
        assert payload["output"] == str(out)

    def test_output_dir_from_config_is_honoured_by_generate_and_batch(self, basic_fixture, monkeypatch, capsys):
        from briefkit.cli import main

        root = basic_fixture.parent.parent  # the temporary project root with briefkit.yml
        (root / "briefkit.yml").write_text(
            "doc_ids:\n  enabled: false\noutput:\n  output_dir: build\n", encoding="utf-8"
        )
        monkeypatch.chdir(root)

        assert main(["generate", str(basic_fixture), "--quiet"]) == 0
        expected = root / "build" / "docs" / "basic" / "executive-briefing.pdf"
        assert expected.exists()
        assert not (basic_fixture / "executive-briefing.pdf").exists()

        assert main(["batch", str(root / "docs"), "--json"]) == 0
        stats = json.loads(capsys.readouterr().out)
        assert stats["total"] == 1
        assert stats["skipped"] == 1, "a current PDF under output_dir must be detected as current"

    def test_template_generate_uses_output_dir(self, basic_fixture, tmp_path):
        from briefkit.templates import get_template

        cfg = _cfg(output_dir=str(tmp_path / "pdfs"))
        result = get_template("minimal")(basic_fixture, config=cfg).generate()
        assert result.is_relative_to(tmp_path / "pdfs")
        assert result.exists()

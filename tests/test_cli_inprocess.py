# SPDX-FileCopyrightText: 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)
# SPDX-License-Identifier: BSD-3-Clause
"""The CLI, driven in-process through main(): every subcommand, its flags and exit codes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pypdf import PdfReader

from briefkit.cli import main


def _text(pdf: Path) -> str:
    return "\n".join((p.extract_text() or "") for p in PdfReader(str(pdf)).pages)


class TestGenerate:
    def test_not_a_directory_exits_1(self, tmp_path, capsys):
        assert main(["generate", str(tmp_path / "nope")]) == 1
        assert "not a directory" in capsys.readouterr().err

    def test_empty_directory_exits_2_with_fix_hints(self, empty_fixture, capsys):
        assert main(["generate", str(empty_fixture), "--no-ids"]) == 2
        err = capsys.readouterr().err
        assert "No content was extracted" in err and "numbered_doc_pattern" in err

    def test_dry_run_writes_nothing_and_json_is_clean(self, basic_fixture, capsys):
        out = basic_fixture / "executive-briefing.pdf"
        assert main(["generate", str(basic_fixture), "--dry-run", "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["extracted"]["subsystems"] == 2 and payload["empty"] is False
        assert not out.exists()
        assert not (basic_fixture.parent.parent / ".briefkit" / "registry.json").exists()

    def test_dry_run_quiet_prints_nothing(self, basic_fixture, capsys):
        assert main(["generate", str(basic_fixture), "--dry-run", "--quiet"]) == 0
        assert capsys.readouterr().out == ""

    def test_title_and_org_reach_the_pdf(self, basic_fixture, tmp_path):
        out = tmp_path / "t.pdf"
        rc = main(
            [
                "generate",
                str(basic_fixture),
                "--no-ids",
                "--quiet",
                "--output",
                str(out),
                "--title",
                "My Custom Title",
                "--org",
                "Acme Sons",
            ]
        )
        assert rc == 0
        text = _text(out)
        assert "My Custom Title" in text and "Acme Sons" in text
        meta = PdfReader(str(out)).metadata
        assert meta.title == "My Custom Title"
        assert meta.author == "Acme Sons"

    def test_project_org_from_config_reaches_the_pdf(self, basic_fixture, tmp_path, monkeypatch):
        root = basic_fixture.parent.parent
        (root / "briefkit.yml").write_text(
            "doc_ids:\n  enabled: false\nproject:\n  org: Config Org\n  tagline: Built to last\n", encoding="utf-8"
        )
        monkeypatch.chdir(root)
        out = tmp_path / "o.pdf"
        assert main(["generate", str(basic_fixture), "--quiet", "--output", str(out)]) == 0
        text = _text(out)
        assert "Config Org" in text and "Built to last" in text
        assert "© " in text and "Config Org" in text

    def test_logo_is_rendered_on_the_cover(self, basic_fixture, tmp_path):
        from PIL import Image

        logo = tmp_path / "logo.png"
        Image.new("RGB", (120, 60), (200, 30, 30)).save(logo)
        out = tmp_path / "l.pdf"
        assert (
            main(["generate", str(basic_fixture), "--no-ids", "--quiet", "--output", str(out), "--logo", str(logo)])
            == 0
        )
        page = PdfReader(str(out)).pages[0]
        assert len(list(page.images)) >= 1, "the configured logo must be placed on the cover"

    def test_missing_logo_warns_and_continues(self, basic_fixture, tmp_path, capsys):
        out = tmp_path / "l.pdf"
        rc = main(["generate", str(basic_fixture), "--no-ids", "--output", str(out), "--logo", str(tmp_path / "x.png")])
        assert rc == 0 and "Logo file not found" in capsys.readouterr().err

    def test_unknown_template_exits_1(self, basic_fixture, capsys):
        assert main(["generate", str(basic_fixture), "--no-ids", "-t", "nonexistent"]) == 1
        assert "Unknown template" in capsys.readouterr().err

    def test_variant_none_is_honoured(self, basic_fixture, tmp_path):
        out = tmp_path / "v.pdf"
        assert (
            main(["generate", str(basic_fixture), "--no-ids", "--quiet", "--output", str(out), "--variant", "none"])
            == 0
        )
        assert "Variant Sections" not in _text(out)


class TestBatchAndStatus:
    def test_batch_json_then_skip_current_then_stale(self, basic_fixture, capsys):
        docs_root = basic_fixture.parent
        assert main(["batch", str(docs_root), "--json"]) == 0
        first = json.loads(capsys.readouterr().out)
        assert first["total"] == 1 and first["generated"] == 1

        assert main(["batch", str(docs_root), "--json"]) == 0
        second = json.loads(capsys.readouterr().out)
        assert second["skipped"] == 1, "unchanged sources must be skipped"

        import os
        import time

        readme = basic_fixture / "README.md"
        os.utime(readme, (time.time() + 5, time.time() + 5))
        assert main(["status", str(docs_root), "--json"]) == 0
        rows = json.loads(capsys.readouterr().out)
        assert rows[0]["status"] == "stale", "a changed README must make the briefing stale"

    def test_batch_no_ids_writes_no_registry(self, basic_fixture, tmp_path, monkeypatch, capsys):
        root = basic_fixture.parent.parent
        (root / "briefkit.yml").write_text("doc_ids:\n  enabled: true\n", encoding="utf-8")
        monkeypatch.chdir(root)
        assert main(["batch", str(basic_fixture.parent), "--no-ids", "--quiet"]) == 0
        assert not (root / ".briefkit" / "registry.json").exists()

    def test_batch_output_flag_is_the_mirror_directory(self, basic_fixture, tmp_path, capsys):
        dest = tmp_path / "mirror"
        assert main(["batch", str(basic_fixture.parent), "--no-ids", "--json", "--output", str(dest)]) == 0
        stats = json.loads(capsys.readouterr().out)
        assert stats["generated"] == 1
        assert list(dest.rglob("*.pdf")), "PDFs must land under the --output directory"
        assert not (basic_fixture / "executive-briefing.pdf").exists()

    def test_batch_dry_run_reports_would_generate(self, basic_fixture, capsys):
        assert main(["batch", str(basic_fixture.parent), "--dry-run", "--no-ids"]) == 0
        out = capsys.readouterr().out
        assert "would be generated" in out
        assert not (basic_fixture / "executive-briefing.pdf").exists()

    def test_batch_error_names_the_exception_type(self, tmp_path, capsys, monkeypatch):
        root = tmp_path / "p"
        docs = root / "docs" / "bad"
        docs.mkdir(parents=True)
        (root / "briefkit.yml").write_text("doc_ids:\n  enabled: false\n")
        (docs / "01-a.md").write_text("# A\n\nText.\n")
        import briefkit.batch as batch_mod

        def _boom(*a, **k):
            raise RuntimeError("kaboom")

        monkeypatch.setattr(batch_mod, "get_template", _boom, raising=False)
        monkeypatch.setattr("briefkit.templates.get_template", _boom)
        assert main(["batch", str(root / "docs"), "--json"]) == 1
        stats = json.loads(capsys.readouterr().out)
        assert stats["failed"] == 1 and "RuntimeError: kaboom" in stats["results"][0]["message"]


class TestInit:
    def test_init_creates_config_and_refuses_to_overwrite(self, tmp_path, capsys):
        assert main(["init", str(tmp_path)]) == 0
        assert (tmp_path / "briefkit.yml").exists() and (tmp_path / ".briefkit").is_dir()
        assert main(["init", str(tmp_path)]) == 1
        assert "already exists" in capsys.readouterr().err
        assert main(["init", str(tmp_path), "--force"]) == 0

    def test_init_dry_run_writes_nothing(self, tmp_path, capsys):
        assert main(["init", str(tmp_path), "--dry-run"]) == 0
        assert "Would create" in capsys.readouterr().out
        assert not (tmp_path / "briefkit.yml").exists()

    def test_init_on_a_missing_directory_is_a_clean_error(self, tmp_path, capsys):
        assert main(["init", str(tmp_path / "does" / "not" / "exist")]) == 1
        assert "not an existing directory" in capsys.readouterr().err


class TestQuality:
    def test_quality_passes_on_briefkits_own_output(self, basic_fixture, tmp_path, capsys):
        out = tmp_path / "q.pdf"
        assert main(["generate", str(basic_fixture), "--no-ids", "--quiet", "--output", str(out)]) == 0
        assert main(["quality", str(out), "--json"]) == 0
        report = json.loads(capsys.readouterr().out)
        assert report["passed"] is True
        assert any(line.startswith("PASS: Text present") for line in report["checks"])

    def test_quality_strict_can_fail_a_small_pdf(self, basic_fixture, tmp_path, capsys):
        out = tmp_path / "q.pdf"
        assert main(["generate", str(basic_fixture), "--no-ids", "--quiet", "--output", str(out), "-t", "minimal"]) == 0
        rc = main(["quality", str(out), "--strict", "--level", "1", "--json"])
        report = json.loads(capsys.readouterr().out)
        assert rc == 1 and report["passed"] is False

    def test_quality_on_a_directory_and_on_a_missing_file(self, basic_fixture, tmp_path, capsys):
        assert main(["quality", str(tmp_path / "missing.pdf")]) == 1
        assert main(["quality", str(basic_fixture / "README.md")]) == 1
        assert "neither a directory nor a .pdf" in capsys.readouterr().err

    def test_quality_fails_a_file_that_is_not_a_pdf(self, tmp_path, capsys):
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf at all")
        assert main(["quality", str(bad), "--json"]) == 1
        report = json.loads(capsys.readouterr().out)
        assert any("Invalid PDF header" in line for line in report["checks"])


class TestListingCommands:
    def test_templates_quiet_lists_names_and_default_adds_descriptions(self, capsys):
        assert main(["templates", "--quiet"]) == 0
        names = capsys.readouterr().out.split()
        assert len(names) == 29 and "witness" in names
        assert main(["templates"]) == 0
        out = capsys.readouterr().out
        assert "briefing" in out and "Default executive briefing" in out
        assert main(["templates", "--json"]) == 0
        assert json.loads(capsys.readouterr().out)["deck"]

    def test_licenses_labels_source_available_as_use_restricted(self, capsys):
        assert main(["licenses"]) == 0
        out = capsys.readouterr().out
        assert "BUSL-1.1" in out and "[use-restricted]" in out
        assert "CC-BY-NC-4.0" in out and "[non-commercial]" in out

    def test_assign_ids_reports_honestly(self, basic_fixture, tmp_path, monkeypatch, capsys):
        root = basic_fixture.parent.parent
        (root / "briefkit.yml").write_text("doc_ids:\n  enabled: true\n", encoding="utf-8")
        monkeypatch.chdir(root)
        assert main(["assign-ids", str(root / "docs"), "--json"]) == 0
        before = json.loads(capsys.readouterr().out)
        assert before == {"checked": 0, "assigned": 0, "existing": 0, "dry_run": False}

        assert main(["generate", str(basic_fixture), "--quiet", "--no-ids"]) == 0
        assert main(["assign-ids", str(root / "docs"), "--dry-run", "--json"]) == 0
        dry = json.loads(capsys.readouterr().out)
        assert dry["checked"] == 1 and dry["assigned"] == 1 and dry["dry_run"] is True
        assert not (root / ".briefkit" / "registry.json").exists()

        assert main(["assign-ids", str(root / "docs"), "--json"]) == 0
        real = json.loads(capsys.readouterr().out)
        assert real["assigned"] == 1
        assert main(["assign-ids", str(root / "docs"), "--json"]) == 0
        again = json.loads(capsys.readouterr().out)
        assert again["assigned"] == 0 and again["existing"] == 1

    def test_config_warns_on_unknown_keys_without_failing(self, basic_fixture, tmp_path, monkeypatch, capsys):
        root = basic_fixture.parent.parent
        (root / "briefkit.yml").write_text("tempalte:\n  preset: report\nlayout:\n  pagesize: A4\n", encoding="utf-8")
        monkeypatch.chdir(root)
        assert main(["config", "--json"]) == 0
        captured = capsys.readouterr()
        assert "unknown setting 'tempalte'" in captured.err and "did you mean 'template'" in captured.err
        assert "layout.pagesize" in captured.err and "page_size" in captured.err
        assert json.loads(captured.out)["template"]["preset"] == "briefing"

    def test_no_subcommand_is_a_usage_error(self):
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 2

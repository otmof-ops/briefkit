"""
briefkit.cli
~~~~~~~~~~~~
Command-line interface for briefkit.  Uses argparse only — no click dependency.

Entry point: briefkit.cli:main (registered in pyproject.toml).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_config(args: argparse.Namespace) -> dict[str, Any]:
    """Load and return the resolved config, applying any CLI flag overrides."""
    from briefkit.config import load_config  # noqa: PLC0415

    config_path = getattr(args, "config", None)
    cfg = load_config(config_path)

    # CLI flag overrides
    if getattr(args, "preset", None):
        cfg["brand"]["preset"] = args.preset
        from briefkit.config import resolve_brand  # noqa: PLC0415
        cfg = resolve_brand(cfg)

    if getattr(args, "template", None):
        cfg["template"]["preset"] = args.template

    if getattr(args, "org", None):
        cfg["project"]["org"] = args.org

    if getattr(args, "logo", None):
        logo_path = Path(args.logo)
        _ALLOWED_LOGO_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".gif"}
        if not logo_path.exists():
            print(f"Warning: Logo file not found: {logo_path}", file=sys.stderr)
        elif logo_path.is_symlink():
            print(f"Warning: Logo path is a symlink, skipping: {logo_path}", file=sys.stderr)
        elif logo_path.suffix.lower() not in _ALLOWED_LOGO_EXTS:
            print(f"Warning: Logo has unsupported extension: {logo_path.suffix}", file=sys.stderr)
        else:
            cfg["brand"]["logo"] = str(logo_path.resolve())

    return cfg


def _output_path(args: argparse.Namespace, cfg: dict[str, Any], path: Path) -> Path:
    """Resolve the output PDF path from flags and config."""
    if getattr(args, "output", None):
        return Path(args.output).resolve()
    filename: str = cfg["output"]["filename"]
    output_dir: str = cfg["output"]["output_dir"]
    if output_dir:
        return Path(output_dir).resolve() / filename
    return path.resolve() / filename


def _open_file(path: Path) -> None:
    """Open *path* with the system default application."""
    if path.suffix.lower() != ".pdf":
        print(f"Warning: Refusing to open non-PDF file: {path}", file=sys.stderr)
        return
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", str(path)], check=True)
        elif system == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", str(path)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"Could not open file: {exc}", file=sys.stderr)


def _emit(data: Any, as_json: bool, quiet: bool = False) -> None:
    """Print *data* as JSON or human-readable text."""
    if quiet:
        return
    if as_json:
        print(json.dumps(data, indent=2, default=str))
    else:
        if isinstance(data, str):
            print(data)
        else:
            print(json.dumps(data, indent=2, default=str))


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def cmd_generate(args: argparse.Namespace) -> int:
    """Generate a briefing PDF for a single directory."""
    from briefkit.batch import _generate_one  # noqa: PLC0415

    path = Path(args.path).resolve()
    if not path.is_dir():
        print(f"Error: {path} is not a directory", file=sys.stderr)
        return 1

    cfg = _load_config(args)

    if getattr(args, "no_ids", False):
        cfg["doc_ids"]["enabled"] = False

    cfg.setdefault("_cli", {})["verbose"] = getattr(args, "verbose", False)

    if getattr(args, "variant", None):
        # Inject variant override into config so renderer picks it up
        cfg.setdefault("_cli", {})["variant"] = args.variant

    if getattr(args, "title", None):
        cfg["project"]["name"] = args.title

    output = _output_path(args, cfg, path)

    if not getattr(args, "quiet", False):
        print(f"Generating briefing for: {path}")
        print(f"Output: {output}")

    # License warning
    license_preset = cfg.get("license", {}).get("preset", "")
    if not license_preset or license_preset == "unlicensed":
        if not getattr(args, "quiet", False):
            print(
                "WARNING: No license configured. Output defaults to 'All Rights Reserved'.\n"
                "         Set license.preset in briefkit.yml or run 'briefkit licenses' for options.",
                file=sys.stderr,
            )

    if getattr(args, "dry_run", False):
        print("(dry-run — no file written)")
        return 0

    result = _generate_one(path, cfg, dry_run=False)

    if result["status"] == "error":
        print(f"Error: {result['message']}", file=sys.stderr)
        return 1

    if not getattr(args, "quiet", False):
        print(f"Done in {result['elapsed']:.1f}s")

    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    """Batch generate briefings for all eligible directories under root."""
    from briefkit.batch import batch_generate  # noqa: PLC0415

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 1

    cfg = _load_config(args)
    force = getattr(args, "force", False)
    dry_run = getattr(args, "dry_run", False)
    quiet = getattr(args, "quiet", False)
    as_json = getattr(args, "json", False)

    stats = batch_generate(root, cfg, force=force, dry_run=dry_run, quiet=quiet or as_json)

    if as_json:
        print(json.dumps(stats, indent=2, default=str))

    return 1 if stats["failed"] > 0 else 0


def cmd_init(args: argparse.Namespace) -> int:
    """Write a briefkit.yml with defaults in the current directory."""
    dest = Path(args.path).resolve() if getattr(args, "path", None) else Path.cwd()
    config_file = dest / "briefkit.yml"

    if config_file.exists() and not getattr(args, "force", False):
        print(f"Error: {config_file} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1

    template = textwrap.dedent("""\
        # briefkit configuration
        # All fields are optional — remove sections you don't need.

        project:
          name: ""          # auto-detected from directory name if blank
          org: ""
          tagline: ""
          url: ""
          copyright: "© {year} {org}"
          abn: ""

        brand:
          preset: navy      # navy | charcoal | ocean | forest | crimson
                            # slate | royal | sunset | mono | midnight
                            # emerald | corporate | arctic | terracotta
                            # ink | gothic | cyber | deep-research
                            # neon | neon-print | custom
          # Uncomment to override individual colors (preset: custom to disable preset):
          # primary: "#1B2A4A"
          # secondary: "#2E86AB"
          # accent: "#E8C547"
          # logo: "logo.png"

        license:
          preset: ""        # License for generated documents. Options:
                            #
                            # PERMISSIVE: MIT | Apache-2.0 | BSD-2-Clause | BSD-3-Clause
                            #             ISC | Zlib | BSL-1.0
                            # COPYLEFT:   GPL-2.0 | GPL-3.0 | LGPL-3.0 | AGPL-3.0
                            #             MPL-2.0 | EUPL-1.2
                            # SOURCE-AVAILABLE: BUSL-1.1 | Elastic-2.0 | SSPL-1.0
                            # CREATIVE COMMONS: CC0-1.0 | CC-BY-4.0 | CC-BY-SA-4.0
                            #                   CC-BY-NC-4.0 | CC-BY-NC-SA-4.0 | CC-BY-ND-4.0
                            # PUBLIC DOMAIN: Unlicense | CC0-1.0
                            # SPECIALIZED: OFL-1.1 | ODbL-1.0
                            # OTHER: proprietary | unlicensed
                            #
                            # Run 'briefkit licenses' for full list with descriptions.
                            # Leave blank or set to 'unlicensed' to skip (not recommended).

        doc_ids:
          enabled: true
          prefix: DOC
          type: BRF
          sequence_digits: 4
          registry_path: .briefkit/registry.json

        layout:
          page_size: A4     # A4 | A3 | Letter | Legal | Tabloid
          orientation: portrait

        output:
          filename: executive-briefing.pdf
          skip_current: true
    """)

    config_file.write_text(template, encoding="utf-8")
    print(f"Created {config_file}")

    # Also create .briefkit/ directory
    briefkit_dir = dest / ".briefkit"
    briefkit_dir.mkdir(exist_ok=True)
    (briefkit_dir / ".gitkeep").touch()

    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    """Generate and open the briefing PDF with the system viewer."""
    cfg = _load_config(args)
    path = Path(args.path).resolve()
    output = _output_path(args, cfg, path)

    rc = cmd_generate(args)
    if rc != 0:
        return rc

    if output.exists():
        _open_file(output)
    else:
        print(f"Output PDF not found: {output}", file=sys.stderr)
        return 1

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show whether briefings under a path are current, stale, or missing."""
    from briefkit.batch import _is_current, find_targets  # noqa: PLC0415
    from briefkit.batch import _output_path as batch_output

    root = Path(args.path).resolve()
    cfg = _load_config(args)
    as_json = getattr(args, "json", False)
    quiet = getattr(args, "quiet", False)

    targets = find_targets(root, cfg)

    rows: list[dict[str, str]] = []
    for directory in targets:
        output_pdf = batch_output(directory, cfg)
        if not output_pdf.exists():
            status = "missing"
        elif _is_current(directory, output_pdf, cfg):
            status = "current"
        else:
            status = "stale"

        rows.append({"path": str(directory), "output": str(output_pdf), "status": status})

    if as_json:
        print(json.dumps(rows, indent=2))
        return 0

    if not rows:
        if not quiet:
            print(f"No eligible directories found under {root}")
        return 0

    status_labels = {"current": "CURRENT", "stale": "STALE  ", "missing": "MISSING"}

    for row in rows:
        label = status_labels.get(row["status"], row["status"].upper())
        if not quiet:
            print(f"  {label}  {row['path']}")

    summary = {s: sum(1 for r in rows if r["status"] == s) for s in ("current", "stale", "missing")}
    if not quiet:
        print(
            f"\n  {len(rows)} total — "
            f"{summary['current']} current, "
            f"{summary['stale']} stale, "
            f"{summary['missing']} missing"
        )

    return 0


def cmd_assign_ids(args: argparse.Namespace) -> int:
    """Assign doc IDs to Markdown files without regenerating the PDF."""
    path = Path(args.path).resolve()
    if not path.is_dir():
        print(f"Error: {path} is not a directory", file=sys.stderr)
        return 1

    cfg = _load_config(args)
    quiet = getattr(args, "quiet", False)
    dry_run = getattr(args, "dry_run", False)

    if not quiet:
        print(f"Assigning doc IDs in: {path}")
        if dry_run:
            print("(dry-run — no files modified)")

    try:
        from briefkit import doc_ids as doc_ids_module  # noqa: PLC0415
        count = doc_ids_module.assign(path, cfg, dry_run=dry_run)
        if not quiet:
            print(f"Assigned IDs to {count} document(s)")
    except ImportError:
        if not quiet:
            print("(doc_ids module not yet available — stub run)")
        count = 0

    return 0


def cmd_quality(args: argparse.Namespace) -> int:
    """Run quality gates on an existing PDF briefing."""
    path = Path(args.path).resolve()
    cfg = _load_config(args)
    as_json = getattr(args, "json", False)
    quiet = getattr(args, "quiet", False)

    # Locate the PDF
    pdf_path = path if path.suffix.lower() == ".pdf" else path / cfg["output"]["filename"]
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    if not quiet:
        print(f"Running quality gates on: {pdf_path}")

    try:
        from briefkit.quality import run_quality_gates  # noqa: PLC0415
        passed, lines = run_quality_gates(pdf_path)
        report = {"pdf": str(pdf_path), "passed": passed, "checks": lines}
    except Exception as exc:
        report = {
            "pdf": str(pdf_path),
            "passed": False,
            "checks": [f"Error: {exc}"],
        }

    _emit(report, as_json=as_json, quiet=quiet)
    return 0 if report.get("passed", False) else 1


def cmd_selftest(args: argparse.Namespace) -> int:
    """Generate a briefing from the built-in test fixture and verify output."""
    import importlib.resources  # noqa: PLC0415

    quiet = getattr(args, "quiet", False)
    as_json = getattr(args, "json", False)

    # Locate the bundled fixture
    try:
        # Python 3.9+ traversable API
        pkg_files = importlib.resources.files("briefkit")
        fixture_dir = pkg_files / "fixtures" / "selftest"
    except (AttributeError, TypeError):
        fixture_dir = Path(__file__).parent / "fixtures" / "selftest"

    # Fall back to the tests/fixtures/basic directory in the repo
    repo_fixture = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "basic"

    if hasattr(fixture_dir, "is_dir") and not fixture_dir.is_dir():  # type: ignore[union-attr]
        if repo_fixture.is_dir():
            fixture_dir = repo_fixture
        else:
            if not quiet:
                print(
                    "Selftest fixture not found — creating a minimal in-memory fixture.",
                    file=sys.stderr,
                )
            return _selftest_inline(args, quiet=quiet, as_json=as_json)

    if not quiet:
        print(f"Running selftest from fixture: {fixture_dir}")

    args.path = str(fixture_dir)
    return cmd_generate(args)


def _selftest_inline(
    args: argparse.Namespace, quiet: bool = False, as_json: bool = False
) -> int:
    """Run a selftest using a temporary in-memory fixture."""
    import tempfile  # noqa: PLC0415

    fixture_md = textwrap.dedent("""\
        # 01 Introduction

        This is the selftest briefing generated by `briefkit selftest`.
        It verifies that the core generation pipeline is operational.

        ## Background

        BriefKit converts structured Markdown documents into polished PDF briefings.

        ## Scope

        This document covers the minimum viable selftest scenario.
    """)

    with tempfile.TemporaryDirectory(prefix="briefkit-selftest-") as tmpdir:
        doc = Path(tmpdir) / "01-introduction.md"
        doc.write_text(fixture_md, encoding="utf-8")

        if not quiet:
            print(f"Selftest fixture: {tmpdir}")

        original_path = getattr(args, "path", None)
        args.path = tmpdir

        rc = cmd_generate(args)

        args.path = original_path

    return rc


def cmd_config(args: argparse.Namespace) -> int:
    """Print the fully resolved configuration."""
    cfg = _load_config(args)
    as_json = getattr(args, "json", False)

    if as_json:
        print(json.dumps(cfg, indent=2, default=str))
    else:
        # Pretty-print as YAML if available, else JSON
        try:
            import yaml  # noqa: PLC0415
            print(yaml.dump(cfg, default_flow_style=False, allow_unicode=True))
        except ImportError:
            print(json.dumps(cfg, indent=2, default=str))

    return 0


def cmd_templates(args: argparse.Namespace) -> int:
    """List available template presets."""
    as_json = getattr(args, "json", False)
    quiet = getattr(args, "quiet", False)

    try:
        from briefkit import templates as templates_module  # noqa: PLC0415
        template_list = templates_module.list_templates()
    except ImportError:
        print("Error: briefkit.templates unavailable.", file=sys.stderr)
        return 1

    if as_json:
        print(json.dumps(template_list, indent=2))
        return 0

    if not quiet:
        print("Available templates:")
        for t in template_list:
            name = t["name"] if isinstance(t, dict) else t
            desc = t.get("description", "") if isinstance(t, dict) else ""
            if desc:
                print(f"  {name:<20} {desc}")
            else:
                print(f"  {name}")

    return 0


def cmd_presets(args: argparse.Namespace) -> int:
    """List all color presets with their hex values."""
    from briefkit.presets import get_preset, list_presets  # noqa: PLC0415

    as_json = getattr(args, "json", False)
    quiet = getattr(args, "quiet", False)

    names = list_presets()

    if as_json:
        data = {name: get_preset(name) for name in names}
        print(json.dumps(data, indent=2))
        return 0

    if quiet:
        for name in names:
            print(name)
        return 0

    for name in names:
        colors = get_preset(name)
        print(f"\n  {name}")
        for key, value in colors.items():
            print(f"    {key:<12} {value}")

    return 0


def cmd_licenses(args: argparse.Namespace) -> int:
    """List all available license presets with descriptions."""
    from briefkit.presets.licenses import LICENSE_CATEGORIES, LICENSE_PRESETS  # noqa: PLC0415

    as_json = getattr(args, "json", False)
    quiet = getattr(args, "quiet", False)

    if as_json:
        print(json.dumps(LICENSE_PRESETS, indent=2, default=str))
        return 0

    if quiet:
        for name in sorted(LICENSE_PRESETS):
            print(name)
        return 0

    print("\n  Available license presets for briefkit.yml (license.preset):\n")
    for category_name, keys in LICENSE_CATEGORIES:
        print(f"  ── {category_name} ──")
        for key in keys:
            preset = LICENSE_PRESETS.get(key)
            if not preset:
                continue
            name = preset["name"]
            spdx = preset.get("spdx", "")
            commercial = preset.get("commercial")
            comm_tag = ""
            if commercial is True:
                comm_tag = " [commercial OK]"
            elif commercial is False:
                comm_tag = " [non-commercial]"
            spdx_tag = f"  (SPDX: {spdx})" if spdx else ""
            print(f"    {key:<20} {name}{spdx_tag}{comm_tag}")
        print()

    print("  Set in briefkit.yml:")
    print("    license:")
    print('      preset: MIT       # or any preset name above')
    print()
    print("  WARNING: Projects without a license default to 'All Rights Reserved'")
    print("  under copyright law. Always specify a license for shared work.\n")

    return 0


# ---------------------------------------------------------------------------
# Argument parser construction
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="briefkit",
        description="Generate professional PDF briefings from structured Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              briefkit init
              briefkit generate ./docs/governance
              briefkit batch ./docs --force
              briefkit status ./docs
              briefkit presets
              briefkit config --json
        """),
    )
    parser.add_argument("--version", action="version", version=_get_version())

    # Global flags
    global_flags = argparse.ArgumentParser(add_help=False)
    global_flags.add_argument(
        "--config", "-c",
        metavar="FILE",
        help="Path to briefkit.yml (default: auto-discover from CWD)",
    )
    global_flags.add_argument(
        "--quiet", "-q",
        action="store_true",
        default=False,
        help="Suppress non-error output",
    )
    global_flags.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose/debug output",
    )
    global_flags.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON",
    )
    global_flags.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be done without writing files",
    )

    # Generation flags (shared by generate, batch, preview)
    gen_flags = argparse.ArgumentParser(add_help=False)
    gen_flags.add_argument(
        "--template", "-t",
        metavar="NAME",
        help="Template preset to use (e.g. briefing, summary, technical)",
    )
    gen_flags.add_argument(
        "--preset", "-p",
        metavar="NAME",
        help="Color preset (e.g. navy, charcoal, ocean, cyber, neon)",
    )
    gen_flags.add_argument(
        "--variant", "-v",
        metavar="NAME",
        help="Output variant (e.g. aiml, legal, medical, engineering, hardware)",
    )
    gen_flags.add_argument(
        "--output", "-o",
        metavar="PATH",
        help="Override output PDF path",
    )
    gen_flags.add_argument(
        "--force", "-f",
        action="store_true",
        default=False,
        help="Regenerate even if output is current",
    )
    gen_flags.add_argument(
        "--no-ids",
        action="store_true",
        default=False,
        help="Disable document ID assignment",
    )
    gen_flags.add_argument(
        "--logo",
        metavar="PATH",
        help="Path to logo image file",
    )
    gen_flags.add_argument(
        "--org",
        metavar="NAME",
        help="Override organisation name",
    )
    gen_flags.add_argument(
        "--title",
        metavar="TEXT",
        help="Override document title",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # --- generate ---
    p_gen = subparsers.add_parser(
        "generate",
        parents=[global_flags, gen_flags],
        help="Generate a briefing PDF for a directory",
        description="Generate an executive briefing PDF from Markdown docs in PATH.",
    )
    p_gen.add_argument("path", metavar="PATH", help="Directory containing Markdown docs")
    p_gen.set_defaults(func=cmd_generate)

    # --- batch ---
    p_batch = subparsers.add_parser(
        "batch",
        parents=[global_flags, gen_flags],
        help="Batch generate all briefings under a root directory",
        description="Recursively find and generate briefings for all eligible directories.",
    )
    p_batch.add_argument("root", metavar="ROOT", help="Root directory to search")
    p_batch.set_defaults(func=cmd_batch)

    # --- init ---
    p_init = subparsers.add_parser(
        "init",
        parents=[global_flags],
        help="Create briefkit.yml with defaults",
        description="Write a briefkit.yml configuration file in the target directory.",
    )
    p_init.add_argument(
        "path",
        metavar="PATH",
        nargs="?",
        default=".",
        help="Directory to initialise (default: current directory)",
    )
    p_init.add_argument(
        "--force", "-f",
        action="store_true",
        default=False,
        help="Overwrite existing briefkit.yml",
    )
    p_init.set_defaults(func=cmd_init)

    # --- preview ---
    p_prev = subparsers.add_parser(
        "preview",
        parents=[global_flags, gen_flags],
        help="Generate and open the briefing PDF",
        description="Generate the briefing and open it with the system PDF viewer.",
    )
    p_prev.add_argument("path", metavar="PATH", help="Directory containing Markdown docs")
    p_prev.set_defaults(func=cmd_preview)

    # --- status ---
    p_status = subparsers.add_parser(
        "status",
        parents=[global_flags],
        help="Show briefing status (current / stale / missing)",
        description="Report whether briefings are up-to-date relative to their sources.",
    )
    p_status.add_argument(
        "path",
        metavar="PATH",
        nargs="?",
        default=".",
        help="Directory to check (default: current directory)",
    )
    p_status.set_defaults(func=cmd_status)

    # --- assign-ids ---
    p_ids = subparsers.add_parser(
        "assign-ids",
        parents=[global_flags],
        help="Assign doc IDs without regenerating the PDF",
        description="Scan Markdown files and write or update document ID front-matter.",
    )
    p_ids.add_argument("path", metavar="PATH", help="Directory to process")
    p_ids.set_defaults(func=cmd_assign_ids)

    # --- quality ---
    p_qual = subparsers.add_parser(
        "quality",
        parents=[global_flags],
        help="Run quality gates on an existing briefing PDF",
        description="Validate an existing PDF against the configured quality constraints.",
    )
    p_qual.add_argument(
        "path",
        metavar="PATH",
        help="Directory containing the PDF, or direct path to a PDF file",
    )
    p_qual.set_defaults(func=cmd_quality)

    # --- selftest ---
    p_self = subparsers.add_parser(
        "selftest",
        parents=[global_flags, gen_flags],
        help="Generate a briefing from the built-in test fixture",
        description="Verify the briefkit installation by generating a test PDF.",
    )
    p_self.set_defaults(func=cmd_selftest)

    # --- config ---
    p_cfg = subparsers.add_parser(
        "config",
        parents=[global_flags],
        help="Print the resolved configuration",
        description="Show the fully resolved briefkit configuration (defaults + project YAML).",
    )
    p_cfg.set_defaults(func=cmd_config)

    # --- templates ---
    p_tpl = subparsers.add_parser(
        "templates",
        parents=[global_flags],
        help="List available template presets",
    )
    p_tpl.set_defaults(func=cmd_templates)

    # --- presets ---
    p_prs = subparsers.add_parser(
        "presets",
        parents=[global_flags],
        help="List color presets with hex values",
    )
    p_prs.set_defaults(func=cmd_presets)

    # --- licenses ---
    p_lic = subparsers.add_parser(
        "licenses",
        parents=[global_flags],
        help="List available license presets",
    )
    p_lic.set_defaults(func=cmd_licenses)

    return parser


def _get_version() -> str:
    try:
        from importlib.metadata import version  # noqa: PLC0415
        return f"briefkit {version('briefkit')}"
    except Exception:  # PackageNotFoundError or ImportError  # noqa: BLE001
        return "briefkit (unknown version)"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point.  Returns an exit code (0 = success, non-zero = failure).
    Registered as ``briefkit`` console_scripts in pyproject.toml.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        rc = args.func(args)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001
        verbose = getattr(args, "verbose", False)
        if verbose:
            import traceback  # noqa: PLC0415
            traceback.print_exc()
        else:
            print(f"Error: {exc}", file=sys.stderr)
            print("Run with --verbose for a full traceback.", file=sys.stderr)
        return 1

    return rc if isinstance(rc, int) else 0


if __name__ == "__main__":
    sys.exit(main())

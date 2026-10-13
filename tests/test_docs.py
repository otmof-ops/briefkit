"""
The documentation is checked, not trusted.

Every fenced ``briefkit ...`` command in the docs must parse with the real
argument parser, every relative link must resolve, every template, preset
and variant must be documented by name, the version must agree everywhere,
and the spelling is American.
"""

from __future__ import annotations

import contextlib
import io
import re
import shlex
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC_FILES = [
    ROOT / "README.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "SECURITY.md",
    ROOT / "SAFETY.md",
    ROOT / "CHANGELOG.md",
    ROOT / "examples" / "README.md",
    *sorted((ROOT / "docs").rglob("*.md")),
]
# A plan, not a description of the tool: its commands may not exist yet.
PLAN_DOCS = {ROOT / "docs" / "perfect-pdf-roadmap.md"}

FENCE = re.compile(r"^```([^\n]*)\n(.*?)^```", re.MULTILINE | re.DOTALL)
SHELL_LANGS = {"", "bash", "sh", "shell", "console", "zsh"}
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
INLINE_CODE = re.compile(r"`[^`\n]*`")

BRITISH = re.compile(
    r"\b(grey|behaviour|centralis(e|ed|es|ing)|catalogue|sanitis(e|ed|er|ing)|organis(e|ed|es|ing|ation|ations)"
    r"|honour(s|ed|ing)?|colour(s|ed)?|serialis(e|ed)|licences?|labelled|favour(s|ed|ite)?|capitalis(e|ed)"
    r"|initialis(e|ed|ing)|customis(e|ed|ing)|recognis(e|ed|es)|optimis(e|ed|ation)|normalis(e|ed)|minimis(e|ed)"
    r"|summaris(e|ed)|utilise|visualise|prioritise|authoris(e|ed|ation)|standardise|synchronise|analys(e|ed|es)"
    r"|modelling|cancelled|travelled|centred?|metres?|artefacts?|judgement|programme|defence|whilst|amongst|learnt"
    r"|fibre|ageing|practise|specialis(e|ed)|containerised)\b",
    re.IGNORECASE,
)


def _fenced_blocks(text: str):
    for match in FENCE.finditer(text):
        yield match.group(1).strip().lower(), match.group(2)


def _briefkit_commands(text: str):
    """Yield (line, argv) for every ``briefkit`` invocation in a shell code block."""
    for lang, body in _fenced_blocks(text):
        if lang not in SHELL_LANGS:
            continue
        for raw in body.splitlines():
            if lang == "" and raw[:1].isspace():
                continue  # an indented line in a plain block is quoted output, not a command
            line = raw.strip()
            if line.startswith("$ "):
                line = line[2:]
            for segment in re.split(r"&&|\|\||;|\|", line):
                segment = re.split(r"\s\d?>>?\s", segment)[0]  # drop a redirection
                segment = segment.strip().strip("()").strip()
                if not segment:
                    continue
                try:
                    tokens = shlex.split(segment, comments=True)
                except ValueError:
                    continue  # an unterminated quote belongs to a heredoc or a loop, not to a command
                while tokens and ENV_ASSIGNMENT.match(tokens[0]):
                    tokens.pop(0)
                if not tokens or tokens[0] != "briefkit":
                    continue
                argv = tokens[1:]
                if any("<" in t or t.startswith("[") for t in argv):
                    continue  # a synopsis with placeholders, not a runnable example
                yield line, argv


def _prose(text: str) -> str:
    """The text with fenced blocks and inline code removed."""
    text = FENCE.sub("", text)
    return INLINE_CODE.sub("", text)


@pytest.mark.parametrize("doc", DOC_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_every_documented_command_parses(doc: Path):
    from briefkit.cli import _build_parser

    if doc in PLAN_DOCS:
        pytest.skip("a plan document")
    parser = _build_parser()
    failures = []
    for line, argv in _briefkit_commands(doc.read_text(encoding="utf-8")):
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                parser.parse_args(argv)
        except SystemExit as exc:
            if exc.code not in (0, None):
                failures.append(f"{line!r}: {err.getvalue().strip().splitlines()[-1]}")
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize("doc", DOC_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_resolve(doc: Path):
    missing = []
    for target in LINK.findall(_prose(doc.read_text(encoding="utf-8"))):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path = target.split("#", 1)[0]
        if not path or ("/" not in path and "." not in path):
            continue  # a bare word used as a placeholder, not a path
        if not (doc.parent / path).exists():
            missing.append(target)
    assert not missing, f"{doc.relative_to(ROOT)}: broken links {missing}"


@pytest.mark.parametrize("doc", DOC_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_american_spelling(doc: Path):
    hits = []
    for number, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
        for match in BRITISH.finditer(line):
            hits.append(f"{number}: {match.group(0)}")
    assert not hits, f"{doc.relative_to(ROOT)}: {hits}"


def test_every_template_preset_and_variant_is_documented():
    from briefkit.presets.colors import PRESETS
    from briefkit.templates import list_templates
    from briefkit.variants import list_variants

    guide = (ROOT / "docs" / "templates-guide.md").read_text(encoding="utf-8")
    missing = [name for name in list_templates() if f"`{name}`" not in guide]
    assert not missing, f"templates-guide.md lacks {missing}"

    for page in ("color-presets.md", "presets-guide.md"):
        text = (ROOT / "docs" / page).read_text(encoding="utf-8")
        missing = [name for name in PRESETS if f"`{name}`" not in text]
        assert not missing, f"{page} lacks {missing}"

    variants = (ROOT / "docs" / "variants.md").read_text(encoding="utf-8")
    missing = [name for name in list_variants() if f"`{name}`" not in variants]
    assert not missing, f"variants.md lacks {missing}"


def test_every_subcommand_has_a_reference_section():
    from briefkit.cli import _build_parser

    parser = _build_parser()
    subparsers = next(a for a in parser._actions if a.dest == "command")
    reference = (ROOT / "docs" / "cli-reference.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for name in subparsers.choices:
        assert f"`briefkit {name}" in reference, f"cli-reference.md does not cover {name}"
        assert f"`briefkit {name}" in readme, f"README.md command table does not list {name}"


def test_version_agrees_everywhere():
    import briefkit

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    declared = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE).group(1)
    assert briefkit.__version__ == declared
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{declared}]" in changelog, "CHANGELOG.md has no section for the current version"
    assert f"[{declared}]: https://" in changelog, "CHANGELOG.md has no compare link for the current version"

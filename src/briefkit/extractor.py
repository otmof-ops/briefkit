"""
briefkit.extractor
~~~~~~~~~~~~~~~~~~
Content extraction from filesystem paths.

Extracted and generalized from generate-briefing-v2.py:
  - parse_markdown()            original lines 430-618
  - extract_doc_set_content()   original lines 724-1180

All Codex-specific references removed.  The public API is:

  parse_markdown(text)  ->  list[dict]
  extract_content(path, level, config)  ->  dict
"""

from __future__ import annotations

import datetime
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from briefkit.bibliography import extract_bibliography, _parse_kebab_bibliography
from briefkit.cross_refs import extract_cross_refs
from briefkit.terms import extract_terms, _GENERIC_TERMS

# ---------------------------------------------------------------------------
# Pre-compiled parse patterns
# ---------------------------------------------------------------------------

_RE_CODE_FENCE = re.compile(r'^```')
_RE_HRULE = re.compile(r'^(\-{3,}|\*{3,}|_{3,})\s*$')
_RE_TABLE_SEP = re.compile(r'^:?-+:?$')
_RE_HEADING = re.compile(r'^(#{1,6})\s+(.+)$')
_RE_ORDERED_LIST = re.compile(r'^(\d+)\.\s+(.+)$')
_RE_UNORDERED_LIST = re.compile(r'^[\*\-\+]\s+(.+)$')

# Pre-compiled inline formatting patterns
_RE_BOLD_ITALIC_AST = re.compile(r'\*{3}(.+?)\*{3}')
_RE_BOLD_ITALIC_UND = re.compile(r'_{3}(.+?)_{3}')
_RE_BOLD_AST = re.compile(r'\*{2}(.+?)\*{2}')
_RE_BOLD_UND = re.compile(r'_{2}(.+?)_{2}')
_RE_ITALIC_AST = re.compile(r'\*(.+?)\*')
_RE_ITALIC_UND = re.compile(r'(?<!\w)_(.+?)_(?!\w)')  # word-boundary restricted
_RE_INLINE_CODE = re.compile(r'`(.+?)`')
_RE_MD_LINK = re.compile(r'\[([^\]]+)\]\([^\)]*\)')


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

def parse_markdown(text: str) -> list[dict]:
    """
    Parse a Markdown string into a list of content block dicts.

    Each block has at minimum a 'type' key. Types:
      heading    — {'type': 'heading', 'level': int, 'text': str}
      paragraph  — {'type': 'paragraph', 'text': str}
      table      — {'type': 'table', 'headers': list[str], 'rows': list[list[str]]}
      code       — {'type': 'code', 'text': str, 'lang': str}
      list_item  — {'type': 'list_item', 'text': str, 'ordered': bool, 'index': int}
      blockquote — {'type': 'blockquote', 'text': str}
      rule       — {'type': 'rule'}
    """
    blocks: list[dict] = []
    lines = text.splitlines()
    i = 0
    list_counter = 0

    def _strip_inline(s: str) -> str:
        """Convert inline markdown to basic HTML that ReportLab Paragraph accepts."""
        if not any(c in s for c in '*_`['):
            return s
        s = _RE_BOLD_ITALIC_AST.sub(r'<b><i>\1</i></b>', s)
        s = _RE_BOLD_ITALIC_UND.sub(r'<b><i>\1</i></b>', s)
        s = _RE_BOLD_AST.sub(r'<b>\1</b>', s)
        s = _RE_BOLD_UND.sub(r'<b>\1</b>', s)
        s = _RE_ITALIC_AST.sub(r'<i>\1</i>', s)
        s = _RE_ITALIC_UND.sub(r'<i>\1</i>', s)
        s = _RE_INLINE_CODE.sub(r'<font name="Courier">\1</font>', s)
        s = re.sub(r'~~(.+?)~~', r'<strike>\1</strike>', s)
        s = _RE_MD_LINK.sub(r'\1', s)
        return s

    in_code_block = False
    code_lines: list[str] = []
    code_lang = ""
    in_table = False
    table_headers: list[str] = []
    table_rows: list[list[str]] = []
    pending_paragraph_lines: list[str] = []
    last_was_list = False

    def _flush_paragraph():
        nonlocal pending_paragraph_lines
        if pending_paragraph_lines:
            combined = " ".join(l.strip() for l in pending_paragraph_lines if l.strip())
            if combined:
                blocks.append({"type": "paragraph", "text": _strip_inline(combined)})
            pending_paragraph_lines = []

    def _flush_table():
        nonlocal in_table, table_headers, table_rows
        if in_table and table_headers:
            blocks.append({
                "type": "table",
                "headers": table_headers,
                "rows": table_rows,
            })
        in_table = False
        table_headers = []
        table_rows = []

    while i < len(lines):
        line = lines[i]

        # Fenced code block
        if _RE_CODE_FENCE.match(line):
            if in_code_block:
                blocks.append({
                    "type": "code",
                    "lang": code_lang,
                    "text": "\n".join(code_lines),
                })
                in_code_block = False
                code_lines = []
                code_lang = ""
            else:
                _flush_paragraph()
                _flush_table()
                in_code_block = True
                code_lang = line[3:].strip()
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Horizontal rule
        if _RE_HRULE.match(line):
            _flush_paragraph()
            _flush_table()
            blocks.append({"type": "rule"})
            i += 1
            continue

        # Table row
        if line.strip().startswith("|") and line.strip().endswith("|"):
            _flush_paragraph()
            cells = [_strip_inline(c.strip()) for c in line.strip().strip("|").split("|")]
            if all(_RE_TABLE_SEP.match(c) for c in cells if c):
                i += 1
                continue
            if not in_table:
                in_table = True
                table_headers = [_strip_inline(c) for c in cells]
                table_rows = []
            else:
                table_rows.append(cells)
            i += 1
            continue
        elif in_table:
            _flush_table()

        # Heading
        m = _RE_HEADING.match(line)
        if m:
            _flush_paragraph()
            level = len(m.group(1))
            text  = _strip_inline(m.group(2).strip())
            blocks.append({"type": "heading", "level": level, "text": text})
            last_was_list = False
            i += 1
            continue

        # Blockquote
        if line.startswith("> ") or line == ">":
            _flush_paragraph()
            quote_lines: list[str] = []
            while i < len(lines) and (lines[i].startswith("> ") or lines[i] == ">"):
                quote_lines.append(lines[i][2:] if lines[i].startswith("> ") else "")
                i += 1
            text = " ".join(l for l in quote_lines)
            blocks.append({"type": "blockquote", "text": _strip_inline(text)})
            continue

        # Ordered list item
        m = _RE_ORDERED_LIST.match(line)
        if m:
            _flush_paragraph()
            if not last_was_list:
                list_counter = 0
            list_counter += 1
            blocks.append({
                "type": "list_item",
                "ordered": True,
                "index": int(m.group(1)),
                "text": _strip_inline(m.group(2).strip()),
            })
            last_was_list = True
            i += 1
            continue

        # Unordered list item
        m = _RE_UNORDERED_LIST.match(line)
        if m:
            _flush_paragraph()
            blocks.append({
                "type": "list_item",
                "ordered": False,
                "index": 0,
                "text": _strip_inline(m.group(1).strip()),
            })
            last_was_list = True
            i += 1
            continue

        # Blank line
        if line.strip() == "":
            _flush_paragraph()
            last_was_list = False
            i += 1
            continue

        # Regular text
        last_was_list = False
        pending_paragraph_lines.append(line)
        i += 1

    _flush_paragraph()
    _flush_table()

    return blocks



# ---------------------------------------------------------------------------
# Doc-set content extractor
# ---------------------------------------------------------------------------

def _extract_doc_set_content(path: Path, config: dict) -> dict:
    """
    Read a doc-set directory and return a structured content dict.

    Reads README.md, numbered docs (01-*.md … NN-*.md), orientation doc,
    engineering-brilliance.md, guide.md, and bibliography from PDF filenames
    and inline citations.
    """
    content_cfg = config.get("content", {})
    max_words   = content_cfg.get("max_words_per_section", 3000)
    max_terms   = content_cfg.get("max_terms_in_index", 40)
    max_refs    = content_cfg.get("max_cross_refs", 30)
    ori_pattern = content_cfg.get("orientation_doc_pattern", "00-what-is-*.md")
    num_pattern = content_cfg.get("numbered_doc_pattern", "[0-9][0-9]-*.md")

    result: dict[str, Any] = {
        "title":            path.name.replace("-", " ").title(),
        "overview":         "",
        "subsystems":       [],
        "brilliance_summary": "",
        "guide_content":    "",
        "orientation":      "",
        "cross_refs":       [],
        "cross_ref_labels": {},
        "terms":            {},
        "bibliography":     [],
        "metrics": {
            "doc_count":        0,
            "word_count":       0,
            "file_count":       0,
            "year":             str(datetime.date.today().year),
            "pdf_count":        0,
            "source_type":      "ACADEMIC",
            "avg_chapter_size": 0,
            "citation_count":   0,
            "table_count":      0,
            "has_orientation":  False,
        },
        "source_type_info": {},
    }

    MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB

    def _read(fp: Path) -> str:
        if fp.is_symlink():
            return ""
        try:
            if fp.stat().st_size > MAX_FILE_BYTES:
                print(f"Warning: Skipping oversized file ({fp.stat().st_size} bytes): {fp}", file=sys.stderr)
                return ""
        except OSError:
            pass
        try:
            return fp.read_text(encoding="utf-8", errors="replace")
        except OSError:  # file permission / encoding / not-found
            return ""

    def _count_words(t: str) -> int:
        return len(t.split())

    total_words = 0

    # .source-type marker
    source_type_file = path / ".source-type"
    if source_type_file.exists():
        raw_st = _read(source_type_file)
        st_info: dict[str, str] = {}
        for ln in raw_st.splitlines():
            if ":" in ln:
                k, _, v = ln.partition(":")
                st_info[k.strip().lower()] = v.strip()
        result["source_type_info"] = st_info
        result["metrics"]["source_type"] = st_info.get("type", "ACADEMIC").upper()

    # Orientation doc (e.g. 00-what-is-*.md)
    orientation_files = sorted(path.glob(ori_pattern))
    if orientation_files:
        raw_ori = _read(orientation_files[0])
        total_words += _count_words(raw_ori)
        result["orientation"] = raw_ori
        result["metrics"]["has_orientation"] = True

    # README.md
    readme = path / "README.md"
    if readme.exists():
        raw = _read(readme)
        total_words += _count_words(raw)
        m = re.search(r'^#\s+(.+)$', raw, re.MULTILINE)
        if m:
            result["title"] = m.group(1).strip()
        overview_match = re.search(r'^(?!#)(.{80,})', raw, re.MULTILINE)
        if overview_match:
            lines_after = raw[overview_match.start():].split("\n")
            para_lines: list[str] = []
            for ln in lines_after:
                if ln.strip() == "" and para_lines:
                    break
                if ln.strip():
                    para_lines.append(ln.strip())
                if len(para_lines) >= 5:
                    break
            result["overview"] = " ".join(para_lines)
    else:
        result["overview"] = f"Overview not available — see numbered documents in {path.name}."

    # Numbered docs
    # Filter out orientation docs (00-what-is-*)
    numbered_files = sorted(
        f for f in path.glob(num_pattern)
        if not f.name.startswith("00-what-is")
    )
    result["metrics"]["doc_count"] = len(numbered_files)

    chapter_sizes: list[int] = []
    total_citation_count = 0
    total_table_count = 0

    for fp in numbered_files:
        raw = _read(fp)
        raw_size = len(raw.encode("utf-8", errors="replace"))
        chapter_sizes.append(raw_size)
        total_words += _count_words(raw)

        # Truncate to max_words, preserving tables and blockquotes
        words = raw.split()
        if len(words) > max_words:
            truncated_lines: list[str] = []
            word_count_so_far = 0
            in_tbl = False
            in_qt  = False
            for ln in raw.splitlines():
                lw = len(ln.split())
                if ln.startswith("|"):
                    in_tbl = True
                    truncated_lines.append(ln)
                    continue
                elif in_tbl and not ln.startswith("|"):
                    in_tbl = False
                if ln.startswith("> "):
                    in_qt = True
                    truncated_lines.append(ln)
                    continue
                elif in_qt and not ln.startswith("> "):
                    in_qt = False
                if word_count_so_far < max_words:
                    truncated_lines.append(ln)
                    word_count_so_far += lw
            raw_for_parse = "\n".join(truncated_lines)
        else:
            raw_for_parse = raw

        stem     = fp.stem
        name_part = re.sub(r'^\d+-', '', stem).replace("-", " ").title()

        blocks = parse_markdown(raw_for_parse)
        tables  = [b for b in blocks if b["type"] == "table"]
        total_table_count += len(tables)
        insights = [b["text"] for b in blocks if b["type"] == "blockquote"]

        cite_count = len(re.findall(r'\[Source', raw, re.IGNORECASE))
        total_citation_count += cite_count

        result["subsystems"].append({
            "name":     name_part,
            "filename": fp.name,
            "content":  raw_for_parse,
            "blocks":   blocks,
            "tables":   tables,
            "insights": insights,
        })

    result["metrics"]["avg_chapter_size"] = (
        sum(chapter_sizes) // len(chapter_sizes) if chapter_sizes else 0
    )
    result["metrics"]["citation_count"] = total_citation_count
    result["metrics"]["table_count"]    = total_table_count

    # Collect PDF list once for reuse (fallback overview + bibliography)
    all_pdfs = sorted(path.glob("*.pdf"))

    if not result["subsystems"] and not result["overview"]:
        if all_pdfs:
            result["overview"] = (
                f"No analysis documents found. "
                f"Primary sources: {', '.join(pdf.name for pdf in all_pdfs[:5])}."
            )
        else:
            result["overview"] = "No analysis documents found in this doc set."

    # engineering-brilliance.md
    brilliance = path / "engineering-brilliance.md"
    if brilliance.exists():
        raw = _read(brilliance)
        total_words += _count_words(raw)
        result["brilliance_summary"] = raw

    # guide.md
    guide = path / "guide.md"
    if guide.exists():
        raw = _read(guide)
        total_words += _count_words(raw)
        result["guide_content"] = raw

    # Cross-references — delegate to standalone module
    cross_refs_list, cross_ref_labels = extract_cross_refs(path)
    result["cross_refs"] = cross_refs_list[:max_refs]
    result["cross_ref_labels"] = cross_ref_labels

    # Term extraction — build all_text efficiently via join (avoids O(n^2) concat)
    all_text = " ".join([
        result.get("overview", ""),
        result.get("brilliance_summary", ""),
        *(sub.get("content", "") for sub in result.get("subsystems", [])),
    ])

    # Use standalone terms module, then supplement with table-header terms
    result["terms"] = extract_terms(
        all_text, title=result["title"], max_terms=max_terms,
    )

    # Add table-header terms not already covered
    th_terms: list[str] = []
    for sub in result["subsystems"]:
        for tbl in sub.get("tables", []):
            for h in tbl.get("headers", []):
                if h and len(h) >= 4:
                    th_terms.append(h.strip())

    if th_terms:
        seen_lower = {t.lower() for t in result["terms"]}
        doc_title_lower = result["title"].lower()
        for term_raw in th_terms:
            term_clean = re.sub(r'[#\*`]', '', term_raw).strip()
            term_lower = term_clean.lower()
            if (
                term_clean
                and len(term_clean) >= 4
                and term_lower not in _GENERIC_TERMS
                and term_lower not in seen_lower
                and term_lower not in doc_title_lower
                and not re.match(r'^\d+', term_clean)
            ):
                result["terms"][term_clean] = ""
                seen_lower.add(term_lower)

        if len(result["terms"]) > max_terms:
            sorted_terms = sorted(result["terms"].keys(), key=str.lower)[:max_terms]
            result["terms"] = {t: "" for t in sorted_terms}

    # Bibliography — use standalone module for inline citations
    # First pass: PDF filenames (preserving pdf_years for metrics)
    out_filename = config.get("output", {}).get("filename", "executive-briefing.pdf")
    pdf_years: list[int] = []
    pdf_count = 0
    for pdf in all_pdfs:
        if pdf.name == out_filename:
            continue
        pdf_count += 1
        stem_pdf = pdf.stem
        arxiv_match = re.match(r'^(\d{4}\.\d{4,5})(v\d+)?$', stem_pdf)
        if arxiv_match:
            result["bibliography"].append({
                "title":   f"arXiv:{arxiv_match.group(1)}",
                "authors": "",
                "year":    ("20" if arxiv_match.group(1)[:2] < "50" else "19") + arxiv_match.group(1)[:2],
                "type":    "paper",
                "doi":     "",
            })
        else:
            author, title_str, year_str = _parse_kebab_bibliography(stem_pdf)
            if year_str:
                pdf_years.append(int(year_str))
            if author or title_str:
                result["bibliography"].append({
                    "title":   title_str or stem_pdf,
                    "authors": author,
                    "year":    year_str,
                    "type":    "paper",
                    "doi":     "",
                })

    # Inline citations via standalone module (dedup against PDF entries)
    inline_bib = extract_bibliography(all_text)
    existing_keys: set[tuple[str, str]] = set()
    for b in result["bibliography"]:
        a = re.sub(r'\.$', '', b.get("authors", "").strip()).lower().replace("et al.", "et al")
        existing_keys.add((a, b.get("year", "")))
    for entry in inline_bib:
        a = re.sub(r'\.$', '', entry.get("authors", "").strip()).lower().replace("et al.", "et al")
        key = (a, entry.get("year", ""))
        if key not in existing_keys:
            result["bibliography"].append(entry)
            existing_keys.add(key)

    # Metrics finalization
    result["metrics"]["word_count"] = total_words
    result["metrics"]["file_count"] = sum(1 for f in path.rglob("*") if f.is_file())
    result["metrics"]["pdf_count"]  = pdf_count

    if pdf_years:
        result["metrics"]["year"] = str(max(pdf_years))
    else:
        year_matches = re.findall(r'\b(19[5-9]\d|20[0-2]\d)\b', result["overview"])
        if year_matches:
            year_counts = Counter(year_matches)
            result["metrics"]["year"] = year_counts.most_common(1)[0][0]

    return result


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def _aggregate_subject_content(path: Path, config: dict, date: datetime.date) -> dict:
    """Aggregate all doc-set content under a subject directory."""
    agg: dict[str, Any] = {
        "title":            path.name.replace("-", " ").title(),
        "overview":         "",
        "subsystems":       [],
        "brilliance_summary": "",
        "guide_content":    "",
        "cross_refs":       [],
        "cross_ref_labels": {},
        "terms":            {},
        "bibliography":     [],
        "metrics": {
            "doc_count":   0,
            "word_count":  0,
            "file_count":  0,
            "year":        str(date.year),
            "source_type": "ACADEMIC",
        },
        "doc_sets": [],
    }

    readme = path / "README.md"
    if readme.exists():
        if readme.is_symlink():
            raw = ""
        else:
            raw = readme.read_text(encoding="utf-8", errors="replace")
        m   = re.search(r'^#\s+(.+)$', raw, re.MULTILINE)
        if m:
            agg["title"] = m.group(1).strip()
        agg["overview"] = raw[:1000]

    cross_refs_seen: set = set()
    for child in sorted(path.iterdir()):
        if child.is_dir() and not child.name.startswith("."):
            numbered = list(child.glob("[0-9][0-9]-*.md"))
            if numbered or (child / "README.md").exists():
                try:
                    ds = _extract_doc_set_content(child, config)
                    agg["doc_sets"].append(ds)
                    agg["metrics"]["doc_count"]  += 1
                    agg["metrics"]["word_count"]  += ds["metrics"]["word_count"]
                    agg["metrics"]["file_count"]  += ds["metrics"]["file_count"]
                    agg["terms"].update(ds["terms"])
                    for ref in ds["cross_refs"]:
                        if ref not in cross_refs_seen:
                            agg["cross_refs"].append(ref)
                            cross_refs_seen.add(ref)
                            agg["cross_ref_labels"].setdefault(ref, ds["cross_ref_labels"].get(ref, ""))
                    agg["bibliography"].extend(ds["bibliography"])
                except Exception as exc:
                    print(f"Warning: Skipped doc-set: {exc}", file=sys.stderr)

    return agg


def _aggregate_division_content(path: Path, config: dict, date: datetime.date) -> dict:
    """Aggregate all subject content under a division directory."""
    agg: dict[str, Any] = {
        "title":            path.name.replace("-", " ").title(),
        "overview":         "",
        "subsystems":       [],
        "brilliance_summary": "",
        "guide_content":    "",
        "cross_refs":       [],
        "cross_ref_labels": {},
        "terms":            {},
        "bibliography":     [],
        "metrics": {
            "doc_count":  0,
            "word_count": 0,
            "file_count": 0,
            "year":       str(date.year),
        },
        "subjects": [],
    }

    readme = path / "README.md"
    if readme.exists():
        if readme.is_symlink():
            raw = ""
        else:
            raw = readme.read_text(encoding="utf-8", errors="replace")
        m   = re.search(r'^#\s+(.+)$', raw, re.MULTILINE)
        if m:
            agg["title"] = m.group(1).strip()
        agg["overview"] = raw[:2000]

    for child in sorted(path.iterdir()):
        if child.is_dir() and not child.name.startswith(".") and child.name not in ("_tools",):
            subject_data: dict[str, Any] = {
                "name":      child.name.replace("-", " ").title(),
                "path":      str(child),
                "doc_count": 0,
                "overview":  "",
            }
            sub_readme = child / "README.md"
            if sub_readme.exists():
                if sub_readme.is_symlink():
                    raw = ""
                else:
                    raw = sub_readme.read_text(encoding="utf-8", errors="replace")
                subject_data["overview"] = raw[:500]
                m = re.search(r'^#\s+(.+)$', raw, re.MULTILINE)
                if m:
                    subject_data["name"] = m.group(1).strip()

            doc_sets = [
                d for d in child.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            ]
            subject_data["doc_count"] = len(doc_sets)
            agg["metrics"]["doc_count"] += len(doc_sets)
            agg["subjects"].append(subject_data)

    return agg


def _aggregate_root_content(path: Path, config: dict, date: datetime.date) -> dict:
    """Aggregate top-level content for the project root (Level 4)."""
    project_cfg = config.get("project", {})
    default_title = project_cfg.get("name", path.name.replace("-", " ").title())

    agg: dict[str, Any] = {
        "title":            default_title,
        "overview":         "",
        "subsystems":       [],
        "brilliance_summary": "",
        "guide_content":    "",
        "cross_refs":       [],
        "cross_ref_labels": {},
        "terms":            {},
        "bibliography":     [],
        "metrics": {
            "doc_count":  0,
            "word_count": 0,
            "file_count": 0,
            "year":       str(date.year),
        },
        "divisions": [],
    }

    readme = path / "README.md"
    if readme.exists():
        if readme.is_symlink():
            raw = ""
        else:
            raw = readme.read_text(encoding="utf-8", errors="replace")
        agg["overview"] = raw[:3000]
        m = re.search(r'^#\s+(.+)$', raw, re.MULTILINE)
        if m:
            agg["title"] = m.group(1).strip()

    guide = path / "guide.md"
    if guide.exists():
        if guide.is_symlink():
            raw = ""
        else:
            raw = guide.read_text(encoding="utf-8", errors="replace")
        agg["guide_content"] = raw[:2000]

    return agg


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_content(
    path: str | Path,
    level: int,
    config: dict | None = None,
) -> dict:
    """
    Extract structured content from *path* for a given hierarchy *level*.

    level 3 (doc set) — calls _extract_doc_set_content() directly.
    level 2 (subject) — aggregates child doc sets.
    level 1 (division) — aggregates subjects.
    level 4 (root)    — aggregates root-level content.

    Returns a structured content dict suitable for BaseBriefingTemplate.
    """
    config = config or {}
    p      = Path(path).resolve()
    today  = datetime.date.today()

    if level == 3:
        return _extract_doc_set_content(p, config)
    elif level == 2:
        return _aggregate_subject_content(p, config, today)
    elif level == 1:
        return _aggregate_division_content(p, config, today)
    else:
        return _aggregate_root_content(p, config, today)

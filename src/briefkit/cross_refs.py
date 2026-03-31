"""Cross-reference extraction from markdown files."""
import re
from pathlib import Path

# Pre-compiled cross-reference patterns (moved to module level)
_CROSS_REF_PAREN = re.compile(
    r'\((?:\.\./)+([a-z0-9\-/]+)(?:/README\.md|/executive-briefing\.pdf)?\)',
    re.IGNORECASE,
)
_CROSS_REF_MD_LINK = re.compile(
    r'\[([^\]]+)\]\((?:\.\./)+([a-z0-9\-/]+)(?:/[^\)]*)?\)',
    re.IGNORECASE,
)


def extract_cross_refs(path, known_groups=None):
    """
    Scan markdown files in a directory for cross-references.

    Args:
        path: Directory to scan.
        known_groups: Optional list of known top-level group names for
            absolute path matching. If None, only relative refs are found.

    Returns:
        tuple: (cross_refs list, cross_ref_labels dict)
    """
    p = Path(path)
    cross_refs = []
    cross_ref_labels = {}
    cross_refs_seen: set = set()

    # Absolute path refs using known groups
    cross_ref_abs = None
    if known_groups:
        cross_ref_abs = re.compile(
            r'\b(' + '|'.join(re.escape(g) for g in known_groups) + r')/([a-z0-9\-/]+)',
            re.IGNORECASE,
        )

    def _read(fp):
        try:
            return fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    all_md = list(p.glob("*.md"))
    for md_file in all_md:
        raw = _read(md_file)

        for match in _CROSS_REF_PAREN.finditer(raw):
            ref = match.group(1).strip("/")
            if ref and ref not in cross_refs_seen:
                cross_refs.append(ref)
                cross_refs_seen.add(ref)
                if ref not in cross_ref_labels:
                    cross_ref_labels[ref] = ref.split("/")[-1].replace("-", " ").title()

        for match in _CROSS_REF_MD_LINK.finditer(raw):
            label, ref = match.group(1), match.group(2).strip("/")
            if ref and ref not in cross_refs_seen:
                cross_refs.append(ref)
                cross_refs_seen.add(ref)
            if ref and ref not in cross_ref_labels:
                cross_ref_labels[ref] = label

        if cross_ref_abs:
            for match in cross_ref_abs.finditer(raw):
                ref = (match.group(1) + "/" + match.group(2)).strip("/")
                if ref and ref not in cross_refs_seen:
                    cross_refs.append(ref)
                    cross_refs_seen.add(ref)
                    if ref not in cross_ref_labels:
                        cross_ref_labels[ref] = ref.split("/")[-1].replace("-", " ").title()

    return cross_refs, cross_ref_labels

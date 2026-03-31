"""PDF version tracking — read/write briefing version from PDF metadata."""
import re
from pathlib import Path


def get_version(pdf_path):
    """
    Read the briefing version from a PDF's metadata keywords.

    Looks for 'codex-briefing-vN' or 'briefkit-vN' pattern in keywords.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        int: Version number, or 0 if not found.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return 0

    # Try pypdf first
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        info = reader.metadata
        if info:
            keywords = ""
            if hasattr(info, "get"):
                keywords = info.get("/Keywords", "") or ""
            elif hasattr(info, "keywords"):
                keywords = info.keywords or ""
            for pattern in [r'briefkit-v(\d+)', r'codex-briefing-v(\d+)']:
                m = re.search(pattern, str(keywords))
                if m:
                    return int(m.group(1))
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: binary scan
    try:
        raw = pdf_path.read_bytes()[:8192]
        for pattern in [rb'briefkit-v(\d+)', rb'codex-briefing-v(\d+)']:
            m = re.search(pattern, raw)
            if m:
                return int(m.group(1))
    except Exception:
        pass

    return 0


def needs_regeneration(pdf_path, current_version):
    """
    Check if a PDF needs regeneration.

    Returns True if the PDF is missing, has no version, or has an older version.

    Args:
        pdf_path: Path to the PDF file.
        current_version: Current template version number.

    Returns:
        bool: True if regeneration needed.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return True
    existing = get_version(pdf_path)
    return existing < current_version

"""
file_conversion.py — Stripped copy of `deerflow.utils.file_conversion`.

Only `extract_outline()` is needed by UploadsMiddleware; the heavy PDF/Office
conversion path (pymupdf4llm, MarkItDown, async file IO, app_config lookup)
has been removed. If you want PDF/PPT/DOC -> Markdown conversion, restore the
original file from deerflow and adapt the `_get_pdf_converter()` lookup to
your own config system.

External deps: stdlib only (`re`, `pathlib`).
"""

import re
from pathlib import Path

# Bold-only structural headings that pymupdf4llm emits when section titles
# share the body font size (common in SEC filings). The starter-keyword
# allow-list filters out boilerplate like all-caps addresses.
_BOLD_HEADING_RE = re.compile(
    r"^\*\*((ITEM|PART|SECTION|SCHEDULE|EXHIBIT|APPENDIX|ANNEX|CHAPTER)"
    r"\b[A-Z0-9 .,\-]*)\*\*\s*$"
)

# Split-bold headings: `**1** **Introduction**`. Pymupdf4llm emits these
# when a section number and its title live in different text spans inside the
# PDF. The negative lookahead `(?!\d[\d\s.,\-–—/:()%]*\*\*)` rejects financial
# table headers like `**2023** **2022** **2021**` while still accepting
# non-ASCII titles such as `**1** **概述**`. Bounded `{0,2}` keeps the regex
# linear (ReDoS-safe) on attacker-controlled input.
_SPLIT_BOLD_HEADING_RE = re.compile(
    r"^\*\*[\dA-Z][\d\.]*\*\*\s+\*\*(?!\d[\d\s.,\-–—/:()%]*\*\*)[^*]+\*\*"
    r"(?:\s+\*\*[^*]+\*\*){0,2}\s*$"
)

# Cap so the prompt cannot blow up on a 1000-page document.
MAX_OUTLINE_ENTRIES = 50


def _clean_bold_title(raw: str) -> str:
    """Normalise pymupdf4llm bold artefacts: `**A** **B**` -> `A B`, strip outer **."""
    merged = re.sub(r"\*\*\s*\*\*", " ", raw).strip()
    if m := re.fullmatch(r"\*\*(.+?)\*\*", merged, re.DOTALL):
        return m.group(1).strip()
    return merged


def extract_outline(md_path: Path) -> list[dict]:
    """Extract document headings from a Markdown file.

    Recognises three styles produced by pymupdf4llm:
        1. Standard `# Heading`
        2. Bold-only structural headings (SEC filings)
        3. Split-bold headings (academic papers)

    Returns a list of `{"title": str, "line": int}` dicts. If truncated, a
    sentinel `{"truncated": True}` is appended so callers can render a
    "showing first N headings" hint without re-reading the file.

    Robust on IO errors: returns `[]` if the file cannot be read.
    """
    outline: list[dict] = []
    try:
        with md_path.open(encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                stripped = line.strip()
                if not stripped:
                    continue

                if stripped.startswith("#"):
                    title = _clean_bold_title(stripped.lstrip("#").strip())
                    if title:
                        outline.append({"title": title, "line": lineno})
                elif m := _BOLD_HEADING_RE.match(stripped):
                    title = m.group(1).strip()
                    if title:
                        outline.append({"title": title, "line": lineno})
                elif _SPLIT_BOLD_HEADING_RE.match(stripped):
                    title = " ".join(re.findall(r"\*\*([^*]+)\*\*", stripped))
                    if title:
                        outline.append({"title": title, "line": lineno})

                if len(outline) >= MAX_OUTLINE_ENTRIES:
                    outline.append({"truncated": True})
                    break
    except Exception:
        return []

    return outline

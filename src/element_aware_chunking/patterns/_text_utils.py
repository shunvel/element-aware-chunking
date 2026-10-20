from __future__ import annotations

import re

DEFAULT_CHUNK_CHARS = 800
DEFAULT_OVERLAP_CHARS = 120


def split_fixed_windows(text: str, size: int, overlap: int) -> list[tuple[str, tuple[int, int]]]:
    if not text:
        return []
    chunks: list[tuple[str, tuple[int, int]]] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        chunks.append((text[start:end], (start, end)))
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks


_HEADING_RE = re.compile(r"^(#{1,6}\s+.+|[A-Z][A-Za-z0-9 ,\-]{2,60}$)", re.MULTILINE)


def split_recursive(text: str, max_chars: int = DEFAULT_CHUNK_CHARS) -> list[str]:
    separators = ["\n\n", "\n", ". ", " "]
    return _recursive_split(text, separators, max_chars)


def _recursive_split(text: str, separators: list[str], max_chars: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    if not separators:
        return split_fixed_windows(text, max_chars, DEFAULT_OVERLAP_CHARS // 2)

    sep = separators[0]
    parts = text.split(sep)
    if len(parts) == 1:
        return _recursive_split(text, separators[1:], max_chars)

    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = part if not current else current + sep + part
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(part) > max_chars:
                chunks.extend(_recursive_split(part, separators[1:], max_chars))
                current = ""
            else:
                current = part
    if current:
        chunks.append(current)
    return chunks


def infer_heading_path(text: str) -> list[str]:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return [re.sub(r"^#+\s*", "", line)]
        if _HEADING_RE.match(line):
            return [line]
    return []

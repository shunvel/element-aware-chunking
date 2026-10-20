from __future__ import annotations

import os
from pathlib import Path

from element_aware_chunking.parsers.base import BaseParser
from element_aware_chunking.parsers.docling_parser import DoclingParser
from element_aware_chunking.parsers.pymupdf_parser import PyMuPDFParser


def get_parser(backend: str | None = None) -> BaseParser:
    backend = (backend or os.getenv("PARSER_BACKEND", "docling")).lower()
    if backend == "pymupdf":
        return PyMuPDFParser()
    return DoclingParser()

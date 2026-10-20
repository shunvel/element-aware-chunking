from __future__ import annotations

from element_aware_chunking.models import Chunk, Document
from element_aware_chunking.patterns._text_utils import infer_heading_path, split_recursive
from element_aware_chunking.patterns.base import BaseChunker


class RecursiveChunker(BaseChunker):
    pattern_name = "recursive"

    def __init__(self, max_chars: int = 800):
        self.max_chars = max_chars

    def chunk(self, document: Document) -> list[Chunk]:
        text = document.full_text or "\n".join(e.text for e in document.elements if e.text)
        heading_path = infer_heading_path(text)
        chunks: list[Chunk] = []
        for part in split_recursive(text, self.max_chars):
            chunks.append(
                Chunk(
                    text=part,
                    pattern=self.pattern_name,
                    source_file=document.source_file,
                    element_type="text",
                    metadata={"heading_path": heading_path},
                )
            )
        return chunks

from __future__ import annotations

from element_aware_chunking.models import Chunk, Document
from element_aware_chunking.patterns._text_utils import (
    DEFAULT_CHUNK_CHARS,
    DEFAULT_OVERLAP_CHARS,
    split_fixed_windows,
)
from element_aware_chunking.patterns.base import BaseChunker


class FixedSizeChunker(BaseChunker):
    pattern_name = "fixed"

    def __init__(self, chunk_chars: int = DEFAULT_CHUNK_CHARS, overlap: int = DEFAULT_OVERLAP_CHARS):
        self.chunk_chars = chunk_chars
        self.overlap = overlap

    def chunk(self, document: Document) -> list[Chunk]:
        text = document.full_text or "\n".join(e.text for e in document.elements if e.text)
        chunks: list[Chunk] = []
        for part, span in split_fixed_windows(text, self.chunk_chars, self.overlap):
            chunks.append(
                Chunk(
                    text=part,
                    pattern=self.pattern_name,
                    source_file=document.source_file,
                    element_type="mixed",
                    metadata={"char_span": span},
                )
            )
        return chunks

from __future__ import annotations

from element_aware_chunking.models import Chunk, Document
from element_aware_chunking.patterns.base import BaseChunker


class PageLevelChunker(BaseChunker):
    pattern_name = "page"

    def chunk(self, document: Document) -> list[Chunk]:
        page_images = document.metadata.get("page_images", {})
        pages = document.page_count or max((e.page_number for e in document.elements), default=1)
        chunks: list[Chunk] = []
        for page in range(1, pages + 1):
            text = document.text_by_page(page)
            if not text.strip():
                continue
            chunks.append(
                Chunk(
                    text=text,
                    pattern=self.pattern_name,
                    source_file=document.source_file,
                    page_number=page,
                    element_type="page",
                    metadata={
                        "page_image_path": page_images.get(page),
                    },
                )
            )
        return chunks

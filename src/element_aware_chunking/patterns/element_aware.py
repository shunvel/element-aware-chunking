from __future__ import annotations

from element_aware_chunking.models import Chunk, Document, ElementType
from element_aware_chunking.patterns.base import BaseChunker


class ElementAwareChunker(BaseChunker):
    pattern_name = "element"

    def chunk(self, document: Document) -> list[Chunk]:
        chunks: list[Chunk] = []
        for el in document.elements:
            text = el.text.strip()
            if el.element_type == ElementType.IMAGE:
                text = el.image_caption or el.text or "[image]"
            if not text and el.element_type != ElementType.IMAGE:
                continue

            meta: dict = {
                "heading_path": el.heading_path,
                "reading_order": el.reading_order,
            }
            if el.bbox:
                meta["bbox"] = el.bbox.model_dump()
            if el.table_markdown:
                meta["table_markdown"] = el.table_markdown
            if el.image_path:
                meta["image_path"] = el.image_path
            if el.image_caption:
                meta["image_caption"] = el.image_caption

            chunks.append(
                Chunk(
                    text=text,
                    pattern=self.pattern_name,
                    source_file=document.source_file,
                    page_number=el.page_number,
                    element_type=el.element_type.value,
                    metadata=meta,
                )
            )
        return chunks

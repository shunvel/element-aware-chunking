from __future__ import annotations

from element_aware_chunking.models import Chunk, Document, ElementType
from element_aware_chunking.patterns._text_utils import split_recursive
from element_aware_chunking.patterns.base import BaseChunker


class HierarchicalChunker(BaseChunker):
    pattern_name = "hierarchical"

    def __init__(self, child_max_chars: int = 400, parent_max_chars: int = 1600):
        self.child_max_chars = child_max_chars
        self.parent_max_chars = parent_max_chars

    def chunk(self, document: Document) -> list[Chunk]:
        """Emit child chunks for retrieval; parent chunks linked via parent_id for context."""
        parents: list[Chunk] = []
        children: list[Chunk] = []

        by_page: dict[int, list] = {}
        for el in document.elements:
            by_page.setdefault(el.page_number, []).append(el)

        for page, els in sorted(by_page.items()):
            parent_text_parts: list[str] = []
            for el in els:
                if el.element_type == ElementType.TABLE:
                    parent_text_parts.append(el.table_markdown or el.text)
                elif el.element_type == ElementType.IMAGE:
                    parent_text_parts.append(el.image_caption or "[figure]")
                elif el.text.strip():
                    parent_text_parts.append(el.text.strip())

            parent_body = "\n\n".join(parent_text_parts)
            if not parent_body.strip():
                continue

            for parent_part in split_recursive(parent_body, self.parent_max_chars):
                parent = Chunk(
                    text=parent_part,
                    pattern=self.pattern_name,
                    source_file=document.source_file,
                    page_number=page,
                    element_type="mixed",
                    metadata={"role": "parent"},
                )
                parents.append(parent)

                child_ids: list[str] = []
                for child_part in split_recursive(parent_part, self.child_max_chars):
                    child = Chunk(
                        text=child_part,
                        pattern=self.pattern_name,
                        source_file=document.source_file,
                        page_number=page,
                        element_type="text",
                        metadata={"role": "child", "parent_id": parent.id},
                    )
                    child_ids.append(child.id)
                    children.append(child)
                parent.metadata["child_ids"] = child_ids

        return parents + children

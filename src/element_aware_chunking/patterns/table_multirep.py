from __future__ import annotations

from element_aware_chunking.models import Chunk, Document, ElementType
from element_aware_chunking.patterns.base import BaseChunker


def linearize_table(headers: list[str] | None, markdown: str, max_rows: int = 8) -> str:
    lines = [ln for ln in markdown.splitlines() if ln.strip()]
    if headers:
        header_line = " | ".join(headers)
        return f"Table columns: {header_line}. Preview: {' '.join(lines[:max_rows])}"
    return f"Table preview: {' '.join(lines[:max_rows])}"


class TableMultiRepChunker(BaseChunker):
    pattern_name = "table_multirep"

    def chunk(self, document: Document) -> list[Chunk]:
        chunks: list[Chunk] = []
        section_context = ""

        for el in document.elements:
            if el.element_type == ElementType.TEXT and el.text.strip():
                if len(el.text) < 200:
                    section_context = el.text.strip()
                continue

            if el.element_type != ElementType.TABLE:
                continue

            md = el.table_markdown or el.text
            summary = linearize_table(el.table_headers, md)
            embed_text = f"{section_context}\n{summary}".strip() if section_context else summary

            meta: dict = {
                "table_markdown": md,
                "table_headers": el.table_headers or [],
                "parent_section": section_context,
                "representation": "table_summary",
            }
            if el.bbox:
                meta["bbox"] = el.bbox.model_dump()

            chunks.append(
                Chunk(
                    text=embed_text,
                    pattern=self.pattern_name,
                    source_file=document.source_file,
                    page_number=el.page_number,
                    element_type="table",
                    metadata=meta,
                )
            )

        if not chunks:
            for el in document.elements:
                if el.element_type == ElementType.TEXT and el.text.strip():
                    chunks.append(
                        Chunk(
                            text=el.text,
                            pattern=self.pattern_name,
                            source_file=document.source_file,
                            page_number=el.page_number,
                            element_type="text",
                            metadata={"note": "no_tables_found_fallback_text"},
                        )
                    )
        return chunks

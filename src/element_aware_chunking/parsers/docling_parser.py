from __future__ import annotations

from pathlib import Path

from element_aware_chunking.models import BBox, Document, Element, ElementType
from element_aware_chunking.parsers.base import BaseParser
from element_aware_chunking.parsers.layout_utils import extract_page_images
from element_aware_chunking.parsers.pymupdf_parser import PyMuPDFParser


class DoclingParser(BaseParser):
    """Docling-backed parser; falls back to PyMuPDF if docling is unavailable."""

    name = "docling"

    def parse(self, path: Path, processed_dir: Path | None = None) -> Document:
        try:
            from docling.document_converter import DocumentConverter
        except ImportError:
            return PyMuPDFParser().parse(path, processed_dir)

        path = path.resolve()
        processed = processed_dir or path.parent / "processed"
        page_images = extract_page_images(path, processed)

        converter = DocumentConverter()
        result = converter.convert(str(path))
        dl_doc = result.document

        elements: list[Element] = []
        order = 0
        full_parts: list[str] = []

        for item, _level in dl_doc.iterate_items():
            label = getattr(item, "label", None)
            text = getattr(item, "text", None) or ""
            if hasattr(item, "export_to_markdown"):
                try:
                    text = item.export_to_markdown() or text
                except Exception:
                    pass

            page_number = 1
            prov = getattr(item, "prov", None)
            if prov and len(prov) > 0:
                page_number = getattr(prov[0], "page_no", 1) or 1

            bbox = None
            if prov and len(prov) > 0 and getattr(prov[0], "bbox", None):
                b = prov[0].bbox
                bbox = BBox(x0=b.l, y0=b.t, x1=b.r, y1=b.b)

            element_type = ElementType.TEXT
            label_str = str(label).lower() if label else ""
            if "table" in label_str:
                element_type = ElementType.TABLE
            elif "picture" in label_str or "figure" in label_str:
                element_type = ElementType.IMAGE

            if not str(text).strip() and element_type == ElementType.TEXT:
                continue

            el = Element(
                element_type=element_type,
                text=str(text).strip(),
                page_number=int(page_number),
                reading_order=order,
                bbox=bbox,
                table_markdown=str(text) if element_type == ElementType.TABLE else None,
            )
            elements.append(el)
            if el.text:
                full_parts.append(el.text)
            order += 1

        if not elements:
            return PyMuPDFParser().parse(path, processed_dir)

        return Document(
            source_file=str(path),
            elements=elements,
            full_text="\n\n".join(full_parts),
            page_count=len(page_images) or max((e.page_number for e in elements), default=1),
            metadata={"page_images": page_images, "parser": self.name},
        )

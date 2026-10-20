from __future__ import annotations

from pathlib import Path

import fitz

from element_aware_chunking.models import BBox, Document, Element, ElementType
from element_aware_chunking.parsers.base import BaseParser
from element_aware_chunking.parsers.layout_utils import (
    associate_caption,
    extract_page_images,
    normalize_bbox,
)


class PyMuPDFParser(BaseParser):
    name = "pymupdf"

    def parse(self, path: Path, processed_dir: Path | None = None) -> Document:
        path = path.resolve()
        processed = processed_dir or path.parent / "processed"
        page_images = extract_page_images(path, processed)

        doc = fitz.open(path)
        elements: list[Element] = []
        order = 0
        full_parts: list[str] = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_number = page_idx + 1

            blocks = page.get_text("dict").get("blocks", [])
            text_blocks: list[Element] = []
            for block in blocks:
                if block.get("type") != 0:
                    continue
                lines = []
                for line in block.get("lines", []):
                    spans = [s.get("text", "") for s in line.get("spans", [])]
                    lines.append("".join(spans))
                text = "\n".join(lines).strip()
                if not text:
                    continue
                bbox = normalize_bbox(block["bbox"])
                el = Element(
                    element_type=ElementType.TEXT,
                    text=text,
                    page_number=page_number,
                    reading_order=order,
                    bbox=bbox,
                )
                elements.append(el)
                text_blocks.append(el)
                full_parts.append(text)
                order += 1

            for img in page.get_images(full=True):
                xref = img[0]
                rects = page.get_image_rects(xref)
                if not rects:
                    continue
                bbox = normalize_bbox(rects[0])
                img_dir = processed / path.stem / "images"
                img_dir.mkdir(parents=True, exist_ok=True)
                img_path = img_dir / f"p{page_number}_xref{xref}.png"
                if not img_path.exists():
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha > 3:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    pix.save(str(img_path))
                el = Element(
                    element_type=ElementType.IMAGE,
                    text="",
                    page_number=page_number,
                    reading_order=order,
                    bbox=bbox,
                    image_path=str(img_path),
                )
                caption = associate_caption(el, text_blocks)
                if caption:
                    el.image_caption = caption
                    el.text = caption
                elements.append(el)
                order += 1

            try:
                tables = page.find_tables()
            except Exception:
                tables = None
            if tables:
                for table in tables.tables:
                    try:
                        md = table.to_markdown()
                    except Exception:
                        md = str(table.extract())
                    if not md or not str(md).strip():
                        continue
                    bbox = None
                    if hasattr(table, "bbox"):
                        bbox = normalize_bbox(table.bbox)
                    headers: list[str] = []
                    data = table.extract()
                    if data and data[0]:
                        headers = [str(c) for c in data[0] if c]
                    el = Element(
                        element_type=ElementType.TABLE,
                        text=str(md),
                        page_number=page_number,
                        reading_order=order,
                        bbox=bbox,
                        table_markdown=str(md),
                        table_headers=headers or None,
                    )
                    elements.append(el)
                    full_parts.append(str(md))
                    order += 1

        doc.close()

        return Document(
            source_file=str(path),
            elements=sorted(elements, key=lambda e: (e.page_number, e.reading_order)),
            full_text="\n\n".join(full_parts),
            page_count=len(page_images),
            metadata={"page_images": page_images, "parser": self.name},
        )

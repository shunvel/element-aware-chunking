from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ElementType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    MIXED = "mixed"
    PAGE = "page"


class BBox(BaseModel):
    """Bounding box in PDF page coordinates (origin top-left)."""

    x0: float
    y0: float
    x1: float
    y1: float

    def to_tuple(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


class Element(BaseModel):
    element_type: ElementType
    text: str = ""
    page_number: int
    reading_order: int = 0
    bbox: BBox | None = None
    heading_path: list[str] = Field(default_factory=list)
    table_markdown: str | None = None
    table_headers: list[str] | None = None
    image_path: str | None = None
    image_caption: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    source_file: str
    elements: list[Element] = Field(default_factory=list)
    full_text: str = ""
    page_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    def text_by_page(self, page_number: int) -> str:
        parts = [e.text for e in self.elements if e.page_number == page_number and e.text]
        return "\n".join(parts)


class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    pattern: str
    source_file: str
    page_number: int | None = None
    element_type: str = "text"
    metadata: dict[str, Any] = Field(default_factory=dict)

    def with_metadata(self, **kwargs: Any) -> Chunk:
        merged = {**self.metadata, **kwargs}
        return self.model_copy(update={"metadata": merged})

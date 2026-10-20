from __future__ import annotations

import math
from pathlib import Path

import fitz

from element_aware_chunking.models import BBox, Element, ElementType


def normalize_bbox(rect: fitz.Rect | tuple[float, float, float, float]) -> BBox:
    if isinstance(rect, fitz.Rect):
        return BBox(x0=rect.x0, y0=rect.y0, x1=rect.x1, y1=rect.y1)
    return BBox(x0=rect[0], y0=rect[1], x1=rect[2], y1=rect[3])


def bbox_center(bbox: BBox) -> tuple[float, float]:
    return ((bbox.x0 + bbox.x1) / 2, (bbox.y0 + bbox.y1) / 2)


def bbox_distance(a: BBox, b: BBox) -> float:
    ax, ay = bbox_center(a)
    bx, by = bbox_center(b)
    return math.hypot(ax - bx, ay - by)


def associate_caption(
    image_el: Element, text_candidates: list[Element], max_distance: float = 120.0
) -> str | None:
    """Pick nearest text block below or beside the image as a caption heuristic."""
    if not image_el.bbox:
        return None
    best: tuple[float, str] | None = None
    for cand in text_candidates:
        if cand.page_number != image_el.page_number or not cand.text.strip() or not cand.bbox:
            continue
        dist = bbox_distance(image_el.bbox, cand.bbox)
        if dist > max_distance:
            continue
        if best is None or dist < best[0]:
            best = (dist, cand.text.strip())
    return best[1] if best else None


def render_page_image(pdf_path: Path, page_number: int, out_dir: Path, dpi: int = 150) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{pdf_path.stem}_p{page_number}.png"
    if out_path.exists():
        return out_path
    doc = fitz.open(pdf_path)
    page = doc[page_number - 1]
    pix = page.get_pixmap(dpi=dpi)
    pix.save(str(out_path))
    doc.close()
    return out_path


def extract_page_images(pdf_path: Path, processed_dir: Path) -> dict[int, str]:
    doc = fitz.open(pdf_path)
    paths: dict[int, str] = {}
    img_dir = processed_dir / pdf_path.stem / "pages"
    for i in range(len(doc)):
        paths[i + 1] = str(render_page_image(pdf_path, i + 1, img_dir))
    doc.close()
    return paths

#!/usr/bin/env python3
"""Generate README screenshots under docs/assets/ (no browser required)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from element_aware_chunking.config import qdrant_url
import importlib.util

from element_aware_chunking.patterns import get_chunker
from element_aware_chunking.pipeline import parse_document

_gif = importlib.util.spec_from_file_location(
    "generate_demo_gif", ROOT / "scripts" / "generate_demo_gif.py"
)
_gif_mod = importlib.util.module_from_spec(_gif)
assert _gif.loader
_gif.loader.exec_module(_gif_mod)
compose_panel = _gif_mod.compose_panel

ASSETS = ROOT / "docs" / "assets"
PDF = ROOT / "data" / "raw" / "sample_product_manual.pdf"
PROCESSED = ROOT / "data" / "processed"


def _font(size: int = 16):
    for name in ("Helvetica.ttc", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def streamlit_compare_png() -> Path:
    document = parse_document(PDF, processed_dir=PROCESSED)
    page_number = 1
    page_images = document.metadata.get("page_images", {})
    page_path = page_images.get(page_number)
    if not page_path:
        raise SystemExit("Missing page image; run make samples")

    page_img = Image.open(page_path)
    fixed = get_chunker("fixed").chunk(document)
    element = get_chunker("element").chunk(document)

    left = compose_panel(page_img, "fixed (baseline)", fixed, page_number, "#e6194b", target_width=520)
    right = compose_panel(page_img, "element-aware", element, page_number, "#f58231", target_width=520)
    gap = 16
    header = 44
    title = Image.new("RGB", (left.width + gap + right.width, header), (18, 18, 22))
    draw = ImageDraw.Draw(title)
    draw.text(
        (12, 12),
        "Streamlit · Compare patterns · sample_product_manual.pdf · page 1",
        fill=(220, 220, 220),
        font=_font(15),
    )
    body = Image.new("RGB", (left.width + gap + right.width, left.height), (18, 18, 22))
    body.paste(left, (0, 0))
    body.paste(right, (left.width + gap, 0))
    out = Image.new("RGB", (body.width, header + body.height), (18, 18, 22))
    out.paste(title, (0, 0))
    out.paste(body, (0, header))

    ASSETS.mkdir(parents=True, exist_ok=True)
    path = ASSETS / "streamlit-compare-patterns.png"
    out.save(path, optimize=True)
    return path


def qdrant_status_png() -> Path | None:
    url = qdrant_url()
    try:
        with urllib.request.urlopen(f"{url}/collections", timeout=3) as resp:
            collections_payload = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError):
        return None

    names = [c.get("name", "?") for c in collections_payload.get("result", {}).get("collections", [])]
    highlight = "element_aware_chunks"
    detail = ""
    if highlight in names:
        try:
            with urllib.request.urlopen(f"{url}/collections/{highlight}", timeout=3) as resp:
                detail = json.dumps(json.loads(resp.read().decode()), indent=2)[:1200]
        except (urllib.error.URLError, TimeoutError, OSError):
            detail = "(collection present; detail unavailable)"

    w, h = 900, 520
    img = Image.new("RGB", (w, h), (24, 26, 32))
    draw = ImageDraw.Draw(img)
    font = _font(16)
    small = _font(13)
    draw.text((20, 20), "Qdrant · localhost collections", fill=(240, 240, 240), font=font)
    y = 56
    for name in names:
        color = (255, 140, 60) if name == highlight else (180, 180, 180)
        draw.text((28, y), f"• {name}", fill=color, font=small)
        y += 22
    draw.text((20, y + 12), f"Detail: {highlight}", fill=(200, 200, 200), font=small)
    for i, line in enumerate(detail.splitlines()[:18]):
        draw.text((28, y + 40 + i * 16), line[:100], fill=(140, 145, 155), font=_font(11))

    path = ASSETS / "qdrant-collections.png"
    img.save(path, optimize=True)
    return path


def main() -> None:
    p1 = streamlit_compare_png()
    print(f"wrote {p1}")
    p2 = qdrant_status_png()
    if p2:
        print(f"wrote {p2}")
    else:
        print("skip qdrant-collections.png (Qdrant not reachable)")


if __name__ == "__main__":
    main()

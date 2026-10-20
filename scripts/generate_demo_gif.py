#!/usr/bin/env python3
"""Build docs/assets/demo.gif — same page, fixed vs element overlays (~30s loop)."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from element_aware_chunking.patterns import get_chunker
from element_aware_chunking.pipeline import parse_document

OUT = ROOT / "docs" / "assets" / "demo.gif"
PATTERNS = ("fixed", "element")
FRAME_MS = 2000  # 15 frames × 2s ≈ 30s


def _load_font(size: int = 18):
    for name in ("Helvetica.ttc", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_overlay(base: Image.Image, chunks, page_number: int, color: str) -> Image.Image:
    img = base.copy().convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    for chunk in chunks:
        if chunk.page_number != page_number:
            continue
        bbox = chunk.metadata.get("bbox")
        if not bbox:
            continue
        draw.rectangle(
            [bbox["x0"], bbox["y0"], bbox["x1"], bbox["y1"]],
            outline=color,
            width=3,
        )
    return Image.alpha_composite(img, overlay).convert("RGB")


def compose_panel(
    page_img: Image.Image,
    label: str,
    chunks,
    page_number: int,
    color: str,
    target_width: int = 480,
) -> Image.Image:
    ratio = target_width / page_img.width
    h = int(page_img.height * ratio)
    resized = page_img.resize((target_width, h), Image.Resampling.LANCZOS)
    if chunks:
        # scale bbox for resize
        scaled_chunks = []
        for c in chunks:
            bbox = c.metadata.get("bbox")
            if not bbox:
                scaled_chunks.append(c)
                continue
            meta = dict(c.metadata)
            meta["bbox"] = {
                k: v * ratio for k, v in bbox.items()
            }
            scaled_chunks.append(c.model_copy(update={"metadata": meta}))
        panel = draw_overlay(resized, scaled_chunks, page_number, color)
    else:
        panel = resized.convert("RGB")

    font = _load_font(20)
    header_h = 36
    out = Image.new("RGB", (target_width, h + header_h), (24, 24, 28))
    out.paste(panel, (0, header_h))
    draw = ImageDraw.Draw(out)
    draw.text((12, 8), label, fill=color, font=font)
    return out


def main() -> None:
    raw = ROOT / "data" / "raw"
    pdf = raw / "sample_product_manual.pdf"
    if not pdf.exists():
        raise SystemExit("Run: make samples")

    document = parse_document(pdf, processed_dir=ROOT / "data" / "processed")
    page_number = 1
    page_images = document.metadata.get("page_images", {})
    page_path = page_images.get(page_number)
    if not page_path or not Path(page_path).exists():
        raise SystemExit("Page image missing; re-run parsing.")

    page_img = Image.open(page_path)
    fixed_chunks = get_chunker("fixed").chunk(document)
    element_chunks = get_chunker("element").chunk(document)

    left = compose_panel(page_img, "fixed (baseline)", fixed_chunks, page_number, "#e6194b")
    right = compose_panel(page_img, "element-aware", element_chunks, page_number, "#f58231")
    gap = 12
    combined_h = max(left.height, right.height)
    combined = Image.new("RGB", (left.width + gap + right.width, combined_h), (18, 18, 22))
    combined.paste(left, (0, 0))
    combined.paste(right, (left.width + gap, 0))

    # Alternate emphasis: full side-by-side + single-pattern zoom frames
    frames: list[Image.Image] = []
    sequence = [
        ("fixed", fixed_chunks, "#e6194b"),
        ("element", element_chunks, "#f58231"),
    ]
    for _ in range(5):  # 5 × (fixed + element + side-by-side) × 2s ≈ 30s
        for name, chunks, color in sequence:
            single = compose_panel(page_img, name, chunks, page_number, color, target_width=720)
            frames.append(single)
        frames.append(combined)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
    )
    print(f"wrote {OUT} ({len(frames)} frames, ~{len(frames) * FRAME_MS / 1000:.0f}s)")


if __name__ == "__main__":
    main()

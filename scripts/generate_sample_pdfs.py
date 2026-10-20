#!/usr/bin/env python3
"""Create permissively licensed sample PDFs under data/raw/ (no network)."""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz

OUT = Path("data/raw")


def _write_pdf(name: str, builder) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    doc = fitz.open()
    builder(doc)
    doc.save(path)
    doc.close()
    print(f"wrote {path}")
    return path


def financial_report(doc: fitz.Document) -> None:
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Annual Report — Financial Highlights", fontsize=14)
    page.insert_text((50, 80), "Footnote: All figures in USD millions.", fontsize=9)
    rect = fitz.Rect(50, 100, 545, 220)
    page.draw_rect(rect, color=(0, 0, 0), width=0.5)
    rows = [
        ["Metric", "FY2024", "FY2025", "YoY %"],
        ["Revenue", "1,240", "1,388", "12%"],
        ["Operating margin", "18.2", "19.1", "0.9pp"],
        ["Free cash flow", "210", "245", "16.7%"],
    ]
    y = 110
    for row in rows:
        line = " | ".join(row)
        page.insert_text((60, y), line, fontsize=10)
        y += 22


def scientific_paper(doc: fitz.Document) -> None:
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "DocLayNet: A Large Human-Annotated Layout Dataset", fontsize=12)
    page.insert_text((50, 75), "Abstract", fontsize=11)
    col1 = (
        "We present a benchmark for document layout analysis. "
        "Models must detect titles, lists, tables, and figures."
    )
    col2 = (
        "Figure 1 shows label distributions. Table 1 reports mAP scores "
        "for baseline detectors on the validation split."
    )
    page.insert_text((50, 95), col1, fontsize=9)
    page.insert_text((310, 95), col2, fontsize=9)
    page.insert_text((50, 200), "Figure 1: Dataset composition by category.", fontsize=9)
    fig = fitz.Rect(50, 215, 280, 340)
    page.draw_rect(fig, color=(0.2, 0.2, 0.8), width=1)
    page.insert_text((55, 360), "EQUATION: F1 = 2PR / (P + R)", fontsize=9)


def product_manual(doc: fitz.Document) -> None:
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Product Manual — Installation", fontsize=14)
    steps = [
        "1. Mount the bracket using screws (M4).",
        "2. Connect the data cable to port J2.",
        "3. Apply 24V DC power; LED D1 should turn green.",
    ]
    y = 90
    for step in steps:
        page.insert_text((50, y), step, fontsize=10)
        y += 24
    page.insert_text((50, 180), "Parameter table", fontsize=11)
    params = [
        ["Parameter", "Min", "Max", "Unit"],
        ["Input voltage", "20", "28", "V DC"],
        ["Operating temp", "-10", "55", "C"],
    ]
    y = 200
    for row in params:
        page.insert_text((50, y), " | ".join(row), fontsize=10)
        y += 20
    shot = fitz.Rect(50, 280, 250, 400)
    page.draw_rect(shot, color=(0.5, 0.5, 0.5), fill=(0.9, 0.9, 0.9))
    page.insert_text((50, 415), "Screenshot: control panel (illustrative).", fontsize=9)


def slide_deck(doc: fitz.Document) -> None:
    page = doc.new_page(width=842, height=595)
    page.insert_text((40, 40), "Q4 Business Review", fontsize=20)
    boxes = [
        (40, 100, 250, 220, "Revenue +12%"),
        (300, 100, 510, 220, "New logos: 48"),
        (560, 100, 770, 220, "NPS: 62"),
    ]
    for x0, y0, x1, y1, label in boxes:
        page.draw_rect(fitz.Rect(x0, y0, x1, y1), color=(0, 0, 0), width=1)
        page.insert_text((x0 + 10, y0 + 40), label, fontsize=12)


def main() -> None:
    _write_pdf("sample_financial_report.pdf", lambda d: financial_report(d))
    _write_pdf("sample_scientific_paper.pdf", lambda d: scientific_paper(d))
    _write_pdf("sample_product_manual.pdf", lambda d: product_manual(d))
    _write_pdf("sample_slide_deck.pdf", lambda d: slide_deck(d))
    print("done")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from element_aware_chunking.patterns import ALL_PATTERN_NAMES
from element_aware_chunking.pipeline import ingest_file
from element_aware_chunking.qdrant_store import QdrantChunkStore

load_dotenv()


def main() -> None:
    raw_dir = Path("data/raw")
    pdfs = sorted(raw_dir.glob("*.pdf"))
    if not pdfs:
        print("No PDFs in data/raw. Run: uv run python scripts/download_samples.py")
        sys.exit(1)

    store = QdrantChunkStore()
    store.ensure_collection(recreate=False)

    for pdf in pdfs:
        for pattern in ALL_PATTERN_NAMES:
            print(f"ingest {pdf.name} pattern={pattern}")
            ingest_file(pdf, pattern, processed_dir=Path("data/processed"), store=store)

    print("ingest complete")


if __name__ == "__main__":
    main()

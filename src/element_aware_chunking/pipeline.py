from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from element_aware_chunking.models import Chunk, Document
from element_aware_chunking.parsers import get_parser
from element_aware_chunking.patterns import get_chunker
from element_aware_chunking.qdrant_store import QdrantChunkStore

load_dotenv()


def parse_document(path: Path, parser_backend: str | None = None, processed_dir: Path | None = None) -> Document:
    parser = get_parser(parser_backend)
    return parser.parse(path, processed_dir=processed_dir)


def chunk_document(document: Document, pattern: str) -> list[Chunk]:
    chunker = get_chunker(pattern)
    return chunker.chunk(document)


def save_chunks(chunks: list[Chunk], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [c.model_dump() for c in chunks]
    out_path.write_text(json.dumps(payload, indent=2))


def ingest_file(
    path: Path,
    pattern: str,
    *,
    parser_backend: str | None = None,
    processed_dir: Path | None = None,
    store: QdrantChunkStore | None = None,
    save_processed: bool = True,
) -> tuple[Document, list[Chunk]]:
    processed = processed_dir or Path("data/processed")
    document = parse_document(path, parser_backend, processed)
    chunks = chunk_document(document, pattern)

    if save_processed:
        out = processed / path.stem / f"chunks_{pattern}.json"
        save_chunks(chunks, out)

    if store is not None:
        store.upsert_chunks(chunks)

    return document, chunks

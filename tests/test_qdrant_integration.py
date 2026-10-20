from element_aware_chunking.models import Chunk
from element_aware_chunking.qdrant_store import QdrantChunkStore


def test_qdrant_upsert_and_search_memory():
    store = QdrantChunkStore(url=":memory:", collection="test_chunks")
    chunks = [
        Chunk(
            text="Revenue grew 12% year over year in Q4.",
            pattern="element",
            source_file="report.pdf",
            page_number=1,
            element_type="text",
        ),
        Chunk(
            text="| Metric | Value |\n| Revenue | 12% |",
            pattern="table_multirep",
            source_file="report.pdf",
            page_number=2,
            element_type="table",
            metadata={"table_markdown": "| Metric | Value |\n| Revenue | 12% |"},
        ),
    ]
    n = store.upsert_chunks(chunks)
    assert n == 2
    hits = store.search("revenue growth", limit=2, pattern="element")
    assert hits
    assert hits[0].payload["element_type"] == "text"

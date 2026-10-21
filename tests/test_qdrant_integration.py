from element_aware_chunking.models import Chunk
from element_aware_chunking.qdrant_store import QdrantChunkStore


def test_qdrant_upsert_and_search_memory(monkeypatch):
    """Keep the integration contract offline; model download is tested separately."""
    import element_aware_chunking.qdrant_store as store_module

    def fake_embed_chunks(chunks, _model_name=None):
        return {
            chunk.id: [1.0, 0.0] if "Revenue" in chunk.text else [0.0, 1.0]
            for chunk in chunks
        }

    monkeypatch.setattr(store_module, "embed_chunks", fake_embed_chunks)
    monkeypatch.setattr(store_module, "table_summary_vector", lambda *_args: None)
    monkeypatch.setattr(store_module, "vector_size", lambda *_args: 2)
    monkeypatch.setattr(
        "element_aware_chunking.embeddings.embed_texts",
        lambda _texts, _model_name=None: [[1.0, 0.0]],
    )

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

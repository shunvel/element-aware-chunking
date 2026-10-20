from __future__ import annotations

import os
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from element_aware_chunking.config import qdrant_url
from element_aware_chunking.embeddings import embed_chunks, table_summary_vector, vector_size
from element_aware_chunking.models import Chunk


TEXT_VECTOR = "text"
TABLE_SUMMARY_VECTOR = "table_summary"


class QdrantChunkStore:
    def __init__(
        self,
        url: str | None = None,
        collection: str | None = None,
        embedding_model: str | None = None,
    ):
        self.url = qdrant_url(url)
        self.collection = collection or os.getenv("QDRANT_COLLECTION", "element_aware_chunks")
        self.embedding_model = embedding_model
        self.client = QdrantClient(url=self.url) if self.url != ":memory:" else QdrantClient(":memory:")
        self._dim: int | None = None

    @property
    def dim(self) -> int:
        if self._dim is None:
            self._dim = vector_size(self.embedding_model)
        return self._dim

    def ensure_collection(self, recreate: bool = False) -> None:
        exists = self.client.collection_exists(self.collection)
        if exists and recreate:
            self.client.delete_collection(self.collection)
            exists = False
        if exists:
            return

        self.client.create_collection(
            collection_name=self.collection,
            vectors_config={
                TEXT_VECTOR: qm.VectorParams(size=self.dim, distance=qm.Distance.COSINE),
                TABLE_SUMMARY_VECTOR: qm.VectorParams(size=self.dim, distance=qm.Distance.COSINE),
            },
        )
        for field in ("element_type", "pattern", "source_file", "page_number"):
            self.client.create_payload_index(
                collection_name=self.collection,
                field_name=field,
                field_schema=qm.PayloadSchemaType.KEYWORD
                if field != "page_number"
                else qm.PayloadSchemaType.INTEGER,
            )

    def _payload(self, chunk: Chunk) -> dict[str, Any]:
        return {
            "chunk_id": chunk.id,
            "text": chunk.text,
            "pattern": chunk.pattern,
            "source_file": chunk.source_file,
            "page_number": chunk.page_number,
            "element_type": chunk.element_type,
            "metadata": chunk.metadata,
        }

    def upsert_chunks(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        self.ensure_collection()
        vectors = embed_chunks(chunks, self.embedding_model)
        points: list[qm.PointStruct] = []

        for chunk in chunks:
            vec_map: dict[str, list[float]] = {TEXT_VECTOR: vectors[chunk.id]}
            tvec = table_summary_vector(chunk, self.embedding_model)
            if tvec is not None:
                vec_map[TABLE_SUMMARY_VECTOR] = tvec

            points.append(
                qm.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec_map,
                    payload=self._payload(chunk),
                )
            )

        self.client.upsert(collection_name=self.collection, points=points)
        return len(points)

    def search(
        self,
        query: str,
        limit: int = 5,
        pattern: str | None = None,
        element_type: str | None = None,
        vector_name: str = TEXT_VECTOR,
    ) -> list[qm.ScoredPoint]:
        from element_aware_chunking.embeddings import embed_texts

        self.ensure_collection()
        query_vec = embed_texts([query], self.embedding_model)[0]
        must: list[qm.FieldCondition] = []
        if pattern:
            must.append(qm.FieldCondition(key="pattern", match=qm.MatchValue(value=pattern)))
        if element_type:
            must.append(
                qm.FieldCondition(key="element_type", match=qm.MatchValue(value=element_type))
            )
        query_filter = qm.Filter(must=must) if must else None

        response = self.client.query_points(
            collection_name=self.collection,
            query=query_vec,
            using=vector_name,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        return list(response.points)

    def fetch_parent_context(self, parent_id: str, limit: int = 1) -> list[dict[str, Any]]:
        results, _ = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=qm.Filter(
                must=[
                    qm.FieldCondition(
                        key="metadata.parent_id",
                        match=qm.MatchValue(value=parent_id),
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
        )
        return [p.payload for p in results if p.payload]

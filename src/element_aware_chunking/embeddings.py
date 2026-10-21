from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
from fastembed import TextEmbedding

from element_aware_chunking.models import Chunk


class EmbeddingModelUnavailableError(RuntimeError):
    """Raised when the configured embedding model cannot be loaded locally."""


@lru_cache(maxsize=1)
def get_text_embedder(model_name: str | None = None) -> TextEmbedding:
    name = model_name or os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    try:
        return TextEmbedding(model_name=name)
    except Exception as exc:
        raise EmbeddingModelUnavailableError(
            f"Could not load embedding model '{name}'. "
            "Set HF_TOKEN in .env (or log in with `huggingface-cli login`) and restart the app. "
            "Once downloaded, FastEmbed uses its local cache."
        ) from exc


def embed_texts(texts: list[str], model_name: str | None = None) -> list[list[float]]:
    if not texts:
        return []
    name = model_name or os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    try:
        model = get_text_embedder(name)
        vectors = list(model.embed(texts))
    except EmbeddingModelUnavailableError:
        raise
    except Exception as exc:
        raise EmbeddingModelUnavailableError(
            f"Could not embed with '{name}'. "
            "Check your network/Hugging Face authentication and restart Streamlit."
        ) from exc
    return [v.tolist() if hasattr(v, "tolist") else list(v) for v in vectors]


def embed_chunks(chunks: list[Chunk], model_name: str | None = None) -> dict[str, list[float]]:
    texts = [c.text for c in chunks]
    vectors = embed_texts(texts, model_name)
    return {chunk.id: vec for chunk, vec in zip(chunks, vectors, strict=True)}


def table_summary_vector(chunk: Chunk, model_name: str | None = None) -> list[float] | None:
    if chunk.element_type != "table" and chunk.pattern != "table_multirep":
        return None
    summary = chunk.metadata.get("table_markdown") or chunk.text
    return embed_texts([summary[:4000]], model_name)[0]


def vector_size(model_name: str | None = None) -> int:
    vec = embed_texts(["probe"], model_name)[0]
    return len(vec)

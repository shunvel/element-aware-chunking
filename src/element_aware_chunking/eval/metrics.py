from __future__ import annotations

import math
from collections import defaultdict

from element_aware_chunking.models import Chunk


def substring_hit(retrieved_texts: list[str], evidence: str) -> bool:
    ev = evidence.strip().lower()
    if not ev:
        return False
    return any(ev in t.lower() for t in retrieved_texts)


def recall_at_k(hits: list[bool], k: int) -> float:
    if not hits:
        return 0.0
    return 1.0 if any(hits[:k]) else 0.0


def mrr(ranks: list[int | None]) -> float:
    if not ranks:
        return 0.0
    scores = [1.0 / r for r in ranks if r is not None]
    return sum(scores) / len(ranks) if ranks else 0.0


def ndcg_at_k(relevance: list[int], k: int) -> float:
    rel = relevance[:k]
    dcg = sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(rel))
    ideal = sorted(relevance, reverse=True)[:k]
    idcg = sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def table_block_integrity(chunks: list[Chunk], table_markdown: str) -> float:
    """Fraction of table markdown that appears intact in a single chunk."""
    if not table_markdown.strip():
        return 1.0
    for c in chunks:
        if table_markdown.strip() in c.text or c.metadata.get("table_markdown", "").strip() == table_markdown.strip():
            return 1.0
    return 0.0


def aggregate_by_key(
    records: list[dict],
    key: str,
) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        buckets[str(rec.get(key, "all"))].append(rec)

    out: dict[str, dict[str, float]] = {}
    for bucket, items in buckets.items():
        out[bucket] = {
            "recall@3": sum(i["recall@3"] for i in items) / len(items),
            "mrr": sum(i["mrr"] for i in items) / len(items),
            "count": float(len(items)),
        }
    return out

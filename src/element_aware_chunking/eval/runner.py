from __future__ import annotations

from pathlib import Path

from element_aware_chunking.embeddings import embed_texts
from element_aware_chunking.eval.dataset import EvalQuestion, load_eval_dataset
from element_aware_chunking.eval.metrics import aggregate_by_key, mrr, recall_at_k, substring_hit
from element_aware_chunking.patterns import ALL_PATTERN_NAMES
from element_aware_chunking.pipeline import chunk_document, parse_document


def rank_evidence(chunks: list, question: str, evidence: str, k: int = 5) -> tuple[bool, int | None]:
    texts = [c.text for c in chunks]
    if not texts:
        return False, None
    q_vec = embed_texts([question])[0]
    c_vecs = embed_texts(texts)
    scores = [sum(a * b for a, b in zip(q_vec, cv)) for cv in c_vecs]
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    top_texts = [texts[i] for i in ranked[:k]]
    hit = substring_hit(top_texts, evidence)
    rank = None
    ev = evidence.strip().lower()
    for pos, idx in enumerate(ranked, start=1):
        if ev in texts[idx].lower():
            rank = pos
            break
    return hit, rank


def run_eval(
    data_dir: Path = Path("data/raw"),
    processed_dir: Path = Path("data/processed"),
    eval_path: Path = Path("data/eval/questions.json"),
) -> dict:
    questions = load_eval_dataset(eval_path)
    if not questions:
        return {"error": "no eval questions", "by_pattern": {}, "by_element_type": {}}

    records: list[dict] = []
    for pattern in ALL_PATTERN_NAMES:
        for q in questions:
            doc_path = data_dir / Path(q.source_file).name
            if not doc_path.exists():
                continue
            document = parse_document(doc_path, processed_dir=processed_dir)
            chunks = chunk_document(document, pattern)
            hit, rank = rank_evidence(chunks, q.question, q.evidence_text)
            records.append(
                {
                    "pattern": pattern,
                    "element_type": q.element_type,
                    "recall@3": 1.0 if hit else 0.0,
                    "mrr": (1.0 / rank) if rank else 0.0,
                    "question_id": q.id,
                }
            )

    return {
        "by_pattern": aggregate_by_key(records, "pattern"),
        "by_element_type": aggregate_by_key(records, "element_type"),
        "records": records,
    }

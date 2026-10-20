from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class EvalQuestion(BaseModel):
    id: str
    question: str
    source_file: str
    evidence_text: str
    element_type: str = Field(description="text | table | image")
    page_number: int | None = None


def load_eval_dataset(path: Path | None = None) -> list[EvalQuestion]:
    path = path or Path("data/eval/questions.json")
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return [EvalQuestion.model_validate(item) for item in data]

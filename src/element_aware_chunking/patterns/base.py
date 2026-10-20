from __future__ import annotations

from abc import ABC, abstractmethod

from element_aware_chunking.models import Chunk, Document


class BaseChunker(ABC):
    pattern_name: str = "base"

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        ...

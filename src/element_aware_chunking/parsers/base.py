from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from element_aware_chunking.models import Document


class BaseParser(ABC):
    name: str = "base"

    @abstractmethod
    def parse(self, path: Path, processed_dir: Path | None = None) -> Document:
        """Parse a file into a layout-aware Document."""

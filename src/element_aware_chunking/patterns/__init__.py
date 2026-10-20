from __future__ import annotations

from element_aware_chunking.patterns.base import BaseChunker
from element_aware_chunking.patterns.element_aware import ElementAwareChunker
from element_aware_chunking.patterns.fixed import FixedSizeChunker
from element_aware_chunking.patterns.hierarchical import HierarchicalChunker
from element_aware_chunking.patterns.page import PageLevelChunker
from element_aware_chunking.patterns.recursive import RecursiveChunker
from element_aware_chunking.patterns.table_multirep import TableMultiRepChunker

PATTERN_REGISTRY: dict[str, BaseChunker] = {
    "fixed": FixedSizeChunker(),
    "recursive": RecursiveChunker(),
    "page": PageLevelChunker(),
    "element": ElementAwareChunker(),
    "table_multirep": TableMultiRepChunker(),
    "hierarchical": HierarchicalChunker(),
}

ALL_PATTERN_NAMES = list(PATTERN_REGISTRY.keys())


def get_chunker(pattern: str) -> BaseChunker:
    if pattern not in PATTERN_REGISTRY:
        raise KeyError(f"Unknown pattern: {pattern}. Choose from {ALL_PATTERN_NAMES}")
    return PATTERN_REGISTRY[pattern]

from element_aware_chunking.models import BBox, Document, Element, ElementType
from element_aware_chunking.patterns import ALL_PATTERN_NAMES, get_chunker
from element_aware_chunking.patterns.table_multirep import TableMultiRepChunker
from element_aware_chunking.eval.metrics import table_block_integrity


def _sample_document() -> Document:
    table_md = "| Col A | Col B |\n| --- | --- |\n| 1 | 2 |"
    return Document(
        source_file="sample.pdf",
        page_count=1,
        full_text="Introduction\n\n" + table_md,
        elements=[
            Element(
                element_type=ElementType.TEXT,
                text="Introduction",
                page_number=1,
                reading_order=0,
                bbox=BBox(x0=10, y0=10, x1=100, y1=30),
            ),
            Element(
                element_type=ElementType.TABLE,
                text=table_md,
                page_number=1,
                reading_order=1,
                bbox=BBox(x0=10, y0=40, x1=200, y1=120),
                table_markdown=table_md,
                table_headers=["Col A", "Col B"],
            ),
        ],
    )


def test_all_patterns_emit_chunks():
    doc = _sample_document()
    for name in ALL_PATTERN_NAMES:
        chunks = get_chunker(name).chunk(doc)
        assert len(chunks) >= 1
        assert chunks[0].pattern == name


def test_element_aware_never_splits_table():
    doc = _sample_document()
    chunks = get_chunker("element").chunk(doc)
    table_chunks = [c for c in chunks if c.element_type == "table"]
    assert len(table_chunks) == 1
    assert "| Col A |" in table_chunks[0].text


def test_table_integrity_metric():
    doc = _sample_document()
    chunks = TableMultiRepChunker().chunk(doc)
    md = doc.elements[1].table_markdown or ""
    assert table_block_integrity(chunks, md) == 1.0


def test_hierarchical_parent_child_links():
    doc = _sample_document()
    chunks = get_chunker("hierarchical").chunk(doc)
    parents = [c for c in chunks if c.metadata.get("role") == "parent"]
    children = [c for c in chunks if c.metadata.get("role") == "child"]
    assert parents
    assert children
    assert all(c.metadata.get("parent_id") for c in children)

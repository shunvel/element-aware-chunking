from __future__ import annotations

from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw

from element_aware_chunking.models import Chunk
from element_aware_chunking.patterns import ALL_PATTERN_NAMES
from element_aware_chunking.pipeline import chunk_document, parse_document
from element_aware_chunking.qdrant_store import QdrantChunkStore

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
DEMO_PDF = "sample_product_manual.pdf"

PATTERN_COLORS = {
    "fixed": "#e6194b",
    "recursive": "#3cb44b",
    "page": "#4363d8",
    "element": "#f58231",
    "table_multirep": "#911eb4",
    "hierarchical": "#42d4f4",
}

PATTERN_LABELS = {
    "fixed": "Fixed-size (baseline)",
    "recursive": "Recursive / structure",
    "page": "Page-level",
    "element": "Element-aware",
    "table_multirep": "Table multi-rep",
    "hierarchical": "Hierarchical parent/child",
}

PATTERN_HINTS = {
    "fixed": "Blind character windows — often splits tables and steps mid-line.",
    "recursive": "Splits on paragraphs/lines — still ignores layout boxes.",
    "page": "One chunk = whole page text (good for slides).",
    "element": "One chunk per text block, table, or figure region (recommended).",
    "table_multirep": "Tables get a summary for embedding + full markdown in metadata.",
    "hierarchical": "Small child chunks linked to larger parent chunks for context.",
}


st.set_page_config(
    page_title="Element-Aware Chunking",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.25rem; padding-bottom: 1rem; max-width: 1280px; }
    h1 { font-size: 1.65rem !important; margin-bottom: 0.25rem !important; }
    [data-testid="stMetric"] { background: rgba(255,255,255,0.03); padding: 0.5rem 0.75rem; border-radius: 8px; }
    .chunk-card {
        border-left: 3px solid #f58231;
        padding: 0.5rem 0.75rem;
        margin: 0.35rem 0;
        background: rgba(128,128,128,0.08);
        border-radius: 0 6px 6px 0;
        font-size: 0.88rem;
        line-height: 1.45;
    }
    .chunk-meta { color: #888; font-size: 0.78rem; margin-bottom: 0.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Parsing document…")
def cached_parse(pdf_path: str, processed: str):
    return parse_document(Path(pdf_path), processed_dir=Path(processed))


@st.cache_data(show_spinner="Chunking…")
def cached_chunk(pdf_path: str, processed: str, pattern: str):
    document = cached_parse(pdf_path, processed)
    return chunk_document(document, pattern)


def draw_chunk_overlay(page_image: Path, chunks: list[Chunk], page_number: int, color: str) -> Image.Image:
    img = Image.open(page_image).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    idx = 0
    for chunk in chunks:
        if chunk.page_number != page_number:
            continue
        bbox = chunk.metadata.get("bbox")
        if not bbox:
            continue
        idx += 1
        x0, y0, x1, y1 = bbox["x0"], bbox["y0"], bbox["x1"], bbox["y1"]
        draw.rectangle([x0, y0, x1, y1], outline=color, width=3)
        draw.text((x0 + 2, y0 + 2), str(idx), fill=color)

    return Image.alpha_composite(img, overlay).convert("RGB")


def display_width(img: Image.Image, max_width: int = 480) -> int:
    return min(img.size[0], max_width)


def chunks_for_page(chunks: list[Chunk], page_number: int, pattern: str) -> list[Chunk]:
    on_page = [c for c in chunks if c.page_number == page_number]
    if on_page:
        return on_page
    if pattern in ("fixed", "recursive"):
        return chunks
    return []


def render_chunk_list(chunks: list[Chunk], pattern: str, page_number: int, height: int = 400) -> None:
    page_chunks = chunks_for_page(chunks, page_number, pattern)
    if pattern in ("fixed", "recursive") and not any(c.page_number == page_number for c in chunks):
        st.caption("Document-wide chunks (not tied to page boxes).")
    if not page_chunks:
        st.caption("No chunks in this view.")
        return
    with st.container(height=height):
        for i, chunk in enumerate(page_chunks[:25], start=1):
            color = PATTERN_COLORS.get(chunk.pattern, "#888")
            preview = chunk.text.replace("\n", " ").strip()
            if len(preview) > 220:
                preview = preview[:220] + "…"
            st.markdown(
                f"""
                <div class="chunk-card" style="border-left-color: {color};">
                  <div class="chunk-meta">#{i} · {chunk.element_type}</div>
                  <div>{preview or "(empty)"}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_pattern_panel(
    pdf_path: Path,
    document,
    pattern: str,
    page_number: int,
    page_image: str | None,
) -> None:
    chunks = cached_chunk(str(pdf_path), str(PROCESSED_DIR), pattern)
    color = PATTERN_COLORS.get(pattern, "#fff")
    st.markdown(
        f"**{PATTERN_LABELS.get(pattern, pattern)}**  \n"
        f"<span style='color:{color}'>■</span> {len(chunks)} chunks total",
        unsafe_allow_html=True,
    )
    st.caption(PATTERN_HINTS.get(pattern, ""))

    if page_image and Path(page_image).exists():
        overlay = draw_chunk_overlay(Path(page_image), chunks, page_number, color)
        st.image(overlay, width=display_width(overlay))
    else:
        st.info("No page image.")

    render_chunk_list(chunks, pattern, page_number, height=320)


st.title("Element-Aware Chunking")
st.caption("See how each pattern splits the same PDF — boxes on the page + chunk text on the right.")

with st.expander("How to use this demo (localhost)", expanded=True):
    st.markdown(
        """
        1. Run from the repo root: `python3 -m streamlit run app/streamlit_app.py` → open **http://localhost:8501**
        2. Choose **Compare patterns** (sidebar) — start with **fixed** vs **element** on `sample_product_manual.pdf`, page **1**.
        3. **Colored boxes** = chunks with layout metadata (`element`, `page`, `table_multirep`).
        4. Switch patterns in the sidebar to see chunk count and text change for the same document.
        5. **Qdrant search** (bottom) works after `make ingest` — optional; overlays work without it.
        """
    )

pdfs = sorted(RAW_DIR.glob("*.pdf"))
if not pdfs:
    st.warning("No PDFs in `data/raw`. Run: `make samples`")
    st.stop()

default_pdf = next((p for p in pdfs if p.name == DEMO_PDF), pdfs[0])
default_idx = pdfs.index(default_pdf) if default_pdf in pdfs else 0

with st.sidebar:
    st.header("Controls")
    view_mode = st.radio("View", ["Compare patterns", "Single pattern"], index=0)
    pdf_path = st.selectbox("Document", pdfs, index=default_idx, format_func=lambda p: p.name)
    document = cached_parse(str(pdf_path), str(PROCESSED_DIR))
    max_page = max(document.page_count, 1)
    page_number = int(st.number_input("Page", min_value=1, max_value=max_page, value=1, step=1))

    if view_mode == "Compare patterns":
        pattern_a = st.selectbox("Pattern A", ALL_PATTERN_NAMES, index=ALL_PATTERN_NAMES.index("fixed"))
        pattern_b = st.selectbox("Pattern B", ALL_PATTERN_NAMES, index=ALL_PATTERN_NAMES.index("element"))
        pattern = pattern_a
    else:
        pattern = st.selectbox(
            "Pattern",
            ALL_PATTERN_NAMES,
            index=ALL_PATTERN_NAMES.index("element"),
            format_func=lambda p: PATTERN_LABELS.get(p, p),
        )

    st.divider()
    st.markdown(f"**Parser:** `{document.metadata.get('parser', '?')}`")
    st.markdown(f"**Pages:** {document.page_count}")

page_images = document.metadata.get("page_images", {})
page_image = page_images.get(page_number)

if view_mode == "Compare patterns":
    st.subheader(f"Same page · {pdf_path.name} · page {page_number}")
    col_a, col_b = st.columns(2)
    with col_a:
        render_pattern_panel(pdf_path, document, pattern_a, page_number, page_image)
    with col_b:
        render_pattern_panel(pdf_path, document, pattern_b, page_number, page_image)
else:
    chunks = cached_chunk(str(pdf_path), str(PROCESSED_DIR), pattern)
    page_chunks = chunks_for_page(chunks, page_number, pattern)
    bbox_count = sum(1 for c in page_chunks if c.metadata.get("bbox"))

    m1, m2, m3 = st.columns(3)
    m1.metric("Chunks (this view)", len(page_chunks))
    m2.metric("With bbox overlay", bbox_count)
    m3.metric("Total (pattern)", len(chunks))

    viz_col, list_col = st.columns(2, gap="large")
    color = PATTERN_COLORS.get(pattern, "#fff")

    with viz_col:
        st.subheader("Page preview")
        st.caption(PATTERN_HINTS.get(pattern, ""))
        if page_image and Path(page_image).exists():
            overlay = draw_chunk_overlay(Path(page_image), chunks, page_number, color)
            st.image(overlay, width=display_width(overlay, 520))
            if bbox_count == 0:
                st.caption("No boxes for this pattern — try **element** or **Compare patterns**.")
        else:
            st.info("No page image.")

    with list_col:
        st.subheader("Chunk text")
        render_chunk_list(chunks, pattern, page_number, height=520)

with st.expander("Qdrant search (after `make ingest`)", expanded=False):
    q_pattern = pattern if view_mode == "Single pattern" else pattern_b
    query = st.text_input("Query", key="qdrant_query", placeholder="e.g. input voltage")
    if query:
        try:
            store = QdrantChunkStore()
            hits = store.search(query, limit=5, pattern=q_pattern)
            if not hits:
                st.caption("No hits.")
            for hit in hits:
                payload = hit.payload or {}
                st.markdown(
                    f"**{hit.score:.3f}** · `{payload.get('element_type')}` · "
                    f"page {payload.get('page_number')}"
                )
                st.text((payload.get("text") or "")[:400])
        except Exception as exc:
            st.error(f"Qdrant unavailable: {exc}")

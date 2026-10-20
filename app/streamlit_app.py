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


st.set_page_config(
    page_title="Element-Aware Chunking",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Tighter vertical rhythm */
    .block-container { padding-top: 1.25rem; padding-bottom: 1rem; max-width: 1180px; }
    h1 { font-size: 1.65rem !important; margin-bottom: 0.25rem !important; }
    [data-testid="stMetric"] { background: rgba(255,255,255,0.03); padding: 0.5rem 0.75rem; border-radius: 8px; }
    .chunk-card {
        border-left: 3px solid #f58231;
        padding: 0.5rem 0.75rem;
        margin: 0.35rem 0;
        background: rgba(128,128,128,0.08);
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
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


def draw_chunk_overlay(page_image: Path, chunks: list[Chunk], page_number: int, pattern: str) -> Image.Image:
    img = Image.open(page_image).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    color = PATTERN_COLORS.get(pattern, "#ffffff")

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

    return Image.alpha_composite(img, overlay)


def display_width(img: Image.Image, max_width: int = 560) -> int:
    w, h = img.size
    if w <= max_width:
        return w
    return max_width


def chunks_for_page(chunks: list[Chunk], page_number: int, pattern: str) -> list[Chunk]:
    on_page = [c for c in chunks if c.page_number == page_number]
    if on_page:
        return on_page
    if pattern in ("fixed", "recursive"):
        return chunks
    return []


def render_chunk_card(chunk: Chunk, index: int) -> None:
    color = PATTERN_COLORS.get(chunk.pattern, "#888")
    preview = chunk.text.replace("\n", " ").strip()
    if len(preview) > 280:
        preview = preview[:280] + "…"
    st.markdown(
        f"""
        <div class="chunk-card" style="border-left-color: {color};">
          <div class="chunk-meta">#{index} · {chunk.element_type} · {chunk.pattern}</div>
          <div>{preview or "<em>(empty)</em>"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.title("Element-Aware Chunking")
st.caption("Same PDF, same page — compare how each pattern draws chunk boundaries.")

pdfs = sorted(RAW_DIR.glob("*.pdf"))
if not pdfs:
    st.warning("No PDFs in `data/raw`. Run: `make samples`")
    st.stop()

with st.sidebar:
    st.header("Controls")
    pdf_path = st.selectbox("Document", pdfs, format_func=lambda p: p.name)
    pattern = st.selectbox(
        "Pattern",
        ALL_PATTERN_NAMES,
        format_func=lambda p: PATTERN_LABELS.get(p, p),
    )
    document = cached_parse(str(pdf_path), str(PROCESSED_DIR))
    max_page = max(document.page_count, 1)
    page_number = st.number_input("Page", min_value=1, max_value=max_page, value=1, step=1)
    st.divider()
    st.markdown(f"**Parser:** `{document.metadata.get('parser', '?')}`")
    st.markdown(f"**Pages:** {document.page_count}")
    st.markdown(
        f"<span style='color:{PATTERN_COLORS.get(pattern)}'>■</span> {PATTERN_LABELS.get(pattern, pattern)}",
        unsafe_allow_html=True,
    )

chunks = cached_chunk(str(pdf_path), str(PROCESSED_DIR), pattern)
page_chunks = chunks_for_page(chunks, int(page_number), pattern)
bbox_count = sum(1 for c in page_chunks if c.metadata.get("bbox"))
page_images = document.metadata.get("page_images", {})
page_image = page_images.get(int(page_number))

m1, m2, m3 = st.columns(3)
m1.metric("Chunks (this view)", len(page_chunks))
m2.metric("With bbox overlay", bbox_count)
m3.metric("Total (pattern)", len(chunks))

viz_col, list_col = st.columns([11, 9], gap="large")

with viz_col:
    st.subheader("Page preview", anchor=False)
    if page_image and Path(page_image).exists():
        overlay = draw_chunk_overlay(Path(page_image), chunks, int(page_number), pattern)
        w = display_width(overlay)
        st.image(
            overlay,
            width=w,
            caption=f"{PATTERN_LABELS.get(pattern, pattern)} — page {page_number}",
        )
        if bbox_count == 0:
            st.caption(
                "No bounding boxes for this pattern on this page. "
                "Try **element** or **page** for layout overlays."
            )
    else:
        st.info("Page image not available.")

with list_col:
    st.subheader("Chunks", anchor=False)
    if pattern in ("fixed", "recursive") and not any(
        c.page_number == int(page_number) for c in chunks
    ):
        st.caption("Text-only patterns are document-wide; list shows all chunks (not page-scoped).")

    if not page_chunks:
        st.caption("No chunks for this page.")
    else:
        with st.container(height=min(520, 120 + len(page_chunks) * 72)):
            for i, chunk in enumerate(page_chunks[:40], start=1):
                render_chunk_card(chunk, i)

with st.expander("Qdrant search", expanded=False):
    query = st.text_input("Query", key="qdrant_query", placeholder="e.g. revenue growth")
    if query:
        try:
            store = QdrantChunkStore()
            hits = store.search(query, limit=5, pattern=pattern)
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

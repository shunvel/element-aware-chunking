# Which chunking pattern when?

Use this as a decision guide for **mixed-content PDFs** (text + tables + figures). All patterns share the same `Chunk` schema and can be compared in the Streamlit viewer.

## Quick picks

| Your document | Start here | Also consider |
|---------------|------------|----------------|
| Mixed PDFs (default) | **`element`** | `table_multirep` if tables dominate |
| Annual reports / financial tables | **`table_multirep`** | `element` for footnotes + narrative |
| Slides / one-pagers / posters | **`page`** | `element` if you need per-block citations |
| Long manuals / policies | **`hierarchical`** | `recursive` for text-only fallback |
| Prose-heavy markdown/HTML export | **`recursive`** | `fixed` only as a baseline |
| Benchmarking / teaching failure modes | **`fixed`** | Compare against `element` on same page |

## Pattern details

### `fixed` — baseline

- **What it does:** Fixed character windows with overlap.
- **Use when:** You need a naive baseline or to demonstrate broken tables / split captions.
- **Avoid when:** Tables, figures, or citations matter.

### `recursive` — structure-aware text

- **What it does:** Splits on paragraphs, lines, sentences (text-first).
- **Use when:** Documents are mostly narrative with clear textual structure.
- **Avoid when:** Layout is visual (slides) or table-heavy without strong linear text.

### `page` — one chunk per page

- **What it does:** Entire page text (and optional page image path) as one unit.
- **Use when:** Pages are visually self-contained (slides, dashboards).
- **Avoid when:** Pages are long and retrieval needs finer granularity.

### `element` — core recommendation

- **What it does:** Atomic units per layout element (text block, table, image/caption); tables are not split.
- **Use when:** Production RAG on real PDFs with heterogeneous layout.
- **Payload:** `bbox`, `element_type`, captions — good for citation UI.

### `table_multirep` — table-heavy

- **What it does:** Linearized table summary for embedding + full `table_markdown` in payload (+ optional parent section).
- **Use when:** QA targets numeric/tabular evidence (reports, specs).
- **Qdrant:** Use `table_summary` named vector + filter `element_type=table`.

### `hierarchical` — parent / child

- **What it does:** Small child chunks for retrieval linked to larger parent chunks for generation context.
- **Use when:** Long sections mix narrative, tables, and figures; you want precise retrieval with broader context at answer time.
- **Trade-off:** More points in the index; retrieval logic must resolve `parent_id` / `child_ids`.

## Parser choice

| Backend | When |
|---------|------|
| **`docling`** (default) | Better reading order and typed elements; install with `make install-docling`. |
| **`pymupdf`** | Lightweight, fewer deps; set `PARSER_BACKEND=pymupdf`. |

Chunking patterns are **parser-agnostic** — they consume a shared `Document` model.

## Qdrant retrieval hints

- Filter by `pattern` to compare strategies fairly.
- Filter by `element_type` for table-only or text-only queries.
- For hierarchical patterns, fetch parent payload after child hit (see [docs/qdrant_payload_design.md](docs/qdrant_payload_design.md)).

## How we chose the sample PDFs

Each file in `data/raw/sample_*.pdf` stresses a different failure mode; see the table in [README.md](README.md#sample-documents).

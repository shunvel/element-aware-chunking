# Qdrant payload & named-vector design

This repo stores **element-aware chunks** in a single Qdrant collection with named vectors and filterable payloads.

## Collection

- **Name**: `element_aware_chunks` (override via `QDRANT_COLLECTION`)
- **URL**: `QDRANT_HOST` + `QDRANT_PORT` (default `localhost:6343` from local Docker), or set `QDRANT_URL`
- **Vectors**:
  - `text` — primary embedding of `Chunk.text` (FastEmbed / BGE-small by default)
  - `table_summary` — optional second vector for table rows (markdown summary linearization)

## Payload schema

| Field | Type | Purpose |
|-------|------|---------|
| `chunk_id` | keyword | Stable chunk UUID |
| `text` | text | Embedded string + display in UI |
| `pattern` | keyword | `fixed`, `recursive`, `page`, `element`, `table_multirep`, `hierarchical` |
| `source_file` | keyword | Original document path |
| `page_number` | integer | Page for citation |
| `element_type` | keyword | `text`, `table`, `image`, `mixed`, `page` |
| `metadata` | object | Pattern-specific fields (bbox, table_markdown, parent_id, child_ids, …) |

Indexed fields: `element_type`, `pattern`, `source_file`, `page_number`.

## Retrieval patterns

1. **Filtered search** — restrict by `pattern` to compare strategies fairly.
2. **Table-heavy queries** — search `table_summary` vector with `element_type=table`.
3. **Hierarchical** — retrieve small `child` chunks, then fetch `metadata.parent_id` / `child_ids` from payload for generation context.

## Why named vectors?

Tables benefit from a **short linearized summary** for embedding while keeping full `table_markdown` in the payload for the LLM. One point, two views — no duplicate rows in Postgres-style side tables.

# Local setup & toolchain

## Python (pick one)

### Option A — `python3` + Make (default)

```bash
cd /path/to/element-aware-chunking
make install          # pip install -e ".[dev]"
make install-docling  # optional: richer layout parsing
```

Requires **Python 3.11+** (`python3 --version`).

### Option B — `uv` (faster)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-extras
```

`make` auto-detects `uv` when it is on your `PATH`.

## Qdrant (Docker)

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and start it.
2. Confirm: `docker --version`
3. From this repo:

```bash
make qdrant
curl -s http://localhost:6343/collections | head
```

Default stack: [rag-okf](../rag-okf/docker-compose.yml) → `qdrant_enterprise_rag` on host port **6343**.

Override in `.env`:

```bash
QDRANT_HOST=localhost
QDRANT_PORT=6343
QDRANT_COMPOSE_FILE=../rag-okf/docker-compose.yml
```

If you use a different compose file, point `QDRANT_COMPOSE_FILE` at it.

## Verify everything

```bash
make verify
```

Runs tests, generates samples if missing, runs eval, and checks Docker/Qdrant when available.

## Streamlit demo

```bash
make samples
python3 -m streamlit run app/streamlit_app.py
```

## Regenerate README hero GIF

```bash
make demo-gif
```

Writes `docs/assets/demo.gif` (fixed vs element on the same page).

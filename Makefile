.PHONY: install install-docling demo ingest eval test qdrant download-samples samples demo-gif verify ui

# Local Qdrant Docker stack (override in .env)
QDRANT_COMPOSE_FILE ?= ../rag-okf/docker-compose.yml

PY ?= python3

ifneq ($(shell command -v uv 2>/dev/null),)
  RUN_SCRIPT = uv run python
  RUN_MODULE = uv run
else
  RUN_SCRIPT = $(PY)
  RUN_MODULE = $(PY) -m
endif

install:
	@if command -v uv >/dev/null 2>&1; then uv sync --extra dev; else $(PY) -m pip install -e ".[dev]"; fi

install-docling:
	@if command -v uv >/dev/null 2>&1; then uv sync --extra docling --extra dev; else $(PY) -m pip install -e ".[dev,docling]"; fi

qdrant:
	docker compose -f $(QDRANT_COMPOSE_FILE) up -d qdrant

demo:
	docker compose --profile demo up --build

ui:
	$(PY) -m streamlit run app/streamlit_app.py

ingest:
	$(RUN_SCRIPT) scripts/ingest_all_patterns.py

eval:
	$(RUN_SCRIPT) scripts/run_eval.py

test:
	$(RUN_MODULE) pytest -q

download-samples:
	$(RUN_SCRIPT) scripts/download_samples.py

samples:
	$(RUN_SCRIPT) scripts/generate_sample_pdfs.py

demo-gif:
	$(RUN_SCRIPT) scripts/generate_demo_gif.py

screenshots:
	$(RUN_SCRIPT) scripts/capture_readme_screenshots.py

verify:
	bash scripts/verify_local.sh

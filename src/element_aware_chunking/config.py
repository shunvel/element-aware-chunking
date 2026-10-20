from __future__ import annotations

import os


def qdrant_url(explicit: str | None = None) -> str:
    """Resolve Qdrant HTTP URL from env (local Docker on host port by default)."""
    if explicit:
        return explicit
    if url := os.getenv("QDRANT_URL"):
        return url
    host = os.getenv("QDRANT_HOST", "localhost")
    port = os.getenv("QDRANT_PORT", "6343")
    return f"http://{host}:{port}"

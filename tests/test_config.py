import os

from element_aware_chunking.config import qdrant_url


def test_qdrant_url_from_host_port(monkeypatch):
    monkeypatch.delenv("QDRANT_URL", raising=False)
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("QDRANT_PORT", "6343")
    assert qdrant_url() == "http://localhost:6343"


def test_qdrant_url_explicit_override(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://custom:6333")
    assert qdrant_url() == "http://custom:6333"

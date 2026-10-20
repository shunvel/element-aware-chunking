#!/usr/bin/env python3
"""Download optional PDFs from manifest; always ensure local samples exist."""

from __future__ import annotations

import json
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path

MANIFEST = Path("data/raw/manifest.json")
OUT_DIR = Path("data/raw")
GENERATE = Path(__file__).parent / "generate_sample_pdfs.py"


def _download(url: str, dest: Path) -> bool:
    print(f"download {url} -> {dest.name}")
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(url, context=ctx, timeout=120) as resp, dest.open("wb") as out:
            out.write(resp.read())
        return True
    except Exception as exc:
        print(f"  urllib failed: {exc}")
    try:
        subprocess.run(["curl", "-fsSL", "-o", str(dest), url], check=True, timeout=120)
        return True
    except Exception as exc:
        print(f"  curl failed: {exc}")
        return False


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text())
        for item in manifest.get("documents", []):
            dest = OUT_DIR / item["filename"]
            if dest.exists():
                print(f"skip {dest.name}")
                continue
            _download(item["url"], dest)

    print("generating local sample PDFs (offline-safe)...")
    subprocess.run([sys.executable, str(GENERATE)], check=True)
    print("done")


if __name__ == "__main__":
    main()

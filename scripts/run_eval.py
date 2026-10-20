#!/usr/bin/env python3
from __future__ import annotations

import json

from element_aware_chunking.eval.runner import run_eval


def main() -> None:
    report = run_eval()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

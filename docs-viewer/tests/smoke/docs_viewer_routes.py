#!/usr/bin/env python3
"""Run all focused Docs Viewer route smoke slices."""

from __future__ import annotations

import argparse
from pathlib import Path

from docs_viewer_route_smoke_helpers import (
    print_result,
    run_browser_smoke,
    run_index_panel_smoke,
    run_navigation_smoke,
    run_search_missing_hash_smoke,
)


def run_all_smokes(page, base_url: str, timeout_ms: int) -> dict[str, object]:
    return {
        "navigation": run_navigation_smoke(page, base_url, timeout_ms),
        "index_panel": run_index_panel_smoke(page, base_url, timeout_ms),
        "search_missing_hash": run_search_missing_hash_smoke(page, base_url, timeout_ms),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--site-root", type=Path, help="Serve a built site root on a temporary local HTTP server.")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    result = run_browser_smoke(
        base_url=args.base_url,
        site_root=args.site_root,
        timeout_ms=args.timeout_ms,
        callback=run_all_smokes,
    )
    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

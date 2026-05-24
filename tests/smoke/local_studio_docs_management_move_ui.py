#!/usr/bin/env python3
"""Smoke-check local Docs Viewer drag/drop move UI through the Studio app server."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[2]
SMOKE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SMOKE_DIR))

from local_studio_docs_management_ui import wait_for_doc, wait_for_management_idle, wait_for_management_ready  # noqa: E402
from local_studio_docs_management_workflows import create_fixture_repo, start_server  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="dlf-docs-move-ui-") as tmp_dir:
        fixture_root = Path(tmp_dir) / "site"
        create_fixture_repo(fixture_root)
        server, base_url = start_server(fixture_root)
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                errors: list[str] = []
                posts: list[str] = []
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.on(
                    "request",
                    lambda request: posts.append(request.url)
                    if request.method == "POST" and "/studio/api/docs/docs/" in request.url
                    else None,
                )

                page.goto(f"{base_url}/docs/?scope=studio&doc=root-doc&mode=manage", wait_until="domcontentloaded")
                wait_for_doc(page, "root-doc", args.timeout_ms)
                wait_for_management_ready(page, args.timeout_ms)
                page.wait_for_selector('[data-drag-doc-id="child-doc"]', timeout=args.timeout_ms)
                page.wait_for_selector('[data-doc-row-id="sibling-doc"]', timeout=args.timeout_ms)

                page.locator('[data-drag-doc-id="child-doc"]').drag_to(
                    page.locator('[data-doc-row-id="sibling-doc"]'),
                    target_position={"x": 80, "y": 18},
                    timeout=args.timeout_ms,
                )
                wait_for_management_idle(page, args.timeout_ms)
                page.wait_for_function(
                    """() => {
                        const row = document.querySelector('[data-doc-row-id="child-doc"]');
                        const sibling = document.querySelector('[data-doc-row-id="sibling-doc"]');
                        return row && sibling && sibling.compareDocumentPosition(row) & Node.DOCUMENT_POSITION_FOLLOWING;
                    }""",
                    timeout=args.timeout_ms,
                )
                browser.close()

            source_text = (fixture_root / "studio/docs-viewer/source/studio" / "child-doc.md").read_text(encoding="utf-8")
            if "parent_id: " not in source_text or "parent_id: root-doc" in source_text:
                raise AssertionError("UI drag/drop move did not move child-doc to the top level")
            if not any("/docs/move" in url for url in posts):
                raise AssertionError(f"missing expected move POST; saw {posts!r}")
            if errors:
                raise AssertionError(f"page errors during local Docs move UI smoke: {errors!r}")
            print(f"local Studio Docs move UI OK: {base_url}/docs/?scope=studio&doc=root-doc&mode=manage")
            return 0
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Smoke-check local Docs Viewer import UI through the Studio app server."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[2]
SMOKE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SMOKE_DIR))

from local_studio_docs_management_ui import open_actions_menu, wait_for_doc, wait_for_management_ready  # noqa: E402
from local_studio_docs_management_workflows import create_fixture_repo, start_server  # noqa: E402


def wait_for_import_ready(page: Page, timeout_ms: int) -> None:
    page.wait_for_selector("#docsViewerImportModal:not([hidden])", timeout=timeout_ms)
    page.wait_for_function(
        """() => {
            const root = document.querySelector("#docsHtmlImportRoot");
            const file = document.querySelector("#docsHtmlImportFileSelect");
            const scope = document.querySelector("#docsHtmlImportScopeSelect");
            const run = document.querySelector("#docsHtmlImportRun");
            return root &&
                root.dataset.studioReady === "true" &&
                root.dataset.studioBusy !== "true" &&
                file &&
                scope &&
                run &&
                !file.disabled &&
                !scope.disabled &&
                !run.disabled;
        }""",
        timeout=timeout_ms,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="dlf-docs-import-ui-") as tmp_dir:
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

                open_actions_menu(page, args.timeout_ms)
                page.locator("#docsViewerManageImportButton").click()
                wait_for_import_ready(page, args.timeout_ms)
                page.locator("#docsHtmlImportFileSelect").select_option("staged-doc.md")
                page.locator("#docsHtmlImportScopeSelect").select_option("studio")
                page.locator("#docsHtmlImportRun").click()
                page.wait_for_function(
                    """() => {
                        const root = document.querySelector("#docsHtmlImportRoot");
                        const result = document.querySelector("#docsHtmlImportResult");
                        const status = document.querySelector("#docsHtmlImportStatus");
                        return root &&
                            root.dataset.studioBusy !== "true" &&
                            result &&
                            !result.hidden &&
                            status &&
                            status.dataset.state === "success";
                    }""",
                    timeout=args.timeout_ms,
                )
                page.wait_for_function(
                    """() => document.querySelector("#docsHtmlImportResultDocId")?.textContent.includes("staged-doc")""",
                    timeout=args.timeout_ms,
                )
                browser.close()

            imported_path = fixture_root / "_docs" / "staged-doc.md"
            generated_path = fixture_root / "assets" / "data" / "docs" / "scopes" / "studio" / "by-id" / "staged-doc.json"
            if not imported_path.exists():
                raise AssertionError(f"UI import did not write fixture source: {imported_path}")
            if not generated_path.exists():
                raise AssertionError(f"UI import did not refresh fixture generated payload: {generated_path}")
            if not any("/docs/import-source" in url for url in posts):
                raise AssertionError(f"missing expected import POST; saw {posts!r}")
            if errors:
                raise AssertionError(f"page errors during local Docs import UI smoke: {errors!r}")
            print(f"local Studio Docs import UI OK: {base_url}/docs/?scope=studio&doc=root-doc&mode=manage")
            return 0
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())

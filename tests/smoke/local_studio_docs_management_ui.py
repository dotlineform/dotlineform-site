#!/usr/bin/env python3
"""Smoke-check local Docs Viewer management UI workflows."""

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

from local_studio_docs_management_workflows import create_fixture_repo, start_server  # noqa: E402


def wait_for_doc(page: Page, doc_id: str, timeout_ms: int) -> str:
    page.wait_for_selector("#docsViewerRoot:not([hidden])", timeout=timeout_ms)
    page.wait_for_selector("#docsViewerContent:not([hidden])", timeout=timeout_ms)
    page.wait_for_function(
        """docId => document.querySelector("#docsViewerContent h1")?.id === docId""",
        arg=doc_id,
        timeout=timeout_ms,
    )
    return page.locator("#docsViewerContent h1").inner_text()


def wait_for_management_ready(page: Page, timeout_ms: int) -> None:
    page.wait_for_function(
        """() => {
            const root = document.querySelector("#docsViewerRoot");
            const actions = document.querySelector(".docsViewer__manageActions");
            const button = document.querySelector("#docsViewerManageActionsButton");
            return root &&
                root.dataset.managementBusy !== "true" &&
                actions &&
                !actions.hidden &&
                button &&
                !button.disabled;
        }""",
        timeout=timeout_ms,
    )


def wait_for_management_idle(page: Page, timeout_ms: int) -> None:
    page.wait_for_function(
        """() => document.querySelector("#docsViewerRoot")?.dataset.managementBusy !== "true" """,
        timeout=timeout_ms,
    )


def open_actions_menu(page: Page, timeout_ms: int) -> None:
    wait_for_management_ready(page, timeout_ms)
    page.locator("#docsViewerManageActionsButton").click()
    page.wait_for_function(
        """() => {
            const menu = document.querySelector("#docsViewerManageActionsMenu");
            return menu && !menu.hidden;
        }""",
        timeout=timeout_ms,
    )


def click_modal_primary(page: Page, timeout_ms: int) -> None:
    page.locator('[data-docs-viewer-management-modal-host="true"] [data-role="modal-primary"]').click()
    page.wait_for_function(
        """() => !document.querySelector('[data-role="docs-viewer-management-modal"]')""",
        timeout=timeout_ms,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="dlf-docs-ui-") as tmp_dir:
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
                page.locator("#docsViewerManageNewButton").click()
                page.wait_for_selector("#docsViewerManagementModalInput", timeout=args.timeout_ms)
                page.locator("#docsViewerManagementModalInput").fill("UI Smoke Created")
                click_modal_primary(page, args.timeout_ms)
                wait_for_doc(page, "ui-smoke-created", args.timeout_ms)
                wait_for_management_idle(page, args.timeout_ms)

                open_actions_menu(page, args.timeout_ms)
                page.locator("#docsViewerManageEditButton").click()
                page.wait_for_selector("#docsViewerMetadataModal:not([hidden])", timeout=args.timeout_ms)
                page.locator("#docsViewerMetadataTitleInput").fill("UI Smoke Renamed")
                page.locator("#docsViewerMetadataSummaryInput").fill("UI workflow fixture")
                page.locator("#docsViewerMetadataStatusInput").select_option("review")
                page.locator("#docsViewerMetadataSaveButton").click()
                page.wait_for_function(
                    """() => document.querySelector("#docsViewerMetadataModal")?.hidden === true""",
                    timeout=args.timeout_ms,
                )
                wait_for_doc(page, "ui-smoke-created", args.timeout_ms)
                page.wait_for_function(
                    """() => document.querySelector("#docsViewerContent h1")?.textContent.trim() === "UI Smoke Renamed" """,
                    timeout=args.timeout_ms,
                )
                wait_for_management_idle(page, args.timeout_ms)

                open_actions_menu(page, args.timeout_ms)
                page.locator("#docsViewerManageSettingsButton").click()
                page.wait_for_selector("#docsViewerSettingsModal:not([hidden])", timeout=args.timeout_ms)
                page.wait_for_function(
                    """() => {
                        const input = document.querySelector("#docsViewerSettingsUpdatedInput");
                        const save = document.querySelector("#docsViewerSettingsSaveButton");
                        return input && save && !input.disabled && !save.disabled;
                    }""",
                    timeout=args.timeout_ms,
                )
                page.locator("#docsViewerSettingsUpdatedInput").uncheck()
                page.locator("#docsViewerSettingsSaveButton").click()
                page.wait_for_function(
                    """() => document.querySelector("#docsViewerSettingsModal")?.hidden === true""",
                    timeout=args.timeout_ms,
                )
                wait_for_doc(page, "ui-smoke-created", args.timeout_ms)

                open_actions_menu(page, args.timeout_ms)
                page.locator("#docsViewerManageArchiveButton").click()
                click_modal_primary(page, args.timeout_ms)
                wait_for_doc(page, "ui-smoke-created", args.timeout_ms)
                wait_for_management_idle(page, args.timeout_ms)

                open_actions_menu(page, args.timeout_ms)
                page.locator("#docsViewerManageDeleteButton").click()
                page.wait_for_selector('[data-role="docs-viewer-management-modal"]', timeout=args.timeout_ms)
                click_modal_primary(page, args.timeout_ms)
                wait_for_doc(page, "archive", args.timeout_ms)
                browser.close()

            source_path = fixture_root / "studio/docs-viewer/source/studio" / "ui-smoke-created.md"
            config_path = fixture_root / "scripts" / "docs" / "docs_scopes.json"
            if source_path.exists():
                raise AssertionError(f"UI delete did not remove fixture source: {source_path}")
            if '"show_updated_date": false' not in config_path.read_text(encoding="utf-8"):
                raise AssertionError("UI settings save did not update fixture docs_scopes.json")
            expected_posts = [
                "/docs/create",
                "/docs/update-metadata",
                "/docs/source-config-settings",
                "/docs/archive",
                "/docs/delete-preview",
                "/docs/delete-apply",
            ]
            missing_posts = [path for path in expected_posts if not any(path in url for url in posts)]
            if missing_posts:
                raise AssertionError(f"missing expected management POSTs: {missing_posts}; saw {posts!r}")
            if errors:
                raise AssertionError(f"page errors during local Docs management UI smoke: {errors!r}")
            print(f"local Studio Docs management UI OK: {base_url}/docs/?scope=studio&doc=root-doc&mode=manage")
            return 0
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Smoke-check Docs Viewer scope lifecycle UI through the Docs Viewer service."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
SMOKE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SMOKE_DIR))

from docs_viewer_management_ui import open_actions_menu, wait_for_doc, wait_for_management_ready  # noqa: E402
from docs_viewer_management_workflows import create_fixture_repo, start_server  # noqa: E402


def modal_title(page: Page) -> str:
    return page.locator('[data-role="docs-viewer-management-modal"] .docsViewer__modalTitle').inner_text()


def click_modal_primary(page: Page, timeout_ms: int) -> None:
    page.locator('[data-docs-viewer-management-modal-host="true"] [data-role="modal-primary"]').click()
    page.wait_for_function(
        """() => !document.querySelector('[data-role="docs-viewer-management-modal"]')""",
        timeout=timeout_ms,
    )


def scope_options(page: Page) -> list[str]:
    return page.eval_on_selector_all(
        "#docsViewerScopeSelect option",
        """options => options.map(option => option.value)""",
    )


def assert_scope_options_alpha(page: Page) -> None:
    options = scope_options(page)
    if options != sorted(options):
        raise AssertionError(f"scope dropdown options are not alpha-ordered: {options!r}")


def wait_for_scope_option(page: Page, scope_id: str, timeout_ms: int) -> None:
    page.wait_for_function(
        """scopeId => Array.from(document.querySelectorAll("#docsViewerScopeSelect option"))
            .some(option => option.value === scopeId)""",
        arg=scope_id,
        timeout=timeout_ms,
    )


def page_diagnostics(page: Page) -> dict[str, object]:
    return page.evaluate(
        """async () => {
            const root = document.querySelector("#docsViewerRoot");
            const content = document.querySelector("#docsViewerContent");
            const status = document.querySelector("#docsViewerStatus");
            let indexText = "";
            let payloadText = "";
            if (root?.dataset.indexTreeUrl) {
                try {
                    const response = await fetch(root.dataset.indexTreeUrl, { cache: "no-store" });
                    const body = await response.text();
                    indexText = String(response.status) + " " + body.slice(0, 500);
                    const payload = JSON.parse(body);
                    const contentUrl = payload?.docs?.[0]?.content_url;
                    if (contentUrl) {
                        const payloadResponse = await fetch(contentUrl, { cache: "no-store" });
                        payloadText = String(payloadResponse.status) + " " + (await payloadResponse.text()).slice(0, 500);
                    }
                } catch (error) {
                    indexText = String(error?.message || error);
                }
            }
            return {
                url: window.location.href,
                rootDataset: root ? Object.assign({}, root.dataset) : null,
                contentHidden: content ? content.hidden : null,
                contentText: content ? content.textContent.trim().slice(0, 300) : "",
                statusText: status ? status.textContent.trim() : "",
                navText: document.querySelector("#docsViewerNav")?.textContent.trim().slice(0, 300) || "",
                indexText,
                payloadText,
                scopeOptions: Array.from(document.querySelectorAll("#docsViewerScopeSelect option")).map(option => option.value),
            };
        }"""
    )


def wait_for_modal_title(page: Page, expected: str, timeout_ms: int) -> None:
    page.wait_for_selector('[data-role="docs-viewer-management-modal"]', timeout=timeout_ms)
    page.wait_for_function(
        """expected => document.querySelector('[data-role="docs-viewer-management-modal"] .docsViewer__modalTitle')
            ?.textContent.trim() === expected""",
        arg=expected,
        timeout=timeout_ms,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="dlf-docs-scope-ui-") as tmp_dir:
        fixture_root = Path(tmp_dir) / "site"
        create_fixture_repo(fixture_root)
        server, base_url = start_server(fixture_root)
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                errors: list[str] = []
                console_errors: list[str] = []
                posts: list[str] = []
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
                page.on(
                    "request",
                    lambda request: posts.append(request.url)
                    if request.method == "POST" and "/docs/" in request.url
                    else None,
                )

                page.goto(f"{base_url}/docs/?scope=studio&doc=root-doc", wait_until="domcontentloaded")
                wait_for_doc(page, "root-doc", args.timeout_ms)
                wait_for_management_ready(page, args.timeout_ms)
                assert_scope_options_alpha(page)

                open_actions_menu(page, args.timeout_ms)
                page.locator("#docsViewerManageNewScopeButton").click()
                wait_for_modal_title(page, "New scope", args.timeout_ms)
                page.locator('[data-role="scope-id"]').fill("uiscope")
                page.locator('[data-role="scope-title"]').fill("UI Scope")
                page.locator('[data-role="scope-publishing-mode"]').select_option("local_uncommitted")
                page.locator('[data-role="scope-write-generated"]').check()
                page.locator('[data-role="scope-build-search"]').check()
                click_modal_primary(page, args.timeout_ms)
                wait_for_modal_title(page, "Preview new scope", args.timeout_ms)
                click_modal_primary(page, args.timeout_ms)
                wait_for_modal_title(page, "Scope created", args.timeout_ms)
                click_modal_primary(page, args.timeout_ms)
                wait_for_scope_option(page, "uiscope", args.timeout_ms)
                wait_for_management_ready(page, args.timeout_ms)
                assert_scope_options_alpha(page)
                page.locator("#docsViewerScopeSelect").select_option("uiscope")
                try:
                    wait_for_doc(page, "uiscope", args.timeout_ms)
                except Exception as exc:
                    raise AssertionError(
                        "created scope did not load default doc: "
                        f"{page_diagnostics(page)!r}; page errors: {errors!r}; console errors: {console_errors!r}"
                    ) from exc
                wait_for_management_ready(page, args.timeout_ms)

                open_actions_menu(page, args.timeout_ms)
                page.locator("#docsViewerManageDeleteScopeButton").click()
                wait_for_modal_title(page, "Delete scope", args.timeout_ms)
                page.locator('[data-role="scope-delete-target"]').select_option("uiscope")
                click_modal_primary(page, args.timeout_ms)
                wait_for_modal_title(page, "Preview delete scope", args.timeout_ms)
                click_modal_primary(page, args.timeout_ms)
                wait_for_modal_title(page, "Scope deleted", args.timeout_ms)
                click_modal_primary(page, args.timeout_ms)
                browser.close()

            docs_config = (fixture_root / "docs-viewer" / "config" / "scopes" / "docs_scopes.json").read_text(encoding="utf-8")
            manifest_path = fixture_root / "docs-viewer" / "config" / "scopes" / "docs_scope_manifest.json"
            if (fixture_root / "docs-viewer" / "source" / "uiscope").exists():
                raise AssertionError("UI scope delete did not remove fixture source root")
            if "uiscope" in docs_config:
                raise AssertionError("UI scope delete did not remove fixture scope config")
            if manifest_path.exists() and "uiscope" in manifest_path.read_text(encoding="utf-8"):
                raise AssertionError("UI scope delete did not remove fixture scope manifest record")
            expected_posts = [
                "/docs/scopes/create-preview",
                "/docs/scopes/create-apply",
                "/docs/scopes/delete-preview",
                "/docs/scopes/delete-apply",
            ]
            missing_posts = [path for path in expected_posts if not any(path in url for url in posts)]
            if missing_posts:
                raise AssertionError(f"missing expected scope lifecycle POSTs: {missing_posts}; saw {posts!r}")
            if errors:
                raise AssertionError(f"page errors during local Docs scope UI smoke: {errors!r}")
            print(f"Docs Viewer service scope lifecycle UI OK: {base_url}/docs/?scope=studio&doc=root-doc")
            return 0
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())

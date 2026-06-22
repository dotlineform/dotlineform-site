#!/usr/bin/env python3
"""Smoke-check Docs Viewer scope lifecycle modal behavior."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from docs_viewer_management_modal_support import (
    REPO_ROOT,
    assert_shell,
    route_url,
    start_static_server,
)

def run_scope_lifecycle_create_payload_check(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <main id="docsViewerRoot" class="docsViewer">
                <button id="scopeLifecycleOpener" type="button">New scope</button>
              </main>
            `;
            window.__docsViewerScopeCreateRequests = [];
            window.fetch = async (url, options = {}) => {
                const body = options.body ? JSON.parse(options.body) : null;
                window.__docsViewerScopeCreateRequests.push({
                    url: String(url),
                    body
                });
                return {
                    ok: true,
                    status: 200,
                    json: async () => ({
                        ok: true,
                        schema_version: 'docs_scope_lifecycle_preview_v1',
                        action: 'create_scope',
                        operation: 'preview',
                        scope_id: body.scope_id,
                        title: body.title,
                        summary_text: 'Preview scope create.',
                        blockers: [],
                        created_files: [],
                        changed_files: [],
                        build_commands: [],
                        urls: {
                            management: `/docs/?scope=${body.scope_id}`,
                            public: ''
                        }
                    })
                };
            };
            const lifecycle = await import('/docs-viewer/runtime/js/management/docs-viewer-scope-lifecycle.js');
            window.__docsViewerScopeCreatePromise = lifecycle.openCreateScopeFlow({
                root: document.getElementById('docsViewerRoot'),
                state: {
                    managementText: {
                        cancelButton: 'Cancel',
                        scopeBuildSearchLabel: 'build inline search',
                        scopeCreateIntro: 'Create scope fixture.',
                        scopeCreatePreviewTitle: 'Preview new scope',
                        scopeCreatePreviewing: 'Previewing new scope...',
                        scopeCreateRequiredMessage: 'Enter the required scope fields.',
                        scopeCreateRouteRequiredMessage: 'Enter a public route path for public scopes.',
                        scopeCreateTitle: 'New scope',
                        scopeDefaultDocIdLabel: 'default doc id',
                        scopeIdLabel: 'scope id',
                        scopeLocalCommittedMode: 'local tracked',
                        scopeLocalCommittedModeNote: 'Local committed note.',
                        scopeLocalExternalMode: 'external local',
                        scopeLocalExternalModeNote: 'External local note.',
                        scopePreviewButton: 'Preview',
                        scopePublicReadonlyMode: 'public',
                        scopePublicReadonlyModeNote: 'Public note.',
                        scopePublicRoutePathLabel: 'public route path',
                        scopePublishingModeLabel: 'publishing mode',
                        scopeSaveButton: 'Save',
                        scopeSourceRootLabel: 'source root',
                        scopeTitleLabel: 'title',
                        scopeWriteGeneratedLabel: 'write generated outputs immediately'
                    }
                },
                capabilities: {
                    scope_lifecycle: {
                        publishing_modes: ['public_readonly', 'local_committed', 'local_external']
                    }
                },
                clientOptions: {
                    baseUrl: 'http://docs-management.test'
                },
                callbacks: {
                    render: () => {},
                    setBusy: busy => { window.__docsViewerScopeBusy = busy; },
                    setMessage: (message, isError) => {
                        window.__docsViewerScopeMessage = { message, isError };
                    }
                }
            }).then(value => {
                window.__docsViewerScopeCreateResult = value;
            });
        }"""
    )
    page.wait_for_selector('[data-role="docs-viewer-management-modal"]')
    assert_shell(
        page,
        '[data-role="docs-viewer-management-modal"]',
        "New scope",
        ["Preview", "Cancel"],
        size_class="docsViewer__modalCard--wide",
    )
    page.locator('[data-role="scope-id"]').fill("private-notes")
    auto_title = page.locator('[data-role="scope-title"]').input_value()
    if auto_title != "Private Notes":
        raise AssertionError(f"scope title did not auto-fill from scope id: {auto_title!r}")
    mode_options = page.locator('[data-role="scope-publishing-mode"] option').evaluate_all(
        "options => options.map(option => option.value)"
    )
    if mode_options != ["local_external", "local_committed", "public_readonly"]:
        raise AssertionError(f"scope publishing modes should include public_readonly after local defaults: {mode_options!r}")
    selected_mode = page.locator('[data-role="scope-publishing-mode"]').input_value()
    if selected_mode != "local_external":
        raise AssertionError(f"scope publishing mode did not default to the first local mode: {selected_mode!r}")
    if not page.locator('[data-role="scope-route-field"]').evaluate("node => node.hidden"):
        raise AssertionError("public route path field should be hidden for local scope modes")
    if page.locator('[data-role="scope-external-root-field"]').count() != 0:
        raise AssertionError("external root field should not be rendered for external local mode")
    page.locator('[data-role="scope-publishing-mode"]').select_option("public_readonly")
    if page.locator('[data-role="scope-route-field"]').evaluate("node => node.hidden"):
        raise AssertionError("public route path field should be visible for public_readonly mode")
    auto_route = page.locator('[data-role="scope-public-route-path"]').input_value()
    if auto_route != "/private-notes/":
        raise AssertionError(f"scope route path did not auto-fill from scope id: {auto_route!r}")
    page.locator('[data-role="scope-publishing-mode"]').select_option("local_external")
    page.locator('[data-role="scope-write-generated"]').uncheck()
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_function("() => window.__docsViewerScopeCreateRequests.length === 1")
    request = page.evaluate("window.__docsViewerScopeCreateRequests[0]")
    expected_body = {
        "scope_id": "private-notes",
        "title": "Private Notes",
        "source_root": "",
        "default_doc_id": "private-notes",
        "publishing_mode": "local_external",
        "public_route_path": "",
        "build_inline_search": False,
        "write_generated_outputs": False,
    }
    if request["url"] != "http://docs-management.test/docs/scopes/create-preview":
        raise AssertionError(f"scope create preview used the wrong endpoint: {request!r}")
    if request["body"] != expected_body:
        raise AssertionError(f"scope create payload did not match disabled generated-output state: {request!r}")
    page.wait_for_function("() => document.querySelector('[data-role=\"docs-viewer-management-modal\"] .docsViewer__modalTitle')?.textContent.trim() === 'Preview new scope'")
    page.locator('button[data-role="modal-cancel"]').click()
    page.wait_for_function("() => window.__docsViewerScopeCreateResult === null")




def run_smoke_for_viewport(page: Page, base_url: str, viewport: dict[str, int]) -> dict[str, object]:
    page.set_viewport_size(viewport)
    page.goto(route_url(base_url, "/__docs_viewer_scope_lifecycle_fixture__.html"), wait_until="domcontentloaded")
    run_scope_lifecycle_create_payload_check(page)
    return {
        "width": viewport["width"],
        "height": viewport["height"],
        "checked": ["scope-lifecycle-create-payload"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="", help="Use an existing local server instead of starting a fixture server.")
    parser.add_argument("--site-root", help="Serve a built site or repository root on a temporary local HTTP server.")
    args = parser.parse_args()

    static_server = None
    base_url = args.base_url
    if args.site_root:
        static_server, base_url = start_static_server(Path(args.site_root))
    elif not base_url:
        static_server, base_url = start_static_server(REPO_ROOT / "site")

    errors: list[str] = []
    results: list[dict[str, object]] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                    results.append(run_smoke_for_viewport(page, base_url, viewport))
            finally:
                browser.close()
    finally:
        if static_server is not None:
            static_server.shutdown()
            static_server.server_close()

    if errors:
        raise AssertionError(f"page errors during Docs Viewer scope lifecycle modal smoke: {errors!r}")
    print(json.dumps({"viewports": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

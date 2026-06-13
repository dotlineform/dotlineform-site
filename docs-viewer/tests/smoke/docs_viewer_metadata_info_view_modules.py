#!/usr/bin/env python3
"""Smoke-check Docs Viewer metadata info view rendering."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def install_fixture(page: Page) -> None:
    page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/shared/docs-viewer-metadata-info-view.js');
            const viewContext = await import('/docs-viewer/runtime/js/shared/docs-viewer-view-context.js');
            window.__docsViewerMetadataInfoViewSmoke = { module, viewContext };
        }"""
    )


def render_context(page: Page, context_expression: str) -> dict[str, object]:
    return page.evaluate(
        f"""() => {{
            const view = window.__docsViewerMetadataInfoViewSmoke.module.createDocsViewerMetadataInfoView();
            const mount = document.createElement('div');
            const context = {context_expression};
            context.mount = mount;
            view.mount(context);
            return {{
                title: mount.querySelector('.docsViewer__metadataInfoTitle')?.textContent || '',
                terms: Array.from(mount.querySelectorAll('dt')).map((node) => node.textContent.trim()),
                values: Array.from(mount.querySelectorAll('dd')).map((node) => node.textContent.trim()),
                text: mount.textContent
            }};
        }}"""
    )


def assert_context_hydrates_from_payload(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const { viewContext } = window.__docsViewerMetadataInfoViewSmoke;
            const selectedDoc = {
                doc_id: 'selected',
                title: 'Tree Title',
                summary: 'Tree summary',
                last_updated: '2026-06-01',
                ui_status: 'draft'
            };
            const payload = {
                title: 'Payload Title',
                summary: 'Payload summary',
                last_updated: '2026-06-05',
                ui_status: 'done',
                viewable: false
            };
            const publicContext = viewContext.createDocsViewerHostedViewContext({
                docsById: new Map([['selected', selectedDoc]]),
                payloadCache: new Map([['selected', payload]]),
                routeAccess: { publicReadOnly: true },
                selectedDocId: 'selected'
            });
            const manageContext = viewContext.createDocsViewerHostedViewContext({
                docsById: new Map([['selected', selectedDoc]]),
                payloadCache: new Map([['selected', payload]]),
                routeAccess: { allowManagement: true },
                selectedDocId: 'selected',
                uiStatusByValue: new Map([['done', { ui_status: 'done', label: 'Done' }]])
            });
            return {
                publicMetadata: publicContext.selectedMetadata,
                publicStatusLabel: publicContext.statusLabel,
                manageMetadata: manageContext.selectedMetadata,
                manageStatusLabel: manageContext.statusLabel
            };
        }"""
    )
    if result["publicMetadata"] != {
        "title": "Payload Title",
        "summary": "Payload summary",
        "last_updated": "2026-06-05",
    }:
        raise AssertionError(f"public context did not use reader payload metadata: {result!r}")
    if result["publicStatusLabel"]:
        raise AssertionError(f"public context exposed payload UI status: {result!r}")
    if result["manageMetadata"]["title"] != "Payload Title" or result["manageMetadata"]["ui_status"] != "done":
        raise AssertionError(f"manage context did not use payload metadata: {result!r}")
    if result["manageMetadata"]["doc_id"] != "selected":
        raise AssertionError(f"manage context did not preserve selected doc identity: {result!r}")
    if result["manageStatusLabel"] != "Done":
        raise AssertionError(f"manage context status label did not use payload status: {result!r}")


def assert_public_reader_metadata(page: Page) -> None:
    result = render_context(
        page,
        """{
            access: { publicReadOnly: true },
            canonicalUrl: '/library/?doc=payload-doc',
            parentTrail: [{ doc_id: 'parent', title: 'Parent' }],
            selectedDoc: {
                doc_id: 'tree-doc',
                title: 'Tree Title',
                summary: 'Tree summary',
                added_date: '2026-06-01',
                last_updated: '2026-06-01',
                ui_status: 'draft',
                viewable: false
            },
            selectedMetadata: {
                title: 'Payload Title',
                summary: 'Payload summary',
                last_updated: '2026-06-05'
            },
            statusLabel: 'Draft',
            viewerScope: 'library'
        }""",
    )
    if result["title"] != "Payload Title":
        raise AssertionError(f"public title did not use payload metadata: {result!r}")
    if result["terms"] != ["Summary", "Updated"]:
        raise AssertionError(f"public info terms are not reader-only: {result!r}")
    text = str(result["text"])
    blocked = ["Doc ID", "Scope", "Parent path", "Added", "UI status", "Visibility", "Route", "Tree summary"]
    leaked = [item for item in blocked if item in text]
    if leaked:
        raise AssertionError(f"public info leaked management/tree metadata {leaked!r}: {result!r}")


def assert_manage_metadata(page: Page) -> None:
    result = render_context(
        page,
        """{
            access: { allowManagement: true, publicReadOnly: false },
            canonicalUrl: '/docs/?scope=studio&doc=payload-doc',
            parentTrail: [{ doc_id: 'parent', title: 'Parent' }],
            selectedDoc: {
                doc_id: 'tree-doc',
                title: 'Tree Title',
                summary: 'Tree summary'
            },
            selectedMetadata: {
                doc_id: 'payload-doc',
                title: 'Payload Title',
                summary: 'Payload summary',
                added_date: '2026-06-01',
                last_updated: '2026-06-05',
                ui_status: 'done',
                viewable: false
            },
            statusLabel: 'Done',
            viewerScope: 'studio'
        }""",
    )
    expected_terms = ["Scope", "Summary", "Parent path", "Added", "Updated", "UI status", "Visibility", "Route"]
    if result["title"] != "Payload Title" or result["terms"] != expected_terms:
        raise AssertionError(f"manage info rendering changed: {result!r}")
    text = str(result["text"])
    for expected in ["payload-doc", "Payload summary", "Done", "Non-viewable"]:
      if expected not in text:
        raise AssertionError(f"manage info missing {expected!r}: {result!r}")
    if "Tree summary" in text:
        raise AssertionError(f"manage info used selected tree metadata: {result!r}")


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(route_url(base_url, "/"), wait_until="domcontentloaded")
    install_fixture(page)
    assert_context_hydrates_from_payload(page)
    assert_public_reader_metadata(page)
    assert_manage_metadata(page)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, default=Path("."))
    parser.add_argument("--timeout-ms", type=int, default=10000)
    args = parser.parse_args()

    server, base_url = start_static_server(args.site_root)
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.set_default_timeout(args.timeout_ms)
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
                run_smoke(page, base_url)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if errors:
        raise AssertionError(f"page errors during Docs Viewer metadata info view smoke: {errors!r}")
    print("Docs Viewer metadata info view module smoke OK")


if __name__ == "__main__":
    main()

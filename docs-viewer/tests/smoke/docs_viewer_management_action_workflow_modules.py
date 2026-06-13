#!/usr/bin/env python3
"""Smoke-check focused Docs Viewer management action workflow helpers."""

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
            const workflow = await import('/docs-viewer/runtime/js/management/docs-viewer-management-action-workflow.js');
            const actions = await import('/docs-viewer/runtime/js/management/docs-viewer-management-actions.js');
            const management = await import('/docs-viewer/runtime/js/management/docs-viewer-management.js');
            const docs = [
                { doc_id: 'root', title: 'Root', parent_id: '', viewable: false },
                { doc_id: 'parent', title: 'Parent', parent_id: 'root', viewable: false },
                { doc_id: 'current', title: 'Current', parent_id: 'parent', viewable: false },
                { doc_id: 'child-a', title: 'Child A', parent_id: 'current' },
                { doc_id: 'child-b', title: 'Child B', parent_id: 'child-a' },
                { doc_id: 'sibling', title: 'Sibling', parent_id: 'parent' }
            ];
            const docsById = new Map(docs.map((doc) => [doc.doc_id, doc]));
            window.__docsViewerManagementActionWorkflowSmoke = {
                workflow,
                actions,
                management,
                docs,
                docsById,
                formatText(template, tokens = {}) {
                    let result = String(template || '');
                    Object.keys(tokens).forEach((key) => {
                        result = result.replace(new RegExp(`\\\\{${key}\\\\}`, 'g'), tokens[key]);
                    });
                    return result;
                }
            };
        }"""
    )


def assert_viewability_targets(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__docsViewerManagementActionWorkflowSmoke;
            const { workflow, docs, docsById } = smoke;
            const calls = [];
            const targetIds = await workflow.resolveViewabilityTargetDocIds({
                doc: docsById.get('current'),
                allDocs: docs,
                findDocById: (docId) => docsById.get(docId) || null,
                confirmAncestors: (detail) => {
                    calls.push({ type: 'ancestors', titles: detail.titles });
                    return true;
                },
                chooseDescendants: (detail) => {
                    calls.push({ type: 'descendants', ids: detail.descendantIds });
                    return { confirmed: true, value: 'all' };
                },
                onInvalidChoice: (value) => calls.push({ type: 'invalid', value })
            });
            const descendants = Array.from(workflow.collectDescendantDocIds(docs, 'current', new Set()));
            const ancestors = workflow.nonViewableAncestorDocs(docsById.get('current'), (docId) => docsById.get(docId) || null)
                .map((doc) => doc.doc_id);
            const cancelled = await workflow.resolveViewabilityTargetDocIds({
                doc: docsById.get('current'),
                allDocs: docs,
                findDocById: (docId) => docsById.get(docId) || null,
                confirmAncestors: () => false
            });
            const invalidCalls = [];
            const invalid = await workflow.resolveViewabilityTargetDocIds({
                doc: docsById.get('current'),
                allDocs: docs,
                findDocById: (docId) => docsById.get(docId) || null,
                confirmAncestors: () => true,
                chooseDescendants: () => ({ confirmed: true, value: 'everything' }),
                onInvalidChoice: (value) => invalidCalls.push(value)
            });
            return { targetIds, calls, descendants, ancestors, cancelled, invalid, invalidCalls };
        }"""
    )
    if result["targetIds"] != ["root", "parent", "current", "child-a", "child-b"]:
        raise AssertionError(f"viewability targets changed: {result!r}")
    if result["calls"] != [
        {"type": "ancestors", "titles": "Root, Parent"},
        {"type": "descendants", "ids": ["child-a", "child-b"]},
    ]:
        raise AssertionError(f"viewability modal details changed: {result!r}")
    if result["descendants"] != ["child-a", "child-b"] or result["ancestors"] != ["root", "parent"]:
        raise AssertionError(f"ancestor/descendant helpers changed: {result!r}")
    if result["cancelled"] is not None or result["invalid"] is not None or result["invalidCalls"] != ["everything"]:
        raise AssertionError(f"viewability cancellation/invalid handling changed: {result!r}")


def assert_changed_module_imports(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const smoke = window.__docsViewerManagementActionWorkflowSmoke;
            return {
                actionController: typeof smoke.actions.createDocsViewerManagementActionController,
                managementInit: typeof smoke.management.initDocsViewerManagement
            };
        }"""
    )
    if result != {"actionController": "function", "managementInit": "function"}:
        raise AssertionError(f"changed Docs Viewer management modules failed import contract: {result!r}")


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(route_url(base_url, "/"), wait_until="domcontentloaded")
    install_fixture(page)
    assert_changed_module_imports(page)
    assert_viewability_targets(page)


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
        raise AssertionError(f"page errors during Docs Viewer management action workflow module smoke: {errors!r}")
    print("Docs Viewer management action workflow module smoke OK")


if __name__ == "__main__":
    main()

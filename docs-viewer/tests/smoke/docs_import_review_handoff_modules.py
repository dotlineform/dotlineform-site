#!/usr/bin/env python3
"""Smoke-check the identity-only Docs Review to managed Docs Import handoff."""

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
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_handoff_modules(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const appContextModule = await import('/site/docs-viewer/runtime/js/shared/docs-viewer-app-context.js');
          const reviewModule = await import('/docs-viewer/runtime/js/review/docs-viewer-review-controller.js');
          const managementModule = await import('/docs-viewer/runtime/js/management/docs-viewer-management-import-controller.js');
          const importModule = await import('/docs-viewer/runtime/js/import/docs-html-import.js');

          const routeRoot = document.createElement('section');
          const routeContext = appContextModule.createDocsViewerRouteContext({
            root: routeRoot,
            window: {
              location: {
                origin: location.origin,
                pathname: '/docs/',
                search: '?import=1&review_package=fixture-review'
              }
            },
            appKind: 'manage',
            resolvedRouteConfig: {
              appKind: 'manage',
              routeId: 'docs-manage',
              viewerBaseUrl: '/docs/',
              defaultScopeId: 'studio',
              includeScopeParam: true,
              access: { managementUi: true },
              features: {},
              services: {},
              preserveQueryParams: []
            }
          });
          const unsafeContext = appContextModule.createDocsViewerRouteContext({
            root: routeRoot,
            window: {
              location: {
                origin: location.origin,
                pathname: '/docs/',
                search: '?import=1&review_package=../unsafe'
              }
            },
            appKind: 'manage',
            resolvedRouteConfig: {
              appKind: 'manage',
              routeId: 'docs-manage',
              viewerBaseUrl: '/docs/',
              defaultScopeId: 'studio',
              includeScopeParam: true,
              access: { managementUi: true },
              features: {},
              services: {},
              preserveQueryParams: []
            }
          });

          document.body.innerHTML = '<div id="docsViewerReviewControlsMount"></div><p id="docsViewerStatus"></p>';
          const reviewController = reviewModule.createDocsViewerReviewController({ document, window });
          reviewController.setProvider({
            activeCollectionId: () => 'fixture-review',
            listCollections: async () => [{ package_id: 'fixture-review', title: 'Fixture review' }],
            readManifest: async () => ({ manifest: { package_id: 'fixture-review', source_scope: 'library' } }),
            build: async () => ({}),
            readAssetInventory: async () => ({ inventories: {} })
          });
          await reviewController.start();
          const reviewHref = document.querySelector('.docsViewer__reviewImportLink')?.getAttribute('href') || '';

          const root = document.createElement('div');
          root.dataset.docsImportReviewPackageId = 'fixture-review';
          const bootStatus = document.createElement('p');
          let initOptions = null;
          const managementController = managementModule.createDocsViewerManagementImportController({
            refs: { root, bootStatus },
            context: { root, managementBaseUrl: 'http://127.0.0.1:9999' },
            callbacks: {
              loadImportModule: async () => ({
                initDocsHtmlImport: async options => { initOptions = options; }
              }),
              viewerScope: () => 'library'
            }
          });
          await managementController.initialize();

          const files = [
            { filename: 'other.jsonl', source_format: 'data_sharing_documents', review_package_ids: ['other-review'] },
            { filename: 'reviewed.jsonl', source_format: 'data_sharing_documents', review_package_ids: ['fixture-review'] }
          ];
          const matched = importModule.docsImportReviewHandoff(files, 'fixture-review');
          const missing = importModule.docsImportReviewHandoff(files, 'deleted-review');

          return {
            routeOpen: routeContext.openImportOnLoad,
            routePackageId: routeContext.importReviewPackageId,
            unsafePackageId: unsafeContext.importReviewPackageId,
            reviewHref,
            initializedPackageId: initOptions && initOptions.reviewPackageId,
            initializedScope: initOptions && initOptions.initialScope,
            matchedFilename: matched.file && matched.file.filename,
            missingRequested: missing.requested,
            missingAvailable: missing.available
          };
        }"""
    )
    expected = {
        "routeOpen": True,
        "routePackageId": "fixture-review",
        "unsafePackageId": "",
        "reviewHref": "/docs/?import=1&review_package=fixture-review",
        "initializedPackageId": "fixture-review",
        "initializedScope": "library",
        "matchedFilename": "reviewed.jsonl",
        "missingRequested": True,
        "missingAvailable": False,
    }
    if result != expected:
        raise AssertionError(f"unexpected review handoff contract: {result!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", default=".", help="Repository root to serve.")
    args = parser.parse_args(argv)
    server, base_url = start_static_server(Path(args.site_root))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            errors: list[str] = []
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.goto(base_url, wait_until="domcontentloaded")
                assert_handoff_modules(page)
            finally:
                browser.close()
            if errors:
                raise AssertionError(f"page errors: {errors}")
    finally:
        server.shutdown()
        server.server_close()
    print("Docs Import review handoff modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

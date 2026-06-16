#!/usr/bin/env python3
"""Smoke-check shared Catalogue editor route boot JavaScript helpers."""

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


def assert_route_boot_helpers(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <main>
                <section id="catalogueRoot"></section>
                <div id="catalogueLoading"></div>
                <div id="catalogueStatus"></div>
                <div id="catalogueMissing"></div>
              </main>
            `;
            const module = await import('/studio/app/frontend/js/catalogue-editor-route-boot.js');
            const root = document.getElementById('catalogueRoot');
            const loadingNode = document.getElementById('catalogueLoading');
            const statusNode = document.getElementById('catalogueStatus');
            const collected = module.collectRequiredElements({
                root: 'catalogueRoot',
                statusNode: 'catalogueStatus'
            });
            const missing = module.collectRequiredElements({
                root: 'catalogueRoot',
                absentNode: 'doesNotExist'
            });
            module.setCatalogueEditorTextWithState(statusNode, 'Loaded', 'success');
            module.initializeCatalogueEditorRoute(root, 'catalogue-test');
            const state = {
                root,
                mode: 'bulk',
                bulkIds: ['001', '002'],
                currentRecord: null,
                serverAvailable: true,
                isSaving: true
            };
            module.syncCatalogueEditorRouteBusyState(state, {
                route: 'catalogue-test',
                bulkIdsKey: 'bulkIds'
            });
            const bulkOptions = module.createCatalogueEditorRouteStateOptions({
                route: 'catalogue-test',
                bulkIdsKey: 'bulkIds'
            });
            const singleOptions = module.createCatalogueEditorRouteStateOptions({
                route: 'catalogue-test'
            });
            const importOptions = module.createCatalogueEditorRouteStateOptions({
                route: 'catalogue-test',
                importModeKey: 'isImportMode'
            });
            const busyOptions = module.createCatalogueEditorRouteStateOptions({
                route: 'catalogue-test',
                busyKeys: ['isSaving', 'importIsBusy']
            });
            const bulkDetail = module.catalogueEditorRouteStateDetail(state, bulkOptions);
            const singleDetail = module.catalogueEditorRouteStateDetail({
                root,
                currentRecord: { id: '003' },
                serverAvailable: true
            }, singleOptions);
            const importDetail = module.catalogueEditorRouteStateDetail({
                root,
                isImportMode: true,
                currentRecord: { id: '004' },
                serverAvailable: true
            }, importOptions);
            const busyState = {
                root,
                currentRecord: { id: '005' },
                serverAvailable: true,
                isSaving: false,
                importIsBusy: true
            };
            module.syncCatalogueEditorRouteBusyState(busyState, busyOptions);
            const available = await module.configureCatalogueEditorRouteRuntime(state, {
                namespace: 'catalogue_test',
                configLoader: async () => ({ ui_text: {} }),
                healthProbe: async () => false,
                applyText: () => {
                    root.dataset.textApplied = 'true';
                }
            });
            const target = new Map();
            const itemSets = await module.loadCatalogueEditorLookupMaps(state, [
                {
                    configKey: 'catalogue_lookup_test',
                    target,
                    normalizeKey: (record) => record.id,
                    afterItems: (items) => {
                        state.itemCount = items.length;
                    }
                }
            ], {
                lookupLoader: async (_config, _key, readOptions) => ({
                    readOptions,
                    items: [
                        { id: '001', title: 'Alpha' },
                        { id: '', title: 'Ignored' },
                        null
                    ]
                })
            });
            module.revealCatalogueEditorRoute(state, {
                loadingNode,
                routeState: {
                    route: 'catalogue-test',
                    bulkIdsKey: 'bulkIds'
                }
            });
            await Promise.all([
                import('/studio/app/frontend/js/catalogue-work-editor.js'),
                import('/studio/app/frontend/js/catalogue-series-editor.js'),
                import('/studio/app/frontend/js/catalogue-moment-editor.js')
            ]);
            return {
                collectedRoot: collected && collected.root === root,
                missingIsNull: missing === null,
                statusText: statusNode.textContent,
                statusState: statusNode.dataset.state || '',
                busy: root.dataset.studioBusy,
                customBusy: root.dataset.studioBusy,
                ready: root.dataset.studioReady,
                mode: root.dataset.studioMode,
                service: root.dataset.studioService,
                recordLoaded: root.dataset.studioRecordLoaded,
                bulkDetail,
                singleDetail,
                importDetail,
                hidden: root.hidden,
                loadingHidden: loadingNode.hidden,
                available,
                textApplied: root.dataset.textApplied,
                itemCount: state.itemCount,
                targetTitle: target.get('001') && target.get('001').title,
                itemSetLength: itemSets[0].length,
                routeImports: true
            };
        }"""
    )
    assert result["collectedRoot"] is True
    assert result["missingIsNull"] is True
    assert result["statusText"] == "Loaded"
    assert result["statusState"] == "success"
    assert result["busy"] == "true"
    assert result["customBusy"] == "true"
    assert result["ready"] == "true"
    assert result["mode"] == "bulk"
    assert result["service"] == "unavailable"
    assert result["recordLoaded"] == "true"
    assert result["bulkDetail"] == {
        "route": "catalogue-test",
        "mode": "bulk",
        "service": "available",
        "recordLoaded": True,
    }
    assert result["singleDetail"] == {
        "route": "catalogue-test",
        "mode": "single",
        "service": "available",
        "recordLoaded": True,
    }
    assert result["importDetail"] == {
        "route": "catalogue-test",
        "mode": "import",
        "service": "available",
        "recordLoaded": False,
    }
    assert result["hidden"] is False
    assert result["loadingHidden"] is True
    assert result["available"] is False
    assert result["textApplied"] == "true"
    assert result["itemCount"] == 3
    assert result["targetTitle"] == "Alpha"
    assert result["itemSetLength"] == 3
    assert result["routeImports"] is True


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_route_boot_helpers(page)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".", help="Site root to serve for module imports.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(Path(args.site_root))


if __name__ == "__main__":
    main()

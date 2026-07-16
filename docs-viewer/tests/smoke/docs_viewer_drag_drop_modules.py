#!/usr/bin/env python3
"""Smoke-check Docs Viewer drag/drop helper contracts."""

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


def assert_drag_drop_helpers(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/management/docs-viewer-drag-drop.js');
            document.body.innerHTML = `
                <nav id="nav" style="padding: 0 0 32px 0;">
                  <ul class="docsViewer__navList" style="display:block; padding:0; margin:0;">
                    <li class="docsViewer__navItem">
                      <div class="docsViewer__navRow" data-doc-row-id="root-a" style="height:20px;"></div>
                    </li>
                    <li class="docsViewer__navItem">
                      <div class="docsViewer__navRow" data-doc-row-id="root-b" style="height:20px;"></div>
                      <ul class="docsViewer__navList docsViewer__navList--child" style="display:block; padding:0; margin:0;">
                        <li class="docsViewer__navItem">
                          <div class="docsViewer__navRow" data-doc-row-id="child-a" style="height:20px;"></div>
                        </li>
                        <li class="docsViewer__navItem">
                          <div class="docsViewer__navRow" data-doc-row-id="child-b" style="height:20px;"></div>
                        </li>
                      </ul>
                    </li>
                  </ul>
                </nav>
            `;
            const nav = document.getElementById('nav');
            const rootList = nav.querySelector('.docsViewer__navList');
            const childList = nav.querySelector('.docsViewer__navList--child');
            const rootB = nav.querySelector('[data-doc-row-id="root-b"]');
            const childB = nav.querySelector('[data-doc-row-id="child-b"]');
            const rootRect = rootB.getBoundingClientRect();
            const childRect = childB.getBoundingClientRect();
            const docsById = new Map([
                ['moving', { doc_id: 'moving', parent_id: 'root-b' }],
                ['root-a', { doc_id: 'root-a' }],
                ['root-b', { doc_id: 'root-b' }],
                ['child-a', { doc_id: 'child-a' }],
                ['child-b', { doc_id: 'child-b' }]
            ]);
            const options = {
                dragDocId: 'moving',
                dragEnabled: true,
                docsById,
                hasChildren: () => false,
                nav
            };
            const rootTerminal = module.terminalRootDropTargetFromEvent({
                target: nav,
                clientY: rootRect.bottom + 8
            }, options);
            const childTerminal = module.terminalRootDropTargetFromEvent({
                target: childList,
                clientY: childRect.bottom + 8
            }, options);
            const currentTarget = module.currentDropTargetFromEvent({
                target: childList,
                clientY: childRect.top + 2
            }, { parentId: 'root-a' }, options);
            const parentId = module.rowDropParentIdFromEvent(rootB, {
                clientY: rootRect.bottom - 2
            }, options);
            return { rootTerminal, childTerminal, currentTarget, parentId };
        }"""
    )
    if result["rootTerminal"] != {"parentId": ""}:
        raise AssertionError(f"root terminal drop target did not resolve to root: {result!r}")
    if result["childTerminal"] is not None:
        raise AssertionError(f"child terminal drop target should not resolve to root: {result!r}")
    if result["currentTarget"] != {"parentId": "root-a"}:
        raise AssertionError(f"current drop target did not use fallback parent: {result!r}")
    if result["parentId"] != "root-b":
        raise AssertionError(f"row drop did not resolve to the row doc as parent: {result!r}")


def assert_management_interaction_terminal_drop(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/management/docs-viewer-management-interactions.js');
            document.body.innerHTML = `
                <nav id="nav" style="padding: 0 0 32px 0;">
                  <ul class="docsViewer__navList" style="display:block; padding:0; margin:0;">
                    <li class="docsViewer__navItem">
                      <div class="docsViewer__navRow" data-doc-row-id="moving" style="height:20px;">
                        <a href="#" data-drag-doc-id="moving" draggable="true">Moving</a>
                      </div>
                    </li>
                    <li class="docsViewer__navItem">
                      <div class="docsViewer__navRow" data-doc-row-id="root-b" style="height:20px;">Root B</div>
                    </li>
                  </ul>
                </nav>
            `;
            const nav = document.getElementById('nav');
            const rootB = nav.querySelector('[data-doc-row-id="root-b"]');
            const rootRect = rootB.getBoundingClientRect();
            const moveCalls = [];
            const controller = module.createDocsViewerManagementInteractionController({
                nav,
                documentIndex: {
                    docsById: new Map([
                        ['moving', { doc_id: 'moving', title: 'Moving', parent_id: 'root-b' }],
                        ['root-b', { doc_id: 'root-b', title: 'Root B' }]
                    ]),
                    childrenByParent: new Map()
                },
                management: {
                    managementAvailable: true,
                    managementBusy: false
                },
                routeSession: { managementContext: true },
                searchRecent: { searchRouteActive: false },
                selectedDocument: { selectedDocId: 'moving' },
                context: {
                    cssEscape: (value) => CSS.escape(value)
                },
                callbacks: {
                    onMoveDoc: (movingDocId, parentId) => moveCalls.push({ movingDocId, parentId })
                }
            });
            controller.wireEvents();

            nav.querySelector('[data-drag-doc-id="moving"]').dispatchEvent(new Event('dragstart', {
                bubbles: true,
                cancelable: true
            }));
            const dragover = new Event('dragover', { bubbles: true, cancelable: true });
            Object.defineProperty(dragover, 'clientY', { value: rootRect.bottom + 8 });
            nav.dispatchEvent(dragover);
            const indicator = nav.classList.contains('is-drop-root');
            const drop = new Event('drop', { bubbles: true, cancelable: true });
            Object.defineProperty(drop, 'clientY', { value: rootRect.bottom + 8 });
            nav.dispatchEvent(drop);

            return {
                dragoverPrevented: dragover.defaultPrevented,
                dropPrevented: drop.defaultPrevented,
                indicator,
                moveCalls
            };
        }"""
    )
    if not result["dragoverPrevented"]:
        raise AssertionError(f"terminal dragover was not accepted as droppable: {result!r}")
    if not result["dropPrevented"]:
        raise AssertionError(f"terminal drop was not handled by the nav controller: {result!r}")
    if not result["indicator"]:
        raise AssertionError(f"terminal dragover did not project the root indicator: {result!r}")
    if result["moveCalls"] != [{"movingDocId": "moving", "parentId": ""}]:
        raise AssertionError(f"terminal drop did not request the expected move: {result!r}")


def assert_management_interaction_first_child_drop(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/management/docs-viewer-management-interactions.js');
            document.body.innerHTML = `
                <nav id="nav" style="padding: 0 0 32px 0;">
                  <ul class="docsViewer__navList" style="display:block; padding:0; margin:0;">
                    <li class="docsViewer__navItem">
                      <div class="docsViewer__navRow" data-doc-row-id="moving" style="height:20px;">
                        <a href="#" data-drag-doc-id="moving" draggable="true">Moving</a>
                      </div>
                    </li>
                    <li class="docsViewer__navItem">
                      <div class="docsViewer__navRow" data-doc-row-id="parent" style="height:20px;">Parent</div>
                      <ul class="docsViewer__navList docsViewer__navList--child" style="display:block; padding:0; margin:0;">
                        <li class="docsViewer__navItem">
                          <div class="docsViewer__navRow" data-doc-row-id="child-a" style="height:20px;">Child A</div>
                        </li>
                      </ul>
                    </li>
                  </ul>
                </nav>
            `;
            const nav = document.getElementById('nav');
            const parent = nav.querySelector('[data-doc-row-id="parent"]');
            const parentRect = parent.getBoundingClientRect();
            const moveCalls = [];
            const controller = module.createDocsViewerManagementInteractionController({
                nav,
                documentIndex: {
                    docsById: new Map([
                        ['moving', { doc_id: 'moving', title: 'Moving' }],
                        ['parent', { doc_id: 'parent', title: 'Parent' }],
                        ['child-a', { doc_id: 'child-a', title: 'Child A', parent_id: 'parent' }]
                    ]),
                    childrenByParent: new Map([
                        ['parent', [{ doc_id: 'child-a', title: 'Child A', parent_id: 'parent' }]]
                    ])
                },
                management: {
                    managementAvailable: true,
                    managementBusy: false
                },
                routeSession: { managementContext: true },
                searchRecent: { searchRouteActive: false },
                selectedDocument: { selectedDocId: 'moving' },
                context: {
                    cssEscape: (value) => CSS.escape(value)
                },
                callbacks: {
                    onMoveDoc: (movingDocId, parentId) => moveCalls.push({ movingDocId, parentId })
                }
            });
            controller.wireEvents();

            nav.querySelector('[data-drag-doc-id="moving"]').dispatchEvent(new Event('dragstart', {
                bubbles: true,
                cancelable: true
            }));
            const dragover = new Event('dragover', { bubbles: true, cancelable: true });
            Object.defineProperty(dragover, 'clientY', { value: parentRect.bottom - 2 });
            parent.dispatchEvent(dragover);
            const parentIndicator = parent.classList.contains('is-drop-inside');
            const rootIndicator = nav.classList.contains('is-drop-root');
            const drop = new Event('drop', { bubbles: true, cancelable: true });
            Object.defineProperty(drop, 'clientY', { value: parentRect.bottom - 2 });
            parent.dispatchEvent(drop);

            return { dragoverPrevented: dragover.defaultPrevented, parentIndicator, rootIndicator, moveCalls };
        }"""
    )
    if not result["dragoverPrevented"]:
        raise AssertionError(f"first-child dragover was not accepted as droppable: {result!r}")
    if not result["parentIndicator"] or result["rootIndicator"]:
        raise AssertionError(f"parent dragover did not project the parent indicator: {result!r}")
    if result["moveCalls"] != [{"movingDocId": "moving", "parentId": "parent"}]:
        raise AssertionError(f"first-child drop did not request the expected move: {result!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", type=Path, default=Path.cwd())
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_static_server(args.site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(base_url, wait_until="domcontentloaded", timeout=args.timeout_ms)
            assert_drag_drop_helpers(page)
            assert_management_interaction_terminal_drop(page)
            assert_management_interaction_first_child_drop(page)
            browser.close()
        print("Docs Viewer drag/drop module helpers OK")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())

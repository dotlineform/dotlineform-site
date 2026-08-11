#!/usr/bin/env python3
"""Smoke-check the shared live-report expansion and composition contracts."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
LOCAL_REPORT_PRESENTATION_URL = "/docs-viewer/runtime/js/reports/docs-viewer-report-presentation.js"
LOCAL_REPORT_PRESENTATION_PATH = (
    REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-report-presentation.js"
)


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        request_path = path.partition("?")[0].partition("#")[0]
        if request_path == LOCAL_REPORT_PRESENTATION_URL:
            return str(LOCAL_REPORT_PRESENTATION_PATH)
        return super().translate_path(path)


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_static_composition() -> None:
    public_entry = (
        REPO_ROOT / "site/docs-viewer/runtime/js/public/docs-viewer-public.js"
    ).read_text(encoding="utf-8")
    manage_entry = (
        REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-manage.js"
    ).read_text(encoding="utf-8")
    public_extras = (
        REPO_ROOT
        / "site/docs-viewer/runtime/js/public/docs-viewer-public-document-reports.js"
    ).read_text(encoding="utf-8")
    public_controller = (
        REPO_ROOT / "site/docs-viewer/runtime/js/reports/docs-viewer-public-reports.js"
    ).read_text(encoding="utf-8")
    manage_controller = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-reports.js"
    ).read_text(encoding="utf-8")
    reports_css = (
        REPO_ROOT / "site/docs-viewer/static/css/docs-viewer-reports.css"
    ).read_text(encoding="utf-8")
    local_reports_css = (
        REPO_ROOT / "docs-viewer/static/css/docs-viewer-local-reports.css"
    ).read_text(encoding="utf-8")
    public_route = (REPO_ROOT / "site/analysis/index.html").read_text(encoding="utf-8")
    public_route_template = (
        REPO_ROOT / "docs-viewer/templates/public-route/index.html"
    ).read_text(encoding="utf-8")
    manage_shell = (
        REPO_ROOT / "docs-viewer/shell/docs-viewer-manage.html"
    ).read_text(encoding="utf-8")

    required_entry_values = (
        "createDocsViewerReportPresentationAdapter",
        "docs-viewer-report-presentation.js",
        "reportPresentationAdapter",
        "withDocsViewerContentDetailDefinitions",
    )
    forbidden_public_entry_values = required_entry_values[:-1]
    if any(value in public_entry for value in forbidden_public_entry_values):
        raise AssertionError("public entrypoint still composes report expansion")
    if "withDocsViewerContentDetailDefinitions" not in public_entry:
        raise AssertionError("public entrypoint lost the shared Content Detail composition")
    if any(value not in manage_entry for value in required_entry_values):
        raise AssertionError("Manage entrypoint did not explicitly compose report expansion")
    if "/management/" in public_entry:
        raise AssertionError("public report expansion imports management runtime")

    forbidden_public_context_values = (
        "documentMountGeneration",
        "reportPresentationAdapter",
        "requestContentDetail",
    )
    if any(value in public_extras for value in forbidden_public_context_values):
        raise AssertionError("public document extras still supply report expansion context")
    forbidden_public_controller_values = (
        "expandedPresentation",
        "registerExpandedPresentation",
        "reportPresentationAdapter",
    )
    if any(value in public_controller for value in forbidden_public_controller_values):
        raise AssertionError("public report controller still registers report expansion")

    required_manage_controller_values = (
        ".then(function (mountResult)",
        "hostIsCurrent(root, context.content)",
        "registerExpandedPresentation(context, root, resolvedReportMeta, mountResult)",
    )
    if any(value not in manage_controller for value in required_manage_controller_values):
        raise AssertionError("Manage report controller discards the exact mount result")

    expansion_selectors = (
        ".docsViewerReport__detailControlRow",
        ".docsViewerReport__detailOpen",
        ".docsViewerReport__detailIcon",
        ".docsViewerReport__expandedViewport",
    )
    if any(value in reports_css for value in expansion_selectors):
        raise AssertionError("public-loaded report stylesheet still composes report expansion")
    if any(value not in local_reports_css for value in expansion_selectors):
        raise AssertionError("Manage local report stylesheet lost report expansion selectors")
    if "overflow: auto" not in local_reports_css:
        raise AssertionError("Manage expanded-report viewport is not horizontally contained")
    for source, label in (
        (public_route, "public route"),
        (public_route_template, "public route template"),
    ):
        if "docs-viewer-reports.css" not in source:
            raise AssertionError(f"{label} lost the shared report stylesheet")
        if "docs-viewer-local-reports.css" in source:
            raise AssertionError(f"{label} loads the Manage-only report stylesheet")
    if "docs-viewer-local-reports.css" not in manage_shell:
        raise AssertionError("Manage shell lost the local report stylesheet")


def install_fixture(page: Page) -> None:
    page.evaluate(
        """async () => {
            const modules = await Promise.all([
                import('/docs-viewer/runtime/js/shared/docs-viewer-content-detail-view.js'),
                import('/docs-viewer/runtime/js/shared/docs-viewer-document-controller.js'),
                import('/docs-viewer/runtime/js/reports/docs-viewer-report-presentation.js')
            ]);
            window.__docsViewerExpandedReportSmoke = {
                contentDetail: modules[0],
                documentController: modules[1],
                reportPresentation: modules[2]
            };
        }"""
    )


def assert_live_report_lifecycle(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const modules = window.__docsViewerExpandedReportSmoke;
            const warnings = [];
            const adapter = modules.reportPresentation.createDocsViewerReportPresentationAdapter({
                warn: (message, error) => warnings.push(`${message}: ${error.message}`)
            });
            const content = document.createElement('article');
            content.className = 'docsViewer__content';
            content.innerHTML = [
                '<p id="before">Before</p>',
                '<div id="report" class="docsViewerReport"><input value="retained"><button id="state">State</button></div>',
                '<p id="after">After</p>'
            ].join('');
            document.body.replaceChildren(content);
            const reportRoot = content.querySelector('#report');
            const stateButton = reportRoot.querySelector('#state');
            let reportState = 0;
            stateButton.addEventListener('click', () => { reportState += 1; });

            const requested = [];
            const registration = adapter.registerMountedReport({
                content,
                doc: { doc_id: 'd-report' },
                document,
                documentMountGeneration: 7,
                mountResult: {
                    expandedPresentation: { kind: 'flow', label: 'Catalogue Works' }
                },
                reportMeta: {
                    reportId: 'catalogue_works', scope: 'studio', preset: 'works', subScope: ''
                },
                reportRoot,
                requestContentDetail: target => {
                    requested.push(target);
                    return true;
                },
                viewerScope: 'studio'
            });
            const control = content.querySelector('.docsViewerReport__detailOpen');
            const controlRow = control.closest('[data-docs-content-detail-control="report"]');
            const embedded = {
                controlImmediatelyBeforeRoot: controlRow.nextSibling === reportRoot,
                controlLabel: control.getAttribute('aria-label'),
                frozenTarget: Object.isFrozen(registration.targetContext)
                    && Object.isFrozen(registration.targetContext.documentTarget)
                    && Object.isFrozen(registration.targetContext.reportTarget),
                registered: registration.registered,
                target: registration.targetContext
            };
            control.click();

            const projectedControls = {};
            const view = modules.contentDetail.createDocsViewerContentDetailView({
                reportPresentationAdapter: adapter
            });
            const viewContext = {
                mainView: {
                    projectControlState: (id, state) => { projectedControls[id] = state; },
                    showWarning: () => {}
                },
                mount: content,
                requestReason: 'content-detail-open',
                targetContext: requested[0]
            };
            view.mount(viewContext);
            const detailRoot = content.querySelector('[data-docs-content-detail-view="report"]');
            const viewport = detailRoot.querySelector('.docsViewerReport__expandedViewport');
            stateButton.click();
            reportRoot.querySelector('input').value = 'edited-live';
            const expanded = {
                activeMarker: content.dataset.docsContentDetailActive,
                exactLiveRoot: viewport.firstElementChild === reportRoot,
                label: projectedControls['content-detail-label'].label,
                newTabHidden: projectedControls['content-detail-open-new-tab'].hidden,
                state: reportState,
                value: reportRoot.querySelector('input').value
            };

            view.unmount(Object.assign({}, viewContext, { requestReason: 'back' }));
            const restored = {
                activeMarkerRemoved: !content.hasAttribute('data-docs-content-detail-active'),
                controlBeforeRoot: controlRow.nextSibling === reportRoot,
                detailRemoved: !content.querySelector('[data-docs-content-detail-view]'),
                exactIdentity: content.querySelector('#report') === reportRoot,
                state: reportState,
                value: reportRoot.querySelector('input').value
            };

            view.mount(viewContext);
            view.unmount(Object.assign({}, viewContext, { requestReason: 'document-navigation' }));
            const navigated = {
                detailRemoved: !content.querySelector('[data-docs-content-detail-view]'),
                reportRemoved: !reportRoot.isConnected
            };
            const released = adapter.releaseDocument({ content, document });
            let staleMessage = '';
            try {
                adapter.mountPresentation({
                    content, document, targetContext: registration.targetContext
                });
            } catch (error) {
                staleMessage = error.message;
            }

            const absentContent = document.createElement('div');
            const absentRoot = document.createElement('div');
            absentContent.appendChild(absentRoot);
            const absent = adapter.registerMountedReport({
                content: absentContent,
                doc: { doc_id: 'd-absent' },
                document,
                documentMountGeneration: 8,
                mountResult: true,
                reportMeta: { reportId: 'plain' },
                reportRoot: absentRoot,
                viewerScope: 'studio'
            });
            const invalid = adapter.registerMountedReport({
                content: absentContent,
                doc: { doc_id: 'd-invalid' },
                document,
                documentMountGeneration: 9,
                mountResult: {
                    expandedPresentation: {
                        kind: 'flow', label: 'Invalid', table: document.createElement('table')
                    }
                },
                reportMeta: { reportId: 'invalid' },
                reportRoot: absentRoot,
                viewerScope: 'studio'
            });

            const semanticContent = document.createElement('div');
            const semanticRoot = document.createElement('div');
            const semanticTable = document.createElement('table');
            semanticRoot.appendChild(semanticTable);
            semanticContent.appendChild(semanticRoot);
            const semantic = adapter.registerMountedReport({
                content: semanticContent,
                doc: { doc_id: 'd-semantic' },
                document,
                documentMountGeneration: 10,
                mountResult: {
                    expandedPresentation: {
                        kind: 'semantic-table',
                        label: 'Semantic report',
                        table: semanticTable,
                        columns: [{ id: 'work', label: 'Work' }],
                        subscribe: () => () => {}
                    }
                },
                reportMeta: { reportId: 'semantic' },
                reportRoot: semanticRoot,
                viewerScope: 'studio'
            });

            return {
                absent,
                embedded,
                expanded,
                invalid,
                navigated,
                released,
                restored,
                semanticRegistered: semantic.registered,
                staleMessage,
                warningCount: warnings.length
            };
        }"""
    )
    if result["embedded"] != {
        "controlImmediatelyBeforeRoot": True,
        "controlLabel": "Open Catalogue Works in expanded view",
        "frozenTarget": True,
        "registered": True,
        "target": {
            "documentMountGeneration": 7,
            "documentTarget": {"docId": "d-report", "scope": "studio"},
            "kind": "report",
            "reportTarget": {
                "preset": "works",
                "reportId": "catalogue_works",
                "scope": "studio",
                "subScope": "",
            },
        },
    }:
        raise AssertionError(f"exact report registration changed: {result!r}")
    if result["expanded"] != {
        "activeMarker": "true",
        "exactLiveRoot": True,
        "label": "Catalogue Works",
        "newTabHidden": True,
        "state": 1,
        "value": "edited-live",
    }:
        raise AssertionError(f"live report expansion changed: {result!r}")
    if result["restored"] != {
        "activeMarkerRemoved": True,
        "controlBeforeRoot": True,
        "detailRemoved": True,
        "exactIdentity": True,
        "state": 1,
        "value": "edited-live",
    }:
        raise AssertionError(f"Back did not restore the exact live report: {result!r}")
    if result["navigated"] != {"detailRemoved": True, "reportRemoved": True}:
        raise AssertionError(f"navigation restored stale report content: {result!r}")
    if result["released"] != {"released": 1}:
        raise AssertionError(f"report registration cleanup changed: {result!r}")
    if "stale or unavailable" not in result["staleMessage"]:
        raise AssertionError(f"stale report target was accepted: {result!r}")
    if result["absent"] != {"registered": False, "reason": "absent"}:
        raise AssertionError(f"absent capability was not ordinary: {result!r}")
    if result["invalid"] != {"registered": False, "reason": "invalid"}:
        raise AssertionError(f"invalid capability did not fail closed: {result!r}")
    if result["warningCount"] != 1 or not result["semanticRegistered"]:
        raise AssertionError(f"capability validation changed: {result!r}")


def assert_content_detail_capture_and_document_release(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const modules = window.__docsViewerExpandedReportSmoke;
            const mount = document.createElement('div');
            document.body.replaceChildren(mount);
            let scrollX = 13;
            let scrollY = 17;
            let restoredScroll = null;
            let releaseContext = null;
            Object.defineProperty(window, 'scrollX', { configurable: true, get: () => scrollX });
            Object.defineProperty(window, 'scrollY', { configurable: true, get: () => scrollY });
            window.scrollTo = value => { restoredScroll = value; };
            const focusTarget = document.createElement('button');
            const invocationControl = document.createElement('button');
            mount.appendChild(invocationControl);
            const fakeAdapter = {
                mountPresentation() {
                    scrollX = 99;
                    scrollY = 101;
                    const root = document.createElement('section');
                    return {
                        focusTarget,
                        invocationControl,
                        label: 'Report',
                        root,
                        release(context) { releaseContext = context; root.remove(); }
                    };
                }
            };
            const view = modules.contentDetail.createDocsViewerContentDetailView({
                reportPresentationAdapter: fakeAdapter
            });
            const context = {
                mainView: { projectControlState: () => {}, showWarning: () => {} },
                mount,
                targetContext: { kind: 'report' }
            };
            view.mount(context);
            view.unmount(Object.assign({}, context, { requestReason: 'back' }));

            const reportReleases = [];
            let extras = null;
            const reportAdapter = {
                releaseDocument(context) { reportReleases.push(context.content); }
            };
            const requestContentDetail = () => true;
            const content = document.createElement('article');
            const controller = modules.documentController.initDocsViewerDocumentController({
                content,
                toolbar: document.createElement('div'),
                results: document.createElement('div'),
                more: document.createElement('div'),
                reportPresentationAdapter: reportAdapter,
                mountDocumentExtras: context => { extras = context; },
                requestContentDetail,
                viewerScope: () => 'studio',
                scopeConfig: {
                    scopeConfigsById: new Map([['studio', { scopeId: 'studio', scopeType: 'local' }]])
                },
                selectedDocument: { selectedDocId: '' },
                routeSession: { managementContext: true },
                hasActiveQuery: () => false,
                clearResultsStatus: () => {},
                setRecentModeActive: () => {},
                projectDocumentShell: () => {},
                renderBookmarkToggle: () => {},
                renderBookmarkUi: () => {},
                renderManagementUi: () => {},
                renderMeta: () => {},
                renderSearchMode: () => {},
                renderSidebar: () => {},
                statusCommands: { setStatus: () => {} }
            });
            controller.renderPayload(
                { doc_id: 'd-report', title: 'Report' },
                { content_html: '<div data-docs-viewer-report-host></div>' },
                ''
            );
            controller.showSearchPane();
            controller.renderDocLoadingState({ doc_id: 'd-next', title: 'Next' });
            controller.handleMissingDoc();
            return {
                extras: {
                    adapterShared: extras.reportPresentationAdapter === reportAdapter,
                    generation: extras.documentMountGeneration,
                    requestShared: extras.requestContentDetail === requestContentDetail
                },
                releaseContext,
                releaseCount: reportReleases.length,
                releaseRootsExact: reportReleases.every(root => root === content),
                restoredScroll
            };
        }"""
    )
    if result["restoredScroll"] != {
        "behavior": "auto",
        "left": 13,
        "top": 17,
    }:
        raise AssertionError(f"Content Detail captured scroll after the live move: {result!r}")
    if result["releaseContext"] != {
        "requestReason": "back",
        "restoreDocumentContext": True,
    }:
        raise AssertionError(f"Content Detail did not pass the release reason: {result!r}")
    if result["extras"] != {
        "adapterShared": True,
        "generation": 1,
        "requestShared": True,
    }:
        raise AssertionError(f"document extras did not receive exact report context: {result!r}")
    if result["releaseCount"] != 4 or not result["releaseRootsExact"]:
        raise AssertionError(f"document lifecycle did not release report registration: {result!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, default=Path("site"))
    parser.add_argument("--timeout-ms", type=int, default=10000)
    args = parser.parse_args()

    assert_static_composition()
    server, base_url = start_static_server(args.site_root)
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.set_default_timeout(args.timeout_ms)
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on(
                    "console",
                    lambda message: errors.append(message.text)
                    if message.type == "error"
                    else None,
                )
                page.goto(f"{base_url}/404.html", wait_until="domcontentloaded")
                install_fixture(page)
                assert_live_report_lifecycle(page)
                assert_content_detail_capture_and_document_release(page)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if errors:
        raise AssertionError(f"page errors during expanded-report smoke: {errors!r}")
    print("Docs Viewer expanded report module smoke OK")


if __name__ == "__main__":
    main()

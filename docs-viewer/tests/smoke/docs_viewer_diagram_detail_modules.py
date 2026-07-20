#!/usr/bin/env python3
"""Smoke-check the focused Docs Viewer persistent diagram-detail contracts."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_VIEWER_SHARED_RUNTIME_PREFIX = "/docs-viewer/runtime/js/shared/"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        clean_path = path.split("?", 1)[0].split("#", 1)[0]
        if clean_path.startswith(DOCS_VIEWER_SHARED_RUNTIME_PREFIX):
            relative_path = clean_path.removeprefix(DOCS_VIEWER_SHARED_RUNTIME_PREFIX)
            return str(REPO_ROOT / "site/docs-viewer/runtime/js/shared" / relative_path)
        return super().translate_path(path)


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def install_fixture(page: Page) -> None:
    page.evaluate(
        """async () => {
            await new Promise((resolve, reject) => {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = '/docs-viewer/static/css/docs-viewer.css';
                link.addEventListener('load', resolve, { once: true });
                link.addEventListener('error', () => reject(new Error('Docs Viewer stylesheet did not load.')), { once: true });
                document.head.appendChild(link);
            });
            const diagramDetail = await import('/docs-viewer/runtime/js/shared/docs-viewer-diagram-detail.js');
            const documentController = await import('/docs-viewer/runtime/js/shared/docs-viewer-document-controller.js');
            window.__docsViewerDiagramDetailSmoke = { diagramDetail, documentController };
        }"""
    )


def assert_persistent_adapter_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { diagramDetail } = window.__docsViewerDiagramDetailSmoke;
            const shell = document.createElement('div');
            shell.className = 'docsViewer';
            const content = document.createElement('article');
            content.className = 'docsViewer__content';
            content.innerHTML = [
                '<p><img id="same-origin" data-docs-viewer-diagram-kind="persistent-svg" src="/assets/data/docs/scopes/library/media/svg/one.svg" alt="One" style="width: 240px; height: 120px"></p>',
                '<p><img id="absolute" data-docs-viewer-diagram-kind="persistent-svg" src="https://media.example.test/docs/two.svg" alt="Two" style="width: 220px; height: 110px"></p>',
                '<p><img id="ordinary" src="/assets/data/docs/scopes/library/media/svg/ordinary.svg" alt="Ordinary SVG"></p>',
                '<div class="docsViewer__diagram" data-docs-viewer-diagram-kind="inline-mermaid"><svg><title>Inline</title><desc>Deferred until DDV-2</desc></svg></div>',
                '<p><img id="missing-target" data-docs-viewer-diagram-kind="persistent-svg" alt="Missing target"></p>'
            ].join('');
            shell.appendChild(content);
            document.body.appendChild(shell);

            const sameOrigin = content.querySelector('#same-origin');
            const before = sameOrigin.getBoundingClientRect();
            const adapter = diagramDetail.createDocsViewerDiagramDetailAdapter();
            const first = adapter.mountDocument({ content, document, window });
            const after = sameOrigin.getBoundingClientRect();
            const second = adapter.mountDocument({ content, document, window });
            const frames = Array.from(content.querySelectorAll('.docsViewer__diagramFrame'));
            const controls = Array.from(content.querySelectorAll('.docsViewer__diagramDetailControl'));
            const firstControl = controls[0];
            const firstFrame = frames[0];
            const firstViewport = firstFrame.querySelector('.docsViewer__diagramViewport');
            const frameStyle = getComputedStyle(firstFrame);
            const viewportStyle = getComputedStyle(firstViewport);
            const controlStyle = getComputedStyle(firstControl);
            const restOpacity = controlStyle.opacity;
            firstControl.focus();
            await new Promise(resolve => setTimeout(resolve, 150));
            const focusedStyle = getComputedStyle(firstControl);

            return {
                first,
                second,
                frameCount: frames.length,
                controlCount: controls.length,
                targets: controls.map(control => control.getAttribute('href')),
                targetAttrs: controls.map(control => ({
                    target: control.getAttribute('target'),
                    rel: control.getAttribute('rel'),
                    label: control.getAttribute('aria-label'),
                    title: control.getAttribute('title'),
                    tabIndex: control.tabIndex,
                    tagName: control.tagName
                })),
                exactShape: frames.every(frame =>
                    frame.children.length === 2
                    && frame.firstElementChild?.classList.contains('docsViewer__diagramViewport')
                    && frame.lastElementChild?.classList.contains('docsViewer__diagramDetailControl')
                    && frame.firstElementChild?.children.length === 1
                    && frame.firstElementChild?.firstElementChild?.dataset.docsViewerDiagramKind === 'persistent-svg'
                ),
                ordinaryDecorated: Boolean(content.querySelector('#ordinary')?.closest('.docsViewer__diagramFrame')),
                inlineDecorated: Boolean(content.querySelector('[data-docs-viewer-diagram-kind="inline-mermaid"]')?.closest('.docsViewer__diagramFrame')),
                missingDecorated: Boolean(content.querySelector('#missing-target')?.closest('.docsViewer__diagramFrame')),
                diagramIsLink: sameOrigin.parentElement?.tagName === 'A',
                framePosition: frameStyle.position,
                viewportOverflow: viewportStyle.overflowX,
                controlPosition: controlStyle.position,
                controlWidth: controlStyle.width,
                controlHeight: controlStyle.height,
                restOpacity,
                focusedOpacity: focusedStyle.opacity,
                focusOutlineWidth: focusedStyle.outlineWidth,
                imageGeometryStable: before.x === after.x && before.y === after.y && before.width === after.width && before.height === after.height,
                iconHidden: firstControl.querySelector('svg')?.getAttribute('aria-hidden') === 'true'
            };
        }"""
    )

    if result["first"] != {"found": 3, "decorated": 2, "skipped": 1}:
        raise AssertionError(f"persistent marker eligibility changed: {result!r}")
    if result["second"] != {"found": 3, "decorated": 0, "skipped": 3}:
        raise AssertionError(f"repeat mount duplicated diagram controls: {result!r}")
    if result["frameCount"] != 2 or result["controlCount"] != 2 or not result["exactShape"]:
        raise AssertionError(f"shared persistent frame shape changed: {result!r}")
    if result["targets"] != [
        "/assets/data/docs/scopes/library/media/svg/one.svg",
        "https://media.example.test/docs/two.svg",
    ]:
        raise AssertionError(f"stable persistent targets were not preserved: {result!r}")
    expected_attrs = {
        "target": "_blank",
        "rel": "noopener",
        "label": "Open diagram in new tab",
        "title": "Open diagram in new tab",
        "tabIndex": 0,
        "tagName": "A",
    }
    if any(attrs != expected_attrs for attrs in result["targetAttrs"]):
        raise AssertionError(f"native accessible new-tab link contract changed: {result!r}")
    if result["ordinaryDecorated"] or result["inlineDecorated"] or result["missingDecorated"]:
        raise AssertionError(f"the persistent adapter decorated an unsupported surface: {result!r}")
    if result["diagramIsLink"] or not result["iconHidden"]:
        raise AssertionError(f"the diagram body or control icon acquired the wrong semantics: {result!r}")
    if result["framePosition"] != "relative" or result["viewportOverflow"] != "auto":
        raise AssertionError(f"diagram frame or viewport ownership changed: {result!r}")
    if result["controlPosition"] != "absolute" or result["controlWidth"] != "32px" or result["controlHeight"] != "32px":
        raise AssertionError(f"detail control geometry changed: {result!r}")
    if not result["imageGeometryStable"]:
        raise AssertionError(f"persistent decoration changed image geometry: {result!r}")
    if float(result["focusedOpacity"]) != 1 or result["focusOutlineWidth"] != "2px":
        raise AssertionError(f"focused control is not fully visible: {result!r}")


def assert_document_controller_mount_contract(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const { documentController } = window.__docsViewerDiagramDetailSmoke;

            function exercise(scopeId, scopeType, includeInlineAdapter) {
                const content = document.createElement('article');
                const order = [];
                const detailMounts = [];
                const controller = documentController.initDocsViewerDocumentController({
                    content,
                    toolbar: document.createElement('div'),
                    results: document.createElement('div'),
                    more: document.createElement('div'),
                    diagramDetailAdapter: {
                        mountDocument(context) {
                            order.push('detail');
                            detailMounts.push(context);
                        }
                    },
                    inlineMermaidAdapter: includeInlineAdapter ? {
                        mountDocument() {
                            order.push('inline');
                        }
                    } : null,
                    mountDocumentExtras: () => order.push('extras'),
                    viewerScope: () => scopeId,
                    scopeConfig: {
                        scopeConfigsById: new Map([[scopeId, { scopeId, scopeType }]])
                    },
                    selectedDocument: { selectedDocId: '' },
                    routeSession: { managementContext: false },
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
                const html = '<p><img data-docs-viewer-diagram-kind="persistent-svg" src="/diagram.svg" alt="Diagram"></p>';
                controller.renderPayload({ doc_id: scopeId, title: scopeId }, { content_html: html }, '');
                return {
                    order,
                    htmlAtMount: detailMounts[0].content.innerHTML,
                    scopeType: detailMounts[0].scopeType,
                    viewerScope: detailMounts[0].viewerScope
                };
            }

            return {
                local: exercise('studio', 'local', true),
                external: exercise('notes', 'local_external', false),
                publicScope: exercise('library', 'public', false)
            };
        }"""
    )

    if result["local"]["order"] != ["detail", "inline", "extras"]:
        raise AssertionError(f"local post-mount adapter order changed: {result!r}")
    for key, scope_type, scope_id in (
        ("local", "local", "studio"),
        ("external", "local_external", "notes"),
        ("publicScope", "public", "library"),
    ):
        record = result[key]
        if record["scopeType"] != scope_type or record["viewerScope"] != scope_id:
            raise AssertionError(f"diagram detail scope context changed: {result!r}")
        if 'data-docs-viewer-diagram-kind="persistent-svg"' not in record["htmlAtMount"]:
            raise AssertionError(f"detail adapter ran before generated HTML mounted: {result!r}")
    if (
        result["external"]["order"] != ["detail", "extras"]
        or result["publicScope"]["order"] != ["detail", "extras"]
    ):
        raise AssertionError(f"persistent detail did not run on every ordinary reader scope: {result!r}")


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/404.html", wait_until="domcontentloaded")
    install_fixture(page)
    assert_persistent_adapter_contract(page)
    assert_document_controller_mount_contract(page)


def fulfill_fixture_images(route) -> None:
    if route.request.resource_type == "image":
        route.fulfill(
            status=200,
            content_type="image/svg+xml",
            body='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 1"></svg>',
        )
        return
    route.continue_()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, default=Path("site"))
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
                page.route("**/*", fulfill_fixture_images)
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
                run_smoke(page, base_url)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if errors:
        raise AssertionError(f"page errors during Docs Viewer diagram detail smoke: {errors!r}")
    print("Docs Viewer diagram detail module smoke OK")


if __name__ == "__main__":
    main()

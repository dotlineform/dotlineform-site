#!/usr/bin/env python3
"""Smoke-check the focused Docs Viewer inline Mermaid runtime contracts."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_VIEWER_SHARED_RUNTIME_PREFIX = "/docs-viewer/runtime/js/shared/"
DOCS_VIEWER_REPO_RUNTIME_PREFIX = "/docs-viewer/runtime/js/"
DOCS_VIEWER_REPO_VENDOR_PREFIX = "/docs-viewer/runtime/vendor/"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        clean_path = path.split("?", 1)[0].split("#", 1)[0]
        if clean_path.startswith(DOCS_VIEWER_SHARED_RUNTIME_PREFIX):
            relative_path = clean_path.removeprefix(DOCS_VIEWER_SHARED_RUNTIME_PREFIX)
            return str(REPO_ROOT / "site/docs-viewer/runtime/js/shared" / relative_path)
        if clean_path.startswith(DOCS_VIEWER_REPO_RUNTIME_PREFIX):
            relative_path = clean_path.removeprefix(DOCS_VIEWER_REPO_RUNTIME_PREFIX)
            return str(REPO_ROOT / "docs-viewer/runtime/js" / relative_path)
        if clean_path.startswith(DOCS_VIEWER_REPO_VENDOR_PREFIX):
            relative_path = clean_path.removeprefix(DOCS_VIEWER_REPO_VENDOR_PREFIX)
            return str(REPO_ROOT / "docs-viewer/runtime/vendor" / relative_path)
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
                const existing = document.querySelector('link[data-inline-mermaid-smoke-styles]');
                if (existing?.sheet) {
                    resolve();
                    return;
                }
                const link = existing || document.createElement('link');
                link.rel = 'stylesheet';
                link.href = '/docs-viewer/static/css/docs-viewer.css';
                link.dataset.inlineMermaidSmokeStyles = 'true';
                link.addEventListener('load', resolve, { once: true });
                link.addEventListener('error', () => reject(new Error('Docs Viewer stylesheet did not load.')), { once: true });
                if (!existing) document.head.appendChild(link);
            });
            document.body.classList.add('docsViewer');
            const inlineMermaid = await import('/docs-viewer/runtime/js/management/docs-viewer-inline-mermaid.js');
            const documentController = await import('/docs-viewer/runtime/js/shared/docs-viewer-document-controller.js');
            window.__docsViewerInlineMermaidSmoke = { inlineMermaid, documentController };
        }"""
    )


def assert_session_renderer_and_failure_containment(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { inlineMermaid } = window.__docsViewerInlineMermaidSmoke;
            let loadCalls = 0;
            let activeRenders = 0;
            let maxActiveRenders = 0;
            const initializationConfigs = [];
            const renderCalls = [];
            const warnings = [];
            const boundHosts = [];
            const renderer = {
                initialize(config) {
                    initializationConfigs.push(config);
                },
                async render(id, source) {
                    activeRenders += 1;
                    maxActiveRenders = Math.max(maxActiveRenders, activeRenders);
                    renderCalls.push({ id, source });
                    await Promise.resolve();
                    activeRenders -= 1;
                    if (source.includes('invalid')) throw new Error('synthetic parser detail');
                    return {
                        svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><title>${source} title</title><desc>${source} description</desc><path d="M0 0h10v10z"/></svg>`,
                        bindFunctions(host) {
                            boundHosts.push(host.dataset.docsViewerDiagramKind);
                        }
                    };
                }
            };
            const adapter = inlineMermaid.createDocsViewerInlineMermaidAdapter({
                loadMermaid: async () => {
                    loadCalls += 1;
                    return renderer;
                },
                warn: (message, error) => warnings.push({ message, detail: error.message })
            });

            const first = document.createElement('article');
            first.innerHTML = [
                '<pre><code class="language-mermaid">first</code></pre>',
                '<pre><code class="language-mermaid">invalid middle</code></pre>',
                '<pre><code class="language-mermaid">third</code></pre>'
            ].join('');
            document.body.appendChild(first);
            const firstResult = await adapter.mountDocument({ content: first });
            const duplicateResult = await adapter.mountDocument({ content: first });

            const second = document.createElement('article');
            second.innerHTML = '<pre><code class="language-mermaid">fourth</code></pre>';
            document.body.appendChild(second);
            const secondResult = await adapter.mountDocument({ content: second });

            let emptyLoadCalls = 0;
            const emptyAdapter = inlineMermaid.createDocsViewerInlineMermaidAdapter({
                loadMermaid: async () => {
                    emptyLoadCalls += 1;
                    return renderer;
                }
            });
            const empty = document.createElement('article');
            empty.innerHTML = '<p>No diagram</p>';
            const emptyResult = await emptyAdapter.mountDocument({ content: empty });

            let concurrentActive = 0;
            let maxConcurrentActive = 0;
            const concurrentAdapter = inlineMermaid.createDocsViewerInlineMermaidAdapter({
                loadMermaid: async () => ({
                    initialize() {},
                    async render(id) {
                        concurrentActive += 1;
                        maxConcurrentActive = Math.max(maxConcurrentActive, concurrentActive);
                        await new Promise(resolve => setTimeout(resolve, 0));
                        concurrentActive -= 1;
                        return {
                            svg: `<svg xmlns="http://www.w3.org/2000/svg"><title>${id}</title><desc>concurrent mount proof</desc></svg>`
                        };
                    }
                })
            });
            const concurrentFirst = document.createElement('article');
            const concurrentSecond = document.createElement('article');
            concurrentFirst.innerHTML = '<pre><code class="language-mermaid">concurrent first</code></pre>';
            concurrentSecond.innerHTML = '<pre><code class="language-mermaid">concurrent second</code></pre>';
            document.body.append(concurrentFirst, concurrentSecond);
            await Promise.all([
                concurrentAdapter.mountDocument({ content: concurrentFirst }),
                concurrentAdapter.mountDocument({ content: concurrentSecond })
            ]);

            const failureStatus = first.querySelector('.docsViewer__diagramError');
            const retainedSource = first.querySelector('pre > code.language-mermaid');
            const hosts = Array.from(document.querySelectorAll('.docsViewer__diagram'));
            return {
                loadCalls,
                initializationConfigs,
                renderCalls,
                maxActiveRenders,
                warnings,
                boundHosts,
                firstResult,
                duplicateResult,
                secondResult,
                emptyResult,
                emptyLoadCalls,
                maxConcurrentActive,
                hostCount: hosts.length,
                hostsAreExact: hosts.every(host =>
                    host.dataset.docsViewerDiagramKind === 'inline-mermaid'
                    && host.children.length === 1
                    && host.firstElementChild?.namespaceURI === 'http://www.w3.org/2000/svg'
                ),
                retainedSource: retainedSource?.textContent || '',
                retainedState: retainedSource?.parentElement?.dataset.docsViewerInlineMermaidState || '',
                failureText: failureStatus?.textContent || '',
                failureRole: failureStatus?.getAttribute('role') || '',
                failureLive: failureStatus?.getAttribute('aria-live') || '',
                failureAssociated: retainedSource?.parentElement?.getAttribute('aria-describedby') === failureStatus?.id,
                failureBeforeSource: failureStatus?.nextElementSibling === retainedSource?.parentElement,
                failureDisplay: failureStatus ? getComputedStyle(failureStatus).display : '',
                failureVisibility: failureStatus ? getComputedStyle(failureStatus).visibility : '',
                failureBorderWidth: failureStatus ? getComputedStyle(failureStatus).borderInlineStartWidth : '',
                sourceDisplay: retainedSource?.parentElement ? getComputedStyle(retainedSource.parentElement).display : ''
            };
        }"""
    )

    if result["loadCalls"] != 1 or len(result["initializationConfigs"]) != 1:
        raise AssertionError(f"Mermaid did not load and initialize once per adapter session: {result!r}")
    expected_config = {
        "startOnLoad": False,
        "theme": "neutral",
        "securityLevel": "strict",
        "htmlLabels": False,
        "flowchart": {"htmlLabels": False},
    }
    if result["initializationConfigs"] != [expected_config]:
        raise AssertionError(f"Mermaid strict initialization changed: {result!r}")
    if result["maxActiveRenders"] != 1:
        raise AssertionError(f"multiple Mermaid fences rendered concurrently: {result!r}")
    if result["maxConcurrentActive"] != 1:
        raise AssertionError(f"separate document mounts rendered Mermaid concurrently: {result!r}")
    if [call["source"] for call in result["renderCalls"]] != ["first", "invalid middle", "third", "fourth"]:
        raise AssertionError(f"Mermaid source order changed: {result!r}")
    render_ids = [call["id"] for call in result["renderCalls"]]
    if len(set(render_ids)) != 4 or render_ids != [f"docs-viewer-inline-mermaid-{index}" for index in range(1, 5)]:
        raise AssertionError(f"Mermaid render identities are not unique and sequential: {result!r}")
    if result["firstResult"] != {"found": 3, "rendered": 2, "failed": 1, "stale": False}:
        raise AssertionError(f"one broken diagram was not contained: {result!r}")
    if result["secondResult"] != {"found": 1, "rendered": 1, "failed": 0, "stale": False}:
        raise AssertionError(f"later document mount did not reuse the session renderer: {result!r}")
    if result["duplicateResult"] != {"found": 0, "rendered": 0, "failed": 0, "stale": False}:
        raise AssertionError(f"processed fences were not protected from duplicate rendering: {result!r}")
    if result["emptyResult"]["found"] != 0 or result["emptyLoadCalls"] != 0:
        raise AssertionError(f"a diagram-free mount loaded Mermaid: {result!r}")
    if result["hostCount"] != 5 or not result["hostsAreExact"] or result["boundHosts"] != ["inline-mermaid"] * 3:
        raise AssertionError(f"successful diagrams did not use the settled host contract: {result!r}")
    if result["retainedSource"] != "invalid middle" or result["retainedState"] != "error":
        raise AssertionError(f"failed Mermaid source was not retained: {result!r}")
    if result["failureText"] != "Diagram could not be rendered. Mermaid source is shown below.":
        raise AssertionError(f"visible Mermaid failure copy changed: {result!r}")
    if result["failureRole"] != "status" or result["failureLive"] != "polite" or not result["failureAssociated"]:
        raise AssertionError(f"Mermaid failure was not politely associated with its source: {result!r}")
    if (
        not result["failureBeforeSource"]
        or result["failureDisplay"] == "none"
        or result["failureVisibility"] != "visible"
        or result["failureBorderWidth"] != "3px"
        or result["sourceDisplay"] == "none"
    ):
        raise AssertionError(f"Mermaid failure and retained source were not visibly ordered: {result!r}")
    if result["warnings"] != [{"message": "docs_viewer: inline Mermaid diagram unavailable", "detail": "synthetic parser detail"}]:
        raise AssertionError(f"Mermaid detailed failure did not stay in diagnostics: {result!r}")


def assert_stale_mount_cannot_replace_content(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { inlineMermaid } = window.__docsViewerInlineMermaidSmoke;
            let finishRender;
            let renderStarted;
            const started = new Promise(resolve => { renderStarted = resolve; });
            const renderer = {
                initialize() {},
                async render() {
                    renderStarted();
                    await new Promise(resolve => { finishRender = resolve; });
                    return {
                        svg: '<svg xmlns="http://www.w3.org/2000/svg"><title>stale title</title><desc>stale description</desc></svg>'
                    };
                }
            };
            const adapter = inlineMermaid.createDocsViewerInlineMermaidAdapter({
                loadMermaid: async () => renderer,
                warn: () => {}
            });
            const content = document.createElement('article');
            content.innerHTML = '<pre><code class="language-mermaid">slow</code></pre>';
            document.body.appendChild(content);
            let current = true;
            const mountPromise = adapter.mountDocument({
                content,
                isCurrentMount: () => current
            });
            await started;
            current = false;
            content.innerHTML = '<p id="replacement">replacement document</p>';
            finishRender();
            const mountResult = await mountPromise;
            return {
                mountResult,
                html: content.innerHTML,
                diagramCount: content.querySelectorAll('.docsViewer__diagram').length,
                errorCount: content.querySelectorAll('.docsViewer__diagramError').length
            };
        }"""
    )
    if result["mountResult"] != {"found": 1, "rendered": 0, "failed": 0, "stale": True}:
        raise AssertionError(f"stale Mermaid result was not identified: {result!r}")
    if result["html"] != '<p id="replacement">replacement document</p>' or result["diagramCount"] or result["errorCount"]:
        raise AssertionError(f"stale Mermaid result changed replacement content: {result!r}")


def assert_accessible_svg_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { inlineMermaid } = window.__docsViewerInlineMermaidSmoke;
            const warnings = [];
            const adapter = inlineMermaid.createDocsViewerInlineMermaidAdapter({
                loadMermaid: async () => ({
                    initialize() {},
                    async render() {
                        return { svg: '<svg xmlns="http://www.w3.org/2000/svg"><path/></svg>' };
                    }
                }),
                warn: (message, error) => warnings.push(error.message)
            });
            const content = document.createElement('article');
            content.innerHTML = '<pre><code class="language-mermaid">missing accessibility</code></pre>';
            document.body.appendChild(content);
            const mountResult = await adapter.mountDocument({ content });
            return {
                mountResult,
                source: content.querySelector('code')?.textContent || '',
                diagramCount: content.querySelectorAll('.docsViewer__diagram').length,
                errorText: content.querySelector('.docsViewer__diagramError')?.textContent || '',
                warnings
            };
        }"""
    )
    if result["mountResult"] != {"found": 1, "rendered": 0, "failed": 1, "stale": False}:
        raise AssertionError(f"inaccessible Mermaid SVG was accepted: {result!r}")
    if result["source"] != "missing accessibility" or result["diagramCount"] != 0:
        raise AssertionError(f"inaccessible Mermaid fallback did not retain source: {result!r}")
    if result["warnings"] != ["Inline Mermaid SVG requires a non-empty title and description."]:
        raise AssertionError(f"accessible SVG contract diagnostic changed: {result!r}")


def assert_checked_browser_runtime_renders(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { inlineMermaid } = window.__docsViewerInlineMermaidSmoke;
            const content = document.createElement('article');
            const pre = document.createElement('pre');
            const code = document.createElement('code');
            code.className = 'language-mermaid';
            code.textContent = [
                'flowchart LR',
                '  accTitle: Inline renderer proof',
                '  accDescr: A short path from source to rendered SVG',
                '  Source --> SVG'
            ].join('\\n');
            pre.appendChild(code);
            content.appendChild(pre);
            document.body.appendChild(content);
            const mountResult = await inlineMermaid.docsViewerInlineMermaidAdapter.mountDocument({ content });

            const mixed = document.createElement('article');
            mixed.innerHTML = [
                '<pre><code class="language-mermaid">flowchart LR\\n  accTitle: First mixed proof\\n  accDescr: The first valid diagram renders before a contained error\\n  A --&gt; B</code></pre>',
                '<pre><code class="language-mermaid">not a Mermaid diagram</code></pre>',
                '<pre><code class="language-mermaid">sequenceDiagram\\n  accTitle: Later mixed proof\\n  accDescr: A later valid diagram renders after an invalid source\\n  participant A\\n  participant B\\n  A-&gt;&gt;B: Continue</code></pre>'
            ].join('');
            document.body.appendChild(mixed);
            const diagnostics = [];
            const originalWarn = console.warn;
            console.warn = (...args) => {
                if (String(args[0] || '').startsWith('docs_viewer:')) {
                    diagnostics.push({ message: String(args[0]), detail: String(args[1]?.message || args[1] || '') });
                }
            };
            let mixedResult;
            try {
                mixedResult = await inlineMermaid.docsViewerInlineMermaidAdapter.mountDocument({ content: mixed });
            } finally {
                console.warn = originalWarn;
            }
            const script = document.querySelector('script[data-docs-viewer-inline-mermaid-runtime]');
            const host = content.querySelector('.docsViewer__diagram');
            const mixedError = mixed.querySelector('.docsViewer__diagramError');
            const mixedSource = mixed.querySelector('pre > code.language-mermaid');
            return {
                mountResult,
                mixedResult,
                assetVersion: script?.dataset.docsViewerInlineMermaidRuntime || '',
                assetPath: script?.getAttribute('src') || '',
                hostKind: host?.dataset.docsViewerDiagramKind || '',
                title: host?.querySelector('svg title')?.textContent || '',
                description: host?.querySelector('svg desc')?.textContent || '',
                sourceCount: content.querySelectorAll('pre > code.language-mermaid').length,
                mixedHostCount: mixed.querySelectorAll('.docsViewer__diagram').length,
                mixedSourceCount: mixed.querySelectorAll('pre > code.language-mermaid').length,
                mixedSource: mixedSource?.textContent || '',
                mixedErrorText: mixedError?.textContent || '',
                mixedDiagnosticCount: diagnostics.length,
                mixedDiagnosticMessage: diagnostics[0]?.message || '',
                mixedDiagnosticHasDetail: Boolean(diagnostics[0]?.detail),
                diagnosticLeakedToContent: diagnostics.some(item => mixed.textContent.includes(item.detail))
            };
        }"""
    )
    if result["mountResult"] != {"found": 1, "rendered": 1, "failed": 0, "stale": False}:
        raise AssertionError(f"checked Mermaid browser runtime did not render: {result!r}")
    if result["assetVersion"] != "11.16.0" or result["assetPath"] != "/docs-viewer/runtime/vendor/mermaid/11.16.0/mermaid.min.js":
        raise AssertionError(f"inline renderer did not load the checked Mermaid asset: {result!r}")
    if result["hostKind"] != "inline-mermaid" or result["sourceCount"] != 0:
        raise AssertionError(f"checked Mermaid render did not use the settled host: {result!r}")
    if result["title"] != "Inline renderer proof" or result["description"] != "A short path from source to rendered SVG":
        raise AssertionError(f"checked Mermaid render did not preserve accessible text: {result!r}")
    if result["mixedResult"] != {"found": 3, "rendered": 2, "failed": 1, "stale": False}:
        raise AssertionError(f"checked Mermaid runtime did not contain an invalid middle diagram: {result!r}")
    if result["mixedHostCount"] != 2 or result["mixedSourceCount"] != 1 or result["mixedSource"] != "not a Mermaid diagram":
        raise AssertionError(f"checked Mermaid runtime did not retain only the failed source: {result!r}")
    if result["mixedErrorText"] != "Diagram could not be rendered. Mermaid source is shown below.":
        raise AssertionError(f"checked Mermaid runtime fallback changed: {result!r}")
    if (
        result["mixedDiagnosticCount"] != 1
        or result["mixedDiagnosticMessage"] != "docs_viewer: inline Mermaid diagram unavailable"
        or not result["mixedDiagnosticHasDetail"]
        or result["diagnosticLeakedToContent"]
    ):
        raise AssertionError(f"checked Mermaid diagnostic was not console-only: {result!r}")


def assert_document_mount_generation_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { documentController } = window.__docsViewerInlineMermaidSmoke;
            const content = document.createElement('article');
            const toolbar = document.createElement('div');
            const results = document.createElement('div');
            const more = document.createElement('div');
            document.body.append(content, toolbar, results, more);
            const order = [];
            const mounts = [];
            const adapter = {
                mountDocument(context) {
                    order.push(`inline:${context.doc.doc_id}`);
                    mounts.push(context);
                    return Promise.resolve();
                }
            };
            const controller = documentController.initDocsViewerDocumentController({
                content,
                toolbar,
                results,
                more,
                inlineMermaidAdapter: adapter,
                mountDocumentExtras: ({ doc }) => order.push(`extras:${doc.doc_id}`),
                viewerScope: () => 'studio',
                scopeConfig: {
                    scopeConfigsById: new Map([['studio', { scopeId: 'studio', scopeType: 'local' }]])
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

            controller.renderPayload(
                { doc_id: 'one', title: 'One' },
                { content_html: '<pre><code class="language-mermaid">one</code></pre>' },
                ''
            );
            const firstWasCurrent = mounts[0].isCurrentMount();
            const firstHtmlAtMount = mounts[0].content.innerHTML;
            controller.renderDocLoadingState({ doc_id: 'two', title: 'Two' });
            const firstAfterLoading = mounts[0].isCurrentMount();
            controller.renderPayload(
                { doc_id: 'two', title: 'Two' },
                { content_html: '<pre><code class="language-mermaid">two</code></pre>' },
                ''
            );
            const secondWasCurrent = mounts[1].isCurrentMount();
            controller.hideDocPane();
            const secondAfterHide = mounts[1].isCurrentMount();
            await Promise.resolve();

            return {
                order,
                firstWasCurrent,
                firstAfterLoading,
                secondWasCurrent,
                secondAfterHide,
                firstHtmlAtMount,
                firstScopeType: mounts[0].scopeType,
                firstViewerScope: mounts[0].viewerScope,
                generations: mounts.map(mount => mount.mountGeneration),
                selectedDocId: mounts[1].doc.doc_id
            };
        }"""
    )
    if result["order"] != ["inline:one", "extras:one", "inline:two", "extras:two"]:
        raise AssertionError(f"inline Mermaid adapter did not own the immediate post-mount slot: {result!r}")
    if not result["firstWasCurrent"] or result["firstAfterLoading"]:
        raise AssertionError(f"loading a replacement did not invalidate the first mount: {result!r}")
    if not result["secondWasCurrent"] or result["secondAfterHide"]:
        raise AssertionError(f"leaving rendered view did not invalidate the second mount: {result!r}")
    if result["firstHtmlAtMount"] != '<pre><code class="language-mermaid">one</code></pre>':
        raise AssertionError(f"adapter ran before generated HTML was mounted: {result!r}")
    if result["firstScopeType"] != "local" or result["firstViewerScope"] != "studio":
        raise AssertionError(f"adapter did not receive explicit content scope context: {result!r}")
    if len(set(result["generations"])) != 2 or result["selectedDocId"] != "two":
        raise AssertionError(f"document mount generations were not distinct: {result!r}")


def assert_exact_scope_gate(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { inlineMermaid, documentController } = window.__docsViewerInlineMermaidSmoke;

            async function exercise(scopeId, scopeType, contentHtml) {
                let loadCalls = 0;
                let mountCalls = 0;
                const rendererAdapter = inlineMermaid.createDocsViewerInlineMermaidAdapter({
                    loadMermaid: async () => {
                        loadCalls += 1;
                        return {
                            initialize() {},
                            async render() {
                                return {
                                    svg: '<svg xmlns="http://www.w3.org/2000/svg"><title>scope gate</title><desc>scope gate proof</desc></svg>'
                                };
                            }
                        };
                    }
                });
                const content = document.createElement('article');
                const controller = documentController.initDocsViewerDocumentController({
                    content,
                    toolbar: document.createElement('div'),
                    results: document.createElement('div'),
                    more: document.createElement('div'),
                    inlineMermaidAdapter: {
                        mountDocument(context) {
                            mountCalls += 1;
                            return rendererAdapter.mountDocument(context);
                        }
                    },
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
                document.body.appendChild(content);
                controller.renderPayload({ doc_id: scopeId, title: scopeId }, { content_html: contentHtml }, '');
                await new Promise(resolve => setTimeout(resolve, 0));
                return {
                    mountCalls,
                    loadCalls,
                    diagramCount: content.querySelectorAll('.docsViewer__diagram').length,
                    fenceCount: content.querySelectorAll('pre > code.language-mermaid').length
                };
            }

            const fence = '<pre><code class="language-mermaid">scope gate</code></pre>';
            return {
                arbitraryLocal: await exercise('another-local-scope', 'local', fence),
                diagramFreeLocal: await exercise('diagram-free-local', 'local', '<p>No diagram</p>'),
                external: await exercise('notes', 'local_external', fence),
                publicScope: await exercise('library', 'public', fence)
            };
        }"""
    )
    if result["arbitraryLocal"] != {"mountCalls": 1, "loadCalls": 1, "diagramCount": 1, "fenceCount": 0}:
        raise AssertionError(f"an arbitrary configured local scope was not eligible: {result!r}")
    if result["diagramFreeLocal"] != {"mountCalls": 1, "loadCalls": 0, "diagramCount": 0, "fenceCount": 0}:
        raise AssertionError(f"a diagram-free local mount loaded Mermaid: {result!r}")
    unsupported = {"mountCalls": 0, "loadCalls": 0, "diagramCount": 0, "fenceCount": 1}
    if result["external"] != unsupported or result["publicScope"] != unsupported:
        raise AssertionError(f"an unsupported scope did not retain its Mermaid fence without loading: {result!r}")


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/404.html", wait_until="domcontentloaded")
    install_fixture(page)
    assert_session_renderer_and_failure_containment(page)
    assert_stale_mount_cannot_replace_content(page)
    assert_accessible_svg_contract(page)
    assert_checked_browser_runtime_renders(page)
    assert_document_mount_generation_contract(page)
    assert_exact_scope_gate(page)


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
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
                run_smoke(page, base_url)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if errors:
        raise AssertionError(f"page errors during Docs Viewer inline Mermaid smoke: {errors!r}")
    print("Docs Viewer inline Mermaid module smoke OK")


if __name__ == "__main__":
    main()

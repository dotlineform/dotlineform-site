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
            document.documentElement.setAttribute('data-theme', 'light');
            for (const href of [
                '/docs-viewer/static/css/docs-viewer-theme.css',
                '/docs-viewer/static/css/docs-viewer.css'
            ]) {
                await new Promise((resolve, reject) => {
                    const existing = document.querySelector(`link[href="${href}"]`);
                    if (existing?.sheet) {
                        resolve();
                        return;
                    }
                    const link = existing || document.createElement('link');
                    link.rel = 'stylesheet';
                    link.href = href;
                    link.addEventListener('load', resolve, { once: true });
                    link.addEventListener('error', () => reject(
                        new Error(`Docs Viewer stylesheet did not load: ${href}`)
                    ), { once: true });
                    if (!existing) document.head.appendChild(link);
                });
            }
            document.body.classList.add('docsViewer');
            const inlineMermaid = await import('/docs-viewer/runtime/js/management/docs-viewer-inline-mermaid.js');
            const documentController = await import('/docs-viewer/runtime/js/shared/docs-viewer-document-controller.js');
            const diagramDetail = await import('/docs-viewer/runtime/js/shared/docs-viewer-diagram-detail.js');
            const appBoot = await import('/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js');
            window.__docsViewerInlineMermaidSmoke = {
                inlineMermaid,
                documentController,
                diagramDetail,
                appBoot
            };
        }"""
    )


def assert_theme_composition_callback(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { appBoot } = window.__docsViewerInlineMermaidSmoke;
            const root = document.createElement('div');
            root.className = 'docsViewer';
            root.innerHTML = `
                <button data-docs-viewer-theme-toggle>
                    <span data-docs-viewer-theme-icon="light"></span>
                    <span data-docs-viewer-theme-icon="dark"></span>
                </button>
            `;
            document.body.appendChild(root);
            document.documentElement.removeAttribute('data-theme');
            window.localStorage.setItem('theme', 'invented');
            const calls = [];
            const owner = await appBoot.initDocsViewerBootThemeToggle({
                root,
                document,
                window,
                appShellReady: Promise.resolve(),
                inlineMermaidAdapter: {
                    handleThemeChange(theme) {
                        calls.push({
                            theme,
                            attribute: document.documentElement.getAttribute('data-theme')
                        });
                    }
                },
                routeContext: {
                    appContext: {
                        routeAccess: { managementUi: true },
                        featurePolicy: { management: true }
                    }
                }
            });
            root.querySelector('[data-docs-viewer-theme-toggle]').click();
            owner.setTheme('invented');
            root.remove();
            return { owner: Boolean(owner), calls };
        }"""
    )
    expected = {
        "owner": True,
        "calls": [
            {"theme": "light", "attribute": "light"},
            {"theme": "dark", "attribute": "dark"},
            {"theme": "light", "attribute": "light"},
        ],
    }
    if result != expected:
        raise AssertionError(f"theme owner did not notify the inline Mermaid adapter: {result!r}")


def assert_session_renderer_and_failure_containment(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { inlineMermaid } = window.__docsViewerInlineMermaidSmoke;
            const semanticTheme = () => {
                const style = getComputedStyle(document.body);
                return {
                    panel: style.getPropertyValue('--docs-viewer-panel').trim(),
                    subtlePanel: style.getPropertyValue('--docs-viewer-panel-2').trim(),
                    primaryText: style.getPropertyValue('--docs-viewer-text').trim(),
                    strongBorder: style.getPropertyValue('--docs-viewer-border-strong').trim(),
                    mutedText: style.getPropertyValue('--docs-viewer-muted').trim(),
                    selectionSurface: style.getPropertyValue('--docs-viewer-selection-bg').trim(),
                    selectionText: style.getPropertyValue('--docs-viewer-selection-text').trim(),
                    canvas: style.getPropertyValue('--docs-viewer-bg').trim(),
                    fontFamily: style.getPropertyValue('--docs-viewer-font-sans').trim()
                };
            };
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

            document.documentElement.setAttribute('data-theme', 'light');
            const lightTheme = semanticTheme();
            const first = document.createElement('article');
            first.innerHTML = [
                '<pre><code class="language-mermaid">first</code></pre>',
                '<pre><code class="language-mermaid">invalid middle</code></pre>',
                '<pre><code class="language-mermaid">third</code></pre>'
            ].join('');
            document.body.appendChild(first);
            const firstResult = await adapter.mountDocument({ content: first });
            const duplicateResult = await adapter.mountDocument({ content: first });

            document.documentElement.setAttribute('data-theme', 'dark');
            const darkTheme = semanticTheme();
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
                lightTheme,
                darkTheme,
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

    if result["loadCalls"] != 1 or len(result["initializationConfigs"]) != 4:
        raise AssertionError(f"Mermaid did not load once and initialize per queued render: {result!r}")

    def expected_config(theme: dict[str, str], dark_mode: bool) -> dict[str, object]:
        return {
            "startOnLoad": False,
            "suppressErrorRendering": True,
            "theme": "base",
            "themeVariables": {
                "background": theme["panel"],
                "primaryColor": theme["subtlePanel"],
                "mainBkg": theme["subtlePanel"],
                "primaryTextColor": theme["primaryText"],
                "textColor": theme["primaryText"],
                "nodeTextColor": theme["primaryText"],
                "titleColor": theme["primaryText"],
                "actorTextColor": theme["primaryText"],
                "primaryBorderColor": theme["strongBorder"],
                "nodeBorder": theme["strongBorder"],
                "actorBorder": theme["strongBorder"],
                "noteBorderColor": theme["strongBorder"],
                "lineColor": theme["mutedText"],
                "arrowheadColor": theme["mutedText"],
                "secondaryColor": theme["selectionSurface"],
                "activationBkgColor": theme["selectionSurface"],
                "noteBkgColor": theme["selectionSurface"],
                "secondaryTextColor": theme["selectionText"],
                "noteTextColor": theme["selectionText"],
                "tertiaryColor": theme["canvas"],
                "clusterBkg": theme["canvas"],
                "fontFamily": theme["fontFamily"],
                "darkMode": dark_mode,
            },
            "securityLevel": "strict",
            "htmlLabels": False,
            "flowchart": {"htmlLabels": False},
        }

    expected_light = expected_config(result["lightTheme"], False)
    expected_dark = expected_config(result["darkTheme"], True)
    if result["initializationConfigs"] != [expected_light, expected_light, expected_light, expected_dark]:
        raise AssertionError(f"Mermaid did not receive the resolved light and dark semantic seeds: {result!r}")
    if any(
        "var(" in str(value)
        for config in result["initializationConfigs"]
        for value in config["themeVariables"].values()
    ):
        raise AssertionError(f"Mermaid received an unresolved CSS variable: {result!r}")
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


def assert_registered_theme_refresh_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { inlineMermaid, diagramDetail } = window.__docsViewerInlineMermaidSmoke;
            let emptyLoadCalls = 0;
            const emptyAdapter = inlineMermaid.createDocsViewerInlineMermaidAdapter({
                loadMermaid: async () => {
                    emptyLoadCalls += 1;
                    throw new Error('diagram-free theme change loaded Mermaid');
                }
            });
            const emptyRefresh = await emptyAdapter.handleThemeChange('dark');

            document.documentElement.setAttribute('data-theme', 'light');
            const initializationConfigs = [];
            const renderCalls = [];
            const bindings = [];
            const warnings = [];
            let renderDark = false;
            const renderer = {
                initialize(config) {
                    initializationConfigs.push(config);
                    renderDark = config.themeVariables.darkMode;
                },
                async render(id, source) {
                    const theme = renderDark ? 'dark' : 'light';
                    renderCalls.push({ id, source, theme });
                    return {
                        svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 20"><title>${source} ${theme}</title><desc>${source} rendered in ${theme} mode.</desc><rect width="40" height="20"></rect></svg>`,
                        bindFunctions(host) {
                            bindings.push({ host, theme });
                        }
                    };
                }
            };
            const created = [];
            const revoked = [];
            const detailAdapter = diagramDetail.createDocsViewerDiagramDetailAdapter({
                createObjectUrl(markup) {
                    const target = `blob:theme-${created.length + 1}`;
                    created.push({ target, markup });
                    return target;
                },
                revokeObjectUrl(target) {
                    revoked.push(target);
                }
            });
            const adapter = inlineMermaid.createDocsViewerInlineMermaidAdapter({
                loadMermaid: async () => renderer,
                warn(message, error) {
                    warnings.push({ message, detail: error.message });
                }
            });
            const content = document.createElement('article');
            content.innerHTML = [
                '<pre><code class="language-mermaid">first source</code></pre>',
                '<pre><code class="language-mermaid">second source</code></pre>'
            ].join('');
            document.body.appendChild(content);
            const requestedTargets = [];
            detailAdapter.mountDocument({
                content,
                doc: { doc_id: 'theme-refresh-doc' },
                document,
                documentMountGeneration: 23,
                requestContentDetail(target) { requestedTargets.push(target); },
                viewerScope: 'studio',
                window
            });
            const mounted = await adapter.mountDocument({
                content,
                diagramDetailAdapter: detailAdapter,
                document,
                window
            });
            const frames = Array.from(content.querySelectorAll('.docsViewer__diagramFrame'));
            const viewports = Array.from(content.querySelectorAll('.docsViewer__diagramViewport'));
            const hosts = Array.from(content.querySelectorAll(
                '[data-docs-viewer-diagram-kind="inline-mermaid"]'
            ));
            const controls = Array.from(content.querySelectorAll('.docsViewer__diagramDetailControl'));
            const initialSvgs = hosts.map(host => host.firstElementChild);
            controls.forEach(control => control.click());
            const presentationTarget = targetContext => {
                const presentation = detailAdapter.mountPresentation({
                    content,
                    document,
                    targetContext
                });
                const target = presentation.newTabTarget;
                presentation.release();
                return target;
            };
            const initialTargets = requestedTargets.map(presentationTarget);

            const undiscovered = document.createElement('pre');
            undiscovered.innerHTML = '<code class="language-mermaid">not registered</code>';
            content.appendChild(undiscovered);

            document.documentElement.setAttribute('data-theme', 'dark');
            const refreshed = await adapter.handleThemeChange('dark');
            const currentSvgs = hosts.map(host => host.firstElementChild);
            const currentTargets = requestedTargets.map(presentationTarget);
            const panelBackground = getComputedStyle(hosts[0]).backgroundColor;
            const inlineRelease = adapter.releaseDocument({ content });
            const detailRelease = detailAdapter.releaseDocument({ content });
            const releasedAgain = adapter.releaseDocument({ content });

            return {
                emptyRefresh,
                emptyLoadCalls,
                mounted,
                refreshed,
                renderCalls,
                darkModes: initializationConfigs.map(config => config.themeVariables.darkMode),
                bindings: bindings.map(binding => ({
                    hostIndex: hosts.indexOf(binding.host),
                    theme: binding.theme
                })),
                stableFrames: frames.every((frame, index) =>
                    frame === hosts[index].closest('.docsViewer__diagramFrame')
                ),
                stableViewports: viewports.every((viewport, index) =>
                    viewport === hosts[index].parentElement
                ),
                stableHosts: hosts.every((host, index) =>
                    host === currentSvgs[index].parentElement
                ),
                replacedSvgs: initialSvgs.every((svg, index) => svg !== currentSvgs[index]),
                titles: currentSvgs.map(svg => svg.querySelector('title')?.textContent || ''),
                svgBackgrounds: currentSvgs.map(svg => svg.style.backgroundColor),
                panelBackground,
                initialTargets,
                currentTargets,
                refreshedMarkupHasBackground: created.slice(2).every(
                    resource => resource.markup.includes('background-color')
                ),
                revoked,
                undiscoveredSource: undiscovered.textContent,
                undiscoveredState: undiscovered.dataset.docsViewerInlineMermaidState || '',
                inlineRelease,
                detailRelease,
                releasedAgain,
                warnings
            };
        }"""
    )
    if result["emptyRefresh"] != {"found": 0, "rendered": 0, "failed": 0} or result["emptyLoadCalls"] != 0:
        raise AssertionError(f"diagram-free theme change performed Mermaid work: {result!r}")
    if result["mounted"] != {"found": 2, "rendered": 2, "failed": 0, "stale": False}:
        raise AssertionError(f"theme-refresh fixture did not mount two diagrams: {result!r}")
    if result["refreshed"] != {"found": 2, "rendered": 2, "failed": 0}:
        raise AssertionError(f"registered diagrams did not refresh in place: {result!r}")
    if [(call["source"], call["theme"]) for call in result["renderCalls"]] != [
        ("first source", "light"),
        ("second source", "light"),
        ("first source", "dark"),
        ("second source", "dark"),
    ]:
        raise AssertionError(f"retained Mermaid sources did not render sequentially: {result!r}")
    if result["darkModes"] != [False, False, True, True]:
        raise AssertionError(f"theme refresh did not reconfigure every queued render: {result!r}")
    if result["bindings"] != [
        {"hostIndex": 0, "theme": "light"},
        {"hostIndex": 1, "theme": "light"},
        {"hostIndex": 0, "theme": "dark"},
        {"hostIndex": 1, "theme": "dark"},
    ]:
        raise AssertionError(f"Mermaid bindings did not follow successful host updates: {result!r}")
    if (
        not result["stableFrames"]
        or not result["stableViewports"]
        or not result["stableHosts"]
        or not result["replacedSvgs"]
    ):
        raise AssertionError(f"theme refresh rebuilt stable diagram chrome: {result!r}")
    if result["titles"] != ["first source dark", "second source dark"]:
        raise AssertionError(f"theme refresh did not commit the dark candidate SVGs: {result!r}")
    if any(background != result["panelBackground"] for background in result["svgBackgrounds"]):
        raise AssertionError(f"themed SVG did not carry its standalone canvas background: {result!r}")
    if (
        result["initialTargets"] != ["blob:theme-1", "blob:theme-2"]
        or result["currentTargets"] != ["blob:theme-3", "blob:theme-4"]
        or result["revoked"] != [
            "blob:theme-1",
            "blob:theme-2",
            "blob:theme-3",
            "blob:theme-4",
        ]
        or not result["refreshedMarkupHasBackground"]
    ):
        raise AssertionError(f"theme refresh did not replace and clean detail resources: {result!r}")
    if result["undiscoveredSource"] != "not registered" or result["undiscoveredState"]:
        raise AssertionError(f"theme refresh rescanned document fences: {result!r}")
    if (
        result["inlineRelease"] != {"released": 2}
        or result["detailRelease"] != {"released": 2}
        or result["releasedAgain"] != {"released": 0}
        or result["warnings"]
    ):
        raise AssertionError(f"theme refresh registry cleanup or diagnostics changed: {result!r}")


def assert_theme_refresh_failure_retention(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { inlineMermaid, diagramDetail } = window.__docsViewerInlineMermaidSmoke;
            document.documentElement.setAttribute('data-theme', 'light');

            function svg(title) {
                return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10"><title>${title}</title><desc>${title} description.</desc><rect width="20" height="10"></rect></svg>`;
            }

            let renderShouldFail = false;
            const renderWarnings = [];
            const renderDetail = diagramDetail.createDocsViewerDiagramDetailAdapter({
                createObjectUrl() {
                    return 'blob:render-current';
                },
                revokeObjectUrl() {}
            });
            const renderAdapter = inlineMermaid.createDocsViewerInlineMermaidAdapter({
                loadMermaid: async () => ({
                    initialize() {},
                    async render() {
                        if (renderShouldFail) throw new Error('fixture themed render failure');
                        return { svg: svg('render current') };
                    }
                }),
                warn(message, error) {
                    renderWarnings.push({ message, detail: error.message });
                }
            });
            const renderContent = document.createElement('article');
            renderContent.innerHTML = '<pre><code class="language-mermaid">render failure source</code></pre>';
            document.body.appendChild(renderContent);
            const renderTargets = [];
            renderDetail.mountDocument({
                content: renderContent,
                doc: { doc_id: 'render-failure-doc' },
                document,
                documentMountGeneration: 29,
                requestContentDetail(target) { renderTargets.push(target); },
                viewerScope: 'studio',
                window
            });
            await renderAdapter.mountDocument({
                content: renderContent,
                diagramDetailAdapter: renderDetail,
                document,
                window
            });
            const renderHost = renderContent.querySelector(
                '[data-docs-viewer-diagram-kind="inline-mermaid"]'
            );
            const renderSvg = renderHost.firstElementChild;
            const renderControl = renderContent.querySelector('.docsViewer__diagramDetailControl');
            renderControl.click();
            const mountedTarget = (adapter, contentRoot, targetContext) => {
                const presentation = adapter.mountPresentation({
                    content: contentRoot,
                    document,
                    targetContext
                });
                const target = presentation.newTabTarget;
                presentation.release();
                return target;
            };
            const renderTarget = mountedTarget(renderDetail, renderContent, renderTargets[0]);
            renderShouldFail = true;
            document.documentElement.setAttribute('data-theme', 'dark');
            const renderFailure = await renderAdapter.handleThemeChange('dark');

            let detailCreates = 0;
            const detailWarnings = [];
            const detailRevoked = [];
            const failingDetail = diagramDetail.createDocsViewerDiagramDetailAdapter({
                createObjectUrl() {
                    detailCreates += 1;
                    if (detailCreates > 1) throw new Error('fixture themed detail failure');
                    return 'blob:detail-current';
                },
                revokeObjectUrl(target) {
                    detailRevoked.push(target);
                },
                warn(message, error) {
                    detailWarnings.push({ message, detail: error.message });
                }
            });
            const detailWarningsFromInline = [];
            const detailAdapter = inlineMermaid.createDocsViewerInlineMermaidAdapter({
                loadMermaid: async () => ({
                    initialize() {},
                    async render() {
                        return {
                            svg: detailCreates
                                ? svg('detail candidate')
                                : svg('detail current')
                        };
                    }
                }),
                warn(message, error) {
                    detailWarningsFromInline.push({ message, detail: error.message });
                }
            });
            document.documentElement.setAttribute('data-theme', 'light');
            const detailContent = document.createElement('article');
            detailContent.innerHTML = '<pre><code class="language-mermaid">detail failure source</code></pre>';
            document.body.appendChild(detailContent);
            const detailTargets = [];
            failingDetail.mountDocument({
                content: detailContent,
                doc: { doc_id: 'detail-failure-doc' },
                document,
                documentMountGeneration: 31,
                requestContentDetail(target) { detailTargets.push(target); },
                viewerScope: 'studio',
                window
            });
            await detailAdapter.mountDocument({
                content: detailContent,
                diagramDetailAdapter: failingDetail,
                document,
                window
            });
            const detailHost = detailContent.querySelector(
                '[data-docs-viewer-diagram-kind="inline-mermaid"]'
            );
            const detailSvg = detailHost.firstElementChild;
            const detailControl = detailContent.querySelector('.docsViewer__diagramDetailControl');
            detailControl.click();
            const detailTarget = mountedTarget(failingDetail, detailContent, detailTargets[0]);
            document.documentElement.setAttribute('data-theme', 'dark');
            const detailFailure = await detailAdapter.handleThemeChange('dark');
            const detailRevokedBeforeRelease = detailRevoked.slice();
            const renderTargetRetained = mountedTarget(
                renderDetail,
                renderContent,
                renderTargets[0]
            ) === renderTarget;
            const detailTargetRetained = mountedTarget(
                failingDetail,
                detailContent,
                detailTargets[0]
            ) === detailTarget;
            const detailRelease = failingDetail.releaseDocument({ content: detailContent });

            return {
                renderFailure,
                renderSvgRetained: renderHost.firstElementChild === renderSvg,
                renderTargetRetained,
                renderWarnings,
                detailFailure,
                detailSvgRetained: detailHost.firstElementChild === detailSvg,
                detailTargetRetained,
                detailWarnings,
                detailWarningsFromInline,
                detailRevokedBeforeRelease,
                detailRevoked,
                detailRelease
            };
        }"""
    )
    if (
        result["renderFailure"] != {"found": 1, "rendered": 0, "failed": 1}
        or not result["renderSvgRetained"]
        or not result["renderTargetRetained"]
        or result["renderWarnings"] != [{
            "message": "docs_viewer: inline Mermaid theme refresh unavailable",
            "detail": "fixture themed render failure",
        }]
    ):
        raise AssertionError(f"failed themed render displaced the usable diagram pair: {result!r}")
    if (
        result["detailFailure"] != {"found": 1, "rendered": 0, "failed": 1}
        or not result["detailSvgRetained"]
        or not result["detailTargetRetained"]
        or result["detailWarnings"] != [{
            "message": "docs_viewer: inline diagram detail refresh unavailable",
            "detail": "fixture themed detail failure",
        }]
        or result["detailWarningsFromInline"] != [{
            "message": "docs_viewer: inline Mermaid theme refresh unavailable",
            "detail": "Inline Mermaid detail refresh did not commit: target-unavailable",
        }]
        or result["detailRevokedBeforeRelease"]
        or result["detailRevoked"] != ["blob:detail-current"]
        or result["detailRelease"] != {"released": 1}
    ):
        raise AssertionError(f"failed themed detail refresh displaced the usable pair: {result!r}")


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
            const { inlineMermaid, diagramDetail } = window.__docsViewerInlineMermaidSmoke;
            const content = document.createElement('article');
            content.className = 'docsViewer__content';
            const representativeSources = [
                [
                    'flowchart LR',
                    '  accTitle: Flowchart theme proof',
                    '  accDescr: Authored source flows through the themed renderer',
                    '  Source --> Renderer --> SVG',
                    '  classDef authored fill:#f4b400,stroke:#6b4f00,color:#101010',
                    '  class Source authored'
                ].join('\\n'),
                [
                    'sequenceDiagram',
                    '  accTitle: Sequence theme proof',
                    '  accDescr: An author asks the viewer to render a diagram',
                    '  participant Author',
                    '  participant Viewer',
                    '  Author->>Viewer: Render source',
                    '  Viewer-->>Author: Display SVG'
                ].join('\\n'),
                [
                    'stateDiagram-v2',
                    '  accTitle: State theme proof',
                    '  accDescr: A diagram moves from source to displayed state',
                    '  [*] --> Source',
                    '  Source --> Displayed',
                    '  Displayed --> [*]'
                ].join('\\n')
            ];
            representativeSources.forEach(source => {
                const pre = document.createElement('pre');
                const code = document.createElement('code');
                code.className = 'language-mermaid';
                code.textContent = source;
                pre.appendChild(code);
                content.appendChild(pre);
            });
            document.body.appendChild(content);
            const detailAdapter = diagramDetail.createDocsViewerDiagramDetailAdapter();
            const requestedTargets = [];
            detailAdapter.mountDocument({
                content,
                doc: { doc_id: 'representative-theme-doc' },
                document,
                documentMountGeneration: 37,
                requestContentDetail(target) { requestedTargets.push(target); },
                viewerScope: 'studio',
                window
            });
            document.documentElement.setAttribute('data-theme', 'light');
            const mountResult = await inlineMermaid.docsViewerInlineMermaidAdapter.mountDocument({
                content,
                diagramDetailAdapter: detailAdapter,
                document,
                window
            });
            const frames = Array.from(content.querySelectorAll('.docsViewer__diagramFrame'));
            const viewports = Array.from(content.querySelectorAll('.docsViewer__diagramViewport'));
            const hosts = Array.from(content.querySelectorAll(
                '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
            ));
            const controls = Array.from(content.querySelectorAll('.docsViewer__diagramDetailControl'));
            controls.forEach(control => control.click());

            function currentTargets() {
                return requestedTargets.map(targetContext => {
                    const presentation = detailAdapter.mountPresentation({
                        content,
                        document,
                        targetContext
                    });
                    const target = presentation.newTabTarget;
                    presentation.release();
                    return target;
                });
            }

            function themedState() {
                const svgs = hosts.map(host => host.querySelector(':scope > svg'));
                return {
                    theme: document.documentElement.getAttribute('data-theme') || '',
                    titles: svgs.map(svg => svg?.querySelector('title')?.textContent || ''),
                    descriptions: svgs.map(svg => svg?.querySelector('desc')?.textContent || ''),
                    backgrounds: svgs.map(svg => svg?.style.backgroundColor || ''),
                    viewBoxes: svgs.map(svg => svg?.getAttribute('viewBox') || ''),
                    targets: currentTargets(),
                    authoredStylePresent: (svgs[0]?.outerHTML || '').toLowerCase().includes('#f4b400'),
                    viewportOverflow: viewports.map(viewport => getComputedStyle(viewport).overflowX),
                    hostOverflow: hosts.map(host => getComputedStyle(host).overflowX)
                };
            }

            const initialSvgs = hosts.map(host => host.firstElementChild);
            const lightState = themedState();
            document.documentElement.setAttribute('data-theme', 'dark');
            const themeResult = await inlineMermaid.docsViewerInlineMermaidAdapter.handleThemeChange('dark');
            const darkState = themedState();
            const detailMarkup = await Promise.all(
                darkState.targets.map(target => fetch(target).then(response => response.text()))
            );
            const stableChrome = frames.every((frame, index) =>
                frame === hosts[index].closest('.docsViewer__diagramFrame')
                && viewports[index] === hosts[index].parentElement
                && controls[index] === frame.querySelector('.docsViewer__diagramDetailControl')
            );
            const replacedSvgs = initialSvgs.every((svg, index) => svg !== hosts[index].firstElementChild);
            const inlineRelease = inlineMermaid.docsViewerInlineMermaidAdapter.releaseDocument({ content });
            const detailRelease = detailAdapter.releaseDocument({ content });

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
            const mixedError = mixed.querySelector('.docsViewer__diagramError');
            const mixedSource = mixed.querySelector('pre > code.language-mermaid');
            return {
                mountResult,
                themeResult,
                lightState,
                darkState,
                detailMarkup,
                stableChrome,
                replacedSvgs,
                inlineRelease,
                detailRelease,
                mixedResult,
                assetVersion: script?.dataset.docsViewerInlineMermaidRuntime || '',
                assetPath: script?.getAttribute('src') || '',
                hostKinds: hosts.map(host => host.dataset.docsViewerDiagramKind || ''),
                sourceCount: content.querySelectorAll('pre > code.language-mermaid').length,
                mixedHostCount: mixed.querySelectorAll('.docsViewer__diagram').length,
                mixedSourceCount: mixed.querySelectorAll('pre > code.language-mermaid').length,
                mixedSource: mixedSource?.textContent || '',
                mixedErrorText: mixedError?.textContent || '',
                mixedDiagnosticCount: diagnostics.length,
                mixedDiagnosticMessage: diagnostics[0]?.message || '',
                mixedDiagnosticHasDetail: Boolean(diagnostics[0]?.detail),
                diagnosticLeakedToContent: diagnostics.some(item => mixed.textContent.includes(item.detail)),
                mermaidErrorArtifactCount: document.querySelectorAll('[id^="ddocs-viewer-inline-mermaid-"]').length
            };
        }"""
    )
    if result["mountResult"] != {"found": 3, "rendered": 3, "failed": 0, "stale": False}:
        raise AssertionError(f"representative Mermaid diagrams did not render: {result!r}")
    if result["themeResult"] != {"found": 3, "rendered": 3, "failed": 0}:
        raise AssertionError(f"representative Mermaid diagrams did not re-render: {result!r}")
    if result["assetVersion"] != "11.16.0" or result["assetPath"] != "/docs-viewer/runtime/vendor/mermaid/11.16.0/mermaid.min.js":
        raise AssertionError(f"inline renderer did not load the checked Mermaid asset: {result!r}")
    if result["hostKinds"] != ["inline-mermaid"] * 3 or result["sourceCount"] != 0:
        raise AssertionError(f"representative Mermaid renders did not use the settled hosts: {result!r}")
    expected_titles = [
        "Flowchart theme proof",
        "Sequence theme proof",
        "State theme proof",
    ]
    expected_descriptions = [
        "Authored source flows through the themed renderer",
        "An author asks the viewer to render a diagram",
        "A diagram moves from source to displayed state",
    ]
    states = [result["lightState"], result["darkState"]]
    if [state["theme"] for state in states] != ["light", "dark"]:
        raise AssertionError(f"representative Mermaid review did not exercise both themes: {result!r}")
    for state in states:
        if state["titles"] != expected_titles or state["descriptions"] != expected_descriptions:
            raise AssertionError(f"representative Mermaid render lost accessible text: {result!r}")
        if (
            any(not background for background in state["backgrounds"])
            or any(not view_box for view_box in state["viewBoxes"])
            or any(not target.startswith("blob:") for target in state["targets"])
            or not state["authoredStylePresent"]
            or state["viewportOverflow"] != ["auto"] * 3
            or state["hostOverflow"] != ["visible"] * 3
        ):
            raise AssertionError(f"representative Mermaid presentation contract changed: {result!r}")
    if result["lightState"]["targets"] == result["darkState"]["targets"]:
        raise AssertionError(f"representative detail targets did not follow the active theme: {result!r}")
    if not result["stableChrome"] or not result["replacedSvgs"]:
        raise AssertionError(f"representative theme refresh rebuilt stable diagram chrome: {result!r}")
    if (
        any("viewBox=" not in markup or "<title" not in markup or "<desc" not in markup
            or "background-color" not in markup for markup in result["detailMarkup"])
        or result["inlineRelease"] != {"released": 3}
        or result["detailRelease"] != {"released": 3}
    ):
        raise AssertionError(f"representative standalone detail contract changed: {result!r}")
    if result["mixedResult"] != {"found": 3, "rendered": 2, "failed": 1, "stale": False}:
        raise AssertionError(f"checked Mermaid runtime did not contain an invalid middle diagram: {result!r}")
    if result["mixedHostCount"] != 2 or result["mixedSourceCount"] != 1 or result["mixedSource"] != "not a Mermaid diagram":
        raise AssertionError(f"checked Mermaid runtime did not retain only the failed source: {result!r}")
    if result["mixedErrorText"] != "Diagram could not be rendered. Mermaid source is shown below.":
        raise AssertionError(f"checked Mermaid runtime fallback changed: {result!r}")
    if result["mermaidErrorArtifactCount"] != 0:
        raise AssertionError(f"Mermaid left its own error rendering in the document body: {result!r}")
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
                diagramFreeExternal: await exercise(
                    'diagram-free-notes',
                    'local_external',
                    '<p>No diagram</p>'
                ),
                publicScope: await exercise('library', 'public', fence)
            };
        }"""
    )
    rendered = {"mountCalls": 1, "loadCalls": 1, "diagramCount": 1, "fenceCount": 0}
    if result["arbitraryLocal"] != rendered or result["external"] != rendered:
        raise AssertionError(f"a managed-local scope was not eligible: {result!r}")
    diagram_free = {"mountCalls": 1, "loadCalls": 0, "diagramCount": 0, "fenceCount": 0}
    if (
        result["diagramFreeLocal"] != diagram_free
        or result["diagramFreeExternal"] != diagram_free
    ):
        raise AssertionError(f"a diagram-free managed-local mount loaded Mermaid: {result!r}")
    unsupported = {"mountCalls": 0, "loadCalls": 0, "diagramCount": 0, "fenceCount": 1}
    if result["publicScope"] != unsupported:
        raise AssertionError(f"public scope did not retain its Mermaid fence without loading: {result!r}")


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/404.html", wait_until="domcontentloaded")
    install_fixture(page)
    assert_theme_composition_callback(page)
    assert_session_renderer_and_failure_containment(page)
    assert_registered_theme_refresh_contract(page)
    assert_theme_refresh_failure_retention(page)
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

#!/usr/bin/env python3
"""Smoke-check the CT-P1/P2 Catalogue token browser-module contracts."""

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
        return super().translate_path(path)


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def install_modules(page: Page) -> None:
    page.evaluate(
        """async () => {
            const contract = await import(
                '/docs-viewer/runtime/js/management/source-editor/catalogue-token-contract.js'
            );
            const targets = await import(
                '/docs-viewer/runtime/js/management/source-editor/catalogue-token-targets.js'
            );
            const modal = await import(
                '/docs-viewer/runtime/js/management/source-editor/catalogue-token-modal.js'
            );
            const contribution = await import(
                '/docs-viewer/runtime/js/management/source-editor/catalogue-token-contribution.js'
            );
            const registry = await import(
                '/docs-viewer/runtime/js/management/source-editor/semantic-token-registry.js'
            );
            const semanticTargets = await import(
                '/docs-viewer/runtime/js/management/source-editor/semantic-token-targets.js'
            );
            const parser = await import(
                '/docs-viewer/runtime/js/management/source-editor/catalogue-token-parser.js'
            );
            const infoView = await import(
                '/docs-viewer/runtime/js/management/source-editor/catalogue-token-info-view.js'
            );
            const sourceEditor = await import(
                '/docs-viewer/runtime/js/management/source-editor/source-editor.js'
            );
            const sourceAdapter = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-source-adapter.js'
            );
            const sourceClient = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-client.js'
            );
            const documentTarget = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-document-target.js'
            );
            const managementActions = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-actions.js'
            );
            window.__catalogueTokenSmoke = {
                contract,
                contribution,
                documentTarget,
                infoView,
                managementActions,
                modal,
                parser,
                registry,
                semanticTargets,
                sourceAdapter,
                sourceClient,
                sourceEditor,
                targets
            };
        }"""
    )


def install_styles(page: Page, base_url: str) -> None:
    for path in (
        "/site/docs-viewer/static/css/docs-viewer.css",
        "/docs-viewer/static/css/docs-viewer-manage.css",
        "/docs-viewer/static/css/docs-viewer-source-editor.css",
    ):
        page.add_style_tag(url=f"{base_url}{path}")


def assert_contract_fixture_and_mixed_search(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__catalogueTokenSmoke;
            const fixture = await fetch(
                '/docs-viewer/tests/fixtures/semantic_tokens_catalogue_v1.json'
            ).then(response => response.json());
            const serialized = fixture.cases.flatMap(testCase => (
                testCase.tokens.filter(token => token.supported).map(token => ({
                    id: testCase.id,
                    actual: smoke.contract.buildCatalogueToken({
                        targetType: token.target_type,
                        targetId: token.target_id,
                        title: token.input_title || token.title
                    }),
                    expected: token.serialized
                }))
            ));
            const registry = smoke.registry.normalizeSemanticTokenRegistry({
                schema_version: 'docs_semantic_token_registry_v1',
                target_lookup_url: '/docs-viewer/data/generated/semantic-tokens/target-lookup.json',
                families: [fixture.catalogue_definition]
            });
            const semanticTargets = smoke.semanticTargets.normalizeSemanticTokenTargets(
                fixture.target_lookup_example,
                registry
            );
            const support = smoke.targets.createCatalogueTargetSupport(registry, semanticTargets);
            const matches = smoke.targets.collectCatalogueTargetMatches(support, 'nerve', 10);
            const idMatches = smoke.targets.collectCatalogueTargetMatches(support, '00008', 10);
            const qualifiedIdMatches = smoke.targets.collectCatalogueTargetMatches(
                support,
                'work:00008',
                10
            );
            const exactTarget = smoke.targets.findCatalogueTargetByIdentity(support, {
                family: 'catalogue',
                targetType: 'work',
                targetId: '00008'
            });
            const parsed = fixture.cases.map(testCase => ({
                id: testCase.id,
                actual: smoke.parser.parseCatalogueTokens(testCase.source, { registry }).map(token => ({
                    raw: token.raw,
                    source_range: { start: token.start, end: token.end },
                    family: token.family,
                    target_type: token.targetType,
                    target_id: token.targetId,
                    title: token.title,
                    supported: token.supported,
                    activatable: token.activatable
                })),
                expected: testCase.tokens.map(token => ({
                    raw: token.raw,
                    source_range: token.source_range,
                    family: token.family,
                    target_type: token.target_type,
                    target_id: token.target_id,
                    title: token.title,
                    supported: token.supported,
                    activatable: token.activatable
                })),
                caret: (testCase.caret_expectations || []).map(expectation => {
                    const tokens = smoke.parser.parseCatalogueTokens(testCase.source, { registry });
                    const active = smoke.parser.catalogueTokenAtSelection(tokens, {
                        start: expectation.offset,
                        end: expectation.offset
                    });
                    return {
                        actual: active ? tokens.indexOf(active) : null,
                        expected: expectation.active_token_index
                    };
                })
            }));
            const definition = smoke.contribution.catalogueTokenControlDefinition();
            const handlers = smoke.contribution.createCatalogueTokenMainViewControlHandlers();
            const infoResolver = smoke.contribution.createCatalogueTokenInfoViewResolver({
                fetch: async () => ({
                    ok: true,
                    json: async () => ({
                        schema_version: 'docs_semantic_token_registry_v1',
                        target_lookup_url: '/docs-viewer/data/generated/semantic-tokens/target-lookup.json',
                        families: [fixture.catalogue_definition]
                    })
                })
            });
            const resolvedInfoViews = [
                await infoResolver({
                    getBufferSnapshot() {
                        return {
                            revision: 0,
                            value: 'Before [[catalogue:work:00638|3 symbols]] after'
                        };
                    },
                    getSelection() {
                        return { start: 18, end: 18 };
                    }
                }),
                await infoResolver({
                    getBufferSnapshot() {
                        return { revision: 0, value: 'Before ordinary text after' };
                    },
                    getSelection() {
                        return { start: 10, end: 10 };
                    }
                })
            ];
            const renderedButton = smoke.contribution.catalogueTokenControlRenderer({
                document
            });
            return {
                definition,
                exactTarget,
                fixtureUiContributions: fixture.catalogue_definition.ui_contributions,
                handlerIds: Object.keys(handlers),
                idMatches,
                matches: matches.map(target => ({
                    family: target.family,
                    targetType: target.targetType,
                    targetId: target.targetId,
                    title: target.title,
                    href: target.href,
                    meta: target.meta
                })),
                modalId: smoke.modal.CATALOGUE_TOKEN_MODAL_ID,
                parsed,
                qualifiedIdMatches,
                rendererIcon: renderedButton.textContent,
                resolvedInfoViews,
                serialized
            };
        }"""
    )
    mismatches = [
        row for row in result["serialized"]
        if row["actual"] != row["expected"]
    ]
    if mismatches:
        raise AssertionError(f"browser serializer drifted from the P0 fixture: {mismatches!r}")
    parser_mismatches = [
        row for row in result["parsed"]
        if row["actual"] != row["expected"]
        or any(item["actual"] != item["expected"] for item in row["caret"])
    ]
    if parser_mismatches:
        raise AssertionError(f"browser parser drifted from the P0 fixture: {parser_mismatches!r}")
    if result["matches"] != [
        {
            "family": "catalogue",
            "targetType": "work",
            "targetId": "00008",
            "title": "nerve",
            "href": "/works/?work=00008",
            "meta": ["July 1990 – January 1995", "nerve"],
        },
        {
            "family": "catalogue",
            "targetType": "series",
            "targetId": "105",
            "title": "nerve",
            "href": "/series/?series=105",
            "meta": ["1990-95"],
        },
    ]:
        raise AssertionError(f"ambiguous Catalogue search changed: {result!r}")
    expected_id_target = {
        "family": "catalogue",
        "targetType": "work",
        "targetId": "00008",
        "title": "nerve",
        "href": "/works/?work=00008",
        "meta": ["July 1990 – January 1995", "nerve"],
    }
    if (
        result["idMatches"] != [expected_id_target]
        or result["qualifiedIdMatches"] != [expected_id_target]
        or result["exactTarget"] != expected_id_target
    ):
        raise AssertionError(f"Catalogue ID search or exact identity lookup changed: {result!r}")
    if result["definition"] != {
        "id": "source-add-catalogue-token",
        "actionId": "source-add-catalogue-token",
        "label": "Add catalogue token",
        "ownerType": "view",
        "ownerViewId": "rendered-document",
        "modeIds": ["markdown-source"],
        "surfaceId": "main-view",
        "appKinds": ["manage"],
        "features": ["source-editing"],
        "renderer": "source-add-catalogue-token",
    }:
        raise AssertionError(f"Catalogue control definition changed: {result!r}")
    if result["handlerIds"] != ["source-add-catalogue-token"]:
        raise AssertionError(f"Catalogue control handler contribution changed: {result!r}")
    if result["rendererIcon"] != "📍":
        raise AssertionError(f"Catalogue control icon changed: {result!r}")
    if result["resolvedInfoViews"] != ["catalogue-token-info", "metadata-info"]:
        raise AssertionError(f"Catalogue source Info routing changed: {result!r}")
    if result["fixtureUiContributions"] != {
        "source_action": result["definition"]["id"],
        "modal": result["modalId"],
        "info_view": "catalogue-token-info",
    }:
        raise AssertionError(f"browser UI contribution ids drifted from the P0 fixture: {result!r}")


def assert_source_adapter_captures_and_guards_range(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__catalogueTokenSmoke;
            const root = document.createElement('div');
            const mount = document.createElement('div');
            root.appendChild(mount);
            document.body.appendChild(root);
            let adapter = null;
            let readTarget = null;
            const controlStates = {};
            const mode = smoke.sourceEditor.createDocsViewerSourceEditorMode();
            await mode.mount({
                root,
                mount,
                selectedDoc: { doc_id: 'selected-parent' },
                sourceTarget: {
                    scope: 'studio',
                    sub_scope: 'tags',
                    doc_id: 'fixture'
                },
                collectionProvider: {
                    readSource(target) {
                        readTarget = Object.assign({}, target);
                        return Promise.resolve({
                            scope: 'studio',
                            sub_scope: 'tags',
                            doc_id: 'fixture',
                            source_revision: 'r1',
                            source_body: 'Before nerve after'
                        });
                    }
                },
                documentView: {
                    projectToolbar() {},
                    requestMode() {}
                },
                sourceEditorServices: {
                    projectMainViewControlState(controlId, state) {
                        controlStates[controlId] = Object.assign({}, state);
                    },
                    setActiveSourceEditorContextAdapter(value) {
                        adapter = value;
                    },
                    sourceEditorActionControlIds: ['source-add-catalogue-token']
                }
            });
            const textarea = mount.querySelector('textarea');
            textarea.setSelectionRange(7, 12);
            const capture = adapter.captureSelection();
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            const staleRejected = adapter.replaceCapturedSelection(capture, 'stale') === false;
            textarea.setSelectionRange(7, 12);
            const freshCapture = adapter.captureSelection();
            const replaced = adapter.replaceCapturedSelection(
                freshCapture,
                '[[catalogue:work:00008|nerve]]'
            );
            const snapshot = adapter.getBufferSnapshot();
            mode.unmount({ root, mount, sourceEditorServices: {} });
            root.remove();
            return {
                capture,
                controlState: controlStates['source-add-catalogue-token'],
                mountedTarget: adapter.getDocumentTarget(),
                readTarget,
                replaced,
                snapshot,
                staleRejected
            };
        }"""
    )
    if result != {
        "capture": {"start": 7, "end": 12, "text": "nerve", "revision": 0},
        "controlState": {"busy": False, "disabled": False},
        "mountedTarget": {
            "scope": "studio",
            "sub_scope": "tags",
            "doc_id": "fixture",
        },
        "readTarget": {
            "scope": "studio",
            "sub_scope": "tags",
            "doc_id": "fixture",
        },
        "replaced": True,
        "snapshot": {
            "revision": 2,
            "value": "Before [[catalogue:work:00008|nerve]] after",
        },
        "staleRejected": True,
    }:
        raise AssertionError(f"captured source-range adapter changed: {result!r}")


def assert_source_target_transport_and_fixed_session(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__catalogueTokenSmoke;
            const parent = { scope: 'Studio', doc_id: 'parent-doc' };
            const detail = {
                scope: 'Studio',
                sub_scope: 'Tags',
                doc_id: 'detail-doc'
            };
            const requests = [];
            const options = {
                baseUrl: 'http://manage.test',
                scope: 'ambient-must-not-win',
                fetch: async (url, requestOptions) => {
                    requests.push({
                        url,
                        method: requestOptions.method,
                        body: requestOptions.body ? JSON.parse(requestOptions.body) : null
                    });
                    return {
                        ok: true,
                        status: 200,
                        json: async () => ({ ok: true })
                    };
                }
            };
            await smoke.sourceClient.readManagedDocSource(parent, options);
            await smoke.sourceClient.readManagedDocSource(detail, options);
            await smoke.sourceClient.rebuildManagedDocSource(detail, {
                source_revision: 'r1',
                source_body: '# Detail'
            }, options);
            await smoke.sourceClient.openManagedDocSource(parent, 'vscode', options);
            await smoke.sourceClient.openManagedDocSource(detail, 'vscode', options);
            await smoke.sourceClient.readManagedDiagramSources(detail, options);
            await smoke.sourceClient.openManagedDiagramSource(detail, {
                media_identity: 'docs/studio/svg/diagram.svg'
            }, options);

            const adapterRequests = [];
            const adapter = smoke.sourceAdapter.createDocsViewerManagementSourceAdapter({
                sourceService: { baseUrl: 'http://adapter.test' },
                viewerScope: () => 'ambient-must-not-win',
                window: {
                    fetch: async (url, requestOptions) => {
                        adapterRequests.push({
                            url,
                            body: requestOptions.body ? JSON.parse(requestOptions.body) : null
                        });
                        return {
                            ok: true,
                            status: 200,
                            json: async () => ({ ok: true })
                        };
                    }
                }
            });
            await adapter.readSource(detail);
            await adapter.writeSource(detail, {
                source_revision: 'r2',
                source_body: '# Adapter'
            });

            const sourceModeRequests = [];
            const actionController = smoke.managementActions.createDocsViewerManagementActionController({
                root: null,
                context: {
                    requestDocumentMode(modeId, requestOptions) {
                        sourceModeRequests.push({
                            modeId,
                            sourceTarget: requestOptions.context.sourceTarget
                        });
                    }
                },
                resolveAction() {
                    return {
                        enabled: true,
                        targetDocIds: ['fallback-must-not-be-read']
                    };
                },
                callbacks: {
                    hideContextMenu() {}
                }
            });
            actionController.handleMarkdownSource(detail);

            const root = document.createElement('div');
            const mount = document.createElement('div');
            root.appendChild(mount);
            document.body.appendChild(root);
            const reads = [];
            const writes = [];
            const reloads = [];
            const modes = [];
            let mountedAdapter = null;
            const mode = smoke.sourceEditor.createDocsViewerSourceEditorMode();
            await mode.mount({
                root,
                mount,
                selectedDoc: { doc_id: 'selected-parent' },
                sourceTarget: detail,
                collectionProvider: {
                    readSource(target) {
                        reads.push(Object.assign({}, target));
                        return Promise.resolve({
                            scope: 'studio',
                            sub_scope: 'tags',
                            doc_id: 'detail-doc',
                            source_revision: 'r1',
                            source_body: '# Detail'
                        });
                    },
                    writeSource(target, payload) {
                        writes.push({
                            target: Object.assign({}, target),
                            payload: Object.assign({}, payload)
                        });
                        return Promise.resolve({
                            scope: 'studio',
                            sub_scope: 'tags',
                            doc_id: 'detail-doc',
                            source_revision: 'r2'
                        });
                    }
                },
                documentView: {
                    projectToolbar() {},
                    requestMode(modeId) {
                        modes.push(modeId);
                    }
                },
                sourceEditorServices: {
                    projectMainViewControlState() {},
                    reloadRenderedDoc(target) {
                        reloads.push(Object.assign({}, target));
                        return Promise.resolve();
                    },
                    setActiveSourceEditorContextAdapter(value) {
                        mountedAdapter = value;
                    }
                }
            });
            await mode.update({
                selectedDoc: { doc_id: 'different-selected-doc' }
            });
            const textarea = mount.querySelector('textarea');
            textarea.value = '# Changed';
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            root.dispatchEvent(new CustomEvent('docs-viewer-source-editor-save', {
                bubbles: true
            }));
            for (let index = 0; index < 20 && reloads.length === 0; index += 1) {
                await new Promise(resolve => setTimeout(resolve, 0));
            }
            const mountedTarget = mountedAdapter.getDocumentTarget();
            mode.unmount({ root, mount, sourceEditorServices: {} });
            root.remove();

            const failureRoot = document.createElement('div');
            const failureMount = document.createElement('div');
            failureRoot.appendChild(failureMount);
            document.body.appendChild(failureRoot);
            const failureModes = [];
            let failureAdapter = null;
            let failureReads = 0;
            const failureMode = smoke.sourceEditor.createDocsViewerSourceEditorMode();
            await failureMode.mount({
                root: failureRoot,
                mount: failureMount,
                sourceTarget: parent,
                collectionProvider: {
                    readSource() {
                        failureReads += 1;
                        return Promise.resolve({
                            scope: 'studio',
                            doc_id: 'parent-doc',
                            source_revision: 'parent-r1',
                            source_body: '# Parent'
                        });
                    },
                    writeSource() {
                        return Promise.reject(new Error('builder failed'));
                    }
                },
                documentView: {
                    projectToolbar() {},
                    requestMode(modeId) {
                        failureModes.push(modeId);
                    }
                },
                sourceEditorServices: {
                    projectMainViewControlState() {},
                    setActiveSourceEditorContextAdapter(value) {
                        failureAdapter = value;
                    }
                }
            });
            const failureTextarea = failureMount.querySelector('textarea');
            failureTextarea.value = '# Parent changed';
            failureTextarea.dispatchEvent(new Event('input', { bubbles: true }));
            failureRoot.dispatchEvent(new CustomEvent('docs-viewer-source-editor-save', {
                bubbles: true
            }));
            let failureStatus = '';
            for (let index = 0; index < 20; index += 1) {
                await new Promise(resolve => setTimeout(resolve, 0));
                failureStatus = failureMount.querySelector(
                    '.docsViewerSourceEditor__status'
                ).textContent;
                if (failureStatus) break;
            }
            await failureMode.update({
                selectedDoc: { doc_id: 'fallback-must-not-load' }
            });
            const failureTarget = failureAdapter.getDocumentTarget();
            failureMode.unmount({
                root: failureRoot,
                mount: failureMount,
                sourceEditorServices: {}
            });
            failureRoot.remove();

            let extraFieldRejected = false;
            let payloadTargetOverrideRejected = false;
            try {
                smoke.documentTarget.normalizeManagedDocumentTarget({
                    scope: 'studio',
                    doc_id: 'parent-doc',
                    selected_doc_id: 'fallback'
                });
            } catch (error) {
                extraFieldRejected = /exactly scope and doc_id/.test(
                    String(error && error.message || '')
                );
            }
            try {
                smoke.sourceClient.rebuildManagedDocSource(parent, {
                    scope: 'other',
                    source_revision: 'r1',
                    source_body: '# Bad'
                }, options);
            } catch (error) {
                payloadTargetOverrideRejected = /must not replace target field scope/.test(
                    String(error && error.message || '')
                );
            }
            return {
                adapterRequests,
                extraFieldRejected,
                fixedSession: {
                    mountedTarget,
                    modes,
                    reads,
                    reloads,
                    writes
                },
                failureSession: {
                    failureModes,
                    failureReads,
                    failureStatus,
                    failureTarget
                },
                payloadTargetOverrideRejected,
                requests,
                sourceModeRequests
            };
        }"""
    )
    expected_target = {
        "scope": "studio",
        "sub_scope": "tags",
        "doc_id": "detail-doc",
    }
    if result["extraFieldRejected"] is not True or result["payloadTargetOverrideRejected"] is not True:
        raise AssertionError(f"managed target allowlist changed: {result!r}")
    if result["requests"] != [
        {
            "url": "http://manage.test/docs/source?scope=studio&doc_id=parent-doc",
            "method": "GET",
            "body": None,
        },
        {
            "url": "http://manage.test/docs/source?scope=studio&sub_scope=tags&doc_id=detail-doc",
            "method": "GET",
            "body": None,
        },
        {
            "url": "http://manage.test/docs/source/rebuild",
            "method": "POST",
            "body": {
                **expected_target,
                "source_revision": "r1",
                "source_body": "# Detail",
            },
        },
        {
            "url": "http://manage.test/docs/open-source",
            "method": "POST",
            "body": {
                "scope": "studio",
                "doc_id": "parent-doc",
                "editor": "vscode",
            },
        },
        {
            "url": "http://manage.test/docs/open-source",
            "method": "POST",
            "body": {**expected_target, "editor": "vscode"},
        },
        {
            "url": "http://manage.test/docs/diagram-sources?scope=studio&sub_scope=tags&doc_id=detail-doc",
            "method": "GET",
            "body": None,
        },
        {
            "url": "http://manage.test/docs/open-diagram-source",
            "method": "POST",
            "body": {
                **expected_target,
                "editor": "vscode",
                "media_identity": "docs/studio/svg/diagram.svg",
            },
        },
    ]:
        raise AssertionError(f"source target transport changed: {result!r}")
    if result["adapterRequests"] != [
        {
            "url": "http://adapter.test/docs/source?scope=studio&sub_scope=tags&doc_id=detail-doc",
            "body": None,
        },
        {
            "url": "http://adapter.test/docs/source/rebuild",
            "body": {
                **expected_target,
                "source_revision": "r2",
                "source_body": "# Adapter",
            },
        },
    ]:
        raise AssertionError(f"source adapter target handoff changed: {result!r}")
    if result["sourceModeRequests"] != [
        {
            "modeId": "markdown-source",
            "sourceTarget": expected_target,
        }
    ]:
        raise AssertionError(f"source entry did not mount its explicit target: {result!r}")
    if result["fixedSession"] != {
        "mountedTarget": expected_target,
        "modes": ["rendered-document"],
        "reads": [expected_target],
        "reloads": [expected_target],
        "writes": [
            {
                "target": expected_target,
                "payload": {
                    "source_revision": "r1",
                    "source_body": "# Changed",
                },
            }
        ],
    }:
        raise AssertionError(f"mounted source target was not retained: {result!r}")
    if result["failureSession"] != {
        "failureModes": [],
        "failureReads": 1,
        "failureStatus": "builder failed",
        "failureTarget": {
            "scope": "studio",
            "doc_id": "parent-doc",
        },
    }:
        raise AssertionError(f"source rebuild failure recovery changed: {result!r}")


def assert_modal_insertion_cancellation_and_stale_guard(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__catalogueTokenSmoke;
            const registryPayload = {
                schema_version: 'docs_semantic_token_registry_v1',
                target_lookup_url: '/docs-viewer/data/generated/semantic-tokens/target-lookup.json',
                families: [{
                    key: 'catalogue',
                    target_types: [
                        { key: 'work' },
                        { key: 'series' },
                        { key: 'moment' }
                    ]
                }]
            };
            const targetPayload = {
                schema_version: 'docs_semantic_token_target_lookup_v1',
                targets: [
                    {
                        family: 'catalogue',
                        target_type: 'work',
                        target_id: '00008',
                        title: 'nerve',
                        href: '/works/?work=00008',
                        meta: ['July 1990 – January 1995', 'nerve']
                    },
                    {
                        family: 'catalogue',
                        target_type: 'series',
                        target_id: '105',
                        title: 'nerve series',
                        href: '/series/?series=105',
                        meta: ['1990-95']
                    }
                ]
            };
            const fakeFetch = async url => ({
                ok: true,
                json: async () => String(url).includes('target-lookup')
                    ? targetPayload
                    : registryPayload
            });

            async function waitForLoaded(root) {
                for (let index = 0; index < 20; index += 1) {
                    const input = root.querySelector('#docsViewerCatalogueTokenSearch');
                    if (input && !input.disabled) return;
                    await new Promise(resolve => setTimeout(resolve, 0));
                }
                throw new Error('Catalogue modal did not load targets.');
            }

            async function insertedCase() {
                const root = document.createElement('div');
                document.body.appendChild(root);
                const state = {
                    value: 'Before nerve after',
                    replaceCount: 0
                };
                const capture = { start: 7, end: 12, text: 'nerve', revision: 0 };
                const adapter = {
                    focus() {},
                    replaceCapturedSelection(candidate, value) {
                        if (JSON.stringify(candidate) !== JSON.stringify(capture)) return false;
                        state.replaceCount += 1;
                        state.value = state.value.slice(0, candidate.start)
                            + value
                            + state.value.slice(candidate.end);
                        return true;
                    },
                    setStatus() {}
                };
                const modalPromise = smoke.modal.openCatalogueTokenModal({
                    adapter,
                    capture,
                    fetch: fakeFetch,
                    root
                });
                await waitForLoaded(root);
                const search = root.querySelector('#docsViewerCatalogueTokenSearch');
                const title = root.querySelector('#docsViewerCatalogueTokenTitle');
                const seeded = {
                    modalId: root.querySelector('[data-role="docs-viewer-management-modal"]').id,
                    nextTabTarget: (() => {
                        const tabbable = Array.from(root.querySelectorAll(
                            'input:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"])'
                        ));
                        return tabbable[tabbable.indexOf(search) + 1]?.id || '';
                    })(),
                    query: search.value,
                    title: title.value,
                    rows: Array.from(root.querySelectorAll('[data-target-index]'))
                        .map(node => ({
                            tabIndex: node.tabIndex,
                            tagName: node.tagName,
                            targetType: node.querySelector('.docsViewerCatalogueTargetPicker__rowKind').textContent,
                            targetId: node.querySelector('.docsViewerCatalogueTargetPicker__rowId').textContent,
                            title: node.querySelector('.docsViewerCatalogueTargetPicker__rowTitle').textContent,
                            meta: node.querySelector('.docsViewerCatalogueTargetPicker__rowMeta')?.textContent || ''
                        }))
                };
                search.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'ArrowDown',
                    bubbles: true
                }));
                search.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter',
                    bubbles: true
                }));
                const keyboardSelected = root.querySelector('[data-target-index="1"]')
                    .getAttribute('aria-selected') === 'true';
                const titleAfterKeyboard = title.value;
                root.querySelector('[data-target-index="0"]').click();
                const titleAfterClick = title.value;
                root.querySelector('[data-target-index="1"]').click();
                title.value = String.raw`nerve | chosen ] \\ path`;
                title.dispatchEvent(new Event('input', { bubbles: true }));
                root.querySelector('[data-role="modal-primary"]').click();
                const modalResult = await modalPromise;
                root.remove();
                return {
                    keyboardSelected,
                    modalResult,
                    seeded,
                    state,
                    titleAfterClick,
                    titleAfterKeyboard
                };
            }

            async function exactTokenCase() {
                const root = document.createElement('div');
                document.body.appendChild(root);
                const raw = '[[catalogue:work:00008|display nerve]]';
                const state = {
                    value: 'Before ' + raw + ' after',
                    replaceCount: 0
                };
                const capture = {
                    start: 7,
                    end: 7 + raw.length,
                    text: raw,
                    revision: 0
                };
                const modalPromise = smoke.modal.openCatalogueTokenModal({
                    adapter: {
                        focus() {},
                        replaceCapturedSelection(candidate, token) {
                            if (JSON.stringify(candidate) !== JSON.stringify(capture)) return false;
                            state.replaceCount += 1;
                            state.value = state.value.slice(0, candidate.start)
                                + token
                                + state.value.slice(candidate.end);
                            return true;
                        },
                        setStatus() {}
                    },
                    capture,
                    fetch: fakeFetch,
                    root
                });
                await waitForLoaded(root);
                const search = root.querySelector('#docsViewerCatalogueTokenSearch');
                const title = root.querySelector('#docsViewerCatalogueTokenTitle');
                const row = root.querySelector('[data-target-index="0"]');
                const restored = {
                    query: search.value,
                    rowCount: root.querySelectorAll('[data-target-index]').length,
                    selected: row && row.getAttribute('aria-selected') === 'true',
                    targetId: row && row.querySelector(
                        '.docsViewerCatalogueTargetPicker__rowId'
                    ).textContent,
                    targetType: row && row.querySelector(
                        '.docsViewerCatalogueTargetPicker__rowKind'
                    ).textContent,
                    title: title.value
                };
                root.querySelector('[data-role="modal-primary"]').click();
                const modalResult = await modalPromise;
                root.remove();
                return { modalResult, restored, state };
            }

            async function unavailableTokenCase() {
                const root = document.createElement('div');
                document.body.appendChild(root);
                const raw = '[[catalogue:work:99999|lost nerve]]';
                let replaceCount = 0;
                const modalPromise = smoke.modal.openCatalogueTokenModal({
                    adapter: {
                        focus() {},
                        replaceCapturedSelection() {
                            replaceCount += 1;
                            return true;
                        }
                    },
                    capture: {
                        start: 0,
                        end: raw.length,
                        text: raw,
                        revision: 0
                    },
                    fetch: fakeFetch,
                    root
                });
                await waitForLoaded(root);
                const initial = {
                    query: root.querySelector('#docsViewerCatalogueTokenSearch').value,
                    rowCount: root.querySelectorAll('[data-target-index]').length,
                    status: root.querySelector(
                        '[data-role="catalogue-search-status"]'
                    ).textContent,
                    title: root.querySelector('#docsViewerCatalogueTokenTitle').value
                };
                root.querySelector('[data-role="modal-primary"]').click();
                const remainedOpen = Boolean(
                    root.querySelector('[data-role="docs-viewer-management-modal"]')
                );
                root.querySelector('[data-role="modal-cancel"]').click();
                await modalPromise;
                root.remove();
                return { initial, remainedOpen, replaceCount };
            }

            async function cancelledCase() {
                const root = document.createElement('div');
                document.body.appendChild(root);
                let replaceCount = 0;
                const modalPromise = smoke.modal.openCatalogueTokenModal({
                    adapter: {
                        focus() {},
                        replaceCapturedSelection() {
                            replaceCount += 1;
                            return true;
                        }
                    },
                    capture: { start: 0, end: 0, text: '', revision: 0 },
                    fetch: fakeFetch,
                    root
                });
                await waitForLoaded(root);
                root.querySelector('[data-role="modal-cancel"]').click();
                const modalResult = await modalPromise;
                root.remove();
                return { modalResult, replaceCount };
            }

            async function staleCase() {
                const root = document.createElement('div');
                document.body.appendChild(root);
                let replaceCount = 0;
                const modalPromise = smoke.modal.openCatalogueTokenModal({
                    adapter: {
                        focus() {},
                        replaceCapturedSelection() {
                            replaceCount += 1;
                            return false;
                        }
                    },
                    capture: { start: 0, end: 0, text: '', revision: 0 },
                    fetch: fakeFetch,
                    root
                });
                await waitForLoaded(root);
                const search = root.querySelector('#docsViewerCatalogueTokenSearch');
                search.value = 'nerve';
                search.dispatchEvent(new Event('input', { bubbles: true }));
                root.querySelector('[data-target-index="0"]').click();
                root.querySelector('[data-role="modal-primary"]').click();
                const remainedOpen = Boolean(root.querySelector('[data-role="docs-viewer-management-modal"]'));
                root.querySelector('[data-role="modal-cancel"]').click();
                await modalPromise;
                root.remove();
                return { remainedOpen, replaceCount };
            }

            async function caretCase() {
                const root = document.createElement('div');
                document.body.appendChild(root);
                let value = 'Before  after';
                const capture = { start: 7, end: 7, text: '', revision: 0 };
                const modalPromise = smoke.modal.openCatalogueTokenModal({
                    adapter: {
                        focus() {},
                        replaceCapturedSelection(candidate, token) {
                            value = value.slice(0, candidate.start)
                                + token
                                + value.slice(candidate.end);
                            return true;
                        }
                    },
                    capture,
                    fetch: fakeFetch,
                    root
                });
                await waitForLoaded(root);
                const search = root.querySelector('#docsViewerCatalogueTokenSearch');
                search.value = 'nerve';
                search.dispatchEvent(new Event('input', { bubbles: true }));
                root.querySelector('[data-target-index="0"]').click();
                const title = root.querySelector('#docsViewerCatalogueTokenTitle').value;
                root.querySelector('[data-role="modal-primary"]').click();
                await modalPromise;
                root.remove();
                return { title, value };
            }

            async function validationCase() {
                const root = document.createElement('div');
                document.body.appendChild(root);
                let replaceCount = 0;
                const modalPromise = smoke.modal.openCatalogueTokenModal({
                    adapter: {
                        focus() {},
                        replaceCapturedSelection() {
                            replaceCount += 1;
                            return true;
                        }
                    },
                    capture: { start: 0, end: 0, text: '', revision: 0 },
                    fetch: fakeFetch,
                    root
                });
                await waitForLoaded(root);
                const search = root.querySelector('#docsViewerCatalogueTokenSearch');
                const title = root.querySelector('#docsViewerCatalogueTokenTitle');
                search.value = 'nerve';
                search.dispatchEvent(new Event('input', { bubbles: true }));
                root.querySelector('[data-target-index="0"]').click();
                search.value = 'absent';
                search.dispatchEvent(new Event('input', { bubbles: true }));
                root.querySelector('[data-role="modal-primary"]').click();
                const currentResultRequired = Boolean(
                    root.querySelector('[data-role="docs-viewer-management-modal"]')
                ) && replaceCount === 0;
                search.value = 'nerve';
                search.dispatchEvent(new Event('input', { bubbles: true }));
                root.querySelector('[data-target-index="0"]').click();
                title.value = '';
                title.dispatchEvent(new Event('input', { bubbles: true }));
                root.querySelector('[data-role="modal-primary"]').click();
                const titleRequired = Boolean(
                    root.querySelector('[data-role="docs-viewer-management-modal"]')
                ) && replaceCount === 0;
                root.querySelector('[data-role="modal-cancel"]').click();
                await modalPromise;
                root.remove();
                return { currentResultRequired, replaceCount, titleRequired };
            }

            return {
                cancelled: await cancelledCase(),
                caret: await caretCase(),
                exactToken: await exactTokenCase(),
                inserted: await insertedCase(),
                stale: await staleCase(),
                unavailableToken: await unavailableTokenCase(),
                validation: await validationCase()
            };
        }"""
    )
    inserted = result["inserted"]
    if inserted["seeded"] != {
        "modalId": "catalogue-token-add-modal",
        "nextTabTarget": "docsViewerCatalogueTokenResults",
        "query": "nerve",
        "title": "nerve",
        "rows": [
            {
                "tabIndex": -1,
                "tagName": "DIV",
                "targetType": "work",
                "targetId": "00008",
                "title": "nerve",
                "meta": "July 1990 – January 1995 · nerve",
            },
            {
                "tabIndex": -1,
                "tagName": "DIV",
                "targetType": "series",
                "targetId": "105",
                "title": "nerve series",
                "meta": "1990-95",
            },
        ],
    }:
        raise AssertionError(f"selection prefilling or mixed rows changed: {result!r}")
    if not inserted["keyboardSelected"]:
        raise AssertionError(f"keyboard target selection changed: {result!r}")
    if (
        inserted["titleAfterKeyboard"] != "nerve series"
        or inserted["titleAfterClick"] != "nerve"
    ):
        raise AssertionError(f"Catalogue selection did not update Title: {result!r}")
    if inserted["state"] != {
        "value": "Before [[catalogue:series:105|nerve \\| chosen \\] \\\\ path]] after",
        "replaceCount": 1,
    }:
        raise AssertionError(f"Catalogue insertion changed: {result!r}")
    if (
        not inserted["modalResult"]["confirmed"]
        or inserted["modalResult"]["target"]["targetType"] != "series"
        or inserted["modalResult"]["target"]["targetId"] != "105"
    ):
        raise AssertionError(f"Catalogue insertion did not confirm: {result!r}")
    if result["cancelled"] != {
        "modalResult": {"confirmed": False},
        "replaceCount": 0,
    }:
        raise AssertionError(f"Catalogue cancellation changed source: {result!r}")
    if result["caret"] != {
        "title": "nerve",
        "value": "Before [[catalogue:work:00008|nerve]] after",
    }:
        raise AssertionError(f"caret insertion or canonical-title prefilling changed: {result!r}")
    exact_token = result["exactToken"]
    if exact_token["restored"] != {
        "query": "work:00008",
        "rowCount": 1,
        "selected": True,
        "targetId": "00008",
        "targetType": "work",
        "title": "display nerve",
    }:
        raise AssertionError(f"complete Catalogue token identity was not restored: {result!r}")
    if (
        exact_token["state"] != {
            "value": "Before [[catalogue:work:00008|display nerve]] after",
            "replaceCount": 1,
        }
        or exact_token["modalResult"]["title"] != "display nerve"
        or exact_token["modalResult"]["target"]["targetId"] != "00008"
        or exact_token["modalResult"]["target"]["targetType"] != "work"
    ):
        raise AssertionError(f"restored Catalogue token confirmation changed: {result!r}")
    if result["stale"] != {
        "remainedOpen": True,
        "replaceCount": 1,
    }:
        raise AssertionError(f"stale captured range was not rejected: {result!r}")
    if result["validation"] != {
        "currentResultRequired": True,
        "replaceCount": 0,
        "titleRequired": True,
    }:
        raise AssertionError(f"Catalogue modal validation gate changed: {result!r}")
    if result["unavailableToken"] != {
        "initial": {
            "query": "work:99999",
            "rowCount": 0,
            "status": "Catalogue target work:99999 is unavailable.",
            "title": "lost nerve",
        },
        "remainedOpen": True,
        "replaceCount": 0,
    }:
        raise AssertionError(f"unavailable token identity fell back to fuzzy search: {result!r}")


def assert_catalogue_info_exact_range_update_remove_and_stale_guard(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__catalogueTokenSmoke;
            const registryPayload = {
                schema_version: 'docs_semantic_token_registry_v1',
                target_lookup_url: '/docs-viewer/data/generated/semantic-tokens/target-lookup.json',
                families: [{
                    key: 'catalogue',
                    labels: { info_view: 'Catalogue token' },
                    target_types: [{
                        key: 'work',
                        label: 'Work',
                        id_policy: {
                            canonical_pattern: '^\\\\d{5}$',
                            input_pattern: '^\\\\d{1,5}$',
                            normalizer: 'digits_left_pad',
                            width: 5
                        }
                    }]
                }]
            };
            const targetPayload = {
                schema_version: 'docs_semantic_token_target_lookup_v1',
                targets: [{
                    family: 'catalogue',
                    target_type: 'work',
                    target_id: '00638',
                    title: '3 symbols',
                    href: '/works/?work=00638',
                    meta: ['2007']
                }]
            };
            const fakeFetch = async url => ({
                ok: true,
                json: async () => String(url).includes('target-lookup')
                    ? targetPayload
                    : registryPayload
            });

            function createState() {
                const state = {
                    value: 'Before [[catalogue:work:00638|3 symbols]] after',
                    revision: 0,
                    selection: { start: 18, end: 18 },
                    listeners: new Set(),
                    status: ''
                };
                state.adapter = {
                    getBufferSnapshot() {
                        return { revision: state.revision, value: state.value };
                    },
                    getSelection() {
                        return {
                            start: state.selection.start,
                            end: state.selection.end,
                            text: state.value.slice(state.selection.start, state.selection.end)
                        };
                    },
                    onSelectionChange(listener) {
                        state.listeners.add(listener);
                        return () => state.listeners.delete(listener);
                    },
                    selectCapturedRange(capture) {
                        if (
                            capture.revision !== state.revision
                            || state.value.slice(capture.start, capture.end) !== capture.text
                        ) return false;
                        state.selection = { start: capture.start, end: capture.end };
                        state.listeners.forEach(listener => listener());
                        return true;
                    },
                    replaceCapturedRange(capture, replacement, mode) {
                        if (
                            capture.revision !== state.revision
                            || state.value.slice(capture.start, capture.end) !== capture.text
                        ) return false;
                        state.value = state.value.slice(0, capture.start)
                            + replacement
                            + state.value.slice(capture.end);
                        state.revision += 1;
                        state.selection = mode === 'select'
                            ? { start: capture.start, end: capture.start + replacement.length }
                            : { start: capture.start + replacement.length, end: capture.start + replacement.length };
                        state.listeners.forEach(listener => listener());
                        return true;
                    },
                    setStatus(message) {
                        state.status = message;
                    }
                };
                return state;
            }

            async function mountView(state) {
                const mount = document.createElement('div');
                document.body.appendChild(mount);
                const view = smoke.infoView.createCatalogueTokenInfoView({ fetch: fakeFetch });
                const context = {
                    mount,
                    sourceEditorServices: {
                        getActiveSourceEditorContextAdapter() {
                            return state.adapter;
                        },
                        publicPreviewBase: 'http://127.0.0.1:4000'
                    }
                };
                await view.mount(context);
                return { context, mount, view };
            }

            const state = createState();
            const mounted = await mountView(state);
            const initial = {
                selection: Object.assign({}, state.selection),
                rows: Array.from(mounted.mount.querySelectorAll('.docsViewer__metadataInfoRow'))
                    .map(row => row.textContent),
                destinationHref: mounted.mount.querySelector(
                    '.docsViewer__metadataInfoRow a'
                ).href,
                title: mounted.mount.querySelector('input').value
            };
            const titleInput = mounted.mount.querySelector('input');
            titleInput.value = 'three signs';
            Array.from(mounted.mount.querySelectorAll('button'))
                .find(button => button.textContent === 'Update token')
                .click();
            const afterUpdate = {
                selection: Object.assign({}, state.selection),
                status: state.status,
                title: mounted.mount.querySelector('input').value,
                value: state.value
            };
            Array.from(mounted.mount.querySelectorAll('button'))
                .find(button => button.textContent === 'Remove token')
                .click();
            const afterRemove = {
                empty: mounted.mount.textContent.includes('Place the caret inside a Catalogue token'),
                status: state.status,
                value: state.value
            };
            mounted.view.unmount(mounted.context);
            mounted.mount.remove();

            const staleState = createState();
            const staleMounted = await mountView(staleState);
            staleState.revision += 1;
            staleMounted.mount.querySelector('input').value = 'stale title';
            Array.from(staleMounted.mount.querySelectorAll('button'))
                .find(button => button.textContent === 'Update token')
                .click();
            const stale = {
                error: staleMounted.mount.textContent.includes(
                    'Markdown source changed. Select the token again.'
                ),
                value: staleState.value
            };
            staleMounted.view.unmount(staleMounted.context);
            staleMounted.mount.remove();
            const rendered = document.createElement('div');
            rendered.innerHTML = [
                '<a href="/works/?work=00638"',
                ' data-semantic-token-family="catalogue"',
                ' data-semantic-token-target-type="work"',
                ' data-semantic-token-target-id="00638">3 symbols</a>'
            ].join('');
            const mountedLinkCount = smoke.semanticTargets.mountSemanticTokenTargetLinks(
                rendered,
                'http://127.0.0.1:4000'
            );
            return {
                afterRemove,
                afterUpdate,
                initial,
                rendered: {
                    href: rendered.querySelector('a').href,
                    mountedLinkCount
                },
                stale
            };
        }"""
    )
    expected_raw = "[[catalogue:work:00638|3 symbols]]"
    if result["initial"] != {
        "selection": {"start": 7, "end": 41},
        "rows": [
            "FamilyCatalogue",
            "Target typework",
            "Target ID00638",
            "Catalogue title3 symbols",
            "Destination/works/?work=00638",
        ],
        "destinationHref": "http://127.0.0.1:4000/works/?work=00638",
        "title": "3 symbols",
    }:
        raise AssertionError(f"Catalogue Info recognition/context changed: {result!r}")
    if result["afterUpdate"] != {
        "selection": {"start": 7, "end": 43},
        "status": "",
        "title": "three signs",
        "value": "Before [[catalogue:work:00638|three signs]] after",
    }:
        raise AssertionError(f"Catalogue Info update changed: {result!r}")
    if result["afterRemove"] != {
        "empty": True,
        "status": "",
        "value": "Before  after",
    }:
        raise AssertionError(f"Catalogue Info removal changed: {result!r}")
    if result["stale"] != {
        "error": True,
        "value": f"Before {expected_raw} after",
    }:
        raise AssertionError(f"Catalogue Info stale-range guard changed: {result!r}")
    if result["rendered"] != {
        "href": "http://127.0.0.1:4000/works/?work=00638",
        "mountedLinkCount": 1,
    }:
        raise AssertionError(f"rendered Catalogue destination changed: {result!r}")


def assert_real_keyboard_tab_and_scroll_flow(page: Page) -> None:
    page.evaluate(
        """() => {
            const smoke = window.__catalogueTokenSmoke;
            const root = document.createElement('div');
            document.body.appendChild(root);
            const registryPayload = {
                schema_version: 'docs_semantic_token_registry_v1',
                target_lookup_url: '/docs-viewer/data/generated/semantic-tokens/target-lookup.json',
                families: [{
                    key: 'catalogue',
                    target_types: [
                        { key: 'work' },
                        { key: 'series' },
                        { key: 'moment' }
                    ]
                }]
            };
            const targetPayload = {
                schema_version: 'docs_semantic_token_target_lookup_v1',
                targets: Array.from({ length: 25 }, (_value, index) => {
                    const id = String(index + 1).padStart(5, '0');
                    return {
                        family: 'catalogue',
                        target_type: 'work',
                        target_id: id,
                        title: 'nerve ' + id,
                        href: '/works/?work=' + id,
                        meta: []
                    };
                })
            };
            const fakeFetch = async url => ({
                ok: true,
                json: async () => String(url).includes('target-lookup')
                    ? targetPayload
                    : registryPayload
            });
            window.__catalogueKeyboardRoot = root;
            window.__catalogueKeyboardModalPromise = smoke.modal.openCatalogueTokenModal({
                adapter: {
                    focus() {},
                    replaceCapturedSelection() { return true; }
                },
                capture: { start: 0, end: 5, text: 'nerve', revision: 0 },
                fetch: fakeFetch,
                root
            });
        }"""
    )
    page.wait_for_function(
        """() => {
            const search = document.querySelector('#docsViewerCatalogueTokenSearch');
            return search && !search.disabled
                && document.querySelectorAll('#docsViewerCatalogueTokenResults [data-target-index]').length === 20;
        }"""
    )
    page.locator("#docsViewerCatalogueTokenResults").evaluate(
        """node => {
            node.style.maxHeight = '80px';
            node.style.overflow = 'auto';
        }"""
    )
    page.locator("#catalogue-token-add-modal").evaluate(
        """node => {
            node.dataset.keyboardNavigation = 'true';
        }"""
    )
    page.locator("#docsViewerCatalogueTokenResults").click(position={"x": 2, "y": 2})
    initial_focus_state = page.evaluate(
        """() => {
            const results = document.querySelector('#docsViewerCatalogueTokenResults');
            const style = getComputedStyle(results);
            return {
                active: document.activeElement === results,
                boxShadow: style.boxShadow,
                focusVisible: results.matches(':focus-visible'),
                outlineStyle: style.outlineStyle
            };
        }"""
    )
    if initial_focus_state != {
        "active": True,
        "boxShadow": "none",
        "focusVisible": False,
        "outlineStyle": "none",
    }:
        raise AssertionError(
            f"Initial non-focus-visible Catalogue list focus changed: {initial_focus_state!r}"
        )
    page.locator("#docsViewerCatalogueTokenSearch").focus()
    page.keyboard.press("Tab")
    if page.evaluate("document.activeElement?.id") != "docsViewerCatalogueTokenResults":
        raise AssertionError("Tab from Catalogue search did not advance to the results list")
    layout_state = page.evaluate(
        """() => {
            const results = document.querySelector('#docsViewerCatalogueTokenResults');
            const resultsRect = results.getBoundingClientRect();
            const rows = Array.from(results.querySelectorAll('[data-target-index]'));
            const style = getComputedStyle(results);
            return {
                boxShadow: style.boxShadow,
                clientWidth: results.clientWidth,
                outlineStyle: style.outlineStyle,
                scrollWidth: results.scrollWidth,
                rowsInside: rows.every(node => {
                    const rect = node.getBoundingClientRect();
                    return rect.left >= resultsRect.left && rect.right <= resultsRect.right;
                })
            };
        }"""
    )
    if (
        layout_state["boxShadow"] != "none"
        or layout_state["outlineStyle"] != "none"
        or layout_state["scrollWidth"] > layout_state["clientWidth"]
        or not layout_state["rowsInside"]
    ):
        raise AssertionError(f"Catalogue results focus or layout changed: {layout_state!r}")
    for _index in range(12):
        page.keyboard.press("ArrowDown")
    keyboard_state = page.evaluate(
        """() => {
            const results = document.querySelector('#docsViewerCatalogueTokenResults');
            const style = getComputedStyle(results);
            return {
                activeDescendant: results?.getAttribute('aria-activedescendant') || '',
                boxShadow: style.boxShadow,
                outlineStyle: style.outlineStyle,
                scrollTop: results?.scrollTop || 0
            };
        }"""
    )
    if keyboard_state["activeDescendant"] != "docsViewerCatalogueTargetOption-12":
        raise AssertionError(f"Arrow keys did not move the active Catalogue result: {keyboard_state!r}")
    if keyboard_state["scrollTop"] <= 0:
        raise AssertionError(f"Arrow-key navigation did not reveal the active result: {keyboard_state!r}")
    if (
        keyboard_state["boxShadow"] != "none"
        or keyboard_state["outlineStyle"] != "none"
    ):
        raise AssertionError(f"Arrow keys restored the Catalogue list border: {keyboard_state!r}")
    page.keyboard.press("Enter")
    if page.locator('[data-target-index="12"]').get_attribute("aria-selected") != "true":
        raise AssertionError("Enter did not commit the active Catalogue result")
    if page.locator("#docsViewerCatalogueTokenTitle").input_value() != "nerve 00013":
        raise AssertionError("Enter selection did not update the Catalogue Title")
    page.keyboard.press("Tab")
    if page.evaluate("document.activeElement?.id") != "docsViewerCatalogueTokenTitle":
        raise AssertionError("Tab from Catalogue results did not advance directly to Title")
    page.keyboard.press("Shift+Tab")
    if page.evaluate("document.activeElement?.id") != "docsViewerCatalogueTokenResults":
        raise AssertionError("Shift+Tab from Catalogue Title did not return to results")
    page.locator(
        "#catalogue-token-add-modal button[data-role='modal-cancel']"
    ).click()
    page.evaluate(
        """async () => {
            await window.__catalogueKeyboardModalPromise;
            window.__catalogueKeyboardRoot.remove();
            delete window.__catalogueKeyboardModalPromise;
            delete window.__catalogueKeyboardRoot;
        }"""
    )


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="domcontentloaded")
    install_styles(page, base_url)
    install_modules(page)
    assert_contract_fixture_and_mixed_search(page)
    assert_source_adapter_captures_and_guards_range(page)
    assert_source_target_transport_and_fixed_session(page)
    assert_modal_insertion_cancellation_and_stale_guard(page)
    assert_catalogue_info_exact_range_update_remove_and_stale_guard(page)
    assert_real_keyboard_tab_and_scroll_flow(page)


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
                page.on(
                    "console",
                    lambda message: errors.append(message.text)
                    if message.type == "error"
                    else None,
                )
                run_smoke(page, base_url)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if errors:
        raise AssertionError(f"page errors during Catalogue token module smoke: {errors!r}")
    print("Docs Viewer Catalogue token modules OK")


if __name__ == "__main__":
    main()

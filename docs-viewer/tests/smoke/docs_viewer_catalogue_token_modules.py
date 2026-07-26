#!/usr/bin/env python3
"""Smoke-check the CT-P1 Catalogue token browser-module contracts."""

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
                '/docs-viewer/runtime/js/management/source-editor/semantic-reference-registry.js'
            );
            const pilotTargets = await import(
                '/docs-viewer/runtime/js/management/source-editor/semantic-targets.js'
            );
            const sourceEditor = await import(
                '/docs-viewer/runtime/js/management/source-editor/source-editor.js'
            );
            window.__catalogueTokenSmoke = {
                contract,
                contribution,
                modal,
                pilotTargets,
                registry,
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
            const registry = smoke.registry.normalizeSemanticReferenceRegistry({
                schema_version: 'docs_semantic_reference_registry_v1',
                target_lookup_url: '/docs-viewer/data/generated/semantic-references/target-lookup.json',
                kinds: [
                    { kind: 'work' },
                    { kind: 'series' },
                    { kind: 'moment' }
                ]
            });
            const pilotTargets = smoke.pilotTargets.normalizeSemanticTargets({
                targets: fixture.target_lookup_example.targets.map(row => ({
                    kind: row.target_type,
                    id: row.target_id,
                    title: row.title,
                    href: row.href,
                    meta: row.meta
                }))
            }, registry);
            const support = smoke.targets.createCatalogueTargetSupport(registry, pilotTargets);
            const matches = smoke.targets.collectCatalogueTargetMatches(support, 'nerve', 10);
            const definition = smoke.contribution.catalogueTokenControlDefinition();
            const handlers = smoke.contribution.createCatalogueTokenMainViewControlHandlers();
            const renderedButton = smoke.contribution.catalogueTokenControlRenderer({
                document
            });
            return {
                definition,
                fixtureUiContributions: fixture.catalogue_definition.ui_contributions,
                handlerIds: Object.keys(handlers),
                matches: matches.map(target => ({
                    family: target.family,
                    targetType: target.targetType,
                    targetId: target.targetId,
                    title: target.title,
                    href: target.href,
                    meta: target.meta
                })),
                modalId: smoke.modal.CATALOGUE_TOKEN_MODAL_ID,
                rendererIcon: renderedButton.textContent,
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
            const controlStates = {};
            const mode = smoke.sourceEditor.createDocsViewerSourceEditorMode();
            await mode.mount({
                root,
                mount,
                selectedDoc: { doc_id: 'fixture' },
                collectionProvider: {
                    readSource() {
                        return Promise.resolve({
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
                replaced,
                snapshot,
                staleRejected
            };
        }"""
    )
    if result != {
        "capture": {"start": 7, "end": 12, "text": "nerve", "revision": 0},
        "controlState": {"busy": False, "disabled": False},
        "replaced": True,
        "snapshot": {
            "revision": 2,
            "value": "Before [[catalogue:work:00008|nerve]] after",
        },
        "staleRejected": True,
    }:
        raise AssertionError(f"captured source-range adapter changed: {result!r}")


def assert_modal_insertion_cancellation_and_stale_guard(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__catalogueTokenSmoke;
            const registryPayload = {
                schema_version: 'docs_semantic_reference_registry_v1',
                target_lookup_url: '/docs-viewer/data/generated/semantic-references/target-lookup.json',
                kinds: [
                    { kind: 'work' },
                    { kind: 'series' },
                    { kind: 'moment' }
                ]
            };
            const targetPayload = {
                schema_version: 'docs_semantic_reference_target_lookup_v1',
                targets: [
                    {
                        kind: 'work',
                        id: '00008',
                        title: 'nerve',
                        href: '/works/?work=00008',
                        meta: ['July 1990 – January 1995', 'nerve']
                    },
                    {
                        kind: 'series',
                        id: '105',
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
                            targetType: node.querySelector('.docsViewerSemanticPicker__rowKind').textContent,
                            targetId: node.querySelector('.docsViewerSemanticPicker__rowId').textContent,
                            title: node.querySelector('.docsViewerSemanticPicker__rowTitle').textContent,
                            meta: node.querySelector('.docsViewerSemanticPicker__rowMeta')?.textContent || ''
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
                inserted: await insertedCase(),
                stale: await staleCase(),
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


def assert_real_keyboard_tab_and_scroll_flow(page: Page) -> None:
    page.evaluate(
        """() => {
            const smoke = window.__catalogueTokenSmoke;
            const root = document.createElement('div');
            document.body.appendChild(root);
            const registryPayload = {
                schema_version: 'docs_semantic_reference_registry_v1',
                target_lookup_url: '/docs-viewer/data/generated/semantic-references/target-lookup.json',
                kinds: [
                    { kind: 'work' },
                    { kind: 'series' },
                    { kind: 'moment' }
                ]
            };
            const targetPayload = {
                schema_version: 'docs_semantic_reference_target_lookup_v1',
                targets: Array.from({ length: 25 }, (_value, index) => {
                    const id = String(index + 1).padStart(5, '0');
                    return {
                        kind: 'work',
                        id,
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
    if keyboard_state["activeDescendant"] != "docsViewerSemanticTargetOption-12":
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
    assert_modal_insertion_cancellation_and_stale_guard(page)
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

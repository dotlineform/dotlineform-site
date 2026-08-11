#!/usr/bin/env python3
"""Smoke-check the TDL-2.3 Tag semantic-token browser contracts."""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from docs_viewer_catalogue_token_modules import start_static_server


def install_modules(page: Page) -> None:
    page.evaluate(
        """async () => {
            const registry = await import(
                '/docs-viewer/runtime/js/management/source-editor/semantic-token-registry.js'
            );
            const semanticTargets = await import(
                '/docs-viewer/runtime/js/management/source-editor/semantic-token-targets.js'
            );
            const parser = await import(
                '/docs-viewer/runtime/js/management/source-editor/tag-token-parser.js'
            );
            const targets = await import(
                '/docs-viewer/runtime/js/management/source-editor/tag-token-targets.js'
            );
            const modal = await import(
                '/docs-viewer/runtime/js/management/source-editor/tag-token-modal.js'
            );
            const contribution = await import(
                '/docs-viewer/runtime/js/management/source-editor/tag-token-contribution.js'
            );
            const infoView = await import(
                '/docs-viewer/runtime/js/management/source-editor/tag-token-info-view.js'
            );
            const hostedViews = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js'
            );
            const report = await import(
                '/docs-viewer/runtime/js/reports/semantic-tokens-report.js'
            );
            window.__tagTokenSmoke = {
                contribution,
                hostedViews,
                infoView,
                modal,
                parser,
                registry,
                report,
                semanticTargets,
                targets
            };
        }"""
    )


def assert_registry_parser_discovery_and_wiring(page: Page) -> None:
    result = page.evaluate(
        r"""async () => {
            const smoke = window.__tagTokenSmoke;
            const registryPayload = {
                schema_version: 'docs_semantic_token_registry_v1',
                target_lookup_url: '/targets.json',
                families: [
                    {
                        key: 'catalogue',
                        labels: {},
                        occurrence_fields: [],
                        ui_contributions: {},
                        target_types: [{
                            key: 'work',
                            id_policy: { canonical_pattern: '^\\d{5}$' }
                        }]
                    },
                    {
                        key: 'tag',
                        labels: {},
                        occurrence_fields: [],
                        ui_contributions: {
                            source_action: 'source-add-tag-token',
                            modal: 'tag-token-add-modal',
                            info_view: 'tag-token-info'
                        },
                        target_types: [{
                            key: 'tag',
                            id_policy: { canonical_pattern: '^[a-z0-9][a-z0-9-]*$' }
                        }]
                    }
                ]
            };
            const targetPayload = {
                schema_version: 'docs_semantic_token_target_lookup_v2',
                targets: [{
                    family: 'tag',
                    target_type: 'tag',
                    target_id: 'nerve',
                    title: 'nerve',
                    href: '/analysis/?doc=report&subdoc=nerve-doc',
                    meta: ['subject', 'Nerve document'],
                    aliases: ['neural', 'nervous-system']
                }]
            };
            const registry = smoke.registry.normalizeSemanticTokenRegistry(registryPayload);
            const normalizedTargets = smoke.semanticTargets.normalizeSemanticTokenTargets(
                targetPayload,
                registry
            );
            const support = smoke.targets.createTagTargetSupport(registry, normalizedTargets);
            const aliasMatches = smoke.targets.collectTagTargetMatches(support, 'neural', 20);
            const exact = smoke.targets.findTagTargetByIdentity(support, {
                family: 'tag', targetType: 'tag', targetId: 'nerve'
            });
            const serialized = smoke.parser.serializeTagToken({
                registry,
                targetId: 'nerve',
                title: 'Nerve | signal'
            });
            const source = [
                'Visible [[tag:tag:nerve|Nerve]].',
                '`[[tag:tag:nerve|inline]]`',
                '<!-- [[tag:tag:nerve|comment]] -->',
                '```',
                '[[tag:tag:nerve|fence]]',
                '```'
            ].join('\n');
            const tokens = smoke.parser.parseTagTokens(source, { registry });
            const token = tokens[0];
            const fakeFetch = async url => ({
                ok: true,
                json: async () => String(url).includes('targets')
                    ? targetPayload
                    : registryPayload
            });
            const resolver = smoke.contribution.createSemanticTokenInfoViewResolver({
                fetch: fakeFetch
            });
            const adapterFor = (value, start, end) => ({
                getBufferSnapshot: () => ({ value, revision: 1 }),
                getSelection: () => ({ start, end })
            });
            const catalogueRaw = '[[catalogue:work:00638|3 symbols]]';
            const views = await Promise.all([
                resolver(adapterFor(token.raw, 5, 5)),
                resolver(adapterFor(catalogueRaw, 5, 5)),
                resolver(adapterFor('ordinary source', 0, 0))
            ]);
            const definition = smoke.contribution.tagTokenControlDefinition();
            const button = smoke.contribution.tagTokenControlRenderer({ document });
            const hosted = smoke.hostedViews.createDocsViewerManagementViewDefinitions();
            return {
                aliasMatches: aliasMatches.map(target => ({
                    id: target.targetId,
                    aliases: target.aliases,
                    meta: target.meta,
                    href: target.href
                })),
                exact: exact && exact.targetId,
                serialized,
                parsed: tokens.map(item => ({
                    id: item.targetId,
                    title: item.title,
                    start: item.start,
                    supported: item.supported
                })),
                atCaret: smoke.parser.tagTokenAtSelection(tokens, {
                    start: token.start + 5,
                    end: token.start + 5
                })?.targetId || '',
                views,
                definition,
                icon: button.textContent,
                actionIds: Object.keys(
                    smoke.contribution.createTagTokenMainViewControlHandlers()
                ),
                hostedInfo: hosted.views.some(view => view.id === 'tag-token-info'),
                hostedControl: hosted.controls.some(control => control.id === 'source-add-tag-token')
            };
        }"""
    )
    expected_target = {
        "id": "nerve",
        "aliases": ["neural", "nervous-system"],
        "meta": ["subject", "Nerve document"],
        "href": "/analysis/?doc=report&subdoc=nerve-doc",
    }
    assert result["aliasMatches"] == [expected_target]
    assert result["exact"] == "nerve"
    assert result["serialized"] == r"[[tag:tag:nerve|Nerve \| signal]]"
    assert result["parsed"] == [
        {"id": "nerve", "title": "Nerve", "start": 8, "supported": True}
    ]
    assert result["atCaret"] == "nerve"
    assert result["views"] == ["tag-token-info", "catalogue-token-info", "metadata-info"]
    assert result["definition"] == {
        "id": "source-add-tag-token",
        "actionId": "source-add-tag-token",
        "label": "Add tag token",
        "ownerType": "view",
        "ownerViewId": "rendered-document",
        "modeIds": ["markdown-source"],
        "surfaceId": "main-view",
        "appKinds": ["manage"],
        "features": ["source-editing"],
        "renderer": "source-add-tag-token",
    }
    assert result["icon"] == "🏷️"
    assert result["actionIds"] == ["source-add-tag-token"]
    assert result["hostedInfo"] is True
    assert result["hostedControl"] is True


def assert_modal_revision_guard_and_occurrence_title(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__tagTokenSmoke;
            const registryPayload = {
                schema_version: 'docs_semantic_token_registry_v1',
                target_lookup_url: '/targets.json',
                families: [{
                    key: 'tag', labels: {}, occurrence_fields: [], ui_contributions: {},
                    target_types: [{
                        key: 'tag',
                        id_policy: { canonical_pattern: '^[a-z0-9][a-z0-9-]*$' }
                    }]
                }]
            };
            const targetPayload = {
                schema_version: 'docs_semantic_token_target_lookup_v2',
                targets: [{
                    family: 'tag', target_type: 'tag', target_id: 'nerve', title: 'nerve',
                    href: '/analysis/?doc=report&subdoc=nerve-doc',
                    meta: ['subject', 'Nerve document'], aliases: ['neural']
                }]
            };
            const fakeFetch = async url => ({
                ok: true,
                json: async () => String(url).includes('targets')
                    ? targetPayload
                    : registryPayload
            });
            async function waitForLoaded(root) {
                for (let index = 0; index < 30; index += 1) {
                    const input = root.querySelector('#docsViewerTagTokenSearch');
                    if (input && !input.disabled) return;
                    await new Promise(resolve => setTimeout(resolve, 0));
                }
                throw new Error('Tag modal did not load targets.');
            }
            async function run(stale) {
                const root = document.createElement('div');
                document.body.appendChild(root);
                const capture = { start: 7, end: 12, text: 'Nerve', revision: 4 };
                const state = { value: 'Before Nerve after', replacements: 0 };
                const promise = smoke.modal.openTagTokenModal({
                    adapter: {
                        focus() {},
                        replaceCapturedSelection(candidate, value) {
                            if (stale) return false;
                            if (JSON.stringify(candidate) !== JSON.stringify(capture)) return false;
                            state.replacements += 1;
                            state.value = state.value.slice(0, candidate.start)
                                + value
                                + state.value.slice(candidate.end);
                            return true;
                        }
                    },
                    capture,
                    fetch: fakeFetch,
                    root
                });
                await waitForLoaded(root);
                const search = root.querySelector('#docsViewerTagTokenSearch');
                search.value = 'neural';
                search.dispatchEvent(new Event('input', { bubbles: true }));
                root.querySelector('[data-target-index="0"]').click();
                const seededTitle = root.querySelector('#docsViewerTagTokenTitle').value;
                root.querySelector('[data-role="modal-primary"]').click();
                await new Promise(resolve => setTimeout(resolve, 0));
                const status = root.querySelector('[data-role="modal-status"]');
                const snapshot = {
                    modalId: root.querySelector('[data-role="docs-viewer-management-modal"]')?.id || '',
                    seededTitle,
                    value: state.value,
                    replacements: state.replacements,
                    status: status && !status.hidden ? status.textContent : ''
                };
                if (stale) {
                    root.querySelector('[data-role="modal-cancel"]').click();
                }
                const settled = await promise;
                root.remove();
                return { snapshot, settled };
            }
            return {
                inserted: await run(false),
                stale: await run(true)
            };
        }"""
    )
    assert result["inserted"] == {
        "snapshot": {
            "modalId": "",
            "seededTitle": "Nerve",
            "value": "Before [[tag:tag:nerve|Nerve]] after",
            "replacements": 1,
            "status": "",
        },
        "settled": {
            "confirmed": True,
            "target": {
                "family": "tag",
                "targetType": "tag",
                "targetId": "nerve",
                "title": "nerve",
                "href": "/analysis/?doc=report&subdoc=nerve-doc",
                "meta": ["subject", "Nerve document"],
                "aliases": ["neural"],
            },
            "title": "Nerve",
            "token": "[[tag:tag:nerve|Nerve]]",
        },
    }
    assert result["stale"]["snapshot"] == {
        "modalId": "tag-token-add-modal",
        "seededTitle": "Nerve",
        "value": "Before Nerve after",
        "replacements": 0,
        "status": "Markdown source changed while this modal was open. Cancel and try again.",
    }
    assert result["stale"]["settled"] == {"confirmed": False}


def assert_info_exact_range_edit_remove_and_stale_error(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__tagTokenSmoke;
            const registryPayload = {
                schema_version: 'docs_semantic_token_registry_v1',
                target_lookup_url: '/targets.json',
                families: [{
                    key: 'tag', labels: {}, occurrence_fields: [], ui_contributions: {},
                    target_types: [{
                        key: 'tag',
                        id_policy: { canonical_pattern: '^[a-z0-9][a-z0-9-]*$' }
                    }]
                }]
            };
            const targetPayload = {
                schema_version: 'docs_semantic_token_target_lookup_v2',
                targets: [{
                    family: 'tag', target_type: 'tag', target_id: 'nerve', title: 'nerve',
                    href: '/analysis/?doc=report&subdoc=nerve-doc',
                    meta: ['subject', 'Nerve document'], aliases: ['neural']
                }]
            };
            const fakeFetch = async url => ({
                ok: true,
                json: async () => String(url).includes('targets')
                    ? targetPayload
                    : registryPayload
            });
            async function run(mode) {
                const root = document.createElement('div');
                document.body.appendChild(root);
                const raw = '[[tag:tag:nerve|Nerve]]';
                const state = {
                    value: 'Before ' + raw + ' after',
                    revision: 3,
                    selection: { start: 7, end: 7 + raw.length }
                };
                const adapter = {
                    getBufferSnapshot: () => ({ value: state.value, revision: state.revision }),
                    getSelection: () => state.selection,
                    onSelectionChange: () => () => {},
                    selectCapturedRange: () => true,
                    replaceCapturedRange(capture, value, selectionMode) {
                        if (mode === 'stale') return false;
                        if (
                            capture.revision !== state.revision
                            || state.value.slice(capture.start, capture.end) !== capture.text
                        ) return false;
                        state.value = state.value.slice(0, capture.start)
                            + value
                            + state.value.slice(capture.end);
                        state.selectionMode = selectionMode;
                        return true;
                    }
                };
                const view = smoke.infoView.createTagTokenInfoView({ fetch: fakeFetch });
                await view.mount({
                    mount: root,
                    sourceEditorServices: {
                        getActiveSourceEditorContextAdapter: () => adapter,
                        publicPreviewBase: 'http://127.0.0.1:4000'
                    }
                });
                const rows = Object.fromEntries(Array.from(
                    root.querySelectorAll('.docsViewer__metadataInfoRow')
                ).map(row => [
                    row.querySelector('dt').textContent,
                    row.querySelector('dd').textContent
                ]));
                if (mode === 'update' || mode === 'stale') {
                    const input = root.querySelector('.docsViewer__fieldInput');
                    input.value = 'Nerve signal';
                    Array.from(root.querySelectorAll('button')).find(
                        button => button.textContent === 'Update token'
                    ).click();
                } else {
                    Array.from(root.querySelectorAll('button')).find(
                        button => button.textContent === 'Remove token'
                    ).click();
                }
                const status = root.querySelector('.docsViewer__metadataInfoEmpty');
                const destinationLink = root.querySelector('.docsViewer__metadataInfoRow a');
                const rendered = document.createElement('div');
                rendered.innerHTML = [
                    '<a href="/analysis/?doc=report&amp;subdoc=nerve-doc"',
                    ' data-semantic-token-family="tag"',
                    ' data-semantic-token-target-type="tag"',
                    ' data-semantic-token-target-id="nerve">Nerve</a>'
                ].join('');
                const snapshot = {
                    destinationHref: destinationLink && destinationLink.getAttribute('href'),
                    rows,
                    value: state.value,
                    selectionMode: state.selectionMode || '',
                    error: status && !status.hidden ? status.textContent : '',
                    renderedHref: rendered.querySelector('a').getAttribute('href'),
                    renderedMountCount: smoke.semanticTargets.mountSemanticTokenTargetLinks(
                        rendered,
                        'http://127.0.0.1:4000'
                    )
                };
                view.dispose({ mount: root });
                root.remove();
                return snapshot;
            }
            return {
                updated: await run('update'),
                removed: await run('remove'),
                stale: await run('stale')
            };
        }"""
    )
    expected_rows = {
        "Family": "Tag",
        "Target ID": "nerve",
        "Aliases": "neural",
        "Group": "subject",
        "Resolved document": "Nerve document",
        "Destination": "/analysis/?doc=report&subdoc=nerve-doc",
    }
    assert result["updated"] == {
        "destinationHref": "/analysis/?doc=report&subdoc=nerve-doc",
        "rows": expected_rows,
        "value": "Before [[tag:tag:nerve|Nerve signal]] after",
        "selectionMode": "select",
        "error": "",
        "renderedHref": "/analysis/?doc=report&subdoc=nerve-doc",
        "renderedMountCount": 0,
    }
    assert result["removed"] == {
        "destinationHref": "/analysis/?doc=report&subdoc=nerve-doc",
        "rows": expected_rows,
        "value": "Before  after",
        "selectionMode": "end",
        "error": "",
        "renderedHref": "/analysis/?doc=report&subdoc=nerve-doc",
        "renderedMountCount": 0,
    }
    assert result["stale"] == {
        "destinationHref": "/analysis/?doc=report&subdoc=nerve-doc",
        "rows": expected_rows,
        "value": "Before [[tag:tag:nerve|Nerve]] after",
        "selectionMode": "",
        "error": "Markdown source changed. Select the token again.",
        "renderedHref": "/analysis/?doc=report&subdoc=nerve-doc",
        "renderedMountCount": 0,
    }


def assert_semantic_report_accepts_tag_occurrences(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const root = document.createElement('div');
            document.body.appendChild(root);
            await window.__tagTokenSmoke.report.mountSemanticTokensReport({
                reportRoot: root,
                reportMeta: { scope: 'analysis' },
                scopeConfigs: [{ scope_id: 'analysis', title: 'Analysis' }],
                viewerScope: 'analysis',
                viewerUrlForScope: (scope, docId) => (
                    '/docs/?scope=' + scope + '&doc=' + docId
                ),
                fetchDocsIndexTree: () => Promise.resolve({
                    docs: [{ doc_id: 'source', title: 'Source document' }]
                }),
                reportService: {
                    readSemanticTokens: () => Promise.resolve({
                        occurrences: [
                            {
                                family: 'catalogue', target_type: 'work', target_id: '00638',
                                title: '3 symbols', source_doc_id: 'source'
                            },
                            {
                                family: 'tag', target_type: 'tag', target_id: 'nerve',
                                title: 'Nerve', source_doc_id: 'source'
                            }
                        ]
                    })
                }
            });
            const snapshot = {
                status: root.querySelector('.docsViewerReport__status').textContent,
                identities: Array.from(
                    root.querySelectorAll('.docsViewerReport__cellMeta')
                ).map(node => node.textContent).sort(),
                documents: Array.from(
                    root.querySelectorAll('.docsViewerReport__cellLink')
                ).map(node => ({ text: node.textContent, href: node.getAttribute('href') }))
            };
            root.remove();
            return snapshot;
        }"""
    )
    assert result == {
        "status": "2 semantic tokens",
        "identities": ["catalogue:work:00638", "tag:tag:nerve"],
        "documents": [
            {"text": "Source document", "href": "/docs/?scope=analysis&doc=source"},
            {"text": "Source document", "href": "/docs/?scope=analysis&doc=source"},
        ],
    }


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="domcontentloaded")
    install_modules(page)
    assert_registry_parser_discovery_and_wiring(page)
    assert_modal_revision_guard_and_occurrence_title(page)
    assert_info_exact_range_edit_remove_and_stale_error(page)
    assert_semantic_report_accepts_tag_occurrences(page)


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
        raise AssertionError(f"page errors during Tag token module smoke: {errors!r}")
    print("Docs Viewer Tag token modules OK")


if __name__ == "__main__":
    main()

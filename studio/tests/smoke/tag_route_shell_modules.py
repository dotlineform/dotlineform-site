#!/usr/bin/env python3
"""Smoke-check Studio Tag route shell JavaScript helpers."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
from threading import Thread
from urllib.parse import unquote, urlsplit

from playwright.sync_api import Page, sync_playwright


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        request_path = unquote(urlsplit(path).path)
        if request_path.startswith("/assets/"):
            relative = f"site/assets/{request_path.removeprefix('/assets/')}"
            return str(Path(self.directory) / relative)
        if request_path.startswith("/studio/app/"):
            relative = f"studio/app/{request_path.removeprefix('/studio/app/')}"
            return str(Path(self.directory) / relative)
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


def assert_tag_save_session_helpers(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/studio/app/frontend/js/tag-route-save-session.js');
            const state = {
                saveMode: 'patch',
                isBusy: false
            };
            const routeChanges = [];
            const availableProbe = await module.probeTagRouteSaveMode(state, {
                healthProbe: async () => true,
                onSaveModeChange: (detail) => routeChanges.push(['save', detail.service]),
                onRouteStateChange: (detail) => routeChanges.push(['route', detail.saveMode])
            });
            const serviceAfterProbe = module.tagRouteServiceState(state);
            const fallback = module.applyTagRoutePatchFallback(state);
            const busyStates = [];
            await module.withTagRouteBusy(state, async () => {
                busyStates.push(`inside:${state.isBusy}`);
            }, {
                syncRouteBusyState: (busyState) => busyStates.push(`sync:${busyState.isBusy}`)
            });
            const fakeWindow = new EventTarget();
            const fakeDocument = new EventTarget();
            fakeDocument.visibilityState = 'visible';
            let reprobeCount = 0;
            const cleanup = module.bindTagSaveModeReprobe(() => {
                reprobeCount += 1;
            }, {
                windowObject: fakeWindow,
                documentObject: fakeDocument
            });
            fakeWindow.dispatchEvent(new Event('focus'));
            fakeWindow.dispatchEvent(new Event('pageshow'));
            fakeDocument.dispatchEvent(new Event('visibilitychange'));
            fakeDocument.visibilityState = 'hidden';
            fakeWindow.dispatchEvent(new Event('focus'));
            cleanup();
            fakeDocument.visibilityState = 'visible';
            fakeWindow.dispatchEvent(new Event('focus'));
            const patchPresentation = module.projectTagPatchFallbackResult({
                switchToPatch: true,
                message: 'Server unavailable.',
                patchResult: {
                    kind: 'warn',
                    message: 'Copy this patch.',
                    snippet: 'diff --git a/file b/file'
                }
            });
            await Promise.all([
                import('/studio/app/frontend/js/analytics-tag-editor.js'),
                import('/studio/app/frontend/js/tag-registry.js'),
                import('/studio/app/frontend/js/tag-aliases.js'),
                import('/studio/app/frontend/js/tag-registry-workflow.js'),
                import('/studio/app/frontend/js/tag-aliases-workflow.js')
            ]);
            return {
                availableProbe,
                serviceAfterProbe,
                fallback,
                routeChanges,
                busyStates,
                reprobeCount,
                patchPresentation,
                routeImports: true
            };
        }"""
    )
    assert result["availableProbe"] == {
        "ok": True,
        "saveMode": "post",
        "service": "available",
    }
    assert result["serviceAfterProbe"] == "available"
    assert result["fallback"] == {
        "saveMode": "patch",
        "service": "unavailable",
    }
    assert result["routeChanges"] == [["save", "available"], ["route", "post"]]
    assert result["busyStates"] == ["sync:true", "inside:true", "sync:false"]
    assert result["reprobeCount"] == 3
    assert result["patchPresentation"] == {
        "switchedToPatch": True,
        "switchMessage": "Server unavailable.",
        "kind": "warn",
        "message": "Copy this patch.",
        "snippet": "diff --git a/file b/file",
    }
    assert result["routeImports"] is True


def assert_tag_delete_document_blockers(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const modals = await import(
                '/studio/app/frontend/js/tag-registry-modals.js'
            );
            document.body.innerHTML = '<main id="tag-delete-smoke"></main>';
            const root = document.getElementById('tag-delete-smoke');
            const state = {
                config: null,
                saveMode: 'post',
                refs: null,
                deleteModalFocusReady: false,
                deleteModalRestoreFocus: null,
                deletePreview: '',
                deletePreviewSeq: 0,
                deleteTagId: ''
            };
            root.innerHTML = modals.renderTagRegistryModals(state);
            state.refs = modals.collectTagRegistryModalRefs(root);
            modals.openTagRegistryDeleteModal(state, {
                tagId: 'trees',
                group: 'subject'
            });
            const waitingDisabled = state.refs.confirmDeleteTag.disabled;
            modals.renderTagRegistryDeleteImpactPreview(state, {
                response: {
                    blocked: true,
                    document_associations: [{
                        target: {
                            scope: 'analysis',
                            sub_scope: 'tags',
                            doc_id: 'd-20260811-000001-000001'
                        },
                        title: 'Trees overview',
                        url: '/docs/?scope=analysis&doc=d-20260430-230000-000099&subdoc=d-20260811-000001-000001'
                    }]
                },
                affectedSeries: []
            });
            const blocked = {
                disabled: state.refs.confirmDeleteTag.disabled,
                impact: state.refs.deleteImpact.textContent.replace(/\\s+/g, ' ').trim(),
                status: state.refs.deleteStatus.textContent.trim(),
                href: state.refs.deleteImpact.querySelector('a').getAttribute('href')
            };
            modals.closeTagRegistryDeleteModal(state);
            modals.openTagRegistryDeleteModal(state, {
                tagId: 'growth',
                group: 'theme'
            });
            modals.renderTagRegistryDeleteImpactPreview(state, {
                response: {
                    blocked: false,
                    document_associations: []
                },
                affectedSeries: []
            });
            return {
                waitingDisabled,
                blocked,
                unblockedDisabled: state.refs.confirmDeleteTag.disabled
            };
        }"""
    )
    assert result["waitingDisabled"] is True
    assert result["blocked"]["disabled"] is True
    assert "associated documents: Trees overview — d-20260811-000001-000001" in (
        result["blocked"]["impact"]
    )
    assert result["blocked"]["status"] == (
        "Edit or delete the associated documents before deleting this Tag."
    )
    assert result["blocked"]["href"] == (
        "/docs/?scope=analysis&doc=d-20260430-230000-000099"
        "&subdoc=d-20260811-000001-000001"
    )
    assert result["unblockedDisabled"] is False


def assert_document_location_provider_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/shared/frontend/js/document-location-provider.js');
            const actualProvider = module.createDocumentLocationProvider();
            const actualAnalysis = await actualProvider.load({ scopeIds: ['analysis'] });
            const calls = [];
            const payload = {
                schema_version: 'docs_document_locations_v1',
                scope_id: 'analysis',
                records: [
                    {
                        url: '/analysis/?doc=d-20260624-213316-478639&subdoc=d-20260727-225608-63967a',
                        scope_id: 'analysis',
                        document_title: 'bird-nerve',
                        report_title: 'All Tags'
                    },
                    {
                        url: '/analysis/?doc=d-20260729-111111-abcdef&subdoc=d-20260727-225608-63967a',
                        scope_id: 'analysis',
                        document_title: 'bird-nerve',
                        report_title: 'Made-up Tags'
                    },
                    {
                        url: '/analysis/?doc=d-20260426-164043-e14f49',
                        scope_id: 'analysis',
                        document_title: 'Analysis',
                        report_title: ''
                    },
                    {
                        url: '/analysis/?doc=d-20260729-121212-fedcba',
                        scope_id: 'analysis',
                        document_title: 'Small bird study',
                        report_title: ''
                    }
                ]
            };
            const provider = module.createDocumentLocationProvider({
                fetchJson: async (url) => {
                    calls.push(url);
                    return payload;
                }
            });
            const exact = await provider.search({
                scopeIds: ['analysis'],
                query: 'bird-nerve'
            });
            const excluded = await provider.search({
                scopeIds: ['analysis'],
                query: 'bird',
                excludedUrls: [payload.records[0].url]
            });
            const resolved = await provider.resolve({
                scopeIds: ['analysis'],
                urls: [
                    payload.records[0].url,
                    '/analysis/?doc=d-20260729-131313-a1b2c3',
                    '/docs/?scope=studio&doc=d-20260729-141414-b1c2d3'
                ]
            });
            let emptyError = '';
            let unsupportedError = '';
            let invalidCommitError = '';
            try {
                await provider.load({ scopeIds: [] });
            } catch (error) {
                emptyError = error.message;
            }
            try {
                await provider.load({ scopeIds: ['library'] });
            } catch (error) {
                unsupportedError = error.message;
            }
            try {
                module.committedDocumentLocation({
                    url: 'https://example.test/document',
                    scope_id: 'analysis',
                    document_title: 'External',
                    report_title: ''
                });
            } catch (error) {
                invalidCommitError = error.message;
            }
            return {
                actual: {
                    analysisCount: actualAnalysis.length,
                    analysisScopes: [...new Set(actualAnalysis.map((record) => record.scope_id))],
                    analysisReports: actualAnalysis.filter((record) => record.report_title).length
                },
                calls,
                exact: exact.map((record) => [record.document_title, record.report_title]),
                excluded: excluded.map((record) => [record.document_title, record.report_title]),
                resolved: resolved.map((record) => ({
                    url: record.url,
                    scope: record.scope_id,
                    title: record.document_title,
                    available: record.available
                })),
                emptyError,
                unsupportedError,
                invalidCommitError
            };
        }"""
    )
    assert result["actual"]["analysisCount"] >= 2
    assert result["actual"]["analysisScopes"] == ["analysis"]
    assert result["actual"]["analysisReports"] >= 1
    assert result["calls"] == [
        "/assets/data/search/analysis/document-locations.json"
    ]
    assert result["exact"] == [
        ["bird-nerve", "All Tags"],
        ["bird-nerve", "Made-up Tags"],
    ]
    assert result["excluded"] == [
        ["bird-nerve", "Made-up Tags"],
        ["Small bird study", ""],
    ]
    assert result["resolved"][0]["available"] is True
    assert result["resolved"][1] == {
        "url": "/analysis/?doc=d-20260729-131313-a1b2c3",
        "scope": "analysis",
        "title": "Unavailable document",
        "available": False,
    }
    assert result["resolved"][2] == {
        "url": "/docs/?scope=studio&doc=d-20260729-141414-b1c2d3",
        "scope": "studio",
        "title": "Unavailable document",
        "available": False,
    }
    assert "non-empty scopeIds" in result["emptyError"]
    assert "unsupported document-location scope: library" in result["unsupportedError"]
    assert result["invalidCommitError"] == "document location commit record is invalid"


def assert_document_location_picker_interactions(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <label>
                Document
                <span class="sharedSearchList__control">
                  <input id="locationInput">
                  <span id="locationPopup"></span>
                </span>
              </label>
            `;
            const providerModule = await import('/shared/frontend/js/document-location-provider.js');
            const pickerModule = await import('/shared/frontend/js/document-location-picker.js');
            const resetPickerDom = () => {
                document.body.innerHTML = `
                  <label>
                    Document
                    <span class="sharedSearchList__control">
                      <input id="locationInput">
                      <span id="locationPopup"></span>
                    </span>
                  </label>
                `;
                return {
                    input: document.getElementById('locationInput'),
                    popup: document.getElementById('locationPopup')
                };
            };
            let input = document.getElementById('locationInput');
            let popup = document.getElementById('locationPopup');
            const commits = [];
            const records = [
                {
                    url: '/analysis/?doc=d-20260624-213316-478639&subdoc=d-20260727-225608-63967a',
                    scope_id: 'analysis',
                    document_title: 'bird-nerve',
                    report_title: 'All Tags',
                    available: true
                },
                {
                    url: '/analysis/?doc=d-20260729-111111-abcdef&subdoc=d-20260727-225608-63967a',
                    scope_id: 'analysis',
                    document_title: 'bird-nerve',
                    report_title: 'Made-up Tags',
                    available: true
                }
            ];
            let picker = pickerModule.bindDocumentLocationPicker(input, popup, {
                scopeIds: ['analysis'],
                excludedUrls: () => [records[0].url],
                provider: {
                    search: async ({ query, excludedUrls }) => (
                        providerModule.searchDocumentLocationRecords(records, query, excludedUrls)
                    )
                },
                onCommit: (record) => commits.push(record)
            });
            input.value = 'bird';
            await picker.refresh();
            const singleScope = {
                buttonCount: popup.querySelectorAll('button').length,
                text: popup.textContent
            };
            input.dispatchEvent(new KeyboardEvent('keydown', {
                key: 'Enter',
                bubbles: true,
                cancelable: true
            }));
            await new Promise((resolve) => setTimeout(resolve, 0));
            const keyboardCommit = commits[0] || null;

            picker.destroy();
            ({ input, popup } = resetPickerDom());
            input.value = 'planning';
            const pointerRecord = {
                url: '/analysis/?doc=d-20260507-172400-74807b',
                scope_id: 'analysis',
                document_title: 'Planning',
                report_title: ''
            };
            picker = pickerModule.bindDocumentLocationPicker(input, popup, {
                scopeIds: ['analysis'],
                provider: { search: async () => [pointerRecord] },
                onCommit: (record) => commits.push(record)
            });
            await picker.refresh();
            const pointerOptions = {
                buttonCount: popup.querySelectorAll('button').length,
                text: popup.textContent
            };
            popup.querySelector('button').click();
            await new Promise((resolve) => setTimeout(resolve, 0));
            const pointerCommit = commits[1] || null;

            picker.destroy();
            ({ input, popup } = resetPickerDom());
            input.value = 'none';
            picker = pickerModule.bindDocumentLocationPicker(input, popup, {
                scopeIds: ['analysis'],
                provider: {
                    search: async ({ query }) => {
                        if (query === 'fail') throw new Error('Projection unavailable.');
                        return [];
                    }
                }
            });
            await picker.refresh();
            const emptyText = popup.textContent;
            input.value = 'fail';
            await picker.refresh();
            const failureText = popup.textContent;

            picker.destroy();
            ({ input, popup } = resetPickerDom());
            input.value = '';
            const pendingCommits = [];
            picker = pickerModule.bindDocumentLocationPicker(input, popup, {
                scopeIds: ['analysis'],
                provider: {
                    search: ({ query }) => new Promise((resolve) => {
                        const delay = query === 'slow' ? 80 : 0;
                        setTimeout(() => resolve([{
                            url: '/analysis/?doc=d-20260426-164043-e14f49',
                            scope_id: 'analysis',
                            document_title: query || 'empty',
                            report_title: ''
                        }]), delay);
                    })
                },
                onCommit: (record) => pendingCommits.push(record)
            });
            input.value = 'prior';
            await picker.refresh();
            input.value = 'slow';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new KeyboardEvent('keydown', {
                key: 'Enter',
                bubbles: true,
                cancelable: true
            }));
            input.value = 'fast';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            await new Promise((resolve) => setTimeout(resolve, 120));
            const asyncText = popup.textContent;
            picker.destroy();

            ({ input, popup } = resetPickerDom());
            input.closest('label').after(popup);
            input.value = 'bird';
            const persistentCommits = [];
            picker = pickerModule.bindDocumentLocationPicker(input, popup, {
                scopeIds: ['analysis'],
                maxOptions: 50,
                persistent: true,
                showReport: false,
                provider: { search: async () => records },
                onCommit: (record) => persistentCommits.push(record)
            });
            await picker.refresh();
            popup.querySelector('button').click();
            await new Promise((resolve) => setTimeout(resolve, 0));
            const persistent = {
                commitCount: persistentCommits.length,
                hidden: popup.hidden,
                reportContextAbsent: !popup.textContent.includes('All Tags')
                    && !popup.textContent.includes('Made-up Tags'),
                titleCount: popup.querySelectorAll(
                    '.sharedDocumentLocationPicker__title'
                ).length,
                selectedCount: popup.querySelectorAll('[aria-selected="true"]').length
            };
            picker.destroy();
            return {
                singleScope,
                keyboardCommit,
                pointerOptions,
                pointerCommit,
                emptyText,
                failureText,
                asyncText,
                pendingCommitCount: pendingCommits.length,
                persistent
            };
        }"""
    )
    assert result["singleScope"]["buttonCount"] == 1
    assert "Made-up Tags" in result["singleScope"]["text"]
    assert "Analysis" not in result["singleScope"]["text"]
    assert result["keyboardCommit"] == {
        "url": (
            "/analysis/?doc=d-20260729-111111-abcdef"
            "&subdoc=d-20260727-225608-63967a"
        ),
        "scope_id": "analysis",
        "document_title": "bird-nerve",
        "report_title": "Made-up Tags",
    }
    assert result["pointerOptions"]["buttonCount"] == 1
    assert "Planning" in result["pointerOptions"]["text"]
    assert result["pointerCommit"]["scope_id"] == "analysis"
    assert "No matching documents." in result["emptyText"]
    assert "Projection unavailable." in result["failureText"]
    assert "fast" in result["asyncText"]
    assert "slow" not in result["asyncText"]
    assert result["pendingCommitCount"] == 0
    assert result["persistent"] == {
        "commitCount": 1,
        "hidden": False,
        "reportContextAbsent": True,
        "titleCount": 2,
        "selectedCount": 1,
    }


def assert_tag_registry_document_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const documents = await import('/studio/app/frontend/js/tag-registry-documents.js');
            const domain = await import('/studio/app/frontend/js/tag-registry-domain.js');
            const render = await import('/studio/app/frontend/js/tag-registry-render.js');
            const modals = await import('/studio/app/frontend/js/tag-registry-modals.js');
            const modalWorkflow = await import(
                '/studio/app/frontend/js/tag-registry-modal-workflow.js'
            );
            const firstUrl =
                '/analysis/?doc=d-20260624-213316-478639'
                + '&subdoc=d-20260727-225608-63967a';
            const secondUrl =
                '/analysis/?doc=d-20260729-111111-abcdef'
                + '&subdoc=d-20260727-225608-63967a';
            const staleUrl = '/analysis/?doc=d-20260729-131313-a1b2c3';
            const unsupportedUrl = '/docs/?scope=studio&doc=d-20260507-172400-74807b';
            const firstRecord = {
                url: firstUrl,
                scope_id: 'analysis',
                document_title: 'bird-nerve',
                report_title: 'All Tags',
                available: true
            };
            const secondRecord = {
                url: secondUrl,
                scope_id: 'analysis',
                document_title: 'bird-nerve',
                report_title: 'Made-up Tags',
                available: true
            };
            const sourceTags = domain.normalizeRegistryTags({
                tag_registry_version: 'tag_registry_v5',
                tags: [
                    {
                        tag_id: 'bird',
                        group: 'subject',
                        doc_url: [firstUrl, secondUrl, staleUrl],
                        updated_at_utc: '2026-07-29T12:00:00Z'
                    },
                    {
                        tag_id: 'empty',
                        group: 'theme',
                        doc_url: [],
                        updated_at_utc: '2026-07-29T11:00:00Z'
                    }
                ]
            }, '');
            const loaded = await documents.loadTagRegistryDocumentLocations(
                sourceTags,
                {
                    provider: {
                        resolve: async ({ scopeIds, urls }) => {
                            if (scopeIds.join(',') !== 'analysis') {
                                throw new Error('unexpected scopes');
                            }
                            return urls.map((url) => {
                                if (url === firstUrl) return firstRecord;
                                if (url === secondUrl) return secondRecord;
                                return documents.unavailableTagRegistryDocument(url);
                            });
                        }
                    }
                }
            );
            const attached = documents.attachTagRegistryDocuments(
                sourceTags,
                loaded.locationsByUrl
            );
            const failed = await documents.loadTagRegistryDocumentLocations(
                sourceTags,
                {
                    provider: {
                        resolve: async () => {
                            throw new Error('Projection unavailable.');
                        }
                    }
                }
            );
            const added = documents.appendTagRegistryDocumentUrl(
                [firstUrl],
                secondRecord
            );
            const duplicate = documents.appendTagRegistryDocumentUrl(
                added,
                secondRecord
            );
            const removed = documents.removeTagRegistryDocumentUrl(
                duplicate,
                firstUrl
            );
            let unsupportedScopeError = '';
            try {
                documents.appendTagRegistryDocumentUrl(
                    removed,
                    {
                        url: unsupportedUrl,
                        scope_id: 'studio',
                        document_title: 'Planning',
                        report_title: ''
                    }
                );
            } catch (error) {
                unsupportedScopeError = error.message;
            }

            document.body.innerHTML = '<div id="list"></div><div id="modals"></div>';
            const list = document.getElementById('list');
            const renderState = {
                config: {
                    app: {
                        runtime: {
                            sites: {
                                public_preview: {
                                    base: 'http://127.0.0.1:4000'
                                }
                            }
                        }
                    }
                },
                tags: attached,
                filterGroup: 'all',
                searchQuery: '',
                sortKey: 'tag',
                sortDir: 'asc',
                refs: { list }
            };
            render.renderTagRegistryList(renderState);
            const table = {
                heading: list.querySelector('[data-sort-key="documents"]').textContent.trim(),
                links: [...list.querySelectorAll('a')].map((link) => ({
                    text: link.textContent.trim(),
                    href: link.getAttribute('href')
                })),
                text: list.textContent,
                textareaCount: list.querySelectorAll('textarea').length
            };

            const modalRoot = document.getElementById('modals');
            const modalState = {
                config: renderState.config,
                studioGroups: ['subject', 'domain', 'form', 'theme'],
                groupDescriptions: new Map(),
                saveMode: 'post',
                editTagId: '',
                editTagGroup: '',
                editTagDocUrls: [],
                editTagPendingDocument: null,
                editModalRestoreFocus: null,
                documentLocationsByUrl: loaded.locationsByUrl,
                documentPicker: { close: () => {} },
                tags: attached,
                registryOptions: [],
                registryUpdatedAt: '2026-07-29T12:00:00Z',
                refs: {}
            };
            modalRoot.innerHTML = modals.renderTagRegistryModals(modalState);
            modalState.refs = modals.collectTagRegistryModalRefs(modalRoot);
            modals.openTagRegistryEditModal(modalState, attached[0]);
            const beforeCancel = {
                links: [...modalState.refs.editDocumentList.querySelectorAll('a')].map(
                    (link) => ({
                        text: link.textContent.trim(),
                        href: link.getAttribute('href')
                    })
                ),
                directRemoveCount: modalState.refs.editDocumentList.querySelectorAll(
                    '[data-remove-edit-document-url]'
                ).length,
                textareaCount: modalState.refs.editModal.querySelectorAll('textarea').length,
                addDisabled: modalState.refs.addEditDocument.disabled
            };
            modalState.editTagDocUrls = documents.removeTagRegistryDocumentUrl(
                modalState.editTagDocUrls,
                secondUrl
            );
            modals.renderTagRegistryEditDocuments(modalState);
            const afterRemove = modalState.editTagDocUrls.slice();
            modals.closeTagRegistryEditModal(modalState);
            const cancelled = {
                tagId: modalState.editTagId,
                group: modalState.editTagGroup,
                urls: modalState.editTagDocUrls,
                pickerHidden: modalState.refs.editDocumentPicker.hidden
            };

            modals.openTagRegistryEditModal(modalState, attached[0]);
            const routeResults = [];
            modalWorkflow.applyTagRegistryEditResult(modalState, {
                tagId: attached[0].tagId,
                group: attached[0].group,
                docUrl: afterRemove,
                result: {
                    message: 'Saved.',
                    summary: 'verbose backend audit summary',
                    response: {
                        doc_url: afterRemove,
                        updated_at_utc: '2026-07-29T13:00:00Z'
                    }
                }
            }, {
                setRouteResult: (...args) => routeResults.push(args),
                renderControls: () => {},
                renderList: () => {},
                syncRouteBusyState: () => {}
            });
            const successfulEdit = {
                modalHidden: modalState.refs.editModal.hidden,
                projectedUrls: modalState.tags
                    .find((tag) => tag.tagId === attached[0].tagId)
                    .docUrl,
                routeResults
            };

            return {
                resolvedTitles: attached[0].documents.map((record) => record.document_title),
                resolvedUrls: attached[0].documents.map((record) => record.url),
                failed: {
                    error: failed.error,
                    titles: failed.records.map((record) => record.document_title)
                },
                added,
                duplicate,
                removed,
                unsupportedScopeError,
                documentSort: domain.compareTags(attached[0], attached[1], 'documents'),
                table,
                beforeCancel,
                afterRemove,
                cancelled,
                successfulEdit
            };
        }"""
    )
    assert result["resolvedTitles"] == [
        "bird-nerve",
        "bird-nerve",
        "Unavailable document",
    ]
    assert result["resolvedUrls"] == [
        (
            "/analysis/?doc=d-20260624-213316-478639"
            "&subdoc=d-20260727-225608-63967a"
        ),
        (
            "/analysis/?doc=d-20260729-111111-abcdef"
            "&subdoc=d-20260727-225608-63967a"
        ),
        "/analysis/?doc=d-20260729-131313-a1b2c3",
    ]
    assert result["failed"]["error"] == "Projection unavailable."
    assert result["failed"]["titles"] == [
        "Unavailable document",
        "Unavailable document",
        "Unavailable document",
    ]
    assert result["added"] == result["duplicate"]
    assert result["removed"] == [
        (
            "/analysis/?doc=d-20260729-111111-abcdef"
            "&subdoc=d-20260727-225608-63967a"
        )
    ]
    assert result["unsupportedScopeError"] == (
        "document location commit record is invalid"
    )
    assert result["documentSort"] > 0
    assert result["table"]["heading"].startswith("documents")
    assert result["table"]["links"] == result["beforeCancel"]["links"]
    assert result["table"]["links"][0]["text"] == "bird-nerve"
    assert result["table"]["links"][1]["text"] == "bird-nerve"
    assert result["table"]["links"][2] == {
        "text": "Unavailable document",
        "href": (
            "http://127.0.0.1:4000/"
            "analysis/?doc=d-20260729-131313-a1b2c3"
        ),
    }
    assert all(
        link["href"].startswith("http://127.0.0.1:4000/analysis/")
        for link in result["table"]["links"]
    )
    assert "—" in result["table"]["text"]
    assert result["table"]["textareaCount"] == 0
    assert result["beforeCancel"]["directRemoveCount"] == 3
    assert result["beforeCancel"]["textareaCount"] == 0
    assert result["beforeCancel"]["addDisabled"] is True
    assert len(result["afterRemove"]) == 2
    assert result["cancelled"] == {
        "tagId": "",
        "group": "",
        "urls": [],
        "pickerHidden": False,
    }
    assert result["successfulEdit"] == {
        "modalHidden": True,
        "projectedUrls": result["afterRemove"],
        "routeResults": [],
    }


def assert_tag_registry_edit_request(page: Page, base_url: str) -> None:
    captured: list[dict[str, object]] = []
    endpoint = f"{base_url}/studio/api/tags/mutate-tag"

    def handle_edit(route) -> None:
        payload = route.request.post_data_json
        captured.append(
            {
                "method": route.request.method,
                "payload": payload,
            }
        )
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "ok": True,
                    "action": "edit",
                    "old_tag_id": "trees",
                    "new_tag_id": "trees",
                    "doc_url": payload["doc_url"],
                    "group_changed": False,
                    "doc_url_changed": True,
                    "document_urls_added": 1,
                    "document_urls_removed": 0,
                    "updated_at_utc": "2026-07-29T12:00:00Z",
                    "summary_text": "saved complete document-link draft",
                }
            ),
        )

    page.route(endpoint, handle_edit)
    result = page.evaluate(
        """async (editEndpoint) => {
            const service = await import('/studio/app/frontend/js/tag-registry-service.js');
            const firstUrl = '/analysis/?doc=d-20260729-111111-abcdef';
            const secondUrl = '/analysis/?doc=d-20260729-121212-fedcba';
            const tag = {
                tagId: 'trees',
                group: 'subject',
                docUrl: [firstUrl]
            };
            const config = {
                app: {
                    runtime: {
                        services: {
                            tags: {
                                mutate_tag: editEndpoint
                            }
                        }
                    }
                }
            };
            const unchanged = await service.submitTagEdit({
                saveMode: 'post',
                tag,
                group: 'subject',
                docUrl: [firstUrl],
                config
            });
            const saved = await service.submitTagEdit({
                saveMode: 'post',
                tag,
                group: 'subject',
                docUrl: [firstUrl, secondUrl],
                config
            });
            const reordered = await service.submitTagEdit({
                saveMode: 'post',
                tag: {
                    ...tag,
                    docUrl: [firstUrl, secondUrl]
                },
                group: 'subject',
                docUrl: [secondUrl, firstUrl],
                config
            });
            return { unchanged, saved, reordered };
        }""",
        endpoint,
    )
    page.unroute(endpoint, handle_edit)

    assert result["unchanged"]["code"] == "no_changes"
    assert result["saved"]["ok"] is True
    assert result["saved"]["response"]["doc_url"] == [
        "/analysis/?doc=d-20260729-111111-abcdef",
        "/analysis/?doc=d-20260729-121212-fedcba",
    ]
    assert result["reordered"]["ok"] is True
    assert len(captured) == 2
    assert all(item["method"] == "POST" for item in captured)
    first_payload = captured[0]["payload"]
    assert isinstance(first_payload, dict)
    assert first_payload["action"] == "edit"
    assert first_payload["tag_id"] == "trees"
    assert first_payload["new_group"] == "subject"
    assert first_payload["doc_url"] == [
        "/analysis/?doc=d-20260729-111111-abcdef",
        "/analysis/?doc=d-20260729-121212-fedcba",
    ]
    assert "description" not in first_payload
    assert set(first_payload) == {
        "action",
        "tag_id",
        "new_group",
        "doc_url",
        "allow_canonical_rename",
        "client_time_utc",
        "activity_context",
    }
    assert captured[1]["payload"]["doc_url"] == [
        "/analysis/?doc=d-20260729-121212-fedcba",
        "/analysis/?doc=d-20260729-111111-abcdef",
    ]


def assert_tag_registry_create_request(page: Page, base_url: str) -> None:
    captured: dict[str, object] = {}
    endpoint = f"{base_url}/studio/api/tags/create-tag"

    def handle_create(route) -> None:
        captured["method"] = route.request.method
        captured["payload"] = route.request.post_data_json
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "ok": True,
                    "action": "create",
                    "tag_id": "renewal",
                    "group": "theme",
                    "doc_url": [],
                    "added": 1,
                    "final_total": 2,
                    "updated_at_utc": "2026-07-27T12:00:00Z",
                    "summary_text": (
                        "created tag renewal; no document association; final 2"
                    ),
                }
            ),
        )

    page.route(endpoint, handle_create)
    result = page.evaluate(
        """async (createEndpoint) => {
            const service = await import('/studio/app/frontend/js/tag-registry-service.js');
            return service.submitCreateTag({
                saveMode: 'post',
                newTagRow: {
                    tag_id: 'renewal',
                    group: 'theme'
                },
                config: {
                    app: {
                        runtime: {
                            services: {
                                tags: {
                                    create_tag: createEndpoint
                                }
                            }
                        }
                    }
                }
            });
        }""",
        endpoint,
    )
    page.unroute(endpoint, handle_create)

    assert result["ok"] is True
    assert result["mode"] == "post"
    assert result["summary"] == (
        "created tag renewal; no document association; final 2"
    )
    assert captured["method"] == "POST"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["group"] == "theme"
    assert payload["tag_id"] == "renewal"
    assert set(payload) == {"group", "tag_id", "client_time_utc", "activity_context"}
    context = payload["activity_context"]
    assert isinstance(context, dict)
    assert context["action_id"] == "create-tag"
    assert context["tag_id"] == "renewal"

    def reject_create(route) -> None:
        route.fulfill(
            status=400,
            content_type="application/json",
            body=json.dumps({"ok": False, "error": "tag_id already exists: renewal"}),
        )

    page.route(endpoint, reject_create)
    rejected = page.evaluate(
        """async (createEndpoint) => {
            const service = await import('/studio/app/frontend/js/tag-registry-service.js');
            return service.submitCreateTag({
                saveMode: 'post',
                newTagRow: {
                    tag_id: 'renewal',
                    group: 'theme'
                },
                config: {
                    app: {
                        runtime: {
                            services: {
                                tags: {
                                    create_tag: createEndpoint
                                }
                            }
                        }
                    }
                }
            });
        }""",
        endpoint,
    )
    page.unroute(endpoint, reject_create)
    assert rejected == {
        "ok": False,
        "mode": "post",
        "switchToPatch": False,
        "message": "tag_id already exists: renewal",
    }

    unavailable = page.evaluate(
        """async () => {
            const service = await import('/studio/app/frontend/js/tag-registry-service.js');
            return service.submitCreateTag({
                saveMode: 'post',
                newTagRow: {
                    tag_id: 'renewal',
                    group: 'theme'
                },
                config: {}
            });
        }"""
    )
    assert unavailable["ok"] is False
    assert unavailable["mode"] == "patch"
    assert unavailable["switchToPatch"] is True
    assert "Missing service endpoint" in unavailable["message"]

    patch_mode = page.evaluate(
        """async () => {
            const workflow = await import('/studio/app/frontend/js/tag-registry-workflow.js');
            return workflow.createTagRegistryTag({
                saveMode: 'patch',
                newTagRow: {
                    tag_id: 'renewal',
                    group: 'theme'
                },
                config: {}
            });
        }"""
    )
    assert patch_mode["ok"] is True
    assert patch_mode["mode"] == "patch"
    assert patch_mode["patchResult"]["kind"] == "warn"
    assert patch_mode["patchResult"]["message"] == (
        "Patch mode: Registry row prepared; nothing has been written."
    )
    patch_payload = json.loads(patch_mode["patchResult"]["snippet"])
    registry_patch = patch_payload["registry"]
    assert registry_patch["path"] == (
        "studio/data/canonical/tags/tag-registry.json"
    )
    assert registry_patch["append_row"]["tag_id"] == "renewal"
    assert registry_patch["append_row"]["group"] == "theme"
    assert "description" not in registry_patch["append_row"]
    assert "doc_id" not in registry_patch["append_row"]
    assert registry_patch["append_row"]["doc_url"] == []
    assert "document" not in patch_payload
    assert patch_payload["notice"].startswith("Nothing has been written")
    assert "rebuild" not in patch_payload


def assert_tag_alias_create_request(page: Page, base_url: str) -> None:
    captured: dict[str, object] = {}
    endpoint = f"{base_url}/studio/api/tags/create-tag-alias"

    def handle_create(route) -> None:
        captured["method"] = route.request.method
        captured["payload"] = route.request.post_data_json
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "ok": True,
                    "action": "create_alias",
                    "alias": "leaf-growth",
                    "tags": ["trees", "growth"],
                    "target_count": 2,
                    "added": 1,
                    "final_total": 2,
                    "updated_at_utc": "2026-07-27T12:00:00Z",
                    "summary_text": "created alias leaf-growth; targets 2; final 2",
                }
            ),
        )

    page.route(endpoint, handle_create)
    result = page.evaluate(
        """async (createEndpoint) => {
            const service = await import('/studio/app/frontend/js/tag-aliases-service.js');
            return service.submitAliasEdit({
                saveMode: 'post',
                isCreate: true,
                originalAlias: '',
                validation: {
                    alias: 'leaf-growth',
                    description: 'Leaf growth',
                    tags: ['trees', 'growth']
                },
                config: {
                    app: {
                        runtime: {
                            services: {
                                tags: {
                                    create_tag_alias: createEndpoint
                                }
                            }
                        }
                    }
                }
            });
        }""",
        endpoint,
    )
    page.unroute(endpoint, handle_create)

    assert result["ok"] is True
    assert result["mode"] == "post"
    assert result["summary"] == "created alias leaf-growth; targets 2; final 2"
    assert captured["method"] == "POST"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["alias"] == "leaf-growth"
    assert payload["description"] == "Leaf growth"
    assert payload["tags"] == ["trees", "growth"]
    assert set(payload) == {"alias", "description", "tags", "client_time_utc", "activity_context"}
    context = payload["activity_context"]
    assert isinstance(context, dict)
    assert context["action_id"] == "create-tag-alias"
    assert context["alias"] == "leaf-growth"

    def reject_create(route) -> None:
        route.fulfill(
            status=400,
            content_type="application/json",
            body=json.dumps({"ok": False, "error": "alias already exists: leaf-growth"}),
        )

    page.route(endpoint, reject_create)
    rejected = page.evaluate(
        """async (createEndpoint) => {
            const service = await import('/studio/app/frontend/js/tag-aliases-service.js');
            return service.submitAliasEdit({
                saveMode: 'post',
                isCreate: true,
                originalAlias: '',
                validation: {
                    alias: 'leaf-growth',
                    description: 'Leaf growth',
                    tags: ['trees']
                },
                config: {
                    app: {
                        runtime: {
                            services: {
                                tags: {
                                    create_tag_alias: createEndpoint
                                }
                            }
                        }
                    }
                }
            });
        }""",
        endpoint,
    )
    page.unroute(endpoint, reject_create)
    assert rejected == {
        "ok": False,
        "mode": "post",
        "switchToPatch": False,
        "message": "alias already exists: leaf-growth",
    }

    unavailable = page.evaluate(
        """async () => {
            const service = await import('/studio/app/frontend/js/tag-aliases-service.js');
            return service.submitAliasEdit({
                saveMode: 'post',
                isCreate: true,
                originalAlias: '',
                validation: {
                    alias: 'leaf-growth',
                    description: 'Leaf growth',
                    tags: ['trees']
                },
                config: {}
            });
        }"""
    )
    assert unavailable["ok"] is False
    assert unavailable["mode"] == "patch"
    assert unavailable["switchToPatch"] is True
    assert "Missing service endpoint" in unavailable["message"]
    assert unavailable["patchResult"]["snippet"]


def assert_studio_tag_editor_interactions(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <input id="workInput">
              <input id="tagInput">
              <button id="addTag"></button>
              <button id="save"></button>
              <p id="warning"></p>
              <p id="status"></p>
              <p id="saveResult"></p>
            `;
            const module = await import('/studio/app/frontend/js/analytics-tag-editor-interactions.js');
            const alpha = { tag_id: 'alpha', group: 'subject', slug: 'alpha' };
            const beta = { tag_id: 'beta', group: 'domain', slug: 'beta' };
            const gamma = { tag_id: 'gamma', group: 'theme', slug: 'gamma' };
            const state = {
                config: {},
                seriesId: 'demo',
                tagsById: new Map([
                    ['alpha', alpha],
                    ['beta', beta],
                    ['gamma', gamma]
                ]),
                slugMap: new Map([
                    ['alpha', [alpha]],
                    ['beta', [beta]],
                    ['gamma', [gamma]]
                ]),
                labelMap: new Map(),
                aliases: new Map([['alias-beta', ['beta']]]),
                seriesEntries: [{
                    entryId: 1,
                    rawInput: 'alpha',
                    canonicalId: 'alpha',
                    group: 'subject',
                    label: 'Alpha',
                    wManual: 0.6,
                    alias: ''
                }],
                baselineSeriesRows: [{ tag_id: 'alpha', w_manual: 0.6 }],
                workEntriesById: new Map(),
                baselineWorkStateById: new Map(),
                seriesWorkOptions: [
                    { workId: '00001' },
                    { workId: '00002' }
                ],
                seriesWorkIds: new Set(['00001', '00002']),
                selectedWorkIds: [],
                selectedWorkId: '',
                refs: {
                    workInput: document.getElementById('workInput'),
                    input: document.getElementById('tagInput'),
                    addButton: document.getElementById('addTag'),
                    saveButton: document.getElementById('save'),
                    saveWarning: document.getElementById('warning'),
                    status: document.getElementById('status'),
                    saveResult: document.getElementById('saveResult')
                },
                statusKind: '',
                statusText: ''
            };
            const calls = [];
            const text = (_key, fallback, tokens = null) => {
                if (!tokens) return fallback;
                return Object.entries(tokens).reduce((value, [token, replacement]) => value.replace(`{${token}}`, replacement), fallback);
            };
            const callbacks = {
                text,
                hidePopup: () => calls.push('hidePopup'),
                hideWorkPopup: () => calls.push('hideWorkPopup'),
                renderAll: () => calls.push('renderAll'),
                renderStatus: () => calls.push('renderStatus'),
                renderWorkPopup: () => calls.push('renderWorkPopup'),
                setSaveResult: (_state, kind, message) => {
                    state.refs.saveResult.dataset.state = kind;
                    state.refs.saveResult.textContent = message;
                    calls.push(`saveResult:${kind}`);
                },
                setStatus: (_state, kind, message) => {
                    state.statusKind = kind;
                    state.statusText = message;
                    calls.push(`status:${kind}`);
                },
                getMatchingWorkOptions: (_state, rawInput) => {
                    const normalized = String(rawInput).padStart(5, '0');
                    return state.seriesWorkOptions.filter((item) => item.workId === normalized);
                }
            };
            module.addAnalyticsTagEditorWorkSelection(state, '00001', true, callbacks);
            module.addAnalyticsTagEditorResolvedTag(state, beta, { rawInput: 'alias-beta', alias: 'alias-beta' }, callbacks);
            const workEntryAfterAdd = state.workEntriesById.get('00001')[0];
            const workProjection = module.projectAnalyticsTagEditorSaveState(state, { text });
            module.cycleAnalyticsTagEditorEntryWeight(state, workEntryAfterAdd.entryId, callbacks);
            const cycledWeight = state.workEntriesById.get('00001')[0].wManual;
            module.removeAnalyticsTagEditorEditableEntry(state, workEntryAfterAdd.entryId, callbacks);
            const workEntriesAfterRemove = state.workEntriesById.get('00001').length;
            module.clearAnalyticsTagEditorSelectedWork(state, '00001', callbacks);
            module.addAnalyticsTagEditorResolvedTag(state, beta, { rawInput: 'beta' }, callbacks);
            const seriesProjection = module.applyAnalyticsTagEditorSaveState(state, { text });
            return {
                selectedAfterClear: state.selectedWorkId,
                selectedIdsAfterClear: state.selectedWorkIds.slice(),
                workEntryAfterAdd,
                workProjection: {
                    isDirty: workProjection.isDirty,
                    saveButtonDisabled: workProjection.saveButtonDisabled,
                    warningText: workProjection.warningText,
                    unresolvedCount: workProjection.metrics.unresolvedCount
                },
                cycledWeight,
                workEntriesAfterRemove,
                seriesEntries: state.seriesEntries.map((entry) => entry.canonicalId),
                seriesProjection: {
                    isDirty: seriesProjection.isDirty,
                    saveButtonDisabled: seriesProjection.saveButtonDisabled,
                    warningText: seriesProjection.warningText,
                    unresolvedCount: seriesProjection.metrics.unresolvedCount
                },
                saveDisabled: state.refs.saveButton.disabled,
                warningText: state.refs.saveWarning.textContent,
                statusKind: state.statusKind,
                calls
            };
        }"""
    )
    assert result["workEntryAfterAdd"]["canonicalId"] == "beta"
    assert result["workEntryAfterAdd"]["alias"] == "alias-beta"
    assert result["workProjection"] == {
        "isDirty": True,
        "saveButtonDisabled": False,
        "warningText": "",
        "unresolvedCount": 0,
    }
    assert result["cycledWeight"] == 0.9
    assert result["workEntriesAfterRemove"] == 0
    assert result["selectedAfterClear"] == ""
    assert result["selectedIdsAfterClear"] == []
    assert result["seriesEntries"] == ["alpha", "beta"]
    assert result["seriesProjection"] == {
        "isDirty": True,
        "saveButtonDisabled": False,
        "warningText": "Save to persist the current tag assignment diff.",
        "unresolvedCount": 0,
    }
    assert result["saveDisabled"] is False
    assert result["warningText"] == "Save to persist the current tag assignment diff."
    assert result["statusKind"] == "success"


def assert_studio_tag_editor_direct_save_failure(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = '<main><div id="seriesTagEditorRoot"></div></main>';
            const stateModule = await import('/studio/app/frontend/js/analytics-tag-editor-state.js');
            const domain = await import('/studio/app/frontend/js/analytics-tag-editor-domain.js');
            const interactions = await import('/studio/app/frontend/js/analytics-tag-editor-interactions.js');
            const saveController = await import('/studio/app/frontend/js/analytics-tag-editor-save-controller.js');
            const alpha = { tag_id: 'alpha', group: 'subject', slug: 'alpha' };
            const beta = { tag_id: 'beta', group: 'domain', slug: 'beta' };
            const state = stateModule.buildAnalyticsTagEditorState({
                mount: document.createElement('div'),
                seriesId: 'demo',
                registryJson: { tags: [alpha, beta] },
                aliasesJson: { aliases: {} },
                assignmentsJson: {
                    series: {
                        demo: {
                            tags: [{ tag_id: 'alpha', w_manual: 0.6 }]
                        }
                    }
                },
                seriesRecordJson: {
                    series: { series_id: 'demo', status: 'published' },
                    ordered_published_work_ids: [],
                    member_works: []
                },
                config: {},
                studioGroups: ['subject', 'domain'],
                defaultWeight: 0.6
            });
            interactions.addAnalyticsTagEditorResolvedTag(state, beta, { rawInput: 'beta' });
            const wrongTargetOptions = domain.buildExactSeriesWorkOptions('demo', {
                series: { series_id: 'other', status: 'published' },
                ordered_published_work_ids: ['00001'],
                member_works: [{ work_id: '00001', title: 'Wrong', status: 'published', series_ids: ['other'] }]
            });
            const baselineBefore = JSON.stringify(state.baselineSeriesRows);
            let saveResult = null;
            let renderCount = 0;
            await saveController.handleAnalyticsTagEditorSave(state, {
                postTags: async () => {
                    throw new Error('service unavailable');
                },
                renderAll: () => {
                    renderCount += 1;
                },
                renderStatus: () => {},
                setSaveResult: (_state, kind, text) => {
                    saveResult = { kind, text };
                },
                syncRouteBusyState: () => {}
            });
            return {
                baselineBefore,
                baselineAfter: JSON.stringify(state.baselineSeriesRows),
                seriesTags: state.seriesEntries.map((entry) => entry.canonicalId),
                statusKind: state.statusKind,
                statusText: state.statusText,
                saveResult,
                serviceAvailable: state.serviceAvailable,
                isBusy: state.isBusy,
                renderCount,
                wrongTargetOptionCount: wrongTargetOptions.length
            };
        }"""
    )
    assert result["baselineAfter"] == result["baselineBefore"]
    assert result["seriesTags"] == ["alpha", "beta"]
    assert result["statusKind"] == "error"
    assert result["statusText"] == "Local save failed."
    assert result["saveResult"] == {
        "kind": "warn",
        "text": "Changes remain unsaved in this editor.",
    }
    assert result["serviceAvailable"] is False
    assert result["isBusy"] is False
    assert result["renderCount"] == 1
    assert result["wrongTargetOptionCount"] == 0


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            assert_tag_save_session_helpers(page)
            assert_tag_delete_document_blockers(page)
            assert_tag_registry_document_contract(page)
            assert_tag_registry_edit_request(page, base_url)
            assert_tag_registry_create_request(page, base_url)
            assert_tag_alias_create_request(page, base_url)
            assert_studio_tag_editor_interactions(page)
            assert_studio_tag_editor_direct_save_failure(page)
            picker_page = browser.new_page()
            picker_errors: list[str] = []
            picker_page.on(
                "pageerror",
                lambda error: picker_errors.append(str(error)),
            )
            picker_page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_document_location_provider_contract(picker_page)
            assert_document_location_picker_interactions(picker_page)
            picker_page.close()
            browser.close()
            if errors or picker_errors:
                raise AssertionError(
                    "page errors during Tag route shell module smoke: "
                    f"route={errors!r}, picker={picker_errors!r}"
                )
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

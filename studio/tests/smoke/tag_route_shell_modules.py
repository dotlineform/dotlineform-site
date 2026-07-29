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


def assert_document_location_provider_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/shared/frontend/js/document-location-provider.js');
            const actualProvider = module.createDocumentLocationProvider();
            const actualAnalysis = await actualProvider.load({ scopeIds: ['analysis'] });
            const actualLibrary = await actualProvider.load({ scopeIds: ['library'] });
            const calls = [];
            const payloads = {
                analysis: {
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
                },
                library: {
                    schema_version: 'docs_document_locations_v1',
                    scope_id: 'library',
                    records: [
                        {
                            url: '/library/?doc=d-20260507-172400-74807b',
                            scope_id: 'library',
                            document_title: 'Beauty',
                            report_title: ''
                        }
                    ]
                }
            };
            const provider = module.createDocumentLocationProvider({
                fetchJson: async (url) => {
                    calls.push(url);
                    const scopeId = url.includes('/analysis/') ? 'analysis' : 'library';
                    return payloads[scopeId];
                }
            });
            const exact = await provider.search({
                scopeIds: ['analysis'],
                query: 'bird-nerve'
            });
            const excluded = await provider.search({
                scopeIds: ['analysis'],
                query: 'bird',
                excludedUrls: [payloads.analysis.records[0].url]
            });
            const multi = await provider.search({
                scopeIds: ['analysis', 'library'],
                query: 'beauty'
            });
            const resolved = await provider.resolve({
                scopeIds: ['analysis'],
                urls: [
                    payloads.analysis.records[0].url,
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
                await provider.load({ scopeIds: ['studio'] });
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
                    analysisReports: actualAnalysis.filter((record) => record.report_title).length,
                    libraryCount: actualLibrary.length,
                    libraryScopes: [...new Set(actualLibrary.map((record) => record.scope_id))]
                },
                calls,
                exact: exact.map((record) => [record.document_title, record.report_title]),
                excluded: excluded.map((record) => [record.document_title, record.report_title]),
                multi: multi.map((record) => [record.scope_id, record.document_title]),
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
    assert result["actual"]["libraryCount"] >= 1
    assert result["actual"]["libraryScopes"] == ["library"]
    assert result["calls"] == [
        "/assets/data/search/analysis/document-locations.json",
        "/assets/data/search/library/document-locations.json",
    ]
    assert result["exact"] == [
        ["bird-nerve", "All Tags"],
        ["bird-nerve", "Made-up Tags"],
    ]
    assert result["excluded"] == [
        ["bird-nerve", "Made-up Tags"],
        ["Small bird study", ""],
    ]
    assert result["multi"] == [["library", "Beauty"]]
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
    assert "unsupported document-location scope: studio" in result["unsupportedError"]
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
            input.value = 'beauty';
            const libraryRecord = {
                url: '/library/?doc=d-20260507-172400-74807b',
                scope_id: 'library',
                document_title: 'Beauty',
                report_title: ''
            };
            picker = pickerModule.bindDocumentLocationPicker(input, popup, {
                scopeIds: ['analysis', 'library'],
                provider: { search: async () => [libraryRecord] },
                onCommit: (record) => commits.push(record)
            });
            await picker.refresh();
            const multiScope = {
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
            return {
                singleScope,
                keyboardCommit,
                multiScope,
                pointerCommit,
                emptyText,
                failureText,
                asyncText,
                pendingCommitCount: pendingCommits.length
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
    assert result["multiScope"]["buttonCount"] == 1
    assert "Library" in result["multiScope"]["text"]
    assert result["pointerCommit"]["scope_id"] == "library"
    assert "No matching documents." in result["emptyText"]
    assert "Projection unavailable." in result["failureText"]
    assert "fast" in result["asyncText"]
    assert "slow" not in result["asyncText"]
    assert result["pendingCommitCount"] == 0


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
                    "doc_url": [
                        "/analysis/?doc=d-20260624-213316-478639"
                        "&subdoc=d-20260729-120000-abcdef"
                    ],
                    "doc_id": "d-20260729-120000-abcdef",
                    "added": 1,
                    "final_total": 2,
                    "updated_at_utc": "2026-07-27T12:00:00Z",
                    "summary_text": (
                        "created tag renewal with linked Analysis document "
                        "d-20260729-120000-abcdef; final 2"
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
        "created tag renewal with linked Analysis document "
        "d-20260729-120000-abcdef; final 2"
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
                config: {
                    app: {
                        runtime: {
                            services: {
                                tags: {
                                    analysis_tags_document_url_template:
                                        '/analysis/?doc=d-20260624-213316-478639&subdoc={doc_id}'
                                }
                            }
                        }
                    }
                }
            });
        }"""
    )
    assert patch_mode["ok"] is True
    assert patch_mode["mode"] == "patch"
    assert patch_mode["patchResult"]["kind"] == "warn"
    assert patch_mode["patchResult"]["message"] == (
        "Patch mode: linked Registry row and Analysis tag document prepared; "
        "nothing has been written."
    )
    patch_payload = json.loads(patch_mode["patchResult"]["snippet"])
    registry_patch = patch_payload["registry"]
    patch_doc_id = patch_payload["document"]["path"].rsplit("/", 1)[-1][:-3]
    assert re.fullmatch(
        r"d-\d{8}-\d{6}-[0-9a-f]{6}",
        patch_doc_id,
    )
    assert registry_patch["path"] == (
        "studio/data/canonical/tags/tag-registry.json"
    )
    assert registry_patch["append_row"]["tag_id"] == "renewal"
    assert registry_patch["append_row"]["group"] == "theme"
    assert "description" not in registry_patch["append_row"]
    assert "doc_id" not in registry_patch["append_row"]
    assert registry_patch["append_row"]["doc_url"] == [
        "/analysis/?doc=d-20260624-213316-478639"
        f"&subdoc={patch_doc_id}"
    ]
    assert patch_payload["document"]["path"].endswith(
        f"/{patch_doc_id}.md"
    )
    assert f"doc_id: {patch_doc_id}" in patch_payload["document"]["source"]
    assert "group: theme" in patch_payload["document"]["source"]
    assert "Renewal" not in patch_payload["document"]["source"]
    assert patch_payload["notice"].startswith("Nothing has been written")
    assert patch_payload["rebuild"].endswith(
        "--write --skip-browser-config"
    )


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
                seriesIndexJson: { series: { demo: { works: [] } } },
                worksIndexJson: { works: {} },
                config: {},
                studioGroups: ['subject', 'domain'],
                defaultWeight: 0.6
            });
            interactions.addAnalyticsTagEditorResolvedTag(state, beta, { rawInput: 'beta' });
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
                renderCount
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

#!/usr/bin/env python3
"""Smoke-check focused Data Sharing prepare JavaScript modules."""

from __future__ import annotations

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import unquote, urlsplit

from playwright.sync_api import Page, sync_playwright


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        request_path = unquote(urlsplit(path).path)
        if request_path.startswith("/analytics/app/"):
            relative = f"analytics-app/app/{request_path.removeprefix('/analytics/app/')}"
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


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def install_fixture(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <main>
                <select id="dataSharingPrepareConfigSelect"></select>
                <div id="dataSharingPrepareMissingSummaryWrap"></div>
                <input id="dataSharingPrepareMissingSummaryOnly" type="checkbox">
                <div id="dataSharingPrepareRenderTarget"></div>
              </main>
            `;
            const workflow = await import('/analytics/app/frontend/js/data-sharing-prepare-workflow.js');
            const docs = await import('/analytics/app/frontend/js/data-sharing-prepare-docs.js');
            const render = await import('/analytics/app/frontend/js/data-sharing-prepare-render.js');
            const service = await import('/analytics/app/frontend/js/data-sharing-prepare-service.js');
            const docCapability = {
                capability: {
                    selection_model: 'documents',
                    sharing_profiles: [
                        {
                            id: 'library-documents',
                            enabled: true,
                            label: 'Library documents',
                            scopes: ['library'],
                            target: {
                                format: 'jsonl',
                                supported_formats: ['json', 'jsonl']
                            },
                            selection: {
                                supports_missing_summary_only: true,
                                default_missing_summary_only: true
                            }
                        },
                        {
                            id: 'disabled-profile',
                            enabled: false,
                            scopes: ['library']
                        }
                    ]
                }
            };
            const state = {
                config: {
                    ui_text: {
                        data_sharing_prepare: {
                            count_selected: 'selected',
                            count_exported: 'packaged',
                            count_skipped: 'skipped',
                            count_failed: 'failed',
                            count_truncated: 'truncated',
                            issues_heading: 'Issues',
                            warnings_heading: 'Warnings',
                            result_files_label: 'files created',
                            result_files_empty: 'No files created.',
                            result_format_label: 'format',
                            format_required: 'Select a supported package format.',
                            selection_required: 'Select at least one document.',
                            status_failed: 'Package preparation failed.',
                            status_success: 'Package prepared.'
                        }
                    }
                },
                scope: 'library',
                prepareCapability: docCapability,
                targetFormat: 'jsonl',
                selectedIds: new Set(['alpha', 'beta']),
                missingSummaryOnlyWrap: document.getElementById('dataSharingPrepareMissingSummaryWrap'),
                missingSummaryOnly: document.getElementById('dataSharingPrepareMissingSummaryOnly'),
                renderTarget: document.getElementById('dataSharingPrepareRenderTarget')
            };
            state.missingSummaryOnlyWrap.hidden = false;
            state.missingSummaryOnly.checked = true;
            window.__dataSharingPrepareModuleSmoke = {
                workflow,
                docs,
                render,
                service,
                state,
                configs: [
                    {
                        id: 'library-documents',
                        enabled: true,
                        scopes: ['library'],
                        target: {
                            format: 'jsonl',
                            supported_formats: ['json', 'jsonl']
                        },
                        selection: {
                            supports_missing_summary_only: true
                        }
                    },
                    {
                        id: 'tags-registry',
                        enabled: true,
                        scopes: ['tags'],
                        target: { format: 'json' }
                    },
                    {
                        id: 'disabled-library',
                        enabled: false,
                        scopes: ['library'],
                        target: { format: 'json' }
                    }
                ]
            };
        }"""
    )


def assert_package_state_projection(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const smoke = window.__dataSharingPrepareModuleSmoke;
            const { workflow, service, state, configs } = smoke;
            const enabledConfigs = workflow.enabledPrepareConfigsForScope({ configs }, 'library');
            const config = enabledConfigs[0];
            const submission = service.buildDataSharingPrepareSubmission(state, {
                config,
                supportedFormats: ['json', 'jsonl']
            });
            const profileOnlyCapability = { capability: { selection_model: 'profile' } };
            const profileRequest = workflow.buildPreparePackageRequest({
                scope: 'tags',
                config: {
                    id: 'tags-registry',
                    selection: { mode: 'all_matching' }
                },
                targetFormat: 'json',
                selectedIds: new Set(['ignored']),
                usesDocumentSelection: false,
                missingSummaryOnlyAvailable: true,
                missingSummaryOnly: true
            });
            const allMatchingRequest = workflow.buildPreparePackageRequest({
                scope: 'library',
                config: {
                    id: 'library-all',
                    selection: { mode: 'all_matching' }
                },
                targetFormat: 'json',
                selectedIds: new Set(['ignored']),
                usesDocumentSelection: true,
                missingSummaryOnlyAvailable: true,
                missingSummaryOnly: false
            });
            state.targetFormat = 'xml';
            const invalidFormat = service.buildDataSharingPrepareSubmission(state, {
                config,
                supportedFormats: ['json', 'jsonl']
            });
            state.targetFormat = 'jsonl';
            state.selectedIds = new Set();
            const missingSelection = service.buildDataSharingPrepareSubmission(state, {
                config,
                supportedFormats: ['json', 'jsonl']
            });
            return {
                selectionModel: workflow.prepareSelectionModel(state.prepareCapability),
                usesDocuments: workflow.usesPrepareDocumentSelection(state.prepareCapability),
                profileCount: workflow.prepareProfilesForCapability(state.prepareCapability).length,
                enabledConfigIds: enabledConfigs.map((item) => item.id),
                submission,
                profileUsesDocuments: workflow.usesPrepareDocumentSelection(profileOnlyCapability),
                profileRequest,
                allMatchingRequest,
                invalidFormat,
                missingSelection
            };
        }"""
    )
    if result["selectionModel"] != "documents" or result["usesDocuments"] is not True:
        raise AssertionError(f"document selection capability projection changed: {result!r}")
    if result["profileCount"] != 1 or result["enabledConfigIds"] != ["library-documents"]:
        raise AssertionError(f"enabled prepare config projection changed: {result!r}")

    submission = result["submission"]
    if submission["ok"] is not True:
        raise AssertionError(f"valid submission rejected: {result!r}")
    request = submission["request"]
    expected_request = {
        "data_domain": "library",
        "config_id": "library-documents",
        "target_format": "jsonl",
        "doc_ids": ["alpha", "beta"],
        "select_all": False,
        "missing_summary_only": True,
    }
    for key, value in expected_request.items():
        if request.get(key) != value:
            raise AssertionError(f"prepare request {key} mismatch: {result!r}")
    activity = request.get("activity_context", {})
    if activity.get("page_id") != "data-sharing-prepare" or activity.get("export_id") != "library:library-documents":
        raise AssertionError(f"prepare activity context mismatch: {result!r}")

    if result["profileUsesDocuments"] is not False:
        raise AssertionError(f"profile-only selection capability changed: {result!r}")
    profile_request = result["profileRequest"]
    if profile_request["doc_ids"] != ["ignored"] or profile_request["select_all"] is not False:
        raise AssertionError(f"profile request should preserve explicit service shape: {result!r}")
    if profile_request["missing_summary_only"] is not None:
        raise AssertionError(f"profile request should not project missing-summary filtering: {result!r}")
    all_matching_request = result["allMatchingRequest"]
    if all_matching_request["doc_ids"] != [] or all_matching_request["select_all"] is not True:
        raise AssertionError(f"all-matching document request changed: {result!r}")

    if result["invalidFormat"]["ok"] is not False or result["invalidFormat"]["statusState"] != "error":
        raise AssertionError(f"invalid format validation changed: {result!r}")
    if result["missingSelection"]["ok"] is not False or result["missingSelection"]["statusMessage"] != "Select at least one document.":
        raise AssertionError(f"missing selection validation changed: {result!r}")


def assert_selectable_records_loading(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__dataSharingPrepareModuleSmoke;
            const { docs, state } = smoke;
            const requested = [];
            const loaded = await docs.loadDataSharingPrepareDocsState({
                config: state.config,
                scope: 'library',
                serviceAvailable: true,
                prepareCapability: state.prepareCapability,
                workflowActive: true,
                exportConfigCount: 1,
                loadJson: async (path) => {
                    requested.push(path);
                    return {
                        ok: true,
                        records: [
                            {
                                doc_id: 'parent',
                                title: 'Parent',
                                viewable: true,
                                content_text_length: 10,
                                summary: 'Summary.'
                            },
                            {
                                doc_id: 'child',
                                parent_id: 'parent',
                                title: 'Child',
                                viewable: false,
                                content_text_length: 0,
                                summary: ''
                            }
                        ]
                    };
                }
            });
            return {
                requested,
                docIds: loaded.docs.map((doc) => doc.doc_id),
                childDepth: loaded.depthById.get('child'),
                childParentCount: loaded.childrenByParent.get('parent')?.length || 0,
                docsIndexError: loaded.docsIndexError
            };
        }"""
    )
    if len(result["requested"]) != 1:
        raise AssertionError(f"selectable-records loader should make one request: {result!r}")
    if "/analytics/api/data-sharing/selectable-records" not in result["requested"][0]:
        raise AssertionError(f"prepare docs loader did not use the Analytics selectable-records API: {result!r}")
    if "data_domain=library" not in result["requested"][0]:
        raise AssertionError(f"selectable-records loader did not pass data_domain: {result!r}")
    if result["docIds"] != ["parent", "child"] or result["childDepth"] != 1 or result["childParentCount"] != 1:
        raise AssertionError(f"selectable records were not projected into document hierarchy state: {result!r}")
    if result["docsIndexError"] is not False:
        raise AssertionError(f"selectable-records loader reported an unexpected error: {result!r}")


def assert_result_rendering(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const smoke = window.__dataSharingPrepareModuleSmoke;
            const { render, state } = smoke;
            const payload = {
                target_format: 'jsonl',
                count_unit: 'record',
                counts: {
                    selected: 2,
                    exported: 1,
                    skipped: 0,
                    failed: 1,
                    truncated: 0
                },
                output_files: [
                    '/tmp/data-sharing/export.jsonl',
                    'nested/extra.jsonl'
                ],
                output_file: '/tmp/data-sharing/export.jsonl',
                errors: ['Fatal <error>'],
                warnings: ['Skipped <warning>']
            };
            state.renderTarget.innerHTML = render.renderDataSharingPrepareResultBody(state, payload);
            return {
                rows: Array.from(state.renderTarget.querySelectorAll('.dataSharingPrepareModal__countRow'))
                    .map((row) => Array.from(row.children).map((node) => node.textContent.trim())),
                fileList: state.renderTarget.querySelector('.dataSharingPrepareModal__fileList')?.value || '',
                issueHeading: state.renderTarget.querySelector('.dataSharingPrepareModal__issues h4')?.textContent.trim() || '',
                issueItems: Array.from(state.renderTarget.querySelectorAll('.dataSharingPrepareModal__issues li'))
                    .map((node) => node.textContent.trim()),
                issueHtml: state.renderTarget.querySelector('.dataSharingPrepareModal__issues')?.innerHTML || ''
            };
        }"""
    )
    if ["format", "JSONL"] not in result["rows"]:
        raise AssertionError(f"result format row missing: {result!r}")
    if ["selected", "2 records"] not in result["rows"] or ["failed", "1 record"] not in result["rows"]:
        raise AssertionError(f"result count labels changed: {result!r}")
    if result["fileList"] != "export.jsonl\nextra.jsonl":
        raise AssertionError(f"result output files changed: {result!r}")
    if result["issueHeading"] != "Issues":
        raise AssertionError(f"result issue heading changed: {result!r}")
    if result["issueItems"] != ["Fatal <error>", "Skipped <warning>"]:
        raise AssertionError(f"result issues changed: {result!r}")
    if "<error>" in result["issueHtml"] or "<warning>" in result["issueHtml"]:
        raise AssertionError(f"result issues were not escaped: {result!r}")


def assert_fallback_write_behavior(page: Page) -> None:
    prepare_requests: list[dict[str, object]] = []

    def handle(route):
        request = route.request
        if request.method == "OPTIONS":
            route.fulfill(
                status=204,
                headers={
                    "access-control-allow-origin": "*",
                    "access-control-allow-methods": "POST, OPTIONS",
                    "access-control-allow-headers": "content-type",
                },
                body="",
            )
            return
        post_data_json = request.post_data_json
        prepare_requests.append(post_data_json() if callable(post_data_json) else post_data_json)
        route.fulfill(
            status=503,
            headers={
                "access-control-allow-origin": "*",
                "content-type": "application/json",
            },
            body=json.dumps(
                {
                    "ok": False,
                    "error": "write service offline",
                    "target_format": "jsonl",
                    "counts": {"selected": 2, "exported": 0, "failed": 2},
                    "errors": ["write unavailable"],
                    "output_file": "var/studio/data-sharing/library/exports/fallback.jsonl",
                }
            ),
        )

    page.route("**/analytics/api/data-sharing/prepare", handle)
    result = page.evaluate(
        """async () => {
            const smoke = window.__dataSharingPrepareModuleSmoke;
            const { service, state } = smoke;
            const request = {
                data_domain: 'library',
                config_id: 'library-documents',
                target_format: 'jsonl',
                doc_ids: ['alpha', 'beta'],
                select_all: false,
                missing_summary_only: true
            };
            const failure = await service.runDataSharingPreparePackage(state, request);
            const success = service.dataSharingPrepareSuccessResult(state, {
                ok: true,
                summary_text: '',
                counts: { selected: 1, exported: 1 }
            });
            return {
                failure: {
                    failed: failure.failed,
                    statusState: failure.statusState,
                    statusMessage: failure.statusMessage,
                    payload: failure.payload
                },
                success
            };
        }"""
    )
    if len(prepare_requests) != 1:
        raise AssertionError(f"prepare write endpoint was not called once: {prepare_requests!r}")
    if prepare_requests[0].get("doc_ids") != ["alpha", "beta"]:
        raise AssertionError(f"prepare write request changed: {prepare_requests!r}")

    failure = result["failure"]
    if failure["failed"] is not True or failure["statusState"] != "error":
        raise AssertionError(f"prepare failure result metadata changed: {result!r}")
    if failure["statusMessage"] != "write service offline":
        raise AssertionError(f"prepare failure message changed: {result!r}")
    if failure["payload"].get("errors") != ["write unavailable"]:
        raise AssertionError(f"prepare failure payload was not preserved: {result!r}")
    success = result["success"]
    if success["failed"] is not False or success["statusMessage"] != "Package prepared.":
        raise AssertionError(f"prepare success fallback message changed: {result!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--site-root", help="Serve a site or repository root on a temporary local HTTP server.")
    args = parser.parse_args()

    server = None
    base_url = args.base_url
    if args.site_root:
        server, base_url = start_static_server(Path(args.site_root))

    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(route_url(base_url, "/"), wait_until="domcontentloaded")
            install_fixture(page)
            assert_package_state_projection(page)
            assert_selectable_records_loading(page)
            assert_result_rendering(page)
            assert_fallback_write_behavior(page)
        finally:
            browser.close()
            if server:
                server.shutdown()
                server.server_close()

    if errors:
        raise AssertionError(f"page errors during Data Sharing prepare module smoke: {errors!r}")
    print("Data Sharing prepare module smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

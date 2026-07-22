#!/usr/bin/env python3
"""Smoke-check Prepare package request composition and compact management workflow."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def setup_page(page: Page, base_url: str, timeout_ms: int) -> None:
    page.goto(base_url, wait_until="domcontentloaded", timeout=timeout_ms)
    page.add_style_tag(url=f"{base_url}/site/docs-viewer/static/css/docs-viewer.css")
    page.add_style_tag(url=f"{base_url}/docs-viewer/static/css/docs-viewer-manage.css")


def assert_prepare_model(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const model = await import('/docs-viewer/runtime/js/packages/document-package-prepare-model.js');
            const documents = [
                { doc_id: 'root', parent_id: '', selectable: true },
                { doc_id: 'child', parent_id: 'root', selectable: true },
                { doc_id: 'grandchild', parent_id: 'child', selectable: true },
                { doc_id: 'sibling', parent_id: '', selectable: true },
                { doc_id: 'blocked', parent_id: 'root', selectable: false }
            ];
            const contentProfile = {
                profile_id: 'document-content',
                target_format: 'jsonl',
                supported_target_formats: ['jsonl', 'json'],
                content_format: 'markdown',
                supported_content_formats: ['markdown', 'plain_text'],
                record_shape: 'document_rows',
                selection: { include_descendants: true },
                external_context: {
                    task: 'Review',
                    response_guidance: 'Return changes',
                    field_descriptions: { doc_id: 'Stable id', content: 'Body' }
                },
                document_fields: [{ output_path: 'doc_id' }, { output_path: 'content' }]
            };
            const treeProfile = {
                ...contentProfile,
                profile_id: 'document-tree',
                target_format: 'json',
                supported_target_formats: ['json'],
                content_format: '',
                supported_content_formats: [],
                record_shape: 'document_tree'
            };
            let ineligibleMessage = '';
            try {
                model.createDocumentPackagePrepareRequest({
                    scope: 'studio',
                    profile: contentProfile,
                    documents,
                    checkedDocIds: ['blocked']
                });
            } catch (error) {
                ineligibleMessage = error.message;
            }
            return {
                descendants: model.documentPackageDescendantIds(documents, 'root'),
                eligibility: model.documentPackageSelectionEligibility(documents, ['root', 'blocked']),
                expanded: model.expandDocumentPackageSelection(documents, ['root', 'sibling'], true),
                exactRequest: model.createDocumentPackagePrepareRequest({
                    scope: 'STUDIO',
                    profile: contentProfile,
                    documents,
                    checkedDocIds: ['root'],
                    includeDescendants: false,
                    targetFormat: 'json',
                    contentFormat: 'plain_text'
                }),
                treeRequest: model.createDocumentPackagePrepareRequest({
                    scope: 'studio',
                    profile: treeProfile,
                    documents,
                    checkedDocIds: ['root'],
                    includeDescendants: false
                }),
                context: model.documentPackageExternalContext(contentProfile),
                missingContext: model.documentPackageExternalContextMissingValues(contentProfile, {
                    task: '',
                    response_guidance: 'Return changes',
                    field_descriptions: { doc_id: 'Stable id', content: '' }
                }),
                ineligibleMessage
            };
        }"""
    )
    expected = {
        "descendants": ["child", "blocked", "grandchild"],
        "eligibility": {
            "eligibleDocIds": ["root"],
            "ineligibleDocIds": ["blocked"],
        },
        "expanded": ["root", "child", "grandchild", "sibling"],
        "exactRequest": {
            "scope": "studio",
            "profile_id": "document-content",
            "doc_ids": ["root"],
            "select_all": False,
            "target_format": "json",
            "content_format": "plain_text",
            "dry_run": False,
            "activity_context": {},
        },
        "treeRequest": {
            "scope": "studio",
            "profile_id": "document-tree",
            "doc_ids": ["root", "child", "grandchild"],
            "select_all": False,
            "target_format": "json",
            "content_format": "",
            "dry_run": False,
            "activity_context": {},
        },
        "context": {
            "task": "Review",
            "response_guidance": "Return changes",
            "field_descriptions": {"doc_id": "Stable id", "content": "Body"},
        },
        "missingContext": ["task", "content"],
        "ineligibleMessage": "Checked documents are unavailable for package preparation: blocked",
    }
    if result != expected:
        raise AssertionError(f"unexpected Prepare package model contract: {result!r}")


def assert_prepare_action_router(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const { createDocsViewerManagementEventRouter } = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-event-router.js'
            );
            document.body.innerHTML = [
                '<button id="manageActions" aria-expanded="true"></button>',
                '<div id="manageMenu"></div>'
            ].join('');
            const calls = [];
            const router = createDocsViewerManagementEventRouter({
                refs: {
                    manageActionsButton: document.querySelector('#manageActions'),
                    manageActionsMenu: document.querySelector('#manageMenu')
                },
                commands: {
                    preparePackage: () => calls.push('preparePackage')
                },
                controllers: {
                    interaction: () => ({ hideContextMenu: () => calls.push('hideContextMenu') })
                }
            });
            const handled = router.handleAppManagementControl({
                actionId: 'prepare-document-package',
                eventType: 'click'
            });
            return {
                handled,
                calls,
                menuHidden: document.querySelector('#manageMenu').hidden,
                expanded: document.querySelector('#manageActions').getAttribute('aria-expanded')
            };
        }"""
    )
    expected = {
        "handled": True,
        "calls": ["hideContextMenu", "preparePackage"],
        "menuHidden": True,
        "expanded": "false",
    }
    if result != expected:
        raise AssertionError(f"unexpected Prepare package Action routing: {result!r}")


def install_workflow_fixture(page: Page, prepare_outcome: str = "success") -> None:
    page.evaluate(
        """async (prepareOutcome) => {
            const workflow = await import('/docs-viewer/runtime/js/packages/document-package-prepare-workflow.js');
            document.body.innerHTML = '<main class="docsViewer" id="docsViewerRoot"><button id="restoreFocus">Prepare package</button></main>';
            window.prepareFixture = {
                busy: [],
                calls: [],
                messages: [],
                selection: ['root', 'sibling']
            };
            const profiles = [{
                profile_id: 'document-content',
                label: 'Document content',
                description: 'Document summaries and content.',
                target_format: 'jsonl',
                supported_target_formats: ['jsonl', 'json'],
                content_format: 'markdown',
                supported_content_formats: ['markdown', 'plain_text'],
                record_shape: 'document_rows',
                selection: { include_descendants: true },
                external_context: {
                    task: 'Review',
                    response_guidance: 'Return changes',
                    field_descriptions: { doc_id: 'Stable id', content: 'Body' }
                },
                document_fields: [{ output_path: 'doc_id' }, { output_path: 'content' }]
            }];
            const documents = [
                { doc_id: 'root', parent_id: '', title: 'Root', selectable: true },
                { doc_id: 'child', parent_id: 'root', title: 'Child', selectable: true },
                { doc_id: 'grandchild', parent_id: 'child', title: 'Grandchild', selectable: true },
                { doc_id: 'sibling', parent_id: '', title: 'Sibling', selectable: true }
            ];
            const client = {
                getConfig: async () => {
                    window.prepareFixture.calls.push({ method: 'config' });
                    return {
                        ok: true,
                        workspace: { available: true, message: '' },
                        scopes: [{ scope: 'studio', label: 'Studio' }],
                        profiles
                    };
                },
                getDocuments: async (scope) => {
                    window.prepareFixture.calls.push({ method: 'documents', scope });
                    return { ok: true, records: documents };
                },
                saveContext: async (payload) => {
                    window.prepareFixture.calls.push({ method: 'context', payload });
                    return { ok: true, external_context: payload.external_context };
                },
                prepare: async (payload) => {
                    window.prepareFixture.calls.push({ method: 'prepare', payload });
                    if (prepareOutcome === 'failure') {
                        const error = new Error('Package write failed.');
                        error.payload = {
                            ok: false,
                            summary_text: 'Package write failed.',
                            counts: { selected: 4, exported: 0, failed: 1 },
                            warnings: ['No package was written.']
                        };
                        throw error;
                    }
                    return {
                        ok: true,
                        summary_text: 'Prepared package with 4 document(s).',
                        counts: { selected: 4, exported: 4, failed: 0 },
                        output_file: '/packages/output.json',
                        metadata_file: '/packages/output.meta.json',
                        warnings: ['One field was truncated.']
                    };
                }
            };
            window.prepareWorkflowPromise = workflow.openDocumentPackagePrepareWorkflow({
                root: document.querySelector('#docsViewerRoot'),
                scope: 'studio',
                checkedDocIds: window.prepareFixture.selection.slice(),
                restoreFocus: document.querySelector('#restoreFocus'),
                client,
                callbacks: {
                    setBusy: (busy) => window.prepareFixture.busy.push(busy),
                    setMessage: (message, isError) => window.prepareFixture.messages.push({ message, isError })
                }
            }).then((result) => {
                window.prepareFixture.result = result;
                return result;
            });
        }""",
        prepare_outcome,
    )


def exercise_success(page: Page, timeout_ms: int) -> None:
    install_workflow_fixture(page)
    page.wait_for_selector('[data-role="docs-viewer-management-modal"]', timeout=timeout_ms)
    if page.locator('[data-role="docs-viewer-management-modal"] input[type="checkbox"]').count() != 1:
        raise AssertionError("compact Prepare workflow should render only the descendants option checkbox")
    if page.locator("[data-package-profile]").count() != 1:
        raise AssertionError("Prepare workflow did not render its profile control")
    page.locator("[data-package-target-format]").select_option("json")
    page.locator("[data-package-content-format]").select_option("plain_text")
    page.locator("[data-package-context-details]").evaluate("details => { details.open = true; }")
    page.locator("[data-package-context-task]").fill("Review selected docs")
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_selector(
        '[data-role="docs-viewer-management-modal"] h2:text("Document package prepared")',
        timeout=timeout_ms,
    )
    result_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    for expected_text in (
        "Prepared package with 4 document(s).",
        "exported",
        "/packages/output.json",
        "One field was truncated.",
    ):
        if expected_text not in result_text:
            raise AssertionError(f"Prepare result omitted {expected_text!r}: {result_text!r}")
    page.locator('[data-role="modal-primary"]').click()
    result = page.evaluate(
        """async () => {
            await window.prepareWorkflowPromise;
            return window.prepareFixture;
        }"""
    )
    prepare_calls = [call for call in result["calls"] if call["method"] == "prepare"]
    context_calls = [call for call in result["calls"] if call["method"] == "context"]
    if len(prepare_calls) != 1 or len(context_calls) != 1:
        raise AssertionError(f"unexpected Prepare workflow calls: {result['calls']!r}")
    request = prepare_calls[0]["payload"]
    if request["doc_ids"] != ["root", "child", "grandchild", "sibling"]:
        raise AssertionError(f"unexpected expanded checked ids: {request!r}")
    if request["select_all"] is not False or request["target_format"] != "json":
        raise AssertionError(f"unexpected package request options: {request!r}")
    if request["content_format"] != "plain_text" or request["activity_context"] != {}:
        raise AssertionError(f"unexpected package request context: {request!r}")
    if context_calls[0]["payload"]["external_context"]["task"] != "Review selected docs":
        raise AssertionError(f"context edit was not saved: {context_calls!r}")
    if result["selection"] != ["root", "sibling"]:
        raise AssertionError(f"workflow mutated checkbox selection: {result!r}")
    if result["busy"] != [True, False, True, False]:
        raise AssertionError(f"unexpected ready/busy projection: {result['busy']!r}")
    if result["result"]["ok"] is not True:
        raise AssertionError(f"unexpected successful workflow result: {result['result']!r}")


def exercise_failure(page: Page, timeout_ms: int) -> None:
    install_workflow_fixture(page, "failure")
    page.wait_for_selector('[data-role="docs-viewer-management-modal"]', timeout=timeout_ms)
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_selector(
        '[data-role="docs-viewer-management-modal"] h2:text("Document package was not prepared")',
        timeout=timeout_ms,
    )
    result_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    if "Package write failed." not in result_text or "No package was written." not in result_text:
        raise AssertionError(f"Prepare failure detail was not retained: {result_text!r}")
    page.locator('[data-role="modal-primary"]').click()
    result = page.evaluate(
        """async () => {
            await window.prepareWorkflowPromise;
            return window.prepareFixture;
        }"""
    )
    if result["result"]["ok"] is not False or result["selection"] != ["root", "sibling"]:
        raise AssertionError(f"unexpected failed workflow result: {result!r}")


def exercise_cancel(page: Page, timeout_ms: int) -> None:
    install_workflow_fixture(page)
    page.wait_for_selector('[data-role="docs-viewer-management-modal"]', timeout=timeout_ms)
    page.locator('[data-role="modal-cancel"]').last.click()
    result = page.evaluate(
        """async () => {
            await window.prepareWorkflowPromise;
            return window.prepareFixture;
        }"""
    )
    if any(call["method"] in {"context", "prepare"} for call in result["calls"]):
        raise AssertionError(f"cancelled workflow should not write: {result['calls']!r}")
    if result["selection"] != ["root", "sibling"] or result["result"] != {"confirmed": False}:
        raise AssertionError(f"cancelled workflow changed state: {result!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", type=Path, default=Path.cwd())
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_static_server(args.site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            setup_page(page, base_url, args.timeout_ms)
            assert_prepare_model(page)
            assert_prepare_action_router(page)
            exercise_success(page, args.timeout_ms)
            exercise_failure(page, args.timeout_ms)
            exercise_cancel(page, args.timeout_ms)
            browser.close()
            if errors:
                raise AssertionError(f"page errors: {errors!r}")
    finally:
        server.shutdown()
        server.server_close()
    print("Docs Viewer Prepare package workflow modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

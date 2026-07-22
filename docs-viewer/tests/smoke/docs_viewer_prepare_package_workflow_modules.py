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
                { doc_id: 'root', parent_id: '', selectable: true, viewable: true, summary: '' },
                { doc_id: 'child', parent_id: 'root', selectable: true, viewable: false, summary: '' },
                { doc_id: 'grandchild', parent_id: 'child', selectable: true, viewable: true, summary: 'Existing' },
                { doc_id: 'sibling', parent_id: '', selectable: true, viewable: false, summary: '' },
                { doc_id: 'blocked', parent_id: 'root', selectable: false, viewable: false, summary: '' }
            ];
            const contentProfile = {
                profile_id: 'document-content',
                target_format: 'jsonl',
                supported_target_formats: ['jsonl', 'json'],
                content_format: 'markdown',
                supported_content_formats: ['markdown', 'plain_text'],
                record_shape: 'document_rows',
                selection: {
                    include_descendants: true,
                    include_non_viewable: true,
                    supports_include_non_viewable: true,
                    supports_missing_summary_only: true,
                    default_missing_summary_only: false
                },
                limits: { max_documents: null },
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
                record_shape: 'document_tree',
                selection: {
                    include_descendants: true,
                    include_non_viewable: true,
                    supports_include_non_viewable: false,
                    supports_missing_summary_only: false,
                    default_missing_summary_only: false
                }
            };
            const filteredProjection = model.projectDocumentPackageSelection({
                profile: contentProfile,
                documents,
                checkedDocIds: ['root', 'sibling'],
                includeDescendants: true,
                missingSummaryOnly: true,
                includeNonViewable: false
            });
            const limitedProjection = model.projectDocumentPackageSelection({
                profile: { ...contentProfile, limits: { max_documents: 2 } },
                documents,
                checkedDocIds: ['root', 'sibling'],
                includeDescendants: true,
                missingSummaryOnly: false,
                includeNonViewable: true
            });
            const treeProjection = model.projectDocumentPackageSelection({
                profile: treeProfile,
                documents,
                checkedDocIds: ['root'],
                includeDescendants: false,
                missingSummaryOnly: true,
                includeNonViewable: false
            });
            let ineligibleMessage = '';
            try {
                model.createDocumentPackagePrepareRequest({
                    scope: 'studio',
                    profile: contentProfile,
                    documents,
                    effectiveDocIds: ['blocked'],
                    missingSummaryOnly: false,
                    includeNonViewable: true
                });
            } catch (error) {
                ineligibleMessage = error.message;
            }
            return {
                descendants: model.documentPackageDescendantIds(documents, 'root'),
                eligibility: model.documentPackageSelectionEligibility(documents, ['root', 'blocked']),
                expanded: model.expandDocumentPackageSelection(documents, ['root', 'sibling'], true),
                filteredProjection,
                limitedProjection,
                treeProjection,
                exactRequest: model.createDocumentPackagePrepareRequest({
                    scope: 'STUDIO',
                    profile: contentProfile,
                    documents,
                    effectiveDocIds: filteredProjection.docIds,
                    missingSummaryOnly: filteredProjection.missingSummaryOnly,
                    includeNonViewable: filteredProjection.includeNonViewable,
                    targetFormat: 'json',
                    contentFormat: 'plain_text'
                }),
                treeRequest: model.createDocumentPackagePrepareRequest({
                    scope: 'studio',
                    profile: treeProfile,
                    documents,
                    effectiveDocIds: treeProjection.docIds,
                    missingSummaryOnly: treeProjection.missingSummaryOnly,
                    includeNonViewable: treeProjection.includeNonViewable
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
        "filteredProjection": {
            "docIds": ["root"],
            "includeDescendants": True,
            "missingSummaryOnly": True,
            "includeNonViewable": False,
            "supportsMissingSummaryOnly": True,
            "supportsIncludeNonViewable": True,
            "total": 1,
            "excludedNonViewableCount": 2,
            "excludedWithSummaryCount": 1,
            "excludedByLimitCount": 0,
            "includedNonViewableCount": 0,
        },
        "limitedProjection": {
            "docIds": ["root", "child"],
            "includeDescendants": True,
            "missingSummaryOnly": False,
            "includeNonViewable": True,
            "supportsMissingSummaryOnly": True,
            "supportsIncludeNonViewable": True,
            "total": 2,
            "excludedNonViewableCount": 0,
            "excludedWithSummaryCount": 0,
            "excludedByLimitCount": 2,
            "includedNonViewableCount": 1,
        },
        "treeProjection": {
            "docIds": ["root", "child", "grandchild"],
            "includeDescendants": True,
            "missingSummaryOnly": False,
            "includeNonViewable": True,
            "supportsMissingSummaryOnly": False,
            "supportsIncludeNonViewable": False,
            "total": 3,
            "excludedNonViewableCount": 0,
            "excludedWithSummaryCount": 0,
            "excludedByLimitCount": 0,
            "includedNonViewableCount": 1,
        },
        "exactRequest": {
            "scope": "studio",
            "profile_id": "document-content",
            "doc_ids": ["root"],
            "select_all": False,
            "missing_summary_only": True,
            "include_non_viewable": False,
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
            "missing_summary_only": False,
            "include_non_viewable": True,
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
        "ineligibleMessage": "Target documents are unavailable for package preparation: blocked",
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
            const zeroTarget = prepareOutcome === 'zero';
            const contentProfile = {
                profile_id: 'document-content',
                label: 'Document content',
                supports_return_import: true,
                description: 'Document summaries and content.',
                target_format: 'jsonl',
                supported_target_formats: ['jsonl', 'json'],
                content_format: 'markdown',
                supported_content_formats: ['markdown', 'plain_text'],
                record_shape: 'document_rows',
                selection: {
                    include_descendants: true,
                    include_non_viewable: true,
                    supports_include_non_viewable: true,
                    supports_missing_summary_only: true,
                    default_missing_summary_only: false
                },
                limits: { max_documents: null },
                external_context: {
                    task: 'Review',
                    response_guidance: 'Return changes',
                    field_descriptions: { doc_id: 'Stable id', content: 'Body' }
                },
                document_fields: [{ output_path: 'doc_id' }, { output_path: 'content' }]
            };
            const profiles = [contentProfile, {
                ...contentProfile,
                profile_id: 'document-tree',
                label: 'Document tree',
                supports_return_import: false,
                description: 'Document hierarchy.',
                target_format: 'json',
                supported_target_formats: ['json'],
                content_format: '',
                supported_content_formats: [],
                record_shape: 'document_tree',
                selection: {
                    include_descendants: true,
                    include_non_viewable: true,
                    supports_include_non_viewable: false,
                    supports_missing_summary_only: false,
                    default_missing_summary_only: false
                }
            }];
            const documents = [
                { doc_id: 'root', parent_id: '', title: 'Root', selectable: true, viewable: true, summary: zeroTarget ? 'Done' : '' },
                { doc_id: 'child', parent_id: 'root', title: 'Child', selectable: true, viewable: false, summary: zeroTarget ? 'Done' : '' },
                { doc_id: 'grandchild', parent_id: 'child', title: 'Grandchild', selectable: true, viewable: true, summary: 'Done' },
                { doc_id: 'sibling', parent_id: '', title: 'Sibling', selectable: true, viewable: false, summary: zeroTarget ? 'Done' : '' }
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
                            counts: {
                                selected: payload.doc_ids.length,
                                exported: 0,
                                failed: payload.doc_ids.length,
                                skipped: 0
                            },
                            warnings: ['No package was written.']
                        };
                        throw error;
                    }
                    const count = payload.doc_ids.length;
                    return {
                        ok: true,
                        summary_text: `Prepared package with ${count} document(s).`,
                        counts: { truncated: 0, skipped: 0, failed: 0, exported: count, selected: count },
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
                activityContext: {
                    page_id: 'docs-manage',
                    action_id: 'prepare-document-package',
                    route: '/docs/',
                    control_id: 'docsViewerManagePreparePackageButton',
                    control_selector: '#docsViewerManagePreparePackageButton',
                    correlation_id: 'prepare:test'
                },
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
    if page.locator('[data-role="docs-viewer-management-modal"] input[type="checkbox"]').count() != 3:
        raise AssertionError("Prepare workflow did not render the three content-profile choices")
    if page.locator("[data-package-profile]").count() != 1:
        raise AssertionError("Prepare workflow did not render its profile control")
    profile_labels = page.locator("[data-package-profile] option").all_text_contents()
    if profile_labels != ["Document content", "Document tree (export only)"]:
        raise AssertionError(f"Prepare workflow projected unexpected profile labels: {profile_labels!r}")
    modal_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    if "checked document" in modal_text:
        raise AssertionError(f"Prepare workflow retained the raw checked-count note: {modal_text!r}")
    if "Total documents to be prepared: 4" not in modal_text:
        raise AssertionError(f"Prepare workflow omitted the initial effective total: {modal_text!r}")
    if "2 non-viewable documents included." not in modal_text:
        raise AssertionError(f"Prepare workflow omitted included non-viewable detail: {modal_text!r}")

    page.locator("[data-package-include-descendants]").uncheck()
    descendants_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    if "Total documents to be prepared: 2" not in descendants_text:
        raise AssertionError(f"descendant choice did not recalculate the total: {descendants_text!r}")
    page.locator("[data-package-include-descendants]").check()

    page.locator("[data-package-missing-summary-only]").check()
    filtered_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    if "Total documents to be prepared: 3" not in filtered_text:
        raise AssertionError(f"missing-summary choice did not recalculate the total: {filtered_text!r}")
    if "1 document excluded because it already has a summary." not in filtered_text:
        raise AssertionError(f"missing-summary exclusion was not explained: {filtered_text!r}")

    page.locator("[data-package-include-non-viewable]").uncheck()
    filtered_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    if "Total documents to be prepared: 1" not in filtered_text:
        raise AssertionError(f"non-viewable choice did not recalculate the total: {filtered_text!r}")
    if "2 non-viewable documents excluded." not in filtered_text:
        raise AssertionError(f"non-viewable exclusions were not explained: {filtered_text!r}")

    page.locator("[data-package-profile]").select_option("document-tree")
    tree_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    if "Total documents to be prepared: 4" not in tree_text:
        raise AssertionError(f"tree profile did not retain its complete target: {tree_text!r}")
    if not page.locator("[data-package-missing-summary-field]").is_hidden():
        raise AssertionError("tree profile exposed the unsupported missing-summary choice")
    if not page.locator("[data-package-include-non-viewable-field]").is_hidden():
        raise AssertionError("tree profile exposed the unsupported non-viewable choice")

    page.locator("[data-package-profile]").select_option("document-content")
    if not page.locator("[data-package-missing-summary-only]").is_checked():
        raise AssertionError("content profile lost its missing-summary choice after profile switching")
    if page.locator("[data-package-include-non-viewable]").is_checked():
        raise AssertionError("content profile lost its non-viewable choice after profile switching")
    restored_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    if "Total documents to be prepared: 1" not in restored_text:
        raise AssertionError(f"profile switching did not restore the effective target: {restored_text!r}")

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
        "Prepared package with 1 document(s).",
        "exported",
        "/packages/output.json",
        "One field was truncated.",
    ):
        if expected_text not in result_text:
            raise AssertionError(f"Prepare result omitted {expected_text!r}: {result_text!r}")
    count_labels = page.locator(".docsViewerPackagePrepare__counts dt").all_text_contents()
    if count_labels != ["selected", "exported", "failed", "skipped", "truncated"]:
        raise AssertionError(f"Prepare result count order changed: {count_labels!r}")
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
    if request["doc_ids"] != ["root"]:
        raise AssertionError(f"request did not use the final effective target: {request!r}")
    if request["select_all"] is not False or request["target_format"] != "json":
        raise AssertionError(f"unexpected package request options: {request!r}")
    if (
        request["content_format"] != "plain_text"
        or request["missing_summary_only"] is not True
        or request["include_non_viewable"] is not False
        or request["activity_context"]["page_id"] != "docs-manage"
        or request["activity_context"]["control_id"] != "docsViewerManagePreparePackageButton"
    ):
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


def exercise_zero_target(page: Page, timeout_ms: int) -> None:
    install_workflow_fixture(page, "zero")
    page.wait_for_selector('[data-role="docs-viewer-management-modal"]', timeout=timeout_ms)
    page.locator("[data-package-missing-summary-only]").check()
    modal_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    if "Total documents to be prepared: 0" not in modal_text:
        raise AssertionError(f"zero-target total was not shown: {modal_text!r}")
    if "4 documents excluded because they already have summaries." not in modal_text:
        raise AssertionError(f"zero-target filter reason was not shown: {modal_text!r}")
    if "No documents remain after applying the selected package filters." not in modal_text:
        raise AssertionError(f"zero-target explanation was not shown: {modal_text!r}")
    if not page.locator('[data-role="modal-primary"]').is_disabled():
        raise AssertionError("Prepare package remained enabled for a zero target")
    page.locator('[data-role="modal-cancel"]').last.click()
    result = page.evaluate(
        """async () => {
            await window.prepareWorkflowPromise;
            return window.prepareFixture;
        }"""
    )
    if any(call["method"] == "prepare" for call in result["calls"]):
        raise AssertionError(f"zero-target workflow submitted a request: {result['calls']!r}")


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
            exercise_zero_target(page, args.timeout_ms)
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

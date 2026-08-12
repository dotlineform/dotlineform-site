#!/usr/bin/env python3
"""Smoke-check generalized Copy/Move client and compact transfer workflow."""

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

    def translate_path(self, path: str) -> str:
        if path.startswith("/docs-viewer/runtime/js/shared/"):
            path = "/site" + path
        return super().translate_path(path)


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    handler = partial(
        QuietStaticHandler,
        directory=str(site_root.expanduser().resolve()),
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_transfer_workflow(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const workflow = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-document-transfer-workflow.js'
            );
            const indexManagement = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-index-controller.js'
            );
            const definitions = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-action-definitions.js'
            );
            document.body.innerHTML = `
              <main id="root">
                <button id="restore" type="button">Index actions</button>
              </main>`;
            const root = document.querySelector('#root');
            const restore = document.querySelector('#restore');
            restore.focus();
            const requests = [];
            const messages = [];
            const busy = [];
            let appliedPayload = null;
            let transferError = '';
            const response = payload => Promise.resolve(new Response(
                JSON.stringify(payload),
                {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' }
                }
            ));
            const fetch = (url, options) => {
                const body = JSON.parse(options.body);
                requests.push({ url, method: options.method, body });
                if (url.endsWith('/docs/document-transfer-preview')) {
                    return response({
                        schema_version: 'docs_document_transfer_preview_v4',
                        ok: true,
                        mode: body.transfer_mode,
                        source: { scope: body.scope },
                        target: {
                            scope: body.target_scope,
                            sub_scope: body.target_sub_scope,
                            placement: 'sub_scope_root'
                        },
                        target_default_publishable: true,
                        custom_metadata: {
                            retained: [],
                            omitted: [{ field: 'project_status' }],
                            rejected: []
                        },
                        document_count: 3,
                        effective_root_count: 2,
                        descendant_count: 1,
                        unique_media_count: 2,
                        retained_external_dependencies: [
                            { kind: 'url', reference: 'https://example.test/media.png' }
                        ],
                        media: [
                            {
                                identity: 'diagram.svg',
                                build_sources: [{ source_identity: 'diagram.mmd' }]
                            },
                            { identity: 'photo.png', build_sources: [] }
                        ],
                        blockers: [],
                        apply_plan: {
                            schema_version: 'docs_document_transfer_apply_plan_v4',
                            mode: body.transfer_mode,
                            source: { scope: body.scope },
                            target: {
                                scope: body.target_scope,
                                sub_scope: body.target_sub_scope
                            }
                        }
                    });
                }
                return response({
                    ok: true,
                    summary_text: 'Copied 3 documents.',
                    effective_roots: [
                        { target_viewer_url: '/docs/?scope=notes&doc=copied-a' }
                    ]
                });
            };
            const waitFor = async predicate => {
                for (let attempt = 0; attempt < 50; attempt += 1) {
                    if (transferError) throw new Error(transferError);
                    const value = predicate();
                    if (value) return value;
                    await new Promise(resolve => setTimeout(resolve, 0));
                }
                throw new Error('Timed out waiting for transfer workflow state.');
            };
            const transferPromise = workflow.openDocumentTransferWorkflow({
                root,
                restoreFocus: restore,
                source: { scope: 'studio' },
                mode: 'copy',
                checkedDocIds: ['checked-a', 'checked-b'],
                targets: [
                    {
                        target: { scope: 'analysis', sub_scope: 'works' },
                        label: 'analysis / Works'
                    },
                    { target: { scope: 'processing' }, label: 'processing' }
                ],
                copyDescendantsAvailable: true,
                clientOptions: {
                    baseUrl: 'http://manage.test',
                    scope: 'studio',
                    fetch
                },
                callbacks: {
                    setBusy: value => busy.push(value),
                    setMessage: (message, isError) => messages.push({ message, isError }),
                    render: () => {},
                    onApplied: payload => { appliedPayload = payload; }
                }
            }).catch(error => {
                transferError = error?.message || String(error);
                throw error;
            });
            const optionsTitle = await waitFor(
                () => document.querySelector('.docsViewer__modalTitle')
            );
            await waitFor(
                () => document.activeElement?.dataset.role === 'modal-cancel'
            );
            const optionsState = {
                title: optionsTitle.textContent,
                focusedRole: document.activeElement?.dataset.role || '',
                targetValues: Array.from(
                    document.querySelectorAll('input[name="docsViewerDocumentTransferTarget"]')
                ).map(input => input.value),
                firstTargetChecked: document.querySelector(
                    'input[name="docsViewerDocumentTransferTarget"]'
                ).checked,
                hasDescendantsChoice: Boolean(document.querySelector(
                    '[data-role="document-transfer-descendants"]'
                ))
            };
            document.querySelector('[data-role="document-transfer-descendants"]').click();
            document.querySelector('[data-role="modal-primary"]').click();
            await waitFor(
                () => document.querySelector('.docsViewer__modalTitle')?.textContent === 'Confirm copy'
            );
            await waitFor(
                () => document.activeElement?.dataset.role === 'modal-cancel'
            );
            const confirmation = {
                focusedRole: document.activeElement?.dataset.role || '',
                body: Array.from(document.querySelectorAll('.docsViewer__modalBody p'))
                    .map(node => node.textContent),
                bold: Array.from(document.querySelectorAll('.docsViewer__modalBody strong'))
                    .map(node => node.textContent),
                primaryDisabled: document.querySelector('[data-role="modal-primary"]').disabled
            };
            document.querySelector('[data-role="modal-primary"]').click();
            const applied = await transferPromise;

            const blockedRequests = [];
            const blockedPromise = workflow.openDocumentTransferWorkflow({
                root,
                restoreFocus: restore,
                source: { scope: 'studio' },
                mode: 'move',
                checkedDocIds: ['checked-a'],
                targets: [{ target: { scope: 'notes' }, label: 'notes' }],
                clientOptions: {
                    baseUrl: 'http://manage.test',
                    scope: 'studio',
                    fetch: (url, options) => {
                        const body = JSON.parse(options.body);
                        blockedRequests.push({ url, body });
                        return response({
                            ok: false,
                            mode: 'move',
                            source: { scope: 'studio' },
                            target: { scope: 'notes', placement: 'scope_root' },
                            document_count: 1,
                            effective_root_count: 1,
                            descendant_count: 0,
                            unique_media_count: 0,
                            retained_external_dependencies: [],
                            media: [],
                            blockers: [{ code: 'inbound_link', message: 'An outside document links here.' }],
                            apply_plan: null
                        });
                    }
                }
            });
            await waitFor(
                () => document.querySelector('.docsViewer__modalTitle')?.textContent === 'Move to scope'
            );
            const moveOptions = {
                hasDescendantsChoice: Boolean(document.querySelector(
                    '[data-role="document-transfer-descendants"]'
                )),
                impactNote: Array.from(document.querySelectorAll('.docsViewer__modalBody p'))
                    .map(node => node.textContent)
                    .find(text => text.includes('always includes every descendant')) || ''
            };
            document.querySelector('[data-role="modal-primary"]').click();
            await waitFor(
                () => document.querySelector('.docsViewer__modalTitle')?.textContent === 'Confirm move'
            );
            const blockedConfirmation = {
                primaryDisabled: document.querySelector('[data-role="modal-primary"]').disabled,
                body: Array.from(document.querySelectorAll('.docsViewer__modalBody p'))
                    .map(node => node.textContent),
                bold: Array.from(document.querySelectorAll('.docsViewer__modalBody strong'))
                    .map(node => node.textContent)
            };
            document.querySelector('[data-role="modal-cancel"]').click();
            const blockedResult = await blockedPromise;
            const blockedFocusRestored = document.activeElement === restore;

            const lineageRequests = [];
            const lineageFetch = (url, options) => {
                const body = JSON.parse(options.body);
                lineageRequests.push({ url, body });
                if (url.endsWith('/docs/document-transfer-apply')) {
                    return response({
                        ok: true,
                        summary_text: 'Copied 1 document (0 New, 1 Replace).',
                        effective_roots: [{
                            target_viewer_url: '/docs/?scope=analysis&doc=host&subdoc=editorial-b'
                        }]
                    });
                }
                const decided = Array.isArray(body.copy_lineage_actions);
                return response({
                    schema_version: 'docs_document_transfer_preview_v4',
                    ok: decided,
                    mode: 'copy',
                    source: { scope: 'dotlineform', sub_scope: 'projects' },
                    target: {
                        scope: 'analysis',
                        sub_scope: 'works',
                        placement: 'sub_scope_root'
                    },
                    target_default_publishable: true,
                    custom_metadata: { retained: [], omitted: [], rejected: [] },
                    document_count: 1,
                    effective_root_count: 1,
                    descendant_count: 0,
                    unique_media_count: 0,
                    retained_external_dependencies: [],
                    media: [],
                    warnings: [],
                    blockers: decided ? [] : [{
                        code: 'lineage_copy_action_required',
                        message: 'choose New or one exact Replace target'
                    }],
                    lineage: {
                        contract_id: 'dotlineform_projects_to_analysis_works',
                        choice_required: !decided,
                        sources: [{
                            source_doc_id: 'working-a',
                            title: 'Working A',
                            action: decided ? body.copy_lineage_actions[0].action : '',
                            replace_target_doc_id: decided
                                ? body.copy_lineage_actions[0].replace_target_doc_id
                                : '',
                            existing_editorials: [{
                                editorial_doc_id: 'editorial-b',
                                title: 'Editorial B',
                                available: true
                            }, {
                                editorial_doc_id: 'missing-b',
                                title: '',
                                available: false
                            }]
                        }]
                    },
                    apply_plan: decided ? {
                        schema_version: 'docs_document_transfer_apply_plan_v4',
                        mode: 'copy',
                        source: { scope: 'dotlineform', sub_scope: 'projects' },
                        target: { scope: 'analysis', sub_scope: 'works' }
                    } : null
                });
            };
            const lineagePromise = workflow.openDocumentTransferWorkflow({
                root,
                restoreFocus: restore,
                source: { scope: 'dotlineform', sub_scope: 'projects' },
                mode: 'copy',
                checkedDocIds: ['working-a'],
                targets: [{
                    target: { scope: 'analysis', sub_scope: 'works' },
                    label: 'analysis / Works'
                }],
                clientOptions: {
                    baseUrl: 'http://manage.test',
                    scope: 'dotlineform',
                    fetch: lineageFetch
                }
            });
            await waitFor(
                () => document.querySelector('.docsViewer__modalTitle')?.textContent === 'Copy to…'
            );
            document.querySelector('[data-role="modal-primary"]').click();
            await waitFor(
                () => document.querySelector('.docsViewer__modalTitle')?.textContent === 'Choose New or Replace'
            );
            await waitFor(
                () => document.activeElement?.dataset.role === 'modal-cancel'
            );
            const lineageChoice = {
                focusedRole: document.activeElement?.dataset.role || '',
                labels: Array.from(document.querySelectorAll('.docsViewer__fieldLabel'))
                    .map(node => node.textContent),
                checkedCount: document.querySelectorAll(
                    'input[name="docsViewerDocumentLineageAction-0"]:checked'
                ).length
            };
            document.querySelector(
                'input[name="docsViewerDocumentLineageAction-0"][value="replace:0"]'
            ).click();
            document.querySelector('[data-role="modal-primary"]').click();
            await waitFor(
                () => document.querySelector('.docsViewer__modalTitle')?.textContent === 'Confirm copy'
            );
            const lineageConfirmation = {
                primaryLabel: document.querySelector('[data-role="modal-primary"]').textContent,
                body: Array.from(document.querySelectorAll('.docsViewer__modalBody p'))
                    .map(node => node.textContent)
            };
            document.querySelector('[data-role="modal-primary"]').click();
            const lineageApplied = await lineagePromise;

            const transferCapabilities = {
                document_transfer: { preview: true, apply: true },
                scopes: {
                    studio: {
                        available: true,
                        document_transfer: {
                            copy_source: true,
                            move_source: true,
                            target: true,
                            collections: [{
                                target: { scope: 'studio' },
                                label: 'studio',
                                copy_source: true,
                                move_source: true,
                                copy_target: true,
                                move_target: true
                            }]
                        }
                    },
                    notes: {
                        available: true,
                        document_transfer: {
                            copy_source: true,
                            move_source: true,
                            target: true,
                            collections: [{
                                target: { scope: 'notes' },
                                label: 'notes',
                                copy_source: true,
                                move_source: true,
                                copy_target: true,
                                move_target: true
                            }]
                        }
                    }
                }
            };
            const warningPreview = {
                ok: true,
                mode: 'move',
                source: { scope: 'studio' },
                target: { scope: 'notes', placement: 'scope_root' },
                document_count: 1,
                effective_root_count: 1,
                descendant_count: 0,
                unique_media_count: 0,
                retained_external_dependencies: [],
                media: [],
                blockers: [],
                warnings: [{
                    code: 'inbound_viewer_link',
                    message: '“Docs Viewer Roadmap” links to “Local Tree Move Projection”.'
                }, {
                    code: 'inbound_viewer_link',
                    message: '“Button Placement” links to “Local Tree Move Projection”.'
                }, {
                    code: 'retained_dependency',
                    message: 'An unrelated dependency will remain unchanged.'
                }],
                apply_plan: { schema_version: 'docs_document_transfer_apply_plan_v4' }
            };
            return {
                optionsState,
                confirmation,
                requests,
                applied,
                appliedPayload,
                busy,
                messages,
                focusRestored: blockedFocusRestored,
                moveOptions,
                blockedConfirmation,
                blockedRequests,
                blockedResult,
                lineageRequests,
                lineageChoice,
                lineageConfirmation,
                lineageApplied,
                warningConfirmation: workflow.buildDocumentTransferConfirmationBody(
                    warningPreview
                ),
                singleWarningConfirmation: workflow.buildDocumentTransferConfirmationBody({
                    ...warningPreview,
                    warnings: [warningPreview.warnings[0]]
                }),
                warningCanApply: workflow.documentTransferPreviewCanApply(warningPreview),
                stateContract: {
                    empty: indexManagement.docsViewerDocumentTransferActionControlState({
                        mode: 'copy',
                        capabilities: transferCapabilities,
                        managementAvailable: true,
                        managementBusy: false,
                        managementChecked: true,
                        resolution: definitions.resolveDocsViewerAction(
                            'copy',
                            definitions.createDocsViewerActionContext({ activeDocId: 'active' })
                        ),
                        source: { scope: 'studio' },
                        targets: [{ target: { scope: 'notes' }, label: 'notes' }]
                    }),
                    ready: indexManagement.docsViewerDocumentTransferActionControlState({
                        mode: 'move',
                        capabilities: transferCapabilities,
                        managementAvailable: true,
                        managementBusy: false,
                        managementChecked: true,
                        resolution: definitions.resolveDocsViewerAction(
                            'move',
                            definitions.createDocsViewerActionContext({
                                activeDocId: 'active',
                                selectedDocIds: ['checked-a']
                            })
                        ),
                        source: { scope: 'studio' },
                        targets: [{ target: { scope: 'notes' }, label: 'notes' }]
                    })
                }
            };
        }"""
    )

    if result["optionsState"] != {
        "title": "Copy to…",
        "focusedRole": "modal-cancel",
        "targetValues": ["0", "1"],
        "firstTargetChecked": True,
        "hasDescendantsChoice": True,
    }:
        raise AssertionError(f"unexpected Copy options state: {result['optionsState']!r}")
    if result["confirmation"] != {
        "focusedRole": "modal-cancel",
        "body": [
            "Copy 3 documents to analysis / works",
            "includes 2 media",
            "New documents will be included in the next Publish.",
            "1 custom metadata field will be omitted because the target does not support it.",
        ],
        "bold": ["3", "analysis / works", "2"],
        "primaryDisabled": False,
    }:
        raise AssertionError(f"unexpected Copy confirmation: {result['confirmation']!r}")
    expected_requests = [
        {
            "url": "http://manage.test/docs/document-transfer-preview",
            "method": "POST",
            "body": {
                "scope": "studio",
                "doc_ids": ["checked-a", "checked-b"],
                "target_scope": "analysis",
                "target_sub_scope": "works",
                "transfer_mode": "copy",
                "include_descendants": True,
            },
        },
        {
            "url": "http://manage.test/docs/document-transfer-apply",
            "method": "POST",
            "body": {
                "scope": "studio",
                "apply_plan": {
                    "schema_version": "docs_document_transfer_apply_plan_v4",
                    "mode": "copy",
                    "source": {"scope": "studio"},
                    "target": {"scope": "analysis", "sub_scope": "works"},
                },
                "confirm": True,
            },
        },
    ]
    if result["requests"] != expected_requests:
        raise AssertionError(f"unexpected transfer requests: {result['requests']!r}")
    if result["applied"] != result["appliedPayload"]:
        raise AssertionError("applied callback did not receive the exact service result")
    if result["busy"] != [True, False, True, False]:
        raise AssertionError(f"unexpected busy projection: {result['busy']!r}")
    if result["moveOptions"] != {
        "hasDescendantsChoice": False,
        "impactNote": "Move always includes every descendant of each checked document.",
    }:
        raise AssertionError(f"unexpected Move options: {result['moveOptions']!r}")
    if not result["blockedConfirmation"]["primaryDisabled"]:
        raise AssertionError("blocked transfer confirmation enabled its primary action")
    if result["blockedConfirmation"]["body"][:2] != [
        "Move 1 document to notes",
        "includes 0 media",
    ] or result["blockedConfirmation"]["bold"] != ["1", "notes", "0"]:
        raise AssertionError(
            f"unexpected Move confirmation summary: {result['blockedConfirmation']!r}"
        )
    if not any(
        line == "Blocked: An outside document links here."
        for line in result["blockedConfirmation"]["body"]
    ):
        raise AssertionError(
            f"blocked transfer omitted its reason: {result['blockedConfirmation']!r}"
        )
    if len(result["blockedRequests"]) != 1:
        raise AssertionError("blocked transfer attempted an apply request")
    if result["blockedRequests"][0]["body"]["include_descendants"] is not False:
        raise AssertionError("Move client request unexpectedly invented a descendant choice")
    if result["blockedResult"] is not None or not result["focusRestored"]:
        raise AssertionError("cancelled blocked transfer did not restore focus")
    if result["lineageChoice"] != {
        "focusedRole": "modal-cancel",
        "labels": [
            "New editorial copy",
            "Replace Editorial B (editorial-b)",
            "Unavailable editorial target (missing-b)",
        ],
        "checkedCount": 0,
    }:
        raise AssertionError(
            f"unexpected lineage choice state: {result['lineageChoice']!r}"
        )
    if result["lineageConfirmation"]["primaryLabel"] != "Replace selected documents":
        raise AssertionError(
            f"Replace confirmation lost its destructive label: "
            f"{result['lineageConfirmation']!r}"
        )
    if not any(
        "Replace editorial-b from working-a" in line
        for line in result["lineageConfirmation"]["body"]
    ):
        raise AssertionError(
            f"Replace confirmation omitted exact identities: "
            f"{result['lineageConfirmation']!r}"
        )
    if any(
        "New documents will be included" in line
        for line in result["lineageConfirmation"]["body"]
    ):
        raise AssertionError(
            f"Replace confirmation claimed New publication behavior: "
            f"{result['lineageConfirmation']!r}"
        )
    if len(result["lineageRequests"]) != 3:
        raise AssertionError(
            f"lineage workflow request count changed: {result['lineageRequests']!r}"
        )
    first_lineage_preview = result["lineageRequests"][0]["body"]
    decided_lineage_preview = result["lineageRequests"][1]["body"]
    if "copy_lineage_actions" in first_lineage_preview:
        raise AssertionError("initial lineage preview invented a New/Replace choice")
    if decided_lineage_preview.get("copy_lineage_actions") != [{
        "source_doc_id": "working-a",
        "action": "replace",
        "replace_target_doc_id": "editorial-b",
    }]:
        raise AssertionError(
            f"lineage workflow changed the exact choice: {decided_lineage_preview!r}"
        )
    if result["lineageApplied"].get("ok") is not True:
        raise AssertionError("lineage workflow did not return its exact apply result")
    if not result["warningCanApply"]:
        raise AssertionError("warning-only transfer was incorrectly blocked")
    aggregated_warning_lines = [
        line
        for line in result["warningConfirmation"]
        if "Docs Broken Links" in line
    ]
    if (
        len(aggregated_warning_lines) != 1
        or "2 broken links" not in aggregated_warning_lines[0]
        or "“studio”" not in aggregated_warning_lines[0]
        or "(doc archived)" not in aggregated_warning_lines[0]
    ):
        raise AssertionError(
            f"transfer confirmation omitted its inbound-link guidance: "
            f"{result['warningConfirmation']!r}"
        )
    if any(
        "Docs Viewer Roadmap" in line or "Button Placement" in line
        for line in result["warningConfirmation"]
    ):
        raise AssertionError(
            f"transfer confirmation did not aggregate inbound-link details: "
            f"{result['warningConfirmation']!r}"
        )
    if not any(
        "unrelated dependency" in line
        for line in result["warningConfirmation"]
    ):
        raise AssertionError(
            f"transfer confirmation omitted its unrelated warning: "
            f"{result['warningConfirmation']!r}"
        )
    singular_warning_lines = [
        line
        for line in result["singleWarningConfirmation"]
        if "Docs Broken Links" in line
    ]
    if (
        len(singular_warning_lines) != 1
        or "1 broken link" not in singular_warning_lines[0]
        or "that reference" not in singular_warning_lines[0]
        or "replace it" not in singular_warning_lines[0]
    ):
        raise AssertionError(
            f"transfer confirmation omitted its singular inbound-link guidance: "
            f"{result['singleWarningConfirmation']!r}"
        )
    if result["stateContract"] != {
        "empty": {
            "disabled": True,
            "disabledReason": "Select one or more documents.",
            "targets": [{"target": {"scope": "notes"}, "label": "notes"}],
        },
        "ready": {
            "disabled": False,
            "disabledReason": "",
            "targets": [{"target": {"scope": "notes"}, "label": "notes"}],
        },
    }:
        raise AssertionError(
            f"unexpected transfer action state: {result['stateContract']!r}"
        )


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
            page.goto(base_url, wait_until="domcontentloaded", timeout=args.timeout_ms)
            page.add_style_tag(
                url=f"{base_url}/site/docs-viewer/static/css/docs-viewer.css"
            )
            page.add_style_tag(
                url=f"{base_url}/docs-viewer/static/css/docs-viewer-manage.css"
            )
            assert_transfer_workflow(page)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    print("Docs Viewer document transfer workflow module smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

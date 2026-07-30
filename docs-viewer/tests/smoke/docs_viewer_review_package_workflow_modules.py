#!/usr/bin/env python3
"""Smoke-check Review package list projection and compact management workflow."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


class RuntimeStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        if path.startswith("/docs-viewer/runtime/js/shared/"):
            path = "/site" + path
        return super().translate_path(path)


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    handler = partial(RuntimeStaticHandler, directory=str(site_root.expanduser().resolve()))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def setup_page(page: Page, base_url: str, timeout_ms: int) -> None:
    page.goto(base_url, wait_until="domcontentloaded", timeout=timeout_ms)
    page.add_style_tag(url=f"{base_url}/site/docs-viewer/static/css/docs-viewer.css")
    page.add_style_tag(url=f"{base_url}/docs-viewer/static/css/docs-viewer-manage.css")


def assert_action_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const definitions = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-action-definitions.js'
            );
            const management = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management.js'
            );
            const routerModule = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-event-router.js'
            );
            const calls = [];
            const button = document.createElement('button');
            const ready = management.docsViewerReviewPackageActionControlState({
                capabilities: {
                    document_packages: { available: true, review_returned: true }
                },
                managementAvailable: true,
                managementBusy: false,
                managementChecked: true,
                scope: 'studio'
            });
            management.projectDocsViewerReviewPackageActionControl(button, ready);
            const router = routerModule.createDocsViewerManagementEventRouter({
                refs: {},
                commands: { reviewPackage: () => calls.push('reviewPackage') },
                controllers: { interaction: () => ({ hideContextMenu: () => calls.push('hideContextMenu') }) }
            });
            return {
                definition: definitions.getDocsViewerActionDefinition('review-document-package'),
                ready,
                unavailable: management.docsViewerReviewPackageActionControlState({
                    capabilities: {
                        document_packages: {
                            available: false,
                            message: 'Package workspace is offline.',
                            review_returned: false
                        }
                    },
                    managementAvailable: true,
                    managementBusy: false,
                    managementChecked: true,
                    scope: 'studio'
                }),
                button: {
                    disabled: button.disabled,
                    ariaLabel: button.getAttribute('aria-label'),
                    title: button.title
                },
                handled: router.handleAppManagementControl({
                    actionId: 'review-document-package',
                    eventType: 'click'
                }),
                calls
            };
        }"""
    )
    expected = {
        "definition": {"id": "review-document-package", "target": "scope"},
        "ready": {"disabled": False, "disabledReason": ""},
        "unavailable": {
            "disabled": True,
            "disabledReason": "Package workspace is offline.",
        },
        "button": {
            "disabled": False,
            "ariaLabel": "Review package",
            "title": "Review package",
        },
        "handled": True,
        "calls": ["hideContextMenu", "reviewPackage"],
    }
    if result != expected:
        raise AssertionError(f"unexpected Review package Action contract: {result!r}")


def install_workflow_fixture(
    page: Page,
    returned_scope: str = "studio",
    review_mode: str = "new",
) -> None:
    page.evaluate(
        """async ({ returnedScope, reviewMode }) => {
            const workflow = await import(
                '/docs-viewer/runtime/js/packages/document-package-review-workflow.js'
            );
            document.body.innerHTML = [
                '<main class="docsViewer" id="docsViewerRoot">',
                '  <button id="restoreFocus">Review package</button>',
                '</main>'
            ].join('');
            window.reviewFixture = { busy: [], calls: [], messages: [] };
            window.reviewWorkflowPromise = workflow.openDocumentPackageReviewWorkflow({
                root: document.querySelector('#docsViewerRoot'),
                scope: 'studio',
                restoreFocus: document.querySelector('#restoreFocus'),
                client: {
                    getConfig: async () => {
                        window.reviewFixture.calls.push({ method: 'config' });
                        return {
                            ok: true,
                            workspace: { available: true, message: '' },
                            scopes: [{ scope: 'studio', label: 'Studio' }]
                        };
                    },
                    getReturned: async (scope) => {
                        window.reviewFixture.calls.push({ method: 'returned', scope });
                        return {
                            ok: true,
                            scope: returnedScope,
                            files: [
                                {
                                    filename: 'alpha.jsonl',
                                    document_count: 2,
                                    supports_docs_review: true,
                                    supports_return_import: true,
                                    scope_label: 'Studio',
                                    sub_scope_label: ''
                                },
                                {
                                    filename: 'tree.json',
                                    document_count: 3,
                                    supports_docs_review: false,
                                    supports_return_import: false,
                                    scope_label: 'Studio',
                                    sub_scope_label: ''
                                },
                                {
                                    filename: 'missing-count.jsonl',
                                    supports_docs_review: true,
                                    supports_return_import: false,
                                    scope_label: 'Studio',
                                    sub_scope_label: 'Tags'
                                },
                                {
                                    filename: 'empty.jsonl',
                                    document_count: 0,
                                    supports_docs_review: true,
                                    supports_return_import: false,
                                    scope_label: 'Studio',
                                    sub_scope_label: 'Tags'
                                },
                                {
                                    filename: 'beta.jsonl',
                                    document_count: 1,
                                    supports_docs_review: true,
                                    supports_return_import: false,
                                    scope_label: 'Studio',
                                    sub_scope_label: 'Tags'
                                }
                            ],
                            blocked_files: [{ filename: 'blocked.jsonl' }],
                            unassigned_files: [{ filename: 'orphan.jsonl' }]
                        };
                    },
                    review: async (payload) => {
                        window.reviewFixture.calls.push({ method: 'review', payload });
                        if (reviewMode === 'failure') {
                            const error = new Error('Docs Review package was not prepared.');
                            error.payload = {
                                ok: false,
                                issues: [{
                                    level: 'error',
                                    code: 'review_package_identity_mismatch',
                                    message: 'Existing review identity does not match.'
                                }],
                                folder_path: '/private/workspace/must-not-be-exposed'
                            };
                            throw error;
                        }
                        return {
                            ok: true,
                            review_package_id: '20260722-204025-documents-document-content',
                            review_url: '/docs-review/?package=20260722-204025-documents-document-content',
                            review_existing: reviewMode === 'existing',
                            counts: { records: 1, valid_records: 1, errors: 0, warnings: 0 },
                            issues: [],
                            summary_text: reviewMode === 'existing'
                                ? 'Docs Review package already exists.'
                                : 'Prepared Docs Review package.'
                        };
                    }
                },
                callbacks: {
                    setBusy: (busy) => window.reviewFixture.busy.push(busy),
                    setMessage: (message, isError) => window.reviewFixture.messages.push({ message, isError })
                }
            }).then((result) => {
                window.reviewFixture.result = result;
                return result;
            });
        }""",
        {"returnedScope": returned_scope, "reviewMode": review_mode},
    )


def exercise_reviewable_list(page: Page, timeout_ms: int) -> None:
    canonical_links = page.evaluate(
        """async () => {
            const review = await import(
                '/docs-viewer/runtime/js/review/docs-viewer-review-controller.js'
            );
            return {
                topLevel: review.reviewCanonicalDocumentHref(
                    { source_scope: 'studio', source_sub_scope: '' },
                    'doc-1'
                ),
                subScope: review.reviewCanonicalDocumentHref(
                    { source_scope: 'studio', source_sub_scope: 'tags' },
                    'doc-1'
                )
            };
        }"""
    )
    if canonical_links != {
        "topLevel": "/docs/?scope=studio&doc=doc-1",
        "subScope": "",
    }:
        raise AssertionError(
            f"unexpected review canonical-link projection: {canonical_links!r}"
        )
    install_workflow_fixture(page)
    page.wait_for_selector('[data-role="docs-viewer-management-modal"]', timeout=timeout_ms)
    modal_card = page.locator(".docsViewer__modalCard")
    if "docsViewer__modalCard--review-package" not in (
        modal_card.get_attribute("class") or ""
    ).split():
        raise AssertionError("Review package chooser did not use its fitted modal variant")
    headings = page.locator(".docsViewerReviewPackage__table th").all_text_contents()
    if headings != ["File", "Collection", "Documents"]:
        raise AssertionError(f"unexpected Review package columns: {headings!r}")
    column_layout = page.evaluate(
        """() => {
            const table = document.querySelector('.docsViewerReviewPackage__table');
            const headings = Array.from(table.querySelectorAll('th'));
            const tableWidth = table.getBoundingClientRect().width;
            return {
                ratios: headings.map((heading) => (
                    heading.getBoundingClientRect().width / tableWidth
                )),
                documentsTextAlign: getComputedStyle(headings[2]).textAlign
            };
        }"""
    )
    expected_ratios = [0.61, 0.21, 0.18]
    if any(
        abs(actual - expected) > 0.01
        for actual, expected in zip(column_layout["ratios"], expected_ratios)
    ):
        raise AssertionError(f"unexpected Review package column widths: {column_layout!r}")
    if column_layout["documentsTextAlign"] != "left":
        raise AssertionError("Review package Documents heading was not left aligned")
    rows = page.locator(".docsViewerReviewPackage__table tbody tr")
    if rows.count() != 2:
        raise AssertionError(f"Review package did not fail closed to two reviewable rows: {rows.count()}")
    row_text = [" ".join(text.split()) for text in rows.all_text_contents()]
    if row_text != ["alpha.jsonl Studio 2", "beta.jsonl Studio / Tags 1"]:
        raise AssertionError(f"unexpected Review package rows: {row_text!r}")
    radios = page.locator('input[name="docsViewerReviewPackage"]')
    if radios.count() != 2 or not radios.first.is_checked():
        raise AssertionError("Review package did not select exactly one package by default")
    radios.nth(1).check()
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_selector(
        '[data-role="docs-viewer-management-modal"] h2:text("Review package prepared")',
        timeout=timeout_ms,
    )
    link = page.locator(".docsViewerReviewPackage__resultLink a")
    if link.inner_text() != "Open in Docs Review":
        raise AssertionError(f"unexpected new-review link label: {link.inner_text()!r}")
    if link.get_attribute("href") != "/docs-review/?package=20260722-204025-documents-document-content":
        raise AssertionError(f"unexpected new-review link target: {link.get_attribute('href')!r}")
    if link.get_attribute("target") != "_blank" or link.get_attribute("rel") != "noopener noreferrer":
        raise AssertionError("Review package did not keep the accepted new-tab browser boundary")
    page.locator('[data-role="modal-primary"]').click()
    result = page.evaluate(
        """async () => {
            await window.reviewWorkflowPromise;
            return window.reviewFixture;
        }"""
    )
    if result["calls"] != [
        {"method": "config"},
        {"method": "returned", "scope": "studio"},
        {
            "method": "review",
            "payload": {
                "scope": "studio",
                "staged_filename": "beta.jsonl",
                "dry_run": False,
            },
        },
    ]:
        raise AssertionError(f"unexpected Review package requests: {result['calls']!r}")
    if result["busy"] != [True, False, True, False]:
        raise AssertionError(f"unexpected Review package ready/busy state: {result['busy']!r}")
    if result["result"].get("ok") is not True:
        raise AssertionError(f"Review package did not report materialization success: {result!r}")
    if result["result"]["selectedFilename"] != "beta.jsonl":
        raise AssertionError(f"Review package did not retain the selected package: {result!r}")
    if [item["filename"] for item in result["result"]["files"]] != [
        "alpha.jsonl",
        "beta.jsonl",
    ]:
        raise AssertionError(f"Review package exposed a blocked list entry: {result!r}")


def exercise_existing_review(page: Page, timeout_ms: int) -> None:
    install_workflow_fixture(page, review_mode="existing")
    page.wait_for_selector('[data-role="docs-viewer-management-modal"]', timeout=timeout_ms)
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_selector(
        '[data-role="docs-viewer-management-modal"] h2:text("Review package already prepared")',
        timeout=timeout_ms,
    )
    link = page.locator(".docsViewerReviewPackage__resultLink a")
    if link.inner_text() != "Open existing review":
        raise AssertionError(f"unexpected existing-review link label: {link.inner_text()!r}")
    if link.get_attribute("href") != "/docs-review/?package=20260722-204025-documents-document-content":
        raise AssertionError(f"unexpected existing-review link target: {link.get_attribute('href')!r}")
    page.locator('[data-role="modal-primary"]').click()
    result = page.evaluate(
        """async () => {
            await window.reviewWorkflowPromise;
            return window.reviewFixture;
        }"""
    )
    if result["result"].get("ok") is not True or result["result"]["payload"].get("review_existing") is not True:
        raise AssertionError(f"Review package did not return the existing review: {result!r}")


def exercise_review_failure(page: Page, timeout_ms: int) -> None:
    install_workflow_fixture(page, review_mode="failure")
    page.wait_for_selector('[data-role="docs-viewer-management-modal"]', timeout=timeout_ms)
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_selector(
        '[data-role="docs-viewer-management-modal"] h2:text("Review package was not prepared")',
        timeout=timeout_ms,
    )
    modal_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    if "Existing review identity does not match." not in modal_text:
        raise AssertionError(f"Review package did not expose the focused issue: {modal_text!r}")
    if "private/workspace" in modal_text:
        raise AssertionError(f"Review package exposed an internal workspace path: {modal_text!r}")
    page.locator('[data-role="modal-primary"]').click()
    result = page.evaluate(
        """async () => {
            await window.reviewWorkflowPromise;
            return window.reviewFixture;
        }"""
    )
    if result["result"].get("ok") is not False:
        raise AssertionError(f"Review package did not retain the failed result: {result!r}")
    if result["busy"] != [True, False, True, False]:
        raise AssertionError(f"unexpected Review package failure busy state: {result['busy']!r}")


def exercise_scope_mismatch(page: Page, timeout_ms: int) -> None:
    install_workflow_fixture(page, "library")
    page.wait_for_selector(
        '[data-role="docs-viewer-management-modal"] h2:text("Review packages unavailable")',
        timeout=timeout_ms,
    )
    modal_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    if "did not match the active Docs Viewer scope" not in modal_text:
        raise AssertionError(f"Review package did not fail closed on a scope mismatch: {modal_text!r}")
    page.locator('[data-role="modal-primary"]').click()
    result = page.evaluate(
        """async () => {
            await window.reviewWorkflowPromise;
            return window.reviewFixture;
        }"""
    )
    if result["result"].get("error") is None or result["busy"] != [True, False]:
        raise AssertionError(f"unexpected scope-mismatch result: {result!r}")


def exercise_review_build_controller(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const review = await import(
                '/docs-viewer/runtime/js/review/docs-viewer-review-controller.js'
            );
            document.body.innerHTML = [
                '<main id="reviewFixtureRoot"></main>',
                '<p id="docsViewerStatus" hidden></p>'
            ].join('');
            const renderer = review.createDocsViewerReviewControlRenderers()[
                'review-package-controls'
            ];
            const rendered = renderer({
                document,
                existingRoot: null
            });
            document.querySelector('#reviewFixtureRoot').append(rendered.root);
            const route = '/docs-review/?package=review-1&doc=doc-1#retained';
            const fixture = {
                buildCalls: [],
                pending: [],
                reloads: []
            };
            const windowRef = {
                location: {
                    href: 'http://fixture.test' + route,
                    search: '?package=review-1&doc=doc-1',
                    assign: () => {},
                    reload: () => fixture.reloads.push(route)
                },
                history: {
                    state: null,
                    replaceState: () => {}
                }
            };
            const provider = {
                activeCollectionId: () => 'review-1',
                build: (packageId) => {
                    fixture.buildCalls.push(packageId);
                    return new Promise((resolve, reject) => {
                        fixture.pending.push({ resolve, reject });
                    });
                },
                listCollections: async () => [{
                    package_id: 'review-1',
                    title: 'Review one',
                    built: true
                }],
                openSource: async () => ({}),
                readAssetInventory: async () => ({ inventories: {} }),
                readManifest: async () => ({
                    manifest: {
                        source_scope: 'studio',
                        source_sub_scope: ''
                    }
                })
            };
            const controller = review.createDocsViewerReviewController({
                document,
                window: windowRef
            });
            controller.setProvider(provider);
            await controller.start();
            const button = document.querySelector(
                '[data-docs-viewer-review-action="build"]'
            );
            const status = document.querySelector('#docsViewerStatus');
            const initial = {
                label: button.textContent,
                disabled: button.disabled,
                action: button.getAttribute('data-docs-viewer-review-action')
            };

            button.click();
            const pendingFailure = {
                disabled: button.disabled,
                status: status.textContent,
                isError: status.classList.contains('is-error')
            };
            fixture.pending[0].reject(new Error('Fixture build failed.'));
            await new Promise((resolve) => setTimeout(resolve, 0));
            const failed = {
                disabled: button.disabled,
                status: status.textContent,
                isError: status.classList.contains('is-error'),
                reloads: fixture.reloads.length
            };

            button.click();
            const pendingRetry = {
                disabled: button.disabled,
                status: status.textContent
            };
            fixture.pending[1].resolve({
                summary_text: 'Built 1 review documents for review-1.'
            });
            await new Promise((resolve) => setTimeout(resolve, 0));
            return {
                initial,
                pendingFailure,
                failed,
                pendingRetry,
                buildCalls: fixture.buildCalls,
                success: {
                    status: status.textContent,
                    isError: status.classList.contains('is-error'),
                    reloads: fixture.reloads
                }
            };
        }"""
    )
    expected = {
        "initial": {
            "label": "Build",
            "disabled": False,
            "action": "build",
        },
        "pendingFailure": {
            "disabled": True,
            "status": "Building review package...",
            "isError": False,
        },
        "failed": {
            "disabled": False,
            "status": "Fixture build failed.",
            "isError": True,
            "reloads": 0,
        },
        "pendingRetry": {
            "disabled": True,
            "status": "Building review package...",
        },
        "buildCalls": ["review-1", "review-1"],
        "success": {
            "status": "Built 1 review documents for review-1.",
            "isError": False,
            "reloads": [
                "/docs-review/?package=review-1&doc=doc-1#retained",
            ],
        },
    }
    if result != expected:
        raise AssertionError(f"unexpected Docs Review Build lifecycle: {result!r}")


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
            assert_action_contract(page)
            exercise_reviewable_list(page, args.timeout_ms)
            exercise_existing_review(page, args.timeout_ms)
            exercise_review_failure(page, args.timeout_ms)
            exercise_scope_mismatch(page, args.timeout_ms)
            exercise_review_build_controller(page)
            browser.close()
            if errors:
                raise AssertionError(f"page errors: {errors!r}")
    finally:
        server.shutdown()
        server.server_close()
    print("Docs Viewer Review package workflow modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

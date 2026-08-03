#!/usr/bin/env python3
"""Smoke-check the consolidated candidate-driven Docs Import modal."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
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
    resolved_root = site_root.expanduser().resolve()
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def ordinary_candidate(filename: str, source_format: str) -> dict[str, object]:
    return {
        "filename": filename,
        "source_format": source_format,
        "candidate_kind": "ordinary_document",
        "validation_state": "ready",
        "target_mode": "ordinary_context",
        "target": None,
        "target_label": "Current Docs display",
        "supports_docs_review": False,
        "supports_return_import": False,
        "docs_review_enabled": False,
        "docs_review_disabled_reason": "ordinary_source",
        "import_enabled": True,
        "import_disabled_reason": "",
        "disabled_reason": "",
        "diagnostics": [],
    }


def returned_candidate(
    filename: str,
    *,
    target: dict[str, str],
    target_label: str,
    supports_review: bool,
    supports_import: bool,
) -> dict[str, object]:
    return {
        "filename": filename,
        "source_format": "data_sharing_documents",
        "candidate_kind": "returned_package",
        "validation_state": "ready",
        "target_mode": "manifest_collection",
        "target": target,
        "target_label": target_label,
        "scope": target["scope"],
        "sub_scope": target.get("sub_scope", ""),
        "supports_docs_review": supports_review,
        "supports_return_import": supports_import,
        "docs_review_enabled": supports_review,
        "docs_review_disabled_reason": "" if supports_review else "docs_review_unsupported",
        "import_enabled": supports_import,
        "import_disabled_reason": "" if supports_import else "return_import_unsupported",
        "disabled_reason": "",
        "diagnostics": [],
        "document_count": 2,
    }


def edited_candidate() -> dict[str, object]:
    return {
        "filename": "edited-tags",
        "display_name": "20260730-095512-document-content (reviewed)",
        "source_format": "edited_review_sources",
        "candidate_kind": "edited_review_source",
        "validation_state": "ready",
        "target_mode": "manifest_collection",
        "target": {"scope": "studio", "sub_scope": "tags"},
        "target_label": "Studio / Tags",
        "scope": "studio",
        "sub_scope": "tags",
        "supports_docs_review": False,
        "supports_return_import": True,
        "docs_review_enabled": False,
        "docs_review_disabled_reason": "edited_review_source",
        "import_enabled": True,
        "import_disabled_reason": "",
        "disabled_reason": "",
        "diagnostics": [],
        "document_count": 2,
    }


def blocked_candidate() -> dict[str, object]:
    return {
        "filename": "invalid-returned.jsonl",
        "source_format": "data_sharing_documents",
        "candidate_kind": "returned_package",
        "validation_state": "blocked",
        "target_mode": "manifest_collection",
        "target": None,
        "target_label": "",
        "supports_docs_review": False,
        "supports_return_import": False,
        "docs_review_enabled": False,
        "docs_review_disabled_reason": "untrusted_package_metadata",
        "import_enabled": False,
        "import_disabled_reason": "untrusted_package_metadata",
        "disabled_reason": "untrusted_package_metadata",
        "diagnostics": [
            {
                "code": "untrusted_package_metadata",
                "message": "Trusted export metadata is unavailable.",
            }
        ],
    }


def wait_until_idle(page: Page) -> None:
    page.wait_for_function(
        "() => document.getElementById('docsHtmlImportRoot').dataset.studioBusy === 'false'",
    )


def selected_snapshot(page: Page) -> dict[str, object]:
    return page.evaluate(
        """() => ({
          filename: document.querySelector(
            '#docsHtmlImportCandidateList [data-import-candidate][aria-selected="true"]'
          )?.dataset.filename || '',
          destination: document.querySelector(
            '#docsHtmlImportCandidateList [data-import-candidate][aria-selected="true"] '
            + '.docsViewerImport__candidateValue'
          )?.textContent || '',
          note: document.getElementById('docsHtmlImportCandidateNote').textContent,
          importDisabled: document.getElementById('docsHtmlImportRun').disabled,
          reviewDisabled: document.getElementById('docsHtmlImportReview').disabled,
          runLabel: document.getElementById('docsHtmlImportRun').textContent
        })""",
    )


def select_candidate(page: Page, filename: str) -> None:
    page.wait_for_function(
        """() => document.getElementById(
          'docsHtmlImportCandidateList'
        )?.getAttribute('aria-disabled') !== 'true'""",
    )
    page.locator(
        "#docsHtmlImportCandidateList [data-import-candidate]"
    ).evaluate_all(
        """(rows, selectedFilename) => {
            const row = rows.find(item => item.dataset.filename === selectedFilename);
            if (!row) throw new Error(`Missing Import candidate: ${selectedFilename}`);
            row.click();
        }""",
        filename,
    )


def assert_consolidated_modal(page: Page, base_url: str, site_root: Path) -> None:
    candidates = [
        ordinary_candidate("alpha.md", "markdown"),
        ordinary_candidate("beta.html", "html"),
        returned_candidate(
            "returned-tags.jsonl",
            target={"scope": "studio", "sub_scope": "tags"},
            target_label="Studio / Tags",
            supports_review=True,
            supports_import=True,
        ),
        returned_candidate(
            "review-only-library.jsonl",
            target={"scope": "library"},
            target_label="Library",
            supports_review=True,
            supports_import=False,
        ),
        edited_candidate(),
        blocked_candidate(),
    ]
    import_requests: list[dict[str, object]] = []
    review_requests: list[dict[str, object]] = []
    review_attempt = 0

    def fulfill(route, payload: object, status: int = 200) -> None:
        route.fulfill(
            status=status,
            content_type="application/json",
            body=json.dumps(payload),
        )

    page.route(
        "**/docs-viewer/runtime/js/shared/docs-viewer-render.js",
        lambda route: route.fulfill(
            path=str(
                site_root
                / "site/docs-viewer/runtime/js/shared/docs-viewer-render.js"
            ),
            content_type="text/javascript",
        ),
    )
    page.route("**/health", lambda route: fulfill(route, {"ok": True}))
    page.route(
        re.compile(r".*/docs/import-source-directories(?:\?.*)?$"),
        lambda route: fulfill(
            route,
            {
                "ok": True,
                "current_directory": "data-sharing/import-staging",
                "current_selectable": True,
                "parent_directory": "data-sharing",
                "directories": [],
            },
        ),
    )
    page.route(
        re.compile(r".*/docs/import-source-files(?:\?.*)?$"),
        lambda route: fulfill(
            route,
            {
                "ok": True,
                "available": True,
                "source_directory": "data-sharing/import-staging",
                "files": [{"filename": "legacy-ignored.md"}],
                "candidates": candidates,
            },
        ),
    )

    def fulfill_import(route) -> None:
        body = route.request.post_data_json
        import_requests.append(body)
        filename = str(body["staged_filename"])
        if body.get("preview_only") is True:
            fulfill(
                route,
                {
                    "ok": True,
                    "collection": True,
                    "preview_only": True,
                    "source_format": "data_sharing_documents",
                    "target": {"scope": "studio", "sub_scope": "tags"},
                    "package": {
                        "export_id": "ds_20260730T120000Z",
                        "source_sha256": "a" * 64,
                        "trusted_metadata_sha256": "b" * 64,
                    },
                    "blockers": [],
                    "warnings": [],
                    "counts": {
                        "records": 2,
                        "creates": 0,
                        "collisions": 2,
                        "record_errors": 0,
                        "media_plans": 0,
                    },
                    "planned_identities": [
                        {"record_index": 0, "doc_id": "tag-a"},
                        {"record_index": 1, "doc_id": "tag-b"},
                    ],
                    "planned_actions": [
                        {"record_index": 0, "doc_id": "tag-a", "action": "overwrite"},
                        {"record_index": 1, "doc_id": "tag-b", "action": "overwrite"},
                    ],
                    "records": [
                        {
                            "record_index": 0,
                            "doc_id": "tag-a",
                            "title": "Tag A",
                            "action": "overwrite",
                        },
                        {
                            "record_index": 1,
                            "doc_id": "tag-b",
                            "title": "Tag B",
                            "action": "overwrite",
                        },
                    ],
                },
            )
            return
        if filename == "returned-tags.jsonl":
            fulfill(
                route,
                {
                    "ok": True,
                    "collection": True,
                    "preview_only": False,
                    "confirmed": True,
                    "source_format": "data_sharing_documents",
                    "target": {"scope": "studio", "sub_scope": "tags"},
                    "viewer_url": (
                        "/docs/?scope=studio&doc=report-tags"
                    ),
                    "staged_filename": filename,
                    "outcome": "completed",
                    "counts": {
                        "created": 0,
                        "overwritten": 2,
                        "failed": 0,
                        "not_attempted": 0,
                    },
                    "records": [
                        {
                            "record_index": 0,
                            "doc_id": "tag-a",
                            "title": "Tag A",
                            "status": "overwritten",
                            "warnings": [],
                        },
                        {
                            "record_index": 1,
                            "doc_id": "tag-b",
                            "title": "Tag B",
                            "status": "overwritten",
                            "warnings": [],
                        },
                    ],
                    "warnings": [],
                },
            )
            return
        doc_id = f"imported-{len(import_requests)}"
        sub_scope = str(body.get("sub_scope") or "")
        fulfill(
            route,
            {
                "ok": True,
                "collection": False,
                "preview_only": False,
                "staged_filename": filename,
                "doc_id": doc_id,
                "target": {
                    "scope": body["scope"],
                    **(
                        {"sub_scope": sub_scope}
                        if sub_scope
                        else {}
                    ),
                    "doc_id": doc_id,
                },
                "viewer_url": (
                    f"/docs/?scope={body['scope']}&doc=report-{sub_scope}"
                    f"&subdoc={doc_id}"
                    if sub_scope
                    else f"/docs/?scope={body['scope']}&doc={doc_id}"
                ),
                "source_format": "markdown",
                "summary_text": f"Imported {filename}.",
                "import_preview": {
                    "source_format": "markdown",
                    "source_stats": {"chars": 12, "links": 0, "images": 0},
                    "warnings": [],
                },
            },
        )

    page.route("**/docs/import-source", fulfill_import)

    def fulfill_review(route) -> None:
        nonlocal review_attempt
        review_attempt += 1
        body = route.request.post_data_json
        review_requests.append(body)
        if review_attempt == 1:
            fulfill(
                route,
                {"ok": False, "error": "Synthetic review preparation failure."},
                status=500,
            )
            return
        fulfill(
            route,
            {
                "ok": True,
                "review_package_id": "20260730-120000-document-content",
                "review_url": (
                    "/docs-review/"
                    "?package=20260730-120000-document-content"
                ),
                "review_existing": True,
                "summary_text": "Docs Review package already exists.",
            },
        )

    page.route("**/docs/packages/returned/review", fulfill_review)
    page.goto(base_url, wait_until="domcontentloaded")
    page.evaluate(
        """async (managementBaseUrl) => {
          document.body.innerHTML = [
            '<button id="importTrigger">Import</button>',
            '<div id="mount"></div>'
          ].join('');
          const shellModule = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js'
          );
          const modalModule = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-modals.js'
          );
          const importModule = await import(
            '/docs-viewer/runtime/js/import/docs-html-import.js'
          );
          const shellRefs = shellModule.renderDocsViewerManagementShell({
            document,
            mount: document.getElementById('mount')
          });
          const modalController = modalModule.createDocsViewerManagementModalController({
            refs: shellRefs,
            management: {},
            scopeConfig: {},
            callbacks: { viewerScope: () => 'studio' }
          });
          modalController.wireEvents();
          window.__caiBusyEvents = [];
          window.__caiTerminalDetails = [];
          window.__caiModalController = modalController;
          window.__caiImportApp = await importModule.initDocsHtmlImport({
            root: document.getElementById('docsHtmlImportRoot'),
            bootStatus: document.getElementById('docsHtmlImportBootStatus'),
            managementBaseUrl,
            initialDestination: { scope: 'studio' },
            initialDestinationLabel: 'Studio',
            onBusyChange: busy => {
              window.__caiBusyEvents.push(busy);
              modalController.projectImportBusy(busy);
            },
            onCollectionStateChange: (viewState, onCommand) => {
              modalController.projectImportCollectionState(viewState, onCommand);
            },
            onTerminalResult: detail => {
              window.__caiTerminalDetails.push(detail);
            }
          });
          await modalController.openImportModal({
            restoreFocus: document.getElementById('importTrigger')
          });
        }""",
        base_url,
    )

    option_values = page.locator(
        "#docsHtmlImportCandidateList [data-import-candidate]"
    ).evaluate_all(
        "(rows) => rows.map((row) => row.dataset.filename)",
    )
    assert option_values == [str(candidate["filename"]) for candidate in candidates]
    assert page.locator(
        ".docsViewerImport__candidateHeader > span"
    ).all_text_contents() == ["File", "Destination"]
    assert page.locator("#docsHtmlImportFileLabel").count() == 0
    assert page.locator("#docsHtmlImportCandidateDetails").count() == 0
    assert page.locator("#docsHtmlImportTypeSelect").count() == 0
    assert page.locator("#docsHtmlImportScopeSelect").count() == 0
    assert page.locator("#docsHtmlImportSourceDirectory").text_content() == (
        "data-sharing/import-staging"
    )
    assert selected_snapshot(page) == {
        "filename": "alpha.md",
        "destination": "Studio",
        "note": "",
        "importDisabled": False,
        "reviewDisabled": True,
        "runLabel": "Import",
    }

    page.locator("#docsHtmlImportRun").click()
    wait_until_idle(page)
    assert import_requests[0]["scope"] == "studio"
    assert import_requests[0]["source_directory"] == "data-sharing/import-staging"
    assert "sub_scope" not in import_requests[0]
    assert import_requests[0]["staged_filename"] == "alpha.md"
    assert page.locator("[data-doc-destination-link]").get_attribute("href") == (
        "/docs/?scope=studio&doc=imported-1"
    )

    page.evaluate(
        """() => window.__caiImportApp.setDestination(
          { scope: 'studio', sub_scope: 'tags' },
          { label: 'Studio / Tags' }
        )""",
    )
    assert page.locator(
        "#docsHtmlImportCandidateList [data-import-candidate]"
    ).count() == len(candidates)
    select_candidate(page, "beta.html")
    child_ordinary = selected_snapshot(page)
    assert child_ordinary["destination"] == "Studio / Tags"
    assert page.locator("#docsHtmlImportIncludePromptMetaWrap").is_visible()
    page.locator("#docsHtmlImportRun").click()
    wait_until_idle(page)
    assert import_requests[1]["scope"] == "studio"
    assert import_requests[1]["source_directory"] == "data-sharing/import-staging"
    assert import_requests[1]["sub_scope"] == "tags"
    assert import_requests[1]["staged_filename"] == "beta.html"
    assert page.locator("[data-doc-destination-link]").get_attribute("href") == (
        "/docs/?scope=studio&doc=report-tags&subdoc=imported-2"
    )

    page.evaluate(
        """() => window.__caiImportApp.setDestination(
          { scope: 'library' },
          { label: 'Library' }
        )""",
    )
    select_candidate(page, "returned-tags.jsonl")
    cross_context = selected_snapshot(page)
    assert cross_context == {
        "filename": "returned-tags.jsonl",
        "destination": "Studio / Tags",
        "note": "",
        "importDisabled": False,
        "reviewDisabled": False,
        "runLabel": "Preview collection",
    }
    page.locator("#docsHtmlImportRun").click()
    page.locator("#docsViewerImportCollectionModal:not([hidden])").wait_for()
    assert import_requests[2]["scope"] == "studio"
    assert import_requests[2]["source_directory"] == "data-sharing/import-staging"
    assert import_requests[2]["sub_scope"] == "tags"
    assert import_requests[2]["staged_filename"] == "returned-tags.jsonl"
    assert import_requests[2]["preview_only"] is True
    assert page.locator("#docsViewerImportModal").is_hidden()
    assert page.locator("#docsImportCollectionCancel").is_visible()
    page.locator("#docsImportCollectionConfirm").click()
    wait_until_idle(page)
    assert import_requests[3]["source_directory"] == "data-sharing/import-staging"
    collection_link = page.locator("[data-collection-destination-link]")
    assert collection_link.get_attribute("href") == (
        "/docs/?scope=studio&doc=report-tags"
    )
    page.locator("#docsImportCollectionClose").click()

    page.evaluate(
        """() => window.__caiModalController.openImportModal({
          restoreFocus: document.getElementById('importTrigger')
        })""",
    )
    assert page.locator(
        "#docsHtmlImportCandidateList [data-import-candidate][aria-selected='true']"
    ).get_attribute("data-filename") == (
        "returned-tags.jsonl"
    )

    select_candidate(page, "review-only-library.jsonl")
    review_only = selected_snapshot(page)
    assert review_only["destination"] == "Library"
    assert review_only["importDisabled"] is True
    assert review_only["reviewDisabled"] is False
    assert "Import unavailable" in str(review_only["note"])

    with page.expect_popup() as failed_popup_info:
        page.locator("#docsHtmlImportReview").click()
    failed_popup = failed_popup_info.value
    failed_popup.wait_for_event("close")
    wait_until_idle(page)
    assert page.locator(
        "#docsHtmlImportCandidateList [data-import-candidate][aria-selected='true']"
    ).get_attribute("data-filename") == (
        "review-only-library.jsonl"
    )
    assert page.locator("#docsHtmlImportReview").is_enabled()
    assert page.locator("#docsHtmlImportStatus").get_attribute("data-state") == (
        "error"
    )

    with page.expect_popup() as review_popup_info:
        page.locator("#docsHtmlImportReview").click()
    review_popup = review_popup_info.value
    review_popup.wait_for_url(
        "**/docs-review/?package=20260730-120000-document-content",
    )
    wait_until_idle(page)
    assert review_requests == [
        {
            "scope": "library",
            "staged_filename": "review-only-library.jsonl",
            "dry_run": False,
        },
        {
            "scope": "library",
            "staged_filename": "review-only-library.jsonl",
            "dry_run": False,
        },
    ]
    assert page.locator("#docsHtmlImportStatus").get_attribute("data-state") == (
        "success"
    )

    select_candidate(page, "edited-tags")
    edited = selected_snapshot(page)
    assert edited["destination"] == "Studio / Tags"
    assert edited["importDisabled"] is False
    assert edited["reviewDisabled"] is True
    assert "review outputs" in str(edited["note"]) or edited["note"] == ""

    select_candidate(page, "invalid-returned.jsonl")
    blocked = selected_snapshot(page)
    assert blocked["destination"] == "Unavailable"
    assert blocked["importDisabled"] is True
    assert blocked["reviewDisabled"] is True
    assert blocked["note"] == (
        "Import unavailable: Trusted export metadata is unavailable."
    )

    select_candidate(page, "alpha.md")
    page.locator("#docsViewerImportCancelButton").click()
    assert page.locator("#docsViewerImportModal").is_hidden()
    page.wait_for_function("() => document.activeElement.id === 'importTrigger'")
    assert page.evaluate("() => window.__caiBusyEvents") == [
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
    ]
    terminal_details = page.evaluate(
        """() => window.__caiTerminalDetails.map(detail => ({
          destinationUrl: detail.destinationUrl,
          target: detail.target,
          collection: detail.result?.collection === true
        }))""",
    )
    assert terminal_details == [
        {
            "destinationUrl": "/docs/?scope=studio&doc=imported-1",
            "target": {"scope": "studio", "doc_id": "imported-1"},
            "collection": False,
        },
        {
            "destinationUrl": (
                "/docs/?scope=studio&doc=report-tags&subdoc=imported-2"
            ),
            "target": {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": "imported-2",
            },
            "collection": False,
        },
        {
            "destinationUrl": "/docs/?scope=studio&doc=report-tags",
            "target": {"scope": "studio", "sub_scope": "tags"},
            "collection": True,
        },
    ]

    malformed_error = page.evaluate(
        """async () => {
          const model = await import(
            '/docs-viewer/runtime/js/import/docs-import-candidate-model.js'
          );
          try {
            model.docsImportCandidateInventory({
              candidates: [{
                filename: 'fabricated.jsonl',
                source_format: 'data_sharing_documents',
                candidate_kind: 'returned_package',
                validation_state: 'ready',
                target_mode: 'ordinary_context',
                target: null,
                supports_docs_review: true,
                supports_return_import: true,
                docs_review_enabled: true,
                import_enabled: true,
                diagnostics: []
              }]
            });
          } catch (error) {
            return error.message;
          }
          return '';
        }""",
    )
    assert malformed_error == (
        "Manifest Import candidate fabricated.jsonl cannot use display context."
    )

    refresh_contract = page.evaluate(
        """async () => {
          const management = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management.js'
          );
          const calls = [];
          const reportState = {
            refreshDocument: target => calls.push({
              kind: 'document',
              target
            }),
            refreshCollection: target => calls.push({
              kind: 'collection',
              target
            })
          };
          const ordinaryParent = {
            result: {
              collection: false,
              target: { scope: 'studio', doc_id: 'parent-import' },
              viewer_url: '/docs/?scope=studio&doc=parent-import'
            },
            destinationUrl: '/docs/?scope=studio&doc=parent-import'
          };
          const ordinaryChild = {
            result: {
              collection: false,
              target: {
                scope: 'studio',
                sub_scope: 'tags',
                doc_id: 'child-import'
              },
              viewer_url: (
                '/docs/?scope=studio&doc=report-tags&subdoc=child-import'
              )
            },
            destinationUrl: (
              '/docs/?scope=studio&doc=report-tags&subdoc=child-import'
            )
          };
          const childCollection = {
            result: {
              collection: true,
              target: { scope: 'studio', sub_scope: 'tags' },
              viewer_url: '/docs/?scope=studio&doc=report-tags'
            },
            destinationUrl: '/docs/?scope=studio&doc=report-tags'
          };
          const parent = await management.refreshDocsImportTerminalDestination(
            ordinaryParent,
            {
              currentCollection: { scope: 'studio' },
              reloadParent: docId => calls.push({ kind: 'parent', docId })
            }
          );
          const child = await management.refreshDocsImportTerminalDestination(
            ordinaryChild,
            {
              currentCollection: { scope: 'studio', sub_scope: 'tags' },
              reportState
            }
          );
          const collection = await management.refreshDocsImportTerminalDestination(
            childCollection,
            {
              currentCollection: { scope: 'studio', sub_scope: 'tags' },
              reportState
            }
          );
          const crossContext = await management.refreshDocsImportTerminalDestination(
            childCollection,
            {
              currentCollection: { scope: 'library' },
              reportState,
              reloadParent: docId => calls.push({ kind: 'wrong-parent', docId })
            }
          );
          let mismatchedUrl = '';
          try {
            await management.refreshDocsImportTerminalDestination(
              {
                ...ordinaryParent,
                destinationUrl: '/docs/?scope=studio&doc=other'
              },
              {
                currentCollection: { scope: 'studio' },
                reloadParent: () => {}
              }
            );
          } catch (error) {
            mismatchedUrl = error.message;
          }
          return { calls, child, collection, crossContext, mismatchedUrl, parent };
        }""",
    )
    assert refresh_contract == {
        "calls": [
            {"kind": "parent", "docId": "parent-import"},
            {
                "kind": "document",
                "target": {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "child-import",
                },
            },
            {
                "kind": "collection",
                "target": {"scope": "studio", "sub_scope": "tags"},
            },
        ],
        "parent": {
            "refreshed": True,
            "target": {"scope": "studio", "doc_id": "parent-import"},
        },
        "child": {
            "refreshed": True,
            "target": {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": "child-import",
            },
        },
        "collection": {
            "refreshed": True,
            "target": {"scope": "studio", "sub_scope": "tags"},
        },
        "crossContext": {
            "refreshed": False,
            "target": {"scope": "studio", "sub_scope": "tags"},
        },
        "mismatchedUrl": (
            "Docs Import terminal destination URL does not match its result."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    site_root = Path(args.site_root).expanduser().resolve()
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            assert_consolidated_modal(page, base_url, site_root)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print("docs import consolidated modal smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

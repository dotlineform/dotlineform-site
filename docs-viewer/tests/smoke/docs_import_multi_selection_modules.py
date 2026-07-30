#!/usr/bin/env python3
"""Smoke-check ordinary Docs Import multi-selection and package isolation."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
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
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_multi_selection(page: Page, base_url: str) -> None:
    import_requests: list[dict[str, object]] = []
    returned_listing_requests: list[str] = []
    source_requests: list[dict[str, object]] = []
    child_failures_remaining = 1
    package_apply_failures_remaining = 1
    staged_files = [
        {"filename": "alpha.md", "source_format": "markdown"},
        {"filename": "beta.html", "source_format": "html"},
        {"filename": "word.docx", "source_format": "docx"},
        {"filename": "notes.json", "source_format": "file"},
        {
            "filename": "reviewed.jsonl",
            "source_format": "data_sharing_documents",
        },
    ]

    def fulfill(route, payload: object) -> None:
        route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

    page.route(
        "**/docs-viewer/config/defaults/docs-viewer-config.json",
        lambda route: fulfill(
            route,
            {
                "schema_version": "docs_viewer_config_v1",
                "scopes": [{"scope_id": "studio"}, {"scope_id": "library"}],
            },
        ),
    )
    page.route(
        "**/docs-viewer/runtime/js/shared/docs-viewer-render.js",
        lambda route: route.fulfill(
            path=str(
                Path(__file__).resolve().parents[3]
                / "site/docs-viewer/runtime/js/shared/docs-viewer-render.js"
            ),
            content_type="text/javascript",
        ),
    )
    page.route("**/health", lambda route: fulfill(route, {"ok": True}))
    page.route(
        "**/docs/import-source-files",
        lambda route: fulfill(route, {"ok": True, "available": True, "files": staged_files}),
    )
    page.route(
        "**/docs/packages/returned?*",
        lambda route: (
            returned_listing_requests.append(route.request.url),
            fulfill(
                route,
                {
                    "ok": True,
                    "scope": "studio",
                    "sub_scope": "tags",
                    "required_capability": "supports_return_import",
                    "files": [
                        {
                            "filename": "returned-tags.jsonl",
                            "scope": "studio",
                            "sub_scope": "tags",
                            "scope_label": "Studio",
                            "sub_scope_label": "Tags",
                            "document_count": 2,
                            "supports_docs_review": True,
                            "supports_return_import": True,
                        },
                        {
                            "filename": "returned-notes.jsonl",
                            "scope": "studio",
                            "sub_scope": "notes",
                            "scope_label": "Studio",
                            "sub_scope_label": "Notes",
                            "document_count": 1,
                            "supports_docs_review": True,
                            "supports_return_import": True,
                        },
                        {
                            "filename": "review-only-tags.jsonl",
                            "scope": "studio",
                            "sub_scope": "tags",
                            "scope_label": "Studio",
                            "sub_scope_label": "Tags",
                            "document_count": 2,
                            "supports_docs_review": True,
                            "supports_return_import": False,
                        }
                    ],
                },
            ),
        )[-1],
    )

    def fulfill_import(route) -> None:
        nonlocal child_failures_remaining, package_apply_failures_remaining
        body = route.request.post_data_json
        import_requests.append(body)
        filename = str(body["staged_filename"])
        if filename == "reviewed.jsonl":
            fulfill(
                route,
                {
                    "ok": True,
                    "collection": True,
                    "preview_only": True,
                    "source_format": "data_sharing_documents",
                    "target": {"scope": body["scope"]},
                    "package": {
                        "export_id": "ds_20260730T110000Z",
                        "source_sha256": "c" * 64,
                    },
                    "blockers": [],
                    "warnings": [],
                    "counts": {
                        "records": 1,
                        "creates": 0,
                        "collisions": 1,
                        "record_errors": 0,
                        "media_plans": 0,
                    },
                    "planned_identities": [
                        {"record_index": 0, "doc_id": "global-a"},
                    ],
                    "planned_actions": [
                        {
                            "record_index": 0,
                            "doc_id": "global-a",
                            "action": "overwrite",
                        },
                    ],
                    "records": [
                        {
                            "record_index": 0,
                            "doc_id": "global-a",
                            "title": "Global A",
                            "action": "overwrite",
                        },
                    ],
                },
            )
            return
        if filename == "returned-tags.jsonl":
            package = {
                "export_id": "ds_20260730T120000Z",
                "source_sha256": "a" * 64,
                "trusted_metadata_sha256": "b" * 64,
            }
            if body.get("preview_only") is True:
                fulfill(
                    route,
                    {
                        "ok": True,
                        "collection": True,
                        "preview_only": True,
                        "source_format": "data_sharing_documents",
                        "target": {"scope": "studio", "sub_scope": "tags"},
                        "package": package,
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
                            {"record_index": 0, "doc_id": "tag-a", "title": "Tag A", "action": "overwrite"},
                            {"record_index": 1, "doc_id": "tag-b", "title": "Tag B", "action": "overwrite"},
                        ],
                    },
                )
                return
            if package_apply_failures_remaining:
                package_apply_failures_remaining -= 1
                route.fulfill(
                    status=503,
                    content_type="application/json",
                    body=json.dumps(
                        {
                            "ok": False,
                            "error": "Synthetic returned-package apply failure.",
                        }
                    ),
                )
                return
            fulfill(
                route,
                {
                    "ok": True,
                    "collection": True,
                    "preview_only": False,
                    "source_format": "data_sharing_documents",
                    "target": {"scope": "studio", "sub_scope": "tags"},
                    "outcome": "completed",
                    "counts": {
                        "created": 0,
                        "overwritten": 2,
                        "failed": 0,
                        "not_attempted": 0,
                    },
                    "records": [
                        {"record_index": 0, "doc_id": "tag-a", "status": "overwritten"},
                        {"record_index": 1, "doc_id": "tag-b", "status": "overwritten"},
                    ],
                    "warnings": [],
                },
            )
            return
        if body.get("sub_scope") == "tags" and child_failures_remaining:
            child_failures_remaining -= 1
            route.fulfill(
                status=422,
                content_type="application/json",
                body=json.dumps(
                    {
                        "ok": False,
                        "error": "Synthetic child Import failure.",
                    }
                ),
            )
            return
        if filename == "beta.html" and not body.get("confirm_interactive_html_overwrite"):
            fulfill(
                route,
                {
                    "ok": True,
                    "preview_only": True,
                    "scope": body["scope"],
                    "staged_filename": filename,
                    "requires_interactive_html_confirmation": True,
                    "summary_text": "Interactive HTML asset overwrite required.",
                    "import_preview": {
                        "source_format": "html",
                        "warnings": ["Interactive HTML asset target already exists."],
                        "interactive_html_plans": [
                            {"target_path": "docs/studio/html/beta-widget.html", "target_exists": True}
                        ],
                    },
                },
            )
            return
        doc_id = Path(filename).stem
        source_format = next(
            record["source_format"] for record in staged_files if record["filename"] == filename
        )
        fulfill(
            route,
            {
                "ok": True,
                "preview_only": False,
                "scope": body["scope"],
                **(
                    {"sub_scope": body["sub_scope"]}
                    if body.get("sub_scope")
                    else {}
                ),
                "staged_filename": filename,
                "doc_id": doc_id,
                "target": {
                    "scope": body["scope"],
                    **(
                        {"sub_scope": body["sub_scope"]}
                        if body.get("sub_scope")
                        else {}
                    ),
                    "doc_id": doc_id,
                },
                "summary_text": f"Imported {filename}",
                "import_preview": {
                    "source_format": source_format,
                    "source_stats": {"chars": 10, "links": 0, "images": 0},
                },
            },
        )

    page.route("**/docs/import-source", fulfill_import)
    page.route(
        "**/docs/open-source",
        lambda route: (
            source_requests.append(route.request.post_data_json),
            fulfill(route, {"ok": True}),
        )[-1],
    )
    result = page.evaluate(
        """async (baseUrl) => {
          document.body.innerHTML = '<button id="importTrigger">Import</button><div id="mount"></div>';
          const shellModule = await import('/docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js');
          const modalModule = await import('/docs-viewer/runtime/js/management/docs-viewer-management-modals.js');
          const importModule = await import('/docs-viewer/runtime/js/import/docs-html-import.js');
          const shellRefs = shellModule.renderDocsViewerManagementShell({
            document,
            mount: document.getElementById('mount')
          });
          const modalController = modalModule.createDocsViewerManagementModalController({
            refs: shellRefs,
            management: {},
            scopeConfig: {},
            callbacks: {
              viewerScope: () => 'studio'
            }
          });
          modalController.wireEvents();

          const terminalDetails = [];
          let collectionRefreshFailuresRemaining = 1;
          const importApp = await importModule.initDocsHtmlImport({
            root: document.getElementById('docsHtmlImportRoot'),
            bootStatus: document.getElementById('docsHtmlImportBootStatus'),
            managementBaseUrl: baseUrl,
            docsViewerConfigUrl: '/docs-viewer/config/defaults/docs-viewer-config.json',
            initialScope: 'studio',
            persistScope: false,
            onBusyChange: busy => modalController.projectImportBusy(busy),
            onCollectionStateChange: (viewState, onCommand) => {
              modalController.projectImportCollectionState(viewState, onCommand);
            },
            onTerminalResult(detail) {
              terminalDetails.push(detail);
              if (
                detail.result?.collection === true
                && collectionRefreshFailuresRemaining
              ) {
                collectionRefreshFailuresRemaining -= 1;
                throw new Error('Synthetic collection report refresh failure.');
              }
            }
          });
          await modalController.openImportModal({
            restoreFocus: document.getElementById('importTrigger')
          });

          const typeSelect = document.getElementById('docsHtmlImportTypeSelect');
          const fileSelect = document.getElementById('docsHtmlImportFileSelect');
          const selectAll = document.getElementById('docsHtmlImportSelectAll');
          const selectionCount = document.getElementById('docsHtmlImportSelectionCount');
          const promptMetaWrap = document.getElementById('docsHtmlImportIncludePromptMetaWrap');
          const runButton = document.getElementById('docsHtmlImportRun');
          const confirmButton = document.getElementById('docsHtmlImportConfirm');
          const selectionBar = document.getElementById('docsHtmlImportSelectionBar');

          const initial = {
            type: typeSelect.value,
            typeLabels: Array.from(typeSelect.options).map(option => option.textContent),
            multiple: fileSelect.multiple,
            filenames: Array.from(fileSelect.options).map(option => option.value),
            selected: Array.from(fileSelect.selectedOptions).map(option => option.value),
            selectionCount: selectionCount.textContent,
            promptMetaHidden: promptMetaWrap.hidden,
            runLabel: runButton.textContent
          };

          selectAll.click();
          const afterSelectAll = {
            selected: Array.from(fileSelect.selectedOptions).map(option => option.value),
            selectionCount: selectionCount.textContent,
            selectAllLabel: selectAll.textContent,
            promptMetaHidden: promptMetaWrap.hidden
          };

          runButton.click();
          for (let attempt = 0; attempt < 1000 && confirmButton.hidden; attempt += 1) {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          if (confirmButton.hidden) throw new Error('interactive HTML replacement confirmation was not shown');
          confirmButton.click();
          while (terminalDetails.length < 1) {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          while (document.getElementById('docsHtmlImportRoot').dataset.studioBusy === 'true') {
            await new Promise(resolve => setTimeout(resolve, 0));
          }

          typeSelect.value = importModule.DOCS_IMPORT_MODE_DATA_SHARING;
          typeSelect.dispatchEvent(new Event('change', { bubbles: true }));
          const packageMode = {
            type: typeSelect.value,
            multiple: fileSelect.multiple,
            filenames: Array.from(fileSelect.options).map(option => option.value),
            selected: Array.from(fileSelect.selectedOptions).map(option => option.value),
            selectionBarHidden: selectionBar.hidden,
            runLabel: runButton.textContent
          };
          runButton.click();
          for (
            let attempt = 0;
            attempt < 1000
              && document.getElementById('docsViewerImportCollectionModal').hidden;
            attempt += 1
          ) {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          const globalPackageConfirmation = {
            modalId: document.querySelector(
              '#docsViewerImportCollectionModal:not([hidden])'
            )?.id || '',
            chooserHidden: document.getElementById('docsViewerImportModal').hidden,
            footerCommands: Array.from(
              document.querySelectorAll(
                '#docsViewerImportCollectionModal [data-collection-command]:not([hidden])'
              )
            ).map(button => button.dataset.collectionCommand)
          };
          document.getElementById('docsImportCollectionCancel').click();
          await new Promise(resolve => setTimeout(resolve, 0));
          await modalController.openImportModal({
            restoreFocus: document.getElementById('importTrigger')
          });

          const locationBeforeChild = location.href;
          importApp.setDestination(
            { scope: 'studio', sub_scope: 'tags' },
            { label: 'studio / Tags' }
          );
          await importApp.refreshStagedFiles();
          Array.from(fileSelect.options).forEach(option => {
            option.selected = option.value === 'alpha.md';
          });
          fileSelect.dispatchEvent(new Event('change', { bubbles: true }));
          const childDestination = {
            locationUnchanged: location.href === locationBeforeChild,
            scopeDisabled: document.getElementById('docsHtmlImportScopeSelect').disabled,
            scopeLabels: Array.from(
              document.getElementById('docsHtmlImportScopeSelect').options
            ).map(option => option.textContent),
            scopeValue: document.getElementById('docsHtmlImportScopeSelect').value,
            typeDisabled: typeSelect.disabled,
            typeLabels: Array.from(typeSelect.options).map(option => option.textContent),
            filenames: Array.from(fileSelect.options).map(option => option.value),
            selected: Array.from(fileSelect.selectedOptions).map(option => option.value)
          };
          runButton.click();
          while (document.getElementById('docsHtmlImportRoot').dataset.studioBusy === 'true') {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          const childFailure = {
            destination: document.getElementById('docsHtmlImportScopeSelect').value,
            destinationDisabled: document.getElementById('docsHtmlImportScopeSelect').disabled,
            runDisabled: runButton.disabled,
            selected: Array.from(fileSelect.selectedOptions).map(option => option.value),
            status: document.getElementById('docsHtmlImportStatus').textContent,
            statusState: document.getElementById('docsHtmlImportStatus').dataset.state || '',
            terminalCount: terminalDetails.length
          };
          runButton.click();
          while (terminalDetails.length < 2) {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          while (document.getElementById('docsHtmlImportRoot').dataset.studioBusy === 'true') {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          const resultLink = document.querySelector('[data-doc-source-link]');
          const childResult = {
            link: {
              scope: resultLink?.dataset.scope || '',
              subScope: resultLink?.dataset.subScope || '',
              docId: resultLink?.dataset.docId || ''
            },
            terminal: {
              scope: terminalDetails[1].scope,
              subScope: terminalDetails[1].subScope,
              docId: terminalDetails[1].docId,
              target: terminalDetails[1].target,
              resultCount: terminalDetails[1].results.length
            }
          };
          resultLink.click();
          await new Promise(resolve => setTimeout(resolve, 0));

          typeSelect.value = importModule.DOCS_IMPORT_MODE_DATA_SHARING;
          typeSelect.dispatchEvent(new Event('change', { bubbles: true }));
          const childPackageInitial = {
            filenames: Array.from(fileSelect.options).map(option => option.value),
            labels: Array.from(fileSelect.options).map(option => option.textContent),
            selected: Array.from(fileSelect.selectedOptions).map(option => option.value),
            runDisabled: runButton.disabled,
            selectionBarHidden: selectionBar.hidden
          };
          fileSelect.options[0].selected = true;
          fileSelect.dispatchEvent(new Event('change', { bubbles: true }));
          const childPackageSelected = {
            selected: Array.from(fileSelect.selectedOptions).map(option => option.value),
            runDisabled: runButton.disabled,
            runLabel: runButton.textContent
          };
          runButton.click();
          for (
            let attempt = 0;
            attempt < 1000
              && document.getElementById('docsViewerImportCollectionModal').hidden;
            attempt += 1
          ) {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          const childPackageConfirmation = {
            chooserHidden: document.getElementById('docsViewerImportModal').hidden,
            planHidden: document.getElementById('docsViewerImportCollectionModal').hidden,
            visibleDialogs: Array.from(
              document.querySelectorAll('.docsViewer__modal')
            ).filter(modal => !modal.hidden).length,
            footerCommands: Array.from(
              document.querySelectorAll(
                '#docsViewerImportCollectionModal [data-collection-command]:not([hidden])'
              )
            ).map(button => button.dataset.collectionCommand),
            backButtons: Array.from(
              document.querySelectorAll('#docsViewerImportCollectionModal button')
            ).filter(button => button.textContent.trim().toLowerCase() === 'back').length,
            planInScrollableBody: document.querySelector(
              '#docsViewerImportCollectionModal .docsViewer__modalBody #docsImportCollectionView'
            ) !== null,
            confirmInFixedActions: document.querySelector(
              '#docsViewerImportCollectionModal .docsViewer__modalActions '
              + '[data-collection-command="confirm"]'
            ) !== null
          };
          document.getElementById('docsImportCollectionCancel').click();
          await new Promise(resolve => setTimeout(resolve, 0));
          const childPackageCancelled = {
            status: document.getElementById('docsImportCollectionStatus').textContent,
            chooserHidden: document.getElementById('docsViewerImportModal').hidden,
            planHidden: document.getElementById('docsViewerImportCollectionModal').hidden
          };
          await modalController.openImportModal({
            restoreFocus: document.getElementById('importTrigger')
          });
          runButton.click();
          for (
            let attempt = 0;
            attempt < 1000
              && document.getElementById('docsViewerImportCollectionModal').hidden;
            attempt += 1
          ) {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          document.getElementById('docsImportCollectionConfirm').click();
          while (document.getElementById('docsHtmlImportRoot').dataset.studioBusy === 'true') {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          const childPackageFailure = {
            status: document.getElementById('docsImportCollectionStatus').textContent,
            statusState: document.getElementById('docsImportCollectionStatus').dataset.state || '',
            retryAvailable: !document.getElementById('docsImportCollectionConfirm').hidden,
            selected: Array.from(fileSelect.selectedOptions).map(option => option.value),
            terminalCount: terminalDetails.length
          };
          document.getElementById('docsImportCollectionConfirm').click();
          while (terminalDetails.length < 3) {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          while (document.getElementById('docsHtmlImportRoot').dataset.studioBusy === 'true') {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          const childPackageRefreshFailure = {
            retryAvailable: !document.getElementById('docsImportCollectionRetry').hidden,
            status: document.getElementById('docsImportCollectionStatus').textContent,
            statusState: document.getElementById('docsImportCollectionStatus').dataset.state || '',
            terminalCount: terminalDetails.length
          };
          document.getElementById('docsImportCollectionRetry').click();
          while (terminalDetails.length < 4) {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          while (document.getElementById('docsHtmlImportRoot').dataset.studioBusy === 'true') {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
          const childPackageResult = {
            status: document.getElementById('docsImportCollectionStatus').textContent,
            statusState: document.getElementById('docsImportCollectionStatus').dataset.state || '',
            closeVisible: !document.getElementById('docsImportCollectionClose').hidden,
            terminal: {
              scope: terminalDetails[3].scope,
              subScope: terminalDetails[3].subScope,
              docId: terminalDetails[3].docId,
              target: terminalDetails[3].target,
              outcome: terminalDetails[3].result.outcome
            }
          };

          importApp.setDestination(null, { fallbackScope: 'library' });
          const restoredGlobal = {
            scopeDisabled: document.getElementById('docsHtmlImportScopeSelect').disabled,
            scopeLabels: Array.from(
              document.getElementById('docsHtmlImportScopeSelect').options
            ).map(option => option.textContent),
            scopeValue: document.getElementById('docsHtmlImportScopeSelect').value,
            typeDisabled: typeSelect.disabled,
            typeLabels: Array.from(typeSelect.options).map(option => option.textContent)
          };

          return {
            initial,
            afterSelectAll,
            childDestination,
            childFailure,
            childPackageCancelled,
            childPackageConfirmation,
            childPackageFailure,
            childPackageInitial,
            childPackageRefreshFailure,
            childPackageResult,
            childPackageSelected,
            childResult,
            globalPackageConfirmation,
            packageMode,
            restoredGlobal,
            terminal: {
              scope: terminalDetails[0].scope,
              docId: terminalDetails[0].docId,
              resultCount: terminalDetails[0].results.length
            }
          };
        }""",
        base_url,
    )

    expected_initial = {
        "type": "files",
        "typeLabels": ["Documents (4)", "Document packages (1)"],
        "multiple": True,
        "filenames": ["alpha.md", "beta.html", "word.docx", "notes.json"],
        "selected": ["alpha.md"],
        "selectionCount": "1 selected",
        "promptMetaHidden": True,
        "runLabel": "Import selected",
    }
    if result["initial"] != expected_initial:
        raise AssertionError(f"unexpected initial ordinary-file mode: {result!r}")
    expected_select_all = {
        "selected": ["alpha.md", "beta.html", "word.docx", "notes.json"],
        "selectionCount": "4 selected",
        "selectAllLabel": "Clear selection",
        "promptMetaHidden": False,
    }
    if result["afterSelectAll"] != expected_select_all:
        raise AssertionError(f"Select all did not select only ordinary files: {result!r}")
    expected_package_mode = {
        "type": "data_sharing_packages",
        "multiple": False,
        "filenames": ["reviewed.jsonl"],
        "selected": ["reviewed.jsonl"],
        "selectionBarHidden": True,
        "runLabel": "Preview collection",
    }
    if result["packageMode"] != expected_package_mode:
        raise AssertionError(f"reviewed-package mode was not isolated and single-select: {result!r}")
    assert result["globalPackageConfirmation"] == {
        "modalId": "docsViewerImportCollectionModal",
        "chooserHidden": True,
        "footerCommands": ["cancel", "confirm"],
    }
    assert result["childDestination"] == {
        "locationUnchanged": True,
        "scopeDisabled": True,
        "scopeLabels": ["studio / Tags"],
        "scopeValue": "studio",
        "typeDisabled": False,
        "typeLabels": ["Documents (4)", "Document packages (1)"],
        "filenames": ["alpha.md", "beta.html", "word.docx", "notes.json"],
        "selected": ["alpha.md"],
    }
    assert result["childFailure"] == {
        "destination": "studio",
        "destinationDisabled": True,
        "runDisabled": False,
        "selected": ["alpha.md"],
        "status": "Synthetic child Import failure.",
        "statusState": "error",
        "terminalCount": 1,
    }
    child_target = {
        "scope": "studio",
        "sub_scope": "tags",
        "doc_id": "alpha",
    }
    assert result["childResult"] == {
        "link": {
            "scope": "studio",
            "subScope": "tags",
            "docId": "alpha",
        },
        "terminal": {
            "scope": "studio",
            "subScope": "tags",
            "docId": "alpha",
            "target": child_target,
            "resultCount": 1,
        },
    }
    assert result["childPackageInitial"] == {
        "filenames": ["returned-tags.jsonl"],
        "labels": ["returned-tags.jsonl — studio / Tags — 2 documents"],
        "selected": [],
        "runDisabled": True,
        "selectionBarHidden": True,
    }
    assert result["childPackageSelected"] == {
        "selected": ["returned-tags.jsonl"],
        "runDisabled": False,
        "runLabel": "Preview collection",
    }
    assert result["childPackageConfirmation"] == {
        "chooserHidden": True,
        "planHidden": False,
        "visibleDialogs": 1,
        "footerCommands": ["cancel", "confirm"],
        "backButtons": 0,
        "planInScrollableBody": True,
        "confirmInFixedActions": True,
    }
    assert result["childPackageCancelled"] == {
        "status": "Collection import cancelled before apply.",
        "chooserHidden": True,
        "planHidden": True,
    }
    assert result["childPackageFailure"] == {
        "status": "Synthetic returned-package apply failure.",
        "statusState": "error",
        "retryAvailable": True,
        "selected": ["returned-tags.jsonl"],
        "terminalCount": 2,
    }
    assert result["childPackageRefreshFailure"] == {
        "retryAvailable": True,
        "status": (
            "Package import completed, but the collection report refresh failed. "
            "Retry the report refresh without importing again."
        ),
        "statusState": "error",
        "terminalCount": 3,
    }
    assert result["childPackageResult"] == {
        "status": "Collection import finished with outcome: completed.",
        "statusState": "success",
        "closeVisible": True,
        "terminal": {
            "scope": "studio",
            "subScope": "tags",
            "docId": "tag-a",
            "target": {"scope": "studio", "sub_scope": "tags"},
            "outcome": "completed",
        },
    }
    assert result["restoredGlobal"] == {
        "scopeDisabled": False,
        "scopeLabels": ["studio", "library"],
        "scopeValue": "library",
        "typeDisabled": False,
        "typeLabels": ["Documents (4)", "Document packages (1)"],
    }
    if [request["staged_filename"] for request in import_requests] != [
        "alpha.md",
        "beta.html",
        "beta.html",
        "word.docx",
        "notes.json",
        "reviewed.jsonl",
        "alpha.md",
        "alpha.md",
        "returned-tags.jsonl",
        "returned-tags.jsonl",
        "returned-tags.jsonl",
        "returned-tags.jsonl",
    ]:
        raise AssertionError(f"ordinary multi-import crossed the package boundary: {import_requests!r}")
    beta_requests = [request for request in import_requests if request["staged_filename"] == "beta.html"]
    if [request.get("confirm_interactive_html_overwrite") for request in beta_requests] != [False, True]:
        raise AssertionError(f"interactive HTML replacement confirmation contract drifted: {import_requests!r}")
    removed_fields = {"overwrite_doc_id", "replacement_doc_id"}
    if any(removed_fields & set(request) for request in import_requests):
        raise AssertionError(f"ordinary import still sent retired document collision fields: {import_requests!r}")
    if result["terminal"] != {"scope": "studio", "docId": "notes", "resultCount": 4}:
        raise AssertionError(f"multi-import did not identify the last imported doc: {result!r}")
    if any(request.get("sub_scope") != "tags" for request in import_requests[-2:]):
        raise AssertionError(f"returned-package retries did not keep their exact destination: {import_requests!r}")
    if any(request.get("sub_scope") != "tags" for request in import_requests[-6:]):
        raise AssertionError(f"child Import retries did not keep their exact destination: {import_requests!r}")
    if any(request.get("sub_scope") for request in import_requests[:-6]):
        raise AssertionError(f"parent Import requests unexpectedly gained a child target: {import_requests!r}")
    package_requests = [
        request for request in import_requests
        if request["staged_filename"] == "returned-tags.jsonl"
    ]
    if [request.get("preview_only") for request in package_requests] != [
        True,
        True,
        False,
        False,
    ]:
        raise AssertionError(f"package cancel or retry crossed the preview/apply boundary: {package_requests!r}")
    expected_package_identity = {
        "export_id": "ds_20260730T120000Z",
        "source_sha256": "a" * 64,
        "trusted_metadata_sha256": "b" * 64,
    }
    for request in package_requests[2:]:
        if any(request.get(key) != value for key, value in expected_package_identity.items()):
            raise AssertionError(f"package apply lost its confirmed identity: {package_requests!r}")
    if not returned_listing_requests:
        raise AssertionError("child Import did not discover returned packages")
    listing_url = returned_listing_requests[-1]
    if "scope=studio" not in listing_url or "sub_scope=tags" not in listing_url:
        raise AssertionError(f"returned-package discovery was not exact: {returned_listing_requests!r}")
    if source_requests != [
        {
            "scope": "studio",
            "sub_scope": "tags",
            "doc_id": "alpha",
            "editor": "vscode",
        }
    ]:
        raise AssertionError(f"child result Source did not use its exact target: {source_requests!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", default=".", help="Repository root to serve.")
    args = parser.parse_args(argv)
    server, base_url = start_static_server(Path(args.site_root))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            errors: list[str] = []
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.goto(base_url, wait_until="domcontentloaded")
                assert_multi_selection(page, base_url)
            finally:
                browser.close()
            if errors:
                raise AssertionError(f"page errors: {errors}")
    finally:
        server.shutdown()
        server.server_close()
    print("Docs Import multi-selection modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

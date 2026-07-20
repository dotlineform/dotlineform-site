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
    staged_files = [
        {"filename": "alpha.md", "source_format": "markdown"},
        {"filename": "beta.html", "source_format": "html"},
        {"filename": "word.docx", "source_format": "docx"},
        {"filename": "notes.json", "source_format": "file"},
        {
            "filename": "reviewed.jsonl",
            "source_format": "data_sharing_documents",
            "review_package_ids": ["fixture-review"],
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
    page.route("**/health", lambda route: fulfill(route, {"ok": True}))
    page.route(
        "**/docs/import-source-files",
        lambda route: fulfill(route, {"ok": True, "available": True, "files": staged_files}),
    )

    def fulfill_import(route) -> None:
        body = route.request.post_data_json
        import_requests.append(body)
        filename = str(body["staged_filename"])
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
                "staged_filename": filename,
                "doc_id": doc_id,
                "summary_text": f"Imported {filename}",
                "import_preview": {
                    "source_format": source_format,
                    "source_stats": {"chars": 10, "links": 0, "images": 0},
                },
            },
        )

    page.route("**/docs/import-source", fulfill_import)
    result = page.evaluate(
        """async (baseUrl) => {
          document.body.innerHTML = '<div id="mount"></div>';
          const shellModule = await import('/docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js');
          const importModule = await import('/docs-viewer/runtime/js/import/docs-html-import.js');
          shellModule.renderDocsViewerManagementShell({
            document,
            mount: document.getElementById('mount')
          });

          let terminalDetail = null;
          let resolveTerminal;
          const terminalPromise = new Promise(resolve => { resolveTerminal = resolve; });
          await importModule.initDocsHtmlImport({
            root: document.getElementById('docsHtmlImportRoot'),
            bootStatus: document.getElementById('docsHtmlImportBootStatus'),
            managementBaseUrl: baseUrl,
            docsViewerConfigUrl: '/docs-viewer/config/defaults/docs-viewer-config.json',
            initialScope: 'studio',
            persistScope: false,
            onTerminalResult(detail) {
              terminalDetail = detail;
              resolveTerminal();
            }
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
          await terminalPromise;
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

          return {
            initial,
            afterSelectAll,
            packageMode,
            terminal: {
              scope: terminalDetail.scope,
              docId: terminalDetail.docId,
              resultCount: terminalDetail.results.length
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
    if [request["staged_filename"] for request in import_requests] != [
        "alpha.md",
        "beta.html",
        "beta.html",
        "word.docx",
        "notes.json",
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

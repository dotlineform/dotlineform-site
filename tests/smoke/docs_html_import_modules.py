#!/usr/bin/env python3
"""Smoke-check focused Docs HTML Import JavaScript modules."""

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
              <main id="docsHtmlImportRoot">
                <button id="docsHtmlImportRun" type="button"></button>
                <button id="docsHtmlImportConfirm" type="button" hidden></button>
                <button id="docsHtmlImportCancel" type="button" hidden></button>
                <p id="docsHtmlImportStatus"></p>
                <section id="docsHtmlImportWarning" hidden>
                  <h2 id="docsHtmlImportCollisionHeading"></h2>
                  <p id="docsHtmlImportCollisionBody"></p>
                  <p id="docsHtmlImportCollisionMeta"></p>
                </section>
                <section id="docsHtmlImportResult" hidden>
                  <h2 id="docsHtmlImportResultTitle"></h2>
                  <dl id="docsHtmlImportResultGrid"></dl>
                  <span id="docsHtmlImportResultDocId"></span>
                  <span id="docsHtmlImportResultCounts"></span>
                </section>
                <section id="docsHtmlImportWarnings" hidden>
                  <h3 id="docsHtmlImportWarningsHeading"></h3>
                  <ul id="docsHtmlImportWarningsList"></ul>
                </section>
              </main>
            `;
            const workflow = await import('/assets/docs-viewer/js/docs-html-import-workflow.js');
            const render = await import('/assets/docs-viewer/js/docs-html-import-render.js');
            const root = document.getElementById('docsHtmlImportRoot');
            const config = {
                docs_html_import: {
                    running_status: 'Running import',
                    running_status_all: 'Importing {index} of {total}: {filename}',
                    overwrite_required: 'Overwrite required.',
                    replacement_doc_id_required: 'Replacement required.',
                    filename_conflict_cancelled: 'Import cancelled.',
                    import_failed: 'Import failed.',
                    import_all_success: 'Imported {count} files.',
                    result_title: 'Imported',
                    result_title_all: 'Imported {count} files',
                    result_summary_counts: '{links} links, {images} images, {svg} SVG, {details} details blocks',
                    result_markdown_counts: '{chars} chars, {links} links, {images} images',
                    result_markdown_package_counts: '{chars} chars, {links} links, {images} images, {attachments} attachments',
                    script_file_result_type: 'script file',
                    image_media_result_type: 'image, {format} <= {max_width}px',
                    attachment_media_result_type: 'attachment',
                    warnings_heading: 'Warnings',
                    collision_heading: 'Overwrite warning',
                    collision_body: 'Overwrite doc body',
                    interactive_asset_collision_body: 'Overwrite asset body',
                    interactive_asset_overwrite_required: 'Asset overwrite required: {path}',
                    filename_conflict_heading: 'File already exists',
                    filename_conflict_body: 'A source file named {doc_id}.md already exists.',
                    filename_conflict_cancel_button: 'Cancel',
                    filename_conflict_replace_button: 'Replace',
                    filename_conflict_replace_all_button: 'Replace all',
                    filename_conflict_ok_button: 'OK',
                    replacement_doc_id_label: 'doc_id'
                }
            };
            const state = {
                root,
                config,
                routePath: '/docs/',
                managementBaseUrl: 'http://docs-management.test',
                runButton: document.getElementById('docsHtmlImportRun'),
                confirmButton: document.getElementById('docsHtmlImportConfirm'),
                cancelButton: document.getElementById('docsHtmlImportCancel'),
                statusNode: document.getElementById('docsHtmlImportStatus'),
                warningNode: document.getElementById('docsHtmlImportWarning'),
                collisionHeadingNode: document.getElementById('docsHtmlImportCollisionHeading'),
                collisionBodyNode: document.getElementById('docsHtmlImportCollisionBody'),
                collisionMetaNode: document.getElementById('docsHtmlImportCollisionMeta'),
                resultNode: document.getElementById('docsHtmlImportResult'),
                resultTitleNode: document.getElementById('docsHtmlImportResultTitle'),
                resultGridNode: document.getElementById('docsHtmlImportResultGrid'),
                resultDocIdNode: document.getElementById('docsHtmlImportResultDocId'),
                resultCountsNode: document.getElementById('docsHtmlImportResultCounts'),
                warningsWrap: document.getElementById('docsHtmlImportWarnings'),
                warningsHeading: document.getElementById('docsHtmlImportWarningsHeading'),
                warningsList: document.getElementById('docsHtmlImportWarningsList'),
                pendingOverwriteDocId: '',
                pendingOverwriteResolver: null,
                replaceAllOverwrites: false,
                isRunning: false
            };
            state.confirmButton.addEventListener('click', () => {
                if (state.pendingOverwriteResolver) state.pendingOverwriteResolver('confirm');
            });
            state.cancelButton.addEventListener('click', () => {
                if (state.pendingOverwriteResolver) state.pendingOverwriteResolver('cancel');
            });
            window.__docsHtmlImportModuleSmoke = { workflow, render, state };
        }"""
    )


def ok_response(payload: str) -> str:
    return payload


def fulfill_json(route, body: str, status: int = 200) -> None:
    route.fulfill(
        status=status,
        headers={
            "access-control-allow-origin": "*",
            "content-type": "application/json",
        },
        body=body,
    )


def assert_result_rendering(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const smoke = window.__docsHtmlImportModuleSmoke;
            const { render, state } = smoke;
            render.renderDocsHtmlImportResult(state, [
                {
                    scope: 'library',
                    doc_id: 'alpha',
                    staged_filename: 'alpha.md',
                    summary_text: 'Imported alpha.',
                    import_preview: {
                        source_format: 'markdown',
                        source_stats: { chars: 120, links: 2, images: 1 },
                        warnings: ['Review <unsafe> warning'],
                        media_plans: [
                            {
                                title: 'Diagram',
                                source_path: 'diagram.png',
                                kind: 'image',
                                media_path: 'docs/library/img/diagram.webp',
                                conversion: { format: 'webp', max_width: 640 }
                            }
                        ]
                    },
                    interactive_html_written: [
                        { display_name: 'Interactive view', target_path: 'assets/docs/alpha.html' }
                    ]
                },
                {
                    scope: 'library',
                    doc_id: 'beta',
                    staged_filename: 'beta.md',
                    import_preview: {
                        source_format: 'markdown_package',
                        source_stats: { chars: 70, links: 1, images: 0, attachments: 1 },
                        media_plans: [
                            {
                                title: 'Dataset',
                                source_path: 'dataset.csv',
                                kind: 'attachment',
                                media_path: 'docs/library/files/dataset.csv'
                            }
                        ]
                    }
                }
            ]);
            return {
                title: state.resultTitleNode.textContent.trim(),
                resultHidden: state.resultNode.hidden,
                rows: Array.from(state.resultGridNode.querySelectorAll('div')).map((row) => row.textContent.replace(/\\s+/g, ' ').trim()),
                sourceLinks: Array.from(state.resultGridNode.querySelectorAll('[data-doc-source-link]')).map((link) => ({
                    text: link.textContent.trim(),
                    scope: link.dataset.scope,
                    docId: link.dataset.docId
                })),
                warningsHidden: state.warningsWrap.hidden,
                warningsHtml: state.warningsList.innerHTML
            };
        }"""
    )
    if result["title"] != "Imported 2 files" or result["resultHidden"] is not False:
        raise AssertionError(f"result title/visibility changed: {result!r}")
    if result["sourceLinks"] != [
        {"text": "alpha", "scope": "library", "docId": "alpha"},
        {"text": "beta", "scope": "library", "docId": "beta"},
    ]:
        raise AssertionError(f"source links changed: {result!r}")
    expected_fragments = [
        "alpha.md: alpha120 chars, 2 links, 1 images",
        "Interactive viewscript file",
        "Diagram (diagram.png)image, WEBP <= 640px: docs/library/img/diagram.webp",
        "beta.md: beta70 chars, 1 links, 0 images, 1 attachments",
        "Dataset (dataset.csv)attachment: docs/library/files/dataset.csv",
    ]
    for fragment in expected_fragments:
        if fragment not in result["rows"]:
            raise AssertionError(f"missing result row {fragment!r}: {result!r}")
    if result["warningsHidden"] is not False or "&lt;unsafe&gt;" not in result["warningsHtml"]:
        raise AssertionError(f"warnings rendering changed: {result!r}")


def assert_overwrite_preview_flow(page: Page) -> None:
    requests: list[dict[str, object]] = []
    responses = [
        ok_response(
            """{
              "ok": true,
              "preview_only": true,
              "requires_overwrite_confirmation": true,
              "summary_text": "Overwrite required for existing-doc.",
              "scope": "library",
              "doc_id": "existing-doc",
              "staged_filename": "existing.html",
              "collision": { "doc_id": "existing-doc", "title": "Existing Doc" },
              "import_preview": {
                "proposed_doc_id": "existing-doc",
                "title": "Existing Doc",
                "source_format": "html",
                "source_stats": { "links": 1, "images": 0, "svg": 0, "details": 0 },
                "warnings": ["Preview warning"]
              }
            }"""
        ),
        ok_response(
            """{
              "ok": true,
              "preview_only": false,
              "scope": "library",
              "doc_id": "existing-doc",
              "staged_filename": "existing.html",
              "summary_text": "Imported existing-doc.",
              "import_preview": {
                "source_format": "html",
                "source_stats": { "links": 1, "images": 0, "svg": 0, "details": 0 }
              }
            }"""
        ),
    ]

    def handle(route) -> None:
        requests.append(route.request.post_data_json)
        fulfill_json(route, responses.pop(0))

    page.route("http://docs-management.test/docs/import-source", handle)
    result = page.evaluate(
        """async () => {
            const smoke = window.__docsHtmlImportModuleSmoke;
            const { workflow, state } = smoke;
            window.setTimeout(() => state.confirmButton.click(), 50);
            await workflow.runDocsHtmlImportWorkflow(state, {
                files: [{ filename: 'existing.html', source_format: 'html' }],
                scope: 'library',
                includePromptMeta: true,
                routePath: '/docs/?mode=manage',
                managementBaseUrl: state.managementBaseUrl,
                config: state.config
            });
            return {
                status: state.statusNode.textContent.trim(),
                statusState: state.statusNode.dataset.state || '',
                warningHidden: state.warningNode.hidden,
                resultHidden: state.resultNode.hidden,
                resultText: state.resultGridNode.textContent.replace(/\\s+/g, ' ').trim(),
                buttons: {
                    run: state.runButton.disabled,
                    confirm: state.confirmButton.disabled,
                    cancel: state.cancelButton.disabled
                },
                isRunning: state.isRunning
            };
        }"""
    )
    page.unroute("http://docs-management.test/docs/import-source", handle)

    if len(requests) != 2:
        raise AssertionError(f"expected preview and confirmed write requests: {requests!r}")
    first, second = requests
    if first.get("scope") != "library" or first.get("include_prompt_meta") is not True:
        raise AssertionError(f"preview request shape changed: {requests!r}")
    if first.get("confirm_overwrite") is not False or first.get("overwrite_doc_id") != "":
        raise AssertionError(f"preview request should not confirm overwrite: {requests!r}")
    if first.get("activity_context", {}).get("route") != "/docs/?mode=manage":
        raise AssertionError(f"activity context route was not explicit: {requests!r}")
    if second.get("confirm_overwrite") is not True or second.get("overwrite_doc_id") != "existing-doc":
        raise AssertionError(f"confirmed overwrite request changed: {requests!r}")
    if result["status"] != "Imported existing-doc." or result["statusState"] != "success":
        raise AssertionError(f"overwrite flow status changed: {result!r}")
    if result["warningHidden"] is not True or result["resultHidden"] is not False:
        raise AssertionError(f"overwrite flow visibility changed: {result!r}")
    if "existing-doc" not in result["resultText"]:
        raise AssertionError(f"overwrite result was not rendered: {result!r}")
    if result["buttons"] != {"run": False, "confirm": False, "cancel": False} or result["isRunning"]:
        raise AssertionError(f"workflow cleanup changed: {result!r}")


def assert_replacement_doc_id_flow(page: Page) -> None:
    requests: list[dict[str, object]] = []
    responses = [
        ok_response(
            """{
              "ok": true,
              "preview_only": true,
              "replacement_doc_id_required": true,
              "summary_text": "Replacement required.",
              "scope": "library",
              "doc_id": "existing-doc",
              "staged_filename": "existing.md",
              "collision": { "doc_id": "existing-doc", "title": "Existing Doc" },
              "import_preview": {
                "proposed_doc_id": "existing-doc",
                "title": "Existing Doc",
                "source_format": "markdown",
                "source_stats": { "chars": 25, "links": 0, "images": 0 },
                "warnings": ["Replacement preview warning"]
              }
            }"""
        ),
        ok_response(
            """{
              "ok": true,
              "preview_only": false,
              "scope": "library",
              "doc_id": "renamed-doc",
              "staged_filename": "existing.md",
              "summary_text": "Imported renamed-doc.",
              "import_preview": {
                "source_format": "markdown",
                "source_stats": { "chars": 25, "links": 0, "images": 0 }
              }
            }"""
        ),
    ]

    def handle(route) -> None:
        requests.append(route.request.post_data_json)
        fulfill_json(route, responses.pop(0))

    page.route("http://docs-management.test/docs/import-source", handle)
    result = page.evaluate(
        """async () => {
            const smoke = window.__docsHtmlImportModuleSmoke;
            const { workflow, state } = smoke;
            const chooseReplacement = new Promise((resolve) => {
                const started = Date.now();
                const timer = window.setInterval(() => {
                    const input = document.getElementById('docsHtmlImportReplacementDocId');
                    const okButton = document.querySelector('[data-role="filename-conflict-ok"]');
                    if (input && okButton) {
                        window.clearInterval(timer);
                        input.value = 'renamed-doc';
                        okButton.click();
                        resolve(true);
                    } else if (Date.now() - started > 2000) {
                        window.clearInterval(timer);
                        resolve(false);
                    }
                }, 20);
            });
            await workflow.runDocsHtmlImportWorkflow(state, {
                files: [{ filename: 'existing.md', source_format: 'markdown' }],
                scope: 'library',
                includePromptMeta: true,
                routePath: '/docs/',
                managementBaseUrl: state.managementBaseUrl,
                config: state.config
            });
            const replacementChosen = await chooseReplacement;
            return {
                status: state.statusNode.textContent.trim(),
                statusState: state.statusNode.dataset.state || '',
                replacementChosen,
                modalRemaining: Boolean(document.querySelector('[data-role="docs-import-filename-conflict-modal"]')),
                resultText: state.resultGridNode.textContent.replace(/\\s+/g, ' ').trim()
            };
        }"""
    )
    page.unroute("http://docs-management.test/docs/import-source", handle)

    if len(requests) != 2:
        raise AssertionError(f"expected replacement preview and write requests: {requests!r}")
    first, second = requests
    if first.get("include_prompt_meta") is not False:
        raise AssertionError(f"markdown import should not send prompt meta: {requests!r}")
    if second.get("replacement_doc_id") != "renamed-doc" or second.get("confirm_overwrite") is not False:
        raise AssertionError(f"replacement request changed: {requests!r}")
    if result != {
        "status": "Imported renamed-doc.",
        "statusState": "success",
        "replacementChosen": True,
        "modalRemaining": False,
        "resultText": "renamed-doc25 chars, 0 links, 0 images",
    }:
        raise AssertionError(f"replacement flow result changed: {result!r}")


def assert_write_failure_partial_result_fallback(page: Page) -> None:
    requests: list[dict[str, object]] = []
    responses = [
        ok_response(
            """{
              "ok": true,
              "preview_only": false,
              "scope": "library",
              "doc_id": "alpha",
              "staged_filename": "alpha.md",
              "summary_text": "Imported alpha.",
              "import_preview": {
                "source_format": "markdown",
                "source_stats": { "chars": 10, "links": 0, "images": 0 }
              }
            }"""
        ),
        ok_response("""{ "ok": false, "error": "write failed" }"""),
    ]

    def handle(route) -> None:
        requests.append(route.request.post_data_json)
        status = 500 if len(requests) == 2 else 200
        fulfill_json(route, responses.pop(0), status=status)

    page.route("http://docs-management.test/docs/import-source", handle)
    result = page.evaluate(
        """async () => {
            const smoke = window.__docsHtmlImportModuleSmoke;
            const { workflow, state } = smoke;
            await workflow.runDocsHtmlImportWorkflow(state, {
                files: [
                    { filename: 'alpha.md', source_format: 'markdown' },
                    { filename: 'beta.md', source_format: 'markdown' }
                ],
                scope: 'library',
                includePromptMeta: false,
                routePath: '/docs/',
                managementBaseUrl: state.managementBaseUrl,
                config: state.config
            });
            return {
                status: state.statusNode.textContent.trim(),
                statusState: state.statusNode.dataset.state || '',
                resultHidden: state.resultNode.hidden,
                resultTitle: state.resultTitleNode.textContent.trim(),
                resultText: state.resultGridNode.textContent.replace(/\\s+/g, ' ').trim(),
                buttons: {
                    run: state.runButton.disabled,
                    confirm: state.confirmButton.disabled,
                    cancel: state.cancelButton.disabled
                },
                pendingResolver: Boolean(state.pendingOverwriteResolver),
                isRunning: state.isRunning
            };
        }"""
    )
    page.unroute("http://docs-management.test/docs/import-source", handle)

    if len(requests) != 2 or requests[1].get("staged_filename") != "beta.md":
        raise AssertionError(f"write failure request sequence changed: {requests!r}")
    if result["status"] != "write failed" or result["statusState"] != "error":
        raise AssertionError(f"write failure status changed: {result!r}")
    if result["resultHidden"] is not False or result["resultTitle"] != "Imported":
        raise AssertionError(f"partial result fallback visibility changed: {result!r}")
    if "alpha" not in result["resultText"] or "beta" in result["resultText"]:
        raise AssertionError(f"partial result fallback changed: {result!r}")
    if result["buttons"] != {"run": False, "confirm": False, "cancel": False}:
        raise AssertionError(f"write failure button cleanup changed: {result!r}")
    if result["pendingResolver"] or result["isRunning"]:
        raise AssertionError(f"write failure state cleanup changed: {result!r}")


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
            assert_result_rendering(page)
            assert_overwrite_preview_flow(page)
            install_fixture(page)
            assert_replacement_doc_id_flow(page)
            install_fixture(page)
            assert_write_failure_partial_result_fallback(page)
        finally:
            browser.close()
            if server:
                server.shutdown()

    if errors:
        raise AssertionError(f"page errors during Docs HTML Import module smoke: {errors!r}")
    print("Docs HTML Import module smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Smoke-check Docs Viewer management import modal behavior."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from docs_viewer_management_modal_support import (
    REPO_ROOT,
    assert_hidden_with_focus,
    assert_shell,
    focus_wrap_id,
    install_modal_fixture,
    route_url,
    start_static_server,
    wait_for_focus,
)

def run_import_modal_check(page: Page) -> None:
    page.locator("#docsViewerManageImportButton").focus()
    page.locator("#docsHtmlImportLongResult").evaluate(
        """node => {
            node.textContent = Array(80).fill('Long imported result line with enough text to require the import body to scroll.').join(' ');
        }"""
    )
    page.evaluate("window.__docsViewerManagementModalSmoke.controller.openImportModal()")
    wait_for_focus(page, "docsViewerImportCancelButton")
    assert_shell(
        page,
        "#docsViewerImportModal",
        "Import docs",
        ["Cancel", "Import"],
        active_id="docsViewerImportCancelButton",
        size_class="docsViewer__modalCard--document",
    )
    layout = page.locator("#docsViewerImportModal").evaluate(
        """modal => {
            const card = modal.querySelector('.docsViewer__modalCard');
            const body = modal.querySelector('.docsViewer__importBody');
            const scrollRegion = modal.querySelector('.docsViewerImport__scrollRegion');
            const footer = modal.querySelector('.docsViewerImport__footer');
            const actions = modal.querySelector('.docsViewerImport__actions');
            const cardRect = card.getBoundingClientRect();
            const bodyRect = body.getBoundingClientRect();
            const scrollRect = scrollRegion.getBoundingClientRect();
            const footerRect = footer.getBoundingClientRect();
            const actionsRect = actions.getBoundingClientRect();
            return {
                cardOverflows: card.scrollHeight > card.clientHeight,
                bodyOverflows: body.scrollHeight > body.clientHeight,
                scrollRegionOverflows: scrollRegion.scrollHeight > scrollRegion.clientHeight,
                footerBelowScroll: footerRect.top >= scrollRect.bottom - 1,
                actionsInsideCard: actionsRect.bottom <= cardRect.bottom + 1,
                actionsInsideBody: actionsRect.bottom <= bodyRect.bottom + 1
            };
        }"""
    )
    if layout != {
        "cardOverflows": False,
        "bodyOverflows": False,
        "scrollRegionOverflows": True,
        "footerBelowScroll": True,
        "actionsInsideCard": True,
        "actionsInsideBody": True,
    }:
        raise AssertionError(f"import modal scroll boundary is wrong: {layout!r}")
    if focus_wrap_id(page, "#docsViewerImportCancelButton", "Shift+Tab") != "docsHtmlImportRun":
        raise AssertionError("import modal did not wrap focus backward to Import")
    page.keyboard.press("Escape")
    assert_hidden_with_focus(page, "#docsViewerImportModal", "docsViewerManageImportButton")


def run_import_render_module_check(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <main>
                <div id="docsHtmlImportWarning" hidden>
                  <h3 id="docsHtmlImportCollisionHeading"></h3>
                  <p id="docsHtmlImportCollisionBody"></p>
                  <p id="docsHtmlImportCollisionMeta"></p>
                </div>
                <button id="docsHtmlImportConfirm" type="button" hidden></button>
                <button id="docsHtmlImportCancel" type="button" hidden></button>
                <div id="docsHtmlImportResult" hidden>
                  <h3 id="docsHtmlImportResultTitle"></h3>
                  <dl id="docsHtmlImportResultGrid" class="docsViewerImport__resultGrid"></dl>
                  <div id="docsHtmlImportWarnings" hidden>
                    <h4 id="docsHtmlImportWarningsHeading"></h4>
                    <ul id="docsHtmlImportWarningsList"></ul>
                  </div>
                </div>
              </main>
            `;
            const render = await import('/docs-viewer/runtime/js/import/docs-html-import-render.js');
            const state = {
                config: {
                    docs_html_import: {
                        result_title_all: 'Imported {count} source files',
                        result_markdown_package_counts: '{chars} chars, {links} links, {images} images, {attachments} attachments',
                        result_summary_counts: '{links} links, {images} images, {svg} SVG, {details} details blocks',
                        image_media_result_type: 'image, {format} <= {max_width}px',
                        attachment_media_result_type: 'attachment',
                        warnings_heading: 'Import warnings',
                        collision_heading: 'Overwrite warning',
                        overwrite_required: 'Overwrite required: {doc_id} ({title}). Review the warning and confirm if you want to replace it.'
                    }
                },
                warningNode: document.getElementById('docsHtmlImportWarning'),
                collisionHeadingNode: document.getElementById('docsHtmlImportCollisionHeading'),
                collisionBodyNode: document.getElementById('docsHtmlImportCollisionBody'),
                collisionMetaNode: document.getElementById('docsHtmlImportCollisionMeta'),
                confirmButton: document.getElementById('docsHtmlImportConfirm'),
                cancelButton: document.getElementById('docsHtmlImportCancel'),
                resultNode: document.getElementById('docsHtmlImportResult'),
                resultTitleNode: document.getElementById('docsHtmlImportResultTitle'),
                resultGridNode: document.getElementById('docsHtmlImportResultGrid'),
                warningsWrap: document.getElementById('docsHtmlImportWarnings'),
                warningsHeading: document.getElementById('docsHtmlImportWarningsHeading'),
                warningsList: document.getElementById('docsHtmlImportWarningsList'),
                pendingOverwriteDocId: ''
            };
            render.renderDocsHtmlImportResult(state, [
                {
                    scope: 'library',
                    doc_id: 'alpha',
                    staged_filename: 'alpha.md',
                    import_preview: {
                        source_format: 'markdown_package',
                        source_stats: { chars: 42, links: 2, images: 1, attachments: 1 },
                        warnings: ['Use & check'],
                        media_plans: [
                            {
                                source_path: 'alpha-image-01.png',
                                title: 'Diagram <One>',
                                kind: 'image',
                                media_path: 'docs/library/img/alpha-image-01.png',
                                conversion: { format: 'webp', max_width: 640 }
                            },
                            {
                                source_path: 'alpha.pdf',
                                kind: 'attachment',
                                media_token: '[[media:docs/library/files/alpha.pdf]]'
                            }
                        ]
                    }
                },
                {
                    scope: 'library',
                    doc_id: 'beta',
                    staged_filename: 'beta.html',
                    import_preview: {
                        source_format: 'html',
                        source_stats: { links: 1, images: 0, svg: 0, details: 1 },
                        warnings: ['Second warning'],
                        media_plan: {
                            source_path: 'beta-image.png',
                            title: 'Beta image',
                            kind: 'image',
                            media_path: 'docs/library/img/beta-image.png'
                        }
                    }
                }
            ]);
            render.renderDocsHtmlImportOverwriteWarning(state, {
                collision: { doc_id: 'alpha', title: 'Alpha Doc' },
                import_preview: { proposed_doc_id: 'alpha', title: 'Alpha Doc' }
            });
            window.__docsHtmlImportRenderSmoke = {
                title: state.resultTitleNode.textContent.trim(),
                rows: Array.from(state.resultGridNode.querySelectorAll('dd')).map(node => node.textContent.trim()),
                warningsHeading: state.warningsHeading.textContent.trim(),
                warnings: Array.from(state.warningsList.querySelectorAll('li')).map(node => node.textContent.trim()),
                resultHidden: state.resultNode.hidden,
                warningHidden: state.warningNode.hidden,
                confirmHidden: state.confirmButton.hidden,
                pendingOverwriteDocId: state.pendingOverwriteDocId,
                collisionMeta: state.collisionMetaNode.textContent.trim(),
                alphaScope: state.resultGridNode.querySelector('[data-doc-source-link]')?.dataset.scope || ''
            };
        }"""
    )
    state = page.evaluate("window.__docsHtmlImportRenderSmoke")
    expected_rows = [
        "alpha.md: alpha",
        "42 chars, 2 links, 1 images, 1 attachments",
        "Diagram <One> (alpha-image-01.png)",
        "image, WEBP <= 640px: docs/library/img/alpha-image-01.png",
        "alpha.pdf",
        "attachment: [[media:docs/library/files/alpha.pdf]]",
        "beta.html: beta",
        "1 links, 0 images, 0 SVG, 1 details blocks",
        "Beta image (beta-image.png)",
        "attachment: docs/library/img/beta-image.png",
    ]
    if state["title"] != "Imported 2 source files" or state["rows"] != expected_rows:
        raise AssertionError(f"import render rows changed: {state!r}")
    if state["warningsHeading"] != "Import warnings":
        raise AssertionError(f"import warnings heading changed: {state!r}")
    if state["warnings"] != ["alpha.md: Use & check", "beta.html: Second warning"]:
        raise AssertionError(f"import warnings changed: {state!r}")
    if state["resultHidden"] or state["warningHidden"] or state["confirmHidden"]:
        raise AssertionError(f"import render did not reveal expected panels: {state!r}")
    if state["pendingOverwriteDocId"] != "alpha" or "alpha (Alpha Doc)" not in state["collisionMeta"]:
        raise AssertionError(f"overwrite warning rendering changed: {state!r}")
    if state["alphaScope"] != "library":
        raise AssertionError(f"source link data attributes changed: {state!r}")


def run_import_workflow_module_check(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <main id="docsHtmlImportRoot">
                <button id="docsHtmlImportRun" type="button"></button>
                <button id="docsHtmlImportConfirm" type="button" hidden></button>
                <button id="docsHtmlImportCancel" type="button" hidden></button>
                <p id="docsHtmlImportStatus"></p>
                <div id="docsHtmlImportWarning" hidden>
                  <h3 id="docsHtmlImportCollisionHeading"></h3>
                  <p id="docsHtmlImportCollisionBody"></p>
                  <p id="docsHtmlImportCollisionMeta"></p>
                </div>
                <div id="docsHtmlImportResult" hidden>
                  <h3 id="docsHtmlImportResultTitle"></h3>
                  <dl id="docsHtmlImportResultGrid" class="docsViewerImport__resultGrid"></dl>
                  <div id="docsHtmlImportWarnings" hidden>
                    <h4 id="docsHtmlImportWarningsHeading"></h4>
                    <ul id="docsHtmlImportWarningsList"></ul>
                  </div>
                </div>
              </main>
            `;
            const workflow = await import('/docs-viewer/runtime/js/import/docs-html-import-workflow.js');
            const state = {
                root: document.getElementById('docsHtmlImportRoot'),
                config: {
                    docs_html_import: {
                        running_status: 'Running import.',
                        overwrite_required: 'Overwrite required: {doc_id} ({title}).',
                        collision_heading: 'Overwrite warning',
                        collision_body: 'Collision body.',
                        result_title: 'Imported',
                        result_summary_counts: '{links} links, {images} images, {svg} SVG, {details} details blocks',
                        warnings_heading: 'Warnings'
                    }
                },
                managementBaseUrl: 'http://docs-management.test',
                routePath: '/docs/?import=1',
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
                warningsWrap: document.getElementById('docsHtmlImportWarnings'),
                warningsHeading: document.getElementById('docsHtmlImportWarningsHeading'),
                warningsList: document.getElementById('docsHtmlImportWarningsList'),
                pendingOverwriteDocId: '',
                pendingOverwriteResolver: null,
                replaceAllOverwrites: false
            };
            const requests = [];
            const busyStates = [];
            window.fetch = async (url, options = {}) => {
                const body = options.body ? JSON.parse(options.body) : {};
                requests.push({ url: String(url), body });
                if (requests.length === 1) {
                    return {
                        ok: true,
                        status: 200,
                        json: async () => ({
                            ok: true,
                            preview_only: true,
                            requires_overwrite_confirmation: true,
                            collision: { doc_id: 'alpha', title: 'Alpha Doc' },
                            import_preview: {
                                source_format: 'html',
                                source_stats: { links: 1, images: 0, svg: 0, details: 0 },
                                warnings: ['Existing doc will be replaced.']
                            },
                            summary_text: 'Overwrite required.'
                        })
                    };
                }
                return {
                    ok: true,
                    status: 200,
                    json: async () => ({
                        ok: true,
                        scope: 'library',
                        doc_id: 'alpha',
                        staged_filename: 'alpha.html',
                        import_preview: {
                            source_format: 'html',
                            source_stats: { links: 1, images: 0, svg: 0, details: 0 },
                            warnings: []
                        },
                        summary_text: 'Imported alpha.'
                    })
                };
            };
            const runPromise = workflow.runDocsHtmlImportWorkflow(state, {
                files: [{ filename: 'alpha.html', source_format: 'html' }],
                scope: 'library',
                includePromptMeta: true,
                routePath: state.routePath,
                managementBaseUrl: state.managementBaseUrl,
                config: state.config,
                onRunningChange: busy => busyStates.push({ busy, runDisabled: state.runButton.disabled })
            });
            for (let tries = 0; tries < 100 && !state.pendingOverwriteResolver; tries += 1) {
                await new Promise(resolve => window.setTimeout(resolve, 10));
            }
            const confirmVisible = !state.warningNode.hidden && !state.confirmButton.hidden && state.statusNode.dataset.state === 'warn';
            if (!state.pendingOverwriteResolver) {
                throw new Error('overwrite resolver was not installed');
            }
            state.pendingOverwriteResolver('confirm');
            await runPromise;
            window.__docsHtmlImportWorkflowSmoke = {
                requests,
                busyStates,
                confirmVisible,
                status: state.statusNode.textContent.trim(),
                statusState: state.statusNode.dataset.state || '',
                resultHidden: state.resultNode.hidden,
                warningHidden: state.warningNode.hidden,
                runDisabled: state.runButton.disabled,
                confirmDisabled: state.confirmButton.disabled,
                pendingResolver: Boolean(state.pendingOverwriteResolver),
                rows: Array.from(state.resultGridNode.querySelectorAll('dd')).map(node => node.textContent.trim())
            };
        }"""
    )
    state = page.evaluate("window.__docsHtmlImportWorkflowSmoke")
    if len(state["requests"]) != 2:
        raise AssertionError(f"workflow did not issue preview/write requests: {state!r}")
    first_body = state["requests"][0]["body"]
    second_body = state["requests"][1]["body"]
    if first_body["scope"] != "library" or first_body["staged_filename"] != "alpha.html":
        raise AssertionError(f"workflow initial request changed: {state!r}")
    if first_body["include_prompt_meta"] is not True or first_body["confirm_overwrite"] is not False:
        raise AssertionError(f"workflow initial request flags changed: {state!r}")
    if second_body["overwrite_doc_id"] != "alpha" or second_body["confirm_overwrite"] is not True:
        raise AssertionError(f"workflow overwrite request changed: {state!r}")
    if second_body["activity_context"]["route"] != "/docs/?import=1":
        raise AssertionError(f"workflow activity context route changed: {state!r}")
    if not state["confirmVisible"]:
        raise AssertionError(f"workflow did not expose overwrite confirmation: {state!r}")
    if state["busyStates"] != [{"busy": True, "runDisabled": True}, {"busy": False, "runDisabled": False}]:
        raise AssertionError(f"workflow busy transitions changed: {state!r}")
    if state["status"] != "Imported alpha." or state["statusState"] != "success":
        raise AssertionError(f"workflow success status changed: {state!r}")
    if state["resultHidden"] or not state["warningHidden"] or state["runDisabled"] or state["confirmDisabled"] or state["pendingResolver"]:
        raise AssertionError(f"workflow final UI state changed: {state!r}")
    if state["rows"] != ["alpha", "1 links, 0 images, 0 SVG, 0 details blocks"]:
        raise AssertionError(f"workflow result rows changed: {state!r}")


def run_import_result_rows_check(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <main id="docsHtmlImportRoot" data-management-base-url="http://docs-management.test">
                <p id="docsHtmlImportIntro"></p>
                <label><span id="docsHtmlImportFileLabel"></span><select id="docsHtmlImportFileSelect"></select></label>
                <label><span id="docsHtmlImportScopeLabel"></span><select id="docsHtmlImportScopeSelect"></select></label>
                <label id="docsHtmlImportIncludePromptMetaWrap">
                  <input type="checkbox" id="docsHtmlImportIncludePromptMeta">
                  <span id="docsHtmlImportIncludePromptMetaLabel"></span>
                </label>
                <p id="docsHtmlImportIncludePromptMetaHint"></p>
                <button id="docsHtmlImportRun" type="button"></button>
                <button id="docsHtmlImportConfirm" type="button" hidden></button>
                <button id="docsHtmlImportCancel" type="button" hidden></button>
                <p id="docsHtmlImportStatus"></p>
                <div id="docsHtmlImportWarning" hidden>
                  <h3 id="docsHtmlImportCollisionHeading"></h3>
                  <p id="docsHtmlImportCollisionBody"></p>
                  <p id="docsHtmlImportCollisionMeta"></p>
                </div>
                <div id="docsHtmlImportResult" hidden>
                  <h3 id="docsHtmlImportResultTitle"></h3>
                  <dl id="docsHtmlImportResultGrid" class="docsViewerImport__resultGrid">
                    <div>
                      <dd id="docsHtmlImportResultDocId"></dd>
                      <dd id="docsHtmlImportResultCounts"></dd>
                    </div>
                  </dl>
                  <div id="docsHtmlImportWarnings" hidden>
                    <h4 id="docsHtmlImportWarningsHeading"></h4>
                    <ul id="docsHtmlImportWarningsList"></ul>
                  </div>
                </div>
              </main>
              <p id="docsHtmlImportBootStatus">loading docs import...</p>
            `;
            const responses = {
                '/docs-viewer/config/ui-text/manage.json': {
                    docs_html_import: {
                        script_file_result_type: 'script file'
                    }
                },
                '/docs-viewer/config/defaults/docs-viewer-config.json': {
                    schema_version: 'docs_viewer_config_v1',
                    scopes: [{ scope_id: 'library' }]
                },
                'http://docs-management.test/health': { ok: true },
                'http://docs-management.test/docs/import-source-files': {
                    ok: true,
                    files: [{ filename: 'source.html', source_format: 'html' }]
                },
                'http://docs-management.test/docs/import-source': {
                    ok: true,
                    scope: 'library',
                    doc_id: 'source',
                    import_preview: {
                        source_format: 'html',
                        source_stats: {
                            links: 1,
                            images: 2,
                            svg: 0,
                            details: 0
                        },
                        warnings: []
                    },
                    interactive_html_written: [
                        { display_name: 'widget-one', result_type: 'script file' },
                        { display_name: 'widget-two', result_type: 'script file' }
                    ],
                    summary_text: 'Created source from source.html. Copied 2 interactive HTML script files.'
                }
            };
            window.fetch = async (url) => {
                const key = String(url);
                if (!Object.prototype.hasOwnProperty.call(responses, key)) {
                    throw new Error(`unexpected fetch: ${key}`);
                }
                return {
                    ok: true,
                    status: 200,
                    json: async () => responses[key]
                };
            };
            const module = await import('/docs-viewer/runtime/js/import/docs-html-import.js');
            await module.initDocsHtmlImport({
                root: document.getElementById('docsHtmlImportRoot'),
                bootStatus: document.getElementById('docsHtmlImportBootStatus'),
                docsViewerConfigUrl: '/docs-viewer/config/defaults/docs-viewer-config.json',
                uiTextUrl: '/docs-viewer/config/ui-text/manage.json',
                managementBaseUrl: 'http://docs-management.test',
                persistScope: false
            });
            document.getElementById('docsHtmlImportRun').click();
        }"""
    )
    page.wait_for_function("() => !document.getElementById('docsHtmlImportResult').hidden")
    rows = page.locator("#docsHtmlImportResultGrid").evaluate(
        """grid => Array.from(grid.querySelectorAll('dd')).map(node => node.textContent.trim())"""
    )
    expected = [
        "source",
        "1 links, 2 images, 0 SVG, 0 details blocks",
        "widget-one",
        "script file",
        "widget-two",
        "script file",
    ]
    if rows != expected:
        raise AssertionError(f"import result rows did not render as expected: {rows!r}")




def run_smoke_for_viewport(page: Page, base_url: str, viewport: dict[str, int]) -> dict[str, object]:
    page.set_viewport_size(viewport)
    page.goto(route_url(base_url, "/__docs_viewer_import_modal_fixture__.html"), wait_until="domcontentloaded")
    install_modal_fixture(page)
    run_import_modal_check(page)
    run_import_render_module_check(page)
    run_import_workflow_module_check(page)
    run_import_result_rows_check(page)
    return {
        "width": viewport["width"],
        "height": viewport["height"],
        "checked": [
            "import",
            "import-render-module",
            "import-workflow-module",
            "import-result-rows",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="", help="Use an existing local server instead of starting a fixture server.")
    parser.add_argument("--site-root", help="Serve a built site or repository root on a temporary local HTTP server.")
    args = parser.parse_args()

    static_server = None
    base_url = args.base_url
    if args.site_root:
        static_server, base_url = start_static_server(Path(args.site_root))
    elif not base_url:
        static_server, base_url = start_static_server(REPO_ROOT / "site")

    errors: list[str] = []
    results: list[dict[str, object]] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                    results.append(run_smoke_for_viewport(page, base_url, viewport))
            finally:
                browser.close()
    finally:
        if static_server is not None:
            static_server.shutdown()
            static_server.server_close()

    if errors:
        raise AssertionError(f"page errors during Docs Viewer import modal smoke: {errors!r}")
    print(json.dumps({"viewports": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

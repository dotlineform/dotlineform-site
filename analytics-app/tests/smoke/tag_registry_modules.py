#!/usr/bin/env python3
"""Smoke-check focused Tag Registry JavaScript modules."""

from __future__ import annotations

import argparse
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
              <main class="tagRegistryPage">
                <button type="button" data-role="open-import-modal">Import</button>
                <div data-role="key"></div>
                <label data-role="search-label" for="tagRegistrySearch"></label>
                <input id="tagRegistrySearch" data-role="search" type="text">
                <div data-role="list"></div>
                <div data-role="modal-host"></div>
              </main>
            `;
            const render = await import('/analytics/app/frontend/js/tag-registry-render.js');
            const importMode = await import('/analytics/app/frontend/js/tag-registry-import-mode.js');
            const modals = await import('/analytics/app/frontend/js/tag-registry-modals.js');
            const workflow = await import('/analytics/app/frontend/js/tag-registry-workflow.js');
            const host = document.querySelector('[data-role="modal-host"]');
            const config = {
                app: {
                    runtime: {
                        services: {
                            analytics: {
                                health: '/analytics/api/health',
                                import_tag_registry: '/analytics/api/import-tag-registry'
                            }
                        }
                    }
                },
                ui_text: {
                    tag_registry: {
                        all_tags_filter: 'All tags [{count}]',
                        table_heading_tag: 'tag',
                        table_heading_description: 'description',
                        table_heading_updated: 'updated',
                        group_info_title: 'Open group descriptions',
                        group_info_aria_label: 'Open group descriptions',
                        patch_import_message: 'Patch mode ({import_mode}): {imported_count} imported; {new_count} new tag rows prepared.',
                        patch_import_none_message: 'Patch mode ({import_mode}): {imported_count} imported; 0 new tags to add.'
                    }
                }
            };
            const state = {
                mount: document.querySelector('.tagRegistryPage'),
                refs: {
                    openImportModal: document.querySelector('[data-role="open-import-modal"]'),
                    key: document.querySelector('[data-role="key"]'),
                    searchLabel: document.querySelector('[data-role="search-label"]'),
                    search: document.querySelector('[data-role="search"]'),
                    list: document.querySelector('[data-role="list"]'),
                    modalHost: host
                },
                config,
                studioGroups: ['subject', 'domain', 'form', 'theme'],
                groupInfoPagePath: '/analytics/tag-groups/',
                groupDescriptions: new Map([
                    ['subject', 'Subject group'],
                    ['domain', 'Domain group']
                ]),
                tags: [
                    {
                        tagId: 'subject:trees',
                        group: 'subject',
                        label: 'trees',
                        description: '<unsafe copy>',
                        updatedAtUtc: '2026-03-04T08:09:10Z',
                        updatedAtMs: 20
                    },
                    {
                        tagId: 'domain:studio',
                        group: 'domain',
                        label: 'studio',
                        description: 'Studio work',
                        updatedAtUtc: '2026-03-03T17:43:04Z',
                        updatedAtMs: 10
                    }
                ],
                filterGroup: 'all',
                searchQuery: '',
                sortKey: 'label',
                sortDir: 'asc',
                importMode: 'add',
                saveMode: 'post',
                importAvailable: true,
                importModalOpen: false,
                selectedFile: null,
                patchSnippet: '',
                newTagState: null,
                demoteState: null,
                deleteTagId: '',
                deletePreview: '',
                deletePreviewSeq: 0
            };
            host.innerHTML = modals.renderTagRegistryModals(state);
            state.refs = {
                ...state.refs,
                ...modals.collectTagRegistryModalRefs(document)
            };
            window.__tagRegistryModuleSmoke = {
                render,
                importMode,
                workflow,
                state,
                callbacks: {
                    modalStateChanges: 0,
                    importAvailabilityChanges: 0,
                    routeStateChanges: 0
                }
            };
        }"""
    )


def assert_render_output(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const smoke = window.__tagRegistryModuleSmoke;
            const { render, state } = smoke;
            render.renderTagRegistryControls(state);
            render.renderTagRegistryList(state);
            const keyButtons = Array.from(state.refs.key.querySelectorAll('button[data-group]'));
            const rows = Array.from(state.refs.list.querySelectorAll('li'));
            return {
                allLabel: keyButtons[0] ? keyButtons[0].textContent.trim() : '',
                groupLabels: keyButtons.slice(1).map((button) => button.textContent.trim()),
                subjectTitle: state.refs.key.querySelector('button[data-group="subject"]')?.getAttribute('title') || '',
                infoLinkCount: state.refs.key.querySelectorAll('a').length,
                sortHeadings: Array.from(state.refs.list.querySelectorAll('button[data-sort-key]')).map((button) => button.textContent.trim()),
                rowLabels: rows.map((row) => row.querySelector('[data-tag-id]')?.textContent.trim() || ''),
                firstRowDescriptionHtml: rows[0]?.querySelector('.tagRegistry__descCol')?.innerHTML.trim() || '',
                firstRowUpdated: rows[0]?.querySelector('.tagRegistry__updatedCol')?.textContent.trim() || '',
                firstRowEditLabel: rows[0]?.querySelector('[data-tag-id]')?.getAttribute('aria-label') || '',
                demoteButtonCount: state.refs.list.querySelectorAll('[data-demote-tag-id]').length,
                deleteButtonCount: state.refs.list.querySelectorAll('[data-delete-tag-id]').length
            };
        }"""
    )
    expected_first_updated = page.evaluate(
        """() => {
            const date = new Date('2026-03-03T17:43:04Z');
            const pad = (value) => String(value).padStart(2, '0');
            return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
        }"""
    )
    expected_group_labels = ["subject [1]", "domain [1]", "form [0]", "theme [0]"]
    if result["allLabel"] != "All tags [2]":
        raise AssertionError(f"unexpected all-filter label: {result!r}")
    if result["groupLabels"] != expected_group_labels:
        raise AssertionError(f"unexpected group labels: {result!r}")
    if result["subjectTitle"] != "Subject group":
        raise AssertionError(f"group title was not rendered: {result!r}")
    if result["infoLinkCount"]:
        raise AssertionError(f"group info link mismatch: {result!r}")
    if result["sortHeadings"] != ["tag ↑", "description", "updated"]:
        raise AssertionError(f"sort headings mismatch: {result!r}")
    if result["rowLabels"] != ["studio", "trees"]:
        raise AssertionError(f"row sort/order mismatch: {result!r}")
    if result["firstRowDescriptionHtml"] != "Studio work":
        raise AssertionError(f"description output mismatch: {result!r}")
    if result["firstRowUpdated"] != expected_first_updated:
        raise AssertionError(f"updated output mismatch: {result!r}")
    if result["firstRowEditLabel"] != "Edit domain:studio":
        raise AssertionError(f"edit aria label mismatch: {result!r}")
    if result["demoteButtonCount"] != 2 or result["deleteButtonCount"] != 2:
        raise AssertionError(f"row action buttons missing: {result!r}")

    escaped = page.evaluate(
        """() => {
            const smoke = window.__tagRegistryModuleSmoke;
            const { render, state } = smoke;
            state.searchQuery = 'trees';
            render.renderTagRegistryList(state);
            return state.refs.list.querySelector('.tagRegistry__descCol').innerHTML.trim();
        }"""
    )
    if escaped != "&lt;unsafe copy&gt;":
        raise AssertionError(f"unsafe description was not escaped: {escaped!r}")

    empty_text = page.evaluate(
        """() => {
            const smoke = window.__tagRegistryModuleSmoke;
            const { render, state } = smoke;
            state.searchQuery = 'missing';
            render.renderTagRegistryList(state);
            return state.refs.list.textContent.replace(/\\s+/g, ' ').trim();
        }"""
    )
    if "none" not in empty_text:
        raise AssertionError(f"empty state was not rendered: {empty_text!r}")


def assert_import_mode_availability(page: Page) -> None:
    page.route(
        "**/analytics/api/health",
        lambda route: route.fulfill(
            status=503,
            headers={
                "access-control-allow-origin": "*",
                "content-type": "application/json",
            },
            body='{"ok": false}',
        ),
    )
    result = page.evaluate(
        """async () => {
            const smoke = window.__tagRegistryModuleSmoke;
            const { importMode, state } = smoke;
            state.refs.importMode.value = 'replace';
            importMode.syncTagRegistryImportModeFromControl(state);
            const syncedReplace = state.importMode;
            state.importModalOpen = true;
            state.importModalRestoreFocus = state.refs.openImportModal;
            state.refs.importModal.hidden = false;
            state.saveMode = 'patch';
            state.importAvailable = true;
            importMode.renderTagRegistryImportAvailability(state, {
                onModalStateChange: () => smoke.callbacks.modalStateChanges += 1
            });
            const afterPatch = {
                saveMode: state.saveMode,
                importAvailable: state.importAvailable,
                openerDisabled: state.refs.openImportModal.disabled,
                importButtonDisabled: state.refs.importButton.disabled,
                modalHidden: state.refs.importModal.hidden,
                importModalOpen: state.importModalOpen,
                modalStateChanges: smoke.callbacks.modalStateChanges
            };
            state.saveMode = 'post';
            state.importAvailable = true;
            importMode.renderTagRegistryImportAvailability(state);
            const afterPost = {
                openerDisabled: state.refs.openImportModal.disabled,
                importButtonDisabled: state.refs.importButton.disabled,
                importAvailable: state.importAvailable
            };
            state.saveMode = 'patch';
            state.importAvailable = true;
            await importMode.probeTagRegistryImportMode(state, {
                onImportAvailabilityChange: () => smoke.callbacks.importAvailabilityChanges += 1,
                onRouteStateChange: () => smoke.callbacks.routeStateChanges += 1
            });
            return {
                syncedReplace,
                afterPatch,
                afterPost,
                afterProbe: {
                    saveMode: state.saveMode,
                    importAvailable: state.importAvailable,
                    importAvailabilityChanges: smoke.callbacks.importAvailabilityChanges,
                    routeStateChanges: smoke.callbacks.routeStateChanges
                }
            };
        }"""
    )
    if result["syncedReplace"] != "replace":
        raise AssertionError(f"import mode control did not sync: {result!r}")
    after_patch = result["afterPatch"]
    if after_patch != {
        "saveMode": "patch",
        "importAvailable": False,
        "openerDisabled": True,
        "importButtonDisabled": True,
        "modalHidden": True,
        "importModalOpen": False,
        "modalStateChanges": 1,
    }:
        raise AssertionError(f"patch availability state mismatch: {result!r}")
    if result["afterPost"] != {
        "openerDisabled": False,
        "importButtonDisabled": False,
        "importAvailable": True,
    }:
        raise AssertionError(f"post availability state mismatch: {result!r}")
    if result["afterProbe"] != {
        "saveMode": "patch",
        "importAvailable": False,
        "importAvailabilityChanges": 1,
        "routeStateChanges": 1,
    }:
        raise AssertionError(f"health probe fallback mismatch: {result!r}")


def assert_patch_save_behavior(page: Page) -> None:
    page.route(
        "**/analytics/api/import-tag-registry",
        lambda route: route.fulfill(
            status=503,
            headers={
                "access-control-allow-origin": "*",
                "content-type": "application/json",
            },
            body='{"ok": false, "error": "offline"}',
        ),
    )
    result = page.evaluate(
        """async () => {
            const smoke = window.__tagRegistryModuleSmoke;
            const { workflow, state } = smoke;
            const newTagRow = {
                tag_id: 'subject:canopy',
                group: 'subject',
                label: 'canopy',
                status: 'active',
                description: 'Tree canopy'
            };
            const postFallback = await workflow.createTagRegistryTag({
                saveMode: 'post',
                newTagRow,
                config: state.config
            });
            const patchImport = await workflow.importTagRegistryTags({
                saveMode: 'patch',
                importMode: 'add',
                patchContext: {
                    config: state.config,
                    importMode: 'add',
                    tags: state.tags
                },
                importRegistry: {
                    tags: [
                        newTagRow,
                        {
                            tag_id: 'domain:studio',
                            group: 'domain',
                            label: 'studio',
                            status: 'active',
                            description: 'Existing tag'
                        }
                    ]
                }
            });
            workflow.applyTagRegistryPatchFallback(state);
            return {
                postFallback: {
                    ok: postFallback.ok,
                    mode: postFallback.mode,
                    switchToPatch: postFallback.switchToPatch,
                    message: postFallback.message,
                    patchKind: postFallback.patchResult && postFallback.patchResult.kind,
                    patchMessage: postFallback.patchResult && postFallback.patchResult.message,
                    patchSnippet: postFallback.patchResult && postFallback.patchResult.snippet
                },
                patchImport: {
                    ok: patchImport.ok,
                    mode: patchImport.mode,
                    patchKind: patchImport.patchResult && patchImport.patchResult.kind,
                    patchMessage: patchImport.patchResult && patchImport.patchResult.message,
                    patchSnippet: patchImport.patchResult && patchImport.patchResult.snippet
                },
                stateAfterFallback: {
                    saveMode: state.saveMode,
                    importAvailable: state.importAvailable
                }
            };
        }"""
    )
    post_fallback = result["postFallback"]
    if post_fallback["ok"] is not False or post_fallback["mode"] != "patch" or not post_fallback["switchToPatch"]:
        raise AssertionError(f"post fallback metadata mismatch: {result!r}")
    if "switched to patch mode" not in post_fallback["message"]:
        raise AssertionError(f"post fallback message mismatch: {result!r}")
    if post_fallback["patchKind"] != "warn" or "new tag row prepared" not in post_fallback["patchMessage"]:
        raise AssertionError(f"post fallback patch result mismatch: {result!r}")
    if '"tag_id": "subject:canopy"' not in post_fallback["patchSnippet"]:
        raise AssertionError(f"post fallback snippet missing new tag: {result!r}")

    patch_import = result["patchImport"]
    if patch_import["ok"] is not True or patch_import["mode"] != "patch":
        raise AssertionError(f"patch import metadata mismatch: {result!r}")
    if patch_import["patchKind"] != "warn" or "1 new tag rows prepared" not in patch_import["patchMessage"]:
        raise AssertionError(f"patch import message mismatch: {result!r}")
    if '"tag_id": "subject:canopy"' not in patch_import["patchSnippet"]:
        raise AssertionError(f"patch import snippet missing new tag: {result!r}")
    if '"tag_id": "domain:studio"' in patch_import["patchSnippet"]:
        raise AssertionError(f"patch import snippet should exclude existing tag: {result!r}")
    if result["stateAfterFallback"] != {"saveMode": "patch", "importAvailable": False}:
        raise AssertionError(f"patch fallback state mismatch: {result!r}")


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
            assert_render_output(page)
            assert_import_mode_availability(page)
            assert_patch_save_behavior(page)
        finally:
            browser.close()
            if server:
                server.shutdown()

    if errors:
        raise AssertionError(f"page errors during Tag Registry module smoke: {errors!r}")
    print("Tag Registry module smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Smoke-check focused tag route shell helper modules."""

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
              <main>
                <section id="tag-aliases" class="tagAliasesPage">
                  <button type="button" data-role="open-import-modal">Import</button>
                  <button type="button" data-role="open-new-alias">New alias</button>
                  <div data-role="key"></div>
                  <label data-role="search-label" for="tagAliasesSearch"></label>
                  <input id="tagAliasesSearch" data-role="search" type="text">
                  <div data-role="list"></div>
                  <div data-role="modal-host"></div>
                </section>
                <section id="seriesTagEditorRoot"></section>
              </main>
            `;
            const modals = await import('/assets/studio/js/tag-aliases-modals.js');
            const stateModule = await import('/assets/studio/js/tag-aliases-state.js');
            const workflow = await import('/assets/studio/js/tag-aliases-workflow.js');
            const importMode = await import('/assets/studio/js/tag-aliases-import-mode.js');
            const tagStudioRouteState = await import('/assets/studio/js/tag-studio-route-state.js');
            await import('/assets/studio/js/tag-studio.js');
            const config = {
                ui_text: {
                    tag_aliases: {
                        server_create_failed: 'Server create failed; switched to patch mode. {message}',
                        patch_create_message: 'Patch mode: alias fragment prepared for new alias "{alias_key}".',
                        patch_import_message: 'Patch mode ({import_mode}): {imported_count} imported; {new_count} alias rows prepared.',
                        patch_import_none_message: 'Patch mode ({import_mode}): {imported_count} imported; 0 new aliases to add.'
                    }
                }
            };
            const mount = document.querySelector('#tag-aliases');
            const modalHost = mount.querySelector('[data-role="modal-host"]');
            const state = {
                mount,
                config,
                studioGroups: ['subject', 'domain', 'form', 'theme'],
                aliasesUpdatedAt: '2026-05-20T09:00:00Z',
                aliases: [],
                registryById: new Map([
                    ['subject:trees', { group: 'subject', label: 'trees' }],
                    ['domain:studio', { group: 'domain', label: 'studio' }]
                ]),
                registryOptions: [],
                importMode: 'add',
                saveMode: 'post',
                importAvailable: true,
                selectedFile: null,
                importModalOpen: false,
                patchSnippet: '',
                promotionState: null,
                demoteState: null,
                editState: null,
                refs: {
                    openImportModal: mount.querySelector('[data-role="open-import-modal"]'),
                    openNewAlias: mount.querySelector('[data-role="open-new-alias"]'),
                    key: mount.querySelector('[data-role="key"]'),
                    searchLabel: mount.querySelector('[data-role="search-label"]'),
                    search: mount.querySelector('[data-role="search"]'),
                    list: mount.querySelector('[data-role="list"]'),
                    modalHost
                }
            };
            state.aliases = [
                stateModule.makeTagAliasEntry(state, 'woods', 'Woodland aliases', ['subject:trees'], state.aliasesUpdatedAt),
                stateModule.makeTagAliasEntry(state, 'mist', 'Mist aliases', ['domain:studio'], state.aliasesUpdatedAt)
            ];
            modalHost.innerHTML = modals.renderTagAliasesModals(state);
            state.refs = {
                ...state.refs,
                ...modals.collectTagAliasesModalRefs(document)
            };
            window.__tagRouteShellModuleSmoke = {
                stateModule,
                workflow,
                importMode,
                tagStudioRouteState,
                state,
                callbacks: {
                    modalStateChanges: 0,
                    importAvailabilityChanges: 0,
                    routeStateChanges: 0
                }
            };
        }"""
    )


def assert_alias_state_projection(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const smoke = window.__tagRouteShellModuleSmoke;
            const { stateModule, state } = smoke;
            stateModule.applyTagAliasesEditProjection(state, {
                originalAlias: 'woods',
                validation: {
                    alias: 'forest',
                    description: 'Dense stand',
                    tags: ['domain:studio']
                },
                response: { updated_at_utc: '2026-05-21T10:00:00Z' }
            });
            const afterEdit = {
                aliases: state.aliases.map((entry) => entry.alias).sort(),
                forestGroups: state.aliases.find((entry) => entry.alias === 'forest')?.groups || [],
                updatedAt: state.aliasesUpdatedAt
            };
            stateModule.applyTagAliasesDeleteProjection(state, {
                aliasKey: 'mist',
                response: { updated_at_utc: '2026-05-21T10:05:00Z' }
            });
            const afterDelete = state.aliases.map((entry) => entry.alias).sort();
            stateModule.applyTagAliasesPromoteProjection(state, {
                aliasKey: 'forest',
                group: 'subject',
                response: { updated_at_utc: '2026-05-21T10:10:00Z' }
            });
            const afterPromote = {
                aliases: state.aliases.map((entry) => entry.alias).sort(),
                promotedTag: state.registryById.get('subject:forest') || null,
                registryOptionCount: state.registryOptions.length
            };
            stateModule.applyTagAliasesDemoteProjection(state, {
                canonicalTagId: 'subject:trees',
                aliasTargets: ['domain:studio'],
                response: { updated_at_utc: '2026-05-21T10:15:00Z' }
            });
            const treesAlias = state.aliases.find((entry) => entry.alias === 'trees');
            return {
                afterEdit,
                afterDelete,
                afterPromote,
                afterDemote: {
                    hasCanonical: state.registryById.has('subject:trees'),
                    alias: treesAlias && {
                        alias: treesAlias.alias,
                        targets: treesAlias.targets,
                        groups: treesAlias.groups,
                        updatedAtUtc: treesAlias.updatedAtUtc
                    },
                    updatedAt: state.aliasesUpdatedAt
                }
            };
        }"""
    )
    if result["afterEdit"] != {
        "aliases": ["forest", "mist"],
        "forestGroups": ["domain"],
        "updatedAt": "2026-05-21T10:00:00Z",
    }:
        raise AssertionError(f"alias edit projection mismatch: {result!r}")
    if result["afterDelete"] != ["forest"]:
        raise AssertionError(f"alias delete projection mismatch: {result!r}")
    promoted = result["afterPromote"]
    if promoted["aliases"] != [] or promoted["promotedTag"] != {"group": "subject", "label": "forest"}:
        raise AssertionError(f"alias promote projection mismatch: {result!r}")
    if promoted["registryOptionCount"] < 2:
        raise AssertionError(f"derived registry options were not refreshed: {result!r}")
    demoted = result["afterDemote"]
    if demoted["hasCanonical"] is not False:
        raise AssertionError(f"demoted canonical tag still present: {result!r}")
    if demoted["alias"] != {
        "alias": "trees",
        "targets": ["domain:studio"],
        "groups": ["domain"],
        "updatedAtUtc": "2026-05-21T10:15:00Z",
    }:
        raise AssertionError(f"demote projection mismatch: {result!r}")


def assert_alias_workflow_fallback(page: Page) -> None:
    page.route(
        "http://127.0.0.1:8787/import-tag-aliases",
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
            const smoke = window.__tagRouteShellModuleSmoke;
            const { workflow, state } = smoke;
            const postFallback = await workflow.saveTagAliasEdit({
                saveMode: 'post',
                isCreate: true,
                originalAlias: '',
                validation: {
                    alias: 'canopy',
                    description: 'Upper layer',
                    tags: ['subject:forest']
                },
                config: state.config
            });
            workflow.applyTagAliasesPatchFallback(state);
            const patchImport = await workflow.importTagAliases({
                saveMode: 'patch',
                importMode: 'add',
                patchContext: state,
                importAliases: {
                    aliases: {
                        canopy: { description: 'Upper layer', tags: ['subject:forest'] },
                        trees: { description: 'Existing demoted alias', tags: ['domain:studio'] }
                    }
                },
                filename: 'aliases.json',
                config: state.config
            });
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
                stateAfterFallback: {
                    saveMode: state.saveMode,
                    importAvailable: state.importAvailable
                },
                patchImport: {
                    ok: patchImport.ok,
                    mode: patchImport.mode,
                    patchKind: patchImport.patchResult && patchImport.patchResult.kind,
                    patchMessage: patchImport.patchResult && patchImport.patchResult.message,
                    patchSnippet: patchImport.patchResult && patchImport.patchResult.snippet
                }
            };
        }"""
    )
    post_fallback = result["postFallback"]
    if post_fallback["ok"] is not False or post_fallback["mode"] != "patch" or not post_fallback["switchToPatch"]:
        raise AssertionError(f"post fallback metadata mismatch: {result!r}")
    if "switched to patch mode" not in post_fallback["message"]:
        raise AssertionError(f"post fallback message mismatch: {result!r}")
    if post_fallback["patchKind"] != "warn" or '"canopy"' not in post_fallback["patchSnippet"]:
        raise AssertionError(f"post fallback patch result mismatch: {result!r}")
    if result["stateAfterFallback"] != {"saveMode": "patch", "importAvailable": False}:
        raise AssertionError(f"patch fallback state mismatch: {result!r}")

    patch_import = result["patchImport"]
    if patch_import["ok"] is not True or patch_import["mode"] != "patch":
        raise AssertionError(f"patch import metadata mismatch: {result!r}")
    if patch_import["patchKind"] != "warn" or "1 alias rows prepared" not in patch_import["patchMessage"]:
        raise AssertionError(f"patch import message mismatch: {result!r}")
    if '"canopy"' not in patch_import["patchSnippet"]:
        raise AssertionError(f"patch import snippet missing new alias: {result!r}")
    if '"trees"' in patch_import["patchSnippet"]:
        raise AssertionError(f"patch import snippet should exclude existing alias: {result!r}")


def assert_import_mode_availability(page: Page) -> None:
    page.route(
        "http://127.0.0.1:8787/health",
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
            const smoke = window.__tagRouteShellModuleSmoke;
            const { importMode, state } = smoke;
            state.refs.importMode.value = 'merge';
            importMode.syncTagAliasesImportModeFromControl(state);
            const syncedMerge = state.importMode;
            state.importModalOpen = true;
            state.importModalRestoreFocus = state.refs.openImportModal;
            state.refs.importModal.hidden = false;
            state.saveMode = 'patch';
            state.importAvailable = true;
            importMode.renderTagAliasesImportAvailability(state, {
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
            importMode.renderTagAliasesImportAvailability(state);
            const afterPost = {
                openerDisabled: state.refs.openImportModal.disabled,
                importButtonDisabled: state.refs.importButton.disabled,
                importAvailable: state.importAvailable
            };
            state.saveMode = 'patch';
            state.importAvailable = true;
            await importMode.probeTagAliasesImportMode(state, {
                onImportAvailabilityChange: () => smoke.callbacks.importAvailabilityChanges += 1,
                onRouteStateChange: () => smoke.callbacks.routeStateChanges += 1
            });
            return {
                syncedMerge,
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
    if result["syncedMerge"] != "merge":
        raise AssertionError(f"import mode control did not sync: {result!r}")
    if result["afterPatch"] != {
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


def assert_tag_studio_route_state(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const smoke = window.__tagRouteShellModuleSmoke;
            const routeRoot = document.querySelector('#seriesTagEditorRoot');
            const state = {
                routeRoot,
                selectedWorkId: '',
                saveMode: 'offline',
                seriesId: '009',
                isBusy: false
            };
            const editDetail = smoke.tagStudioRouteState.buildTagStudioRouteStateDetail(state);
            state.selectedWorkId = '00042';
            state.saveMode = 'post';
            state.isBusy = true;
            const singleDetail = smoke.tagStudioRouteState.buildTagStudioRouteStateDetail(state);
            smoke.tagStudioRouteState.syncTagStudioRouteBusyState(state);
            smoke.tagStudioRouteState.markTagStudioRouteReady(state, true);
            return {
                editDetail,
                singleDetail,
                routeRootDataset: {
                    studioBusy: routeRoot.dataset.studioBusy || '',
                    studioReady: routeRoot.dataset.studioReady || '',
                    studioRoute: routeRoot.dataset.studioRoute || '',
                    studioMode: routeRoot.dataset.studioMode || '',
                    studioService: routeRoot.dataset.studioService || '',
                    studioRecordLoaded: routeRoot.dataset.studioRecordLoaded || ''
                },
                nullDetail: smoke.tagStudioRouteState.buildTagStudioRouteStateDetail(null)
            };
        }"""
    )
    if result["editDetail"] != {
        "route": "series-tag-editor",
        "mode": "edit",
        "service": "unavailable",
        "recordLoaded": True,
    }:
        raise AssertionError(f"edit route detail mismatch: {result!r}")
    if result["singleDetail"] != {
        "route": "series-tag-editor",
        "mode": "single",
        "service": "available",
        "recordLoaded": True,
    }:
        raise AssertionError(f"single route detail mismatch: {result!r}")
    if result["routeRootDataset"] != {
        "studioBusy": "true",
        "studioReady": "true",
        "studioRoute": "series-tag-editor",
        "studioMode": "single",
        "studioService": "available",
        "studioRecordLoaded": "true",
    }:
        raise AssertionError(f"route state dataset mismatch: {result!r}")
    if result["nullDetail"] != {
        "route": "series-tag-editor",
        "mode": "edit",
        "service": "unavailable",
        "recordLoaded": False,
    }:
        raise AssertionError(f"null route detail mismatch: {result!r}")


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
            assert_alias_state_projection(page)
            assert_alias_workflow_fallback(page)
            assert_import_mode_availability(page)
            assert_tag_studio_route_state(page)
        finally:
            browser.close()
            if server:
                server.shutdown()

    if errors:
        raise AssertionError(f"page errors during tag route shell module smoke: {errors!r}")
    print("Tag route shell module smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

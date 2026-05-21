#!/usr/bin/env python3
"""Smoke-check shared Tag route shell save-session JavaScript helpers."""

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


def assert_tag_save_session_helpers(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/assets/studio/js/tag-route-save-session.js');
            const state = {
                saveMode: 'patch',
                importAvailable: false,
                isBusy: false
            };
            const routeChanges = [];
            const availableProbe = await module.probeTagRouteSaveMode(state, {
                syncImportAvailable: true,
                healthProbe: async () => true,
                onSaveModeChange: (detail) => routeChanges.push(['save', detail.service]),
                onRouteStateChange: (detail) => routeChanges.push(['route', detail.saveMode])
            });
            const serviceAfterProbe = module.tagRouteServiceState(state);
            const fallback = module.applyTagRoutePatchFallback(state, { syncImportAvailable: true });
            const busyStates = [];
            await module.withTagRouteBusy(state, async () => {
                busyStates.push(`inside:${state.isBusy}`);
            }, {
                syncRouteBusyState: (busyState) => busyStates.push(`sync:${busyState.isBusy}`)
            });
            const fakeWindow = new EventTarget();
            const fakeDocument = new EventTarget();
            fakeDocument.visibilityState = 'visible';
            let reprobeCount = 0;
            const cleanup = module.bindTagSaveModeReprobe(() => {
                reprobeCount += 1;
            }, {
                windowObject: fakeWindow,
                documentObject: fakeDocument
            });
            fakeWindow.dispatchEvent(new Event('focus'));
            fakeWindow.dispatchEvent(new Event('pageshow'));
            fakeDocument.dispatchEvent(new Event('visibilitychange'));
            fakeDocument.visibilityState = 'hidden';
            fakeWindow.dispatchEvent(new Event('focus'));
            cleanup();
            fakeDocument.visibilityState = 'visible';
            fakeWindow.dispatchEvent(new Event('focus'));
            const patchPresentation = module.projectTagPatchFallbackResult({
                switchToPatch: true,
                message: 'Server unavailable.',
                patchResult: {
                    kind: 'warn',
                    message: 'Copy this patch.',
                    snippet: 'diff --git a/file b/file'
                }
            });
            await Promise.all([
                import('/assets/studio/js/tag-studio.js'),
                import('/assets/studio/js/tag-registry.js'),
                import('/assets/studio/js/tag-aliases.js'),
                import('/assets/studio/js/tag-registry-import-mode.js'),
                import('/assets/studio/js/tag-aliases-import-mode.js'),
                import('/assets/studio/js/tag-registry-workflow.js'),
                import('/assets/studio/js/tag-aliases-workflow.js')
            ]);
            return {
                availableProbe,
                serviceAfterProbe,
                fallback,
                routeChanges,
                busyStates,
                reprobeCount,
                patchPresentation,
                routeImports: true
            };
        }"""
    )
    assert result["availableProbe"] == {
        "ok": True,
        "saveMode": "post",
        "importAvailable": True,
        "service": "available",
    }
    assert result["serviceAfterProbe"] == "available"
    assert result["fallback"] == {
        "saveMode": "patch",
        "importAvailable": False,
        "service": "unavailable",
    }
    assert result["routeChanges"] == [["save", "available"], ["route", "post"]]
    assert result["busyStates"] == ["sync:true", "inside:true", "sync:false"]
    assert result["reprobeCount"] == 3
    assert result["patchPresentation"] == {
        "switchedToPatch": True,
        "switchMessage": "Server unavailable.",
        "kind": "warn",
        "message": "Copy this patch.",
        "snippet": "diff --git a/file b/file",
    }
    assert result["routeImports"] is True


def assert_tag_registry_modal_workflow(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <section id="registry">
                <p id="editStatus"></p>
                <div id="editModal"></div>
                <input id="editTagName" value="old">
                <textarea id="editDescription"></textarea>
                <p id="newStatus"></p>
                <p id="newWarning"></p>
                <input id="newSlug" value=" New-Slug ">
                <textarea id="newDescription">Description</textarea>
                <div id="newGroupKey"></div>
                <button id="createTag"></button>
                <p id="demoteStatus"></p>
                <div id="demoteGroupKey"></div>
                <div id="demoteTagList"></div>
                <button id="confirmDemote"></button>
              </section>
            `;
            const module = await import('/assets/studio/js/tag-registry-modal-workflow.js');
            const state = {
                config: { ui_text: {} },
                registryUpdatedAt: '2026-05-21T10:00:00Z',
                tags: [
                    { tagId: 'subject:alpha', group: 'subject', label: 'alpha', description: 'Old', updatedAtUtc: '2026-05-21T10:00:00Z' },
                    { tagId: 'domain:beta', group: 'domain', label: 'beta', description: 'Beta', updatedAtUtc: '2026-05-21T10:00:00Z' }
                ],
                registryOptions: [],
                aliasKeys: new Set(),
                groupDescriptions: new Map([
                    ['subject', 'Subject'],
                    ['domain', 'Domain']
                ]),
                newTagState: { group: 'subject', slug: '', description: '' },
                demoteState: { tagId: 'subject:alpha', tags: [] },
                refs: {
                    editStatus: document.getElementById('editStatus'),
                    editModal: document.getElementById('editModal'),
                    editTagName: document.getElementById('editTagName'),
                    editDescription: document.getElementById('editDescription'),
                    newTagStatus: document.getElementById('newStatus'),
                    newTagWarning: document.getElementById('newWarning'),
                    newTagSlug: document.getElementById('newSlug'),
                    newTagDescription: document.getElementById('newDescription'),
                    newGroupKey: document.getElementById('newGroupKey'),
                    createTag: document.getElementById('createTag'),
                    demoteStatus: document.getElementById('demoteStatus'),
                    demoteGroupKey: document.getElementById('demoteGroupKey'),
                    demoteTagList: document.getElementById('demoteTagList'),
                    confirmDemote: document.getElementById('confirmDemote')
                }
            };
            const calls = [];
            const options = {
                tagSlugRe: /^[a-z0-9][a-z0-9-]*$/,
                studioGroups: ['subject', 'domain'],
                maxAliasTags: 4,
                text: (_key, fallback, tokens = null) => {
                    if (!tokens) return fallback;
                    return Object.entries(tokens).reduce((value, [token, replacement]) => value.replace(`{${token}}`, replacement), fallback);
                },
                findTagById: (tagId) => state.tags.find((tag) => tag.tagId === tagId) || null,
                setImportResult: (kind, message) => calls.push(['result', kind, message]),
                renderControls: () => calls.push(['renderControls']),
                renderList: () => calls.push(['renderList']),
                syncRouteBusyState: () => calls.push(['sync'])
            };
            module.updateTagRegistryNewWorkflow(state, options);
            const validation = module.getTagRegistryNewValidation(state, options);
            module.addTagRegistryDemoteTag(state, 'domain:beta', options);
            module.updateTagRegistryDemoteWorkflow(state, options);
            module.applyTagRegistryEditResult(state, {
                tagId: 'subject:alpha',
                description: 'New description',
                result: {
                    message: 'Saved.',
                    summary: 'Registry updated.',
                    response: { updated_at_utc: '2026-05-21T10:05:00Z' }
                }
            }, options);
            return {
                normalizedSlug: state.newTagState.slug,
                validation,
                createDisabled: state.refs.createTag.disabled,
                demoteTags: state.demoteState.tags.slice(),
                demoteDisabled: state.refs.demoteStatus.textContent,
                editedDescription: state.tags.find((tag) => tag.tagId === 'subject:alpha').description,
                editModalHidden: state.refs.editModal.hidden,
                calls
            };
        }"""
    )
    assert result["normalizedSlug"] == "new-slug"
    assert result["validation"]["valid"] is True
    assert result["createDisabled"] is False
    assert result["demoteTags"] == ["domain:beta"]
    assert result["editedDescription"] == "New description"
    assert result["editModalHidden"] is True
    assert result["calls"] == [
        ["result", "success", "Registry updated."],
        ["renderControls"],
        ["renderList"],
        ["sync"],
    ]


def assert_tag_studio_interactions(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <input id="workInput">
              <input id="tagInput">
              <button id="addTag"></button>
              <button id="save"></button>
              <p id="warning"></p>
              <p id="status"></p>
              <p id="saveResult"></p>
            `;
            const module = await import('/assets/studio/js/tag-studio-interactions.js');
            const alpha = { tag_id: 'subject:alpha', group: 'subject', label: 'Alpha', slug: 'alpha' };
            const beta = { tag_id: 'domain:beta', group: 'domain', label: 'Beta', slug: 'beta' };
            const gamma = { tag_id: 'theme:gamma', group: 'theme', label: 'Gamma', slug: 'gamma' };
            const state = {
                config: { ui_text: {} },
                seriesId: 'demo',
                tagsById: new Map([
                    ['subject:alpha', alpha],
                    ['domain:beta', beta],
                    ['theme:gamma', gamma]
                ]),
                slugMap: new Map([
                    ['alpha', [alpha]],
                    ['beta', [beta]],
                    ['gamma', [gamma]]
                ]),
                labelMap: new Map(),
                aliases: new Map([['alias-beta', ['domain:beta']]]),
                seriesEntries: [{
                    entryId: 1,
                    rawInput: 'subject:alpha',
                    canonicalId: 'subject:alpha',
                    group: 'subject',
                    label: 'Alpha',
                    wManual: 0.6,
                    alias: ''
                }],
                baselineSeriesRows: [{ tag_id: 'subject:alpha', w_manual: 0.6 }],
                workEntriesById: new Map(),
                baselineWorkStateById: new Map(),
                seriesWorkOptions: [
                    { workId: '00001' },
                    { workId: '00002' }
                ],
                seriesWorkIds: new Set(['00001', '00002']),
                selectedWorkIds: [],
                selectedWorkId: '',
                offlineBaseSeriesRow: {
                    tags: [{ tag_id: 'subject:alpha', w_manual: 0.6 }],
                    works: {
                        '00001': {
                            tags: [{ tag_id: 'theme:gamma', w_manual: 0.9 }]
                        }
                    }
                },
                refs: {
                    workInput: document.getElementById('workInput'),
                    input: document.getElementById('tagInput'),
                    addButton: document.getElementById('addTag'),
                    saveButton: document.getElementById('save'),
                    saveWarning: document.getElementById('warning'),
                    status: document.getElementById('status'),
                    saveResult: document.getElementById('saveResult')
                },
                statusKind: '',
                statusText: ''
            };
            const calls = [];
            const text = (_key, fallback, tokens = null) => {
                if (!tokens) return fallback;
                return Object.entries(tokens).reduce((value, [token, replacement]) => value.replace(`{${token}}`, replacement), fallback);
            };
            const callbacks = {
                text,
                hidePopup: () => calls.push('hidePopup'),
                hideWorkPopup: () => calls.push('hideWorkPopup'),
                renderAll: () => calls.push('renderAll'),
                renderStatus: () => calls.push('renderStatus'),
                renderWorkPopup: () => calls.push('renderWorkPopup'),
                setSaveResult: (_state, kind, message) => {
                    state.refs.saveResult.dataset.state = kind;
                    state.refs.saveResult.textContent = message;
                    calls.push(`saveResult:${kind}`);
                },
                setStatus: (_state, kind, message) => {
                    state.statusKind = kind;
                    state.statusText = message;
                    calls.push(`status:${kind}`);
                },
                getMatchingWorkOptions: (_state, rawInput) => {
                    const normalized = String(rawInput).padStart(5, '0');
                    return state.seriesWorkOptions.filter((item) => item.workId === normalized);
                }
            };
            module.addTagStudioWorkSelection(state, '00001', true, callbacks);
            module.addTagStudioResolvedTag(state, beta, { rawInput: 'alias-beta', alias: 'alias-beta' }, callbacks);
            const workEntryAfterAdd = state.workEntriesById.get('00001')[0];
            const workProjection = module.projectTagStudioSaveState(state, { text });
            module.cycleTagStudioEntryWeight(state, workEntryAfterAdd.entryId, callbacks);
            const cycledWeight = state.workEntriesById.get('00001')[0].wManual;
            module.removeTagStudioEditableEntry(state, workEntryAfterAdd.entryId, callbacks);
            const workEntriesAfterRemove = state.workEntriesById.get('00001').length;
            module.restoreTagStudioDeletedEntry(state, 'theme:gamma', 'work', callbacks);
            const restoredWorkEntry = state.workEntriesById.get('00001')[0];
            module.clearTagStudioSelectedWork(state, '00001', callbacks);
            module.addTagStudioResolvedTag(state, beta, { rawInput: 'beta' }, callbacks);
            const seriesProjection = module.applyTagStudioSaveState(state, { text });
            return {
                selectedAfterClear: state.selectedWorkId,
                selectedIdsAfterClear: state.selectedWorkIds.slice(),
                workEntryAfterAdd,
                workProjection: {
                    isDirty: workProjection.isDirty,
                    saveButtonDisabled: workProjection.saveButtonDisabled,
                    warningText: workProjection.warningText,
                    unresolvedCount: workProjection.metrics.unresolvedCount
                },
                cycledWeight,
                workEntriesAfterRemove,
                restoredWorkEntry,
                seriesEntries: state.seriesEntries.map((entry) => entry.canonicalId),
                seriesProjection: {
                    isDirty: seriesProjection.isDirty,
                    saveButtonDisabled: seriesProjection.saveButtonDisabled,
                    warningText: seriesProjection.warningText,
                    unresolvedCount: seriesProjection.metrics.unresolvedCount
                },
                saveDisabled: state.refs.saveButton.disabled,
                warningText: state.refs.saveWarning.textContent,
                statusKind: state.statusKind,
                calls
            };
        }"""
    )
    assert result["workEntryAfterAdd"]["canonicalId"] == "domain:beta"
    assert result["workEntryAfterAdd"]["alias"] == "alias-beta"
    assert result["workProjection"] == {
        "isDirty": True,
        "saveButtonDisabled": False,
        "warningText": "",
        "unresolvedCount": 0,
    }
    assert result["cycledWeight"] == 0.9
    assert result["workEntriesAfterRemove"] == 0
    assert result["restoredWorkEntry"]["canonicalId"] == "theme:gamma"
    assert result["restoredWorkEntry"]["wManual"] == 0.9
    assert result["selectedAfterClear"] == ""
    assert result["selectedIdsAfterClear"] == []
    assert result["seriesEntries"] == ["subject:alpha", "domain:beta"]
    assert result["seriesProjection"] == {
        "isDirty": True,
        "saveButtonDisabled": False,
        "warningText": "Save to persist the current tag assignment diff.",
        "unresolvedCount": 0,
    }
    assert result["saveDisabled"] is False
    assert result["warningText"] == "Save to persist the current tag assignment diff."
    assert result["statusKind"] == "success"


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            assert_tag_save_session_helpers(page)
            assert_tag_registry_modal_workflow(page)
            assert_tag_studio_interactions(page)
            browser.close()
            if errors:
                raise AssertionError(f"page errors during Tag route shell module smoke: {errors!r}")
    finally:
        server.shutdown()
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".", help="Site root to serve for module imports.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(Path(args.site_root))


if __name__ == "__main__":
    main()

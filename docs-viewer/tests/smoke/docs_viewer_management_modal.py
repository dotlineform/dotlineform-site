#!/usr/bin/env python3
"""Smoke-check generic Docs Viewer management modal shell behavior."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from docs_viewer_management_modal_support import (
    REPO_ROOT,
    active_id,
    active_role,
    assert_hidden_with_focus,
    assert_shell,
    focus_wrap_id,
    focus_wrap_role,
    install_modal_fixture,
    modal_state,
    route_url,
    start_static_server,
    wait_for_focus,
)

def run_metadata_modal_check(page: Page) -> None:
    page.locator("#currentDocLink").focus()
    page.evaluate(
        """() => {
            const smoke = window.__docsViewerManagementModalSmoke;
            smoke.metadataPromise = smoke.controller.openMetadataModal(smoke.state.docsById.get('current-doc'));
        }"""
    )
    wait_for_focus(page, "docsViewerMetadataTitleInput")
    assert_shell(
        page,
        "#docsViewerMetadataModal",
        "Edit metadata",
        ["Cancel", "OK"],
        active_id="docsViewerMetadataTitleInput",
    )
    if focus_wrap_id(page, "#docsViewerMetadataTitleInput", "Shift+Tab") != "docsViewerMetadataSaveButton":
        raise AssertionError(f"metadata modal did not wrap focus backward to OK: {modal_state(page, '#docsViewerMetadataModal')!r}")
    values = page.locator("#docsViewerMetadataModal").evaluate(
        """modal => ({
            date: modal.querySelector('#docsViewerMetadataDateInput')?.value || '',
            dateDisplay: modal.querySelector('#docsViewerMetadataDateDisplayInput')?.value || ''
        })"""
    )
    if values != {"date": "2026-06-02", "dateDisplay": "June 2026"}:
        raise AssertionError(f"metadata date fields were not populated: {values!r}")
    page.locator("#docsViewerMetadataCancelButton").click()
    assert_hidden_with_focus(page, "#docsViewerMetadataModal", "currentDocLink")


def run_settings_modal_check(page: Page) -> None:
    page.locator("#docsViewerManageSettingsButton").focus()
    page.evaluate(
        """() => {
            const smoke = window.__docsViewerManagementModalSmoke;
            smoke.controller.openSettingsModalShell();
            smoke.controller.setSettingsField({
                field: 'example_setting',
                current_value: true,
                warnings: ['Scope setting comes from the smoke fixture.']
            });
        }"""
    )
    wait_for_focus(page, "docsViewerSettingsBooleanInput")
    state = assert_shell(
        page,
        "#docsViewerSettingsModal",
        "Settings",
        ["Cancel", "OK"],
        active_id="docsViewerSettingsBooleanInput",
        size_class="docsViewer__modalCard--compact",
    )
    if "Scope setting comes from the smoke fixture." not in state["bodyText"]:
        raise AssertionError(f"settings warnings were not rendered: {state!r}")
    if focus_wrap_id(page, "#docsViewerSettingsBooleanInput", "Shift+Tab") != "docsViewerSettingsSaveButton":
        raise AssertionError("settings modal did not wrap focus backward to OK")
    page.locator("#docsViewerSettingsCancelButton").click()
    assert_hidden_with_focus(page, "#docsViewerSettingsModal", "docsViewerManageSettingsButton")


def run_transient_confirm_check(page: Page) -> None:
    page.locator("#transientOpener").focus()
    page.evaluate(
        """() => {
            const smoke = window.__docsViewerManagementModalSmoke;
            smoke.confirmPromise = smoke.managementModals.openDocsViewerConfirmModal({
                root: smoke.root,
                title: 'Confirm change',
                body: 'Apply current change?',
                primaryLabel: 'Apply',
                cancelLabel: 'Cancel'
            }).then(value => smoke.confirmResult = value);
        }"""
    )
    page.wait_for_function("() => document.querySelector('[data-role=\"docs-viewer-management-modal\"]')")
    page.wait_for_function("() => document.activeElement?.dataset.role === 'modal-primary'")
    assert_shell(
        page,
        '[data-role="docs-viewer-management-modal"]',
        "Confirm change",
        ["Apply", "Cancel"],
        active_role="modal-primary",
        size_class="docsViewer__modalCard--compact",
    )
    if focus_wrap_role(page, '[data-role="modal-primary"]', "Shift+Tab") != "modal-cancel":
        raise AssertionError("confirm modal did not wrap focus backward to cancel")
    page.keyboard.press("Escape")
    page.wait_for_function("() => window.__docsViewerManagementModalSmoke.confirmResult === false")
    if active_id(page) != "transientOpener":
        raise AssertionError("confirm modal did not return focus to opener")

    page.locator("#transientOpener").focus()
    page.evaluate(
        """() => {
            const smoke = window.__docsViewerManagementModalSmoke;
            smoke.disabledConfirmResult = undefined;
            smoke.disabledConfirmPromise = smoke.managementModals.openDocsViewerConfirmModal({
                root: smoke.root,
                title: 'Nothing to publish',
                body: 'Changed files: 0',
                primaryLabel: 'Publish',
                cancelLabel: 'Cancel',
                primaryDisabled: true
            }).then(value => smoke.disabledConfirmResult = value);
        }"""
    )
    page.wait_for_function("() => document.querySelector('[data-role=\"docs-viewer-management-modal\"]')")
    page.wait_for_function("() => document.activeElement?.dataset.role === 'modal-cancel'")
    state = assert_shell(
        page,
        '[data-role="docs-viewer-management-modal"]',
        "Nothing to publish",
        ["Publish", "Cancel"],
        active_role="modal-cancel",
        size_class="docsViewer__modalCard--compact",
    )
    if state["actionDisabled"] != [True, False]:
        raise AssertionError(f"disabled confirm modal did not disable only primary action: {state!r}")
    page.keyboard.press("Enter")
    page.wait_for_function("() => window.__docsViewerManagementModalSmoke.disabledConfirmResult === false")
    if active_id(page) != "transientOpener":
        raise AssertionError("disabled confirm modal did not return focus to opener")


def run_transient_notice_check(page: Page) -> None:
    page.locator("#transientOpener").focus()
    page.evaluate(
        """() => {
            const smoke = window.__docsViewerManagementModalSmoke;
            smoke.noticePromise = smoke.managementModals.openDocsViewerNoticeModal({
                root: smoke.root,
                title: 'Action unavailable',
                body: "This action is not available.",
                primaryLabel: 'OK'
            }).then(value => smoke.noticeResult = value);
        }"""
    )
    page.wait_for_function("() => document.querySelector('[data-role=\"docs-viewer-management-modal\"]')")
    page.wait_for_function("() => document.activeElement?.dataset.role === 'modal-primary'")
    state = assert_shell(
        page,
        '[data-role="docs-viewer-management-modal"]',
        "Action unavailable",
        ["OK"],
        active_role="modal-primary",
        size_class="docsViewer__modalCard--compact",
    )
    if "This action is not available." not in state["bodyText"]:
        raise AssertionError(f"notice modal did not render body text: {state!r}")
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_function("() => window.__docsViewerManagementModalSmoke.noticeResult?.confirmed === true")
    if active_id(page) != "transientOpener":
        raise AssertionError("notice modal did not return focus to opener")


def run_transient_text_check(page: Page) -> None:
    page.locator("#transientOpener").focus()
    page.evaluate(
        """() => {
            const smoke = window.__docsViewerManagementModalSmoke;
            smoke.textPromise = smoke.managementModals.openDocsViewerTextInputModal({
                root: smoke.root,
                title: 'New doc',
                label: 'title',
                initialValue: '',
                required: true,
                requiredMessage: 'Enter a title first.',
                primaryLabel: 'Create',
                cancelLabel: 'Cancel'
            }).then(value => smoke.textResult = value);
        }"""
    )
    wait_for_focus(page, "docsViewerManagementModalInput")
    assert_shell(
        page,
        '[data-role="docs-viewer-management-modal"]',
        "New doc",
        ["Create", "Cancel"],
        active_id="docsViewerManagementModalInput",
        size_class="docsViewer__modalCard--compact",
    )
    page.locator('[data-role="modal-primary"]').click()
    status_text = page.locator('[data-role="modal-status"]').inner_text()
    if status_text != "Enter a title first.":
        raise AssertionError(f"text modal did not show required status: {status_text!r}")
    page.locator("#docsViewerManagementModalInput").fill("Smoke Doc")
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_function(
        "() => window.__docsViewerManagementModalSmoke.textResult?.value === 'Smoke Doc'"
    )
    if active_id(page) != "transientOpener":
        raise AssertionError("text modal did not return focus to opener")


def run_transient_choice_check(page: Page) -> None:
    page.locator("#transientOpener").focus()
    page.evaluate(
        """() => {
            const smoke = window.__docsViewerManagementModalSmoke;
            smoke.choicePromise = smoke.managementModals.openDocsViewerChoiceModal({
                root: smoke.root,
                title: 'Make viewable',
                body: 'Apply to descendants?',
                value: 'selected',
                choices: [
                    { value: 'selected', label: 'Selected doc only' },
                    { value: 'all', label: 'Selected doc and descendants' }
                ],
                primaryLabel: 'Continue',
                cancelLabel: 'Cancel'
            }).then(value => smoke.choiceResult = value);
        }"""
    )
    page.wait_for_function("() => document.querySelector('[data-role=\"docs-viewer-management-modal\"]')")
    page.wait_for_function("() => document.activeElement?.name === 'docsViewerManagementModalChoice'")
    assert_shell(
        page,
        '[data-role="docs-viewer-management-modal"]',
        "Make viewable",
        ["Continue", "Cancel"],
        size_class="docsViewer__modalCard--compact",
    )
    page.locator('input[name="docsViewerManagementModalChoice"][value="all"]').check()
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_function(
        "() => window.__docsViewerManagementModalSmoke.choiceResult?.value === 'all'"
    )
    if active_id(page) != "transientOpener":
        raise AssertionError("choice modal did not return focus to opener")


def run_filename_conflict_check(page: Page) -> None:
    page.locator("#filenameConflictOpener").focus()
    page.evaluate(
        """() => {
            const smoke = window.__docsViewerManagementModalSmoke;
            smoke.filenamePromise = smoke.importModals.openReplacementDocIdModal({
                root: smoke.root,
                config: {},
                payload: {
                    collision: { doc_id: 'existing-doc' },
                    import_preview: { proposed_doc_id: 'existing-doc' }
                }
            }).then(value => smoke.filenameResult = value);
        }"""
    )
    wait_for_focus(page, "docsHtmlImportReplacementDocId")
    assert_shell(
        page,
        '[data-role="docs-import-filename-conflict-modal"]',
        "File already exists",
        ["Cancel", "Replace", "Replace all", "OK"],
        active_id="docsHtmlImportReplacementDocId",
        size_class="docsViewer__modalCard--compact",
    )
    if focus_wrap_id(page, "#docsHtmlImportReplacementDocId", "Shift+Tab") != "":
        raise AssertionError("filename-conflict focus wrap should land on an action button with role, not an id")
    if active_role(page) != "filename-conflict-ok":
        raise AssertionError("filename-conflict modal did not wrap focus backward to OK")
    page.locator("#docsHtmlImportReplacementDocId").fill("")
    page.locator('[data-role="filename-conflict-ok"]').click()
    status_text = page.locator('[data-role="filename-conflict-status"]').inner_text()
    if status_text != "Enter a doc_id first.":
        raise AssertionError(f"filename-conflict modal did not validate doc_id: {status_text!r}")
    page.locator("#docsHtmlImportReplacementDocId").fill("replacement-doc")
    page.locator('[data-role="filename-conflict-ok"]').click()
    page.wait_for_function(
        "() => window.__docsViewerManagementModalSmoke.filenameResult?.replacementDocId === 'replacement-doc'"
    )
    if active_id(page) != "filenameConflictOpener":
        raise AssertionError("filename-conflict modal did not return focus to opener")


def run_delete_confirm_idle_check(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <main id="docsViewerRoot" class="docsViewer" data-management-busy="false">
                <div id="docsViewerManageRow">
                  <div class="docsViewer__manageActions">
                    <button id="docsViewerManageActionsButton" type="button">Actions</button>
                    <div id="docsViewerManageActionsMenu" hidden>
                      <button id="docsViewerManageDeleteButton" type="button">Delete</button>
                    </div>
                    <button id="docsViewerManageRebuildButton" type="button">Rebuild</button>
                    <button id="docsViewerManageSettingsButton" type="button">Settings</button>
                    <button id="docsViewerManageNewScopeButton" type="button">New scope</button>
                    <button id="docsViewerManageDeleteScopeButton" type="button">Delete scope</button>
                    <button id="docsViewerManageImportButton" type="button">Import</button>
                    <button id="docsViewerManageNewButton" type="button">New</button>
                    <button id="docsViewerManageEditButton" type="button">Edit</button>
                    <button id="docsViewerManageViewableButton" type="button">Show</button>
                  </div>
                </div>
                <label class="docsViewer__draftLabel"><input id="docsViewerDraftToggle" type="checkbox"> show non-viewable</label>
                <nav id="docsViewerNav"></nav>
                <p id="docsViewerStatus"></p>
              </main>
            `;

            const root = document.getElementById('docsViewerRoot');
            const nav = document.getElementById('docsViewerNav');
            const status = document.getElementById('docsViewerStatus');
            const doc = {
                doc_id: 'current-doc',
                title: 'Current Doc',
                parent_id: '',
                hidden: false
            };
            const state = {
                allDocs: [doc],
                docsById: new Map([['current-doc', doc]]),
                childrenByParent: new Map(),
                payloadCache: new Map(),
                searchEntries: [],
                selectedDocId: 'current-doc',
                managementContext: true,
                managementChecked: true,
                managementAvailable: true,
                managementBusy: false,
                managementCapabilities: {
                    scopes: {
                        studio: {
                            available: true
                        }
                    }
                },
                managementText: {
                    cancelButton: 'Cancel',
                    checkingNote: 'Checking manage mode...',
                    clearSearchNote: 'Clear search to manage the current doc.',
                    deleteConfirmButton: 'Delete',
                    deleteConfirmTitle: 'Confirm delete',
                    serverNotConfiguredError: 'Server unavailable.',
                    scopeDeleteMenuButton: 'Delete scope',
                    scopeNewButton: 'New scope',
                    unavailableNote: 'Manage mode unavailable.'
                },
                searchRouteActive: false,
                showNonViewable: true,
                uiStatuses: [],
                managementMessage: '',
                managementMessageIsError: false,
                managementStatusOwnsViewerStatus: false,
                statusMenuOpen: false
            };
            window.__docsViewerDeletePreviewCalls = 0;
            window.fetch = (url, options) => {
                if (!String(url).endsWith('/docs/delete-preview')) {
                    return Promise.reject(new Error(`unexpected fetch: ${url}`));
                }
                window.__docsViewerDeletePreviewCalls += 1;
                return new Promise(resolve => {
                    window.setTimeout(() => {
                        resolve({
                            ok: true,
                            status: 200,
                            json: () => Promise.resolve({
                                ok: true,
                                allowed: true,
                                title: 'Current Doc',
                                warnings: []
                            })
                        });
                    }, 20);
                });
            };
            const management = await import('/docs-viewer/runtime/js/management/docs-viewer-management.js');
            const controller = management.initDocsViewerManagement({
                root,
                nav,
                managementState: {
                    domains: {
                        documentIndex: state,
                        generatedData: state,
                        management: state,
                        routeSession: state,
                        scopeConfig: state,
                        searchRecent: state,
                        selectedDocument: state
                    }
                },
                managementBaseUrl: 'http://docs-management.test',
                isManagementContext: () => true,
                currentViewerConfig: () => ({}),
                getConfigValue: () => undefined,
                getConfigText: (_config, _path, fallback) => fallback || '',
                formatText: (template, tokens = {}) => String(template || '').replace(/\\{(\\w+)\\}/g, (_match, key) => tokens[key] || ''),
                setStatus: (message, isError) => {
                    status.textContent = message || '';
                    status.dataset.state = isError ? 'error' : 'idle';
                },
                viewerScope: () => 'studio',
                cssEscape: value => CSS.escape(value),
                renderSidebar: () => {},
                renderBookmarkUi: () => {}
            });
            controller.render();
            document.getElementById('docsViewerManageDeleteButton').click();
            window.__docsViewerDeleteBusyDuringPreview = root.dataset.managementBusy;
        }"""
    )
    if page.evaluate("window.__docsViewerDeleteBusyDuringPreview") != "true":
        raise AssertionError("delete preview did not mark management busy before the modal")
    page.wait_for_selector('[data-role="docs-viewer-management-modal"]')
    state = page.locator("#docsViewerRoot").evaluate(
        """root => {
            const modal = document.querySelector('[data-role="docs-viewer-management-modal"]');
            const title = modal ? modal.querySelector('.docsViewer__modalTitle') : null;
            return {
                busy: root.dataset.managementBusy,
                cursor: getComputedStyle(root).cursor,
                previewCalls: window.__docsViewerDeletePreviewCalls,
                title: title ? title.textContent.trim() : ''
            };
        }"""
    )
    if state["title"] != "Confirm delete":
        raise AssertionError(f"delete confirmation modal did not open: {state!r}")
    if state["previewCalls"] != 1:
        raise AssertionError(f"delete preview request count changed: {state!r}")
    if state["busy"] != "false" or state["cursor"] == "progress":
        raise AssertionError(f"delete confirmation should not leave the viewer busy: {state!r}")


def run_index_double_click_edit_check(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <main id="docsViewerRoot" class="docsViewer" data-management-busy="false">
                <div id="docsViewerManageRow">
                  <div class="docsViewer__manageActions">
                    <button id="docsViewerManageActionsButton" type="button">Actions</button>
                    <div id="docsViewerManageActionsMenu" hidden>
                      <button id="docsViewerManageRebuildButton" type="button">Rebuild</button>
                      <button id="docsViewerManageNormalizeOrderButton" type="button">Normalize order</button>
                      <button id="docsViewerManageSettingsButton" type="button">Settings</button>
                      <button id="docsViewerManageNewScopeButton" type="button">New scope</button>
                      <button id="docsViewerManageDeleteScopeButton" type="button">Delete scope</button>
                      <button id="docsViewerManageImportButton" type="button">Import</button>
                      <button id="docsViewerManageNewButton" type="button">New</button>
                      <button id="docsViewerManageEditButton" type="button">Edit</button>
                      <button id="docsViewerManageDeleteButton" type="button">Delete</button>
                      <button id="docsViewerManageViewableButton" type="button">Show</button>
                    </div>
                  </div>
                </div>
                <label class="docsViewer__draftLabel"><input id="docsViewerDraftToggle" type="checkbox"> show non-viewable</label>
                <nav id="docsViewerNav">
                  <div class="docsViewer__navRow" data-doc-row-id="current-doc">
                    <span class="docsViewer__toggleSpacer"></span>
                    <a href="#current-doc" class="docsViewer__navLink" id="currentDocLink">Current Doc</a>
                  </div>
                  <div class="docsViewer__navRow" data-doc-row-id="other-doc">
                    <span class="docsViewer__toggleSpacer"></span>
                    <a href="#other-doc" class="docsViewer__navLink" id="otherDocLink">Other Doc</a>
                  </div>
                </nav>
                <div class="docsViewer__contextMenu" id="docsViewerContextMenu" hidden></div>
                <div id="docsViewerStatusPills" hidden></div>
                <p id="docsViewerStatus"></p>
                <div class="docsViewer__modal" id="docsViewerMetadataModal" hidden>
                  <div class="docsViewer__modalBackdrop" data-metadata-close="true"></div>
                  <div class="docsViewer__modalCard" role="dialog" aria-modal="true" aria-labelledby="docsViewerMetadataHeading">
                    <h2 class="docsViewer__modalTitle" id="docsViewerMetadataHeading">Edit metadata</h2>
                    <p id="docsViewerMetadataDocId"></p>
                    <form id="docsViewerMetadataForm">
                      <input id="docsViewerMetadataTitleInput" name="title" required>
                      <textarea id="docsViewerMetadataSummaryInput" name="summary"></textarea>
                      <input id="docsViewerMetadataDateInput" name="date">
                      <input id="docsViewerMetadataDateDisplayInput" name="date_display">
                      <select id="docsViewerMetadataStatusInput" name="ui_status"></select>
                      <input id="docsViewerMetadataNonViewableInput" name="non_viewable" type="checkbox">
                      <span id="docsViewerMetadataNonViewableLabel">non-viewable</span>
                      <input id="docsViewerMetadataParentInput" name="parent_id">
                      <div id="docsViewerMetadataParentPopup" hidden></div>
                      <button id="docsViewerMetadataCancelButton" type="button">Cancel</button>
                      <button id="docsViewerMetadataSaveButton" type="submit">OK</button>
                    </form>
                  </div>
                </div>
                <div class="docsViewer__modal" id="docsViewerImportModal" hidden>
                  <div class="docsViewer__modalBackdrop" data-import-close="true"></div>
                  <div id="docsHtmlImportRoot"></div>
                  <p id="docsHtmlImportBootStatus"></p>
                </div>
                <div class="docsViewer__modal" id="docsViewerSettingsModal" hidden>
                  <div class="docsViewer__modalBackdrop" data-settings-close="true"></div>
                  <form id="docsViewerSettingsForm">
                    <p id="docsViewerSettingsScope"></p>
                    <input id="docsViewerSettingsBooleanInput" type="checkbox">
                    <div id="docsViewerSettingsWarnings"></div>
                    <p id="docsViewerSettingsStatus"></p>
                    <button id="docsViewerSettingsCancelButton" type="button">Cancel</button>
                    <button id="docsViewerSettingsSaveButton" type="submit">OK</button>
                  </form>
                </div>
              </main>
            `;

            const docs = [
                { doc_id: 'current-doc', title: 'Current Doc', parent_id: '', viewable: true },
                { doc_id: 'other-doc', title: 'Other Doc', parent_id: '', viewable: true }
            ];
            const status = document.getElementById('docsViewerStatus');
            const state = {
                allDocs: docs,
                docs,
                childrenByParent: new Map([['', docs]]),
                docsById: new Map(docs.map(doc => [doc.doc_id, doc])),
                expandedDocIds: new Set(),
                payloadCache: new Map(),
                searchEntries: [],
                searchLoaded: false,
                searchRequestPromise: null,
                selectedDocId: 'current-doc',
                managementContext: true,
                managementChecked: true,
                managementAvailable: true,
                managementBusy: false,
                managementCapabilities: { scopes: { studio: { available: true } } },
                managementText: {
                    checkingNote: 'Checking manage mode...',
                    clearSearchNote: 'Clear search to manage the current doc.',
                    docNonViewableEmoji: 'H',
                    importCancelButton: 'Cancel',
                    metadataNonViewableLabel: 'non-viewable',
                    metadataParentInvalid: 'Invalid parent.',
                    metadataParentNoMatches: 'No matches.',
                    metadataParentRootOption: 'Root',
                    metadataStatusNoneOption: 'None',
                    metadataStatusSelectedSuffix: 'selected',
                    serverNotConfiguredError: 'Server unavailable.',
                    scopeDeleteMenuButton: 'Delete scope',
                    scopeNewButton: 'New scope',
                    settingsLoading: 'Loading settings...',
                    settingsLoadFailed: 'Settings failed.',
                    settingsSaveFailed: 'Save failed.',
                    settingsSaving: 'Saving settings...',
                    unavailableNote: 'Manage mode unavailable.'
                },
                metadataEditingDocId: '',
                metadataRestoreFocusId: '',
                reloadNonce: '',
                searchRouteActive: false,
                searchQuery: '',
                searchVisibleCount: 0,
                showNonViewable: true,
                uiStatuses: [],
                uiStatusByValue: new Map(),
                managementMessage: '',
                managementMessageIsError: false,
                managementStatusOwnsViewerStatus: false,
                statusMenuOpen: false
            };
            const management = await import('/docs-viewer/runtime/js/management/docs-viewer-management.js');
            const controller = management.initDocsViewerManagement({
                root: document.getElementById('docsViewerRoot'),
                nav: document.getElementById('docsViewerNav'),
                managementState: {
                    domains: {
                        documentIndex: state,
                        generatedData: state,
                        management: state,
                        routeSession: state,
                        scopeConfig: state,
                        searchRecent: state,
                        selectedDocument: state
                    }
                },
                SEARCH_BATCH_SIZE: 20,
                managementBaseUrl: 'http://docs-management.test',
                isManagementContext: () => true,
                currentViewerConfig: () => ({}),
                getConfigValue: () => undefined,
                getConfigText: (_config, _path, fallback) => fallback || '',
                formatText: (template, tokens = {}) => String(template || '').replace(/\\{(\\w+)\\}/g, (_match, key) => tokens[key] || ''),
                setStatus: (message, isError) => {
                    status.textContent = message || '';
                    status.dataset.state = isError ? 'error' : 'idle';
                },
                viewerScope: () => 'studio',
                cssEscape: value => CSS.escape(value),
                renderSidebar: () => {},
                renderBookmarkUi: () => {},
                cancelSearchDebounce: () => {},
                loadIndex: () => Promise.resolve(),
                setHistory: () => {}
            });
            controller.render();
            state.selectedDocId = 'other-doc';
        }"""
    )
    page.locator("#currentDocLink").dblclick()
    page.wait_for_selector("#docsViewerMetadataModal:not([hidden])")
    state = page.locator("#docsViewerMetadataModal").evaluate(
        """modal => ({
            docId: modal.querySelector('#docsViewerMetadataDocId').textContent.trim(),
            titleValue: modal.querySelector('#docsViewerMetadataTitleInput').value,
            activeId: document.activeElement ? document.activeElement.id : ''
        })"""
    )
    if state["docId"] != "other-doc" or state["titleValue"] != "Other Doc":
        raise AssertionError(f"double-click did not open edit modal for the selected index doc: {state!r}")
    page.locator("#docsViewerMetadataCancelButton").click()



def run_smoke_for_viewport(page: Page, base_url: str, viewport: dict[str, int]) -> dict[str, object]:
    page.set_viewport_size(viewport)
    page.goto(route_url(base_url, "/__docs_viewer_modal_fixture__.html"), wait_until="domcontentloaded")
    install_modal_fixture(page)
    run_metadata_modal_check(page)
    run_settings_modal_check(page)
    run_transient_confirm_check(page)
    run_transient_notice_check(page)
    run_transient_text_check(page)
    run_transient_choice_check(page)
    run_filename_conflict_check(page)
    run_delete_confirm_idle_check(page)
    run_index_double_click_edit_check(page)
    return {
        "width": viewport["width"],
        "height": viewport["height"],
        "checked": [
            "metadata",
            "settings",
            "transient-confirm",
            "transient-notice",
            "transient-text",
            "transient-choice",
            "filename-conflict",
            "delete-confirm-idle",
            "index-double-click-edit",
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
        raise AssertionError(f"page errors during Docs Viewer management modal smoke: {errors!r}")
    print(json.dumps({"viewports": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

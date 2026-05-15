#!/usr/bin/env python3
"""Smoke-check Docs Viewer management modal composition."""

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
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def install_modal_fixture(page: Page) -> None:
    page.evaluate(
        """async () => {
            const css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = '/assets/docs-viewer/css/docs-viewer-management.css';
            const cssLoaded = new Promise((resolve, reject) => {
                css.addEventListener('load', resolve, { once: true });
                css.addEventListener('error', reject, { once: true });
            });
            document.head.appendChild(css);
            await cssLoaded;

            document.body.innerHTML = `
              <main id="docsViewerRoot" class="docsViewer">
                <div class="docsViewer__manageActions">
                  <button id="docsViewerManageActionsButton" type="button">Actions</button>
                  <button id="docsViewerManageImportButton" type="button">Import</button>
                  <button id="docsViewerManageSettingsButton" type="button">Settings</button>
                  <button id="transientOpener" type="button">Transient</button>
                  <button id="filenameConflictOpener" type="button">Filename conflict</button>
                </div>
                <nav id="docsViewerNav" class="docsViewer__nav">
                  <div data-doc-row-id="current-doc">
                    <a href="#current-doc" class="docsViewer__navLink" id="currentDocLink">Current Doc</a>
                  </div>
                </nav>
                <div class="docsViewer__modal" id="docsViewerMetadataModal" hidden>
                  <div class="docsViewer__modalBackdrop" data-metadata-close="true"></div>
                  <div class="docsViewer__modalCard" role="dialog" aria-modal="true" aria-labelledby="docsViewerMetadataHeading">
                    <div class="docsViewer__modalHeader">
                      <div class="docsViewer__modalHeaderCopy">
                        <h2 class="docsViewer__modalTitle" id="docsViewerMetadataHeading">Edit metadata</h2>
                        <p class="docsViewer__modalMeta muted small" id="docsViewerMetadataDocId"></p>
                      </div>
                    </div>
                    <form class="docsViewer__modalForm" id="docsViewerMetadataForm">
                      <label class="docsViewer__field">
                        <span class="docsViewer__fieldLabel">title</span>
                        <input class="docsViewer__fieldInput" id="docsViewerMetadataTitleInput" name="title" type="text" required>
                      </label>
                      <label class="docsViewer__field">
                        <span class="docsViewer__fieldLabel">summary</span>
                        <textarea class="docsViewer__fieldInput docsViewer__fieldInput--textarea" id="docsViewerMetadataSummaryInput" name="summary" rows="4"></textarea>
                      </label>
                      <label class="docsViewer__field">
                        <span class="docsViewer__fieldLabel" id="docsViewerMetadataStatusLabel">status</span>
                        <select class="docsViewer__fieldInput docsViewer__fieldInput--listbox" id="docsViewerMetadataStatusInput" name="ui_status"></select>
                      </label>
                      <label class="docsViewer__field docsViewer__field--checkbox">
                        <input class="docsViewer__checkboxInput" id="docsViewerMetadataHiddenInput" name="hidden" type="checkbox">
                        <span class="docsViewer__fieldLabel" id="docsViewerMetadataHiddenLabel">hidden</span>
                      </label>
                      <div class="docsViewer__field docsViewer__field--parent">
                        <label class="docsViewer__fieldLabel" for="docsViewerMetadataParentInput">parent</label>
                        <div class="docsViewer__parentPicker">
                          <input class="docsViewer__fieldInput" id="docsViewerMetadataParentInput" name="parent_id" type="text" role="combobox" aria-expanded="false" aria-controls="docsViewerMetadataParentPopup">
                          <div class="docsViewer__parentPopup" id="docsViewerMetadataParentPopup" role="listbox" hidden></div>
                        </div>
                      </div>
                      <label class="docsViewer__field">
                        <span class="docsViewer__fieldLabel">sort order</span>
                        <input class="docsViewer__fieldInput" id="docsViewerMetadataSortOrderInput" name="sort_order" type="number" step="1">
                      </label>
                      <p class="docsViewer__modalNote muted small" id="docsViewerMetadataNote">Blank sort order leaves the doc unordered.</p>
                      <div class="docsViewer__modalActions">
                        <button class="docsViewer__actionButton docsViewer__actionButton--defaultWidth" type="button" id="docsViewerMetadataCancelButton">Cancel</button>
                        <button class="docsViewer__actionButton docsViewer__actionButton--defaultWidth" type="submit" id="docsViewerMetadataSaveButton">OK</button>
                      </div>
                    </form>
                  </div>
                </div>
                <div class="docsViewer__modal" id="docsViewerImportModal" hidden>
                  <div class="docsViewer__modalBackdrop" data-import-close="true"></div>
                  <div class="docsViewer__modalCard docsViewer__modalCard--document" role="dialog" aria-modal="true" aria-labelledby="docsViewerImportHeading">
                    <div class="docsViewer__modalHeader">
                      <div class="docsViewer__modalHeaderCopy">
                        <h2 class="docsViewer__modalTitle" id="docsViewerImportHeading">Import docs</h2>
                      </div>
                    </div>
                    <div class="docsViewer__importBody" id="docsViewerImportBody">
                      <div class="docsViewerImport" id="docsHtmlImportRoot" hidden tabindex="-1">
                        <div class="docsViewerImport__panel">
                          <div class="docsViewerImport__footer">
                            <p class="docsViewerImport__status" id="docsHtmlImportStatus">Ready.</p>
                            <div class="docsViewerImport__actions">
                              <button type="button" class="docsViewerImport__button docsViewerImport__button--defaultWidth" id="docsHtmlImportRun">Import</button>
                              <button type="button" class="docsViewerImport__button docsViewerImport__button--defaultWidth" id="docsHtmlImportConfirm" hidden>Confirm overwrite</button>
                              <button type="button" class="docsViewerImport__button docsViewerImport__button--defaultWidth" id="docsHtmlImportCancel" hidden>Cancel overwrite</button>
                            </div>
                          </div>
                        </div>
                      </div>
                      <p class="docsViewerImport__status" id="docsHtmlImportBootStatus">loading docs import...</p>
                    </div>
                  </div>
                </div>
                <div class="docsViewer__modal" id="docsViewerSettingsModal" hidden>
                  <div class="docsViewer__modalBackdrop" data-settings-close="true"></div>
                  <div class="docsViewer__modalCard docsViewer__modalCard--compact" role="dialog" aria-modal="true" aria-labelledby="docsViewerSettingsHeading">
                    <div class="docsViewer__modalHeader">
                      <div class="docsViewer__modalHeaderCopy">
                        <h2 class="docsViewer__modalTitle" id="docsViewerSettingsHeading">Settings</h2>
                        <p class="docsViewer__modalMeta muted small" id="docsViewerSettingsScope"></p>
                      </div>
                    </div>
                    <form class="docsViewer__modalForm" id="docsViewerSettingsForm">
                      <label class="docsViewer__field docsViewer__field--checkbox">
                        <input class="docsViewer__checkboxInput" id="docsViewerSettingsUpdatedInput" name="show_updated_date" type="checkbox">
                        <span class="docsViewer__fieldLabel" id="docsViewerSettingsUpdatedLabel">show updated dates</span>
                      </label>
                      <div class="docsViewer__settingsWarnings muted small" id="docsViewerSettingsWarnings" hidden></div>
                      <p class="docsViewer__modalNote muted small" id="docsViewerSettingsStatus" hidden></p>
                      <div class="docsViewer__modalActions">
                        <button class="docsViewer__actionButton docsViewer__actionButton--defaultWidth" type="button" id="docsViewerSettingsCancelButton">Cancel</button>
                        <button class="docsViewer__actionButton docsViewer__actionButton--defaultWidth" type="submit" id="docsViewerSettingsSaveButton">OK</button>
                      </div>
                    </form>
                  </div>
                </div>
              </main>
            `;

            const managementModals = await import('/assets/docs-viewer/js/docs-viewer-management-modals.js');
            const importModals = await import('/assets/docs-viewer/js/docs-html-import-modals.js');
            const root = document.getElementById('docsViewerRoot');
            const nav = document.getElementById('docsViewerNav');
            const state = {
                docsById: new Map([
                    ['current-doc', {
                        doc_id: 'current-doc',
                        title: 'Current Doc',
                        summary: 'Smoke fixture doc.',
                        parent_id: '',
                        sort_order: 2,
                        ui_status: 'in-progress',
                        hidden: false
                    }]
                ]),
                managementBusy: false,
                managementText: {
                    importCancelButton: 'Cancel',
                    metadataParentNoMatches: 'No matches',
                    metadataParentRootOption: 'Top level',
                    metadataStatusNoneOption: 'No status',
                    metadataStatusSelectedSuffix: 'selected',
                    settingsLoading: 'Loading settings...',
                    settingsLoadFailed: 'Settings failed.',
                    settingsSaveFailed: 'Save failed.',
                    settingsSaving: 'Saving settings...'
                },
                metadataEditingDocId: '',
                metadataRestoreFocusId: '',
                uiStatuses: [
                    { ui_status: 'in-progress', emoji: '>', label: 'In progress' },
                    { ui_status: 'done', emoji: '*', label: 'Done' }
                ]
            };
            const refs = {
                importModal: document.getElementById('docsViewerImportModal'),
                importRoot: document.getElementById('docsHtmlImportRoot'),
                manageActionsButton: document.getElementById('docsViewerManageActionsButton'),
                manageImportButton: document.getElementById('docsViewerManageImportButton'),
                manageSettingsButton: document.getElementById('docsViewerManageSettingsButton'),
                metadataCancelButton: document.getElementById('docsViewerMetadataCancelButton'),
                metadataDocId: document.getElementById('docsViewerMetadataDocId'),
                metadataForm: document.getElementById('docsViewerMetadataForm'),
                metadataHiddenInput: document.getElementById('docsViewerMetadataHiddenInput'),
                metadataModal: document.getElementById('docsViewerMetadataModal'),
                metadataParentInput: document.getElementById('docsViewerMetadataParentInput'),
                metadataParentPopup: document.getElementById('docsViewerMetadataParentPopup'),
                metadataSortOrderInput: document.getElementById('docsViewerMetadataSortOrderInput'),
                metadataStatusInput: document.getElementById('docsViewerMetadataStatusInput'),
                metadataSummaryInput: document.getElementById('docsViewerMetadataSummaryInput'),
                metadataTitleInput: document.getElementById('docsViewerMetadataTitleInput'),
                settingsCancelButton: document.getElementById('docsViewerSettingsCancelButton'),
                settingsForm: document.getElementById('docsViewerSettingsForm'),
                settingsModal: document.getElementById('docsViewerSettingsModal'),
                settingsSaveButton: document.getElementById('docsViewerSettingsSaveButton'),
                settingsScope: document.getElementById('docsViewerSettingsScope'),
                settingsStatus: document.getElementById('docsViewerSettingsStatus'),
                settingsUpdatedInput: document.getElementById('docsViewerSettingsUpdatedInput'),
                settingsWarnings: document.getElementById('docsViewerSettingsWarnings')
            };
            const controller = managementModals.createDocsViewerManagementModalController({
                nav,
                state,
                context: {
                    cssEscape: CSS.escape
                },
                refs,
                callbacks: {
                    currentSelectedDoc: () => state.docsById.get('current-doc'),
                    hideContextMenu: () => {},
                    hideManageActionsMenu: () => {},
                    isDocHidden: doc => Boolean(doc.hidden),
                    metadataParentOptions: () => [
                        { value: '', label: 'Top level' },
                        { value: 'parent-doc', label: 'Parent Doc' }
                    ],
                    onImportOpen: () => {
                        refs.importRoot.hidden = false;
                        document.getElementById('docsHtmlImportBootStatus').hidden = true;
                    },
                    onMetadataSubmit: () => controller.closeMetadataModal({ saved: true }),
                    onSettingsSubmit: event => {
                        event.preventDefault();
                        controller.closeSettingsModal();
                    },
                    viewerScope: () => 'studio'
                }
            });
            controller.wireEvents();
            document.addEventListener('keydown', event => controller.handleDocumentKeydown(event));
            window.__docsViewerManagementModalSmoke = {
                controller,
                importModals,
                managementModals,
                root,
                state
            };
        }"""
    )


def modal_state(page: Page, selector: str) -> dict[str, object]:
    return page.locator(selector).evaluate(
        """modal => {
            const card = modal.querySelector('[role="dialog"]');
            const title = modal.querySelector('.docsViewer__modalTitle');
            const actions = Array.from(modal.querySelectorAll('.docsViewer__modalActions button, .docsViewerImport__actions button:not([hidden])'));
            const active = document.activeElement;
            const rect = card ? card.getBoundingClientRect() : null;
            return {
                hidden: modal.hidden,
                role: card ? card.getAttribute('role') : '',
                modal: card ? card.getAttribute('aria-modal') : '',
                labelledBy: card ? card.getAttribute('aria-labelledby') : '',
                titleId: title ? title.id : '',
                title: title ? title.textContent.trim() : '',
                cardClass: card ? card.className : '',
                cardWidth: rect ? Math.round(rect.width) : 0,
                viewportWidth: window.innerWidth,
                actionLabels: actions.map(button => button.textContent.trim()),
                actionClasses: actions.map(button => button.className),
                activeId: active ? active.id || '' : '',
                activeRole: active ? active.dataset.role || '' : '',
                bodyText: modal.textContent || ''
            };
        }"""
    )


def assert_shell(
    page: Page,
    selector: str,
    title: str,
    actions: list[str],
    active_id: str = "",
    active_role: str = "",
    size_class: str = "",
) -> dict[str, object]:
    state = modal_state(page, selector)
    if state["hidden"]:
        raise AssertionError(f"modal should be visible: {state!r}")
    if state["role"] != "dialog" or state["modal"] != "true":
        raise AssertionError(f"modal lacks dialog semantics: {state!r}")
    if not state["labelledBy"] or state["labelledBy"] != state["titleId"]:
        raise AssertionError(f"modal is not labelled by its title: {state!r}")
    if state["title"] != title:
        raise AssertionError(f"unexpected modal title: {state!r}")
    if actions and state["actionLabels"] != actions:
        raise AssertionError(f"unexpected modal actions: {state!r}")
    if size_class and size_class not in state["cardClass"]:
        raise AssertionError(f"modal size class mismatch: {state!r}")
    if state["cardWidth"] > state["viewportWidth"] - 8:
        raise AssertionError(f"modal exceeds viewport width: {state!r}")
    if not all(("defaultWidth" in value or "default-width" in value) for value in state["actionClasses"]):
        raise AssertionError(f"modal actions are missing default-width class: {state!r}")
    if active_id and state["activeId"] != active_id:
        raise AssertionError(f"modal focus did not enter expected control: {state!r}")
    if active_role and state["activeRole"] != active_role:
        raise AssertionError(f"modal focus did not enter expected role: {state!r}")
    return state


def wait_for_focus(page: Page, expected_id: str) -> None:
    page.wait_for_function(
        "expected => document.activeElement && document.activeElement.id === expected",
        arg=expected_id,
    )


def focus_wrap_id(page: Page, selector: str, key: str) -> str:
    page.locator(selector).focus()
    page.keyboard.press(key)
    return page.evaluate("document.activeElement ? document.activeElement.id || '' : ''")


def focus_wrap_role(page: Page, selector: str, key: str) -> str:
    page.locator(selector).focus()
    page.keyboard.press(key)
    return page.evaluate("document.activeElement ? document.activeElement.dataset.role || '' : ''")


def active_id(page: Page) -> str:
    return page.evaluate("document.activeElement ? document.activeElement.id || '' : ''")


def active_role(page: Page) -> str:
    return page.evaluate("document.activeElement ? document.activeElement.dataset.role || '' : ''")


def assert_hidden_with_focus(page: Page, selector: str, expected_focus_id: str) -> None:
    page.wait_for_function(
        """([modalSelector, expected]) => {
            const modal = document.querySelector(modalSelector);
            return modal && modal.hidden && document.activeElement && document.activeElement.id === expected;
        }""",
        arg=[selector, expected_focus_id],
    )
    state = page.locator(selector).evaluate(
        """(modal, expected) => ({
            hidden: modal.hidden,
            focusedId: document.activeElement ? document.activeElement.id || '' : '',
            expected
        })""",
        expected_focus_id,
    )
    if state != {"hidden": True, "focusedId": expected_focus_id, "expected": expected_focus_id}:
        raise AssertionError(f"modal did not close and return focus: {state!r}")


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
    page.locator("#docsViewerMetadataCancelButton").click()
    assert_hidden_with_focus(page, "#docsViewerMetadataModal", "currentDocLink")


def run_import_modal_check(page: Page) -> None:
    page.locator("#docsViewerManageImportButton").focus()
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
    if focus_wrap_id(page, "#docsViewerImportCancelButton", "Shift+Tab") != "docsHtmlImportRun":
        raise AssertionError("import modal did not wrap focus backward to Import")
    page.keyboard.press("Escape")
    assert_hidden_with_focus(page, "#docsViewerImportModal", "docsViewerManageImportButton")


def run_settings_modal_check(page: Page) -> None:
    page.locator("#docsViewerManageSettingsButton").focus()
    page.evaluate(
        """() => {
            const smoke = window.__docsViewerManagementModalSmoke;
            smoke.controller.openSettingsModalShell();
            smoke.controller.setSettingsField({
                current_value: true,
                warnings: ['Scope setting comes from the smoke fixture.']
            });
        }"""
    )
    wait_for_focus(page, "docsViewerSettingsUpdatedInput")
    state = assert_shell(
        page,
        "#docsViewerSettingsModal",
        "Settings",
        ["Cancel", "OK"],
        active_id="docsViewerSettingsUpdatedInput",
        size_class="docsViewer__modalCard--compact",
    )
    if "Scope setting comes from the smoke fixture." not in state["bodyText"]:
        raise AssertionError(f"settings warnings were not rendered: {state!r}")
    if focus_wrap_id(page, "#docsViewerSettingsUpdatedInput", "Shift+Tab") != "docsViewerSettingsSaveButton":
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
                title: 'Confirm archive',
                body: 'Archive Current Doc?',
                primaryLabel: 'Archive',
                cancelLabel: 'Cancel'
            }).then(value => smoke.confirmResult = value);
        }"""
    )
    page.wait_for_function("() => document.querySelector('[data-role=\"docs-viewer-management-modal\"]')")
    page.wait_for_function("() => document.activeElement?.dataset.role === 'modal-primary'")
    assert_shell(
        page,
        '[data-role="docs-viewer-management-modal"]',
        "Confirm archive",
        ["Archive", "Cancel"],
        active_role="modal-primary",
        size_class="docsViewer__modalCard--compact",
    )
    if focus_wrap_role(page, '[data-role="modal-primary"]', "Shift+Tab") != "modal-cancel":
        raise AssertionError("confirm modal did not wrap focus backward to cancel")
    page.keyboard.press("Escape")
    page.wait_for_function("() => window.__docsViewerManagementModalSmoke.confirmResult === false")
    if active_id(page) != "transientOpener":
        raise AssertionError("confirm modal did not return focus to opener")


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
        ["Cancel", "Replace", "OK"],
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


def run_smoke_for_viewport(page: Page, base_url: str, viewport: dict[str, int]) -> dict[str, object]:
    page.set_viewport_size(viewport)
    page.goto(route_url(base_url, "/assets/docs-viewer/css/docs-viewer-management.css"), wait_until="domcontentloaded")
    install_modal_fixture(page)
    run_metadata_modal_check(page)
    run_import_modal_check(page)
    run_settings_modal_check(page)
    run_transient_confirm_check(page)
    run_transient_text_check(page)
    run_transient_choice_check(page)
    run_filename_conflict_check(page)
    return {
        "width": viewport["width"],
        "height": viewport["height"],
        "checked": [
            "metadata",
            "import",
            "settings",
            "transient-confirm",
            "transient-text",
            "transient-choice",
            "filename-conflict",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--site-root", help="Serve a built site or repository root on a temporary local HTTP server.")
    args = parser.parse_args()

    static_server = None
    base_url = args.base_url
    if args.site_root:
        static_server, base_url = start_static_server(Path(args.site_root))

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

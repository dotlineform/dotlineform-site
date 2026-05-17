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
                          <div class="docsViewerImport__scrollRegion">
                            <p class="docsViewerImport__intro" id="docsHtmlImportIntro">Import fixture.</p>
                            <div class="docsViewerImport__result" id="docsHtmlImportResult">
                              <h3 id="docsHtmlImportResultTitle">Created new doc</h3>
                              <dl class="docsViewerImport__resultGrid">
                                <div>
                                  <dt>title</dt>
                                  <dd id="docsHtmlImportLongResult">Long result text</dd>
                                </div>
                              </dl>
                            </div>
                          </div>
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
                '/assets/docs-viewer/data/ui-text.json': {
                    docs_html_import: {
                        script_file_result_type: 'script file'
                    }
                },
                '/assets/docs-viewer/data/docs-viewer-config.json': {
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
            const module = await import('/assets/docs-viewer/js/docs-html-import.js');
            await module.initDocsHtmlImport({
                root: document.getElementById('docsHtmlImportRoot'),
                bootStatus: document.getElementById('docsHtmlImportBootStatus'),
                docsViewerConfigUrl: '/assets/docs-viewer/data/docs-viewer-config.json',
                uiTextUrl: '/assets/docs-viewer/data/ui-text.json',
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


def run_scope_lifecycle_create_payload_check(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <main id="docsViewerRoot" class="docsViewer">
                <button id="scopeLifecycleOpener" type="button">New scope</button>
              </main>
            `;
            window.__docsViewerScopeCreateRequests = [];
            window.fetch = async (url, options = {}) => {
                const body = options.body ? JSON.parse(options.body) : null;
                window.__docsViewerScopeCreateRequests.push({
                    url: String(url),
                    body
                });
                return {
                    ok: true,
                    status: 200,
                    json: async () => ({
                        ok: true,
                        schema_version: 'docs_scope_lifecycle_preview_v1',
                        action: 'create_scope',
                        operation: 'preview',
                        scope_id: body.scope_id,
                        title: body.title,
                        summary_text: 'Preview scope create.',
                        blockers: [],
                        created_files: [],
                        changed_files: [],
                        build_commands: [],
                        urls: {
                            management: `/docs/?scope=${body.scope_id}&mode=manage`,
                            public: ''
                        }
                    })
                };
            };
            const lifecycle = await import('/assets/docs-viewer/js/docs-viewer-scope-lifecycle.js');
            window.__docsViewerScopeCreatePromise = lifecycle.openCreateScopeFlow({
                root: document.getElementById('docsViewerRoot'),
                state: {
                    managementText: {
                        cancelButton: 'Cancel',
                        scopeBuildSearchLabel: 'build inline search',
                        scopeCreateIntro: 'Create scope fixture.',
                        scopeCreatePreviewTitle: 'Preview new scope',
                        scopeCreatePreviewing: 'Previewing new scope...',
                        scopeCreateRequiredMessage: 'Enter the required scope fields.',
                        scopeCreateRouteRequiredMessage: 'Enter a public route path for public read-only scopes.',
                        scopeCreateTitle: 'New scope',
                        scopeDefaultDocIdLabel: 'default doc id',
                        scopeIdLabel: 'scope id',
                        scopeLocalCommittedMode: 'local-only committed scope',
                        scopeLocalCommittedModeNote: 'Local committed note.',
                        scopeLocalUncommittedMode: 'local-only uncommitted scope',
                        scopeLocalUncommittedModeNote: 'Local uncommitted note.',
                        scopePreviewButton: 'Preview',
                        scopePublicReadonlyMode: 'public read-only scope',
                        scopePublicReadonlyModeNote: 'Public note.',
                        scopePublicRoutePathLabel: 'public route path',
                        scopePublishingModeLabel: 'publishing mode',
                        scopeSaveButton: 'Save',
                        scopeSourceRootLabel: 'source root',
                        scopeTitleLabel: 'title',
                        scopeWriteGeneratedLabel: 'write generated outputs immediately'
                    }
                },
                capabilities: {
                    scope_lifecycle: {
                        publishing_modes: ['public_readonly', 'local_committed', 'local_uncommitted']
                    }
                },
                clientOptions: {
                    baseUrl: 'http://docs-management.test'
                },
                callbacks: {
                    render: () => {},
                    setBusy: busy => { window.__docsViewerScopeBusy = busy; },
                    setMessage: (message, isError) => {
                        window.__docsViewerScopeMessage = { message, isError };
                    }
                }
            }).then(value => {
                window.__docsViewerScopeCreateResult = value;
            });
        }"""
    )
    page.wait_for_selector('[data-role="docs-viewer-management-modal"]')
    assert_shell(
        page,
        '[data-role="docs-viewer-management-modal"]',
        "New scope",
        ["Preview", "Cancel"],
        size_class="docsViewer__modalCard--wide",
    )
    page.locator('[data-role="scope-id"]').fill("private-notes")
    page.locator('[data-role="scope-title"]').fill("Private Notes")
    page.locator('[data-role="scope-write-generated"]').uncheck()
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_function("() => window.__docsViewerScopeCreateRequests.length === 1")
    request = page.evaluate("window.__docsViewerScopeCreateRequests[0]")
    expected_body = {
        "scope_id": "private-notes",
        "title": "Private Notes",
        "source_root": "_docs_private-notes",
        "default_doc_id": "private-notes",
        "publishing_mode": "public_readonly",
        "public_route_path": "/private-notes/",
        "build_inline_search": False,
        "write_generated_outputs": False,
    }
    if request["url"] != "http://docs-management.test/docs/scopes/create-preview":
        raise AssertionError(f"scope create preview used the wrong endpoint: {request!r}")
    if request["body"] != expected_body:
        raise AssertionError(f"scope create payload did not match disabled generated-output state: {request!r}")
    page.wait_for_function("() => document.querySelector('[data-role=\"docs-viewer-management-modal\"] .docsViewer__modalTitle')?.textContent.trim() === 'Preview new scope'")
    page.locator('button[data-role="modal-cancel"]').click()
    page.wait_for_function("() => window.__docsViewerScopeCreateResult === null")


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
                    <button id="docsViewerManageArchiveButton" type="button">Archive</button>
                    <button id="docsViewerManageViewableButton" type="button">Show</button>
                  </div>
                </div>
                <button id="docsViewerIndexUndoButton" type="button">Undo</button>
                <label class="docsViewer__draftLabel"><input id="docsViewerDraftToggle" type="checkbox"> show hidden</label>
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
                sort_order: 1,
                hidden: false
            };
            const state = {
                allDocs: [doc],
                docsById: new Map([['current-doc', doc]]),
                childrenByParent: new Map(),
                payloadCache: new Map(),
                searchEntries: [],
                selectedDocId: 'current-doc',
                managementMode: true,
                managementChecked: true,
                managementAvailable: true,
                managementBusy: false,
                managementCapabilities: {
                    scopes: {
                        studio: {
                            available: true,
                            archive_available: true
                        }
                    }
                },
                managementText: {
                    archiveUnavailableNote: 'Archive unavailable.',
                    cancelButton: 'Cancel',
                    checkingNote: 'Checking manage mode...',
                    clearSearchNote: 'Clear search to manage the current doc.',
                    deleteConfirmButton: 'Delete',
                    deleteConfirmTitle: 'Confirm delete',
                    serverNotConfiguredError: 'Server unavailable.',
                    unavailableNote: 'Manage mode unavailable.',
                    undoMoveLabel: 'Undo move'
                },
                searchRouteActive: false,
                showHidden: true,
                uiStatuses: [],
                moveUndo: null,
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
                                warnings: [],
                                inbound_refs: []
                            })
                        });
                    }, 20);
                });
            };
            const management = await import('/assets/docs-viewer/js/docs-viewer-management.js');
            const controller = management.initDocsViewerManagement({
                root,
                nav,
                state,
                MANAGEMENT_MODE: 'manage',
                managementBaseUrl: 'http://docs-management.test',
                getCurrentMode: () => 'manage',
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
    run_import_result_rows_check(page)
    run_scope_lifecycle_create_payload_check(page)
    run_delete_confirm_idle_check(page)
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
            "import-result-rows",
            "scope-lifecycle-create-payload",
            "delete-confirm-idle",
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

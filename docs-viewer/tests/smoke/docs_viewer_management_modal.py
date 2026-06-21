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


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_VIEWER_SHARED_RUNTIME_PREFIX = "/docs-viewer/runtime/js/shared/"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        if path.startswith(DOCS_VIEWER_SHARED_RUNTIME_PREFIX):
            relative_path = path.removeprefix(DOCS_VIEWER_SHARED_RUNTIME_PREFIX).split("?", 1)[0].split("#", 1)[0]
            return str(REPO_ROOT / "site/docs-viewer/runtime/js/shared" / relative_path)
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


def install_modal_fixture(page: Page) -> None:
    page.evaluate(
        """async () => {
            const css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = '/docs-viewer/static/css/docs-viewer-manage.css';
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
                        <span class="docsViewer__fieldLabel">date</span>
                        <input class="docsViewer__fieldInput" id="docsViewerMetadataDateInput" name="date" type="text">
                      </label>
                      <label class="docsViewer__field">
                        <span class="docsViewer__fieldLabel">date display</span>
                        <input class="docsViewer__fieldInput" id="docsViewerMetadataDateDisplayInput" name="date_display" type="text">
                      </label>
                      <label class="docsViewer__field">
                        <span class="docsViewer__fieldLabel" id="docsViewerMetadataStatusLabel">status</span>
                        <select class="docsViewer__fieldInput docsViewer__fieldInput--listbox" id="docsViewerMetadataStatusInput" name="ui_status"></select>
                      </label>
                      <label class="docsViewer__field docsViewer__field--checkbox">
                        <input class="docsViewer__checkboxInput" id="docsViewerMetadataNonViewableInput" name="non_viewable" type="checkbox">
                        <span class="docsViewer__fieldLabel" id="docsViewerMetadataNonViewableLabel">non-viewable</span>
                      </label>
                      <div class="docsViewer__field docsViewer__field--parent">
                        <label class="docsViewer__fieldLabel" for="docsViewerMetadataParentInput">parent</label>
                        <div class="docsViewer__parentPicker">
                          <input class="docsViewer__fieldInput" id="docsViewerMetadataParentInput" name="parent_id" type="text" role="combobox" aria-expanded="false" aria-controls="docsViewerMetadataParentPopup">
                          <div class="docsViewer__parentPopup" id="docsViewerMetadataParentPopup" role="listbox" hidden></div>
                        </div>
                      </div>
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

            const managementModals = await import('/docs-viewer/runtime/js/management/docs-viewer-management-modals.js');
            const importModals = await import('/docs-viewer/runtime/js/import/docs-html-import-modals.js');
            const root = document.getElementById('docsViewerRoot');
            const nav = document.getElementById('docsViewerNav');
            const state = {
                docsById: new Map([
                    ['current-doc', {
                        doc_id: 'current-doc',
                        title: 'Current Doc',
                        summary: 'Smoke fixture doc.',
                        date: '2026-06-02',
                        date_display: 'June 2026',
                        parent_id: '',
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
                metadataDateDisplayInput: document.getElementById('docsViewerMetadataDateDisplayInput'),
                metadataDateInput: document.getElementById('docsViewerMetadataDateInput'),
                metadataDocId: document.getElementById('docsViewerMetadataDocId'),
                metadataForm: document.getElementById('docsViewerMetadataForm'),
                metadataNonViewableInput: document.getElementById('docsViewerMetadataNonViewableInput'),
                metadataModal: document.getElementById('docsViewerMetadataModal'),
                metadataParentInput: document.getElementById('docsViewerMetadataParentInput'),
                metadataParentPopup: document.getElementById('docsViewerMetadataParentPopup'),
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
                    isDocNonViewable: doc => doc.viewable === false,
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
                actionDisabled: actions.map(button => button.disabled),
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
                            management: `/docs/?scope=${body.scope_id}`,
                            public: ''
                        }
                    })
                };
            };
            const lifecycle = await import('/docs-viewer/runtime/js/management/docs-viewer-scope-lifecycle.js');
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
                        scopeCreateRouteRequiredMessage: 'Enter a public route path for public scopes.',
                        scopeCreateTitle: 'New scope',
                        scopeDefaultDocIdLabel: 'default doc id',
                        scopeIdLabel: 'scope id',
                        scopeLocalCommittedMode: 'local tracked',
                        scopeLocalCommittedModeNote: 'Local committed note.',
                        scopeLocalUncommittedMode: 'local untracked',
                        scopeLocalUncommittedModeNote: 'Local uncommitted note.',
                        scopePreviewButton: 'Preview',
                        scopePublicReadonlyMode: 'public',
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
    auto_title = page.locator('[data-role="scope-title"]').input_value()
    if auto_title != "Private Notes":
        raise AssertionError(f"scope title did not auto-fill from scope id: {auto_title!r}")
    mode_options = page.locator('[data-role="scope-publishing-mode"] option').evaluate_all(
        "options => options.map(option => option.value)"
    )
    if mode_options != ["local_uncommitted", "local_committed", "public_readonly"]:
        raise AssertionError(f"scope publishing modes should include public_readonly after local defaults: {mode_options!r}")
    selected_mode = page.locator('[data-role="scope-publishing-mode"]').input_value()
    if selected_mode != "local_uncommitted":
        raise AssertionError(f"scope publishing mode did not default to the first local mode: {selected_mode!r}")
    if not page.locator('[data-role="scope-route-field"]').evaluate("node => node.hidden"):
        raise AssertionError("public route path field should be hidden for local scope modes")
    page.locator('[data-role="scope-publishing-mode"]').select_option("public_readonly")
    if page.locator('[data-role="scope-route-field"]').evaluate("node => node.hidden"):
        raise AssertionError("public route path field should be visible for public_readonly mode")
    auto_route = page.locator('[data-role="scope-public-route-path"]').input_value()
    if auto_route != "/private-notes/":
        raise AssertionError(f"scope route path did not auto-fill from scope id: {auto_route!r}")
    page.locator('[data-role="scope-publishing-mode"]').select_option("local_uncommitted")
    page.locator('[data-role="scope-write-generated"]').uncheck()
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_function("() => window.__docsViewerScopeCreateRequests.length === 1")
    request = page.evaluate("window.__docsViewerScopeCreateRequests[0]")
    expected_body = {
        "scope_id": "private-notes",
        "title": "Private Notes",
        "source_root": "docs-viewer/source/private-notes",
        "default_doc_id": "private-notes",
        "publishing_mode": "local_uncommitted",
        "public_route_path": "",
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
                    <input id="docsViewerSettingsUpdatedInput" type="checkbox">
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
    page.goto(route_url(base_url, "/docs-viewer/static/css/docs-viewer-manage.css"), wait_until="domcontentloaded")
    install_modal_fixture(page)
    run_metadata_modal_check(page)
    run_import_modal_check(page)
    run_settings_modal_check(page)
    run_transient_confirm_check(page)
    run_transient_notice_check(page)
    run_transient_text_check(page)
    run_transient_choice_check(page)
    run_filename_conflict_check(page)
    run_import_render_module_check(page)
    run_import_workflow_module_check(page)
    run_import_result_rows_check(page)
    run_scope_lifecycle_create_payload_check(page)
    run_delete_confirm_idle_check(page)
    run_index_double_click_edit_check(page)
    return {
        "width": viewport["width"],
        "height": viewport["height"],
        "checked": [
            "metadata",
            "import",
            "settings",
            "transient-confirm",
            "transient-notice",
            "transient-text",
            "transient-choice",
            "filename-conflict",
            "import-render-module",
            "import-workflow-module",
            "import-result-rows",
            "scope-lifecycle-create-payload",
            "delete-confirm-idle",
            "index-double-click-edit",
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

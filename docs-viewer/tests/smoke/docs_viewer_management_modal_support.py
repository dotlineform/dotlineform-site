#!/usr/bin/env python3
"""Shared fixtures and assertions for Docs Viewer management modal smokes."""

from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_VIEWER_SHARED_RUNTIME_PREFIX = "/docs-viewer/runtime/js/shared/"
DOCS_VIEWER_REPO_RUNTIME_PREFIX = "/docs-viewer/runtime/js/"
DOCS_VIEWER_REPO_CSS_PREFIX = "/docs-viewer/static/css/"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        if path.startswith(DOCS_VIEWER_SHARED_RUNTIME_PREFIX):
            relative_path = path.removeprefix(DOCS_VIEWER_SHARED_RUNTIME_PREFIX).split("?", 1)[0].split("#", 1)[0]
            return str(REPO_ROOT / "site/docs-viewer/runtime/js/shared" / relative_path)
        if path.startswith(DOCS_VIEWER_REPO_RUNTIME_PREFIX):
            relative_path = path.removeprefix(DOCS_VIEWER_REPO_RUNTIME_PREFIX).split("?", 1)[0].split("#", 1)[0]
            return str(REPO_ROOT / "docs-viewer/runtime/js" / relative_path)
        if path.startswith(DOCS_VIEWER_REPO_CSS_PREFIX):
            relative_path = path.removeprefix(DOCS_VIEWER_REPO_CSS_PREFIX).split("?", 1)[0].split("#", 1)[0]
            return str(REPO_ROOT / "docs-viewer/static/css" / relative_path)
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
            await cssLoaded.catch(() => null);

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
                      <label class="docsViewer__field docsViewer__field--checkbox" id="docsViewerSettingsBooleanField" hidden>
                        <input class="docsViewer__checkboxInput" id="docsViewerSettingsBooleanInput" type="checkbox">
                        <span class="docsViewer__fieldLabel" id="docsViewerSettingsBooleanLabel"></span>
                      </label>
                      <label class="docsViewer__field" id="docsViewerSettingsTextField" hidden>
                        <span class="docsViewer__fieldLabel" id="docsViewerSettingsTextLabel"></span>
                        <input class="docsViewer__fieldInput" id="docsViewerSettingsTextInput" type="text" autocomplete="off" spellcheck="false">
                      </label>
                      <p class="docsViewer__modalNote muted small" id="docsViewerSettingsDescription" hidden></p>
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
                settingsBooleanField: document.getElementById('docsViewerSettingsBooleanField'),
                settingsBooleanInput: document.getElementById('docsViewerSettingsBooleanInput'),
                settingsBooleanLabel: document.getElementById('docsViewerSettingsBooleanLabel'),
                settingsTextField: document.getElementById('docsViewerSettingsTextField'),
                settingsTextInput: document.getElementById('docsViewerSettingsTextInput'),
                settingsTextLabel: document.getElementById('docsViewerSettingsTextLabel'),
                settingsDescription: document.getElementById('docsViewerSettingsDescription'),
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

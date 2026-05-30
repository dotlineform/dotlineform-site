#!/usr/bin/env python3
"""Smoke-check the Tag Registry route-owned modals."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright


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


def install_modal_fixture(page) -> None:
    page.evaluate(
        """async () => {
            const css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = '/analytics/app/assets/css/analytics.css';
            const cssLoaded = new Promise((resolve, reject) => {
                css.addEventListener('load', resolve, { once: true });
                css.addEventListener('error', reject, { once: true });
            });
            document.head.appendChild(css);
            await cssLoaded;
            document.body.innerHTML = `
              <main class="tagRegistryPage">
                <button id="importOpener" type="button" data-role="open-import-modal">Import</button>
                <button id="newOpener" type="button">New</button>
                <button id="editOpener" type="button">Edit</button>
                <button id="demoteOpener" type="button">Demote</button>
                <button id="deleteOpener" type="button">Delete</button>
                <button id="patchOpener" type="button">Patch</button>
                <div data-role="modal-host"></div>
              </main>
            `;
            const module = await import('/analytics/app/frontend/js/tag-registry-modals.js');
            const host = document.querySelector('[data-role="modal-host"]');
            const state = {
                refs: {
                    openImportModal: document.querySelector('[data-role="open-import-modal"]')
                },
                config: {
                    ui_text: {
                        tag_registry: {
                            patch_modal_label: 'Manual patch snippet',
                            edit_description_label: 'description',
                            new_slug_label: 'tag',
                            new_description_label: 'description',
                            demote_search_label: 'find target tags',
                            demote_search_placeholder: 'search tags',
                            delete_impact_intro: 'Delete impact copy.'
                        }
                    }
                },
                studioGroups: ['subject', 'domain', 'form', 'theme'],
                groupInfoPagePath: '/analytics/tag-groups/',
                groupDescriptions: new Map([
                    ['subject', 'Subject group'],
                    ['domain', 'Domain group'],
                    ['form', 'Form group'],
                    ['theme', 'Theme group']
                ]),
                importAvailable: true,
                importModalOpen: false,
                selectedFile: null,
                patchSnippet: '',
                saveMode: 'post',
                newTagState: null,
                demoteState: null,
                deleteTagId: '',
                deletePreview: '',
                deletePreviewSeq: 0,
                refsHost: host
            };
            host.innerHTML = module.renderTagRegistryModals(state);
            state.refs = {
                ...state.refs,
                ...module.collectTagRegistryModalRefs(document)
            };
            window.__tagRegistryModalSmoke = {
                module,
                state,
                callbacks: {
                    importSubmit: 0,
                    editSave: 0,
                    createTag: 0,
                    demoteSubmit: 0,
                    deleteConfirm: 0,
                    patchCopy: 0,
                    modalStateChanges: 0
                }
            };
            module.wireTagRegistryModalEvents(state, {
                onModalStateChange: () => window.__tagRegistryModalSmoke.callbacks.modalStateChanges += 1,
                onImportSubmit: () => window.__tagRegistryModalSmoke.callbacks.importSubmit += 1,
                onPatchCopy: () => window.__tagRegistryModalSmoke.callbacks.patchCopy += 1,
                onEditSave: () => window.__tagRegistryModalSmoke.callbacks.editSave += 1,
                onCreateTag: () => window.__tagRegistryModalSmoke.callbacks.createTag += 1,
                onNewTagInput: () => {},
                onDemoteSearch: () => {},
                onDemoteSubmit: () => window.__tagRegistryModalSmoke.callbacks.demoteSubmit += 1,
                onDeleteConfirm: () => window.__tagRegistryModalSmoke.callbacks.deleteConfirm += 1
            });
        }"""
    )


def modal_state(page, role: str) -> dict[str, object]:
    return page.locator(f'[data-role="{role}"]').evaluate(
        """modal => {
            const dialog = modal.querySelector('[role="dialog"]');
            const title = modal.querySelector('.tagStudioModal__title');
            const actionButtons = Array.from(modal.querySelectorAll('.tagStudioModal__actions button'));
            const active = document.activeElement;
            return {
                hidden: modal.hidden,
                role: dialog ? dialog.getAttribute('role') : '',
                modal: dialog ? dialog.getAttribute('aria-modal') : '',
                labelledBy: dialog ? dialog.getAttribute('aria-labelledby') : '',
                titleId: title ? title.id : '',
                title: title ? title.textContent.trim() : '',
                dialogClass: dialog ? dialog.className : '',
                actionLabels: actionButtons.map(button => button.textContent.trim()),
                actionRoles: actionButtons.map(button => button.dataset.role || ''),
                actionClasses: actionButtons.map(button => button.className),
                activeRole: active ? active.dataset.role || '' : '',
                activeId: active ? active.id || '' : '',
                bodyText: modal.textContent || ''
            };
        }"""
    )


def assert_shell(
    page,
    role: str,
    title: str,
    actions: list[str],
    action_roles: list[str],
    active_role: str,
    size_class: str | None = None,
) -> dict[str, object]:
    state = modal_state(page, role)
    if state["hidden"]:
        raise AssertionError(f"modal should be visible: {state!r}")
    if state["role"] != "dialog" or state["modal"] != "true":
        raise AssertionError(f"modal lacks dialog semantics: {state!r}")
    if not state["labelledBy"] or state["labelledBy"] != state["titleId"]:
        raise AssertionError(f"modal is not labelled by its title: {state!r}")
    if state["title"] != title:
        raise AssertionError(f"unexpected modal title: {state!r}")
    if size_class and size_class not in state["dialogClass"]:
        raise AssertionError(f"modal size mismatch: {state!r}")
    if state["actionLabels"] != actions or state["actionRoles"] != action_roles:
        raise AssertionError(f"unexpected modal actions: {state!r}")
    if not all("tagStudio__button--defaultWidth" in value for value in state["actionClasses"]):
        raise AssertionError(f"modal action buttons are missing default-width class: {state!r}")
    if active_role and state["activeRole"] != active_role:
        raise AssertionError(f"modal focus did not enter expected control: {state!r}")
    return state


def assert_focus_return(page, role: str, opener_id: str) -> None:
    state = page.locator(f'[data-role="{role}"]').evaluate(
        """(modal, openerId) => ({
            hidden: modal.hidden,
            focusedId: document.activeElement ? document.activeElement.id || '' : '',
            expected: openerId
        })""",
        opener_id,
    )
    if state != {"hidden": True, "focusedId": opener_id, "expected": opener_id}:
        raise AssertionError(f"modal did not close and return focus: {state!r}")


def focus_wrap_role(page, selector: str, key: str) -> str:
    page.locator(selector).focus()
    page.keyboard.press(key)
    return page.evaluate("document.activeElement ? document.activeElement.dataset.role || '' : ''")


def open_direct_modal(page, opener_id: str, expression: str) -> None:
    page.evaluate(
        """([openerId, expression]) => {
            const smoke = window.__tagRegistryModalSmoke;
            const opener = document.querySelector(`#${openerId}`);
            opener.focus();
            Function('smoke', expression)(smoke);
        }""",
        [opener_id, expression],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--site-root", help="Serve a site or repository root on a temporary local HTTP server.")
    args = parser.parse_args()

    server = None
    base_url = args.base_url
    if args.site_root:
        server, base_url = start_static_server(Path(args.site_root))

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(route_url(base_url, "/"), wait_until="domcontentloaded")
            install_modal_fixture(page)

            page.locator("#importOpener").focus()
            page.locator("#importOpener").click()
            import_state = assert_shell(
                page,
                "import-modal",
                "Import Registry",
                ["Close"],
                ["close-import-modal"],
                "choose-file",
                "tagStudioModal__dialog--wide",
            )
            page.locator('[data-role="import-btn"]').click()
            if focus_wrap_role(page, '[data-role="choose-file"]', "Shift+Tab") != "close-import-modal":
                raise AssertionError("import modal did not wrap focus backward to Close")
            page.locator('[data-role="import-modal"] .tagStudioModal__backdrop').click(position={"x": 4, "y": 4})
            assert_focus_return(page, "import-modal", "importOpener")

            open_direct_modal(page, "newOpener", "smoke.module.openTagRegistryNewModal(smoke.state);")
            new_state = assert_shell(
                page,
                "new-modal",
                "New Tag",
                ["Cancel", "Create"],
                ["close-new-modal", "create-tag"],
                "new-tag-slug",
            )
            if focus_wrap_role(page, 'button[data-new-group="subject"]', "Shift+Tab") != "close-new-modal":
                raise AssertionError("new modal did not wrap focus backward to Cancel")
            page.keyboard.press("Escape")
            assert_focus_return(page, "new-modal", "newOpener")

            open_direct_modal(
                page,
                "editOpener",
                "smoke.module.openTagRegistryEditModal(smoke.state, { tagId: 'subject:smoke', group: 'subject', description: 'Old copy' });",
            )
            edit_state = assert_shell(
                page,
                "edit-modal",
                "Edit Tag",
                ["Close", "Save"],
                ["close-edit-modal", "save-edit"],
                "edit-description",
            )
            page.locator('[data-role="save-edit"]').click()
            page.locator('button[data-role="close-edit-modal"]').click()
            assert_focus_return(page, "edit-modal", "editOpener")

            open_direct_modal(
                page,
                "demoteOpener",
                "smoke.module.openTagRegistryDemoteModal(smoke.state, { tag: { tagId: 'subject:smoke', group: 'subject' }, aliasKey: 'smoke' }); smoke.module.renderTagRegistryDemoteSelectionState(smoke.state, { selectedItems: [{ tagId: 'domain:target', group: 'domain', label: 'target' }], canConfirm: true, statusKind: '', statusMessage: '' });",
            )
            demote_state = assert_shell(
                page,
                "demote-modal",
                "Demote Tag to Alias",
                ["Close", "Demote"],
                ["close-demote-modal", "confirm-demote"],
                "demote-tag-search",
            )
            page.locator('[data-role="confirm-demote"]').click()
            page.keyboard.press("Escape")
            assert_focus_return(page, "demote-modal", "demoteOpener")

            open_direct_modal(
                page,
                "deleteOpener",
                "smoke.module.openTagRegistryDeleteModal(smoke.state, { tagId: 'subject:smoke', group: 'subject', label: 'smoke' });",
            )
            delete_state = assert_shell(
                page,
                "delete-modal",
                "Delete Tag",
                ["Cancel", "Delete"],
                ["close-delete-modal", "confirm-delete-tag"],
                "confirm-delete-tag",
            )
            page.locator('[data-role="confirm-delete-tag"]').click()
            page.locator('button[data-role="close-delete-modal"]').click()
            assert_focus_return(page, "delete-modal", "deleteOpener")

            open_direct_modal(
                page,
                "patchOpener",
                "smoke.module.showTagRegistryPatchModal(smoke.state, 'diff --git a/studio/data/canonical/analytics/tag-registry.json b/studio/data/canonical/analytics/tag-registry.json');",
            )
            patch_state = assert_shell(
                page,
                "patch-modal",
                "Registry Patch Preview",
                ["Close", "Copy"],
                ["close-patch-modal", "copy-patch"],
                "copy-patch",
                "tagStudioModal__dialog--wide",
            )
            if "diff --git" not in patch_state["bodyText"]:
                raise AssertionError(f"patch snippet did not render: {patch_state!r}")
            page.locator('[data-role="copy-patch"]').click()
            page.keyboard.press("Escape")
            assert_focus_return(page, "patch-modal", "patchOpener")

            callbacks = page.evaluate("window.__tagRegistryModalSmoke.callbacks")
            expected_callbacks = {
                "importSubmit": 1,
                "editSave": 1,
                "createTag": 0,
                "demoteSubmit": 1,
                "deleteConfirm": 1,
                "patchCopy": 1,
            }
            if {key: callbacks[key] for key in expected_callbacks} != expected_callbacks or callbacks["modalStateChanges"] < 3:
                raise AssertionError(f"modal route callbacks changed unexpectedly: {callbacks!r}")

            print(json.dumps({
                "import": import_state,
                "new": new_state,
                "edit": edit_state,
                "demote": demote_state,
                "delete": delete_state,
                "patch": patch_state,
                "callbacks": callbacks,
            }, sort_keys=True))
        finally:
            browser.close()
            if server is not None:
                server.shutdown()
                server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

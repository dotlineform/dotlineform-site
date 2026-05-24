#!/usr/bin/env python3
"""Smoke-check the Series Tags session and import modals."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


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


def install_modal_fixture(page) -> None:
    page.evaluate(
        """async () => {
            const css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = '/studio/app/assets/css/studio.css';
            const cssLoaded = new Promise((resolve, reject) => {
                css.addEventListener('load', resolve, { once: true });
                css.addEventListener('error', reject, { once: true });
            });
            document.head.appendChild(css);
            await cssLoaded;
            document.body.innerHTML = `
              <main class="seriesTagsPage">
                <button id="sessionOpener" type="button">Session</button>
                <button id="importOpener" type="button">Import</button>
                <div data-role="series-tags-session-modal-host"></div>
                <div data-role="series-tags-import-modal-host"></div>
              </main>
            `;
            const module = await import('/studio/app/frontend/js/series-tags-modals.js');
            const sessionModalHost = document.querySelector('[data-role="series-tags-session-modal-host"]');
            const importModalHost = document.querySelector('[data-role="series-tags-import-modal-host"]');
            const state = {
                refs: { sessionModalHost, importModalHost },
                config: {
                    ui_text: {
                        series_tags: {
                            session_import_status_apply: 'Ready to apply.',
                            session_import_status_conflict: 'Conflict with current repo row.'
                        }
                    }
                },
                offlineSession: {
                    version: 'tag_assignments_offline_v1',
                    updated_at_utc: '2026-05-15T10:00:00Z',
                    series: {
                        smoke: {
                            base_series_updated_at_utc: '',
                            base_row_snapshot: { tags: [] },
                            staged_row: { tags: [{ tag_id: 'subject:smoke', w_manual: 1 }] },
                            staged_at_utc: '2026-05-15T10:00:00Z'
                        }
                    }
                },
                importFile: { name: 'series-tags-import.json' },
                importPayload: { series: {} },
                importPreview: {
                    applicable_count: 1,
                    conflict_count: 1,
                    series: [
                        { series_id: 'smoke', status: 'apply', invalid_work_ids: [] },
                        { series_id: 'conflict', status: 'conflict', invalid_work_ids: [] }
                    ]
                },
                importResolutions: { conflict: 'skip' },
                sessionModalOpen: false,
                importModalOpen: false,
                resultKind: 'success',
                resultText: 'Import preview ready.'
            };
            window.__seriesTagsModalSmoke = {
                state,
                module,
                sessionActions: [],
                importActions: [],
                resolutionChanges: [],
                renders: 0
            };
            const rerender = () => {
                module.renderSessionModal(state);
                module.renderImportModal(state);
                window.__seriesTagsModalSmoke.renders += 1;
            };
            module.wireSeriesTagsModalEvents(state, {
                onModalStateChange: rerender,
                onSessionAction: action => window.__seriesTagsModalSmoke.sessionActions.push(action),
                onImportAction: action => window.__seriesTagsModalSmoke.importActions.push(action),
                onImportResolutionChange: (seriesId, value) => {
                    state.importResolutions[seriesId] = value;
                    window.__seriesTagsModalSmoke.resolutionChanges.push([seriesId, value]);
                }
            });
            rerender();
        }"""
    )


def open_session_modal(page) -> None:
    page.evaluate(
        """() => {
            const smoke = window.__seriesTagsModalSmoke;
            const opener = document.querySelector('#sessionOpener');
            opener.focus();
            smoke.state.sessionModalRestoreFocus = opener;
            smoke.state.sessionModalFocusReady = false;
            smoke.state.sessionModalOpen = true;
            smoke.state.importModalOpen = false;
            smoke.module.renderSessionModal(smoke.state);
        }"""
    )


def open_import_modal(page) -> None:
    page.evaluate(
        """() => {
            const smoke = window.__seriesTagsModalSmoke;
            const opener = document.querySelector('#importOpener');
            opener.focus();
            smoke.state.importModalRestoreFocus = opener;
            smoke.state.importModalFocusReady = false;
            smoke.state.importModalOpen = true;
            smoke.state.sessionModalOpen = false;
            smoke.module.renderImportModal(smoke.state);
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
                role: dialog ? dialog.getAttribute('role') : "",
                modal: dialog ? dialog.getAttribute('aria-modal') : "",
                labelledBy: dialog ? dialog.getAttribute('aria-labelledby') : "",
                titleId: title ? title.id : "",
                title: title ? title.textContent.trim() : "",
                dialogClass: dialog ? dialog.className : "",
                actionLabels: actionButtons.map(button => button.textContent.trim()),
                actionRoles: actionButtons.map(button => button.dataset.role || ""),
                actionClasses: actionButtons.map(button => button.className),
                activeRole: active ? active.dataset.role || "" : "",
                activeSessionAction: active ? active.dataset.sessionAction || "" : "",
                activeImportAction: active ? active.dataset.importAction || "" : "",
                statusRole: modal.querySelector('.tagStudioModal__status')?.dataset.role || "",
                statusText: modal.querySelector('.tagStudioModal__status')?.textContent.trim() || "",
                bodyText: modal.textContent || ""
            };
        }"""
    )


def assert_shell_basics(state: dict[str, object], title: str) -> None:
    if state["hidden"]:
        raise AssertionError(f"modal should be visible: {state!r}")
    if state["role"] != "dialog" or state["modal"] != "true":
        raise AssertionError(f"modal lacks dialog semantics: {state!r}")
    if not state["labelledBy"] or state["labelledBy"] != state["titleId"]:
        raise AssertionError(f"modal is not labelled by its title: {state!r}")
    if state["title"] != title:
        raise AssertionError(f"unexpected modal title: {state!r}")
    if not all("tagStudio__button--defaultWidth" in value for value in state["actionClasses"]):
        raise AssertionError(f"modal action row is missing default-width buttons: {state!r}")


def assert_focus_return(page, modal_role: str, opener_id: str) -> None:
    state = page.locator(f'[data-role="{modal_role}"]').evaluate(
        """(modal, openerId) => ({
            hidden: modal.hidden,
            focusedId: document.activeElement ? document.activeElement.id || "" : "",
            expected: openerId
        })""",
        opener_id,
    )
    if state != {"hidden": True, "focusedId": opener_id, "expected": opener_id}:
        raise AssertionError(f"modal did not close and return focus: {state!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--site-root", help="Serve a site or repository root on a temporary local HTTP server.")
    parser.add_argument("--timeout-ms", type=int, default=15000)
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

            open_session_modal(page)
            session_state = modal_state(page, "series-tags-session-modal")
            assert_shell_basics(session_state, "Offline session")
            if "tagStudioModal__dialog--compact" not in session_state["dialogClass"]:
                raise AssertionError(f"session modal is not compact: {session_state!r}")
            if session_state["actionLabels"] != ["Close"] or session_state["actionRoles"] != ["close-session-modal"]:
                raise AssertionError(f"unexpected session modal actions: {session_state!r}")
            if session_state["activeSessionAction"] != "copy":
                raise AssertionError(f"session modal did not focus the first workflow action: {session_state!r}")
            if session_state["statusRole"] != "series-tags-session-result" or session_state["statusText"] != "Import preview ready.":
                raise AssertionError(f"session modal status slot is wrong: {session_state!r}")

            page.locator('button[data-session-action="copy"]').click()
            page.locator('button[data-session-action="download"]').click()
            session_actions = page.evaluate("window.__seriesTagsModalSmoke.sessionActions")
            if session_actions != ["copy", "download"]:
                raise AssertionError(f"session actions should stay route-owned callbacks: {session_actions!r}")

            page.locator('button[data-session-action="copy"]').focus()
            page.keyboard.press("Shift+Tab")
            focused_after_wrap = page.evaluate("document.activeElement ? document.activeElement.dataset.role || '' : ''")
            if focused_after_wrap != "close-session-modal":
                raise AssertionError(f"session modal did not wrap focus backward: {focused_after_wrap!r}")
            page.locator('[data-role="close-session-modal"]').last.focus()
            page.keyboard.press("Tab")
            focused_after_forward_wrap = page.evaluate("document.activeElement ? document.activeElement.dataset.sessionAction || '' : ''")
            if focused_after_forward_wrap != "copy":
                raise AssertionError(f"session modal did not wrap focus forward: {focused_after_forward_wrap!r}")

            page.keyboard.press("Escape")
            assert_focus_return(page, "series-tags-session-modal", "sessionOpener")

            open_import_modal(page)
            import_state = modal_state(page, "series-tags-import-modal")
            assert_shell_basics(import_state, "Import assignments")
            if "tagStudioModal__dialog--wide" not in import_state["dialogClass"]:
                raise AssertionError(f"import modal is not wide: {import_state!r}")
            if import_state["actionLabels"] != ["Close", "Apply import"] or import_state["actionRoles"] != ["close-import-modal", "apply-import"]:
                raise AssertionError(f"unexpected import modal actions: {import_state!r}")
            if "tagStudio__button--defaultAction" not in import_state["actionClasses"][1]:
                raise AssertionError(f"import apply action is not primary: {import_state!r}")
            if import_state["activeImportAction"] != "choose-file":
                raise AssertionError(f"import modal did not focus the file command: {import_state!r}")
            if import_state["statusRole"] != "series-tags-import-result" or import_state["statusText"] != "Import preview ready.":
                raise AssertionError(f"import modal status slot is wrong: {import_state!r}")
            if "Conflict with current repo row." not in import_state["bodyText"]:
                raise AssertionError(f"import review rows did not render: {import_state!r}")

            page.locator('button[data-import-action="preview-import"]').click()
            page.locator('[data-role="apply-import"]').click()
            page.locator('select[data-import-resolution="conflict"]').select_option("overwrite")
            callback_state = page.evaluate(
                """() => ({
                    importActions: window.__seriesTagsModalSmoke.importActions,
                    resolutionChanges: window.__seriesTagsModalSmoke.resolutionChanges
                })"""
            )
            if callback_state != {
                "importActions": ["preview-import", "apply-import"],
                "resolutionChanges": [["conflict", "overwrite"]],
            }:
                raise AssertionError(f"import controls should return through route callbacks: {callback_state!r}")

            page.locator('button[data-import-action="choose-file"]').focus()
            page.keyboard.press("Shift+Tab")
            import_wrap = page.evaluate("document.activeElement ? document.activeElement.dataset.role || '' : ''")
            if import_wrap != "apply-import":
                raise AssertionError(f"import modal did not wrap focus backward: {import_wrap!r}")

            page.locator(".tagStudioModal__backdrop").last.click(position={"x": 4, "y": 4})
            assert_focus_return(page, "series-tags-import-modal", "importOpener")

            print(json.dumps({"session": session_state, "import": import_state, "callbacks": callback_state}, sort_keys=True))
        finally:
            browser.close()
            if server is not None:
                server.shutdown()
                server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

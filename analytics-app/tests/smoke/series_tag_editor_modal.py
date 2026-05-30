#!/usr/bin/env python3
"""Smoke-check the Series Tag Editor save-preview modal helper."""

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


def assert_modal_state(page, expected_focus: str) -> dict[str, object]:
    state = page.locator('[data-role="analytics-modal"]').evaluate(
        """modal => {
            const dialog = modal.querySelector('[role="dialog"]');
            const title = modal.querySelector('.analyticsModal__title');
            const actionButtons = Array.from(modal.querySelectorAll('.analyticsModal__actions button'));
            const active = document.activeElement;
            return {
                hidden: modal.hidden,
                role: dialog ? dialog.getAttribute('role') : "",
                modal: dialog ? dialog.getAttribute('aria-modal') : "",
                labelledBy: dialog ? dialog.getAttribute('aria-labelledby') : "",
                titleId: title ? title.id : "",
                title: title ? title.textContent.trim() : "",
                actionLabels: actionButtons.map((button) => button.textContent.trim()),
                actionRoles: actionButtons.map((button) => button.dataset.role || ""),
                defaultWidthActions: actionButtons.every((button) => button.classList.contains('analytics__button--defaultWidth')),
                activeRole: active ? active.dataset.role || "" : "",
                tagsText: modal.querySelector('[data-role="modal-tags"]')?.textContent || "",
                snippetText: modal.querySelector('[data-role="modal-snippet"]')?.textContent || ""
            };
        }"""
    )
    if state["hidden"]:
        raise AssertionError(f"modal should be visible: {state!r}")
    if state["role"] != "dialog" or state["modal"] != "true":
        raise AssertionError(f"modal lacks dialog semantics: {state!r}")
    if not state["labelledBy"] or state["labelledBy"] != state["titleId"]:
        raise AssertionError(f"modal is not labelled by its title: {state!r}")
    if state["title"] != "Tag Assignment Patch Preview":
        raise AssertionError(f"unexpected modal title: {state!r}")
    if state["actionLabels"] != ["Close", "Copy"] or state["actionRoles"] != ["modal-cancel", "copy-snippet"]:
        raise AssertionError(f"unexpected modal actions: {state!r}")
    if not state["defaultWidthActions"]:
        raise AssertionError(f"modal actions are missing default-width buttons: {state!r}")
    if state["activeRole"] != expected_focus:
        raise AssertionError(f"modal focus did not enter expected action: {state!r}")
    if '"series_tags"' not in state["tagsText"] or "subject:smoke" not in state["tagsText"]:
        raise AssertionError(f"resolved payload missing from modal: {state!r}")
    if "Update series" not in state["snippetText"]:
        raise AssertionError(f"patch guidance missing from modal: {state!r}")
    return state


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
              <main class="analyticsPage">
                <button id="opener" type="button" data-role="save">Save</button>
                <section id="analytics-tag-editor" class="analyticsTagEditor" data-role="series-tag-editor">
                  <p class="analytics__status" data-role="status"></p>
                  <div data-role="modal-host"></div>
                </section>
              </main>
            `;
            const module = await import('/analytics/app/frontend/js/analytics-tag-editor-modals.js');
            const mount = document.querySelector('#analytics-tag-editor');
            const state = {
                config: { ui_text: { series_tag_editor: {} } },
                mount,
                seriesId: 'smoke-series',
                refs: {
                    status: mount.querySelector('[data-role="status"]'),
                    modalHost: mount.querySelector('[data-role="modal-host"]')
                },
                modalSnippet: ''
            };
            state.refs.modalHost.innerHTML = module.renderAnalyticsTagEditorSaveModal(state);
            state.refs = {
                ...state.refs,
                ...module.collectAnalyticsTagEditorSaveModalRefs(mount)
            };
            window.__seriesTagEditorSmoke = { state, module, copyCount: 0 };
            module.wireAnalyticsTagEditorSaveModalEvents(state, {
                onCopySnippet: () => {
                    window.__seriesTagEditorSmoke.copyCount += 1;
                    state.refs.status.textContent = 'copy callback ran';
                }
            });
        }"""
    )


def open_modal(page) -> None:
    page.evaluate(
        """() => {
            const smoke = window.__seriesTagEditorSmoke;
            document.querySelector('#opener').focus();
            smoke.module.openAnalyticsTagEditorSaveModal(smoke.state, {
                seriesChanged: true,
                changedWorkIds: ['00001'],
                nextSeriesRows: [{ tag_id: 'subject:smoke', w_manual: 0.6 }],
                nextWorkStateById: new Map([
                    ['00001', [{ tag_id: 'domain:test', w_manual: 0.9 }]]
                ])
            });
        }"""
    )


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
            open_modal(page)
            modal = assert_modal_state(page, "modal-cancel")

            page.keyboard.press("Tab")
            focused_after_tab = page.evaluate("document.activeElement ? document.activeElement.dataset.role || '' : ''")
            if focused_after_tab != "copy-snippet":
                raise AssertionError(f"modal did not advance focus to Copy: {focused_after_tab!r}")
            page.keyboard.press("Tab")
            focused_after_wrap = page.evaluate("document.activeElement ? document.activeElement.dataset.role || '' : ''")
            if focused_after_wrap != "modal-cancel":
                raise AssertionError(f"modal did not wrap focus to Close: {focused_after_wrap!r}")

            page.locator('[data-role="copy-snippet"]').click()
            copy_state = page.evaluate(
                """() => ({
                    copyCount: window.__seriesTagEditorSmoke.copyCount,
                    status: window.__seriesTagEditorSmoke.state.refs.status.textContent
                })"""
            )
            if copy_state != {"copyCount": 1, "status": "copy callback ran"}:
                raise AssertionError(f"copy callback should stay route-owned: {copy_state!r}")

            page.keyboard.press("Escape")
            close_state = page.evaluate(
                """() => ({
                    hidden: window.__seriesTagEditorSmoke.state.refs.modal.hidden,
                    focusedId: document.activeElement ? document.activeElement.id || "" : ""
                })"""
            )
            if close_state != {"hidden": True, "focusedId": "opener"}:
                raise AssertionError(f"modal did not close and return focus after Escape: {close_state!r}")

            open_modal(page)
            assert_modal_state(page, "modal-cancel")
            page.locator('.analyticsModal__actions [data-role="modal-cancel"]').click()
            cancel_state = page.evaluate(
                """() => ({
                    hidden: window.__seriesTagEditorSmoke.state.refs.modal.hidden,
                    focusedId: document.activeElement ? document.activeElement.id || "" : ""
                })"""
            )
            if cancel_state != {"hidden": True, "focusedId": "opener"}:
                raise AssertionError(f"modal did not close and return focus after action close: {cancel_state!r}")

            open_modal(page)
            assert_modal_state(page, "modal-cancel")
            page.locator(".analyticsModal__backdrop").click(position={"x": 4, "y": 4})
            backdrop_state = page.evaluate(
                """() => ({
                    hidden: window.__seriesTagEditorSmoke.state.refs.modal.hidden,
                    focusedId: document.activeElement ? document.activeElement.id || "" : ""
                })"""
            )
            if backdrop_state != {"hidden": True, "focusedId": "opener"}:
                raise AssertionError(f"modal did not close and return focus after backdrop: {backdrop_state!r}")

            print(json.dumps({"modal": modal, "copy": copy_state}, sort_keys=True))
        finally:
            browser.close()
            if server is not None:
                server.shutdown()
                server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

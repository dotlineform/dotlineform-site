#!/usr/bin/env python3
"""Smoke-check shared Docs Viewer modal keyboard focus behavior."""

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
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_shared_focus_trap(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const modalModule = await import('/docs-viewer/runtime/js/management/docs-viewer-management-modal-shell.js');
          document.documentElement.setAttribute('data-theme', 'dark');
          for (const href of [
            '/site/docs-viewer/static/css/docs-viewer-theme.css',
            '/site/docs-viewer/static/css/docs-viewer.css',
            '/docs-viewer/static/css/docs-viewer-manage.css'
          ]) {
            await new Promise((resolve, reject) => {
              const stylesheet = document.createElement('link');
              stylesheet.rel = 'stylesheet';
              stylesheet.href = href;
              stylesheet.addEventListener('load', resolve, { once: true });
              stylesheet.addEventListener('error', reject, { once: true });
              document.head.appendChild(stylesheet);
            });
          }
          document.body.innerHTML = `
            <button id="outside">Outside</button>
            <div class="docsViewer__modal" id="modal">
              <select id="scope"><option>studio</option></select>
              <select id="file" size="10"><option>one.md</option></select>
              <button id="cancel">Cancel</button>
              <button id="run">Import</button>
            </div>`;
          const modal = document.querySelector('#modal');

          function pressTab(shiftKey = false) {
            const event = new KeyboardEvent('keydown', {
              key: 'Tab',
              shiftKey,
              bubbles: true,
              cancelable: true
            });
            const trapped = modalModule.trapDocsViewerModalFocus(event, modal);
            return {
              trapped,
              prevented: event.defaultPrevented,
              activeId: document.activeElement && document.activeElement.id
            };
          }

          document.querySelector('#scope').focus();
          const internalForward = pressTab();
          document.querySelector('#run').focus();
          const wrapForward = pressTab();
          const wrapBackward = pressTab(true);
          document.querySelector('#outside').focus();
          const recoverOutside = pressTab();
          return { internalForward, wrapForward, wrapBackward, recoverOutside };
        }"""
    )
    expected = {
        "internalForward": {
            "trapped": True,
            "prevented": True,
            "activeId": "file",
        },
        "wrapForward": {
            "trapped": True,
            "prevented": True,
            "activeId": "scope",
        },
        "wrapBackward": {
            "trapped": True,
            "prevented": True,
            "activeId": "run",
        },
        "recoverOutside": {
            "trapped": True,
            "prevented": True,
            "activeId": "scope",
        },
    }
    if result != expected:
        raise AssertionError(f"unexpected shared modal focus traversal: {result!r}")


def assert_choice_modal_radio_navigation(page: Page) -> None:
    page.evaluate(
        """async () => {
          const modalModule = await import('/docs-viewer/runtime/js/management/docs-viewer-management-modal-shell.js');
          document.body.innerHTML = `
            <main class="docsViewer" id="root">
              <button id="open">Open</button>
              <div style="height: 2000px"></div>
            </main>`;
          window.scrollTo(0, 400);
          document.querySelector('#open').addEventListener('click', () => {
            window.choiceModalResult = modalModule.openDocsViewerChoiceModal({
              root: document.querySelector('#root'),
              title: 'Choose scope',
              value: 'analysis',
              choices: [
                { value: 'analysis', label: 'analysis' },
                { value: 'library', label: 'library' },
                { value: 'moments', label: 'moments' }
              ],
              primaryLabel: 'Preview copy',
              cancelLabel: 'Cancel'
            });
          });
        }"""
    )
    page.locator("#open").click()
    page.wait_for_function("document.activeElement?.value === 'analysis'")
    page.evaluate("window.scrollTo(0, 400)")

    def state() -> dict[str, object]:
        return page.evaluate(
            """() => {
              const active = document.activeElement;
              const focusStyle = getComputedStyle(active);
              return {
                active: active?.value || active?.dataset?.role || active?.textContent || '',
                checked: document.querySelector('input[type="radio"]:checked')?.value || '',
                scrollY: window.scrollY,
                outlineStyle: focusStyle.outlineStyle,
                outlineWidth: focusStyle.outlineWidth
              };
            }"""
        )

    opened = state()
    page.keyboard.press("Tab")
    tab_to_primary = state()
    page.keyboard.press("Shift+Tab")
    shift_tab_to_group = state()
    page.keyboard.press("ArrowDown")
    down_to_library = state()
    page.keyboard.press("ArrowDown")
    down_to_moments = state()
    page.keyboard.press("ArrowDown")
    down_wraps = state()
    page.keyboard.press("ArrowUp")
    up_wraps = state()
    page.keyboard.press("Escape")

    result = {
        "opened": opened,
        "tabToPrimary": tab_to_primary,
        "shiftTabToGroup": shift_tab_to_group,
        "downToLibrary": down_to_library,
        "downToMoments": down_to_moments,
        "downWraps": down_wraps,
        "upWraps": up_wraps,
    }
    expected = {
        "opened": {
            "active": "analysis",
            "checked": "analysis",
            "scrollY": 400,
            "outlineStyle": "none",
            "outlineWidth": "0px",
        },
        "tabToPrimary": {
            "active": "modal-primary",
            "checked": "analysis",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
        "shiftTabToGroup": {
            "active": "analysis",
            "checked": "analysis",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
        "downToLibrary": {
            "active": "library",
            "checked": "library",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
        "downToMoments": {
            "active": "moments",
            "checked": "moments",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
        "downWraps": {
            "active": "analysis",
            "checked": "analysis",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
        "upWraps": {
            "active": "moments",
            "checked": "moments",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
    }
    if result != expected:
        raise AssertionError(f"unexpected choice modal radio navigation: {result!r}")


def assert_review_sessions_modal(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const sessionsModule = await import('/docs-viewer/runtime/js/management/docs-viewer-review-sessions-modal.js');
          document.body.innerHTML = `
            <main class="docsViewer">
              <button id="outside">Outside</button>
              <div id="mount"></div>
            </main>`;
          const outside = document.querySelector('#outside');
          const mount = document.querySelector('#mount');
          let closeCount = 0;
          let sessionsModal;
          sessionsModal = sessionsModule.createDocsViewerReviewSessionsModal({
            document,
            mount,
            callbacks: {
              onClose() {
                closeCount += 1;
                sessionsModal.close();
              }
            }
          });

          outside.focus();
          sessionsModal.open();
          await new Promise(resolve => setTimeout(resolve, 0));
          const focusedOnOpen = document.activeElement?.textContent || '';

          document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Tab',
            bubbles: true,
            cancelable: true
          }));
          const focusedAfterTab = document.activeElement?.textContent || '';

          document.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Escape',
            bubbles: true,
            cancelable: true
          }));
          await new Promise(resolve => setTimeout(resolve, 0));
          return {
            closeCount,
            focusedOnOpen,
            focusedAfterTab,
            focusReturnedTo: document.activeElement?.id || '',
            hidden: mount.querySelector('.docsViewer__modal')?.hidden
          };
        }"""
    )
    expected = {
        "closeCount": 1,
        "focusedOnOpen": "Cancel",
        "focusedAfterTab": "Cancel",
        "focusReturnedTo": "outside",
        "hidden": True,
    }
    if result != expected:
        raise AssertionError(f"unexpected review sessions modal focus behavior: {result!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", default=".", help="Repository root to serve.")
    args = parser.parse_args(argv)
    server, base_url = start_static_server(Path(args.site_root))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            errors: list[str] = []
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.goto(base_url, wait_until="domcontentloaded")
                assert_shared_focus_trap(page)
                assert_choice_modal_radio_navigation(page)
                assert_review_sessions_modal(page)
            finally:
                browser.close()
            if errors:
                raise AssertionError(f"page errors: {errors}")
    finally:
        server.shutdown()
        server.server_close()
    print("Docs Viewer modal focus modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

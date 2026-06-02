#!/usr/bin/env python3
"""Smoke-check standalone UI Catalogue demo routes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
SERVER_DIR = REPO_ROOT / "ui-catalogue-app" / "app" / "server" / "ui_catalogue_app"
sys.path.insert(0, str(SERVER_DIR))

from ui_catalogue_app_server import UiCatalogueAppServer  # noqa: E402


ROUTES = [
    {
        "view_id": "ui_catalogue_demos",
        "path": "/ui-catalogue/demos/",
        "root": "#uiCatalogueDemoIndexRoot",
    },
    {
        "view_id": "ui_catalogue_demo_button",
        "path": "/ui-catalogue/demos/primitives/button/",
        "root": "#uiCatalogueDemoButtonRoot",
    },
    {
        "view_id": "ui_catalogue_demo_input",
        "path": "/ui-catalogue/demos/primitives/input/",
        "root": "#uiCatalogueDemoInputRoot",
    },
    {
        "view_id": "ui_catalogue_demo_list",
        "path": "/ui-catalogue/demos/primitives/list/",
        "root": "#uiCatalogueDemoListRoot",
    },
    {
        "view_id": "ui_catalogue_demo_modal_shell",
        "path": "/ui-catalogue/demos/primitives/modal-shell/",
        "root": "#uiCatalogueDemoModalShellRoot",
    },
    {
        "view_id": "ui_catalogue_demo_panel",
        "path": "/ui-catalogue/demos/primitives/panel/",
        "root": "#uiCatalogueDemoPanelRoot",
    },
    {
        "view_id": "ui_catalogue_demo_action_menu",
        "path": "/ui-catalogue/demos/patterns/action-menu/",
        "root": "#uiCatalogueDemoActionMenuRoot",
    },
    {
        "view_id": "ui_catalogue_demo_reopenable_command_result",
        "path": "/ui-catalogue/demos/patterns/reopenable-command-result/",
        "root": "#uiCatalogueDemoReopenableCommandResultRoot",
    },
    {
        "view_id": "ui_catalogue_demo_select_menu",
        "path": "/ui-catalogue/demos/patterns/select-menu/",
        "root": "#uiCatalogueDemoSelectMenuRoot",
    },
    {
        "view_id": "ui_catalogue_demo_column_links",
        "path": "/ui-catalogue/demos/patterns/column-links/",
        "root": "#uiCatalogueDemoColumnLinksRoot",
    },
]


def start_server() -> tuple[UiCatalogueAppServer, str]:
    server = UiCatalogueAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def wait_for_demo_ready(page: Page, root_selector: str) -> None:
    page.wait_for_selector(root_selector, timeout=10_000)
    page.wait_for_function(
        """selector => {
            const root = document.querySelector(selector);
            return root
                && root.dataset.uiCatalogueDemoReady === 'true'
                && root.dataset.uiCatalogueDemoBusy === 'false';
        }""",
        arg=root_selector,
        timeout=10_000,
    )


def check_modal_shell(page: Page, base_url: str, viewport: dict[str, int]) -> dict[str, object]:
    page.set_viewport_size(viewport)
    page.goto(f"{base_url}/ui-catalogue/demos/primitives/modal-shell/", wait_until="domcontentloaded")
    wait_for_demo_ready(page, "#uiCatalogueDemoModalShellRoot")
    opener = page.locator('[data-ui-demo-modal-open="uiCatalogueDemoConfirmModal"]')
    opener.scroll_into_view_if_needed()
    opener.click()
    page.wait_for_selector("#uiCatalogueDemoConfirmModal[data-open='true']", timeout=10_000)
    state = page.locator("#uiCatalogueDemoConfirmModal").evaluate(
        """modal => {
            const dialog = modal.querySelector('[role="dialog"]');
            const title = modal.querySelector('.uiCatalogueDemoModal__title');
            const actions = Array.from(modal.querySelectorAll('.uiCatalogueDemoModal__actions button'));
            const rect = dialog ? dialog.getBoundingClientRect() : null;
            return {
                hidden: modal.hidden,
                open: modal.dataset.open || '',
                ariaHidden: modal.getAttribute('aria-hidden') || '',
                role: dialog ? dialog.getAttribute('role') : '',
                modal: dialog ? dialog.getAttribute('aria-modal') : '',
                title: title ? title.textContent.trim() : '',
                actionLabels: actions.map(button => button.textContent.trim()),
                activeText: document.activeElement ? document.activeElement.textContent.trim() : '',
                dialogWidth: rect ? Math.round(rect.width) : 0,
                viewportWidth: window.innerWidth
            };
        }"""
    )
    if state["hidden"] or state["open"] != "true" or state["ariaHidden"] != "false":
        raise AssertionError(f"modal did not open with explicit state: {state!r}")
    if state["role"] != "dialog" or state["modal"] != "true":
        raise AssertionError(f"modal lacks dialog semantics: {state!r}")
    if state["title"] != "Delete alias" or state["actionLabels"] != ["Cancel", "Delete"]:
        raise AssertionError(f"unexpected modal content: {state!r}")
    if state["activeText"] != "Delete":
        raise AssertionError(f"modal initial focus did not enter primary control: {state!r}")
    if state["dialogWidth"] > state["viewportWidth"] - 8:
        raise AssertionError(f"modal overflows viewport: {state!r}")
    page.keyboard.press("Escape")
    page.wait_for_function(
        """() => {
            const modal = document.querySelector("#uiCatalogueDemoConfirmModal");
            return modal
                && modal.hidden
                && modal.dataset.open === "false"
                && modal.getAttribute("aria-hidden") === "true";
        }""",
        timeout=10_000,
    )
    return {"width": viewport["width"], "height": viewport["height"], "modal": "confirm"}


def check_dark_theme(page: Page, base_url: str, viewport: dict[str, int]) -> dict[str, object]:
    page.set_viewport_size(viewport)
    page.add_init_script("window.localStorage.setItem('theme', 'dark')")
    page.goto(f"{base_url}/ui-catalogue/demos/patterns/action-menu/", wait_until="domcontentloaded")
    wait_for_demo_ready(page, "#uiCatalogueDemoActionMenuRoot")
    page.locator("[data-ui-demo-menu-trigger]").click()
    page.wait_for_selector(".uiCatalogueDemoMenu__surface:not([hidden])", timeout=10_000)
    state = page.evaluate(
        """() => {
            const styles = element => getComputedStyle(element);
            const root = document.querySelector("#uiCatalogueDemoActionMenuRoot");
            const framed = document.querySelector(".uiCatalogueDemoExample--framed");
            const button = document.querySelector(".uiCatalogueDemoButton");
            const menu = document.querySelector(".uiCatalogueDemoMenu__surface");
            const code = document.querySelector(".uiCatalogueDemoCode pre");
            return {
                viewportWidth: window.innerWidth,
                theme: document.documentElement.getAttribute("data-theme"),
                bodyBackground: styles(document.body).backgroundColor,
                rootColor: root ? styles(root).color : "",
                rootSurfaceToken: root ? styles(root).getPropertyValue("--ui-demo-surface").trim() : "",
                rootCodeToken: root ? styles(root).getPropertyValue("--ui-demo-surface-code").trim() : "",
                framedBackground: framed ? styles(framed).backgroundColor : "",
                buttonBackground: button ? styles(button).backgroundColor : "",
                menuBackground: menu ? styles(menu).backgroundColor : "",
                codeBackground: code ? styles(code).backgroundColor : ""
            };
        }"""
    )
    expected = {
        "theme": "dark",
        "bodyBackground": "rgb(15, 15, 16)",
        "rootColor": "rgb(242, 242, 242)",
        "rootSurfaceToken": "#161618",
        "rootCodeToken": "#121316",
        "framedBackground": "rgb(22, 22, 24)",
        "buttonBackground": "rgb(22, 22, 24)",
        "menuBackground": "rgb(22, 22, 24)",
        "codeBackground": "rgb(18, 19, 22)",
    }
    actual = {key: state.get(key) for key in expected}
    if actual != expected:
        raise AssertionError(f"unexpected UI Catalogue dark theme at viewport {viewport!r}: {state!r}")
    toggle = page.locator(".uiCatalogueThemeToggle")
    default_toggle_state = toggle.evaluate(
        """button => {
            const styles = getComputedStyle(button);
            return {
                borderWidth: styles.borderTopWidth,
                background: styles.backgroundColor
            };
        }"""
    )
    if default_toggle_state != {"borderWidth": "0px", "background": "rgba(0, 0, 0, 0)"}:
        raise AssertionError(f"unexpected UI Catalogue theme toggle default style: {default_toggle_state!r}")
    toggle.hover()
    hover_toggle_state = toggle.evaluate("button => getComputedStyle(button).backgroundColor")
    if hover_toggle_state != "rgb(28, 28, 31)":
        raise AssertionError(f"unexpected UI Catalogue theme toggle hover background: {hover_toggle_state!r}")
    return {"width": viewport["width"], "height": viewport["height"], "theme": "dark"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_server()
    try:
        console_errors: list[str] = []
        page_errors: list[str] = []
        requests: list[str] = []
        failed_responses: list[str] = []
        modal_results: list[dict[str, object]] = []
        dark_theme_results: list[dict[str, object]] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                page.on("request", lambda request: requests.append(request.url))
                page.on(
                    "response",
                    lambda response: failed_responses.append(f"{response.status} {response.url}")
                    if response.status >= 400
                    else None,
                )
                page.goto(f"{base_url}/ui-catalogue/demos/", wait_until="domcontentloaded")
                wait_for_demo_ready(page, "#uiCatalogueDemoIndexRoot")
                requests.clear()

                for route in ROUTES:
                    page.goto(f"{base_url}{route['path']}", wait_until="domcontentloaded")
                    wait_for_demo_ready(page, route["root"])
                    doc_link_count = page.locator(".uiCatalogueShellDocLink").count()
                    if doc_link_count:
                        raise AssertionError(f"{route['path']} still renders header doc pill")

                for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                    modal_results.append(check_modal_shell(page, base_url, viewport))
                    dark_theme_results.append(check_dark_theme(page, base_url, viewport))
            finally:
                browser.close()

        if not any("/ui-catalogue/app/assets/css/ui-catalogue-demo.css" in request for request in requests):
            raise AssertionError("UI Catalogue demo CSS was not requested")
        if not any("/ui-catalogue/app/assets/css/ui-catalogue-shell.css" in request for request in requests):
            raise AssertionError("UI Catalogue shell CSS was not requested")
        if not any("/ui-catalogue/app/assets/js/ui-catalogue-demo.js" in request for request in requests):
            raise AssertionError("UI Catalogue demo JS was not requested")
        if not any("/ui-catalogue/app/assets/js/ui-catalogue-shell.js" in request for request in requests):
            raise AssertionError("UI Catalogue shell JS was not requested")
        legacy_ui_catalogue_requests = [request for request in requests if "/assets/ui-catalogue/" in request or "/studio/ui-catalogue/" in request]
        if legacy_ui_catalogue_requests:
            raise AssertionError(f"UI Catalogue demos should not request retired UI Catalogue paths: {legacy_ui_catalogue_requests!r}")
        studio_asset_requests = [request for request in requests if "/studio/app/" in request]
        if studio_asset_requests:
            raise AssertionError(f"UI Catalogue demos should not request Studio app assets: {studio_asset_requests!r}")
        main_css_requests = [request for request in requests if "/assets/css/main.css" in request]
        if main_css_requests:
            raise AssertionError(f"UI Catalogue demos should not request public main CSS: {main_css_requests!r}")
        if failed_responses:
            raise AssertionError(f"failed responses: {failed_responses}")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(
            json.dumps(
                {
                    "base_url": base_url,
                    "routes": len(ROUTES),
                    "modal_viewports": modal_results,
                    "dark_theme_viewports": dark_theme_results,
                },
                sort_keys=True,
            )
        )
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())

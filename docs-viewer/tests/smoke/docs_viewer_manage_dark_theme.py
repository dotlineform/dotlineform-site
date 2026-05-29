#!/usr/bin/env python3
"""Smoke-check local Docs Viewer manage-mode dark theme tokens."""

from __future__ import annotations

import argparse
import json

from playwright.sync_api import Page, sync_playwright

from docs_viewer_service_manage import start_server


EXPECTED_DARK_STATE = {
    "theme": "dark",
    "allowManagement": "true",
    "bodyBackground": "rgb(15, 15, 16)",
    "rootColor": "rgb(242, 242, 242)",
    "rootBackgroundToken": "#0f0f10",
    "panelToken": "#161618",
    "sidebarBackground": "rgb(22, 22, 24)",
    "searchBackground": "rgb(22, 22, 24)",
    "contentColor": "rgb(242, 242, 242)",
    "headingColor": "rgb(242, 242, 242)",
    "infoBackground": "rgb(22, 22, 24)",
}


def collect_theme_state(page: Page, base_url: str, timeout_ms: int) -> dict[str, object]:
    page.add_init_script("window.localStorage.setItem('theme', 'dark')")
    page.goto(f"{base_url}/docs/?scope=studio&doc=docs-viewer&mode=manage", wait_until="domcontentloaded")
    page.wait_for_selector("#docsViewerRoot:not([hidden])", timeout=timeout_ms)
    page.wait_for_function(
        """() => document.querySelector("#docsViewerContent h1")?.id === "docs-viewer" """,
        timeout=timeout_ms,
    )
    page.wait_for_function(
        """() => document.querySelector("#docsViewerManageActionsButton") && document.querySelector("#docsViewerInfoToggle") """,
        timeout=timeout_ms,
    )
    page.locator("#docsViewerInfoToggle").click()
    page.wait_for_function(
        """() => document.querySelector("#docsViewerRoot")?.dataset.infoPanelState === "open" """,
        timeout=timeout_ms,
    )
    return page.evaluate(
        """() => {
            const styles = element => getComputedStyle(element);
            const root = document.querySelector("#docsViewerRoot");
            const sidebar = document.querySelector(".docsViewer__sidebarInner");
            const search = document.querySelector(".docsViewer__searchInput");
            const content = document.querySelector("#docsViewerContent");
            const heading = document.querySelector("#docsViewerContent h1");
            const info = document.querySelector("#docsViewerInfoPanel");
            return {
                viewportWidth: window.innerWidth,
                theme: document.documentElement.getAttribute("data-theme"),
                allowManagement: root?.dataset.allowManagement || "",
                bodyBackground: styles(document.body).backgroundColor,
                rootColor: root ? styles(root).color : "",
                rootBackgroundToken: root ? styles(root).getPropertyValue("--docs-viewer-bg").trim() : "",
                panelToken: root ? styles(root).getPropertyValue("--docs-viewer-panel").trim() : "",
                sidebarBackground: sidebar ? styles(sidebar).backgroundColor : "",
                searchBackground: search ? styles(search).backgroundColor : "",
                contentColor: content ? styles(content).color : "",
                headingColor: heading ? styles(heading).color : "",
                infoBackground: info ? styles(info).backgroundColor : ""
            };
        }"""
    )


def assert_dark_state(theme_state: dict[str, object]) -> None:
    actual = {key: theme_state.get(key) for key in EXPECTED_DARK_STATE}
    if actual != EXPECTED_DARK_STATE:
        raise AssertionError(f"unexpected dark manage theme at viewport {theme_state.get('viewportWidth')}: {theme_state!r}")


def assert_theme_toggle_style(page: Page) -> None:
    toggle = page.locator(".docsViewer__themeToggle")
    default_state = toggle.evaluate(
        """button => {
            const styles = getComputedStyle(button);
            return {
                borderWidth: styles.borderTopWidth,
                background: styles.backgroundColor
            };
        }"""
    )
    if default_state != {"borderWidth": "0px", "background": "rgba(0, 0, 0, 0)"}:
        raise AssertionError(f"unexpected Docs Viewer theme toggle default style: {default_state!r}")
    toggle.hover()
    hover_state = toggle.evaluate("button => getComputedStyle(button).backgroundColor")
    if hover_state != "rgb(28, 28, 31)":
        raise AssertionError(f"unexpected Docs Viewer theme toggle hover background: {hover_state!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    server, base_url = start_server()
    states: list[dict[str, object]] = []
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                page = browser.new_page(viewport=viewport)
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                state = collect_theme_state(page, base_url, args.timeout_ms)
                assert_dark_state(state)
                assert_theme_toggle_style(page)
                states.append(state)
                page.close()
            browser.close()
        if errors:
            raise AssertionError(f"page errors during Docs Viewer dark-theme smoke: {errors!r}")
        print(json.dumps({"base_url": base_url, "viewports": [state["viewportWidth"] for state in states]}, sort_keys=True))
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())

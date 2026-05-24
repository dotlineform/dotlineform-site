#!/usr/bin/env python3
"""Smoke-check local Studio UI Catalogue demo routes."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402


ROUTES = [
    {
        "view_id": "ui_catalogue_demos",
        "path": "/studio/ui-catalogue/demos/",
        "root": "#uiCatalogueDemoIndexRoot",
    },
    {
        "view_id": "ui_catalogue_demo_button",
        "path": "/studio/ui-catalogue/demos/primitives/button/",
        "root": "#uiCatalogueDemoButtonRoot",
    },
    {
        "view_id": "ui_catalogue_demo_input",
        "path": "/studio/ui-catalogue/demos/primitives/input/",
        "root": "#uiCatalogueDemoInputRoot",
    },
    {
        "view_id": "ui_catalogue_demo_list",
        "path": "/studio/ui-catalogue/demos/primitives/list/",
        "root": "#uiCatalogueDemoListRoot",
    },
    {
        "view_id": "ui_catalogue_demo_modal_shell",
        "path": "/studio/ui-catalogue/demos/primitives/modal-shell/",
        "root": "#uiCatalogueDemoModalShellRoot",
    },
    {
        "view_id": "ui_catalogue_demo_panel",
        "path": "/studio/ui-catalogue/demos/primitives/panel/",
        "root": "#uiCatalogueDemoPanelRoot",
    },
    {
        "view_id": "ui_catalogue_demo_reopenable_command_result",
        "path": "/studio/ui-catalogue/demos/patterns/reopenable-command-result/",
        "root": "#uiCatalogueDemoReopenableCommandResultRoot",
    },
    {
        "view_id": "ui_catalogue_demo_column_links",
        "path": "/studio/ui-catalogue/demos/patterns/column-links/",
        "root": "#uiCatalogueDemoColumnLinksRoot",
    },
]


def start_server() -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), REPO_ROOT)
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
    page.goto(f"{base_url}/studio/ui-catalogue/demos/primitives/modal-shell/", wait_until="domcontentloaded")
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_server()
    try:
        with urllib.request.urlopen(f"{base_url}/studio/runtime-config.json", timeout=10) as response:
            runtime_config = json.loads(response.read().decode("utf-8"))
        runtime_views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
        runtime_by_id = {view.get("id"): view for view in runtime_views if isinstance(view, dict)}
        for route in ROUTES:
            runtime_view = runtime_by_id.get(route["view_id"])
            if not runtime_view or runtime_view.get("path") != route["path"]:
                raise AssertionError(f"runtime config missing {route['view_id']}: {runtime_views!r}")

        console_errors: list[str] = []
        page_errors: list[str] = []
        requests: list[str] = []
        failed_responses: list[str] = []
        modal_results: list[dict[str, object]] = []
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
                page.goto(f"{base_url}/studio/", wait_until="domcontentloaded")
                home_links = page.locator('.studioLinkList__item[href="/studio/ui-catalogue/demos/"]').count()
                if home_links != 1:
                    raise AssertionError("local Studio home does not expose the UI Catalogue demo index")
                requests.clear()

                for route in ROUTES:
                    page.goto(f"{base_url}{route['path']}", wait_until="domcontentloaded")
                    wait_for_demo_ready(page, route["root"])
                    doc_link = page.locator(".studioLayout__docLink").get_attribute("href")
                    if "mode=manage" not in str(doc_link or ""):
                        raise AssertionError(f"{route['path']} doc link is not manage-mode: {doc_link!r}")

                for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                    modal_results.append(check_modal_shell(page, base_url, viewport))
            finally:
                browser.close()

        if not any("/studio/ui-catalogue/assets/css/ui-catalogue-demo.css" in request for request in requests):
            raise AssertionError("UI Catalogue demo CSS was not requested")
        if not any("/studio/ui-catalogue/assets/js/ui-catalogue-demo.js" in request for request in requests):
            raise AssertionError("UI Catalogue demo JS was not requested")
        legacy_ui_catalogue_requests = [request for request in requests if "/assets/ui-catalogue/" in request]
        if legacy_ui_catalogue_requests:
            raise AssertionError(f"UI Catalogue demos should not request legacy public UI Catalogue assets: {legacy_ui_catalogue_requests!r}")
        if not any("/studio/app/assets/css/studio.css" in request for request in requests):
            raise AssertionError("UI Catalogue demos should request Studio shell CSS")
        main_css_requests = [request for request in requests if "/assets/css/main.css" in request]
        if main_css_requests:
            raise AssertionError(f"UI Catalogue demos should not request public main CSS: {main_css_requests!r}")
        if failed_responses:
            raise AssertionError(f"failed responses: {failed_responses}")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(json.dumps({"base_url": base_url, "routes": len(ROUTES), "modal_viewports": modal_results}, sort_keys=True))
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())

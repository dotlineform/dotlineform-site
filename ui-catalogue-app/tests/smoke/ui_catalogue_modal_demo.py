#!/usr/bin/env python3
"""Smoke-check the UI Catalogue modal shell demo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from threading import Thread

from playwright.sync_api import Page, sync_playwright


ROOT_SELECTOR = "#uiCatalogueDemoModalShellRoot"
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
SERVER_DIR = REPO_ROOT / "ui-catalogue-app" / "app" / "server" / "ui_catalogue_app"
sys.path.insert(0, str(SERVER_DIR))

from ui_catalogue_app_server import UiCatalogueAppServer  # noqa: E402


def start_ui_catalogue_server() -> tuple[UiCatalogueAppServer, str]:
    server = UiCatalogueAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def wait_for_demo_ready(page: Page, timeout_ms: int) -> None:
    page.wait_for_selector(f"{ROOT_SELECTOR}:not([hidden])", timeout=timeout_ms)
    page.wait_for_function(
        """selector => {
            const root = document.querySelector(selector);
            return root
                && root.dataset.uiCatalogueDemoReady === 'true'
                && root.dataset.uiCatalogueDemoBusy === 'false';
        }""",
        arg=ROOT_SELECTOR,
        timeout=timeout_ms,
    )


def modal_state(page: Page, modal_id: str) -> dict[str, object]:
    return page.locator(f"#{modal_id}").evaluate(
        """modal => {
            const dialog = modal.querySelector('[role="dialog"]');
            const title = modal.querySelector('.uiCatalogueDemoModal__title');
            const actions = Array.from(modal.querySelectorAll('.uiCatalogueDemoModal__actions button'));
            const active = document.activeElement;
            const rect = dialog ? dialog.getBoundingClientRect() : null;
            return {
                hidden: modal.hidden,
                open: modal.dataset.open || '',
                ariaHidden: modal.getAttribute('aria-hidden') || '',
                role: dialog ? dialog.getAttribute('role') : '',
                modal: dialog ? dialog.getAttribute('aria-modal') : '',
                labelledBy: dialog ? dialog.getAttribute('aria-labelledby') : '',
                titleId: title ? title.id : '',
                title: title ? title.textContent.trim() : '',
                dialogClass: dialog ? dialog.className : '',
                actionLabels: actions.map(button => button.textContent.trim()),
                actionClasses: actions.map(button => button.className),
                activeId: active ? active.id || '' : '',
                activeText: active ? active.textContent.trim() : '',
                cardWidth: rect ? Math.round(rect.width) : 0,
                viewportWidth: window.innerWidth,
                bodyText: modal.textContent || ''
            };
        }"""
    )


def assert_modal_shell(
    page: Page,
    modal_id: str,
    expected_title: str,
    expected_actions: list[str],
    expected_active: str,
    size_class: str,
) -> dict[str, object]:
    state = modal_state(page, modal_id)
    if state["hidden"] or state["open"] != "true" or state["ariaHidden"] != "false":
        raise AssertionError(f"modal did not open with explicit state: {state!r}")
    if state["role"] != "dialog" or state["modal"] != "true":
        raise AssertionError(f"modal lacks dialog semantics: {state!r}")
    if not state["labelledBy"] or state["labelledBy"] != state["titleId"]:
        raise AssertionError(f"modal is not labelled by its title: {state!r}")
    if state["title"] != expected_title:
        raise AssertionError(f"unexpected modal title: {state!r}")
    if state["actionLabels"] != expected_actions:
        raise AssertionError(f"unexpected modal action row: {state!r}")
    if size_class and size_class not in state["dialogClass"]:
        raise AssertionError(f"modal size class mismatch: {state!r}")
    if not all("uiCatalogueDemoButton--fixed" in value for value in state["actionClasses"]):
        raise AssertionError(f"modal action buttons are not fixed-width demo commands: {state!r}")
    if state["cardWidth"] > state["viewportWidth"] - 8:
        raise AssertionError(f"modal overflows viewport: {state!r}")
    if expected_active and state["activeId"] != expected_active and state["activeText"] != expected_active:
        raise AssertionError(f"modal focus did not enter expected control: {state!r}")
    return state


def assert_closed_with_focus(page: Page, modal_id: str, opener_selector: str) -> None:
    page.wait_for_function(
        """([modalId, openerSelector]) => {
            const modal = document.getElementById(modalId);
            const opener = document.querySelector(openerSelector);
            return modal
                && opener
                && modal.hidden
                && modal.dataset.open === 'false'
                && modal.getAttribute('aria-hidden') === 'true'
                && document.activeElement === opener;
        }""",
        arg=[modal_id, opener_selector],
    )


def focus_wrap(page: Page, selector: str, key: str) -> str:
    page.locator(selector).focus()
    page.keyboard.press(key)
    return page.evaluate("document.activeElement ? document.activeElement.textContent.trim() || document.activeElement.id || '' : ''")


def open_modal(page: Page, modal_id: str) -> str:
    opener_selector = f'[data-ui-demo-modal-open="{modal_id}"]'
    opener = page.locator(opener_selector)
    opener.scroll_into_view_if_needed()
    opener.click()
    page.wait_for_selector(f"#{modal_id}[data-open='true']")
    return opener_selector


def run_notice_check(page: Page) -> None:
    opener_selector = open_modal(page, "uiCatalogueDemoNoticeModal")
    assert_modal_shell(
        page,
        "uiCatalogueDemoNoticeModal",
        "Prepare complete",
        ["Close"],
        "Close",
        "uiCatalogueDemoModal__dialog--compact",
    )
    page.keyboard.press("Escape")
    assert_closed_with_focus(page, "uiCatalogueDemoNoticeModal", opener_selector)


def run_confirm_check(page: Page) -> None:
    opener_selector = open_modal(page, "uiCatalogueDemoConfirmModal")
    assert_modal_shell(
        page,
        "uiCatalogueDemoConfirmModal",
        "Delete alias",
        ["Cancel", "Delete"],
        "Delete",
        "uiCatalogueDemoModal__dialog--compact",
    )
    if focus_wrap(page, "#uiCatalogueDemoConfirmModal [data-ui-demo-modal-initial-focus]", "Shift+Tab") != "Cancel":
        raise AssertionError("confirmation modal did not wrap focus backward to Cancel")
    page.locator("#uiCatalogueDemoConfirmModal .uiCatalogueDemoModal__actions [data-ui-demo-modal-close]").click()
    assert_closed_with_focus(page, "uiCatalogueDemoConfirmModal", opener_selector)


def run_input_check(page: Page) -> None:
    opener_selector = open_modal(page, "uiCatalogueDemoInputModal")
    assert_modal_shell(
        page,
        "uiCatalogueDemoInputModal",
        "New document",
        ["Cancel", "Create"],
        "uiCatalogueDemoModalTitleInput",
        "uiCatalogueDemoModal__dialog--compact",
    )
    page.locator("#uiCatalogueDemoInputModal [data-ui-demo-modal-submit]").click()
    status = page.locator("#uiCatalogueDemoInputModal [data-ui-demo-modal-status]").inner_text()
    if status != "Enter a title before continuing.":
        raise AssertionError(f"input modal did not show validation status: {status!r}")
    page.locator("#uiCatalogueDemoModalTitleInput").fill("Smoke document")
    page.locator("#uiCatalogueDemoInputModal [data-ui-demo-modal-submit]").click()
    assert_closed_with_focus(page, "uiCatalogueDemoInputModal", opener_selector)


def run_workflow_check(page: Page) -> None:
    opener_selector = open_modal(page, "uiCatalogueDemoWorkflowModal")
    state = assert_modal_shell(
        page,
        "uiCatalogueDemoWorkflowModal",
        "Import review",
        ["Cancel", "Preview", "Apply"],
        "uiCatalogueDemoModalConflictSelect",
        "uiCatalogueDemoModal__dialog--wide",
    )
    if "Preview before applying imported changes." not in state["bodyText"]:
        raise AssertionError(f"workflow status slot missing: {state!r}")
    if focus_wrap(page, "#uiCatalogueDemoWorkflowModal [data-ui-demo-modal-initial-focus]", "Shift+Tab") != "Apply":
        raise AssertionError("workflow modal did not wrap focus backward to Apply")
    page.locator("#uiCatalogueDemoWorkflowModal .uiCatalogueDemoModal__backdrop").click(position={"x": 4, "y": 4})
    assert_closed_with_focus(page, "uiCatalogueDemoWorkflowModal", opener_selector)


def run_viewport_smoke(page: Page, base_url: str, viewport: dict[str, int], timeout_ms: int) -> dict[str, object]:
    page.set_viewport_size(viewport)
    page.goto(route_url(base_url, "/ui-catalogue/demos/primitives/modal-shell/"), wait_until="domcontentloaded")
    wait_for_demo_ready(page, timeout_ms)
    run_notice_check(page)
    run_confirm_check(page)
    run_input_check(page)
    run_workflow_check(page)
    return {
        "width": viewport["width"],
        "height": viewport["height"],
        "checked": ["notice", "confirm", "input", "workflow"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    server = None
    base_url = args.base_url
    if not base_url:
        server, base_url = start_ui_catalogue_server()

    errors: list[str] = []
    results: list[dict[str, object]] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                    results.append(run_viewport_smoke(page, base_url, viewport, args.timeout_ms))
            finally:
                browser.close()
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()

    if errors:
        raise AssertionError(f"page errors during UI Catalogue modal demo smoke: {errors!r}")
    print(json.dumps({"viewports": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

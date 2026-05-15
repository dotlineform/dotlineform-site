#!/usr/bin/env python3
"""Smoke-check the Studio activity detail modal."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


ROOT_SELECTOR = "#studioActivityRoot"
ACTIVITY_FEED_GLOB = "http://127.0.0.1:8788/catalogue/read**"


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


def activity_feed() -> dict[str, object]:
    return {
        "header": {
            "schema": "studio_activity_log_v1",
            "generated_at_utc": "2026-05-15T10:00:00Z",
            "entry_count": 1,
        },
        "entries": [
            {
                "id": "activity-modal-smoke",
                "activity_id": "activity-modal-smoke",
                "time_utc": "2026-05-15T10:00:00Z",
                "timestamp": "2026-05-15T10:00:00Z",
                "status": "completed",
                "page_label": "Catalogue Work",
                "user_action_label": "Save work",
                "script_purpose_label": "Save catalogue source",
                "detail_items": [
                    "Wrote source JSON",
                    "Updated Studio activity feed",
                ],
                "record_groups": {
                    "works": {"count": 1},
                    "files": {"count": 2},
                },
            }
        ],
    }


def wait_for_studio_route_ready(page, timeout_ms: int) -> dict[str, str]:
    page.wait_for_selector(f"{ROOT_SELECTOR}:not([hidden])", timeout=timeout_ms)
    page.wait_for_selector(f"{ROOT_SELECTOR}[data-studio-ready='true']", timeout=timeout_ms)
    page.wait_for_function(
        "selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'",
        arg=ROOT_SELECTOR,
        timeout=timeout_ms,
    )
    return page.locator(ROOT_SELECTOR).evaluate(
        """root => ({
            route: root.dataset.studioRoute || "",
            ready: root.dataset.studioReady || "",
            busy: root.dataset.studioBusy || "",
            mode: root.dataset.studioMode || "",
            service: root.dataset.studioService || "",
            recordLoaded: root.dataset.studioRecordLoaded || ""
        })"""
    )


def assert_ready_contract(attrs: dict[str, str]) -> None:
    expected = {
        "route": "studio-activity",
        "ready": "true",
        "busy": "false",
        "mode": "list",
        "service": "available",
        "recordLoaded": "true",
    }
    for key, value in expected.items():
        if attrs.get(key) != value:
            raise AssertionError(f"unexpected activity route {key}: {attrs!r}")


def assert_activity_modal(page, timeout_ms: int) -> dict[str, object]:
    opener = page.locator("[data-activity-id='activity-modal-smoke']")
    opener.click()
    page.wait_for_selector('[data-role="studio-modal"]', timeout=timeout_ms)

    modal_state = page.locator('[data-role="studio-modal"]').evaluate(
        """modal => {
            const dialog = modal.querySelector('[role="dialog"]');
            const title = modal.querySelector('.tagStudioModal__title');
            const closeButton = modal.querySelector('.tagStudioModal__close');
            const actionButtons = Array.from(modal.querySelectorAll('.tagStudioModal__actions button'));
            const bodyLines = Array.from(modal.querySelectorAll('.tagStudioModal__label'))
                .map(node => node.textContent.trim())
                .filter(Boolean);
            return {
                role: dialog ? dialog.getAttribute('role') : "",
                modal: dialog ? dialog.getAttribute('aria-modal') : "",
                labelledBy: dialog ? dialog.getAttribute('aria-labelledby') : "",
                titleId: title ? title.id : "",
                title: title ? title.textContent.trim() : "",
                closeLabel: closeButton ? closeButton.getAttribute('aria-label') : "",
                actionLabels: actionButtons.map(button => button.textContent.trim()),
                bodyLines,
                activeRole: document.activeElement ? document.activeElement.getAttribute('data-role') : ""
            };
        }"""
    )
    if modal_state["role"] != "dialog" or modal_state["modal"] != "true":
        raise AssertionError(f"activity modal lacks dialog semantics: {modal_state!r}")
    if not modal_state["labelledBy"] or modal_state["labelledBy"] != modal_state["titleId"]:
        raise AssertionError(f"activity modal is not labelled by its title: {modal_state!r}")
    if modal_state["title"] != "Activity details":
        raise AssertionError(f"activity modal title mismatch: {modal_state!r}")
    if modal_state["closeLabel"] != "Close" or modal_state["actionLabels"] != ["Close"]:
        raise AssertionError(f"activity modal close controls mismatch: {modal_state!r}")
    if modal_state["bodyLines"] != ["Wrote source JSON", "Updated Studio activity feed"]:
        raise AssertionError(f"activity modal body mismatch: {modal_state!r}")
    if modal_state["activeRole"] != "modal-cancel":
        raise AssertionError(f"activity modal did not focus the close action: {modal_state!r}")

    page.keyboard.press("Escape")
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=timeout_ms)
    focus_returned = page.evaluate(
        "() => document.activeElement && document.activeElement.getAttribute('data-activity-id')"
    )
    if focus_returned != "activity-modal-smoke":
        raise AssertionError(f"activity modal did not return focus to opener: {focus_returned!r}")

    opener.click()
    page.wait_for_selector('[data-role="studio-modal"]', timeout=timeout_ms)
    page.locator(".tagStudioModal__backdrop").click(position={"x": 8, "y": 8})
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=timeout_ms)

    opener.click()
    page.wait_for_selector('[data-role="studio-modal"]', timeout=timeout_ms)
    page.locator('[data-role="modal-cancel"]').last.click()
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=timeout_ms)

    return modal_state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--site-root", help="Serve a built site root on a temporary local HTTP server.")
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
            page.route(
                ACTIVITY_FEED_GLOB,
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(activity_feed()),
                ),
            )
            page.goto(route_url(base_url, "/studio/activity/"), wait_until="domcontentloaded")
            attrs = wait_for_studio_route_ready(page, args.timeout_ms)
            assert_ready_contract(attrs)
            modal = assert_activity_modal(page, args.timeout_ms)
            print(json.dumps({"route": attrs, "modal": modal}, sort_keys=True))
        finally:
            browser.close()
            if server is not None:
                server.shutdown()
                server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

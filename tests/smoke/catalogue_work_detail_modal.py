#!/usr/bin/env python3
"""Smoke-check the catalogue work detail confirmation modals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from threading import Thread
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Route, sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.studio.studio_app_server import StudioAppServer  # noqa: E402


ROOT_SELECTOR = "#catalogueWorkDetailRoot"
DETAIL_UID = "00001-001"
WORK_ID = "00001"


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def start_local_studio_server() -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


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
        "route": "catalogue-work-detail",
        "ready": "true",
        "busy": "false",
        "mode": "single",
        "service": "available",
        "recordLoaded": "true",
    }
    for key, value in expected.items():
        if attrs.get(key) != value:
            raise AssertionError(f"unexpected ready state for {key}: {attrs!r}")


def request_json(route: Route) -> dict[str, object]:
    post_data_json = route.request.post_data_json
    if callable(post_data_json):
        return post_data_json()
    if post_data_json:
        return post_data_json
    post_data = getattr(route.request, "post_data", "") or "{}"
    if callable(post_data):
        post_data = post_data()
    return json.loads(post_data or "{}")


def modal_shell_state(page) -> dict[str, object]:
    return page.locator('[data-role="studio-modal"]').evaluate(
        """modal => {
            const dialog = modal.querySelector('[role="dialog"]');
            const title = modal.querySelector('.tagStudioModal__title');
            const actionButtons = Array.from(modal.querySelectorAll('.tagStudioModal__actions button'));
            return {
                role: dialog ? dialog.getAttribute('role') : "",
                modal: dialog ? dialog.getAttribute('aria-modal') : "",
                labelledBy: dialog ? dialog.getAttribute('aria-labelledby') : "",
                titleId: title ? title.id : "",
                title: title ? title.textContent.trim() : "",
                dialogClass: dialog ? dialog.className : "",
                actionLabels: actionButtons.map(button => button.textContent.trim()),
                actionClasses: actionButtons.map(button => button.className),
                activeRole: document.activeElement ? document.activeElement.getAttribute('data-role') || "" : "",
                bodyText: modal.textContent || ""
            };
        }"""
    )


def assert_modal_shell(page, title: str, actions: list[str], timeout_ms: int) -> dict[str, object]:
    page.wait_for_selector('[data-role="studio-modal"]', timeout=timeout_ms)
    state = modal_shell_state(page)
    if state["role"] != "dialog" or state["modal"] != "true":
        raise AssertionError(f"modal lacks dialog semantics: {state!r}")
    if not state["labelledBy"] or state["labelledBy"] != state["titleId"]:
        raise AssertionError(f"modal is not labelled by its title: {state!r}")
    if state["title"] != title:
        raise AssertionError(f"unexpected modal title: {state!r}")
    if "tagStudioModal__dialog--compact" not in state["dialogClass"]:
        raise AssertionError(f"confirmation modal is not compact: {state!r}")
    if state["actionLabels"] != actions:
        raise AssertionError(f"unexpected modal actions: {state!r}")
    if not all("tagStudio__button--defaultWidth" in value for value in state["actionClasses"]):
        raise AssertionError(f"modal actions are missing default-width buttons: {state!r}")
    if state["activeRole"] != "modal-primary":
        raise AssertionError(f"confirmation modal did not focus the primary action: {state!r}")
    return state


def close_with_escape(page, opener_selector: str, timeout_ms: int) -> None:
    page.keyboard.press("Escape")
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=timeout_ms)
    focused_id = page.evaluate("document.activeElement ? document.activeElement.id : ''")
    expected_id = opener_selector.lstrip("#")
    if focused_id != expected_id:
        raise AssertionError(f"modal did not return focus to opener: {focused_id!r}")


def close_with_backdrop(page, opener_selector: str, timeout_ms: int) -> None:
    page.mouse.click(12, 12)
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=timeout_ms)
    focused_id = page.evaluate("document.activeElement ? document.activeElement.id : ''")
    expected_id = opener_selector.lstrip("#")
    if focused_id != expected_id:
        raise AssertionError(f"modal did not return focus to opener: {focused_id!r}")


def close_with_cancel(page, opener_selector: str, timeout_ms: int) -> None:
    page.locator('[data-role="modal-cancel"]').last.click()
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=timeout_ms)
    focused_id = page.evaluate("document.activeElement ? document.activeElement.id : ''")
    expected_id = opener_selector.lstrip("#")
    if focused_id != expected_id:
        raise AssertionError(f"modal did not return focus to opener: {focused_id!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    server = None
    base_url = args.base_url
    if not base_url:
        server, base_url = start_local_studio_server()

    detail_record = {
        "detail_uid": DETAIL_UID,
        "work_id": WORK_ID,
        "detail_id": "001",
        "details_subfolder": "details",
        "section_id": "detail-section",
        "section_title": "Smoke detail section",
        "sort_order": "1",
        "project_filename": "smoke-detail.jpg",
        "title": "Smoke detail",
        "status": "published",
        "published_date": "2026-05-15",
        "width_px": "1200",
        "height_px": "900",
    }
    work_record = {
        "work_id": WORK_ID,
        "title": "Smoke work",
        "year_display": "2026",
        "status": "published",
    }
    publication_apply_requests: list[dict[str, object]] = []
    delete_apply_requests: list[dict[str, object]] = []

    def fulfil_json(route: Route, payload: dict[str, object]) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(payload),
        )

    def handle_catalogue(route: Route) -> None:
        nonlocal detail_record
        request = route.request
        parsed = urlparse(request.url)
        query = parse_qs(parsed.query)
        path = parsed.path.removeprefix("/studio/api")
        if request.method == "GET" and path in {"/health", "/catalogue/health"}:
            fulfil_json(route, {"ok": True})
            return
        if request.method == "GET" and path == "/catalogue/read":
            key = query.get("key", [""])[0]
            if key == "catalogue_lookup_work_detail_search":
                fulfil_json(route, {"items": [detail_record]})
                return
            if key == "catalogue_lookup_work_search":
                fulfil_json(route, {"items": [work_record]})
                return
            if key == "catalogue_lookup_work_detail_base":
                fulfil_json(route, {"work_detail": detail_record, "record_hash": "hash-detail-current"})
                return
        if request.method == "POST" and path == "/catalogue/build-preview":
            fulfil_json(route, {
                "ok": True,
                "build": {
                    "work_ids": [WORK_ID],
                    "series_ids": [],
                    "rebuild_search": True,
                },
            })
            return
        if request.method == "POST" and path == "/catalogue/publication-preview":
            fulfil_json(route, {
                "ok": True,
                "preview": {
                    "blocked": False,
                    "blockers": [],
                    "summary": f"Unpublish detail {DETAIL_UID} and clean public output.",
                },
            })
            return
        if request.method == "POST" and path == "/catalogue/publication-apply":
            body = request_json(route)
            publication_apply_requests.append(body)
            detail_record = {**detail_record, "status": "draft"}
            fulfil_json(route, {
                "ok": True,
                "status": "ok",
                "record": detail_record,
                "record_hash": "hash-detail-draft",
            })
            return
        if request.method == "POST" and path == "/catalogue/delete-preview":
            fulfil_json(route, {
                "ok": True,
                "preview": {
                    "blocked": False,
                    "blockers": [],
                    "validation_errors": [],
                    "summary": f"Delete source record {DETAIL_UID} and remove generated detail output.",
                },
            })
            return
        if request.method == "POST" and path == "/catalogue/delete-apply":
            body = request_json(route)
            delete_apply_requests.append(body)
            fulfil_json(route, {"ok": True, "deleted": True})
            return
        fulfil_json(route, {"ok": False, "error": f"Unhandled mock route: {request.method} {path}"})

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.route(f"{base_url}/studio/api/catalogue/**", handle_catalogue)
            page.goto(
                route_url(base_url, f"/studio/catalogue-work-detail/?detail={DETAIL_UID}"),
                wait_until="domcontentloaded",
            )
            attrs = wait_for_studio_route_ready(page, args.timeout_ms)
            assert_ready_contract(attrs)

            publication_button = "#catalogueWorkDetailPublication"
            delete_button = "#catalogueWorkDetailDelete"

            page.locator(publication_button).click()
            unpublish_modal = assert_modal_shell(page, "Confirm unpublish", ["Cancel", "Unpublish"], args.timeout_ms)
            if f"Unpublish detail {DETAIL_UID}" not in unpublish_modal["bodyText"]:
                raise AssertionError(f"unpublish preview text missing from modal: {unpublish_modal!r}")
            close_with_escape(page, publication_button, args.timeout_ms)
            if publication_apply_requests:
                raise AssertionError(f"publication apply ran after Escape close: {publication_apply_requests!r}")

            page.locator(publication_button).click()
            assert_modal_shell(page, "Confirm unpublish", ["Cancel", "Unpublish"], args.timeout_ms)
            page.locator('[data-role="modal-primary"]').click()
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            page.wait_for_function("selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'", arg=ROOT_SELECTOR, timeout=args.timeout_ms)
            if len(publication_apply_requests) != 1:
                raise AssertionError(f"publication apply should be route-owned and confirmed once: {publication_apply_requests!r}")
            publication_request = publication_apply_requests[0]
            if publication_request.get("kind") != "work_detail" or publication_request.get("action") != "unpublish":
                raise AssertionError(f"unexpected publication apply request: {publication_request!r}")
            if publication_request.get("detail_uid") != DETAIL_UID:
                raise AssertionError(f"publication apply lost detail ownership: {publication_request!r}")

            page.locator(delete_button).click()
            delete_modal = assert_modal_shell(page, "Confirm delete", ["Cancel", "Delete"], args.timeout_ms)
            if f"Delete source record {DETAIL_UID}" not in delete_modal["bodyText"]:
                raise AssertionError(f"delete preview text missing from modal: {delete_modal!r}")
            close_with_backdrop(page, delete_button, args.timeout_ms)
            if delete_apply_requests:
                raise AssertionError(f"delete apply ran after backdrop close: {delete_apply_requests!r}")

            page.locator(delete_button).click()
            assert_modal_shell(page, "Confirm delete", ["Cancel", "Delete"], args.timeout_ms)
            close_with_cancel(page, delete_button, args.timeout_ms)
            if delete_apply_requests:
                raise AssertionError(f"delete apply ran after cancel action: {delete_apply_requests!r}")

            page.locator(delete_button).click()
            assert_modal_shell(page, "Confirm delete", ["Cancel", "Delete"], args.timeout_ms)
            page.locator('[data-role="modal-primary"]').click()
            page.wait_for_function(
                "() => window.location.pathname === '/studio/catalogue-work/'",
                timeout=args.timeout_ms,
            )
            if len(delete_apply_requests) != 1:
                raise AssertionError(f"delete apply should be route-owned and confirmed once: {delete_apply_requests!r}")
            delete_request = delete_apply_requests[0]
            if delete_request.get("kind") != "work_detail" or delete_request.get("detail_uid") != DETAIL_UID:
                raise AssertionError(f"unexpected delete apply request: {delete_request!r}")

            print(json.dumps({
                "route": attrs,
                "publication_apply_requests": len(publication_apply_requests),
                "delete_apply_requests": len(delete_apply_requests),
                "unpublish_modal": unpublish_modal,
                "delete_modal": delete_modal,
            }, sort_keys=True))
        finally:
            browser.close()
            if server:
                server.shutdown()
                server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

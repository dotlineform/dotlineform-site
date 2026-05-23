#!/usr/bin/env python3
"""Smoke-check the catalogue moment confirmation modals."""

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


ROOT_SELECTOR = "#catalogueMomentRoot"
MOMENT_ID = "smoke-moment"


def start_local_studio_server() -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


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
        "route": "catalogue-moment",
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
    page.wait_for_timeout(50)
    focused = page.evaluate(
        """selector => {
            const active = document.activeElement;
            if (!active) return "";
            if (selector.startsWith("#")) return active.id || "";
            return active.matches(selector) ? selector : "";
        }""",
        opener_selector,
    )
    expected = opener_selector.lstrip("#") if opener_selector.startswith("#") else opener_selector
    if focused != expected:
        raise AssertionError(f"modal did not return focus to opener: {focused!r}")


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


def build_preview_payload() -> dict[str, object]:
    return {
        "ok": True,
        "build": {
            "moment_ids": [MOMENT_ID],
            "rebuild_search": True,
            "readiness": {
                "items": [
                    {
                        "key": "moment_prose",
                        "status": "ready",
                        "title": "moment prose",
                        "summary": "Staged prose is ready to import.",
                        "source_path": "var/studio/catalogue/prose/smoke-moment.md",
                    },
                    {
                        "key": "moment_media",
                        "status": "ready",
                        "title": "moment media",
                        "summary": "Source media is ready.",
                        "source_path": "projects/smoke/smoke.jpg",
                        "exists": True,
                    },
                ]
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    server = None
    base_url = args.base_url
    if not base_url:
        server, base_url = start_local_studio_server()

    moment_record = {
        "moment_id": MOMENT_ID,
        "title": "Smoke moment",
        "status": "published",
        "date": "2026-05-15",
        "date_display": "15 May 2026",
        "published_date": "2026-05-15",
        "source_image_file": "smoke.jpg",
        "image_alt": "Smoke moment image",
    }
    prose_apply_requests: list[dict[str, object]] = []
    publication_apply_requests: list[dict[str, object]] = []
    delete_apply_requests: list[dict[str, object]] = []

    def fulfil_json(route: Route, payload: dict[str, object]) -> None:
        route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

    def handle_catalogue(route: Route) -> None:
        nonlocal moment_record
        request = route.request
        parsed = urlparse(request.url)
        query = parse_qs(parsed.query)
        path = parsed.path.removeprefix("/studio/api")
        if request.method == "GET" and path in {"/health", "/catalogue/health"}:
            fulfil_json(route, {"ok": True})
            return
        if request.method == "GET" and path == "/catalogue/read":
            key = query.get("key", [""])[0]
            if key == "catalogue_moments":
                fulfil_json(route, {"moments": {MOMENT_ID: moment_record}})
                return
        if request.method == "POST" and path == "/catalogue/moment/preview":
            fulfil_json(route, {
                "ok": True,
                "record": moment_record,
                "record_hash": "hash-moment-current",
                "preview": {
                    "public_url": f"/moments/{MOMENT_ID}/",
                    "generated_page_exists": True,
                    "generated_json_exists": True,
                    "in_moments_index": True,
                    "source_image_exists": True,
                    "source_exists": True,
                },
                "readiness": build_preview_payload()["build"]["readiness"],
                "build": build_preview_payload()["build"],
            })
            return
        if request.method == "POST" and path == "/catalogue/build-preview":
            fulfil_json(route, build_preview_payload())
            return
        if request.method == "POST" and path == "/catalogue/prose/import-preview":
            fulfil_json(route, {
                "ok": True,
                "valid": True,
                "overwrite_required": True,
                "target_path": "_moments/smoke-moment.md",
                "staging_path": "var/studio/catalogue/prose/smoke-moment.md",
            })
            return
        if request.method == "POST" and path == "/catalogue/prose/import-apply":
            body = request_json(route)
            prose_apply_requests.append(body)
            fulfil_json(route, {
                "ok": True,
                "changed": True,
                "target_path": "_moments/smoke-moment.md",
                "imported_at_utc": "2026-05-15T12:00:00Z",
            })
            return
        if request.method == "POST" and path == "/catalogue/publication-preview":
            fulfil_json(route, {
                "ok": True,
                "preview": {
                    "blocked": False,
                    "blockers": [],
                    "summary": f"Unpublish moment {MOMENT_ID} and clean public output.",
                },
            })
            return
        if request.method == "POST" and path == "/catalogue/publication-apply":
            body = request_json(route)
            publication_apply_requests.append(body)
            moment_record = {**moment_record, "status": "draft"}
            fulfil_json(route, {
                "ok": True,
                "status": "ok",
                "record": moment_record,
                "record_hash": "hash-moment-draft",
            })
            return
        if request.method == "POST" and path == "/catalogue/delete-preview":
            fulfil_json(route, {
                "ok": True,
                "preview": {
                    "blocked": False,
                    "blockers": [],
                    "validation_errors": [],
                    "summary": f"Delete source record {MOMENT_ID} and remove generated moment output.",
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
            page.goto(route_url(base_url, f"/studio/catalogue-moment/?moment={MOMENT_ID}"), wait_until="domcontentloaded")
            attrs = wait_for_studio_route_ready(page, args.timeout_ms)
            assert_ready_contract(attrs)

            prose_button = '[data-prose-import="moment"]'
            publication_button = "#catalogueMomentPublication"
            delete_button = "#catalogueMomentDelete"

            page.locator(prose_button).click()
            prose_modal = assert_modal_shell(page, "Confirm prose overwrite", ["Cancel", "Overwrite"], args.timeout_ms)
            if "_moments/smoke-moment.md" not in prose_modal["bodyText"]:
                raise AssertionError(f"prose overwrite text missing from modal: {prose_modal!r}")
            close_with_escape(page, prose_button, args.timeout_ms)
            if prose_apply_requests:
                raise AssertionError(f"prose import apply ran after Escape close: {prose_apply_requests!r}")

            page.locator(prose_button).click()
            assert_modal_shell(page, "Confirm prose overwrite", ["Cancel", "Overwrite"], args.timeout_ms)
            page.locator('[data-role="modal-primary"]').click()
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            page.wait_for_function("selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'", arg=ROOT_SELECTOR, timeout=args.timeout_ms)
            if len(prose_apply_requests) != 1:
                raise AssertionError(f"prose import apply should be route-owned and confirmed once: {prose_apply_requests!r}")
            prose_request = prose_apply_requests[0]
            if prose_request.get("target_kind") != "moment" or prose_request.get("moment_id") != MOMENT_ID:
                raise AssertionError(f"unexpected prose import apply request: {prose_request!r}")

            page.locator(publication_button).click()
            unpublish_modal = assert_modal_shell(page, "Confirm unpublish", ["Cancel", "Unpublish"], args.timeout_ms)
            if f"Unpublish moment {MOMENT_ID}" not in unpublish_modal["bodyText"]:
                raise AssertionError(f"unpublish preview text missing from modal: {unpublish_modal!r}")
            close_with_cancel(page, publication_button, args.timeout_ms)
            if publication_apply_requests:
                raise AssertionError(f"publication apply ran after cancel action: {publication_apply_requests!r}")

            page.locator(publication_button).click()
            assert_modal_shell(page, "Confirm unpublish", ["Cancel", "Unpublish"], args.timeout_ms)
            page.locator('[data-role="modal-primary"]').click()
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            page.wait_for_function("selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'", arg=ROOT_SELECTOR, timeout=args.timeout_ms)
            if len(publication_apply_requests) != 1:
                raise AssertionError(f"publication apply should be route-owned and confirmed once: {publication_apply_requests!r}")
            publication_request = publication_apply_requests[0]
            if publication_request.get("kind") != "moment" or publication_request.get("action") != "unpublish":
                raise AssertionError(f"unexpected publication apply request: {publication_request!r}")
            if publication_request.get("moment_id") != MOMENT_ID:
                raise AssertionError(f"publication apply lost moment ownership: {publication_request!r}")

            page.locator(delete_button).click()
            delete_modal = assert_modal_shell(page, "Confirm delete", ["Cancel", "Delete"], args.timeout_ms)
            if f"Delete source record {MOMENT_ID}" not in delete_modal["bodyText"]:
                raise AssertionError(f"delete preview text missing from modal: {delete_modal!r}")
            close_with_backdrop(page, delete_button, args.timeout_ms)
            if delete_apply_requests:
                raise AssertionError(f"delete apply ran after backdrop close: {delete_apply_requests!r}")

            page.locator(delete_button).click()
            assert_modal_shell(page, "Confirm delete", ["Cancel", "Delete"], args.timeout_ms)
            page.locator('[data-role="modal-primary"]').click()
            page.wait_for_url("**/studio/catalogue-status/?mode=manage", timeout=args.timeout_ms)
            if len(delete_apply_requests) != 1:
                raise AssertionError(f"delete apply should be route-owned and confirmed once: {delete_apply_requests!r}")
            delete_request = delete_apply_requests[0]
            if delete_request.get("kind") != "moment" or delete_request.get("moment_id") != MOMENT_ID:
                raise AssertionError(f"unexpected delete apply request: {delete_request!r}")

            print(json.dumps({
                "route": attrs,
                "prose_apply_requests": len(prose_apply_requests),
                "publication_apply_requests": len(publication_apply_requests),
                "delete_apply_requests": len(delete_apply_requests),
                "prose_modal": prose_modal,
                "unpublish_modal": unpublish_modal,
                "delete_modal": delete_modal,
            }, sort_keys=True))
        finally:
            browser.close()
            if server is not None:
                server.shutdown()
                server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

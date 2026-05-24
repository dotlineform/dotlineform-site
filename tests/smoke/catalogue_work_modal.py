#!/usr/bin/env python3
"""Smoke-check the catalogue work editor modal composition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from threading import Thread
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Route, TimeoutError as PlaywrightTimeoutError, sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402


ROOT_SELECTOR = "#catalogueWorkRoot"
WORK_ID = "00001"
SERIES_ID = "009"


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
        "route": "catalogue-work",
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


def fulfil_json(route: Route, payload: dict[str, object]) -> None:
    route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))


def modal_shell_state(page) -> dict[str, object]:
    return page.locator('[data-role="studio-modal"]').evaluate(
        """modal => {
            const dialog = modal.querySelector('[role="dialog"]');
            const title = modal.querySelector('.tagStudioModal__title');
            const status = modal.querySelector('.tagStudioModal__status');
            const actionButtons = Array.from(modal.querySelectorAll('.tagStudioModal__actions button'));
            return {
                role: dialog ? dialog.getAttribute('role') : "",
                modal: dialog ? dialog.getAttribute('aria-modal') : "",
                labelledBy: dialog ? dialog.getAttribute('aria-labelledby') : "",
                titleId: title ? title.id : "",
                title: title ? title.textContent.trim() : "",
                dialogClass: dialog ? dialog.className : "",
                actionLabels: actionButtons.map(button => button.textContent.trim()),
                actionRoles: actionButtons.map(button => button.getAttribute('data-role') || ""),
                actionClasses: actionButtons.map(button => button.className),
                activeId: document.activeElement ? document.activeElement.id || "" : "",
                activeRole: document.activeElement ? document.activeElement.getAttribute('data-role') || "" : "",
                statusText: status && !status.hidden ? status.textContent.trim() : "",
                bodyText: modal.textContent || ""
            };
        }"""
    )


def assert_modal_shell(
    page,
    title: str,
    actions: list[str],
    timeout_ms: int,
    *,
    size_class: str = "",
) -> dict[str, object]:
    page.wait_for_selector('[data-role="studio-modal"]', timeout=timeout_ms)
    state = modal_shell_state(page)
    if state["role"] != "dialog" or state["modal"] != "true":
        raise AssertionError(f"modal lacks dialog semantics: {state!r}")
    if not state["labelledBy"] or state["labelledBy"] != state["titleId"]:
        raise AssertionError(f"modal is not labelled by its title: {state!r}")
    if state["title"] != title:
        raise AssertionError(f"unexpected modal title: {state!r}")
    if size_class and size_class not in state["dialogClass"]:
        raise AssertionError(f"modal size class missing: {state!r}")
    if state["actionLabels"] != actions:
        raise AssertionError(f"unexpected modal actions: {state!r}")
    if not all("tagStudio__button--defaultWidth" in value for value in state["actionClasses"]):
        raise AssertionError(f"modal actions are missing default-width buttons: {state!r}")
    return state


def focused_token(page, selector: str) -> str:
    return page.evaluate(
        """selector => {
            const active = document.activeElement;
            if (!active) return "";
            if (selector.startsWith("#")) return active.id || "";
            return active.matches(selector) ? selector : "";
        }""",
        selector,
    )


def assert_focus_returned(page, opener_selector: str) -> None:
    expected = opener_selector.lstrip("#") if opener_selector.startswith("#") else opener_selector
    focused = focused_token(page, opener_selector)
    if focused != expected:
        raise AssertionError(f"modal did not return focus to opener: {focused!r}")


def close_with_escape(page, opener_selector: str, timeout_ms: int, *, expect_focus: bool = True) -> None:
    page.keyboard.press("Escape")
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=timeout_ms)
    page.wait_for_timeout(50)
    if expect_focus:
        assert_focus_returned(page, opener_selector)


def close_with_backdrop(page, opener_selector: str, timeout_ms: int) -> None:
    page.mouse.click(12, 12)
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=timeout_ms)
    page.wait_for_timeout(50)
    assert_focus_returned(page, opener_selector)


def build_preview_payload() -> dict[str, object]:
    return {
        "ok": True,
        "build": {
            "work_ids": [WORK_ID],
            "series_ids": [SERIES_ID],
            "rebuild_search": True,
            "readiness": {
                "items": [
                    {
                        "key": "work_prose",
                        "status": "ready",
                        "title": "work prose",
                        "summary": "Staged prose is ready to import.",
                        "source_path": "var/studio/catalogue/prose/work-00001.md",
                    }
                ]
            },
        },
        "field_plan": {
            "rule_ids": ["work_metadata"],
            "artifacts": ["work_local_public_metadata"],
            "explanations": [
                {
                    "artifact": "work_local_public_metadata",
                    "reason": "title affects the work metadata payload",
                }
            ],
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

    work_record = {
        "work_id": WORK_ID,
        "title": "Smoke work",
        "year": 2026,
        "year_display": "2026",
        "status": "published",
        "published_date": "2026-05-15",
        "series_ids": [SERIES_ID],
        "downloads": [{"filename": "original.pdf", "label": "Original PDF"}],
        "links": [{"url": "https://example.com/original", "label": "Original link"}],
    }
    series_record = {
        "series_id": SERIES_ID,
        "title": "Smoke series",
        "status": "published",
    }
    build_preview_requests: list[dict[str, object]] = []
    prose_apply_requests: list[dict[str, object]] = []
    publication_apply_requests: list[dict[str, object]] = []
    delete_apply_requests: list[dict[str, object]] = []

    def handle_catalogue(route: Route) -> None:
        nonlocal work_record
        request = route.request
        parsed = urlparse(request.url)
        query = parse_qs(parsed.query)
        path = parsed.path.removeprefix("/studio/api")
        if request.method == "GET" and path in {"/health", "/catalogue/health"}:
            fulfil_json(route, {"ok": True})
            return
        if request.method == "GET" and path == "/catalogue/read":
            key = query.get("key", [""])[0]
            if key == "catalogue_lookup_work_search":
                fulfil_json(route, {"items": [{**work_record, "record_hash": "hash-work-current"}]})
                return
            if key == "catalogue_lookup_series_search":
                fulfil_json(route, {"items": [series_record]})
                return
            if key == "catalogue_lookup_work_base":
                fulfil_json(route, {
                    "work": work_record,
                    "record_hash": "hash-work-current",
                    "detail_sections": [],
                })
                return
        if request.method == "POST" and path == "/catalogue/build-preview":
            build_preview_requests.append(request_json(route))
            fulfil_json(route, build_preview_payload())
            return
        if request.method == "POST" and path == "/catalogue/prose/import-preview":
            fulfil_json(route, {
                "ok": True,
                "valid": True,
                "overwrite_required": True,
                "target_path": "_works/00001.md",
                "staging_path": "var/studio/catalogue/prose/work-00001.md",
            })
            return
        if request.method == "POST" and path == "/catalogue/prose/import-apply":
            prose_apply_requests.append(request_json(route))
            fulfil_json(route, {
                "ok": True,
                "target_path": "_works/00001.md",
                "imported_at_utc": "2026-05-15T12:00:00Z",
            })
            return
        if request.method == "POST" and path == "/catalogue/publication-preview":
            fulfil_json(route, {
                "ok": True,
                "preview": {
                    "blocked": False,
                    "blockers": [],
                    "summary": f"Unpublish work {WORK_ID} and clean public output.",
                },
            })
            return
        if request.method == "POST" and path == "/catalogue/publication-apply":
            publication_apply_requests.append(request_json(route))
            work_record = {**work_record, "status": "draft"}
            fulfil_json(route, {
                "ok": True,
                "status": "ok",
                "record": work_record,
                "record_hash": "hash-work-draft",
            })
            return
        if request.method == "POST" and path == "/catalogue/delete-preview":
            fulfil_json(route, {
                "ok": True,
                "preview": {
                    "blocked": False,
                    "blockers": [],
                    "validation_errors": [],
                    "summary": f"Delete source record {WORK_ID} and remove generated work output.",
                },
            })
            return
        if request.method == "POST" and path == "/catalogue/delete-apply":
            delete_apply_requests.append(request_json(route))
            fulfil_json(route, {"ok": True, "deleted": True})
            return
        fulfil_json(route, {"ok": False, "error": f"Unhandled mock route: {request.method} {path}"})

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page_errors: list[str] = []
            console_warnings: list[str] = []
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on("console", lambda message: console_warnings.append(message.text) if message.type in {"error", "warning"} else None)
            page.route(f"{base_url}/studio/api/catalogue/**", handle_catalogue)
            page.goto(route_url(base_url, f"/studio/catalogue-work/?work={WORK_ID}"), wait_until="domcontentloaded")
            attrs = wait_for_studio_route_ready(page, args.timeout_ms)
            assert_ready_contract(attrs)

            add_download_button = "#catalogueWorkNewFileLink"
            add_link_button = "#catalogueWorkNewLinkLink"
            publication_button = "#catalogueWorkPublication"
            delete_button = "#catalogueWorkDelete"
            prose_button = '[data-prose-import="work"]'

            page.locator(prose_button).focus()
            page.locator(prose_button).click()
            prose_modal = assert_modal_shell(page, "Confirm prose overwrite", ["Cancel", "Overwrite"], args.timeout_ms, size_class="tagStudioModal__dialog--compact")
            if "_works/00001.md" not in prose_modal["bodyText"]:
                raise AssertionError(f"prose overwrite text missing from modal: {prose_modal!r}")
            close_with_escape(page, prose_button, args.timeout_ms, expect_focus=False)
            if prose_apply_requests:
                raise AssertionError(f"prose apply ran after Escape close: {prose_apply_requests!r}")

            page.locator(prose_button).focus()
            page.locator(prose_button).click()
            assert_modal_shell(page, "Confirm prose overwrite", ["Cancel", "Overwrite"], args.timeout_ms, size_class="tagStudioModal__dialog--compact")
            page.locator('[data-role="modal-primary"]').click()
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            page.wait_for_function("selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'", arg=ROOT_SELECTOR, timeout=args.timeout_ms)
            if len(prose_apply_requests) != 1 or prose_apply_requests[0].get("target_kind") != "work":
                raise AssertionError(f"prose apply should remain route-owned: {prose_apply_requests!r}")

            page.locator(add_download_button).click()
            try:
                download_modal = assert_modal_shell(page, "Add download", ["Cancel", "Save"], args.timeout_ms)
            except PlaywrightTimeoutError as error:
                button_state = page.locator(add_download_button).evaluate(
                    """button => ({
                        disabled: Boolean(button.disabled),
                        hidden: Boolean(button.hidden),
                        text: button.textContent.trim(),
                        activeId: document.activeElement ? document.activeElement.id || "" : "",
                        filesText: document.querySelector("#catalogueWorkFilesResults")?.textContent || ""
                    })"""
                )
                raise AssertionError({
                    "message": "Add download modal did not open",
                    "button": button_state,
                    "page_errors": page_errors,
                    "console": console_warnings,
                }) from error
            if download_modal["activeId"] != "catalogueWorkDownloadFilename":
                raise AssertionError(f"download modal did not focus first field: {download_modal!r}")
            page.keyboard.press("Shift+Tab")
            if modal_shell_state(page)["activeRole"] != "entry-modal-save":
                raise AssertionError("download modal focus did not wrap backward to Save")
            page.keyboard.press("Tab")
            if modal_shell_state(page)["activeId"] != "catalogueWorkDownloadFilename":
                raise AssertionError("download modal focus did not wrap forward to the first field")
            page.locator('[data-role="entry-modal-save"]').click()
            validation_state = modal_shell_state(page)
            if validation_state["statusText"] != "Each download needs a filename.":
                raise AssertionError(f"download modal validation status missing: {validation_state!r}")
            page.fill("#catalogueWorkDownloadFilename", "smoke.pdf")
            page.fill("#catalogueWorkDownloadLabel", "Smoke PDF")
            page.keyboard.press("Enter")
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            assert_focus_returned(page, add_download_button)
            if "smoke.pdf" not in page.locator("#catalogueWorkFilesResults").inner_text():
                raise AssertionError("download modal did not return the new entry to the route")

            edit_download_button = "[data-download-edit='0']"
            page.locator(edit_download_button).click()
            assert_modal_shell(page, "Edit download", ["Cancel", "Save"], args.timeout_ms)
            close_with_escape(page, edit_download_button, args.timeout_ms)

            delete_download_button = "[data-download-delete='0']"
            page.locator(delete_download_button).click()
            delete_download_modal = assert_modal_shell(page, "Delete download", ["Cancel", "Delete"], args.timeout_ms, size_class="tagStudioModal__dialog--compact")
            if "Original PDF" not in delete_download_modal["bodyText"]:
                raise AssertionError(f"embedded delete text missing from modal: {delete_download_modal!r}")
            close_with_backdrop(page, delete_download_button, args.timeout_ms)

            page.locator(add_link_button).click()
            assert_modal_shell(page, "Add link", ["Cancel", "Save"], args.timeout_ms)
            close_with_backdrop(page, add_link_button, args.timeout_ms)

            page.fill("#catalogueWorkField-title", "Smoke work updated")
            preview_button = '[data-action="preview-build-impact"]'
            page.locator(preview_button).focus()
            page.locator(preview_button).click()
            build_modal = assert_modal_shell(page, "Public update preview", ["Close"], args.timeout_ms, size_class="tagStudioModal__dialog--wide")
            page.wait_for_function(
                "() => document.activeElement && document.activeElement.getAttribute('data-role') === 'modal-cancel'",
                timeout=args.timeout_ms,
            )
            build_modal = modal_shell_state(page)
            if "Changed fields: title, downloads." not in build_modal["bodyText"]:
                raise AssertionError(f"build preview changed-field text missing: {build_modal!r}")
            close_with_escape(page, preview_button, args.timeout_ms)
            field_preview_requests = [
                item for item in build_preview_requests
                if item.get("record_family") == "work" and item.get("changed_fields")
            ]
            if not field_preview_requests or field_preview_requests[-1].get("changed_fields") != ["title", "downloads"]:
                raise AssertionError(f"field-aware build preview request not route-owned: {build_preview_requests!r}")

            page.locator(publication_button).click()
            unpublish_modal = assert_modal_shell(page, "Confirm unpublish", ["Cancel", "Unpublish"], args.timeout_ms, size_class="tagStudioModal__dialog--compact")
            if f"Unpublish work {WORK_ID}" not in unpublish_modal["bodyText"]:
                raise AssertionError(f"unpublish preview text missing from modal: {unpublish_modal!r}")
            close_with_escape(page, publication_button, args.timeout_ms)
            if publication_apply_requests:
                raise AssertionError(f"publication apply ran after Escape close: {publication_apply_requests!r}")

            page.locator(publication_button).click()
            assert_modal_shell(page, "Confirm unpublish", ["Cancel", "Unpublish"], args.timeout_ms, size_class="tagStudioModal__dialog--compact")
            page.locator('[data-role="modal-primary"]').click()
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            page.wait_for_function("selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'", arg=ROOT_SELECTOR, timeout=args.timeout_ms)
            if len(publication_apply_requests) != 1:
                raise AssertionError(f"publication apply should be route-owned and confirmed once: {publication_apply_requests!r}")
            publication_request = publication_apply_requests[0]
            if publication_request.get("kind") != "work" or publication_request.get("action") != "unpublish":
                raise AssertionError(f"unexpected publication apply request: {publication_request!r}")

            page.locator(delete_button).click()
            delete_modal = assert_modal_shell(page, "Confirm delete", ["Cancel", "Delete"], args.timeout_ms, size_class="tagStudioModal__dialog--compact")
            if f"Delete source record {WORK_ID}" not in delete_modal["bodyText"]:
                raise AssertionError(f"delete preview text missing from modal: {delete_modal!r}")
            page.locator('[data-role="modal-primary"]').click()
            page.wait_for_url("**/studio/catalogue-status/?mode=manage", timeout=args.timeout_ms)
            if len(delete_apply_requests) != 1 or delete_apply_requests[0].get("kind") != "work":
                raise AssertionError(f"delete apply should be route-owned and confirmed once: {delete_apply_requests!r}")

            print(json.dumps({
                "route": attrs,
                "build_preview_requests": len(build_preview_requests),
                "prose_apply_requests": len(prose_apply_requests),
                "publication_apply_requests": len(publication_apply_requests),
                "delete_apply_requests": len(delete_apply_requests),
            }, sort_keys=True))
        finally:
            browser.close()
            if server is not None:
                server.shutdown()
                server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

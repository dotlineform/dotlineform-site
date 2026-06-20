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

REPO_ROOT = Path(__file__).resolve().parents[3]
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
            const title = modal.querySelector('.studioModal__title');
            const status = modal.querySelector('.studioModal__status');
            const actionButtons = Array.from(modal.querySelectorAll('.studioModal__actions button'));
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
    if not all("studioUi__button--defaultWidth" in value for value in state["actionClasses"]):
        raise AssertionError(f"modal actions are missing default-width buttons: {state!r}")
    return state


def focused_token(page, selector: str) -> str:
    return page.evaluate(
        """selector => {
            const active = document.activeElement;
            const isPlainIdSelector = /^#[A-Za-z0-9_-]+$/.test(selector);
            if (!active) return "";
            if (isPlainIdSelector) return active.id || "";
            return active.matches(selector) ? selector : "";
        }""",
        selector,
    )


def assert_focus_returned(page, opener_selector: str) -> None:
    expected = opener_selector.lstrip("#") if opener_selector.startswith("#") and " " not in opener_selector else opener_selector
    try:
        page.wait_for_function(
            """selector => {
                const active = document.activeElement;
                const isPlainIdSelector = /^#[A-Za-z0-9_-]+$/.test(selector);
                if (!active) return false;
                if (isPlainIdSelector) return active.id === selector.slice(1);
                return active.matches(selector);
            }""",
            arg=opener_selector,
            timeout=1000,
        )
    except PlaywrightTimeoutError as error:
        focus_state = page.evaluate(
            """selector => {
                const active = document.activeElement;
                const opener = document.querySelector(selector);
                return {
                    activeTag: active ? active.tagName : "",
                    activeId: active ? active.id || "" : "",
                    activeText: active ? active.textContent.trim() : "",
                    activeAction: active ? active.getAttribute("data-record-list-action") || "" : "",
                    openerExists: Boolean(opener),
                    openerDisabled: opener ? Boolean(opener.disabled) : null,
                    openerText: opener ? opener.textContent.trim() : ""
                };
            }""",
            opener_selector,
        )
        raise AssertionError(f"modal did not return focus to opener: {focus_state!r}") from error
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
            "readiness": {"items": []},
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
    detail_sections = [
        {
            "section_id": f"{WORK_ID}-1",
            "section_title": "details",
            "details_subfolder": "details",
            "count": 1,
            "details": [
                {
                    "detail_uid": f"{WORK_ID}-001",
                    "detail_id": "001",
                    "title": "Smoke detail",
                    "project_filename": "detail-001.jpg",
                }
            ],
        }
    ]
    build_preview_requests: list[dict[str, object]] = []
    publication_apply_requests: list[dict[str, object]] = []
    work_delete_apply_requests: list[dict[str, object]] = []
    section_save_requests: list[dict[str, object]] = []
    section_delete_apply_requests: list[dict[str, object]] = []

    def handle_catalogue(route: Route) -> None:
        nonlocal work_record, detail_sections
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
                    "detail_sections": detail_sections,
                })
                return
        if request.method == "POST" and path == "/catalogue/build-preview":
            build_preview_requests.append(request_json(route))
            fulfil_json(route, build_preview_payload())
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
        if request.method == "POST" and path == "/catalogue/work-detail-section/save":
            save_request = request_json(route)
            section_save_requests.append(save_request)
            detail_sections = [
                {
                    **section,
                    "section_title": str(save_request.get("section_title") or section.get("section_title") or ""),
                    **({"detail_sort": "title"} if save_request.get("detail_sort") == "title" else {}),
                }
                if section.get("section_id") == save_request.get("section_id")
                else section
                for section in detail_sections
            ]
            fulfil_json(route, {
                "ok": True,
                "changed": True,
                "section_id": save_request.get("section_id"),
                "section": detail_sections[0],
                "build_requested": True,
            })
            return
        if request.method == "POST" and path == "/catalogue/delete-preview":
            delete_request = request_json(route)
            if delete_request.get("kind") == "work_detail_section":
                fulfil_json(route, {
                    "ok": True,
                    "preview": {
                        "blocked": False,
                        "blockers": [],
                        "validation_errors": [],
                        "summary": f"Delete detail section {WORK_ID}-1, 1 detail record(s), and remove generated detail output.",
                    },
                })
                return
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
            delete_request = request_json(route)
            if delete_request.get("kind") == "work_detail_section":
                section_delete_apply_requests.append(delete_request)
                detail_sections = []
                fulfil_json(route, {"ok": True, "deleted": True})
                return
            work_delete_apply_requests.append(delete_request)
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

            resource_actions = "#catalogueWorkResourcesActions"
            resources_results = "#catalogueWorkResourcesResults"
            add_download_button = f'{resource_actions} [data-record-list-action="new-download"]'
            add_link_button = f'{resource_actions} [data-record-list-action="new-link"]'
            publication_button = "#catalogueWorkPublication"
            delete_button = "#catalogueWorkDelete"

            embedded_section_state = page.evaluate(
                """() => ({
                    filesHeading: Boolean(document.querySelector('#catalogueWorkFilesHeading')),
                    linksHeading: Boolean(document.querySelector('#catalogueWorkLinksHeading')),
                    resourcesMeta: document.querySelector('#catalogueWorkResourcesMeta')?.textContent.trim() || '',
                    addDownloadText: document.querySelector('#catalogueWorkResourcesActions [data-record-list-action="new-download"]')?.textContent.trim() || '',
                    addDownloadLabel: document.querySelector('#catalogueWorkResourcesActions [data-record-list-action="new-download"]')?.getAttribute('aria-label') || '',
                    addLinkText: document.querySelector('#catalogueWorkResourcesActions [data-record-list-action="new-link"]')?.textContent.trim() || '',
                    addLinkLabel: document.querySelector('#catalogueWorkResourcesActions [data-record-list-action="new-link"]')?.getAttribute('aria-label') || '',
                    actionAppearance: Array.from(document.querySelectorAll('#catalogueWorkResourcesActions [data-record-list-action]')).map((button) => button.dataset.appearance).join(',')
                })"""
            )
            if embedded_section_state != {
                "filesHeading": False,
                "linksHeading": False,
                "resourcesMeta": "",
                "addDownloadText": "📄",
                "addDownloadLabel": "Add file",
                "addLinkText": "🔗",
                "addLinkLabel": "Add link",
                "actionAppearance": "icon,icon,icon,icon",
            }:
                raise AssertionError(f"embedded list chrome did not match compact toolbar contract: {embedded_section_state!r}")

            section_delete_button = '#catalogueWorkDetailBrowserSectionActions [data-record-list-action="delete"]'
            section_edit_button = '#catalogueWorkDetailBrowserSectionActions [data-record-list-action="edit"]'
            page.locator(section_edit_button).click()
            try:
                edit_section_modal = assert_modal_shell(page, "Edit detail section", ["Cancel", "Save"], args.timeout_ms)
            except PlaywrightTimeoutError as error:
                section_action_state = page.locator("#catalogueWorkDetailBrowserSectionActions").evaluate(
                    """node => ({
                        text: node.textContent || '',
                        selectedId: document.querySelector('#catalogueWorkDetailBrowserSections')?.dataset.recordListSelectedId || '',
                        editDisabled: Boolean(node.querySelector('[data-record-list-action="edit"]')?.disabled),
                        editLabel: node.querySelector('[data-record-list-action="edit"]')?.getAttribute('aria-label') || '',
                        activeAction: document.activeElement ? document.activeElement.getAttribute('data-record-list-action') || '' : ''
                    })"""
                )
                raise AssertionError({
                    "message": "Section edit modal did not open",
                    "actions": section_action_state,
                    "page_errors": page_errors,
                    "console": console_warnings,
                }) from error
            if edit_section_modal["activeId"] != "catalogueWorkDetailSectionTitle":
                raise AssertionError(f"section edit modal did not focus title field: {edit_section_modal!r}")
            edit_section_fields = page.locator('[data-role="studio-modal"]').evaluate(
                """modal => ({
                    title: modal.querySelector('#catalogueWorkDetailSectionTitle')?.value || '',
                    order: modal.querySelector('#catalogueWorkDetailSectionOrder')?.value || '',
                    orderDisabled: Boolean(modal.querySelector('#catalogueWorkDetailSectionOrder')?.disabled),
                    sort: modal.querySelector('#catalogueWorkDetailSectionSort')?.value || '',
                    sortOptions: Array.from(modal.querySelectorAll('#catalogueWorkDetailSectionSort option')).map(option => option.textContent.trim())
                })"""
            )
            if edit_section_fields != {
                "title": "details",
                "order": "1",
                "orderDisabled": True,
                "sort": "detail_id",
                "sortOptions": ["id", "title"],
            }:
                raise AssertionError(f"section edit modal fields do not match source section: {edit_section_fields!r}")
            page.locator('[data-role="detail-section-modal-save"]').click()
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            page.wait_for_function("selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'", arg=ROOT_SELECTOR, timeout=args.timeout_ms)
            if section_save_requests:
                raise AssertionError(f"unchanged section edit should not call save: {section_save_requests!r}")

            page.locator(section_edit_button).click()
            assert_modal_shell(page, "Edit detail section", ["Cancel", "Save"], args.timeout_ms)
            page.fill("#catalogueWorkDetailSectionTitle", "smoke details")
            page.select_option("#catalogueWorkDetailSectionSort", "title")
            page.locator('[data-role="detail-section-modal-save"]').click()
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            page.wait_for_function("selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'", arg=ROOT_SELECTOR, timeout=args.timeout_ms)
            if section_save_requests != [{
                "work_id": WORK_ID,
                "section_id": f"{WORK_ID}-1",
                "section_title": "smoke details",
                "detail_sort": "title",
            }]:
                raise AssertionError(f"unexpected section save request: {section_save_requests!r}")
            detail_browser_text = page.locator("#catalogueWorkDetailBrowserSections").inner_text()
            if "smoke details" not in detail_browser_text:
                raise AssertionError(f"detail browser did not refresh after section edit: {detail_browser_text!r}")

            page.locator(section_delete_button).click()
            section_delete_modal = assert_modal_shell(page, "Confirm detail section delete", ["Cancel", "Delete"], args.timeout_ms, size_class="studioModal__dialog--compact")
            if f"Delete detail section {WORK_ID}-1" not in section_delete_modal["bodyText"]:
                raise AssertionError(f"section delete preview text missing from modal: {section_delete_modal!r}")
            page.wait_for_function(
                "() => document.activeElement && document.activeElement.getAttribute('data-role') === 'modal-cancel'",
                timeout=args.timeout_ms,
            )
            close_with_escape(page, section_delete_button, args.timeout_ms)
            if section_delete_apply_requests:
                raise AssertionError(f"section delete apply ran after Escape close: {section_delete_apply_requests!r}")

            page.locator(section_delete_button).click()
            assert_modal_shell(page, "Confirm detail section delete", ["Cancel", "Delete"], args.timeout_ms, size_class="studioModal__dialog--compact")
            page.locator('[data-role="modal-primary"]').click()
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            page.wait_for_function("selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'", arg=ROOT_SELECTOR, timeout=args.timeout_ms)
            if len(section_delete_apply_requests) != 1:
                raise AssertionError(f"section delete apply should be route-owned and confirmed once: {section_delete_apply_requests!r}")
            section_delete_request = section_delete_apply_requests[0]
            if section_delete_request.get("kind") != "work_detail_section" or section_delete_request.get("section_id") != f"{WORK_ID}-1":
                raise AssertionError(f"unexpected section delete apply request: {section_delete_request!r}")
            empty_detail_browser = page.locator("#catalogueWorkDetailBrowserSections").inner_text()
            if "No work details for this work." not in empty_detail_browser:
                raise AssertionError(f"detail browser did not hide section UI after last section delete: {empty_detail_browser!r}")
            detail_sections = [
                {
                    "section_id": f"{WORK_ID}-1",
                    "section_title": "details",
                    "details_subfolder": "details",
                    "count": 1,
                    "details": [
                        {
                            "detail_uid": f"{WORK_ID}-001",
                            "detail_id": "001",
                            "title": "Smoke detail",
                            "project_filename": "detail-001.jpg",
                        }
                    ],
                }
            ]
            page.goto(route_url(base_url, f"/studio/catalogue-work/?work={WORK_ID}"), wait_until="domcontentloaded")
            attrs = wait_for_studio_route_ready(page, args.timeout_ms)
            assert_ready_contract(attrs)

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
                        resourcesText: document.querySelector("#catalogueWorkResourcesResults")?.textContent || ""
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
            if "smoke.pdf" not in page.locator(resources_results).inner_text():
                raise AssertionError("download modal did not return the new entry to the route")

            page.locator(f"{resources_results} [data-record-list-record-id='download-0']").click()
            download_list_state = page.locator(resources_results).evaluate(
                """node => ({
                    hasList: Boolean(node.querySelector('[data-record-list-id="catalogueWorkResources"]')),
                    rowCount: node.querySelectorAll('[data-record-list-row="true"]').length,
                    selectedId: node.querySelector('[data-record-list-id="catalogueWorkResources"]')?.dataset.recordListSelectedId || '',
                    selectedRows: node.querySelectorAll('[data-record-list-row="true"][aria-selected="true"]').length,
                    text: node.textContent || ''
                })"""
            )
            if not download_list_state["hasList"] or download_list_state["rowCount"] < 3:
                raise AssertionError(f"resource list did not render through shared record list: {download_list_state!r}")
            if download_list_state["selectedId"] != "download-0" or download_list_state["selectedRows"] != 1:
                raise AssertionError(f"resource list did not expose download row selection: {download_list_state!r}")
            if "Original PDF" not in download_list_state["text"]:
                raise AssertionError(f"resource list lost existing download row content: {download_list_state!r}")

            edit_download_button = '#catalogueWorkResourcesActions [data-record-list-action="edit"]'
            delete_download_button = '#catalogueWorkResourcesActions [data-record-list-action="delete"]'
            action_state = page.locator(resource_actions).evaluate(
                """node => ({
                    editDisabled: Boolean(node.querySelector('[data-record-list-action="edit"]')?.disabled),
                    deleteDisabled: Boolean(node.querySelector('[data-record-list-action="delete"]')?.disabled),
                    editText: node.querySelector('[data-record-list-action="edit"]')?.textContent.trim() || '',
                    deleteText: node.querySelector('[data-record-list-action="delete"]')?.textContent.trim() || '',
                    addFileText: node.querySelector('[data-record-list-action="new-download"]')?.textContent.trim() || '',
                    addLinkText: node.querySelector('[data-record-list-action="new-link"]')?.textContent.trim() || '',
                    editLabel: node.querySelector('[data-record-list-action="edit"]')?.getAttribute('aria-label') || '',
                    deleteLabel: node.querySelector('[data-record-list-action="delete"]')?.getAttribute('aria-label') || '',
                    addFileLabel: node.querySelector('[data-record-list-action="new-download"]')?.getAttribute('aria-label') || '',
                    addLinkLabel: node.querySelector('[data-record-list-action="new-link"]')?.getAttribute('aria-label') || ''
                })"""
            )
            if action_state != {
                "editDisabled": False,
                "deleteDisabled": False,
                "editText": "✏️",
                "deleteText": "🗑️",
                "addFileText": "📄",
                "addLinkText": "🔗",
                "editLabel": "Edit",
                "deleteLabel": "Delete",
                "addFileLabel": "Add file",
                "addLinkLabel": "Add link",
            }:
                raise AssertionError(f"download shared actions did not enable after row selection: {action_state!r}")
            page.locator(edit_download_button).click()
            assert_modal_shell(page, "Edit download", ["Cancel", "Save"], args.timeout_ms)
            close_with_escape(page, edit_download_button, args.timeout_ms, expect_focus=False)

            page.locator(f"{resources_results} [data-record-list-record-id='download-0']").click()
            page.locator(delete_download_button).click()
            delete_download_modal = assert_modal_shell(page, "Delete download", ["Cancel", "Delete"], args.timeout_ms, size_class="studioModal__dialog--compact")
            if "Original PDF" not in delete_download_modal["bodyText"]:
                raise AssertionError(f"embedded delete text missing from modal: {delete_download_modal!r}")
            page.wait_for_function(
                "() => document.activeElement && document.activeElement.getAttribute('data-role') === 'modal-cancel'",
                timeout=args.timeout_ms,
            )
            delete_download_modal = modal_shell_state(page)
            if "studioUi__button--defaultAction" not in delete_download_modal["actionClasses"][0]:
                raise AssertionError(f"embedded delete cancel action is not the default: {delete_download_modal!r}")
            if "studioUi__button--defaultAction" in delete_download_modal["actionClasses"][1]:
                raise AssertionError(f"embedded delete primary action should not be the default: {delete_download_modal!r}")
            page.mouse.click(12, 12)
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            page.wait_for_timeout(50)

            page.locator(add_link_button).click()
            assert_modal_shell(page, "Add link", ["Cancel", "Save"], args.timeout_ms)
            close_with_backdrop(page, add_link_button, args.timeout_ms)

            page.locator(f"{resources_results} [data-record-list-record-id='link-0']").click()
            link_list_state = page.locator(resources_results).evaluate(
                """node => {
                    const labelCell = node.querySelector('[data-record-list-cell="label"]');
                    const targetCell = node.querySelector('[data-record-list-row="true"][data-record-list-record-id="link-0"] [data-record-list-cell="target"]');
                    const link = targetCell ? targetCell.querySelector('a') : null;
                    return {
                        hasList: Boolean(node.querySelector('[data-record-list-id="catalogueWorkResources"]')),
                        rowCount: node.querySelectorAll('[data-record-list-row="true"]').length,
                        selectedId: node.querySelector('[data-record-list-id="catalogueWorkResources"]')?.dataset.recordListSelectedId || '',
                        selectedRows: node.querySelectorAll('[data-record-list-row="true"][aria-selected="true"]').length,
                        labelHasLink: Boolean(labelCell && labelCell.querySelector('a')),
                        linkHref: link ? link.href : '',
                        linkTarget: link ? link.target : '',
                        linkRel: link ? link.rel : '',
                        text: node.textContent || ''
                    };
                }"""
            )
            if not link_list_state["hasList"] or link_list_state["rowCount"] < 1:
                raise AssertionError(f"resource list did not render through shared record list: {link_list_state!r}")
            if link_list_state["selectedId"] != "link-0" or link_list_state["selectedRows"] != 1:
                raise AssertionError(f"resource list did not expose link row selection: {link_list_state!r}")
            if "Original link" not in link_list_state["text"] or "https://example.com/original" not in link_list_state["text"]:
                raise AssertionError(f"resource list lost existing link row content: {link_list_state!r}")
            if link_list_state["labelHasLink"]:
                raise AssertionError(f"link list should keep label cells as plain text: {link_list_state!r}")
            if link_list_state["linkHref"] != "https://example.com/original" or link_list_state["linkTarget"] != "_blank" or link_list_state["linkRel"] != "noopener noreferrer":
                raise AssertionError(f"link list did not render safe external-link attributes: {link_list_state!r}")

            edit_link_button = '#catalogueWorkResourcesActions [data-record-list-action="edit"]'
            delete_link_button = '#catalogueWorkResourcesActions [data-record-list-action="delete"]'
            link_action_state = page.locator(resource_actions).evaluate(
                """node => ({
                    editDisabled: Boolean(node.querySelector('[data-record-list-action="edit"]')?.disabled),
                    deleteDisabled: Boolean(node.querySelector('[data-record-list-action="delete"]')?.disabled),
                    editText: node.querySelector('[data-record-list-action="edit"]')?.textContent.trim() || '',
                    deleteText: node.querySelector('[data-record-list-action="delete"]')?.textContent.trim() || '',
                    addFileText: node.querySelector('[data-record-list-action="new-download"]')?.textContent.trim() || '',
                    addLinkText: node.querySelector('[data-record-list-action="new-link"]')?.textContent.trim() || '',
                    editLabel: node.querySelector('[data-record-list-action="edit"]')?.getAttribute('aria-label') || '',
                    deleteLabel: node.querySelector('[data-record-list-action="delete"]')?.getAttribute('aria-label') || '',
                    addFileLabel: node.querySelector('[data-record-list-action="new-download"]')?.getAttribute('aria-label') || '',
                    addLinkLabel: node.querySelector('[data-record-list-action="new-link"]')?.getAttribute('aria-label') || ''
                })"""
            )
            if link_action_state != {
                "editDisabled": False,
                "deleteDisabled": False,
                "editText": "✏️",
                "deleteText": "🗑️",
                "addFileText": "📄",
                "addLinkText": "🔗",
                "editLabel": "Edit",
                "deleteLabel": "Delete",
                "addFileLabel": "Add file",
                "addLinkLabel": "Add link",
            }:
                raise AssertionError(f"link shared actions did not enable after row selection: {link_action_state!r}")
            page.locator(edit_link_button).click()
            assert_modal_shell(page, "Edit link", ["Cancel", "Save"], args.timeout_ms)
            close_with_escape(page, edit_link_button, args.timeout_ms, expect_focus=False)

            page.locator(f"{resources_results} [data-record-list-record-id='link-0']").click()
            page.locator(delete_link_button).click()
            delete_link_modal = assert_modal_shell(page, "Delete link", ["Cancel", "Delete"], args.timeout_ms, size_class="studioModal__dialog--compact")
            if "Original link" not in delete_link_modal["bodyText"]:
                raise AssertionError(f"link delete text missing from modal: {delete_link_modal!r}")
            page.wait_for_function(
                "() => document.activeElement && document.activeElement.getAttribute('data-role') === 'modal-cancel'",
                timeout=args.timeout_ms,
            )
            delete_link_modal = modal_shell_state(page)
            if "studioUi__button--defaultAction" not in delete_link_modal["actionClasses"][0]:
                raise AssertionError(f"link delete cancel action is not the default: {delete_link_modal!r}")
            if "studioUi__button--defaultAction" in delete_link_modal["actionClasses"][1]:
                raise AssertionError(f"link delete primary action should not be the default: {delete_link_modal!r}")
            page.mouse.click(12, 12)
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            page.wait_for_timeout(50)

            page.locator(publication_button).click()
            unpublish_modal = assert_modal_shell(page, "Confirm unpublish", ["Cancel", "Unpublish"], args.timeout_ms, size_class="studioModal__dialog--compact")
            if f"Unpublish work {WORK_ID}" not in unpublish_modal["bodyText"]:
                raise AssertionError(f"unpublish preview text missing from modal: {unpublish_modal!r}")
            close_with_escape(page, publication_button, args.timeout_ms)
            if publication_apply_requests:
                raise AssertionError(f"publication apply ran after Escape close: {publication_apply_requests!r}")

            page.locator(publication_button).click()
            assert_modal_shell(page, "Confirm unpublish", ["Cancel", "Unpublish"], args.timeout_ms, size_class="studioModal__dialog--compact")
            page.locator('[data-role="modal-primary"]').click()
            page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=args.timeout_ms)
            page.wait_for_function("selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'", arg=ROOT_SELECTOR, timeout=args.timeout_ms)
            if len(publication_apply_requests) != 1:
                raise AssertionError(f"publication apply should be route-owned and confirmed once: {publication_apply_requests!r}")
            publication_request = publication_apply_requests[0]
            if publication_request.get("kind") != "work" or publication_request.get("action") != "unpublish":
                raise AssertionError(f"unexpected publication apply request: {publication_request!r}")

            page.locator(delete_button).click()
            delete_modal = assert_modal_shell(page, "Confirm delete", ["Cancel", "Delete"], args.timeout_ms, size_class="studioModal__dialog--compact")
            if f"Delete source record {WORK_ID}" not in delete_modal["bodyText"]:
                raise AssertionError(f"delete preview text missing from modal: {delete_modal!r}")
            page.wait_for_function(
                "() => document.activeElement && document.activeElement.getAttribute('data-role') === 'modal-cancel'",
                timeout=args.timeout_ms,
            )
            delete_modal = modal_shell_state(page)
            if "studioUi__button--defaultAction" not in delete_modal["actionClasses"][0]:
                raise AssertionError(f"delete cancel action is not the default: {delete_modal!r}")
            if "studioUi__button--defaultAction" in delete_modal["actionClasses"][1]:
                raise AssertionError(f"delete primary action should not be the default: {delete_modal!r}")
            page.locator('[data-role="modal-primary"]').click()
            page.wait_for_url("**/studio/catalogue-status/", timeout=args.timeout_ms)
            if len(work_delete_apply_requests) != 1 or work_delete_apply_requests[0].get("kind") != "work":
                raise AssertionError(f"delete apply should be route-owned and confirmed once: {work_delete_apply_requests!r}")

            print(json.dumps({
                "route": attrs,
                "build_preview_requests": len(build_preview_requests),
                "publication_apply_requests": len(publication_apply_requests),
                "section_delete_apply_requests": len(section_delete_apply_requests),
                "delete_apply_requests": len(work_delete_apply_requests),
            }, sort_keys=True))
        finally:
            browser.close()
            if server is not None:
                server.shutdown()
                server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

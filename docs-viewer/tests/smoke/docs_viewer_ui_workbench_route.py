#!/usr/bin/env python3
"""Smoke-check the Admin-owned Docs Viewer UI Workbench and every registered specimen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlparse
import urllib.request

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "admin-app" / "app" / "server" / "admin_app"))

from admin_app_server import AdminAppServer  # noqa: E402
from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


EXPECTED_PACKS = [
    {
        "app_id": "docs-viewer",
        "entrypoint": "/docs-viewer/tests/workbench/docs-viewer-workbench-registry.js",
        "label": "Docs Viewer",
        "route_owner": "admin",
    }
]


def start_admin() -> tuple[AdminAppServer, str]:
    server = AdminAppServer(("127.0.0.1", 0), REPO_ROOT)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def read_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8")


def read_status(url: str) -> int:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status
    except HTTPError as error:
        return error.code


def assert_route_contracts(admin_url: str) -> None:
    admin_config = json.loads(read_text(f"{admin_url}/admin/runtime-config.json"))
    workbench_route = admin_config["app"]["routes"].get("admin_ui_workbench", {})
    if workbench_route.get("path") != "/admin/ui-workbench/":
        raise AssertionError(f"Admin runtime config is missing UI Workbench: {workbench_route!r}")
    packs = admin_config["app"].get("workbench", {}).get("packs", [])
    if packs != EXPECTED_PACKS:
        raise AssertionError(f"Admin UI Workbench pack registry changed: {packs!r}")

    admin_html = read_text(f"{admin_url}/admin/ui-workbench/")
    frame_html = read_text(
        f"{admin_url}/admin/app/frontend/routes/admin-ui-workbench-frame.html"
    )
    registry_module = read_text(
        f"{admin_url}/docs-viewer/tests/workbench/docs-viewer-workbench-registry.js"
    )
    if "data-admin-route-outlet" not in admin_html:
        raise AssertionError("Admin UI Workbench did not use the registered Admin shell")
    if "admin-ui-workbench-frame.js" not in frame_html:
        raise AssertionError("Admin did not serve its Workbench specimen frame")
    if "docsViewerWorkbenchPackRecord" not in registry_module:
        raise AssertionError("Admin did not serve the Docs Viewer-owned specimen pack")
    if read_status(f"{admin_url}/docs/ui-workbench/") != 404:
        raise AssertionError("The retired Docs Viewer Workbench route was still served by Admin")
    if read_status(f"{admin_url}/shared/ui-workbench/workbench-channel.js") != 404:
        raise AssertionError("The retired cross-service Workbench protocol was still served")


def workbench_pack(page: Page) -> dict[str, object]:
    return page.evaluate(
        """async () => {
          const registry = await import(
            '/docs-viewer/tests/workbench/docs-viewer-workbench-registry.js'
          );
          registry.validateDocsViewerWorkbenchRegistry();
          registry.validateDocsViewerWorkbenchReviewRecipes();
          return registry.docsViewerWorkbenchPackRecord();
        }"""
    )


def wait_for_mount(
    page: Page,
    specimen_id: str,
    comparison_specimen_id: str,
    timeout_ms: int,
) -> None:
    page.wait_for_function(
        """({primary, comparison}) => {
          const root = document.querySelector('#adminUiWorkbenchRoot');
          return root?.dataset.adminSpecimenMounted === primary
            && (root?.dataset.adminCompareSpecimenMounted || '') === comparison
            && root?.dataset.adminBusy === 'false';
        }""",
        arg={"primary": specimen_id, "comparison": comparison_specimen_id},
        timeout=timeout_ms,
    )
    page.wait_for_timeout(50)


def select_exact_specimen(
    page: Page,
    record: dict[str, object],
    timeout_ms: int,
) -> None:
    page.locator("#adminUiWorkbenchSpecimen").select_option(str(record["id"]))
    wait_for_mount(page, str(record["id"]), "", timeout_ms)


def assert_single_specimen_controls(page: Page) -> None:
    if not page.locator("#adminUiWorkbenchAppField").is_hidden():
        raise AssertionError("The one-pack Workbench exposed an unnecessary app selector")
    if page.locator("#adminUiWorkbenchSpecimen").is_disabled():
        raise AssertionError("The exact specimen control did not become ready")
    if page.locator("#adminUiWorkbenchRecipe").is_disabled():
        raise AssertionError("The named review recipe control did not become ready")
    for retired_selector in (
        "#adminUiWorkbenchFamily",
        "#adminUiWorkbenchState",
        "#adminUiWorkbenchCompare",
        "#adminUiWorkbenchOpenPack",
        "#adminUiWorkbenchFrame",
    ):
        if page.locator(retired_selector).count():
            raise AssertionError(f"Retired Workbench control remains: {retired_selector}")


def assert_recipe(
    page: Page,
    recipe: dict[str, object],
    timeout_ms: int,
) -> None:
    recipe_id = str(recipe["id"])
    primary_id = str(recipe["primarySpecimenId"])
    comparison_id = str(recipe["comparisonSpecimenId"])
    page.locator("#adminUiWorkbenchRecipe").select_option(recipe_id)

    if recipe["mode"] == "side-by-side":
        wait_for_mount(page, primary_id, comparison_id, timeout_ms)
        if page.locator("#adminUiWorkbenchComparisonStage").is_hidden():
            raise AssertionError(f"Side-by-side recipe did not show B: {recipe_id}")
        if not page.locator("#adminUiWorkbenchRecipeStepField").is_hidden():
            raise AssertionError(f"Side-by-side recipe exposed sequential controls: {recipe_id}")
    else:
        wait_for_mount(page, primary_id, "", timeout_ms)
        if not page.locator("#adminUiWorkbenchComparisonStage").is_hidden():
            raise AssertionError(f"Sequential recipe rendered simultaneous panels: {recipe_id}")
        if page.locator("#adminUiWorkbenchRecipeStepField").is_hidden():
            raise AssertionError(f"Sequential recipe did not expose its named specimens: {recipe_id}")
        page.locator("#adminUiWorkbenchRecipeStep").select_option("comparison")
        wait_for_mount(page, comparison_id, "", timeout_ms)

    if page.locator("#adminUiWorkbenchRecipeQuestion").inner_text().strip() != str(
        recipe["question"]
    ):
        raise AssertionError(f"Recipe question was not projected: {recipe_id}")
    dimensions = page.locator("#adminUiWorkbenchRecipeDimensions").inner_text()
    if not all(str(value) in dimensions for value in recipe["dimensions"]):
        raise AssertionError(f"Recipe dimensions were not projected: {recipe_id}")


def run_browser_smoke(admin_url: str, timeout_ms: int) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        console_errors: list[str] = []
        page_errors: list[str] = []
        write_requests: list[str] = []
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error"
            else None,
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on(
            "request",
            lambda request: write_requests.append(
                f"{request.method} {urlparse(request.url).path}"
            )
            if request.method not in {"GET", "HEAD", "OPTIONS"}
            else None,
        )

        page.goto(f"{admin_url}/admin/ui-workbench/", wait_until="domcontentloaded")
        wait_for_route_ready(
            page,
            "#adminUiWorkbenchRoot",
            "data-admin-ready",
            "data-admin-busy",
            timeout_ms,
        )
        page.wait_for_function(
            """() => Boolean(
              document.querySelector('#adminUiWorkbenchRoot')?.dataset.adminSpecimenMounted
            )""",
            timeout=timeout_ms,
        )

        pack = workbench_pack(page)
        records = pack.get("specimens", [])
        recipes = pack.get("recipes", [])
        if not isinstance(records, list) or not records:
            raise AssertionError(f"Docs Viewer Workbench registry is empty: {records!r}")
        if not isinstance(recipes, list) or not recipes:
            raise AssertionError(f"Docs Viewer Workbench recipes are missing: {recipes!r}")
        if len({str(record["id"]) for record in records}) != len(records):
            raise AssertionError(f"Docs Viewer Workbench registry contains duplicate ids: {records!r}")
        if any("comparisonGroup" in record for record in records):
            raise AssertionError("Specimens still encode implicit comparison groups")

        assert_single_specimen_controls(page)
        for record in records:
            select_exact_specimen(page, record, timeout_ms)

        for recipe in recipes:
            assert_recipe(page, recipe, timeout_ms)

        side_by_side = next(
            recipe for recipe in recipes if recipe["mode"] == "side-by-side"
        )
        page.locator("#adminUiWorkbenchRecipe").select_option(str(side_by_side["id"]))
        page.locator("#adminUiWorkbenchTheme").click()
        wait_for_mount(
            page,
            str(side_by_side["primarySpecimenId"]),
            str(side_by_side["comparisonSpecimenId"]),
            timeout_ms,
        )
        if page.locator("#adminUiWorkbenchTheme").get_attribute("data-value") != "dark":
            raise AssertionError("Theme toggle did not project dark")
        page.locator("#adminUiWorkbenchViewport").click()
        wait_for_mount(
            page,
            str(side_by_side["primarySpecimenId"]),
            str(side_by_side["comparisonSpecimenId"]),
            timeout_ms,
        )
        if page.locator("#adminUiWorkbenchViewport").get_attribute("data-value") != "narrow":
            raise AssertionError("Viewport toggle did not project narrow")
        if page.locator(
            '.adminWorkbench__frameShell[data-workbench-viewport="narrow"]'
        ).count() != 2:
            raise AssertionError("Narrow viewport was not projected to both comparison panels")
        frame_sources = page.locator(".adminWorkbench__specimenFrame").evaluate_all(
            "frames => frames.filter((frame) => frame.src).map((frame) => frame.src)"
        )
        if len(frame_sources) != 2 or any("theme=dark" not in source for source in frame_sources):
            raise AssertionError(f"Dark theme was not projected to both frames: {frame_sources!r}")

        route_state = page.locator("#adminUiWorkbenchRoot").evaluate(
            """root => ({
              ready: root.dataset.adminReady || '',
              busy: root.dataset.adminBusy || '',
              mode: root.dataset.adminMode || '',
              service: root.dataset.adminService || '',
              mounted: root.dataset.adminSpecimenMounted || '',
              compareMounted: root.dataset.adminCompareSpecimenMounted || ''
            })"""
        )
        if (
            route_state["ready"] != "true"
            or route_state["busy"] != "false"
            or route_state["service"] != "available"
            or not route_state["mounted"]
            or not route_state["compareMounted"]
        ):
            raise AssertionError(f"Admin UI Workbench route state is incomplete: {route_state!r}")

        browser.close()

    if write_requests:
        raise AssertionError(f"UI Workbench issued write requests: {write_requests!r}")
    if console_errors:
        raise AssertionError(f"UI Workbench console errors: {console_errors!r}")
    if page_errors:
        raise AssertionError(f"UI Workbench page errors: {page_errors!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=20_000)
    args = parser.parse_args(argv)

    admin_server, admin_url = start_admin()
    try:
        assert_route_contracts(admin_url)
        run_browser_smoke(admin_url, args.timeout_ms)
    finally:
        admin_server.shutdown()
        admin_server.server_close()
    print("Docs Viewer UI Workbench route OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

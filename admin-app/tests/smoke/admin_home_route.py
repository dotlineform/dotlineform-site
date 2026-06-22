#!/usr/bin/env python3
"""Smoke-check the local Admin home route."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from threading import Thread
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
ADMIN_SERVER_DIR = REPO_ROOT / "admin-app" / "app" / "server" / "admin_app"
for path in (REPO_ROOT, ADMIN_SERVER_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from admin_app_server import AdminAppServer  # noqa: E402


def start_server() -> tuple[AdminAppServer, str]:
    server = AdminAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def read_text(url: str) -> str:
    with urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8")


def main() -> int:
    server, base_url = start_server()
    try:
        health = json.loads(read_text(f"{base_url}/health"))
        if health != {"app": "admin", "status": "ok"}:
            raise AssertionError(f"unexpected Admin health payload: {health!r}")

        runtime = json.loads(read_text(f"{base_url}/admin/runtime-config.json"))
        if runtime["app"]["runtime"]["routes"]["home"] != "/admin/":
            raise AssertionError("Admin runtime config did not expose /admin/ home route")
        home_view = next(
            (view for view in runtime["app"]["runtime"]["views"] if view.get("id") == "admin_home"),
            None,
        )
        if not home_view or home_view.get("template") != "/admin/app/frontend/routes/admin-home.html":
            raise AssertionError(f"Admin runtime config did not expose the home template: {home_view!r}")
        if home_view.get("shell_type") != "html-template":
            raise AssertionError(f"Admin runtime config did not expose the home shell type: {home_view!r}")

        html = read_text(f"{base_url}/admin/")
        expected = [
            "dotlineform admin",
            "data-admin-theme-toggle",
            "/admin/app/assets/css/admin.css",
            "/admin/app/frontend/js/admin-app.js",
            "data-admin-route-outlet",
        ]
        missing = [text for text in expected if text not in html]
        if missing:
            raise AssertionError(f"Admin home shell missing expected content: {missing!r}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.goto(f"{base_url}/admin/", wait_until="domcontentloaded")
            if page.locator("[data-admin-route-outlet]").count() != 1:
                raise AssertionError("Admin home did not render the static Admin shell outlet")
            root = page.locator("[data-admin-home]")
            expect(root).to_have_attribute("data-admin-ready", "true", timeout=10_000)
            for href in ["/admin/audits/", "/admin/checks/", "/admin/activity/", "/admin/testing/"]:
                expect(page.locator(f'a.studioHomeLinks__pill[href="{href}"]')).to_be_visible(timeout=10_000)
            theme_toggle = page.locator("[data-admin-theme-toggle]")
            if theme_toggle.count() != 1:
                raise AssertionError("Admin home did not expose exactly one theme toggle")
            browser.close()

        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")

        testing_html = read_text(f"{base_url}/admin/testing/")
        if "data-admin-route-outlet" not in testing_html or "/admin/app/frontend/js/admin-app.js" not in testing_html:
            raise AssertionError("Admin testing route did not render the static Admin shell")
        testing_runs = json.loads(read_text(f"{base_url}/admin/api/testing/runs"))
        if testing_runs.get("runs_root") != "var/admin/test-runs":
            raise AssertionError(f"unexpected Admin testing runs payload: {testing_runs!r}")
    finally:
        server.shutdown()
        server.server_close()

    print(json.dumps({"ok": True, "base_url": base_url}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

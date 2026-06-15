#!/usr/bin/env python3
"""Smoke-check the local Admin home route."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from threading import Thread
from urllib.request import urlopen


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

        html = read_text(f"{base_url}/admin/")
        expected = [
            "dotlineform admin",
            'href="/admin/audits/"',
            'href="/admin/checks/"',
            'href="/admin/activity/"',
            'href="/admin/testing/"',
            'class="studioHomeLinks__pill"',
            "data-admin-theme-toggle",
            "/admin/app/assets/css/admin.css",
            "/admin/app/frontend/js/admin-theme.js",
            "/admin/app/frontend/js/admin-home.js",
        ]
        missing = [text for text in expected if text not in html]
        if missing:
            raise AssertionError(f"Admin home missing expected content: {missing!r}")

        testing_html = read_text(f"{base_url}/admin/testing/")
        if "Admin test runs" not in testing_html or "/admin/app/frontend/js/admin-testing.js" not in testing_html:
            raise AssertionError("Admin testing route did not render the testing shell")
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

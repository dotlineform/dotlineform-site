#!/usr/bin/env python3
"""Smoke-check the local Studio risk route shell."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import urllib.request
from pathlib import Path
from threading import Thread

from playwright.sync_api import expect, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402


DELETE_FIXTURE_RUN_ID = "risk-route-smoke-delete-snapshot"


def start_server() -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def write_delete_fixture() -> Path:
    run_dir = REPO_ROOT / "var" / "studio" / "risk" / "runs" / DELETE_FIXTURE_RUN_ID
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    created_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (run_dir / "manifest.json").write_text(
        json.dumps({"run_id": DELETE_FIXTURE_RUN_ID, "app": "docs-viewer", "area": "runtime", "created_at_utc": created_at}),
        encoding="utf-8",
    )
    (run_dir / "summary.json").write_text(
        json.dumps({"run_id": DELETE_FIXTURE_RUN_ID, "app": "docs-viewer", "area": "runtime", "status": "passed", "warnings": [], "evidence": []}),
        encoding="utf-8",
    )
    (run_dir / "summary.md").write_text("# Smoke delete snapshot\n", encoding="utf-8")
    return run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    delete_fixture_run_dir = write_delete_fixture()
    server, base_url = start_server()
    try:
        with urllib.request.urlopen(f"{base_url}/studio/runtime-config.json", timeout=10) as response:
            runtime_config = json.loads(response.read().decode("utf-8"))
        runtime_views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
        runtime_by_id = {view.get("id"): view for view in runtime_views if isinstance(view, dict)}
        runtime_view = runtime_by_id.get("studio_risk")
        if not runtime_view or runtime_view.get("path") != "/studio/risk/?mode=manage":
            raise AssertionError(f"runtime config missing studio_risk: {runtime_views!r}")
        risk_api = runtime_config.get("app", {}).get("runtime", {}).get("services", {}).get("risk", {})
        if risk_api.get("runs") != "/studio/api/risk/runs":
            raise AssertionError(f"runtime config missing local risk API: {risk_api!r}")

        with urllib.request.urlopen(f"{base_url}/studio/api/risk/producers", timeout=10) as response:
            producers_payload = json.loads(response.read().decode("utf-8"))
        if not producers_payload.get("ok") or not any(
            producer.get("producer_id") == "runtime-checks"
            for producer in producers_payload.get("producers", [])
            if isinstance(producer, dict)
        ):
            raise AssertionError(f"local risk API returned unexpected payload: {producers_payload!r}")

        with urllib.request.urlopen(f"{base_url}/studio/risk/?mode=manage", timeout=10) as response:
            bootstrap_html = response.read().decode("utf-8")
        if 'id="studioApp"' not in bootstrap_html or "studio-app.js" not in bootstrap_html:
            raise AssertionError("risk should be served through the JavaScript Studio app bootstrap")
        if "studioRiskRoot" in bootstrap_html:
            raise AssertionError("risk route body should be rendered by JavaScript, not Python")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            console_errors: list[str] = []
            page_errors: list[str] = []
            viewports = (
                ("desktop", {"width": 1280, "height": 900}),
                ("mobile", {"width": 390, "height": 844}),
            )
            for label, viewport in viewports:
                page = browser.new_page(viewport=viewport)
                page.on("console", lambda message, current_label=label: console_errors.append(f"{current_label}: {message.text}") if message.type == "error" else None)
                page.on("pageerror", lambda error, current_label=label: page_errors.append(f"{current_label}: {error}"))
                page.goto(f"{base_url}/studio/risk/?mode=manage", wait_until="domcontentloaded")
                root = page.locator("#studioRiskRoot")
                expect(root).to_be_visible(timeout=10_000)
                expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
                expect(root).to_have_attribute("data-studio-service", "available", timeout=10_000)
                expect(page.locator("#studioRiskRun")).to_be_enabled(timeout=10_000)
                expect(page.locator("#studioRiskApp")).to_have_value("docs-viewer")
                expect(page.locator("#studioRiskArea")).to_have_value("runtime")

                doc_link_count = page.locator(".studioLayout__docLink").count()
                if doc_link_count:
                    raise AssertionError("risk still renders header doc pill")
                if page.locator('.site-nav [data-studio-navigate="studio_risk"]').count():
                    raise AssertionError("risk should not appear as a top-nav item")

                if label == "desktop":
                    delete_button = page.locator(f'[data-risk-run-delete="{DELETE_FIXTURE_RUN_ID}"]')
                    expect(delete_button).to_be_visible(timeout=10_000)
                    page.once("dialog", lambda dialog: dialog.accept())
                    delete_button.click()
                    expect(page.locator("#studioRiskStatus")).to_contain_text("deleted", timeout=10_000)
                    expect(page.locator(f'[data-risk-run-delete="{DELETE_FIXTURE_RUN_ID}"]')).to_have_count(0, timeout=10_000)
                    if delete_fixture_run_dir.exists():
                        raise AssertionError(f"delete fixture still exists: {delete_fixture_run_dir}")

                    page.locator("#studioRiskDryRun").check()
                    page.locator("#studioRiskRunId").fill("risk-route-smoke-dry-run")
                    page.locator("#studioRiskRun").click()
                    expect(page.locator("#studioRiskStatus")).to_contain_text("completed", timeout=10_000)
                    expect(root).to_have_attribute("data-studio-busy", "false", timeout=10_000)
                page.close()
            browser.close()

        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Studio risk route OK: {base_url}/studio/risk/?mode=manage")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())

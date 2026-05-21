#!/usr/bin/env python3
"""Smoke-check shared Catalogue editor action workflow JavaScript helpers."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


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


def assert_action_workflow_helpers(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/assets/studio/js/catalogue-editor-action-workflow.js');
            const unchanged = module.resolveCatalogueSaveBuildOutcome({
                response: { changed: false, saved_at_utc: '2026-05-21T10:00:00Z' },
                isPublished: true
            });
            const unpublished = module.resolveCatalogueSaveBuildOutcome({
                response: { changed: true, saved_at_utc: '2026-05-21T10:01:00Z' },
                isPublished: false
            });
            const pending = module.resolveCatalogueSaveBuildOutcome({
                response: {
                    changed: true,
                    saved_at_utc: '2026-05-21T10:02:00Z',
                    build_targets: [{ work_id: '001' }]
                },
                isPublished: true,
                buildTargets: [{ work_id: '001' }]
            });
            const applied = module.resolveCatalogueSaveBuildOutcome({
                response: {
                    changed: true,
                    saved_at_utc: '2026-05-21T10:03:00Z',
                    build_requested: true,
                    build: { ok: true, completed_at_utc: '2026-05-21T10:04:00Z' }
                },
                isPublished: true
            });
            const failed = module.resolveCatalogueSaveBuildOutcome({
                response: {
                    changed: true,
                    saved_at_utc: '2026-05-21T10:05:00Z',
                    build_requested: true,
                    build: {
                        ok: false,
                        error: 'build failed',
                        remaining_targets: [{ work_id: '002' }]
                    }
                },
                isPublished: true,
                fallbackBuildTargets: [{ work_id: 'fallback' }]
            });
            const preview = module.extractCatalogueActionPreview({
                preview: { blocked: true, blockers: ['Blocked by parent status.'] }
            });
            const publicationBlocker = module.getCataloguePreviewBlocker(preview, {
                fallback: 'Publication change is blocked.'
            });
            const deleteBlocker = module.getCataloguePreviewBlocker({
                validation_errors: ['Delete requires removing members first.']
            }, {
                includeValidationErrors: true,
                fallback: 'Delete is blocked.'
            });
            const noBlocker = module.getCataloguePreviewBlocker({
                blocked: false,
                blockers: [],
                validation_errors: ['ignored']
            });
            await Promise.all([
                import('/assets/studio/js/catalogue-work-actions.js'),
                import('/assets/studio/js/catalogue-work-detail-actions.js'),
                import('/assets/studio/js/catalogue-series-actions.js'),
                import('/assets/studio/js/catalogue-moment-actions.js')
            ]);
            return {
                unchanged,
                unpublished,
                pending,
                applied,
                failed,
                publicationBlocker,
                deleteBlocker,
                noBlocker,
                actionImports: true
            };
        }"""
    )
    assert result["unchanged"]["kind"] == "unchanged"
    assert result["unchanged"]["rebuildPending"] is False
    assert result["unpublished"]["kind"] == "saved_unpublished"
    assert result["unpublished"]["rebuildPending"] is False
    assert result["pending"]["kind"] == "saved"
    assert result["pending"]["rebuildPending"] is True
    assert result["pending"]["buildTargets"][0]["work_id"] == "001"
    assert result["applied"]["kind"] == "saved_and_updated"
    assert result["applied"]["stamp"] == "2026-05-21T10:04:00Z"
    assert result["failed"]["kind"] == "saved_update_failed"
    assert result["failed"]["error"] == "build failed"
    assert result["failed"]["buildTargets"][0]["work_id"] == "002"
    assert result["publicationBlocker"] == "Blocked by parent status."
    assert result["deleteBlocker"] == "Delete requires removing members first."
    assert result["noBlocker"] == ""
    assert result["actionImports"] is True


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            assert_action_workflow_helpers(page)
            browser.close()
            if errors:
                raise AssertionError(f"page errors during Catalogue action workflow module smoke: {errors!r}")
    finally:
        server.shutdown()
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".", help="Site root to serve for module imports.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(Path(args.site_root))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Smoke-check focused Docs Import collection preview and decision ownership."""

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
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_collection_controller(page: Page, base_url: str) -> None:
    requests: list[dict[str, object]] = []

    def fulfill_collection_preview(route) -> None:
        request_body = route.request.post_data_json
        requests.append(request_body)
        if request_body.get("preview_only") is False:
            route.fulfill(
                status=200,
                content_type="application/json",
                body='''{
                  "ok": true,
                  "collection": true,
                  "source_format": "data_sharing_documents",
                  "scope": "library",
                  "staged_filename": "reviewed.jsonl",
                  "preview_only": false,
                  "confirmed": true,
                  "outcome": "completed",
                  "counts": {"created": 0, "overwritten": 3, "skipped": 0, "failed": 0, "not_attempted": 0},
                  "records": [
                    {"record_index": 0, "doc_id": "alpha", "title": "Alpha", "status": "overwritten", "warnings": []},
                    {"record_index": 1, "doc_id": "beta", "title": "Beta", "status": "overwritten", "warnings": []},
                    {"record_index": 2, "doc_id": "gamma", "title": "Gamma", "status": "overwritten", "warnings": []}
                  ],
                  "warnings": [],
                  "report_path": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/results/result.md"
                }''',
            )
            return
        route.fulfill(
            status=200,
            content_type="application/json",
            body='''{
              "ok": true,
              "collection": true,
              "source_format": "data_sharing_documents",
              "preview_only": true,
              "requires_decisions": true,
              "ready_for_confirmation": false,
              "package": {"export_id": "ds_20260712T170000Z", "source_sha256": "abc123"},
              "counts": {"records": 3, "creates": 0, "collisions": 3, "record_errors": 0, "media_plans": 0},
              "records": [
                {"record_index": 0, "doc_id": "alpha", "title": "Alpha", "action": "decision-required", "decision_kind": "collision", "allowed_actions": ["overwrite", "skip", "cancel"], "collision": {"exists": true, "doc_id": "alpha"}, "parent": {}, "media_plans": [], "warnings": [], "errors": []},
                {"record_index": 1, "doc_id": "beta", "title": "Beta", "action": "decision-required", "decision_kind": "collision", "allowed_actions": ["overwrite", "skip", "cancel"], "collision": {"exists": true, "doc_id": "beta"}, "parent": {}, "media_plans": [], "warnings": [], "errors": []},
                {"record_index": 2, "doc_id": "gamma", "title": "Gamma", "action": "decision-required", "decision_kind": "collision", "allowed_actions": ["overwrite", "skip", "cancel"], "collision": {"exists": true, "doc_id": "gamma"}, "parent": {}, "media_plans": [], "warnings": [], "errors": []}
              ],
              "blockers": [],
              "warnings": []
            }''',
        )

    page.route(
        "**/docs/import-source",
        fulfill_collection_preview,
    )
    result = page.evaluate(
        """async (baseUrl) => {
          document.body.innerHTML = '<div id="host"></div><p id="status"></p>';
          const module = await import('/docs-viewer/runtime/js/import/docs-import-collection-controller.js');
          let terminalResultCount = 0;
          const controller = module.createDocsImportCollectionController({
            host: document.getElementById('host'),
            statusNode: document.getElementById('status'),
            onTerminalResult: () => { terminalResultCount += 1; }
          });
          await controller.preview({
            file: { filename: 'reviewed.jsonl', source_format: 'data_sharing_documents' },
            scope: 'library',
            managementBaseUrl: baseUrl
          });
          document.querySelector('[data-collection-decision="overwrite"]').click();
          const afterFirst = controller.snapshot();
          document.querySelector('[data-collection-apply-all]').checked = true;
          document.querySelector('[data-collection-decision="overwrite"]').click();
          const readySnapshot = controller.snapshot();
          const readyStatus = document.getElementById('status').textContent;
          await controller.confirmApply();
          const resultSnapshot = controller.snapshot();
          const resultReportVisible = document.getElementById('host').textContent.includes('results/result.md');
          controller.reset({ active: true });
          await controller.preview({
            file: { filename: 'reviewed.jsonl', source_format: 'data_sharing_documents' },
            scope: 'library',
            managementBaseUrl: baseUrl
          });
          document.querySelector('[data-collection-decision="cancel"]').click();
          return {
            afterFirst,
            readySnapshot,
            readyStatus,
            resultSnapshot,
            resultReportVisible,
            terminalResultCount,
            cancelledSnapshot: controller.snapshot(),
            cancelDecisionVisible: Boolean(document.querySelector('[data-collection-decision]')),
            recordCount: document.querySelectorAll('.docsViewerImport__collectionRecords > li').length
          };
        }""",
        base_url,
    )
    if result["readySnapshot"]["phase"] != "confirmation":
        raise AssertionError(f"collection decisions did not remain controller-owned: {result!r}")
    if result["afterFirst"]["phase"] != "decision" or result["afterFirst"]["decisions"] != {"0": "overwrite"}:
        raise AssertionError(f"unchecked apply-to-all changed remaining collisions: {result!r}")
    if result["readySnapshot"]["decisions"] != {"0": "overwrite", "1": "overwrite", "2": "overwrite"}:
        raise AssertionError(f"apply-to-all did not resolve collision decisions: {result!r}")
    if result["recordCount"] != 3 or "ready for confirmation" not in result["readyStatus"]:
        raise AssertionError(f"collection view projection failed: {result!r}")
    if result["resultSnapshot"]["phase"] != "result" or not result["resultReportVisible"]:
        raise AssertionError(f"confirmed apply result did not remain collection-controller owned: {result!r}")
    if result["terminalResultCount"] != 1:
        raise AssertionError(f"confirmed apply did not signal one terminal result: {result!r}")
    if result["cancelledSnapshot"]["phase"] != "cancelled" or result["cancelDecisionVisible"]:
        raise AssertionError(f"pre-apply cancellation left active decision controls: {result!r}")
    expected_preview = {"scope": "library", "staged_filename": "reviewed.jsonl", "preview_only": True}
    if requests[0] != expected_preview or requests[2] != expected_preview:
        raise AssertionError(f"collection preview did not use the existing import POST safely: {requests!r}")
    apply_request = requests[1]
    if apply_request.get("export_id") != "ds_20260712T170000Z" or apply_request.get("source_sha256") != "abc123":
        raise AssertionError(f"confirmed package identity was not submitted: {apply_request!r}")
    if apply_request.get("decisions") != [
        {"record_index": 0, "action": "overwrite", "target_doc_id": "alpha", "note": ""},
        {"record_index": 1, "action": "overwrite", "target_doc_id": "beta", "note": ""},
        {"record_index": 2, "action": "overwrite", "target_doc_id": "gamma", "note": ""},
    ]:
        raise AssertionError(f"explicit expanded decisions did not match the reviewed plan: {apply_request!r}")
    if set(apply_request) != {
        "scope", "staged_filename", "preview_only", "confirm", "export_id", "source_sha256", "decisions", "activity_context"
    }:
        raise AssertionError(f"apply request widened beyond the safe collection contract: {apply_request!r}")


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="domcontentloaded")
    assert_collection_controller(page, base_url)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", default=".", help="Repo/site root to serve.")
    args = parser.parse_args(argv)
    server, base_url = start_static_server(Path(args.site_root))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            run_smoke(page, base_url)
            browser.close()
            if errors:
                raise AssertionError(f"page errors: {errors}")
    finally:
        server.shutdown()
        server.server_close()
    print("Docs Import collection modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
            const module = await import('/studio/app/frontend/js/catalogue-editor-action-workflow.js');
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
            const skippedNoArtifacts = module.resolveCatalogueSaveBuildOutcome({
                response: {
                    changed: true,
                    saved_at_utc: '2026-05-21T10:06:00Z',
                    build_requested: false,
                    build_skipped: { reason: 'no_public_build_artifacts' }
                },
                isPublished: true
            });
            const presentationLabels = {
                resultLabels: {
                    unchanged: { text: 'unchanged result', tone: '' },
                    saved: { text: 'saved result', tone: 'success' },
                    savedUnpublished: { text: 'unpublished result', tone: 'success' },
                    savedAndUpdated: { text: 'applied result', tone: 'success' },
                    savedUpdateFailed: { text: 'partial result', tone: 'warn' }
                },
                statusLabels: {
                    loaded: { text: 'loaded status', tone: 'success' },
                    savedAndUpdated: { text: 'build complete', tone: 'success' },
                    savedUpdateFailed: { text: 'build failed', tone: 'error' }
                }
            };
            const presentationUnchanged = module.projectCatalogueSaveOutcomePresentation({
                outcome: unchanged,
                changed: false,
                ...presentationLabels
            });
            const presentationSaved = module.projectCatalogueSaveOutcomePresentation({
                outcome: pending,
                changed: true,
                ...presentationLabels
            });
            const presentationUnpublished = module.projectCatalogueSaveOutcomePresentation({
                outcome: unpublished,
                changed: true,
                ...presentationLabels
            });
            const presentationApplied = module.projectCatalogueSaveOutcomePresentation({
                outcome: applied,
                changed: true,
                ...presentationLabels
            });
            const presentationFailed = module.projectCatalogueSaveOutcomePresentation({
                outcome: failed,
                changed: true,
                ...presentationLabels
            });
            const actionPresentation = module.projectCatalogueActionPresentation({
                resultKey: 'done',
                statusKey: 'ready',
                resultLabels: {
                    done: { text: 'result done', tone: 'success' }
                },
                statusLabels: {
                    ready: { text: 'status ready', tone: 'success' }
                }
            });
            const pendingTargets = module.resolveCataloguePendingBuildTargets({
                rebuildPending: true,
                pendingTargets: [{ work_id: 'pending' }],
                fallbackTargets: [{ work_id: 'fallback' }]
            });
            const fallbackTargets = module.resolveCataloguePendingBuildTargets({
                rebuildPending: false,
                pendingTargets: [{ work_id: 'pending' }],
                fallbackTargets: [{ work_id: 'fallback' }]
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
            const workRecordModule = await import('/studio/app/frontend/js/catalogue-work-action-records.js');
            const searchRecord = workRecordModule.projectWorkSearchRecord(' 001 ', {
                title: 'Work title',
                year_display: '2026',
                status: 'published',
                series_ids: ['009']
            }, 'hash-001');
            const state = {
                sourceWorkRecordsById: new Map(),
                workSearchById: new Map(),
                bulkRecords: new Map(),
                bulkRecordHashes: new Map()
            };
            const singleMutation = workRecordModule.applyWorkRecordMutation(state, {
                workId: '002',
                record: {
                    title: 'Single work',
                    year_display: '2025',
                    status: 'draft',
                    series_ids: ['008']
                },
                recordHash: 'hash-002'
            });
            const bulkMutations = workRecordModule.applyBulkWorkRecordMutations(state, [
                {
                    work_id: '003',
                    record_hash: 'hash-003',
                    record: {
                        title: 'Bulk work',
                        year_display: '2024',
                        status: 'published',
                        series_ids: ['007']
                    }
                },
                { work_id: '', record_hash: 'ignored', record: { title: 'Ignored' } },
                { work_id: '004', record_hash: 'ignored', record: null }
            ]);
            await Promise.all([
                import('/studio/app/frontend/js/catalogue-work-actions.js'),
                import('/studio/app/frontend/js/catalogue-work-detail-actions.js'),
                import('/studio/app/frontend/js/catalogue-series-actions.js'),
                import('/studio/app/frontend/js/catalogue-moment-actions.js')
            ]);
            return {
                unchanged,
                unpublished,
                pending,
                applied,
                failed,
                skippedNoArtifacts,
                presentationUnchanged,
                presentationSaved,
                presentationUnpublished,
                presentationApplied,
                presentationFailed,
                actionPresentation,
                pendingTargets,
                fallbackTargets,
                publicationBlocker,
                deleteBlocker,
                noBlocker,
                searchRecord,
                singleMutation,
                bulkMutationCount: bulkMutations.length,
                sourceRecordTitle: state.sourceWorkRecordsById.get('00003').title,
                bulkRecordTitle: state.bulkRecords.get('00003').title,
                bulkRecordHash: state.bulkRecordHashes.get('00003'),
                bulkSearchRecord: state.workSearchById.get('00003'),
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
    assert result["skippedNoArtifacts"]["kind"] == "saved"
    assert result["skippedNoArtifacts"]["rebuildPending"] is False
    assert result["presentationUnchanged"] == {
        "resultText": "unchanged result",
        "resultTone": "",
        "statusText": "loaded status",
        "statusTone": "success",
    }
    assert result["presentationSaved"] == {
        "resultText": "saved result",
        "resultTone": "success",
        "statusText": "loaded status",
        "statusTone": "success",
    }
    assert result["presentationUnpublished"] == {
        "resultText": "unpublished result",
        "resultTone": "success",
        "statusText": "loaded status",
        "statusTone": "success",
    }
    assert result["presentationApplied"] == {
        "resultText": "applied result",
        "resultTone": "success",
        "statusText": "build complete",
        "statusTone": "success",
    }
    assert result["presentationFailed"] == {
        "resultText": "partial result",
        "resultTone": "warn",
        "statusText": "build failed",
        "statusTone": "error",
    }
    assert result["actionPresentation"] == {
        "resultText": "result done",
        "resultTone": "success",
        "statusText": "status ready",
        "statusTone": "success",
    }
    assert result["pendingTargets"][0]["work_id"] == "pending"
    assert result["fallbackTargets"][0]["work_id"] == "fallback"
    assert result["publicationBlocker"] == "Blocked by parent status."
    assert result["deleteBlocker"] == "Delete requires removing members first."
    assert result["noBlocker"] == ""
    assert result["searchRecord"] == {
        "work_id": "00001",
        "title": "Work title",
        "year_display": "2026",
        "status": "published",
        "series_ids": ["009"],
        "record_hash": "hash-001",
    }
    assert result["singleMutation"]["workId"] == "00002"
    assert result["singleMutation"]["recordHash"] == "hash-002"
    assert result["singleMutation"]["searchRecord"]["title"] == "Single work"
    assert result["bulkMutationCount"] == 1
    assert result["sourceRecordTitle"] == "Bulk work"
    assert result["bulkRecordTitle"] == "Bulk work"
    assert result["bulkRecordHash"] == "hash-003"
    assert result["bulkSearchRecord"] == {
        "work_id": "00003",
        "title": "Bulk work",
        "year_display": "2024",
        "status": "published",
        "series_ids": ["007"],
        "record_hash": "hash-003",
    }
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

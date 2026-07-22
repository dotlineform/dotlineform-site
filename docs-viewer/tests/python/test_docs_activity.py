#!/usr/bin/env python3
"""Verify Docs Management Studio Activity helper behavior."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
STUDIO_SERVER_DIR = REPO_ROOT / "studio" / "app" / "server"
STUDIO_SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
for path in (DOCS_SERVICES_DIR, STUDIO_SERVER_DIR, STUDIO_SHARED_PYTHON_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import docs_activity  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import studio_activity  # noqa: E402


def write_activity_contract(repo_root: Path) -> None:
    contract_path = repo_root / studio_activity.ACTIVITY_CONTRACT_REL_PATH
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        json.dumps(
            {
                "pages": {
                    "docs-manage": {
                        "label": "docs manage",
                        "route": "/docs/",
                        "actions": {
                            "prepare-document-package": {
                                "label": "prepare document package",
                                "control_id": "docsViewerManagePreparePackageButton",
                                "control_selector": "#docsViewerManagePreparePackageButton",
                                "endpoint": docs_activity.DOCUMENT_PACKAGE_PREPARE_PATH,
                                "record_id_field": "export_id",
                            }
                        },
                    },
                    "docs-import": {
                        "label": "docs import",
                        "route": "/docs/",
                        "actions": {
                            "import-docs-source": {
                                "label": "import docs source",
                                "control_id": "docsHtmlImportRun",
                                "control_selector": "#docsHtmlImportRun",
                                "endpoint": routes.IMPORT_SOURCE_PATH,
                                "record_id_field": "staged_filename",
                            },
                            "import-docs-collection": {
                                "label": "import docs collection",
                                "control_id": "docsImportCollectionConfirm",
                                "control_selector": "[data-collection-command=confirm]",
                                "endpoint": routes.IMPORT_SOURCE_PATH,
                                "record_id_field": "staged_filename",
                            }
                        },
                    },
                    "docs-package-returned": {
                        "label": "returned document packages",
                        "route": "/docs/packages/returned/",
                        "actions": {
                            "apply-returned-summaries": {
                                "label": "apply returned summaries",
                                "control_id": "documentPackageReturnedSummaryApply",
                                "control_selector": "#documentPackageReturnedSummaryApply",
                                "endpoint": docs_activity.DOCUMENT_PACKAGE_APPLY_PATH,
                                "record_id_field": "staged_filename",
                            }
                        },
                    },
                    "docs-broken-links": {
                        "label": "docs broken links",
                        "route": "/docs/?scope=studio&doc=docs-broken-links",
                        "actions": {
                            "run-broken-links-audit": {
                                "label": "run broken-links audit",
                                "control_id": "docsBrokenLinksReportRun",
                                "control_selector": "#docsBrokenLinksReportRun",
                                "endpoint": routes.BROKEN_LINKS_PATH,
                                "record_id_field": "scope",
                            }
                        },
                    },
                },
                "script_purposes": {
                    "prepare-share-package": {"label": "prepare share package"},
                    "import-source-data": {"label": "import source data"},
                    "update-docs-source": {"label": "update docs source"},
                    "run-audit": {"label": "run audit"},
                },
            }
        ),
        encoding="utf-8",
    )


def activity_entries(repo_root: Path) -> list[dict[str, object]]:
    feed_path = repo_root / studio_activity.FEED_REL_PATH
    if not feed_path.exists():
        return []
    payload = json.loads(feed_path.read_text(encoding="utf-8"))
    return payload["entries"]


def export_body() -> dict[str, object]:
    return {
        "profile_id": "document-content",
        "doc_ids": ["library", "longform", "notes"],
        "activity_context": {
            "page_id": "docs-manage",
            "action_id": "prepare-document-package",
            "route": "/docs/",
            "control_id": "docsViewerManagePreparePackageButton",
            "control_selector": "#docsViewerManagePreparePackageButton",
            "correlation_id": "export:library",
        },
    }


def test_docs_export_activity_suppresses_dry_run_and_no_write() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        write_activity_contract(repo_root)
        payload = {
            "ok": True,
            "output_written": True,
            "export_id": "ds_20260720T120000Z",
            "profile_id": "document-content",
            "counts": {"exported": 3, "failed": 0},
            "issue_counts": {"warnings": 0},
        }

        docs_activity.maybe_attach_docs_export_activity(repo_root, export_body(), payload, dry_run=True)
        assert "activity_log" not in payload
        assert activity_entries(repo_root) == []

        payload["output_written"] = False
        docs_activity.maybe_attach_docs_export_activity(repo_root, export_body(), payload, dry_run=False)
        assert "activity_log" not in payload
        assert activity_entries(repo_root) == []


def test_docs_export_activity_writes_compact_doc_ids() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        write_activity_contract(repo_root)
        payload = {
            "ok": True,
            "output_written": True,
            "export_id": "ds_20260720T120000Z",
            "profile_id": "document-content",
            "output_file": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/exports/export.jsonl",
            "counts": {"exported": 3, "failed": 0},
            "issue_counts": {"warnings": 0},
        }

        docs_activity.maybe_attach_docs_export_activity(repo_root, export_body(), payload, dry_run=False)

        assert payload["activity_log"]["written_count"] == 1
        entry = activity_entries(repo_root)[0]
        assert entry["status"] == "completed"
        assert entry["page_id"] == "docs-manage"
        assert entry["user_action_id"] == "prepare-document-package"
        assert entry["record_groups"]["docs"]["sample_ids"] == ["library", "longform", "notes"]
        assert entry["source_refs"] == docs_activity.DOCS_ACTIVITY_SOURCE_REFS
        assert payload["activity_context"]["control_id"] == "docsViewerManagePreparePackageButton"


def import_source_body() -> dict[str, object]:
    return {
        "staged_filename": "import-me.html",
        "activity_context": {
            "page_id": "docs-import",
            "action_id": "import-docs-source",
            "route": "/docs/",
            "control_id": "docsHtmlImportRun",
            "control_selector": "#docsHtmlImportRun",
            "correlation_id": "import-source:import-me",
            "staged_filename": "import-me.html",
        },
    }


def test_import_source_activity_suppresses_preview() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        write_activity_contract(repo_root)
        body = import_source_body()
        preview_payload = {"ok": True, "doc_id": "new-doc", "preview_only": True}

        docs_activity.maybe_attach_import_source_activity(repo_root, body, preview_payload, dry_run=False)

        assert "activity_log" not in preview_payload
        assert activity_entries(repo_root) == []


def test_collection_import_activity_records_grouped_result_and_safe_report_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        write_activity_contract(repo_root)
        body = {
            "staged_filename": "reviewed.jsonl",
            "activity_context": {
                "page_id": "docs-import",
                "action_id": "import-docs-collection",
                "route": "/docs/",
                "control_id": "docsImportCollectionConfirm",
                "control_selector": "[data-collection-command=confirm]",
                "correlation_id": "import-collection:reviewed",
                "staged_filename": "reviewed.jsonl",
            },
        }
        payload = {
            "ok": True,
            "collection": True,
            "preview_only": False,
            "outcome": "partial",
            "counts": {"created": 1, "overwritten": 0, "skipped": 1, "failed": 1, "not_attempted": 0},
            "records": [
                {"doc_id": "alpha", "status": "created"},
                {"doc_id": "beta", "status": "skipped", "note": "Repair metadata."},
                {"doc_id": "gamma", "status": "failed"},
            ],
            "report_path": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/results/result.md",
        }

        docs_activity.maybe_attach_import_source_activity(repo_root, body, payload, dry_run=False)

        assert payload["activity_log"]["written_count"] == 1
        entry = activity_entries(repo_root)[0]
        assert entry["status"] == "warning"
        assert entry["record_groups"]["docs"]["sample_ids"] == ["alpha"]
        assert entry["record_groups"]["files"]["sample_ids"] == [payload["report_path"]]
        assert any("Repair metadata." in item for item in entry["detail_items"])


def import_apply_body(confirm: bool) -> dict[str, object]:
    return {
        "staged_filename": "content.jsonl",
        "confirm": confirm,
        "activity_context": {
            "page_id": "docs-package-returned",
            "action_id": "apply-returned-summaries",
            "route": "/docs/packages/returned/",
            "control_id": "documentPackageReturnedSummaryApply",
            "control_selector": "#documentPackageReturnedSummaryApply",
            "correlation_id": "import-apply:content",
            "staged_filename": "content.jsonl",
        },
    }


def test_import_apply_activity_suppresses_unconfirmed_apply() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        write_activity_contract(repo_root)
        payload = {
            "ok": True,
            "summary_apply_written": True,
            "updates": [{"doc_id": "library"}],
            "counts": {"errors": 0, "warnings": 0},
        }

        docs_activity.maybe_attach_documents_import_apply_activity(repo_root, import_apply_body(False), payload, dry_run=False)

        assert "activity_log" not in payload
        assert activity_entries(repo_root) == []


def test_import_apply_activity_uses_direct_returned_package_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        write_activity_contract(repo_root)
        payload = {
            "ok": True,
            "summary_apply_written": True,
            "updates": [{"doc_id": "library"}],
            "counts": {"errors": 0, "warnings": 0},
        }

        docs_activity.maybe_attach_documents_import_apply_activity(
            repo_root,
            import_apply_body(True),
            payload,
            dry_run=False,
        )

        assert payload["activity_log"]["written_count"] == 1
        entry = activity_entries(repo_root)[0]
        assert entry["page_id"] == "docs-package-returned"
        assert entry["user_action_id"] == "apply-returned-summaries"
        assert entry["record_groups"]["docs"]["sample_ids"] == ["library"]


def test_broken_links_activity_uses_warning_status_for_broken_links() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        write_activity_contract(repo_root)
        body = {
            "scope": "studio",
            "activity_context": {
                "page_id": "docs-broken-links",
                "action_id": "run-broken-links-audit",
                "route": "/docs/?scope=studio&doc=docs-broken-links",
                "control_id": "docsBrokenLinksReportRun",
                "control_selector": "#docsBrokenLinksReportRun",
                "correlation_id": "broken-links:studio",
                "scope": "studio",
            },
        }
        payload = {"ok": True, "scope": "studio", "summary": {"total": 2}}

        docs_activity.maybe_attach_broken_links_activity(repo_root, body, payload)

        assert payload["activity_log"]["written_count"] == 1
        entry = activity_entries(repo_root)[0]
        assert entry["status"] == "warning"
        assert entry["record_groups"]["docs"]["sample_ids"] == ["studio"]
        assert "Found 2 broken link(s)." in entry["detail_items"]


def main() -> None:
    test_docs_export_activity_suppresses_dry_run_and_no_write()
    test_docs_export_activity_writes_compact_doc_ids()
    test_import_source_activity_suppresses_preview()
    test_collection_import_activity_records_grouped_result_and_safe_report_path()
    test_import_apply_activity_suppresses_unconfirmed_apply()
    test_import_apply_activity_uses_direct_returned_package_contract()
    test_broken_links_activity_uses_warning_status_for_broken_links()
    print("Docs activity tests OK")


if __name__ == "__main__":
    main()

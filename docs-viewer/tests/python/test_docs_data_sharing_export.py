#!/usr/bin/env python3
"""Docs data sharing export tests."""

from __future__ import annotations

from pathlib import Path

from docs_management_test_support import (
    analytics_data_sharing_api,
    docs_data_sharing_package,
    documents_prepare,
    make_repo,
)

def test_docs_export_request_passes_target_format() -> None:
    calls: list[dict[str, object]] = []
    original_build_export = docs_data_sharing_package.build_export

    def fake_build_export(**kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "target_format": kwargs["target_format"],
            "output_file": "var/analytics/data-sharing/exports/test.json",
            "output_written": False,
            "counts": {"selected": 1, "exported": 1, "skipped": 0, "failed": 0, "truncated": 0},
            "issue_counts": {"errors": 0, "warnings": 0},
        }

    docs_data_sharing_package.build_export = fake_build_export
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            adapter = analytics_data_sharing_api.data_sharing_service.resolve_for_service(repo_root, "documents", "prepare")
            result = documents_prepare.prepare_package(
                repo_root,
                {
                    "data_domain": "documents",
                    "config_id": "document-content",
                    "selection": {
                        "docs_scope": "studio",
                        "doc_ids": ["child"],
                        "select_all": False,
                        "missing_summary_only": False,
                    },
                    "target_format": "json",
                    "content_format": "plain_text",
                },
                dry_run=True,
                adapter=adapter,
                dependencies=analytics_data_sharing_api.documents_data_sharing_dependencies(),
            )
    finally:
        docs_data_sharing_package.build_export = original_build_export

    assert result["ok"] is True
    assert result["target_format"] == "json"
    assert calls[0]["target_format"] == "json"
    assert calls[0]["content_format"] == "plain_text"
    assert calls[0]["write"] is False

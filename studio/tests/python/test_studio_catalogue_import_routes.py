#!/usr/bin/env python3
"""Studio catalogue import route tests."""

from __future__ import annotations

import json
import tempfile
from http import HTTPStatus
from pathlib import Path

import pytest

from studio_app_server_test_support import catalogue_post_response, write_repo_marker

def test_catalogue_import_preview_and_apply_dry_run_use_fixture_workbook() -> None:
    openpyxl = pytest.importorskip("openpyxl")
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "repo"
        source_dir = repo_root / "studio" / "data" / "canonical" / "catalogue"
        source_dir.mkdir(parents=True)
        write_repo_marker(repo_root)
        (source_dir / "works.json").write_text(
            json.dumps({"catalogue_source_works_version": "catalogue_source_works_v1", "works": {}}),
            encoding="utf-8",
        )
        (source_dir / "work_details").mkdir(parents=True, exist_ok=True)
        (source_dir / "series.json").write_text(
            json.dumps({"catalogue_source_series_version": "catalogue_source_series_v1", "series": {"001": {"series_id": "001", "title": "Series", "status": "published", "primary_work_id": "00042"}}}),
            encoding="utf-8",
        )
        workbook_path = repo_root / "data" / "works_bulk_import.xlsx"
        workbook_path.parent.mkdir(parents=True)
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Works"
        sheet.append(["work_id", "series_ids", "title"])
        sheet.append(["42", "001", "Imported Work"])
        workbook.save(workbook_path)

        status, preview_payload = catalogue_post_response(repo_root, "/import-preview", {"mode": "works"}, dry_run=True)
        apply_status, apply_payload = catalogue_post_response(repo_root, "/import-apply", {"mode": "works"}, dry_run=True)

        assert status == HTTPStatus.OK
        assert preview_payload["preview"]["summary"]["importable_count"] == 1
        assert preview_payload["preview"]["importable_ids"] == ["00042"]
        assert apply_status == HTTPStatus.OK
        assert apply_payload["dry_run"] is True
        assert apply_payload["would_write"] is True
        assert json.loads((source_dir / "works.json").read_text(encoding="utf-8"))["works"] == {}

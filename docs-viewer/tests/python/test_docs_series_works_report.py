"""Exact document subjects select current generated Series membership."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import docs_management_read_service as read_service
import docs_management_routes as routes
import docs_series_works_report as report
from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config, write_site_tools_config, write_text


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_ID = "d-20260905-000000-000001"
TARGET = {"scope": "analysis", "sub_scope": "works", "doc_id": DOC_ID}


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "repo"
    base = tmp_path / "projects"
    base.mkdir()
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(base))
    write_site_tools_config(root)
    write_docs_scope_config(root, [docs_scope_record(
        "analysis",
        sub_scopes=[docs_sub_scope_record("analysis", "works")],
    )])
    registry = root / "docs-viewer/config/reports/reports.json"
    write_text(registry, (REPO_ROOT / "docs-viewer/config/reports/reports.json").read_text())
    source = root / f"docs-viewer/scopes/analysis/source/sub-scopes/works/documents/{DOC_ID}.md"
    write_text(source, f'''---
doc_id: {DOC_ID}
title: This title does not choose a Series
series_id: "143"
---
:::report
id: series_works
access: local
:::
''')
    series_file = base / "catalogue/generated/series/index/143.json"
    payload = {
        "series": {"series_id": "143", "title": "simultaneous equations", "status": "draft"},
        "member_works": [
            {"work_id": "01942", "title": "se2", "year_display": "2026"},
            {"work_id": "01941", "title": "se1", "year_display": "2026"},
        ],
    }
    write_text(series_file, json.dumps(payload))
    return root, source, series_file, payload


def test_get_reads_subject_and_preserves_generated_order_without_status_filter(workspace):
    root, _, series_file, payload = workspace
    query = {key: [value] for key, value in TARGET.items()}
    result = read_service.docs_management_get_payload(root, routes.SERIES_WORKS_REPORT_PATH, query)
    assert result == {
        "ok": True,
        "schema": report.REPORT_SCHEMA,
        "target": TARGET,
        "series_id": "143",
        "title": "simultaneous equations",
        "works": payload["member_works"],
    }
    payload["member_works"] = []
    series_file.write_text(json.dumps(payload))
    assert report.build_series_works_report(root, TARGET)["works"] == []


@pytest.mark.parametrize("declaration", ["", 'work_id: "01941"', 'series_id: "143"\nwork_id: "01941"'])
def test_report_requires_the_documents_sole_series_subject(workspace, declaration):
    root, source, _, _ = workspace
    source.write_text(source.read_text().replace('series_id: "143"', declaration))
    with pytest.raises(ValueError, match="Series subject"):
        report.build_series_works_report(root, TARGET)


def test_unavailable_generated_series_does_not_fall_back_to_other_data(workspace):
    root, _, series_file, _ = workspace
    series_file.unlink()
    with pytest.raises(ValueError, match="Series 143 is unavailable"):
        report.build_series_works_report(root, TARGET)


def test_mismatched_payload_and_duplicate_members_are_rejected(workspace):
    _, _, _, payload = workspace
    with pytest.raises(ValueError, match="does not match"):
        report.series_work_rows(payload, "144")
    payload["member_works"].append(payload["member_works"][0])
    with pytest.raises(ValueError, match="member identity"):
        report.series_work_rows(payload, "143")


def prepare_work_media(workspace):
    root, _, series_file, _ = workspace
    work_file = series_file.parents[2] / "works/index/01941.json"
    work = {
        "work_id": "01941", "title": "se1", "year_display": "2026", "medium_caption": "digital c-type print",
        "width_px": 3543, "height_px": 3543, "media_version": 2, "height_cm": 30.0, "width_cm": 30.0,
    }
    write_text(work_file, json.dumps({"work": work}))
    write_text(root / "site-tools/config/site-tools.json", json.dumps({"media": {
        "base": "https://media.example.test", "image_works": "/current/works",
    }}))
    write_text(root / "_data/pipeline.json", json.dumps({
        "variants": {"primary": {"suffix": "primary", "preferred_width": 1600}}, "encoding": {"format": "webp"},
    }))
    return work_file, work


def test_media_get_reads_only_the_selected_generated_work(workspace):
    root, _, _, _ = workspace
    work_file, work = prepare_work_media(workspace)
    query = {key: [value] for key, value in {**TARGET, "work_id": "01941"}.items()}
    result = read_service.docs_management_get_payload(root, routes.SERIES_WORK_MEDIA_PATH, query)
    assert result["target"] == TARGET
    presentation = result["presentation"]
    assert presentation["target"] == {"kind": "catalogue-work", "id": "01941"}
    assert presentation["schema_version"] == "docs_media_view_v1"
    assert presentation["image"]["src"] == "https://media.example.test/current/works/01941-primary-1600.webp?v=2"
    assert presentation["new_tab_target"] == presentation["image"]["src"]
    assert presentation["metadata"] == [
        {"label": "Year", "value": "2026"}, {"label": "Medium", "value": "digital c-type print"},
        {"label": "Dimensions", "value": "30 × 30 cm"}, {"label": "Catalogue number", "value": "01941"},
    ]
    # The other Series member has no Work file; neither list nor selected read needs it.
    assert len(report.build_series_works_report(root, TARGET)["works"]) == 2
    work["title"] = "Updated generated title"
    work_file.write_text(json.dumps({"work": work}))
    assert report.build_series_work_media(root, TARGET, "01941")["presentation"]["label"] == work["title"]


@pytest.mark.parametrize("work_id", ["00001", "../01941", "", "1941"])
def test_media_rejects_targets_outside_the_current_series(workspace, work_id):
    root, _, _, _ = workspace
    with pytest.raises(ValueError, match="not a member"):
        report.build_series_work_media(root, TARGET, work_id)


def test_media_rejects_missing_mismatched_and_unusable_work_data(workspace):
    root, _, _, _ = workspace
    work_file, work = prepare_work_media(workspace)
    work["work_id"] = "01942"
    work_file.write_text(json.dumps({"work": work}))
    with pytest.raises(ValueError, match="does not match"):
        report.build_series_work_media(root, TARGET, "01941")
    work["work_id"] = "01941"
    work["width_px"] = 0
    work_file.write_text(json.dumps({"work": work}))
    with pytest.raises(ValueError, match="positive integer"):
        report.build_series_work_media(root, TARGET, "01941")
    work_file.unlink()
    with pytest.raises(ValueError, match="Work 01941 is unavailable"):
        report.build_series_work_media(root, TARGET, "01941")

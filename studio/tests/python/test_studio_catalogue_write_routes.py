"""Canonical Catalogue mutations and the paused output boundary through Studio's API."""

from http import HTTPStatus
from pathlib import Path

import pytest

from catalogue_factory import write_catalogue_source
from studio_app_server_test_support import catalogue_post_response, write_repo_marker
from catalogue.catalogue_revisions import record_hash
from catalogue.catalogue_source import records_from_json_source


@pytest.fixture
def catalogue(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    write_repo_marker(repo)
    projects = tmp_path / "projects"
    projects.mkdir()
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects))
    source = write_catalogue_source(repo)
    return repo, source


@pytest.mark.parametrize("path", ["/build-preview", "/build-apply", "/media-publish-preview", "/media-publish-apply"])
def test_output_and_media_paused_before_reading_source(tmp_path, path):
    status, payload = catalogue_post_response(tmp_path, path, {})
    assert status == HTTPStatus.SERVICE_UNAVAILABLE
    assert "Stage 5" in payload["error"]
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("path", ["/publication-preview", "/publication-apply"])
def test_record_publication_routes_removed(path):
    with pytest.raises(FileNotFoundError):
        catalogue_post_response(Path.cwd(), path, {})


def test_create_ungrouped_work_and_empty_series(catalogue):
    repo, source = catalogue
    for family, record_id in [("work", "00003"), ("series", "011")]:
        status, payload = catalogue_post_response(repo, f"/{family}/create", {f"{family}_id": record_id, "record": {"title": "New", "year": 2026, "year_display": "2026"}})
        assert status == HTTPStatus.OK
        assert payload["record_hash"] == record_hash(payload["record"])
        assert not {"status", "published_date", "primary_work_id", "series_type", "series_ids"} & payload["record"].keys()
    assert "series_id" not in records_from_json_source(source).works["00003"]


@pytest.mark.parametrize("path", ["/work/save", "/bulk-save"])
def test_set_clear_and_stale_work_membership(catalogue, path):
    repo, source = catalogue
    for series_id in ("010", None):
        current = records_from_json_source(source).works["00001"]
        revision = record_hash(current)
        body = {"work_id": "00001", "expected_record_hash": revision, "record": {"series_id": series_id}} if path == "/work/save" else {"kind": "works", "ids": ["00001"], "expected_record_hashes": {"00001": revision}, "set_fields": {"series_id": series_id}}
        status, response = catalogue_post_response(repo, path, body)
        assert status == HTTPStatus.OK
        updated = records_from_json_source(source).works["00001"]
        assert updated.get("series_id") == series_id
        assert ("series_id" in updated) == bool(series_id)
        assert response["lookup_refresh"]["written_count"] > 0
        assert not {"build", "r2_media", "semantic_target_lookup"} & response.keys()
        status, _ = catalogue_post_response(repo, path, body)
        assert status == HTTPStatus.CONFLICT


def test_series_and_member_changes_are_coherent_and_revision_bound(catalogue):
    repo, source = catalogue
    records = records_from_json_source(source)
    body = {"series_id": "009", "expected_record_hash": record_hash(records.series["009"]), "record": {"title": "Updated"}, "work_updates": [{"work_id": "00001", "series_id": None, "expected_record_hash": "stale"}]}
    before = {p.name: p.read_bytes() for p in source.glob("*.json")}
    assert catalogue_post_response(repo, "/series/save", body)[0] == HTTPStatus.CONFLICT
    assert before == {p.name: p.read_bytes() for p in source.glob("*.json")}
    body["work_updates"][0]["expected_record_hash"] = record_hash(records.works["00001"])
    status, payload = catalogue_post_response(repo, "/series/save", body)
    assert status == HTTPStatus.OK
    updated = records_from_json_source(source)
    assert updated.series["009"]["title"] == "Updated"
    assert "series_id" not in updated.works["00001"]
    assert payload["work_records"][0]["record_hash"] == record_hash(updated.works["00001"])


@pytest.mark.parametrize("field,value", [("series_ids", ["009"]), ("status", "draft"), ("published_date", "2026-01-01"), ("series_id", "999")])
def test_invalid_work_changes_do_not_write(catalogue, field, value):
    repo, source = catalogue
    current = records_from_json_source(source).works["00001"]
    before = (source / "works.json").read_bytes()
    with pytest.raises(ValueError):
        catalogue_post_response(repo, "/work/save", {"work_id": "00001", "expected_record_hash": record_hash(current), "record": {field: value}})
    assert (source / "works.json").read_bytes() == before

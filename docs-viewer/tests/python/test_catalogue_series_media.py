"""Exact generated Series membership and confined thumbnail HTTP reads."""

import io
import json
from types import MethodType, SimpleNamespace

import pytest

from docs_catalogue_media import CATALOGUE_THUMBNAIL_PREFIX, catalogue_thumbnail_path, read_catalogue_series
from docs_management_read_service import docs_management_get_payload
import docs_management_routes as routes
from docs_viewer_service import DocsViewerRequestHandler
from repo_factory import write_json, write_site_tools_config


@pytest.fixture
def series(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    generated = tmp_path / "projects/catalogue/generated"
    payload = {"header": {"schema": "series_record_v5", "series_id": "143"},
               "series": {"series_id": "143", "title": "A Series"},
               "member_works": [{"work_id": "01942", "title": "Second"},
                                {"work_id": "01941", "title": "First"}]}
    write_site_tools_config(repo)
    write_json(generated / "series/index/143.json", payload)
    thumbnail = generated / "works/thumbs/01942-thumb-96.webp"
    thumbnail.parent.mkdir(parents=True)
    thumbnail.write_bytes(b"existing thumbnail")
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(tmp_path / "projects"))
    return repo, generated, payload


def test_series_read_preserves_order_and_empty_series_without_work_reads(series):
    repo, generated, payload = series
    assert not (generated / "works/index").exists()
    assert routes.CATALOGUE_SERIES_PATH in routes.GET_PATHS
    assert docs_management_get_payload(repo, routes.CATALOGUE_SERIES_PATH, {"series_id": ["143"]}) == payload
    payload["member_works"] = []
    write_json(generated / "series/index/143.json", payload)
    assert read_catalogue_series(repo, "143")["member_works"] == []


@pytest.mark.parametrize("series_id", ["14", "143 ", "../143", "144", 143])
def test_series_read_requires_exact_existing_identity(series, series_id):
    with pytest.raises(ValueError):
        read_catalogue_series(series[0], series_id)


@pytest.mark.parametrize("change", [
    lambda p: p["series"].update(series_id="144"),
    lambda p: p["series"].update(title=""),
    lambda p: p.update(member_works=None),
    lambda p: p["member_works"].append(p["member_works"][0]),
    lambda p: p["member_works"][0].update(work_id="1942"),
    lambda p: p["member_works"][0].update(title=""),
])
def test_series_read_rejects_mismatched_or_ambiguous_membership(series, change):
    repo, generated, payload = series
    change(payload)
    write_json(generated / "series/index/143.json", payload)
    with pytest.raises(ValueError):
        read_catalogue_series(repo, "143")


def test_thumbnail_read_is_generated_owned_and_confined(series, tmp_path):
    repo, generated, _ = series
    route = CATALOGUE_THUMBNAIL_PREFIX + "01942-thumb-96.webp"
    assert catalogue_thumbnail_path(repo, route).read_bytes() == b"existing thumbnail"
    for filename in ("../01942-thumb-96.webp", "01942-primary-800.webp", "1942-thumb-96.webp", "01942-thumb-777.webp"):
        with pytest.raises(ValueError):
            catalogue_thumbnail_path(repo, CATALOGUE_THUMBNAIL_PREFIX + filename)
    with pytest.raises(FileNotFoundError):
        catalogue_thumbnail_path(repo, CATALOGUE_THUMBNAIL_PREFIX + "01941-thumb-96.webp")
    outside = tmp_path / "outside.webp"
    outside.write_bytes(b"outside")
    (generated / "works/thumbs/01941-thumb-96.webp").symlink_to(outside)
    with pytest.raises(ValueError):
        catalogue_thumbnail_path(repo, CATALOGUE_THUMBNAIL_PREFIX + "01941-thumb-96.webp")


def test_thumbnail_http_dispatch_and_generated_read_gate(series):
    repo, _, _ = series
    statuses, headers, errors = [], {}, []
    handler = SimpleNamespace(
        repo_root=repo, config=SimpleNamespace(generated_reads_enabled=True),
        path=CATALOGUE_THUMBNAIL_PREFIX + "01942-thumb-96.webp", wfile=io.BytesIO(),
        send_response=statuses.append, send_cors_headers=lambda: None,
        send_header=lambda k, v: headers.update({k: v}), end_headers=lambda: None,
        send_json=lambda p, status: errors.append((p, status)),
    )
    handler.send_catalogue_thumbnail = MethodType(DocsViewerRequestHandler.send_catalogue_thumbnail, handler)
    DocsViewerRequestHandler.do_GET(handler)
    assert statuses == [200]
    assert handler.wfile.getvalue() == b"existing thumbnail"
    assert headers["Content-Type"] == "image/webp"
    assert headers["X-Content-Type-Options"] == "nosniff"
    handler.config.generated_reads_enabled = False
    DocsViewerRequestHandler.do_GET(handler)
    assert errors[-1][1] == 403


def test_configured_thumbnail_variant_is_generated_by_catalogue():
    from pathlib import Path

    repo = Path(__file__).resolve().parents[3]
    pipeline = json.loads((repo / "_data/pipeline.json").read_text())
    registry = json.loads((repo / "docs-viewer/config/routes/docs-viewer-routes.json").read_text())
    public = json.loads((repo / "site/docs-viewer/config/routes/docs-viewer-public-routes.json").read_text())
    for route in registry["routes"]:
        settings = route.get("catalogue_paths", {}).get("work_thumbnails")
        if settings:
            assert settings["size"] in pipeline["variants"]["thumb"]["sizes"]
            assert settings["suffix"] == pipeline["variants"]["thumb"]["suffix"]
            assert settings["format"] == pipeline["encoding"]["format"]
        if route["app_kind"] == "public":
            projected = next(r for r in public["routes"] if r["route_id"] == route["route_id"])
            assert projected["catalogue_paths"] == route["catalogue_paths"]

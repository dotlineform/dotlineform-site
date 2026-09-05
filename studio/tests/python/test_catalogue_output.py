"""Catalogue output coverage, refresh equivalence and persisted-write failures."""

import hashlib
import io
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from catalogue_factory import read_json, write_catalogue_source
from catalogue.catalogue_output_paths import catalogue_output_workspace
from catalogue.catalogue_revisions import record_hash
from catalogue.catalogue_source import records_from_json_source, write_source_record_payloads
from catalogue.generate_work_pages import generate_catalogue_json
from catalogue.catalogue_json_build import populate_catalogue_output
from catalogue.catalogue_write_service import handle_catalogue_post
from catalogue import catalogue_build_media as media
from studio.services.media import publish_media_to_r2 as transport
from studio_app_server_test_support import StudioAppRequestHandler, catalogue_post_response


@pytest.fixture
def output_catalogue(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "site-tools/config").mkdir(parents=True)
    shutil.copyfile(Path.cwd() / "site-tools/config/site-tools.json", repo / "site-tools/config/site-tools.json")
    source = write_catalogue_source(repo)
    base = tmp_path / "external"
    root = base / "catalogue/generated"
    root.mkdir(parents=True)
    (base / "catalogue/media-staging").mkdir()
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(base))
    return repo, source, root


def test_full_output_preserves_relationships_sections_and_media(output_catalogue):
    repo, source, root = output_catalogue
    records = records_from_json_source(source)
    records.work_detail_sections["00001-1"]["section_order"] = 1
    records.work_detail_sections["00001-2"] = {**records.work_detail_sections["00001-1"], "section_id": "00001-2", "section_order": 2, "details_subfolder": "more", "detail_sort": "title"}
    for number, title in (("002", "Zulu"), ("003", "Alpha")):
        uid = "00001-" + number
        records.work_details[uid] = {**records.work_details["00001-001"], "detail_id": number, "detail_uid": uid, "section_id": "00001-2", "project_filename": number + ".jpg", "title": title}
    write_source_record_payloads(source, records)
    source_bytes = {p.relative_to(source): p.read_bytes() for p in source.rglob("*.json")}
    result = generate_catalogue_json(repo, source, write=False)
    assert result["counts"] == {"works": 2, "series": 2, "details": 3}
    assert list(root.iterdir()) == []
    generate_catalogue_json(repo, source, write=True)
    assert read_json(root / "works/index/00001.json")["work"]["series_id"] == "009"
    assert "series_id" not in read_json(root / "works/index/00002.json")["work"]
    assert read_json(root / "series/index/010.json")["member_works"] == []
    work = read_json(root / "works/index/00001.json")
    detail = work["sections"][0]["details"][0]
    assert [section["section_id"] for section in work["sections"]] == ["00001-1", "00001-2"]
    assert [item["detail_uid"] for item in work["sections"][1]["details"]] == ["00001-003", "00001-002"]
    assert detail["detail_uid"] == "00001-001"
    assert work["work"]["media"]["thumbnails"][0]["path"].startswith("works/thumbs/00001-")
    assert detail["media"]["primary"][0]["url"].startswith("https://media.dotlineform.com/work_details/img/00001-001-")
    assert read_json(root / "work_details/work_details_index.json")["work_details"]["00001-001"]["section_id"] == "00001-1"
    assert source_bytes == {p.relative_to(source): p.read_bytes() for p in source.rglob("*.json")}
    assert generate_catalogue_json(repo, source, write=True)["written"] == []


def test_focused_membership_and_deleted_output_match_full_build(output_catalogue):
    repo, source, root = output_catalogue
    generate_catalogue_json(repo, source, write=True)
    records = records_from_json_source(source)
    records.works["00001"]["series_id"] = "010"
    records.works["00001"]["title"] = "Moved"
    records.works.pop("00002")
    records.work_details.clear()
    records.work_detail_sections.clear()
    write_source_record_payloads(source, records)
    generate_catalogue_json(repo, source, write=True, work_ids=["00001", "00002"])
    assert read_json(root / "series/index/009.json")["member_works"] == []
    assert read_json(root / "series/index/010.json")["member_works"][0]["work_id"] == "00001"
    assert not (root / "works/index/00002.json").exists()
    assert read_json(root / "works/index/00001.json")["sections"] == []
    assert read_json(root / "work_details/work_details_index.json")["work_details"] == {}
    assert generate_catalogue_json(repo, source, write=True)["written"] == []
    stale = root / "work_details/thumbs/99999-001-thumb-800.webp"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"obsolete")
    assert generate_catalogue_json(repo, source, write=False)["deleted"] == [stale.relative_to(root).as_posix()]
    assert stale.exists()
    generate_catalogue_json(repo, source, write=True)
    assert not stale.exists()


def test_output_root_is_required_and_confined(output_catalogue, tmp_path):
    repo, source, root = output_catalogue
    root.rmdir()
    with pytest.raises(ValueError, match="does not exist"):
        catalogue_output_workspace(repo)
    assert not root.exists()
    root.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (root / "works").symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(ValueError, match="outside"):
        generate_catalogue_json(repo, source, write=True)
    assert list(elsewhere.iterdir()) == []


def test_population_preserves_current_media_without_processing_it(output_catalogue):
    repo, source, root = output_catalogue
    (root.parent / "media-staging").rmdir()
    work = "works/thumbs/00001-thumb-96.webp"
    detail = "work_details/thumbs/00001-001-thumb-96.webp"
    for relative in (work, work.replace("96", "192"), detail, detail.replace("96", "192")):
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_bytes(b"current thumbnail from Save")
    before_source = {p.relative_to(source): p.read_bytes() for p in source.rglob("*.json")}
    preview = populate_catalogue_output(repo, write=False)
    assert preview["thumbnails"] == {"existing_count": 4, "missing": []}
    assert not list(root.rglob("*.json"))
    result = populate_catalogue_output(repo, write=True)
    assert result["status"] == "completed"
    assert (root / detail).read_bytes() == b"current thumbnail from Save"
    assert (root / work).read_bytes() == b"current thumbnail from Save"
    assert before_source == {p.relative_to(source): p.read_bytes() for p in source.rglob("*.json")}
    assert read_json(root / "works/index/00001.json")["work"]["media_version"] == 1


def test_population_reports_exact_missing_thumbnails(output_catalogue):
    repo, _, root = output_catalogue
    result = populate_catalogue_output(repo, write=True)
    assert result["status"] == "incomplete"
    assert result["thumbnails"]["missing"] == [
        "works/thumbs/00001-thumb-96.webp",
        "works/thumbs/00001-thumb-192.webp",
        "work_details/thumbs/00001-001-thumb-96.webp",
        "work_details/thumbs/00001-001-thumb-192.webp",
    ]
    assert not (root / "works/thumbs").exists()


def test_save_keeps_canonical_data_and_revision_on_media_failure(output_catalogue):
    repo, source, root = output_catalogue
    current = records_from_json_source(source).works["00001"]
    _, response = handle_catalogue_post(repo, "/work/save", {
        "work_id": "00001", "expected_record_hash": record_hash(current), "record": {"title": "Saved edit"},
    })
    saved = records_from_json_source(source).works["00001"]
    assert saved["title"] == "Saved edit"
    assert response["saved"] is True
    assert response["record_hash"] == record_hash(saved)
    assert response["output"]["status"] == "failed"
    assert response["output"]["error"]
    assert response["lookup_refresh"]["written_count"] > 0
    assert not (root / "works/index/00001.json").exists()


def test_create_and_delete_without_media_complete_output(output_catalogue):
    repo, source, root = output_catalogue
    _, created = handle_catalogue_post(repo, "/work/create", {
        "work_id": "00003", "record": {"title": "Independent", "year": 2026, "year_display": "2026"},
    })
    assert created["output"]["status"] == "completed"
    assert read_json(root / "works/index/00003.json")["work"]["title"] == "Independent"
    _, deleted = handle_catalogue_post(repo, "/delete-apply", {
        "kind": "work", "id": "00003", "expected_record_hash": created["record_hash"],
    })
    assert deleted["output"]["status"] == "completed"
    assert not (root / "works/index/00003.json").exists()


def test_records_without_media_do_not_require_staging(output_catalogue):
    repo, _, root = output_catalogue
    staging = root.parent / "media-staging"
    staging.rmdir()
    for kind, record_id in (("work", "00003"), ("series", "011")):
        _, saved = handle_catalogue_post(repo, f"/{kind}/create", {
            f"{kind}_id": record_id, "record": {"title": "No media required", "year": 2026, "year_display": "2026"},
        })
        assert saved["output"]["status"] == "completed", saved
    assert not staging.exists()


def test_studio_serves_generated_thumbnails_and_rejects_paths_outside_output(output_catalogue, tmp_path):
    repo, _, root = output_catalogue
    thumbnail = root / "works/thumbs/00001-thumb-800.webp"
    thumbnail.parent.mkdir(parents=True)
    thumbnail.write_bytes(b"thumbnail bytes")
    outside = tmp_path / "outside.webp"
    outside.write_bytes(b"outside bytes")
    (thumbnail.parent / "outside.webp").symlink_to(outside)
    handler = object.__new__(StudioAppRequestHandler)
    handler.server = SimpleNamespace(repo_root=repo)
    handler.wfile = io.BytesIO()
    for method in ("send_response", "send_header", "end_headers", "send_error"):
        setattr(handler, method, Mock())
    route = "/studio/catalogue-output/works/thumbs/"
    assert handler.is_catalogue_media_path(route + thumbnail.name)
    handler.send_catalogue_media(route + thumbnail.name)
    handler.send_response.assert_called_once_with(200)
    handler.send_header.assert_any_call("Cache-Control", "no-store")
    assert handler.wfile.getvalue() == b"thumbnail bytes"
    for path in (route + "outside.webp", "/studio/catalogue-output/../source/works.json"):
        handler.send_catalogue_media(path)
        assert handler.send_error.call_args.args[0] == 404
    assert handler.wfile.getvalue() == b"thumbnail bytes"


def test_import_apply_completes_generated_output(output_catalogue):
    openpyxl = pytest.importorskip("openpyxl")
    repo, _, root = output_catalogue
    workbook_path = repo / "data/works_bulk_import.xlsx"
    workbook_path.parent.mkdir()
    workbook = openpyxl.Workbook()
    workbook.active.title = "Works"
    workbook.active.append(["work_id", "series_id", "title"])
    workbook.active.append(["42", "010", "Imported Work"])
    workbook.save(workbook_path)
    status, response = catalogue_post_response(repo, "/import-apply", {"mode": "works"})
    assert status == 200
    assert response["saved"] is True
    assert response["output"]["status"] == "completed", response
    assert read_json(root / "works/index/00042.json")["work"]["title"] == "Imported Work"
    assert read_json(root / "series/index/010.json")["member_works"][0]["work_id"] == "00042"


class MemoryMedia:
    def __init__(self):
        self.objects = {}
        self.fail_put = ""
        self.fail_delete = False

    def head_object(self, key):
        content = self.objects.get(key)
        return transport.RemoteObject(len(content), hashlib.md5(content).hexdigest()) if content is not None else None

    def put_object(self, key, path, content_type):
        if key == self.fail_put:
            raise RuntimeError("controlled upload failure")
        self.objects[key] = path.read_bytes()

    def delete_object(self, key):
        if self.fail_delete:
            raise RuntimeError("controlled cleanup failure")
        self.objects.pop(key, None)


@pytest.fixture
def media_client(output_catalogue, monkeypatch):
    _, _, root = output_catalogue
    source_root = root.parents[1] / "projects/alpha"
    (source_root / "details").mkdir(parents=True)
    (source_root / "cover.jpg").write_bytes(b"cover")
    (source_root / "details/detail.jpg").write_bytes(b"detail")
    client = MemoryMedia()

    def convert(source, width, target):
        target.write_bytes(source.read_bytes() + str(width).encode())
        return 0, ""

    monkeypatch.setattr(media, "run_ffmpeg_thumb", convert)
    monkeypatch.setattr(media, "run_ffmpeg_primary", convert)
    monkeypatch.setattr(media, "read_image_dims_px", lambda path: (640, 480))
    monkeypatch.setattr(transport, "load_r2_credentials", lambda **kwargs: None)
    monkeypatch.setattr(transport, "R2Client", lambda credentials: client)
    return client


def save_work(repo, source, record):
    return handle_catalogue_post(repo, "/work/save", {
        "work_id": "00001", "expected_record_hash": record_hash(records_from_json_source(source).works["00001"]), "record": record,
    })[1]


def test_save_completes_thumbnails_primary_downloads_and_confirmed_versions(output_catalogue, media_client):
    repo, source, root = output_catalogue
    generate_catalogue_json(repo, source, write=True)
    download = root.parent / "media-staging/works/files/00001-book.pdf"
    download.parent.mkdir(parents=True)
    download.write_bytes(b"pdf bytes")
    response = save_work(repo, source, {"downloads": [{"filename": download.name, "label": "Book"}]})
    assert response["output"]["status"] == "completed", response.get("output")
    work = read_json(root / "works/index/00001.json")
    assert work["work"]["media_version"] == 2
    assert work["work"]["width_px"] == 640
    assert work["sections"][0]["details"][0]["media_version"] == 2
    assert (root / work["work"]["media"]["thumbnails"][0]["path"]).is_file()
    assert media_client.objects["works/files/00001-book.pdf"] == b"pdf bytes"
    assert response["record_hash"] == record_hash(records_from_json_source(source).works["00001"])
    same = save_work(repo, source, {"title": "Alpha"})
    assert same["output"]["status"] == "completed"
    assert same["record"]["media_version"] == 2
    replacement = root.parents[1] / "projects/alpha/replacement.jpg"
    replacement.write_bytes(b"replacement image")
    os.utime(replacement, (1, 1))
    replaced = save_work(repo, source, {"project_filename": replacement.name})
    assert replaced["output"]["status"] == "completed"
    assert replaced["record"]["media_version"] == 3
    assert media_client.objects[f"works/img/00001-primary-{transport.PRIMARY_WIDTHS[0]}.webp"].startswith(b"replacement image")
    assert generate_catalogue_json(repo, source, write=True)["written"] == []


def test_series_membership_bulk_and_detail_section_share_output_completion(output_catalogue, media_client):
    repo, source, root = output_catalogue
    records = records_from_json_source(source)
    _, saved = handle_catalogue_post(repo, "/series/save", {
        "series_id": "010", "expected_record_hash": record_hash(records.series["010"]),
        "record": {"title": "Destination"},
        "work_updates": [{"work_id": "00001", "series_id": "010", "expected_record_hash": record_hash(records.works["00001"])}],
    })
    assert saved["output"]["status"] == "completed", saved
    assert read_json(root / "series/index/009.json")["member_works"] == []
    assert read_json(root / "series/index/010.json")["member_works"][0]["work_id"] == "00001"
    records = records_from_json_source(source)
    for kind, item_id, record in (("works", "00002", records.works["00002"]), ("work_details", "00001-001", records.work_details["00001-001"])):
        _, bulk = handle_catalogue_post(repo, "/bulk-save", {
            "kind": kind, "ids": [item_id], "expected_record_hashes": {item_id: record_hash(record)}, "set_fields": {"title": "Bulk title"},
        })
        assert bulk["output"]["status"] == "completed", bulk
    _, section = handle_catalogue_post(repo, "/work-detail-section/save", {
        "work_id": "00001", "section_id": "00001-1", "expected_record_hash": record_hash(records.work_detail_sections["00001-1"]),
        "section_title": "Updated section", "detail_sort": "title",
    })
    assert section["output"]["status"] == "completed", section
    output = read_json(root / "works/index/00001.json")
    assert output["sections"][0]["section_title"] == "Updated section"
    assert output["sections"][0]["details"][0]["title"] == "Bulk title"
    assert read_json(root / "works/index/00002.json")["work"]["title"] == "Bulk title"
    unchanged = handle_catalogue_post(repo, "/bulk-save", {
        "kind": "works", "ids": ["00002"], "expected_record_hashes": {"00002": record_hash(records_from_json_source(source).works["00002"])}, "set_fields": {"title": "Bulk title"},
    })[1]
    assert unchanged["changed_count"] == 0
    assert unchanged["output"]["status"] == "completed"
    assert unchanged["records"][0]["record_hash"] == record_hash(records_from_json_source(source).works["00002"])
    assert generate_catalogue_json(repo, source, write=True)["written"] == []


@pytest.mark.parametrize("filename", ["../other.pdf", "subfolder/file.pdf"])
def test_invalid_download_path_keeps_save_but_writes_no_remote_objects(output_catalogue, media_client, filename):
    repo, source, _ = output_catalogue
    saved = save_work(repo, source, {"downloads": [{"filename": filename, "label": "Invalid file"}]})
    assert saved["saved"] is True
    assert saved["output"]["status"] == "failed"
    assert filename in saved["output"]["error"]
    assert media_client.objects == {}


def test_incomplete_remote_set_preserves_saved_edit_and_only_promotes_complete_sets(output_catalogue, media_client):
    repo, source, root = output_catalogue
    media_client.fail_put = f"work_details/img/00001-001-primary-{transport.PRIMARY_WIDTHS[-1]}.webp"
    response = save_work(repo, source, {"title": "Saved despite failure"})
    records = records_from_json_source(source)
    assert response["output"]["status"] == "failed"
    assert records.works["00001"]["title"] == "Saved despite failure"
    assert records.works["00001"]["media_version"] == 2
    assert records.work_details["00001-001"]["media_version"] == 1
    assert not (root / "works/index/00001.json").exists()
    media_client.fail_put = ""
    fixed = save_work(repo, source, {"title": "Saved despite failure"})
    assert fixed["output"]["status"] == "completed"
    assert records_from_json_source(source).work_details["00001-001"]["media_version"] == 2


def test_delete_cleanup_is_exact_and_can_reconcile_from_existing_output(output_catalogue, media_client):
    repo, source, root = output_catalogue
    response = save_work(repo, source, {"title": "Alpha"})
    assert response["output"]["status"] == "completed"
    media_client.objects["archive/catalogue/works/img/00001-primary-800.webp"] = b"frozen"
    media_client.fail_delete = True
    deleted = handle_catalogue_post(repo, "/delete-apply", {"kind": "work_detail", "detail_uid": "00001-001", "expected_record_hash": record_hash(records_from_json_source(source).work_details["00001-001"])})[1]
    assert deleted["output"]["status"] == "failed"
    assert "00001-001" not in records_from_json_source(source).work_details
    media_client.fail_delete = False
    fixed = save_work(repo, source, {"title": "Alpha"})
    assert fixed["output"]["status"] == "completed", fixed["output"]
    assert not list((root / "work_details/thumbs").glob("00001-001-*"))
    assert not any(key.startswith("work_details/img/00001-001-") for key in media_client.objects)
    assert media_client.objects["archive/catalogue/works/img/00001-primary-800.webp"] == b"frozen"

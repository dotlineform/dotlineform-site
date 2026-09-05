"""Catalogue media source ownership and write-free derivative previews."""

from catalogue import catalogue_build_media as media
from catalogue.catalogue_source import CatalogueSourceRecords


def test_detail_source_uses_parent_media_identity_and_own_section_folder(tmp_path):
    base = tmp_path / "external"
    (base / "processing/ink-engine/details").mkdir(parents=True)
    records = CatalogueSourceRecords(
        works={"00001": {"work_id": "00001", "media_source_id": "processing", "project_folder": "ink-engine", "project_filename": "cover.jpg"}},
        series={},
        work_detail_sections={"00001-1": {"section_id": "00001-1", "work_id": "00001", "details_subfolder": "details"}},
        work_details={"00001-001": {"work_id": "00001", "detail_uid": "00001-001", "section_id": "00001-1", "project_filename": "detail.jpg"}},
    )
    env = {"DOTLINEFORM_PROJECTS_BASE_DIR": str(base)}
    source, missing, _, error = media.resolve_detail_media_source(records, "00001-001", env=env)
    assert source == base / "processing/ink-engine/details/detail.jpg"
    assert not missing and not error
    source, missing, _, error = media.resolve_work_media_source(records, "00001", env=env)
    assert source == base / "processing/ink-engine/cover.jpg"
    assert not missing and not error


def test_derivative_dry_run_does_not_invoke_converter_or_write(tmp_path):
    calls = []
    plan = {"tasks": [{"kind": "work", "id": "00001", "status": "pending"}]}
    result = media.execute_local_media_plan(
        tmp_path, scope={}, write=False, plan_builder=lambda *args, **kwargs: plan,
        thumb_runner=lambda *args: calls.append(args), primary_runner=lambda *args: calls.append(args),
    )
    assert result["planned"] == {"work": ["00001"], "work_details": []}
    assert calls == []
    assert list(tmp_path.iterdir()) == []

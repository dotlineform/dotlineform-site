"""Deletion changes canonical records while output and media remain paused."""

from http import HTTPStatus

import pytest

from catalogue_factory import write_catalogue_source
from catalogue.catalogue_delete_service import delete_apply_response
from catalogue.catalogue_revisions import CatalogueRevisionConflict, record_hash
from catalogue.catalogue_service_context import build_catalogue_write_context
from catalogue.catalogue_source import records_from_json_source, validate_source_records


@pytest.mark.parametrize("kind,record_id", [("series", "009"), ("work", "00001"), ("work_detail_section", "00001-1"), ("work_detail", "00001-001")])
def test_source_only_delete_preserves_independent_records(tmp_path, kind, record_id):
    source = write_catalogue_source(tmp_path)
    records = records_from_json_source(source)
    families = {"series": records.series, "work": records.works, "work_detail": records.work_details, "work_detail_section": records.work_detail_sections}
    output = tmp_path / "site/archive/works/00001/index.html"
    output.parent.mkdir(parents=True)
    output.write_text("frozen archive")
    context = build_catalogue_write_context(tmp_path)
    with pytest.raises(CatalogueRevisionConflict):
        delete_apply_response(context, {"kind": kind, "id": record_id, "expected_record_hash": "stale"})
    assert records_from_json_source(source) == records
    status, payload = delete_apply_response(context, {"kind": kind, "id": record_id, "expected_record_hash": record_hash(families[kind][record_id])})
    assert status == HTTPStatus.OK and payload["deleted"]
    updated = records_from_json_source(source)
    assert not validate_source_records(updated)
    assert output.read_text() == "frozen archive"
    assert "00002" in updated.works and "010" in updated.series
    if kind == "series":
        assert "009" not in updated.series
        assert "series_id" not in updated.works["00001"]
        assert updated.work_details == records.work_details
    else:
        assert not updated.work_details and not updated.work_detail_sections
        assert ("00001" in updated.works) == (kind != "work")

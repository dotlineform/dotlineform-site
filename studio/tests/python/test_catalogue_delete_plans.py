"""Deletion previews validate canonical relationships without output cleanup plans."""

from catalogue_factory import write_catalogue_source
from catalogue.catalogue_delete_plans import build_delete_preview
from catalogue.catalogue_source import records_from_json_source


def test_series_delete_preview_clears_membership_without_deleting_works(tmp_path):
    source = write_catalogue_source(tmp_path)
    before = records_from_json_source(source)
    preview = build_delete_preview(source, "series", "009")
    assert not preview["blocked"]
    assert preview["affected"] == {"works": ["00001"], "series": ["009"], "work_details": []}
    assert preview["cleanup"] == {}
    assert records_from_json_source(source) == before

"""Studio lookup refresh follows canonical changes independently of output generation."""

import json

from catalogue_factory import write_catalogue_source
from catalogue import catalogue_lookup_refresh as refresh
from catalogue.catalogue_source import records_from_json_source, write_source_record_payloads
from catalogue.catalogue_lookup import build_work_search_payload, build_series_lookup_payload
from catalogue.catalogue_revisions import record_hash


def test_metadata_only_save_refreshes_revision_and_reassignment_refreshes_both_series(tmp_path):
    source = write_catalogue_source(tmp_path)
    lookup = tmp_path / "lookup"
    for update in ({"provenance": "Updated"}, {"series_id": "010"}):
        records = records_from_json_source(source)
        before = dict(records.works["00001"])
        records.works["00001"].update(update)
        write_source_record_payloads(source, records)
        plan = refresh.derive_lookup_refresh_plan(record_family="work", changed_field_names=list(update))
        result = refresh.work_change_lookup_refresh(source, lookup, tmp_path, work_id="00001", current_record=before, updated_record=records.works["00001"], lookup_plan=plan)
        assert result["written_count"] >= 3
        search = json.loads((lookup / "work_search.json").read_text())
        assert search == build_work_search_payload(records)
        for sid in {before.get("series_id"), records.works["00001"].get("series_id")}:
            assert json.loads((lookup / "series" / (sid + ".json")).read_text()) == build_series_lookup_payload(records, sid)
        assert build_series_lookup_payload(records, records.works["00001"]["series_id"])["member_works"][0]["record_hash"] == record_hash(records.works["00001"])

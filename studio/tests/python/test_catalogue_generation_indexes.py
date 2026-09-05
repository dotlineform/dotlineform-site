"""Series ordering and independent membership in generated Catalogue indexes."""

from catalogue import catalogue_generation_indexes as indexes


def test_series_ordering_uses_title_numbers_and_explicit_sort_direction():
    series = {"009": {"series_id": "009", "title": "Numbers", "sort_fields": "title"}}
    works = {
        "00001": {"work_id": "00001", "title": "Work 10", "year": 2021, "series_id": "009"},
        "00002": {"work_id": "00002", "title": "Work 2", "year": 2022, "series_id": "009"},
        "00003": {"work_id": "00003", "title": "Work 1", "year": 2023, "series_id": "009"},
    }
    context = indexes.build_series_work_index_context(series_records=series, work_records=works)
    assert indexes.ordered_work_ids_by_series(context)["009"] == ["00003", "00002", "00001"]
    series["009"]["sort_fields"] = "year"
    context = indexes.build_series_work_index_context(series_records=series, work_records=works)
    assert indexes.ordered_work_ids_by_series(context)["009"] == ["00001", "00002", "00003"]
    series["009"]["sort_fields"] = "-year"
    context = indexes.build_series_work_index_context(series_records=series, work_records=works)
    assert indexes.ordered_work_ids_by_series(context)["009"] == ["00003", "00002", "00001"]


def test_series_index_includes_empty_series_and_leaves_ungrouped_works_independent():
    series = {"009": {"series_id": "009", "title": "Empty"}}
    works = {"00001": {"work_id": "00001", "title": "Independent"}}
    context = indexes.build_series_work_index_context(series_records=series, work_records=works)
    assert indexes.build_series_index_records(series_records=series, context=context) == {
        "009": {"series_id": "009", "title": "Empty", "work_count": 0}
    }
    assert indexes.build_series_member_work_records(context=context, series_id="009") == []

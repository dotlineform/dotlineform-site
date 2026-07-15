---
doc_id: catalogue-per-work-detail-source
title: Catalogue Per-Work Detail Source
added_date: 2026-06-22
last_updated: 2026-07-15
parent_id: studio
viewable: true
---
# Catalogue Per-Work Detail Source

## Source Boundary

Work details are stored as one canonical aggregate per Work:

```text
studio/data/canonical/catalogue/work_details/<work_id>.json
```

- `works.json` owns primary Work metadata.
- A Work with details has one detail file; a Work without details has no file.
- Each file owns the Work's ordered detail sections and their nested detail records.
- Empty sections are invalid because section creation starts with one or more selected images.

This structure matches the [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor): detail sections are created, browsed, and deleted as Work-owned aggregates rather than as independent Studio records.

## Record Shape

The file-level `work_id` identifies the parent Work.

A section owns:

- stable `section_id`;
- title and source-media subfolder;
- optional section ordering and detail-sort rules;
- its nested `details` array.

A detail owns:

- stable `detail_uid` and child-local `detail_id`;
- title and source filename;
- generated dimensions when known.

`work_id` and `section_id` are structurally implied for nested details and should not be repeated there. The canonical schema and serializers in `studio/services/catalogue/catalogue_source.py` are the exact authority; this page intentionally does not reproduce the complete JSON schema.

## Read Models

The browser never reads canonical detail files directly.

- `catalogue_work_record` combines one canonical Work, its detail sections, and the generated context needed by the Work editor.
- `catalogue_work_detail_record` resolves one `detail_uid` to its parent Work file and returns a focused detail projection. It remains a service capability even though there is no standalone Work-detail editor route.
- Work and Series search payloads remain generated list projections and do not contain the full detail source.

The Local Studio read boundary is `GET /studio/api/catalogue/read`; dispatch lives in `studio/app/server/studio/studio_catalogue_api.py`, and projection builders live in `studio/services/catalogue/catalogue_lookup.py`.

## Mutation And Generation

Section creation and deletion use `studio/services/catalogue/catalogue_detail_section_service.py`. The service validates the combined Work/detail state, writes the affected per-Work file atomically, refreshes relevant projections, and coordinates media or cleanup work.

Targeted edit, preview, build, and delete operations should load only the affected Work aggregate. Global loading is appropriate for work that is inherently global, including:

- full source validation;
- full catalogue or search builds;
- workbook import/export validation;
- orphan and stale-artifact audits.

Public detail JSON and media remain generated outputs. They do not become canonical merely because the browser or public site consumes them.

## Why This Method

Per-Work files make the ownership and write boundary explicit, reduce the amount of canonical data needed for a focused operation, and keep a Work plus its details understandable as one aggregate.

The service layer hides the storage shape from consumers. Callers should ask to load a Work aggregate, resolve a detail, or serialize an affected aggregate; they should not depend on whether canonical storage is flat, nested, or split across files.

## Extension And Weak Spots

- Add section-level metadata to the section schema and projection builder, not to every nested detail.
- Add detail-level metadata to the nested record and resolve inherited parent context in the service projection.
- Keep global flattening inside catalogue services that genuinely need it.
- Individual detail mutations are supported by lower-level catalogue helpers and legacy flows, but the active Studio UI deliberately exposes section-level management only.
- Several global catalogue services still normalize per-Work files into in-memory maps. That compatibility is useful, but it can obscure whether a new workflow is truly targeted or is accidentally scanning the whole corpus.

Tests around source loading, detail-section transactions, focused projections, delete planning, and catalogue generation are the authority for exact current behavior.

---
doc_id: catalogue-new-work-detail-editor
title: "New Catalogue Work Detail"
added_date: 2026-04-18
last_updated: 2026-04-29
parent_id: user-guide
sort_order: 60
---
# New Catalogue Work Detail

Route:

- `/studio/catalogue-new-work-detail/`
- focused create flow accepts `?work=<work_id>`

This legacy page creates a new canonical work-detail source record in `assets/studio/data/catalogue/work_details.json`.

The main work-detail editor also supports parent-scoped create mode at `/studio/catalogue-work-detail/?work=<work_id>&mode=new`. This page remains available until route migration retires the standalone create implementation.

Implementation note: this legacy create route now consumes the same work-detail field definitions, id normalization, draft validation, next-id suggestion, and create payload helper as the main work-detail editor.

## Current Scope

The first implementation is draft-first:

- create a new detail under an existing work
- derive or suggest the next `detail_id` for that work
- enter core draft detail metadata
- save the new detail with `status = draft`
- redirect into the main work-detail editor after create

## Media Boundary

This page does not upload or copy media.

It only captures the source metadata fields that point at the existing detail media conventions such as:

- `project_subfolder`
- `project_filename`

## Related References

- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

---
doc_id: catalogue-new-work-detail-editor
title: "New Catalogue Work Detail"
last_updated: 2026-04-18
parent_id: studio
sort_order: 110
---
# New Catalogue Work Detail

Route:

- `/studio/catalogue-new-work-detail/`
- focused create flow accepts `?work=<work_id>`

This page creates a new canonical work-detail source record in `assets/studio/data/catalogue/work_details.json`.

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

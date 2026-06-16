---
doc_id: catalogue-work-detail-editor
title: Catalogue Work Detail Editor
added_date: 2026-04-22
last_updated: 2026-06-16
parent_id: studio
viewable: true
---
# Catalogue Work Detail Editor

Status: retired

The standalone Studio route `/studio/catalogue-work-detail/` has been removed.

Retired surfaces:

- Studio route registry entry and served route
- frontend route shell, editor, state, form, selection, action, event, and UI-text modules
- local Studio `POST /studio/api/catalogue/work-detail/create`
- local Studio `POST /studio/api/catalogue/work-detail/save`
- catalogue write-service `/work-detail/create` and `/work-detail/save` dispatch

Current work-detail browsing lives on [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor). That browser reads generated work lookup `detail_sections[]`, where section metadata is projected once per section and nested detail summaries contain only detail-owned fields.

Canonical work-detail source is still stored in `studio/data/canonical/catalogue/work_details.json`, but it now uses the v2 split model:

- `work_detail_sections` for `details_subfolder`, `section_title`, `section_order`, and `detail_sort`
- `work_details` for `detail_uid`, `work_id`, `detail_id`, `section_id`, `title`, `project_filename`, and generated dimensions

Future work-detail editing should be implemented as work-scoped modals and APIs that operate on sections and details together. Do not restore the retired standalone route or adapt the old create/save endpoints as a compatibility layer.

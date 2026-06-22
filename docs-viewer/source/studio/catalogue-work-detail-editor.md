---
doc_id: catalogue-work-detail-editor
title: Catalogue Work Detail Editing
added_date: 2026-04-22
last_updated: 2026-06-22
parent_id: studio
viewable: true
---
# Catalogue Work Detail Editing

Work-detail browsing lives on [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor). That browser reads the service-only `catalogue_work_record` projection, where section metadata is projected once per section and nested detail summaries contain only detail-owned fields.

Canonical work-detail source is stored as one file per detailed work under `studio/data/canonical/catalogue/work_details/<work_id>.json`:

- section records own `details_subfolder`, `section_title`, `section_order`, `detail_sort`, and nested details
- nested details own `detail_uid`, `detail_id`, `title`, `project_filename`, and generated dimensions
- `work_id` is implied by the file and `section_id` is implied by the containing section
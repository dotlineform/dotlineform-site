---
doc_id: catalogue-new-series-editor
title: "New Catalogue Series"
added_date: 2026-04-17
last_updated: 2026-04-26
parent_id: user-guide
sort_order: 80
---
# New Catalogue Series

Route:

- `/studio/catalogue-new-series/`

This page creates a new canonical series source record in `assets/studio/data/catalogue/series.json`.

## Current Scope

The first implementation is intentionally narrow:

- create a new `series_id`
- enter draft series metadata
- save the new series with `status = draft`
- omit `primary_work_id` at create time
- redirect into the main series editor after create

Member works and `primary_work_id` are completed in the standard series editor after the draft series exists.

Series prose is imported separately through the staged Markdown flow and stored under `_docs_src_catalogue/series/<series_id>.md`.

## Draft And Publish Boundary

Current rule:

- source save may create a draft series without `primary_work_id`
- scoped build remains blocked until the series has a valid `primary_work_id`
- the series editor is the place to add members, assign `primary_work_id`, and rebuild

## Related References

- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)

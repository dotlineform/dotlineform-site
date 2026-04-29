---
doc_id: catalogue-new-work-editor
title: "New Catalogue Work"
added_date: 2026-04-18
last_updated: 2026-04-29
parent_id: user-guide
sort_order: 40
---
# New Catalogue Work

Route:

- `/studio/catalogue-new-work/`

This route is now a compatibility redirect to `/studio/catalogue-work/?mode=new`.

The standalone new-work editor surface is retired. New work creation now happens in the unified [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor), which shares the normal work metadata form and switches between open/edit and new draft modes.

## Current Behavior

The route:

- redirects immediately to `/studio/catalogue-work/?mode=new`
- has no standalone create controller; the old `assets/studio/js/catalogue-new-work-editor.js` implementation has been removed
- is no longer represented by a `catalogue_new_work_editor` route key or UI text block in `studio_config.json`

## Replacement Workflow

Use `/studio/catalogue-work/?mode=new` or the `New` button on `/studio/catalogue-work/`.

The unified new mode:

- creates draft work source records
- keeps `status` visible and fixed to `draft` while creating
- requires `work_id`, `title`, `year`, `year_display`, and `series_ids`
- opens the created record in normal edit mode after create
- leaves public-site update unavailable until the draft exists

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Drafts](/docs/?scope=studio&doc=catalogue-status)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)

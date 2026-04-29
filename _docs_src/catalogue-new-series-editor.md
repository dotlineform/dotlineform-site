---
doc_id: catalogue-new-series-editor
title: "New Catalogue Series"
added_date: 2026-04-17
last_updated: 2026-04-29
parent_id: user-guide
sort_order: 80
---
# New Catalogue Series

Route:

- `/studio/catalogue-new-series/`

This route is now a compatibility redirect to `/studio/catalogue-series/?mode=new`.

## Current Status

Series creation now lives in the main [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor).

The compatibility route:

- keeps old links from becoming dead ends
- redirects immediately to `/studio/catalogue-series/?mode=new`
- has no standalone create controller; the old `assets/studio/js/catalogue-new-series-editor.js` implementation has been removed
- no longer owns active route or UI text entries in `studio_config.json`

Use `/studio/catalogue-series/` as the active route for both creating and editing series records.

## Draft And Publish Boundary

The current rule is unchanged:

- source save may create a draft series without `primary_work_id`
- scoped build remains blocked until the series has a valid `primary_work_id`
- the series editor is the place to add members, assign `primary_work_id`, and rebuild

## Related References

- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Series Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-series-unified-editor)

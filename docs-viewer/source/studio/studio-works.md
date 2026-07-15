---
doc_id: studio-works
title: Catalogue Works
added_date: 2026-04-01
last_updated: 2026-07-15
parent_id: studio
viewable: true
---
# Catalogue Works

## What It Does

`/studio/studio-works/` is a read-only catalogue index with Studio-only storage context and curator sorting.

Use it to:

- scan all public Work rows;
- sort by catalogue ID, year, title, Series, or storage location;
- focus the list on one Series with `?series=<series_id>`;
- preserve sort and Series context when following public Work links;
- copy the alphabetical Series-title list.

Editing belongs in the [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor).

## Data And Ownership

The page deliberately combines three read models:

- `/assets/data/works_index.json` for public Work rows;
- `/assets/data/series_index.json` for public Series context and Series ordering;
- `/studio/data/generated/activity/work-storage-index.json` for curator-only storage values.

The public indexes define what the published catalogue exposes. The Studio-only storage index augments those rows without leaking curator metadata into public catalogue payloads.

`studio/app/frontend/js/studio-works.js` owns loading, filtering, sorting, link-state propagation, and rendering. `catalogue-public-links.js` resolves public-preview URLs when Studio and the preview site use different local hosts.

## Extension And Weak Spots

- Add a public display column only when its value belongs in the public index.
- Add curator-only context through a Studio-owned projection, not by expanding public payloads.
- Keep sort keys and row data attributes aligned in `studio-works.js` and the route template.
- The page depends on generated public and Studio indexes being mutually current; it is not a canonical-source diagnostic surface.

The route uses `#worksStudioRoot` for the shared [Route Ready State](/docs/?scope=studio&doc=route-ready-state). Focused smoke coverage begins in `studio/tests/smoke/local_studio_app_studio_works_route.py`.

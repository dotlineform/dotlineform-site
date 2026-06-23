---
doc_id: data-models-catalogue-indexes
title: Catalogue Indexes And Payloads
added_date: 2026-05-19
last_updated: 2026-06-23
parent_id: studio
viewable: true
---
# Catalogue Indexes And Payloads

## Shared Catalogue Indexes

### `site/assets/data/series_index.json`

Purpose:

- canonical lookup map for series-level list and membership data

Current content families:

- series identity and publishing state
- list-card display metadata
- ordered work membership
- `primary_work_id`
- sort metadata used elsewhere in the catalogue and Studio

Current consumers:

- `/series/` in works mode
- `/series/<series_id>/`
- `/works/<work_id>/` when series context is needed for prev/next navigation
- Studio pages that need canonical series membership context

Why it exists separately:

- series list and membership data is needed in multiple places
- pages should not fetch every per-series record just to build a grid or navigation context

### `site/assets/data/works_index.json`

Purpose:

- lightweight lookup map for works used by grids, titles, and cross-scope references

Current content families:

- work identity
- title and year display
- series membership

Current consumers:

- `/series/<series_id>/` for work cards
- Studio pages that need fast work lookup without loading every work record

Why it stays lightweight:

- the work page’s full detail/prose payload is much larger
- series grids need fast bulk access to many works at once

### `site/assets/data/recent_index.json`

Purpose:

- snapshot ledger for the public `/recent/` page

Current content families:

- recent publication entry kind: `series` or `work`
- target id for route resolution
- snapshot title and caption text
- publication date
- thumbnail indirection via `thumb_id`
- lightweight write-order metadata for stable same-day ordering

Current consumers:

- `/recent/`

Why it is a separate derived artifact:

- the page needs publish-event history, not just current catalogue state
- snapshot titles and captions intentionally do not track later title edits or work-to-series moves
- deleted or unpublished targets can be pruned centrally by the generator when the catalogue rebuilds

### `site/assets/data/moments_index.json`

Purpose:

- lightweight lookup map for moments in the merged catalogue

Current content families:

- moment identity
- title and date display
- thumbnail indirection via `thumb_id`

Current consumers:

- `/series/` in moments mode

Why it is separate from the per-moment record:

- the merged catalogue only needs card metadata
- loading prose and image metadata for every moment card would be unnecessary

## Per-Record Catalogue Payloads

### `site/assets/series/index/<series_id>.json`

Purpose:

- page-local payload for one series page

Current content families:

- page-local series metadata
- rendered prose as `content_html`

Membership and thumbnail selection do not live in this payload. Public list and
grid contexts should read `site/assets/data/series_index.json` instead.

Current site mapping:

- `/series/<series_id>/`

Why it exists:

- the page needs prose and enough series metadata to update the local header
- shared membership and card context belong in the aggregate index so consumers do not fetch every per-series record

### `site/assets/works/index/<work_id>.json`

Purpose:

- page-local payload for one work and its detail structure

Current content families:

- canonical work metadata
- rendered prose as optional `content_html`
- `sections[]`
- ordered detail records grouped by section; nested detail records carry detail identity, title, and dimensions only, not route layout metadata

Current route mapping:

- `/works/?work=<work_id>`
- `/work-details/?detail=<detail_uid>`

Why it is the most important catalogue record:

- the work page needs richer metadata than the index provides
- the detail page derives its canonical title, ordering, and back-link context from the parent work record
- avoiding a separate global detail index reduces duplication and keeps detail ordering local to the work that owns it
- work prose is optional, so the record still exists even when `_docs_catalogue/works/<work_id>.md` is missing

### Retired `site/assets/moments/index/<moment_id>.json`

Purpose:

- retired page-local payload for one moment

Former content families:

- generated runtime moment metadata
- rendered prose as `content_html`
- image list and dimensions

Current route mapping:

- selected moments render through the public Docs Viewer moments scope at `/moments/?doc=<moment_doc_id>`
- current payloads live under `site/assets/data/docs/scopes/moments/index-tree.json` and `site/assets/data/docs/scopes/moments/by-id/<moment_doc_id>.json`

Why it is retired:

- the public moment page now uses Docs Viewer scope payloads for prose, metadata, and routing
- the merged catalogue list still uses lightweight moment index data where needed

## Catalogue Search Model

### `site/assets/data/search/catalogue/index.json`

Purpose:

- search-owned flat index for `works`, `series`, and `moments`

Current content families:

- one `entries[]` array across all three catalogue kinds
- per-entry display metadata and route href
- normalized search terms and combined `search_text`
- selected structured fields such as series relationships and work medium type from per-work JSON
- work-only search enrichment terms such as `medium_caption` folded into derived search fields from per-work JSON

Current site mapping:

- `/search/?scope=catalogue`

Why it is separate from the main indexes:

- search needs a flattened, text-oriented shape
- list/runtime pages need lookup-oriented shapes
- keeping those concerns separate avoids bloating the runtime indexes used by ordinary pages

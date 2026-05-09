---
doc_id: site-request-analytics-tag-route-cleanup
title: Analytics Tag Route Cleanup Request
added_date: 2026-05-09
last_updated: "2026-05-09 16:00"
ui_status: done
parent_id: change-requests
sort_order: 213
viewable: true
---
# Analytics Tag Route Cleanup Request

Status: implemented.

## Purpose

Move the existing tag Studio pages under the Analytics route namespace so UI routing matches the product/domain model before the tag write-server structural review and script folder reorganization continue.

Tags are conceptually an Analytics metadata layer over catalogue works and series.
The docs already place tag pages under the Analytics parent, and `/studio/analytics/` already links to the tag pages.
The page routes now live under `/studio/analytics/`.

## Context

The retired historical routes were:

- `/studio/tag-registry/`
- `/studio/tag-aliases/`
- `/studio/tag-groups/`
- `/studio/series-tags/`
- `/studio/series-tag-editor/?series=<series_id>`

The canonical Analytics routes are:

- `/studio/analytics/tag-registry/`
- `/studio/analytics/tag-aliases/`
- `/studio/analytics/tag-groups/`
- `/studio/analytics/series-tags/`
- `/studio/analytics/series-tag-editor/?series=<series_id>`

This cleanup was completed before the `tag_write_server.py` structural review moves into implementation slices that touch route/activity context.
It also settles the route ownership before the scripts directory reorganization.

## Scope

In scope:

- move all tag page routes under `/studio/analytics/`
- update `/studio/analytics/` dashboard links
- update `assets/studio/data/studio_config.json` route values
- update `assets/studio/data/activity_contract.json` route metadata for tag pages
- update docs that list the tag page routes
- update Studio smoke-test route references and readiness expectations
- update any hardcoded links from tag page controllers
- document that old routes have no redirects or aliases

Out of scope:

- changing tag write-server endpoint URLs such as `/save-tags` or `/import-tag-registry`
- moving `scripts/studio/tag_write_server.py` or extracted helper modules
- renaming `tag_write_server.py` to `analytics_server.py`
- changing tag data schemas, registry semantics, scoring semantics, or Analytics export/import stubs
- redesigning the tag pages

## Compatibility Decision

Implemented behavior:

- new canonical routes live under `/studio/analytics/`
- old `/studio/tag-registry/`, `/studio/tag-aliases/`, `/studio/tag-groups/`, `/studio/series-tags/`, and `/studio/series-tag-editor/` routes were removed without compatibility redirects or aliases
- docs and config should use the new canonical routes
- tests should target the new canonical routes

This deliberately avoids a separate cleanup pass for temporary compatibility pages.

## Implementation Plan

### Slice 1: route inventory

Confirm every current route reference before editing:

- Studio page templates under `studio/`
- `assets/studio/data/studio_config.json`
- `assets/studio/data/activity_contract.json`
- dashboard links in `studio/analytics/index.md`
- page controllers under `assets/studio/js/`
- smoke tests and route-ready docs
- tag reference docs under `_docs/`

Acceptance checks:

- route inventory lists all hardcoded old routes
- compatibility approach is chosen before moving files

### Slice 2: page route move

Create the canonical Analytics tag routes and update source templates.

Expected target paths:

- `studio/analytics/tag-registry/index.md`
- `studio/analytics/tag-aliases/index.md`
- `studio/analytics/tag-groups/index.md`
- `studio/analytics/series-tags/index.md`
- `studio/analytics/series-tag-editor/index.md`

Expected canonical permalinks:

- `/studio/analytics/tag-registry/`
- `/studio/analytics/tag-aliases/`
- `/studio/analytics/tag-groups/`
- `/studio/analytics/series-tags/`
- `/studio/analytics/series-tag-editor/`

Acceptance checks:

- pages render at the new canonical routes
- route roots keep the same `data-studio-ready`, `data-studio-busy`, `data-studio-mode`, `data-studio-service`, and `data-studio-record-loaded` contracts
- old route behavior is deliberately removed according to the compatibility decision

### Slice 3: config, activity, and link updates

Update canonical route references:

- Analytics dashboard links
- Studio config route values
- activity contract route metadata
- inter-page links from series list to editor
- docs references and examples
- smoke tests and route-ready docs

Acceptance checks:

- `rg "/studio/tag-registry|/studio/tag-aliases|/studio/tag-groups|/studio/series-tags|/studio/series-tag-editor"` shows only deliberate historical notes
- activity contract tests still pass
- Studio smoke tests target the new canonical routes

### Slice 4: verification and closeout

Run targeted verification:

- route-ready smoke checks for the five canonical routes
- activity contract tests
- relevant Studio smoke tests if route references changed there
- Jekyll build to a separate destination if a local server is already running
- rebuild Studio docs/search payloads when docs change

Closeout docs:

- update [Analytics Plan](/docs/?scope=studio&doc=new-pipeline-refine-analytics)
- update [Series Tags](/docs/?scope=studio&doc=series-tags)
- update [Tag Registry](/docs/?scope=studio&doc=tag-registry)
- update [Tag Aliases](/docs/?scope=studio&doc=tag-aliases)
- update [Tag Groups](/docs/?scope=studio&doc=tag-groups)
- update [Tag Editor](/docs/?scope=studio&doc=tag-editor)
- update [Tag Write Server Slices](/docs/?scope=studio&doc=site-request-script-structural-review-tag-write-server) to note that UI route cleanup is complete

## Benefits

- aligns visible Studio URLs with the Analytics domain model
- reduces conceptual ambiguity before tag service restructuring
- gives script folder organization a clearer target domain
- keeps tag pages discoverable through the Analytics dashboard and docs tree

## Risks

- route changes can break local bookmarks or hardcoded links
- activity contract route metadata can drift from page paths
- local bookmarks to old routes now fail rather than redirecting
- any missed hardcoded old route now fails immediately instead of being masked by an alias

## Closeout

The implementation moved the page templates, route config, activity metadata, hardcoded activity contexts, route docs, and smoke-test route references to the Analytics namespace.

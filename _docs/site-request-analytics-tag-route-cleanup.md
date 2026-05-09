---
doc_id: site-request-analytics-tag-route-cleanup
title: Analytics Tag Route Cleanup Request
added_date: 2026-05-09
last_updated: "2026-05-09 15:45"
ui_status: proposed
parent_id: change-requests
sort_order: 213
viewable: true
---
# Analytics Tag Route Cleanup Request

Status: proposed.

## Purpose

Move the existing tag Studio pages under the Analytics route namespace so UI routing matches the product/domain model before the tag write-server structural review and script folder reorganization continue.

Tags are conceptually an Analytics metadata layer over catalogue works and series.
The docs already place tag pages under the Analytics parent, and `/studio/analytics/` already links to the tag pages.
The remaining mismatch is that the page routes still live directly under `/studio/`.

## Context

The current routes are historical:

- `/studio/tag-registry/`
- `/studio/series-tags/`
- `/studio/series-tag-editor/?series=<series_id>`

The desired Analytics routes are:

- `/studio/analytics/tag-registry/`
- `/studio/analytics/series-tags/`
- `/studio/analytics/series-tag-editor/?series=<series_id>`

This cleanup should happen before the `tag_write_server.py` structural review moves into implementation slices that touch route/activity context.
It should also happen before the scripts directory reorganization, because script folders should follow settled UI/domain ownership rather than trying to force it.

## Scope

In scope:

- move or alias the three tag page routes under `/studio/analytics/`
- update `/studio/analytics/` dashboard links
- update `assets/studio/data/studio_config.json` route values
- update `assets/studio/data/activity_contract.json` route metadata for tag pages
- update docs that list the tag page routes
- update Studio smoke-test route references and readiness expectations
- update any hardcoded links from tag registry, series tags, and tag editor controllers
- decide and document compatibility behavior for old routes

Out of scope:

- changing tag write-server endpoint URLs such as `/save-tags` or `/import-tag-registry`
- moving `scripts/studio/tag_write_server.py` or extracted helper modules
- renaming `tag_write_server.py` to `analytics_server.py`
- changing tag data schemas, registry semantics, scoring semantics, or Analytics export/import stubs
- redesigning the tag pages

## Compatibility Decision

Preferred behavior:

- new canonical routes live under `/studio/analytics/`
- old `/studio/tag-registry/`, `/studio/series-tags/`, and `/studio/series-tag-editor/` routes should remain as short-term compatibility redirects or lightweight aliases if Jekyll routing supports that cleanly
- docs and config should use the new canonical routes
- tests should target the new canonical routes

If redirects add too much complexity, keep the old pages as compatibility aliases for one pass, but make the canonical route explicit in docs and follow up with removal once local links have moved.

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
- `studio/analytics/series-tags/index.md`
- `studio/analytics/series-tag-editor/index.md`

Expected canonical permalinks:

- `/studio/analytics/tag-registry/`
- `/studio/analytics/series-tags/`
- `/studio/analytics/series-tag-editor/`

Acceptance checks:

- pages render at the new canonical routes
- route roots keep the same `data-studio-ready`, `data-studio-busy`, `data-studio-mode`, `data-studio-service`, and `data-studio-record-loaded` contracts
- old route behavior is either redirected, aliased, or deliberately removed according to the compatibility decision

### Slice 3: config, activity, and link updates

Update canonical route references:

- Analytics dashboard links
- Studio config route values
- activity contract route metadata
- inter-page links from series list to editor
- docs references and examples
- smoke tests and route-ready docs

Acceptance checks:

- `rg "/studio/tag-registry|/studio/series-tags|/studio/series-tag-editor"` shows only deliberate compatibility notes or historical changelog entries
- activity contract tests still pass
- Studio smoke tests target the new canonical routes

### Slice 4: verification and closeout

Run targeted verification:

- route-ready smoke checks for the three canonical routes
- activity contract tests
- relevant Studio smoke tests if route references changed there
- Jekyll build to a separate destination if a local server is already running
- rebuild Studio docs/search payloads when docs change

Closeout docs:

- update [Analytics Plan](/docs/?scope=studio&doc=new-pipeline-refine-analytics)
- update [Series Tags](/docs/?scope=studio&doc=series-tags)
- update [Tag Registry](/docs/?scope=studio&doc=tag-registry)
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
- smoke tests may pass old aliases unless they are explicitly updated to canonical routes
- Jekyll permalink aliases or redirects may add clutter if not kept intentionally short-lived

## Recommended Next Step

Start with the route inventory and compatibility decision.
This should be a small, self-contained request and is likely suitable for a one-session implementation if compatibility behavior stays simple.

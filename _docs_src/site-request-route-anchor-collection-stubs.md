---
doc_id: site-request-route-anchor-collection-stubs
title: Route-Anchor Collection Stubs Spec
added_date: 2026-04-30
last_updated: 2026-04-30
parent_id: site-request-field-aware-build-scoping
sort_order: 5
---
# Route-Anchor Collection Stubs Spec

Status:

- implemented

## Summary

This spec defines the pre-analysis cleanup for generated Jekyll collection Markdown files.

The catalogue pages are JSON-first at runtime, and generated collection stubs now avoid mutable metadata and checksums. The previous model let a metadata-only edit rewrite `_works/*.md`, `_work_details/*.md`, `_series/*.md`, or `_moments/*.md`, which woke Jekyll as if a route page changed.

The implemented model is simpler:

- collection Markdown files are route anchors only
- generated JSON artifacts own runtime page content
- metadata-only saves do not rewrite collection Markdown stubs
- stubs are written only when route identity changes, a route is created, or a route is removed

This is part of Task 0 in [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping).

## Route Contract

Jekyll collections currently provide clean static routes:

| Collection | Route | Current generated stub |
|---|---|---|
| `works` | `/works/<work_id>/` | `_works/<work_id>.md` |
| `work_details` | `/work_details/<detail_uid>/` | `_work_details/<detail_uid>.md` |
| `series` | `/series/<series_id>/` | `_series/<series_id>.md` |
| `moments` | `/moments/<moment_id>/` | `_moments/<moment_id>.md` |

The public page layouts already load most meaningful page content from JSON:

| Page | Primary runtime JSON |
|---|---|
| work | `assets/works/index/<work_id>.json` |
| work detail | parent work JSON at `assets/works/index/<work_id>.json` |
| series | `assets/data/series_index.json`, `assets/data/works_index.json`, and focused series JSON where needed |
| moment | `assets/moments/index/<moment_id>.json` |

The collection files are now route anchors. Runtime content comes from generated JSON payloads.

## Target Contract

Generated collection stubs contain no mutable catalogue metadata:

- no title
- no year or date
- no dimensions
- no series membership
- no parent work title
- no rendered prose
- no downloads or links
- no metadata checksum

The route identity comes from the filename and Jekyll's `page.slug`.

The generated stub shape is:

```md
---
---
```

Do not repeat `layout` in generated front matter. `_config.yml` already assigns stable collection layouts, and those layouts are not expected to vary per generated route.

## Runtime Responsibilities

Layouts and client scripts should treat the stub as a route shell only.

| Page | Route identity source | Runtime data source |
|---|---|---|
| work | `page.slug` | focused work JSON |
| work detail | `page.slug` as `detail_uid`; derive `work_id` from the `detail_uid` prefix | parent work JSON |
| series | `page.slug` | series and works indexes, plus focused series JSON where needed |
| moment | `page.slug` | focused moment JSON |

Server-rendered fallback payloads should be removed where they serialize mutable front matter. The page shell may still render stable structural attributes such as base URLs, media base paths, pipeline-derived image variant settings, and route IDs.

Client-side loading states should handle the short gap before JSON arrives. Loading text should come from config and use:

- `loading...`

Complete JSON failure should use config-backed text:

- `info not available`

The site does not need to preserve a non-JavaScript fallback catalogue experience.

Client scripts should update `document.title` after JSON loads so browser titles follow runtime metadata rather than route IDs.

## Generator Responsibilities

The generator:

- creates missing stubs for published routes
- removes stale stubs when public routes are deleted or unpublished through cleanup flows
- avoids rewriting existing stubs for metadata-only changes
- normalizes older metadata-bearing stubs only when `--force` is used
- avoids checksums based on source metadata for route-anchor stubs
- keeps route-stub writes deterministic

Metadata checksums and payload versions should move to the JSON artifacts that actually serialize the metadata.

## Write-Server Responsibilities

Studio save flows should not treat route-stub rewrites as a normal metadata-save side effect.

For metadata-only saves:

- route stubs should be skipped
- local media should be skipped unless media-affecting fields changed
- JSON artifacts should be selected by the field-aware planner

For structural operations:

- create should create the necessary route stub when a public route becomes visible
- delete and unpublish should remove the route stub through the existing generated-artifact cleanup path
- ID-changing operations, if ever supported, should be treated as route removal plus route creation

## Audit Responsibilities

Audit and consistency checks should validate route existence, not metadata equivalence in the stubs.

Expected checks:

- each public work route has `_works/<work_id>.md`
- each public detail route has `_work_details/<detail_uid>.md`
- each public series route has `_series/<series_id>.md`
- each public moment route has `_moments/<moment_id>.md`
- public indexes and focused JSON reference existing route stubs where the route is expected
- stubs do not need to duplicate title, dimensions, status, series membership, or checksums

## Implementation Tasks

1. Done: work, series, detail, and moment layouts derive route identity from `page.slug`.
2. Done: front-matter-derived fallback JSON was removed where it serialized mutable metadata.
3. Done: direct detail routes derive parent work context from the `detail_uid` prefix and parent work JSON.
4. Done: `scripts/generate_work_pages.py` emits metadata-free route stubs.
5. Done: route-stub checksums were removed.
6. Done: delete, unpublish, and cleanup flows continue to remove stale route stubs through generated-artifact cleanup.
7. Done: `scripts/audit_site_consistency.py` validates route-anchor stubs by filename and generated JSON references.
8. Done: script docs were updated with the route-anchor contract.
9. Pending manual check: metadata-only saves should be smoke-tested in Studio after deployment.

## Decisions

- Final stub shape is empty front matter. Layouts stay in `_config.yml`.
- Deriving `work_id` from the `detail_uid` prefix is valid for current and future detail IDs.
- Work-detail direct routes should use parent work JSON via derived `work_id`; do not add a separate generated detail lookup JSON for this pass.
- Loading placeholder text is `loading...` and should be stored in config.
- Generic JSON-failure text is `info not available` and should be stored in config.
- Client scripts should update `document.title` after JSON loads.

## Acceptance Checks

- Editing a work title does not rewrite `_works/<work_id>.md`.
- Editing a series title does not rewrite `_series/<series_id>.md`.
- Editing a detail title does not rewrite `_work_details/<detail_uid>.md`.
- Editing a moment title does not rewrite `_moments/<moment_id>.md`.
- Creating a public record creates the required route stub.
- Deleting or unpublishing a public record removes the stale route stub where appropriate.
- Direct visits to work, work-detail, series, and moment routes still load their JSON-backed content.
- Direct work-detail visits derive the parent work id from `detail_uid` and read the parent work JSON.
- Public page loading and JSON-failure text comes from config.
- Browser titles update from runtime JSON metadata after load.
- Jekyll still builds the collection routes successfully.

## Benefits

- Metadata-only edits stop changing Jekyll-rendered route pages.
- Runtime source of truth becomes clearer: JSON owns content, stubs own routes.
- Field-aware build scoping has one less mutable artifact family to reason about.
- Generated diffs become smaller and easier to review.

## Risks

- Public catalogue pages become explicitly JavaScript/data dependent.
- JSON generation or fetch failures become more visible.
- Public page loading depends on the relevant JSON payload being present and fetchable.
- Work-detail direct routes depend on the current `detail_uid` prefix convention.
- Audit scripts and cleanup flows can drift if future code treats stubs as metadata records again.

Mitigation:

- keep route-existence checks in audit
- keep create/delete/unpublish cleanup explicit
- add direct-route browser checks for each collection type
- use conservative fallback in build planning until route-stub behavior is verified

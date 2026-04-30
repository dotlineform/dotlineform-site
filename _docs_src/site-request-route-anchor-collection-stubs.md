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

- planned

## Summary

This spec defines the pre-analysis cleanup for generated Jekyll collection Markdown files.

The current catalogue pages are JSON-first at runtime, but generated collection stubs still carry mutable metadata and checksums. That means a metadata-only edit can rewrite `_works/*.md`, `_work_details/*.md`, `_series/*.md`, or `_moments/*.md`, which wakes Jekyll as if a route page changed.

The target model is simpler:

- collection Markdown files are route anchors only
- generated JSON artifacts own runtime page content
- metadata-only saves do not rewrite collection Markdown stubs
- stubs are written only when route identity changes, a route is created, or a route is removed

This is part of Task 0 in [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping).

## Current Contract

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

The remaining front matter is mostly fallback content, route identity, or checksum state. In practice, the site is already JavaScript/data dependent, so that fallback content does not justify the Jekyll churn it creates.

## Target Contract

Generated collection stubs should contain no mutable catalogue metadata:

- no title
- no year or date
- no dimensions
- no series membership
- no parent work title
- no rendered prose
- no downloads or links
- no metadata checksum

The route identity should come from the filename and Jekyll's `page.slug`.

The preferred final stub shape is:

```md
---
---
```

If explicit layout front matter is kept for readability, it must still be stable and metadata-free:

```md
---
layout: work
---
```

Because `_config.yml` already assigns collection layouts by collection type, layout-only front matter is optional rather than functionally required.

## Runtime Responsibilities

Layouts and client scripts should treat the stub as a route shell only.

| Page | Route identity source | Runtime data source |
|---|---|---|
| work | `page.slug` | focused work JSON |
| work detail | `page.slug` as `detail_uid`; derive `work_id` from the `detail_uid` prefix unless a better detail lookup is added | parent work JSON |
| series | `page.slug` | series and works indexes, plus focused series JSON where needed |
| moment | `page.slug` | focused moment JSON |

Server-rendered fallback payloads should be removed where they serialize mutable front matter. The page shell may still render stable structural attributes such as base URLs, media base paths, pipeline-derived image variant settings, and route IDs.

Client-side loading states should handle the short gap before JSON arrives. Complete JSON failure can use a small generic error state; the site does not need to preserve a non-JavaScript fallback catalogue experience.

## Generator Responsibilities

The generator should:

- create missing stubs for published routes
- remove stale stubs when public routes are deleted or unpublished through cleanup flows
- avoid rewriting existing stubs for metadata-only changes
- avoid checksums based on source metadata for route-anchor stubs
- keep route-stub writes deterministic

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

1. Update work, series, detail, and moment layouts to derive route identity from `page.slug`.
2. Remove front-matter-derived fallback JSON from layouts where it serializes mutable metadata.
3. Update detail-page runtime logic so direct detail routes can recover enough context from JSON without front matter.
4. Update `scripts/generate_work_pages.py` to emit metadata-free route stubs.
5. Remove route-stub checksums or narrow them to stable route-shell content only.
6. Update delete, unpublish, and cleanup flows so stale route stubs are still removed.
7. Update `scripts/audit_site_consistency.py` expectations for route-anchor stubs.
8. Update script/data-model docs after implementation.
9. Verify metadata-only saves do not rewrite collection stubs.

## Open Questions

- Should the final stub be empty front matter or explicit layout-only front matter?
- Is deriving `work_id` from the `detail_uid` prefix always valid for current and future detail IDs?
- Should work-detail direct routes add a small generated detail lookup JSON, or is parent-work JSON via derived `work_id` enough?
- What exact loading placeholder should each public page show before JSON arrives?
- What should the generic JSON-failure state say on public pages?
- Should client scripts update `document.title` after JSON loads so browser titles follow runtime metadata?

## Acceptance Checks

- Editing a work title does not rewrite `_works/<work_id>.md`.
- Editing a series title does not rewrite `_series/<series_id>.md`.
- Editing a detail title does not rewrite `_work_details/<detail_uid>.md`.
- Editing a moment title does not rewrite `_moments/<moment_id>.md`.
- Creating a public record creates the required route stub.
- Deleting or unpublishing a public record removes the stale route stub where appropriate.
- Direct visits to work, work-detail, series, and moment routes still load their JSON-backed content.
- Jekyll still builds the collection routes successfully.

## Benefits

- Metadata-only edits stop changing Jekyll-rendered route pages.
- Runtime source of truth becomes clearer: JSON owns content, stubs own routes.
- Field-aware build scoping has one less mutable artifact family to reason about.
- Generated diffs become smaller and easier to review.

## Risks

- Public catalogue pages become explicitly JavaScript/data dependent.
- JSON generation or fetch failures become more visible.
- Work-detail direct routes need careful handling because they currently use the most front matter fallback.
- Audit scripts and cleanup flows can drift if they keep treating stubs as metadata records.

Mitigation:

- keep route-existence checks in audit
- keep create/delete/unpublish cleanup explicit
- add direct-route browser checks for each collection type
- use conservative fallback in build planning until route-stub behavior is verified

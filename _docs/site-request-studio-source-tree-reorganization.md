---
doc_id: site-request-studio-source-tree-reorganization
title: Studio Source Tree Reorganization Request
added_date: 2026-05-23
last_updated: 2026-05-23
ui_status: planned
parent_id: change-requests
sort_order: 10010
viewable: true
---
# Studio Source Tree Reorganization Request

Status:

- planned
- depends on completing the current Local Studio localization work
- should not be combined with Docs Viewer portability extraction

## Summary

Reorganize Studio-owned source files behind a clearer `studio/` boundary after the Local Studio app migration is stable.

The current repo layout still reflects the old Jekyll-hosted Studio model.
Studio browser modules, local static assets, UI Catalogue demos, route shells, app-server modules, and related source files live across `scripts/`, `assets/`, `_includes/`, `_ui_catalogue_notes/`, and `studio/`.
That made sense when Studio pages were Jekyll routes, but it is now harder to tell which files are public-site assets, Local Studio app source, Docs Viewer source, or generated output.

This request should make Studio ownership visible in the source tree without changing user-facing route URLs as a first goal.

## Boundary Decision

This request covers Studio-owned files only.

In scope:

- Local Studio Python app server modules and route-family modules
- Studio-owned browser JavaScript and CSS
- Studio-owned static data and local runtime config
- UI Catalogue demos and notes that are Studio reference surfaces
- local-only source or support files that should no longer sit in public Jekyll paths
- compatibility serving paths needed so existing browser code and smoke tests can migrate safely

Out of scope:

- full Docs Viewer portable extraction
- public Jekyll content and public-site assets
- generated docs/search payload relocation, unless needed as a narrow compatibility adapter
- Catalogue, Analytics, Docs, or media domain rewrites unrelated to source ownership
- package-manager or monorepo restructuring

Docs Viewer integration may move only where it is Studio-specific.
Reusable Docs Viewer runtime code, data contracts, generated payload expectations, and portable setup decisions belong to the Docs Viewer extraction work.

## Target Direction

The exact layout should be confirmed after the current localization work finishes, but the direction is:

```text
studio/
  app/
    server/
    static/
    shells/
  ui-catalogue/
    demos/
    notes/
```

Preserve browser-facing route and asset compatibility during the migration.
For example, Local Studio may continue to serve `/assets/studio/...` or `/studio/ui-catalogue/...` while the source files move to clearer Studio-owned locations.

## Implementation Tasks

- Inventory current Studio-owned source, static, UI Catalogue, and generated-output-adjacent paths.
- Classify each path as Studio-owned, Docs Viewer-owned, public-site-owned, domain-service-owned, or generated output.
- Define the final Studio source-tree layout before moving files.
- Move Python app-server modules in a small first slice, with import compatibility kept narrow and temporary.
- Move Studio static assets in a second slice, with local app static serving preserving existing URLs where practical.
- Move UI Catalogue notes and demo source under the Studio boundary, preserving local demo routes.
- Update smoke tests, docs, Jekyll excludes, and local runner docs in the same slices as the moves.
- Remove transitional import/path aliases once all references are migrated.

## Acceptance Criteria

- Studio-owned source files are discoverable under a coherent `studio/` source boundary.
- Public Jekyll preview does not watch Studio-only source or demo assets.
- Local Studio routes, UI Catalogue demos, and migrated app workflows still pass their focused smoke checks.
- Existing public-site builds continue to exclude Studio-only surfaces.
- Docs Viewer portable/shared files are not buried under Studio unless they are explicitly Studio shell integration files.

## Related References

- [Local Studio App Implementation Plan](/docs/?scope=studio&doc=local-studio-app-implementation-plan)
- [Studio Local Vanilla Web App Request](/docs/?scope=studio&doc=site-request-studio-local-vanilla-web-app)
- [Docs Viewer Shell Extraction Request](/docs/?scope=studio&doc=site-request-docs-viewer-shell-extraction)
- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)

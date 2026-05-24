---
doc_id: site-request-studio-source-tree-reorganization
title: Studio Source Tree Reorganization Request
added_date: 2026-05-23
last_updated: 2026-05-24
ui_status: planned
parent_id: change-requests
sort_order: 10010
viewable: true
---
# Studio Source Tree Reorganization Request

Status:

- drafting spec
- Local Studio localization work is complete, see [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- Docs Viewer portability extraction is a follow-on phase, see [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)

## Summary

Physically separate Studio from the public Jekyll site inside this repo by moving Studio-owned source, canonical data, config, services, workflows, frontend, and assets under the repo-level `studio/` folder.

After this reorganization, the rest of the repo should read as a normal GitHub Pages/Jekyll publishing surface.
The root-level Jekyll site should contain layouts, includes, public route JavaScript, public CSS, generated JSON that published pages read, and public assets such as thumbnails and site media.
A person browsing that part of the repo should be able to understand how the published site renders without also seeing the authoring system that produced its data.

Studio is the authoring and maintenance system.
To understand where the website data comes from, and how it is maintained, a reader should look under `studio/`.
Studio generates public artifacts for the Jekyll site, but it does not own their published output locations.
Because Studio owns the canonical data and maintenance workflows, it is tightly bound to this Jekyll site.
Moving Studio into a separate repo is not a future target for this request.
The goal is source-tree separation inside one repo, not repository separation.

This is intentionally a physical source-tree separation, not a compatibility migration.
The implementation should move the files, update imports, routes, static serving, scripts, tests, and docs to the new locations, and then get Studio working again from those locations.
It should not preserve old Studio source paths by adding compatibility shims, copied migration artifacts, or local serving of old site-owned folders such as `/assets/studio/...`.

## Boundary Decision

This request covers the physical ownership boundary between Studio and the public Jekyll site.

Move under `studio/`:

- canonical website data used by Studio to generate published site data
- Local Studio Python app server modules, route-family modules, and service adapters
- Studio-owned domain services and workflow support that exist for authoring or maintaining site data
- Studio frontend JavaScript, shell code, route modules, CSS, UI text, static config, and local runtime config
- Studio-owned assets, including Studio-only CSS, images, fixture assets, and UI Catalogue demo assets
- UI Catalogue demos and notes that are Studio reference surfaces
- local-only source, fixtures, tests, and support files that should no longer sit in public Jekyll paths

Remain outside `studio/`:

- public Jekyll layouts, includes, pages, and config needed to publish the site
- public route JavaScript that reads generated JSON into published pages
- public CSS and public assets required by the published site
- generated JSON/search/docs/catalogue outputs consumed by published pages
- public thumbnails and media assets used by published pages
- full Docs Viewer portable extraction
- package-manager restructuring

Same-repo boundary:

- Studio and the Jekyll site remain in the same repository
- Studio is the canonical authoring system for the site, so the site does not have an independent update path without Studio
- no task in this request should prepare for, imply, or preserve a future Studio repo split
- repo-split planning should be removed from this request's future direction; it was a hypothetical option, not a target architecture

Docs Viewer integration may move only where it is Studio-specific.
Reusable Docs Viewer runtime code, data contracts, generated payload expectations, and portable setup decisions belong to the Docs Viewer extraction work.

Domain code should be classified by purpose rather than by current path.
If a script is the canonical source, maintenance service, write workflow, local API adapter, or Studio UI support for website data, it belongs under `studio/`.
If a file is the published output or public runtime needed by GitHub Pages/Jekyll, it belongs outside `studio/`.

## Target Direction

The exact layout should be confirmed before moving files, but the direction is:

```text
studio/
  data/
    canonical/
    config/
  app/
    server/
    frontend/
    assets/
    shells/
  services/
    catalogue/
    analytics/
    docs/
    media/
  ui-catalogue/
    demos/
    notes/
  tests/
```

The layout names are not final.
The important rule is that these are source and authoring locations.
Browser URLs, public output paths, and generated-data destinations should be updated to match the new boundary rather than preserved through compatibility mounts.
This tree is a same-repo organization boundary.
It is not a staging step toward moving Studio into a separate repository.

## Published Output Rule

Studio may generate public artifacts, but those artifacts belong to the public Jekyll site when they are required for publishing.

Examples:

- canonical catalogue, analytics, docs, and media-maintenance source data moves under `studio/`
- generated public catalogue/search/docs JSON consumed by published pages remains under public asset paths
- public thumbnails and media used by published pages remain under public asset paths
- public route JavaScript that reads generated JSON into pages remains outside `studio/`
- Studio-only config, local runtime config, UI text, editors, reports, and workflow assets move under `studio/`

The reorganization should make generation direction obvious:

```text
studio/ source and services -> generated public artifacts -> Jekyll/GitHub Pages site
```

The public site holds what it needs to publish.
Studio holds the machinery and canonical inputs that produce and maintain those published artifacts.

## No Compatibility Layer

This request should not create compatibility layers for old Studio source paths.

Do not:

- keep old `assets/studio/...` source locations alive through local static aliases
- copy moved Studio files back into public paths as migration artifacts
- add broad import aliases from old script paths to new `studio/` paths
- preserve old Jekyll-hosted Studio shell assumptions through adapter files
- defer path cleanup by teaching Studio to read from both old and new source locations

The preferred approach is direct:

- move the files to their intended owners
- update imports and references
- update Local Studio static serving and runtime config to the new Studio-owned paths
- update generators so public outputs are still written where the Jekyll site needs them
- run focused checks and fix the breakage caused by the move

Temporary local edits while a slice is in progress are fine, but they should not be committed as compatibility infrastructure.

## Browser App Direction

The reorganization should also reduce Python ownership of browser presentation over time.

The current Local Studio app server still owns too much shell structure: route labels, top-navigation groups, active-section mapping, HTML shell rendering, per-route script/style inclusion, and runtime config projection.
That makes small UI shell changes create a relatively broad Python blast radius.

The future direction is a browser-owned Studio app shell with Python as the local server and service boundary:

```text
Python
- serves one minimal Studio shell
- serves static files
- exposes browser-safe runtime config JSON
- exposes read/write APIs
- enforces local write allowlists, backups, previews, applies, and compact logs

JavaScript
- renders Studio navigation and home link lists from config
- owns active route and section state
- mounts route modules based on the current route and runtime metadata
- owns app-shell UI behavior
- calls Python only for data, generated reads, previews, applies, writes, and local workflow services
```

This is not a requirement to adopt a frontend framework or rewrite Studio as a full single-page app in the reorganization slice.
A vanilla JavaScript shell is enough as the next architectural step.
The practical goal is to move shell composition and navigation rendering out of Python while keeping Python authoritative for local filesystem writes and service guardrails.
If the browser-shell step is too broad to complete in the same slice as the physical file moves, it should still end with the same ownership boundary: Studio shell source under `studio/`, public Jekyll source outside it, and no old-path compatibility layer.

## CSS Ownership Direction

Local Studio currently loads public `assets/css/main.css` for base font, size, spacing, layout, and primitive tokens, then layers Studio CSS on top.
That is a concrete public-site dependency and should be removed during the source-tree reorganization.

The target is:

- public `assets/css/main.css` owns public-site styles and genuinely shared primitives only
- Studio has its own base or main stylesheet under `studio/` for font, size, spacing, layout, shell, and primitive tokens needed by Local Studio
- Studio route, editor, modal, dashboard, and operational classes live in Studio-owned CSS
- any selector left in public `main.css` must be used by public routes too, not retained only because Studio needs it
- Local Studio shell rendering should load Studio-owned CSS directly, then Studio route CSS, without depending on public `main.css`

## Implementation Tasks

- Inventory current Studio-owned source, canonical data, config, static assets, UI Catalogue files, local services, tests, and generated-output-adjacent paths.
- Classify each path as Studio source, public Jekyll source, public generated output, Docs Viewer reusable source, or out-of-scope dependency.
- Define the final `studio/` source-tree layout before moving files.
- Move canonical website data and Studio config under `studio/`, then update generators and services to read from the new canonical locations while writing public outputs to the existing Jekyll/public output paths.
- Move Local Studio Python app-server modules, route-family modules, local API adapters, and Studio-owned services under `studio/`.
- Move Studio frontend JavaScript, shell code, CSS, UI text, static config, and Studio-only assets under `studio/`.
- Update the Local Studio server to serve Studio-owned frontend/assets from `studio/` paths, not from public site-owned `/assets/studio/...` paths.
- Split Studio's CSS base from public `assets/css/main.css`, moving Studio-only tokens/classes into Studio-owned CSS and leaving only public or genuinely shared selectors in public `main.css`.
- Move top navigation, active-section mapping, and home-list rendering toward a focused JavaScript shell module when doing so helps complete the physical separation cleanly.
- Move UI Catalogue notes and demo source under the Studio boundary, and update demo routes to read from the new Studio-owned source paths.
- Update tests, smoke scripts, checks, docs, Jekyll excludes, and local runner docs in the same slices as the moves.
- Remove old Studio source paths instead of retaining import/path aliases or compatibility serving routes.
- Verify public Jekyll output still receives the generated data and assets it needs after Studio source moves.
- Remove any repo-split framing from this request and related implementation notes touched by the slice; Studio remains coupled to this Jekyll site as its canonical authoring system.

## Acceptance Criteria

- Studio-owned source files, canonical data, config, services, frontend code, CSS, local assets, tests, and UI Catalogue source are physically located under a coherent repo-level `studio/` boundary.
- Public Jekyll source outside `studio/` contains only what is needed to publish the site: Jekyll layouts/includes/pages/config, public runtime JS/CSS, public assets, and generated public data.
- A reader can understand the public publishing surface without seeing the Studio authoring and maintenance machinery.
- A reader can understand where the site data comes from by looking under `studio/`.
- Studio can regenerate public artifacts from canonical source under `studio/`.
- Studio and the Jekyll site remain in one repo; no future repo split is listed or implied as a target outcome of this request.
- Generated public outputs remain available to Jekyll at stable public paths.
- Public Jekyll preview does not watch Studio-only source, services, config, tests, or demo assets.
- Local Studio no longer depends on public `assets/css/main.css` for base typography, size, spacing, shell, or Studio-only primitive classes.
- Public `assets/css/main.css` contains no Studio-only route, editor, modal, dashboard, or operational selectors after the split.
- Local Studio routes, UI Catalogue demos, and migrated app workflows still pass their focused smoke checks.
- Existing public-site builds continue to exclude Studio-only surfaces.
- Docs Viewer portable/shared files are not buried under Studio unless they are explicitly Studio shell integration files.
- Old Studio source locations such as `assets/studio/...` are removed or reduced to generated public output only; they are not kept alive as source locations through compatibility shims.
- No broad old-path import aliases, copied migration artifacts, or static serving aliases are committed for moved Studio source.
- Python remains the local API/write boundary, but no longer needs broad edits for routine Studio shell navigation changes once the browser-shell step lands.

## Related References

- [Studio Source Tree Reorganization Tasks](/docs/?scope=studio&doc=site-request-studio-source-tree-reorganization-tasks)
- [Local Studio App Implementation Plan](/docs/?scope=studio&doc=local-studio-app-implementation-plan)
- [Studio Local Vanilla Web App Request](/docs/?scope=studio&doc=site-request-studio-local-vanilla-web-app)
- [Docs Viewer Shell Extraction Request](/docs/?scope=studio&doc=site-request-docs-viewer-shell-extraction)
- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)

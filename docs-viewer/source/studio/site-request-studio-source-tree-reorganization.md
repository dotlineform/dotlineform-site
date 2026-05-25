---
doc_id: site-request-studio-source-tree-reorganization
title: Studio Source Tree Reorganization Request
added_date: 2026-05-23
last_updated: 2026-05-24
ui_status: done
parent_id: archive
sort_order: 92000
viewable: true
---

This document is archived and is no longer maintained.

---

# Studio Source Tree Reorganization Request

Status:

- complete: implementation and final verification tracked in [Studio Source Tree Reorganization Tasks](/docs/?scope=studio&doc=site-request-studio-source-tree-reorganization-tasks)

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
- canonical publishing Markdown under `studio/data/canonical/catalogue-markdown/`; this is Studio-owned site source, not Docs Viewer-owned source
- Docs Viewer source Markdown under `docs-viewer/source/studio/`, `docs-viewer/source/analysis/`, `docs-viewer/source/library/`, and any other source Markdown folder that Docs Viewer explicitly owns
- change request workflow source under `studio/workflows/change-requests/logs/entries/`; this is Studio-owned workflow data, not Docs Viewer-owned source
- Local Studio Python app server modules, route-family modules, and service adapters
- Studio-owned domain services and workflow support that exist for authoring or maintaining site data
- Studio-owned build scripts, checks, tests, test fixtures, and Codex-run verification support
- Studio frontend JavaScript, shell code, route modules, CSS, UI text, static config, and local runtime config
- Studio-owned assets, including Studio-only CSS, images, fixture assets, and UI Catalogue demo assets
- current Docs Viewer runtime code, server/services, source config, UI text, CSS, and associated assets because Docs Viewer remains Studio-hosted until the later extraction
- UI Catalogue demos and notes that are Studio reference surfaces
- local-only source, fixtures, tests, and support files that should no longer sit in public Jekyll paths

Remain outside `studio/`:

- public Jekyll layouts, includes, pages, and config needed to publish the site
- public route JavaScript that reads generated JSON into published pages
- public CSS and public assets required by the published site
- generated JSON/search/docs/catalogue outputs consumed by published pages
- generated Docs Viewer JSON and search payloads consumed by public `/library/` and `/analysis/` installs
- generated or served Docs Viewer runtime config/report registry payloads needed by public read-only installs
- public thumbnails and media assets used by published pages
- full Docs Viewer portable extraction
- package-manager restructuring

Public-site root rule:

- the public site may contain publishing source and runtime needed by published pages
- it should not own development tooling, build scripts, checks, tests, fixtures, validators, audit scripts, Studio-only route shells, UI Catalogue source, or Docs Viewer source/runtime internals
- root convenience commands may remain only as intentional entrypoints into Studio/Docs Viewer tooling, not as old-path compatibility layers

Same-repo boundary:

- Studio and the Jekyll site remain in the same repository
- Studio is the canonical authoring system for the site, so the site does not have an independent update path without Studio
- no task in this request should prepare for, imply, or preserve a future Studio repo split
- repo-split planning should be removed from this request's future direction; it was a hypothetical option, not a target architecture

Docs Viewer boundary for this request:

- Docs Viewer is both a publishing module and a manage-mode interface
- as a publishing module, Docs Viewer converts an owned source scope folder under `docs-viewer/source/<scope>/` into generated JSON/search payloads that public read-only routes can consume, such as `/library/` and `/analysis/`
- as a manage-mode interface, Docs Viewer imports source Markdown and edits metadata for an allowed source scope
- manage mode is currently enabled through `/docs/`
- `/docs/` has no special source ownership meaning; it defaults to the `studio` scope under `docs-viewer/source/studio/`, but manage mode can switch to other allowed Docs Viewer source folders such as `docs-viewer/source/library/`
- `docs-viewer/source/studio/` is therefore just another Docs Viewer-owned source folder, not a privileged root docs source
- `docs-viewer/source/library/` and `docs-viewer/source/analysis/` are Docs Viewer-owned canonical source folders; Docs Viewer decides whether a scope is available locally through Studio, publicly on the site, or both
- current Docs Viewer code is relatively self-contained but remains Studio-hosted, so it moves under `studio/` with the other Studio source
- Docs Viewer should have a clear home inside `studio/`, not be scattered through generic Studio app, service, data, or asset folders
- the existing localization of Docs Viewer scripts, CSS, config, and services should be preserved as a recognizable internal boundary to make later extraction easier
- the Studio server owns Docs Viewer management/server behavior until a later extraction moves that responsibility out of Studio
- Docs Viewer source Markdown is unpublished source data, so it moves under the internal Docs Viewer home in `studio/`
- Docs Viewer reports are Docs Viewer-owned runtime/config/document surfaces even when the report reads data owned by another repo domain
- for example, the `change-history.md` report is a Docs Viewer report that reads Studio-owned `studio/workflows/change-requests/` data
- report ownership does not transfer ownership of the data being read; a Docs Viewer report should be able to read allowed data from anywhere in the repo where Docs Viewer is installed
- any remaining `_docs` naming pattern should refer only to Docs Viewer-owned canonical source scopes; Studio-owned change-request workflow data and catalogue Markdown now live in non-Docs-Viewer Studio homes to remove the old prefix confusion
- `studio/workflows/change-requests/` is Studio-owned change request workflow data; generated logs may be consumed by Codex and generated reports may be surfaced for humans through `/docs/`, but Docs Viewer does not own the source workflow or treat it as a published Docs Viewer scope
- `studio/data/canonical/catalogue-markdown/` is canonical publishing Markdown generated into public site data by Studio; it lives under Studio canonical data, not under the internal Docs Viewer home
- generated Docs Viewer JSON/search payloads are published artifacts read by public installs such as `/library/` and `/analysis/`, so they remain in the public Jekyll site output paths
- the later Docs Viewer extraction means moving Docs Viewer runtime, server, services, Docs Viewer source files, config, and associated assets out of Studio into a true reusable boundary such as `docs-viewer/`
- until that later extraction happens, Docs Viewer is not treated as an independent portable package inside this source-tree reorganization

Domain code should be classified by purpose rather than by current path.
If a script is the canonical source, maintenance service, write workflow, local API adapter, or Studio UI support for website data, it belongs under `studio/`.
If a script builds, validates, checks, tests, audits, or generates data for the site, it belongs under Studio or Docs Viewer according to the domain it serves.
If a file is the published output or public runtime needed by GitHub Pages/Jekyll, it belongs outside `studio/`.
The public site should contain only publishing infrastructure, route/page source, public runtime scripts for published pages, public CSS/assets, and generated data needed at runtime.

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
    media/
  checks/
  tests/
  docs-viewer/
    runtime/
    server/
    services/
    build/
    source/
      studio/
      library/
      analysis/
    config/
    reports/
    assets/
    tests/
  workflows/
    change-requests/
      logs/
  ui-catalogue/
    demos/
    notes/
```

The layout names are not final.
The important rule is that these are source and authoring locations.
The `studio/docs-viewer/` branch is an internal Studio-hosted home for the current Docs Viewer implementation.
It should preserve the work already done to localize Docs Viewer scripts and assets, so the later extraction can move a coherent subtree rather than rediscover scattered files.
Browser URLs, public output paths, and generated-data destinations should be updated to match the new boundary rather than preserved through compatibility mounts.
This tree is a same-repo organization boundary.
It is not a staging step toward moving Studio into a separate repository.

## Published Output Rule

Studio may generate public artifacts, but those artifacts belong to the public Jekyll site when they are required for publishing.

Examples:

- canonical catalogue data, `studio/data/canonical/catalogue-markdown/` publishing Markdown, analytics source, and media-maintenance source data live under Studio canonical source
- Docs Viewer-owned source Markdown, including `docs-viewer/source/studio/`, `docs-viewer/source/library/`, and `docs-viewer/source/analysis/`, lives under the internal Docs Viewer home in `studio/`
- Studio-owned change request log source under `studio/workflows/change-requests/logs/entries/` lives under Studio workflow source, not under Docs Viewer
- generated public catalogue/search/docs JSON consumed by published pages remains under public asset paths
- generated Docs Viewer JSON/search payloads for public `/library/` and `/analysis/` remain under public asset paths
- generated Catalogue search indexes and policy are produced by Studio; the public site owns only the published search payloads and route runtime that displays them
- Docs Viewer search indexes and search config are produced by Docs Viewer; public read-only installs consume only the generated payloads and runtime
- generated change request log data remains Studio-owned even when a Docs Viewer-owned report reads it
- Docs Viewer report definitions, report documents such as `change-history.md`, report runtime modules, and report registry/config move with Docs Viewer; generated public report registry/config payloads may remain outside Studio when read-only installs need them
- public thumbnails and media used by published pages remain under public asset paths
- public route JavaScript that reads generated JSON into pages remains outside `studio/`
- Studio-only config, local runtime config, Docs Viewer source config, UI text, editors, reports, and workflow assets move under `studio/`

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

Before this reorganization, Local Studio loaded public `assets/css/main.css` for base font, size, spacing, layout, and primitive tokens, then layered Studio CSS on top.
That concrete public-site dependency was removed during the source-tree reorganization.

The implemented split is:

- public `assets/css/main.css` owns public-site styles and genuinely shared primitives only
- Studio has its own base or main stylesheet under `studio/` for font, size, spacing, layout, shell, and primitive tokens needed by Local Studio
- Studio route, editor, modal, dashboard, and operational classes live in Studio-owned CSS
- any selector left in public `main.css` must be used by public routes too, not retained only because Studio needs it
- Local Studio shell rendering loads Studio-owned CSS directly without depending on public `main.css`

## Implementation Tracking

Implementation tasks are tracked in [Studio Source Tree Reorganization Tasks](/docs/?scope=studio&doc=site-request-studio-source-tree-reorganization-tasks).
The current path-family inventory is recorded in [Studio Source Tree Reorganization Inventory](/docs/?scope=studio&mode=manage&doc=site-request-studio-source-tree-reorganization-inventory).
Keep task status, handover notes, sequencing, and deferred-task reasons there so this request stays focused on the stable boundary decision and acceptance contract.

## Final Status

Completed on 2026-05-24.
The physical source-tree reorganization is implemented without old-path compatibility shims.

The final moved-path summary is:

- Studio canonical catalogue, analytics, runtime config, generated Studio read models, and thumbnail-quality review output now live under `studio/data/`.
- Local Studio server, route views, API adapters, frontend modules, UI text, CSS, and Studio-only images now live under `studio/app/`.
- Catalogue, analytics, media, data-sharing, and shared service code now live under `studio/services/` and `studio/shared/`.
- Docs Viewer source Markdown, runtime modules, shell source, CSS, config, build scripts, server/services, and tests now live under `studio/docs-viewer/`.
- Change request workflow source logs, generated workflow projections, reports, and docs-log services now live under `studio/workflows/change-requests/`.
- UI Catalogue demos, notes, and assets now live under `studio/ui-catalogue/`.
- Checks, smoke tests, Python tests, fixtures, and the run-checks command now live under `studio/checks/`, `studio/tests/`, and `studio/commands/`.
- Public Jekyll output remains outside `studio/`: layouts, includes, public route JS, public CSS, public media, generated catalogue/docs/search payloads, and public read-only Docs Viewer route adapters.

Final verification passed:

- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick --run-id stsr-020-quick-final-pass`; summary at `var/test-runs/stsr-020-quick-final-pass/summary.md`.
- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile studio-smoke --run-id stsr-020-studio-smoke-final-pass`; summary at `var/test-runs/stsr-020-studio-smoke-final-pass/summary.md`.
- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke --run-id stsr-020-docs-viewer-smoke-final-pass`; summary at `var/test-runs/stsr-020-docs-viewer-smoke-final-pass/summary.md`.
- `$HOME/miniconda3/bin/python3 studio/checks/audit_public_build_surface.py --site-root /tmp/dlf-jekyll-build`.
- Targeted supporting checks included a public Jekyll build to `/tmp/dlf-jekyll-build`, dry-run Studio docs and Studio search builds, focused Local Studio Docs Viewer/Catalogue/UI Catalogue/thumbnail-quality smokes, focused pytest for Studio app server and Catalogue routes, and targeted JavaScript/Ruby syntax checks.

Generated Docs Viewer payloads and search payloads were intentionally not rebuilt during close-out.
The task updated source documentation and a structured docs-log source record only.

Remaining risks and follow-ups:

- Some generated docs/search payloads still contain historical path text until the next explicit docs rebuild.
- Historical request, inventory, and generated change-history records still mention old paths as history; those references should not be treated as active source paths.
- Docs Viewer remains Studio-hosted under `studio/docs-viewer/`; the portable extraction is a separate follow-on request.
- Public read-only `/library/` and `/analysis/` remain the owners of public Docs Viewer install validation; manage-mode `/docs/` remains a Local Studio route.

## Acceptance Criteria

- Studio-owned source files, canonical data, config, services, frontend code, CSS, local assets, tests, and UI Catalogue source are physically located under a coherent repo-level `studio/` boundary.
- Public Jekyll source outside `studio/` contains only what is needed to publish the site: Jekyll layouts/includes/pages/config, public runtime JS/CSS, public assets, and generated public data.
- Build scripts, checks, tests, fixtures, audits, and verification helpers are owned by Studio or Docs Viewer, not by the public Jekyll publishing surface.
- A reader can understand the public publishing surface without seeing the Studio authoring and maintenance machinery.
- A reader can understand where the site data comes from by looking under `studio/`.
- Studio can regenerate public artifacts from canonical source under `studio/`.
- Studio and the Jekyll site remain in one repo; no future repo split is listed or implied as a target outcome of this request.
- Generated public outputs remain available to Jekyll at stable public paths.
- Generated Docs Viewer JSON/search payloads used by public `/library/` and `/analysis/` remain available at their public site paths.
- Generated or served Docs Viewer report registry/config payloads needed by read-only installs remain available to those installs, while the source report definitions/config/runtime live under Docs Viewer ownership.
- Current Docs Viewer runtime, server/services, config, Docs Viewer source files, and associated assets are Studio-hosted under a clear internal Docs Viewer home such as `studio/docs-viewer/` until a later extraction moves that coherent subtree to a true portable boundary.
- Docs Viewer-owned reports can read allowed data owned by Studio or other repo domains; the report implementation/config/document moves with Docs Viewer, while the data remains with its owning domain.
- `docs-viewer/source/studio/` is treated as one Docs Viewer-owned source scope among others, not as a special root docs source.
- `studio/workflows/change-requests/` is treated as Studio-owned change request workflow data; generated reports may be surfaced through `/docs/`, but Docs Viewer does not own the log source workflow.
- Public Jekyll preview does not watch Studio-only source, services, config, tests, or demo assets.
- Local Studio no longer depends on public `assets/css/main.css` for base typography, size, spacing, shell, or Studio-only primitive classes.
- Public `assets/css/main.css` contains no Studio-only route, editor, modal, dashboard, or operational selectors after the split.
- Local Studio routes, UI Catalogue demos, and migrated app workflows still pass their focused smoke checks.
- Existing public-site builds continue to exclude Studio-only surfaces.
- The source-tree reorganization does not attempt the full Docs Viewer portable extraction; that later request is responsible for moving Docs Viewer out of Studio into a reusable package such as `docs-viewer/`.
- Old Studio source locations such as `assets/studio/...` are removed or reduced to generated public output only; they are not kept alive as source locations through compatibility shims.
- No broad old-path import aliases, copied migration artifacts, or static serving aliases are committed for moved Studio source.
- Python remains the local API/write boundary, but no longer needs broad edits for routine Studio shell navigation changes once the browser-shell step lands.

## Related work

- Local Studio localization work is complete, see [Local Studio App](/docs/?scope=studio&doc=local-studio-app)
- Docs Viewer portability extraction is a follow-on phase, see [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)

## References

- [Local Studio App Implementation Plan](/docs/?scope=studio&doc=local-studio-app-implementation-plan)
- [Studio Local Vanilla Web App Request](/docs/?scope=studio&doc=site-request-studio-local-vanilla-web-app)
- [Docs Viewer Shell Extraction Request](/docs/?scope=studio&doc=site-request-docs-viewer-shell-extraction)
- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)

## Change Log Entries

- `change-2026-05-24-completed-studio-source-tree-reorganization`

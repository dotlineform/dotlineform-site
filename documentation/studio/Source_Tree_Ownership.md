---
draft: false
doc_id: d-20260524-214228-7247ef
title: Source Tree Ownership
added_date: "2026-05-24 21:42:28"
last_updated: "2026-11-18"
parent_id: d-20260331-000000-4a16b0

---
# Source Tree Ownership

## Repository Shape

The repository contains several local apps, shared domain services and one tracked public deploy tree. For the workflow across these roots, see [How the site fits together](../guide/How_The_Site_Fits_Together.md).

| Root | Owns |
| --- | --- |
| `studio/` | catalogue authoring app; catalogue and media services; canonical Catalogue data; live Studio read projections; Studio/public-catalogue tests |
| `docs-viewer/` | Docs Viewer canonical runtime and stylesheets, services, configuration, builders, import/export, integrated document packages and tests |
| `app/` | separate native Mac and iPad app, with its own [project instructions](../../app/AGENTS.md) |
| `processing/` | separate Java/Processing project source, pinned sketchbook libraries, project scripts, and project-owned tests |
| `shared/` | reviewed app-neutral frontend modules and styles used across routes or apps, including explicitly accepted one-consumer cross-app primitives |
| `site/` | tracked static deploy root: public shells and site-owned assets, deployed public data, public thumbnails, and the committed shared/public Docs Viewer runtime projection |
| `site-tools/` | public-tree validation, the explicit Docs Viewer runtime projection command and manifest, and durable site-level tooling config |
| `tooling/lint/` | repository development-tool pins, shared lint rules, and checked maintained Python/JavaScript boundaries |
| `var/` | ignored reports, logs, caches, staging, and other local working output |

`DOTLINEFORM_DOCS_BASE_DIR` selects external Working and Preview storage. `DOTLINEFORM_PROJECTS_BASE_DIR` independently selects external project inputs, Catalogue media staging and document packages under `data-sharing/`. [Working storage and roles](Source_Organisation.md#storage-and-roles)

## Studio Boundary

| Studio path | Responsibility |
| --- | --- |
| `studio/app/frontend/` | browser shell, route templates/scripts, shared route helpers, checked browser config |
| `studio/app/server/` | loopback server, HTTP routing, runtime config projection, API adapters |
| `studio/app/assets/` | Studio-only CSS and static assets |
| `studio/services/catalogue/` | catalogue validation, mutation, lookup, build, publication, cleanup, import, and reports |
| `studio/services/media/` | derivative generation and remote media transport |
| `studio/data/canonical/` | authoritative Work, Series, Gallery and relationship metadata |
| `studio/data/config/` | checked Catalogue field and output inventory |
| `studio/shared/` | Python helpers shared by Studio-owned services and commands |
| `studio/tests/` | Studio and public-catalogue contracts |

Studio services provide live read projections from canonical source. Refresh Catalogue separately owns replaceable Catalogue reader output under `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`; see [Catalogue Architecture](Catalogue_Architecture.md).

Studio entrypoints establish service and shared-module paths through `studio/shared/python/studio_python_paths.py`. Catalogue/media modules use the established `catalogue.*`, `media.*` and shared-module imports directly. Missing dependencies, including failures inside imported modules, propagate without retrying under another package name. The bootstrap is retained; module retirement does not change operation ownership.

The legacy Catalogue pages, payloads, Search/Recent indexes, runtime and thumbnails now live in `site/archive/`. Shared shell styles, scripts and icons have independent archive copies. Active Studio Catalogue operations use the current Save → Refresh → Regenerate → Publish workflow and configured Docs workspace, independently of that archive. Active Docs projection and code-update destinations exclude the archive. Archived remote media is served from `https://media.dotlineform.com/archive/catalogue/`, with full copies of the R2 `works/` and `work_details/` prefixes; the original source objects remain intact. [Catalogue Archive](Catalogue_Archive.md) records how the snapshot and rclone copy were made.

## App Boundaries

### Retired Analytics Boundary

The standalone Analytics source tree, runner, routes, APIs, configuration, checks, and tests are retired. Studio Tag services were subsequently retired; Concept definitions belong to Docs documents. Docs Viewer owns integrated document packages. Do not restore `/analytics/...`, `/studio/analytics/...`, `/studio/data-sharing/...`, or `/analytics/data-sharing/...` compatibility paths.

### Docs Viewer

Docs Viewer owns `/docs/`, its management APIs and `/docs-review/`. The external Working and Preview roots and the public destinations are configured in [`docs-workspace.json`](../../docs-viewer/config/workspace/docs-workspace.json). Working holds editable source in `working/source/`, replaceable outputs in `working/generated/`, ready media and publication queues. Publish applies those selected outputs and removals to Preview and the configured repository and R2 destinations. The public reader at `/` consumes prepared files and media. [Publish and deploy](../guide/Publish_And_Deploy.md)

Shared/public browser code is canonical under `docs-viewer/runtime/js/{public,shared}/`, with the focused public report loader under `docs-viewer/runtime/js/reports/`; shared/public stylesheets are canonical under `docs-viewer/static/css/`. Local Manage and Review serve those canonical files. `site-tools/config/site-code-update.json` is the sole maintained inventory that maps the public subset into tracked `site/docs-viewer/` for static preview and GitHub Pages. `bin/site-code-update` is the only producer of that runtime projection. Local-only report, management, review, import, and stylesheet files never enter the public artifact merely because they share a canonical parent directory.

### Processing

`processing/` is hosted in this repository but remains a separate Java/Processing project. It is not a website module or part of `site/`. Its development, build, test, render, and export lifecycle should be project-owned rather than inferred from the website toolchain.

The Studio [Processing](Processing.md) family covers repository placement and shared-system integration. Keep durable Processing development documentation with its project owner.

Processing work media is not repository source. It belongs beneath the configured external `$DOTLINEFORM_PROJECTS_BASE_DIR/processing/<project-id>/` root. A selected output becomes public only through the existing Catalogue Work/Series pipeline using the Work's exact configured media-source identity; `processing/` and Docs Viewer do not become competing public media owners.

## Repository Lint Boundary

`tooling/lint/targets.json` maps adopted Python and JavaScript source roots to
their application owner. It does not merge those applications: its ESLint
blocks retain their real browser context, while each Python path remains under
its service or command owner.

Generated, published, vendor, dependency, cache, canonical-data, retired, and
Processing paths are explicit exclusions. Add a source root only after the
complete proposed boundary has been audited and passes; use explicit
`bin/lint-python` or `bin/lint-js` paths while a new boundary is still being
adopted.

## Shared Frontend Rule

`shared/frontend/` is for reviewed production UI behaviour whose interaction contract is independent of one app shell. Reuse across real routes or apps is the default evidence. A one-consumer component is exceptional: its shared responsibility must be explicit, transport and workflow policy must stay injected, and its durable Shared UI page must name any cross-app domain constraint.

Shared modules must not call an app-specific API or assume one route shell. Each app keeps transport, data adapters, commit behavior, and route orchestration with its owner.

Do not move code into `shared/` merely because it looks reusable. A speculative second consumer is not evidence, and an accepted one-consumer boundary does not require migrating existing app UI to manufacture reuse.

## Source, Generated, And Working Data

```text
checked config + canonical source
  -> owning app/service
  -> generated local or public read model
  -> runtime consumer

canonical shared/public runtime code
  -> bin/site-code-update
  -> tracked site runtime projection

temporary inputs, logs, reports, and caches
  -> var/ or external workspace
```

- Canonical source is edited and validated.
- Generated output is rebuildable even when checked in.
- The deployed public document and media projection lives under `site/` or its configured remote destination.
- App-local generated output lives with its app.
- Reports and run artifacts do not become documentation source.

## Compatibility Rule

Do not preserve old ownership through manually copied files, aliases, broad fallback reads, or static-serving shims. The explicit runtime projection is a deployment artifact, not a second editable source tree.

In particular, do not restore former `site/assets/studio/`, `_docs_catalogue/`, root check/test folders, retired Analytics or Admin routes, or alternate Docs Viewer source homes. A narrow wrapper is acceptable only when it delegates clearly to the current owner and does not create a second data or route contract.

## How To Place New Work

Ask in order:

1. Which app or headless domain owns the user-visible capability?
2. Is this canonical source, checked policy, generated output, or local working data?
3. Which runtime consumes it?
4. Does sharing represent a proven same contract or only hoped-for reuse?
5. Which tests and documentation owner will make the boundary discoverable?

The [Projection Contract](Projection_Contract.md) covers cross-boundary source-to-output checks. App overviews and code are the authority for exact current subdirectories.

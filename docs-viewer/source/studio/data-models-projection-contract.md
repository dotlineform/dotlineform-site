---
doc_id: data-models-projection-contract
title: Projection Contract
added_date: 2026-05-23
last_updated: 2026-06-12
parent_id: architecture
viewable: true
---
# Projection Contract

This document defines the boundary between canonical source, public projections, Studio projections, and Docs Viewer payloads.

It complements [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership) by documenting the source/projection contract rather than the whole repo layout.

The executable source of truth is `admin-app/checks/projection_contract.json`.

- Run `$HOME/miniconda3/bin/python3 admin-app/checks/audit_projection_contract.py` to validate the manifest, checked-in public JSON leak rules, and public source-reference rules.
- When a built public site is available, pass `--site-root <path>` to audit public output from the same manifest.

`public` means intended for dotlineform.com runtime output. It does not mean repository privacy. Canonical source can remain in a public repo while generated public projections omit source-only fields.

## Contract Rules

- canonical source is the editable source of truth
- public projections are generated runtime artifacts for public routes and public read-only viewer scopes
- Studio projections are local-app artifacts for authoring, review, lookup, diagnostics, and write workflows
- Docs Viewer payloads are generated scope payloads; only Library and Analysis payloads are public by default
- Public static builds must consume public projections and must not publish Studio-only source or projections
- source-only fields can exist in canonical source only when public builders copy fields through an explicit allowlist or documented transform
- local generated and import/export artifacts under `var/` are working output, not canonical source

## Catalogue

| Family | Canonical Source | Public Projection | Studio Projection | Owner |
| --- | --- | --- | --- | --- |
| Catalogue metadata | `studio/data/canonical/catalogue/works.json`, `series.json`, `work_details.json`, `moments.json` | fixed public route shells; `site/assets/data/series_index.json`, `site/assets/data/works_index.json`, `site/assets/data/recent_index.json`, `site/assets/data/moments_index.json`, `site/assets/series/index/`, `site/assets/works/index/`, `site/assets/moments/index/` | `studio/data/generated/catalogue-lookup/`, catalogue editor API read responses, project-state and thumbnail-quality local reports | [Catalogue Source Model](/docs/?scope=studio&doc=data-models-catalogue-source), [Catalogue Indexes And Payloads](/docs/?scope=studio&doc=data-models-catalogue-indexes) |
| Catalogue prose | `studio/data/canonical/catalogue-markdown/works/`, `studio/data/canonical/catalogue-markdown/series/`, `studio/data/canonical/catalogue-markdown/moments/` | rendered `content_html` in per-record public payloads | editor/source-open workflows and moment prose import preview/apply state | [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json) |
| Catalogue media metadata | source image fields in canonical catalogue JSON plus `DOTLINEFORM_PROJECTS_BASE_DIR` media roots | public route thumbnails under `site/assets/works/img/`, `site/assets/work_details/img/`, `site/assets/moments/img/`; public page media URLs from generated payloads | local derivative staging under `var/catalogue/media/` | [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json), [Publish Media To R2](/docs/?scope=studio&doc=scripts-publish-media-to-r2) |
| Catalogue search | public catalogue projections | `site/assets/data/search/catalogue/index.json` | search preview/build diagnostics | [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline-architecture) |

Catalogue public builders must treat canonical source JSON as input, not as a browser payload.
The current manifest-backed leak rule covers source media path fields such as `project_folder`, `project_subfolder`, `project_filename`, `details_subfolder`, `source_image_file`, and `provenance`.
It also treats work `storage` and any retired `notes` keys as forbidden in public output.
`storage` remains available to Studio through the Studio-only `studio/data/generated/activity/work-storage-index.json` projection; public catalogue work records, public indexes, and catalogue search must not publish it.
Work and series `notes` are no longer source-schema fields; catalogue prose Markdown files own narrative text.

Catalogue search is catalogue-owned and does not consume Analytics tag source data.
Analytics tag registry, aliases, assignments, and groups are local Analytics source data, not public catalogue projections.

## Docs Viewer Scopes

| Scope | Canonical Source | Public Projection | Local Docs Viewer Projection | Owner |
| --- | --- | --- | --- | --- |
| Studio docs | `docs-viewer/source/studio/*.md` | none by default | `docs-viewer/generated/docs/studio/`, `docs-viewer/generated/search/studio/index.json`, `<DOCS_VIEWER_BASE_URL>/docs/` manage payload reads | [Studio Scope](/docs/?scope=studio&doc=data-models-studio), [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder) |
| Library docs | `docs-viewer/source/library/*.md` | `site/assets/data/docs/scopes/library/`, `site/assets/data/search/library/index.json`, `/library/` | local manage-mode access to the same generated payloads plus data-sharing working output under `var/analytics/data-sharing/` | [Public Scopes](/docs/?scope=studio&doc=docs-viewer-public-scopes) |
| Analysis docs | `docs-viewer/source/analysis/**/*.md` | `site/assets/data/docs/scopes/analysis/`, `site/assets/data/search/analysis/index.json`, `/analysis/` | local manage-mode access to the same generated payloads | [Public Scopes](/docs/?scope=studio&doc=docs-viewer-public-scopes) |

Docs source files are the canonical authored content. Generated Docs Viewer payloads are projections of that source.
`viewable: false` can remain generated for manage-mode review while staying out of public/default tree discovery and search.

The public site may publish Library and Analysis Docs Viewer payloads and search. It must not publish Studio docs payloads or Studio docs search unless a separate public Studio docs surface is intentionally defined.

## Studio App Data

| Family | Canonical Source | Public Projection | Studio Projection | Owner |
| --- | --- | --- | --- | --- |
| Tag vocabulary and assignments | `analytics-app/data/canonical/tag-registry.json`, `tag-aliases.json`, `tag-assignments.json`, `tag-groups.json` | none by default; public catalogue search does not consume Analytics tags | local analytics API read/write payloads and tag route templates | [Analytics](/docs/?scope=studio&doc=analytics) |
| Work storage lookup | `studio/data/generated/activity/work-storage-index.json` | none | Studio Works storage review data | [Studio Works](/docs/?scope=studio&doc=studio-works) |
| Studio config and UI text | `studio/app/frontend/config/studio-config.json`, `studio/app/frontend/config/ui-text/*.json`, related checked-in config files | public Docs Viewer config and public search policy only where separately generated or copied by their owners | local runtime config JSON and Studio route UI text payloads | [Studio Runtime](/docs/?scope=studio&doc=studio-runtime) |
| Admin activity | local write-service outputs under `var/admin/activity/` | none | Admin Activity route/API data | [Activity](/docs/?scope=studio&doc=activity) |

Studio app data is local by default.
Public builders can read a narrow subset only through documented adapters.
The tracked `site/` root should contain only public paths, and site validation should confirm required deploy files are present before upload.

## Config And Build Outputs

Public build configuration is part of the projection contract:

- `site-tools/config/site-tools.json` is the public static validation and site-level settings config
- public Docs Viewer config exposes only public read-only scopes
- `bin/local-studio` serves Studio routes, local runtime config, and Studio-owned APIs
- `bin/local-admin` serves Admin routes, local Admin runtime config, and Admin-owned APIs
- `docs-viewer/bin/docs-viewer` serves Docs Viewer manage mode, generated reads, Docs management APIs, and document Data Sharing endpoints
- `bin/site-preview` and `bin/site-validate` run public static preview and validation paths

## Public Build Surface

The public static build should include:

- home, about, recent, and other public site pages
- public catalogue pages for works, series, work details, and moments
- public catalogue JSON projections under `site/assets/data/` and per-record public payloads
- public catalogue search output under `site/assets/data/search/catalogue/`
- public media and thumbnail assets intentionally served by the site
- shared public JavaScript under `site/assets/js/`
- shared public CSS under `site/assets/css/`
- generated or public-copied Docs Viewer runtime files required by read-only installs
- public Docs Viewer browser config generated from `docs-viewer/config/defaults/docs-viewer-public-config.json`
- public read-only Library route at `/library/`
- public read-only Analysis route at `/analysis/`
- generated Library docs payloads and search under `site/assets/data/docs/scopes/library/` and `site/assets/data/search/library/`
- generated Analysis docs payloads and search under `site/assets/data/docs/scopes/analysis/` and `site/assets/data/search/analysis/`

The public static build should not include:

- `/studio/` routes
- `/docs/` local management route
- Studio app source/assets under `studio/app/`
- generated Studio docs payloads under `docs-viewer/generated/docs/studio/`
- generated Studio docs search under `docs-viewer/generated/search/studio/`
- canonical catalogue source data under `studio/data/canonical/catalogue/`
- Studio catalogue lookup data under `studio/data/generated/catalogue-lookup/`
- local scripts, tests, logs, or `var/` output
- footer or nav links that point public users to `/studio/` or `/docs/`

`/library/` and `/analysis/` are intentionally public read-only Docs Viewer installs.
They should keep using public generated docs payloads and public generated docs search.
`/docs/` is local management infrastructure and should not be published.

Generated output paths should stay explicit.
Adding a new generated family requires naming:

- source owner
- public projection path, if any
- Studio projection path, if any
- builder or local service owner
- check that prevents accidental publication or source-only field leaks

## Current Enforcement

Existing enforcement is split across several checks and builders:

- `admin-app/checks/projection_contract.json` classifies current Phase 6 artifact families and owns cross-domain public-build policy
- `admin-app/checks/audit_projection_contract.py` validates the manifest, `_config.yml` exclusions, checked-in public JSON field-leak rules, public template/script source references, and optional built public output
- public build surface audit checks that public output excludes Studio routes, Studio assets, Studio docs payloads/search, and canonical catalogue source
- run `bin/site-validate` to check the deploy root before upload
- catalogue build planners and validators decide which public catalogue projections are refreshed from source edits
- docs builder emits viewable/manage-mode metadata according to each scope contract
- search builders own scope-specific flattened search projections
- site consistency and field-registry checks catch selected catalogue/source relationship drift

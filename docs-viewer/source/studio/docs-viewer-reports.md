---
doc_id: docs-viewer-reports
title: Reports
added_date: 2026-05-13
last_updated: 2026-06-24
parent_id: docs-viewer
viewable: true
viewer_report: reports_list
viewer_report_access: local
---
# Docs Viewer Reports

Docs Viewer reports are lightweight, document-level inspection surfaces rendered inside the normal Docs Viewer document pane.

They exist so a document can show generated data that is easier to scan as a list, table, or summary than as prose.
The report-backed document still behaves like any other Docs Viewer document: it has a `doc_id`, title, `parent_id`, generated title ordering, visibility, search metadata, bookmarks, and `/docs/` management-route links.

Reports are deliberately not a dashboard or workflow framework.
They are for read-only or inspection-oriented views over Docs Viewer data, not for source edits, imports, exports, rebuilds, or apply flows.

## Source Metadata

A source doc opts into a report with front matter:

```yaml
viewer_report: docs_index_table
viewer_report_scope: library
viewer_report_access: local
viewer_report_preset: library_documents_admin
```

Fields:

- `viewer_report`: report id from the report metadata registry
- `viewer_report_scope`: optional generated docs scope the report reads; defaults to the current viewer scope when omitted
- `viewer_report_access`: optional access intent; target supported values are `public` and `local`
- `viewer_report_preset`: optional report-specific preset id

If a report is not available in the current context, the document pane shows a small unavailable state instead of failing silently.

## Access Intent

`viewer_report_access` is an access intent on the parent document, not a promotion mechanism by itself.

Target values:

- `public`: the report is intended to be allowed on public static routes when the report has also been explicitly promoted and allowlisted
- `local`: the report is intended only for local `/docs/`, covering the current manage/local report use cases

Changing a source document to `viewer_report_access: public` does not automatically make the report executable on `/library/`, `/analysis/`, or another public route.
Public execution also requires a code/config promotion slice:

- the report id must be included in a public-safe report metadata projection
- the executable report loader must be included in the public runtime allowlist
- the public route must expose the browser-safe config and generated data roots the report needs
- the report implementation must avoid local services, management actions, source paths, credentials, and manage-only data

Treat `public` as a design-time requirement or a change request for an existing report until those promotion conditions are satisfied.
If the public route sees a report with `viewer_report_access: public` that has not been promoted, it should render a contained unavailable state rather than importing arbitrary report code.

`manage` is the legacy name for local-only report access.
The intended end state is to migrate existing `manage` report defaults and source front matter to `local`, avoiding a permanent compatibility alias unless a migration requires one with explicit removal criteria.

## Runtime Design

The manage Docs Viewer entrypoint opts into report mounting through `docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js`.
The shared document controller renders the document payload and calls an optional document-extras hook; it does not import report runtime, report services, or report modules.
Public entrypoints do not provide that hook, and public route config does not expose the report registry until a specific public report is promoted.

The entry runtime wires the document controller but does not own report filtering, sorting, row rendering, or report-specific data shaping.

The report controller:

- loads the report metadata registry supplied by the manage route config
- normalizes report and preset metadata
- checks the requested report id against the executable module allowlist
- applies the report access policy
- imports the allowed report module and calls its mount function

Report modules own their own rendering behavior and route-state parameters.
Report state should use report-prefixed URL parameters, such as `report_sort`, so ordinary Docs Viewer route state remains understandable.

## Registry And Metadata

Report metadata lives in:

- `docs-viewer/config/reports/reports.json`

The browser-visible projection used by the manage route is:

- `site/assets/data/docs/reports.json`

The source registry describes report ids, titles, descriptions, default access policy, loader ids, and presets.
The generated browser JSON is browser-visible when the manage route loads it and can be used by documentation and by the `reports_list` report without inspecting JavaScript source.
Public `/library/` and `/analysis/` route configs do not reference this registry.

Executable module loading remains allowlisted in:

- `docs-viewer/runtime/js/reports/docs-viewer-reports.js`

The JSON registry does not define arbitrary import paths.
Adding a JSON entry without a matching allowlisted loader does not make a new report executable.
This keeps the registry useful as user-facing metadata without turning it into an open-ended code-loading surface.

## Presets

Presets are named configurations for a reusable report module.
The report id chooses the module; the preset chooses a supported shape or behavior inside that module.

Example:

```yaml
viewer_report: docs_index_table
viewer_report_preset: library_documents_admin
```

Preset ids are implementation and design handles.
They are useful when configuring a report-backed source doc, but they are not intended as the language a user must quote when specifying a new requirement.

For requirements, describe the desired behavior in product terms:

- create a public A-Z list of Library docs by title
- create a management report that shows non-viewable docs first with title and `doc_id`
- create a generated-docs inspection list for parent or orphan records

The implementer then decides whether the behavior maps to an existing preset, needs a new preset, or needs a new report module.
This keeps requirements readable while preserving reusable technical configurations in `docs-viewer/config/reports/reports.json`.

## Current Reports

`docs_index_table` renders generated docs index-tree records for a selected scope.
It preserves the tree order by default and indents title cells by hierarchy depth.
It is used by [Library Documents](/docs/?scope=studio&doc=library-documents) to review Library docs in manage mode.

`reports_list` renders the report metadata registry itself.
This document uses it so the list of configured reports stays visible from the Docs Viewer.

`source_config` renders the Docs Viewer source config report in manage mode.
It reads through the standalone Docs Viewer service and shows source config, browser projection, generated output paths, and generated viewer options for every configured scope.

`semantic_references` renders generated semantic-reference targets and source docs in manage mode.
It reads the current scope's `references/index.json` plus per-target buckets from `references/by-target/`.
The report defaults to all configured docs scopes and provides a `report_scope` selector for focusing on one scope.

`docs_broken_links` runs the Docs Viewer broken-links audit for a selected scope in manage mode.
It uses the local Docs API endpoint `POST /docs/broken-links` and replaces the retired `/studio/docs-broken-links/` Studio route shell.

## Good Candidates

Good report candidates are compact, read-oriented views over generated docs data:

- docs index tables
- non-viewable docs lists
- parent, child, or orphan inspection lists
- recently updated or recently added variants
- public A-Z indexes
- generated-data summaries

Poor report candidates are workflows with writes, long-running operations, broad Studio route state, or project-specific write allowlists.

## Files

- `site/assets/data/docs/reports.json`
- `docs-viewer/config/reports/reports.json`
- `docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js`
- `docs-viewer/runtime/js/reports/docs-viewer-reports.js`
- `docs-viewer/runtime/js/reports/`
- `docs-viewer/static/css/docs-viewer-reports.css`

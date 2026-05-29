---
doc_id: docs-viewer-reports
title: Docs Viewer Reports
added_date: 2026-05-13
last_updated: 2026-05-25
parent_id: docs-viewer
viewer_report: reports_list
viewer_report_access: public
---
# Docs Viewer Reports

Docs Viewer reports are lightweight, document-level inspection surfaces rendered inside the normal Docs Viewer document pane.

They exist so a document can show generated data that is easier to scan as a list, table, or summary than as prose.
The report-backed document still behaves like any other Docs Viewer document: it has a `doc_id`, title, `parent_id`, generated title ordering, visibility, search metadata, bookmarks, and management-mode routing.

Reports are deliberately not a dashboard or workflow framework.
They are for read-only or inspection-oriented views over Docs Viewer data, not for source edits, imports, exports, rebuilds, or apply flows.

## Source Metadata

A source doc opts into a report with front matter:

```yaml
viewer_report: docs_index_table
viewer_report_scope: library
viewer_report_access: manage
viewer_report_preset: library_documents_admin
```

Fields:

- `viewer_report`: report id from the report metadata registry
- `viewer_report_scope`: optional generated docs scope the report reads; defaults to the current viewer scope when omitted
- `viewer_report_access`: optional access gate; supported values are `public`, `manage`, and `local`
- `viewer_report_preset`: optional report-specific preset id

If a report is not available in the current context, the document pane shows a small unavailable state instead of failing silently.

## Runtime Design

The Docs Viewer document controller detects report metadata on the loaded document payload, creates a small report context, and delegates to the report controller.
The entry runtime wires the document controller but does not own report filtering, sorting, row rendering, or report-specific data shaping.

The report controller:

- loads the browser-visible report metadata registry
- normalizes report and preset metadata
- checks the requested report id against the executable module allowlist
- applies the report access policy
- imports the allowed report module and calls its mount function

Report modules own their own rendering behavior and route-state parameters.
Report state should use report-prefixed URL parameters, such as `report_sort`, so ordinary Docs Viewer route state remains understandable.

## Registry And Metadata

Report metadata lives in:

- `assets/data/docs/reports.json`

That JSON file is intentionally browser-visible.
It describes report ids, titles, descriptions, default access policy, loader ids, and presets.
It can be used by documentation and by the `reports_list` report without inspecting JavaScript source.

Executable module loading remains allowlisted in:

- `docs-viewer/runtime/js/docs-viewer-reports.js`

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
- create a management report that shows hidden docs first with title and `doc_id`
- create a generated-docs inspection list for parent or orphan records

The implementer then decides whether the behavior maps to an existing preset, needs a new preset, or needs a new report module.
This keeps requirements readable while preserving reusable technical configurations in `assets/data/docs/reports.json`.

## Current Reports

`docs_index_table` renders generated docs index records for a selected scope.
It is used by [Library Documents](/docs/?scope=studio&doc=library-documents) to review Library docs in manage mode.

`reports_list` renders the report metadata registry itself.
This document uses it so the list of configured reports stays visible from the Docs Viewer.

`source_config` renders the Docs Viewer source config report in manage mode.
It reads through the standalone Docs Viewer service and shows source config, browser projection, generated output paths, and generated viewer options for every configured scope.

`change_history` renders structured docs-log entries in manage mode.
It reads ignored local projections under `studio/workflows/change-requests/generated/` through the Docs management API and provides domain filtering for migrated change history.

`semantic_references` renders generated semantic-reference targets and source docs in manage mode.
It reads the current scope's `references/index.json` plus per-target buckets from `references/by-target/`.
The report defaults to all configured docs scopes and provides a `report_scope` selector for focusing on one scope.

`docs_broken_links` runs the Docs Viewer broken-links audit for a selected scope in manage mode.
It uses the local Docs API endpoint `POST /docs/broken-links` and replaces the retired `/studio/docs-broken-links/` Studio route shell.

## Good Candidates

Good report candidates are compact, read-oriented views over generated docs data:

- docs index tables
- hidden or non-viewable docs lists
- parent, child, or orphan inspection lists
- recently updated or recently added variants
- public A-Z indexes
- generated-data summaries

Poor report candidates are workflows with writes, long-running operations, broad Studio route state, or project-specific write allowlists.

## Files

- `assets/data/docs/reports.json`
- `docs-viewer/runtime/js/docs-viewer-reports.js`
- `docs-viewer/runtime/js/reports/`
- `docs-viewer/static/css/docs-viewer-reports.css`

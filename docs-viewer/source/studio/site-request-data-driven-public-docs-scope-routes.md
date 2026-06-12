---
doc_id: site-request-data-driven-public-docs-scope-routes
title: Data-Driven Public Docs Scope Routes Request
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: planned
parent_id: change-requests
viewable: true
---
# Data-Driven Public Docs Scope Routes Request

Status:

- planned

## Summary

Make public Docs Viewer scope creation data-driven.

Creating a new public read-only Docs Viewer scope must update source/config records and generated route metadata.
It must not generate new Python source files or require hardcoded per-scope route entries in the public-site builder.

## Context

The static public-site migration replaced Jekyll/Liquid public route stubs with Python-rendered static HTML artifacts.
The current public Docs Viewer route renderer is already generic enough to render read-only Docs Viewer shells, but the installed public routes are still listed explicitly in `public-site/build/public_site_builder/routes.py`.

The Docs Viewer New Scope lifecycle path also still contains a retired public-route assumption: for public read-only scopes it plans and writes a Markdown route stub under the requested public route path.
That was appropriate for the previous Jekyll route model, but it is wrong for the current static builder.

## Problem

A new public read-only scope currently has two stale extension points:

- public route shells are represented as hardcoded Python entries for `library` and `analysis`
- New Scope public-readonly apply still writes a legacy Markdown route stub

That creates a maintenance trap.
If each new public scope requires a Python code edit, the public route model becomes source-code-driven rather than config-driven.
If New Scope generates Python code, it creates a worse problem: local management UI would become a source-code generator for installed public pages.

## Goals

- Make public Docs Viewer routes derive from data/config records.
- Keep public route rendering in existing Python builder modules, not generated Python source.
- Refactor public-site route assembly so public Docs Viewer routes are expanded from route config or scope config.
- Update New Scope public-readonly preview/apply so it creates or updates data/config records only.
- Ensure the write set clearly separates:
  - source docs
  - scope config
  - route config
  - public-site config or derived public-site inputs
  - working generated outputs
  - published public snapshots
- Preserve manage-mode scope creation behavior.
- Preserve public read-only behavior with no management assets, backend probes, or local write capability.

## Non-Goals

- Do not generate Python scripts or Python route entries from the New Scope action.
- Do not reintroduce Jekyll, Liquid route stubs, or persistent Markdown public route files.
- Do not change public Docs Viewer runtime behavior unless required by the route-config refactor.
- Do not redesign Docs Viewer scope storage or workspace mounting; that belongs to the workspace-mount architecture request.
- Do not make every Docs Viewer scope public by default.

## Decisions Needed

Before implementation, decide:

- whether public route records are edited directly in `docs-viewer/config/routes/*.json` or generated from `docs-viewer/config/scopes/docs_scopes.json`
- whether `public-site/config/public-site.json` should list public Docs Viewer assets per scope or derive them from scope config at build time
- whether New Scope public-readonly creation should be temporarily blocked until the data-driven public route path exists
- whether public route audit requirements are static configured lists, derived generated expectations, or both
- whether scope deletion should remove public route records and public-site config entries for user-created public scopes

## Candidate Implementation Slices

1. Audit current public Docs Viewer route ownership.
2. Define the public Docs Viewer route metadata source of truth.
3. Refactor public-site route assembly to render public Docs Viewer routes from data.
4. Refactor public-site config/audit handling for public Docs Viewer scope assets.
5. Update New Scope public-readonly preview/apply to write data/config records only.
6. Update scope delete behavior for user-created public scopes.
7. Update stable docs and route lifecycle tests.

## Verification Expectations

- Focused Python tests for data-driven public Docs Viewer route expansion.
- Focused tests proving New Scope public-readonly does not write Markdown route stubs or Python source.
- Focused tests for route config records produced or edited by the lifecycle path.
- Public-site build and artifact audit.
- Public Docs Viewer browser smoke for existing `/library/` and `/analysis/`.
- A temporary fixture or test scope proving a new public read-only route can be rendered without editing Python route code.

## Related Docs

- [Portable Scope Setup](/docs/?scope=studio&doc=docs-viewer-portable-scope-setup)
- [New Scopes Builder](/docs/?scope=studio&doc=docs-viewer-new-scopes-builder)
- [Public Scopes](/docs/?scope=studio&doc=docs-viewer-public-scopes)
- [Public Site Static Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build)

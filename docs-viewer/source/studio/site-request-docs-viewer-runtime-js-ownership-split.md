---
doc_id: site-request-docs-viewer-runtime-js-ownership-split
title: Docs Viewer Runtime JavaScript Ownership Split Request
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: planned
parent_id: change-requests
viewable: true
---
# Docs Viewer Runtime JavaScript Ownership Split Request

Status:

- planned

## Summary

Split Docs Viewer runtime JavaScript into explicit public, shared, management, and reporting ownership areas.

After the split, the public-site GitHub Actions workflow should trigger on public/shared runtime changes only, instead of treating every file under `docs-viewer/runtime/js/` as public-site affecting.

## Context

The public-site workflow currently includes this path filter:

- `docs-viewer/runtime/js/**`

That filter is intentionally conservative, but it is too broad for ongoing development.
The directory contains both public read-only runtime modules and local Studio/management modules.

The New Scope public-disable fix changed `docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js`.
That module is loaded from management code and is not part of the current public artifact runtime copy graph, but the broad workflow filter still triggered the public-site build.

## Problem

The current folder boundary does not express runtime ownership.

As a result:

- local management-only JavaScript changes can trigger public-site builds and deploy gates
- public-site workflow filters need to compensate for unclear source ownership
- future runtime refactors can accidentally expand or shrink the public artifact without an obvious directory-level review point
- file-level workflow filters would need manual maintenance as imports move

## Goals

- Define stable Docs Viewer JavaScript ownership areas.
- Move public read-only runtime modules into a public-owned area.
- Move modules used by both public and management runtimes into a shared-owned area.
- Move local management-only modules into a management-owned area.
- Move report-only modules into a report-owned area.
- Update static imports and dynamic imports after the move.
- Update public-site builder config and validation to copy the public runtime from the new ownership areas.
- Update `.github/workflows/public-site.yml` path filters so public-site builds trigger on public/shared runtime changes and not on management-only changes.
- Keep existing public Docs Viewer behavior for `/library/` and `/analysis/`.
- Keep existing local Studio Docs Viewer management behavior.

## Non-Goals

- Do not introduce a JavaScript bundler or transpiler.
- Do not convert classic public catalogue scripts under `assets/js/`; that belongs to the public JavaScript runtime and payload review request.
- Do not redesign the Docs Viewer public route contract.
- Do not change generated docs payload schemas.
- Do not remove management features from the local Studio runtime.

## Proposed Ownership Areas

Use directory names that make workflow ownership clear:

- `docs-viewer/runtime/js/public/`
- `docs-viewer/runtime/js/shared/`
- `docs-viewer/runtime/js/management/`
- `docs-viewer/runtime/js/reports/`

The exact file placement must be decided from an import graph audit before files move.

## Audit Requirements

The first implementation batch must record:

- the current public runtime copy graph produced from `docs-viewer-public.js`
- all static imports from public runtime entrypoints
- all dynamic imports reachable from public runtime entrypoints
- all management-only modules and their dynamic import boundaries
- all report-only modules and their entrypoints
- files that are used by both public and management runtimes
- files currently copied into `_public_site/docs-viewer/runtime/js/`
- workflow path filters that currently trigger public-site builds

## Decisions Needed

Before moving files, decide:

- whether entrypoint filenames stay at the runtime root as compatibility shims for one release or move directly into `public/`
- whether shared modules live under `shared/` even when only public runtime imports them today but management import is expected
- whether the public-site builder should derive public runtime files only from entrypoints or also enforce an allowlisted directory policy
- whether workflow filters should include `shared/**` unconditionally or derive the public runtime graph in a CI precheck
- whether validation should assert that management and report modules are absent from the public artifact by directory prefix

## Candidate Implementation Slices

1. Runtime ownership and import graph audit.
2. Directory split plan and file placement map.
3. Move public and shared modules, then update imports.
4. Move management and report modules, then update dynamic imports.
5. Update public-site builder config, artifact validation, and expected runtime count.
6. Update GitHub Actions path filters to public/shared ownership paths.
7. Update Docs Viewer runtime documentation.

## Verification Expectations

- Focused import graph check for the public runtime.
- Public-site build and artifact audit.
- Validation proving management and report runtime files are absent from `_public_site`.
- Public Docs Viewer browser smoke for `/library/` and `/analysis/`.
- Local Studio Docs Viewer management smoke, including New Scope modal behavior.
- Actionlint validation for `.github/workflows/public-site.yml`.
- A non-public management-only JS change should not match the public-site workflow path filters after the split.

## Related Docs

- [GitHub Actions](/docs/?scope=studio&doc=github-actions)
- [Public JavaScript Runtime and Payload Review Request](/docs/?scope=studio&doc=site-request-public-js-runtime-payload-review)
- [Portable Static Docs Viewer Install Request](/docs/?scope=studio&doc=site-request-data-driven-public-docs-scope-routes)

---
doc_id: docs-viewer-portable-setup
title: Docs Viewer Portable Setup
added_date: 2026-05-11
last_updated: 2026-05-19
parent_id: docs-viewer
sort_order: 3000
---
# Docs Viewer Portable Setup

This document answers two practical questions from the current implementation state:

- what must be copied into an existing Jekyll project to use the Docs Viewer
- how to set up a new Library-style docs scope with one local management view and one read-only public view

It intentionally describes the current repo as it is now after the initial shell/service extraction.
The older portability plan for reducing host integration work lives in [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer).

## Current Shape

The Docs Viewer is not a separately packaged plugin yet.
It is a tracked `docs-viewer/` source boundary plus host-owned Jekyll route adapters, generated JSON outputs, and wrapper build commands.
The standalone Docs Viewer service owns local `/docs/` manage mode.

Current live scopes:

- `studio`: source docs in `docs-viewer/source/studio/`, managed at `<DOCS_VIEWER_BASE_URL>/docs/?scope=studio&mode=manage`
- `library`: source docs in `docs-viewer/source/library/`, managed at `<DOCS_VIEWER_BASE_URL>/docs/?scope=library&mode=manage`, read at `/library/`
- `analysis`: source docs in `docs-viewer/source/analysis/`, managed at `<DOCS_VIEWER_BASE_URL>/docs/?scope=analysis&mode=manage`, read at `/analysis/`

The public `/library/` and `/analysis/` routes are read-only.
They should not expose `?mode=manage`, management CSS, management JS, localhost write endpoints, or Docs Import.

The `/docs/` route is the local management page served by `docs-viewer/bin/docs-viewer`.
It can switch the active scope with the `scope` query parameter.
## Child References

- [File Manifest](/docs/?scope=studio&doc=docs-viewer-portable-files) lists the current include, runtime, CSS, config, generated-output, script, dependency, and management-server copy set.
- [Source Shape](/docs/?scope=studio&doc=docs-viewer-portable-source-shape) defines the required Markdown/front-matter shape for portable scopes.
- [Scope Setup](/docs/?scope=studio&doc=docs-viewer-portable-scope-setup) gives the current Library-style scope setup procedure.

## Related Planning

Use this page as the current install guide.
Use [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer) for the ordered work to reduce hardcoded scope lists, move docs search under Docs Viewer ownership, extract CSS/config, and package the local management/import surface.

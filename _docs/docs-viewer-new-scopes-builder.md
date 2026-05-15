---
doc_id: docs-viewer-new-scopes-builder
title: New Scopes Builder
added_date: 2026-05-15
last_updated: "2026-05-15"
parent_id: docs-viewer
sort_order: 45
hidden: false
---
# New Scopes Builder

This document records the technical design and implementation notes for the Docs Viewer New Scopes Builder.
It should be populated as the implementation progresses and reviewed fully before the feature is treated as complete.

The product request is tracked in [Docs Viewer New Scope Button Request](/docs/?scope=studio&doc=site-request-docs-viewer-new-scope-button).

## Purpose

The New Scopes Builder is the local-management workflow for creating and deleting Docs Viewer scopes from `/docs/?mode=manage`.

It should:

- create the same files a developer would otherwise create by hand
- keep all write behavior behind the loopback docs-management server
- preserve public read-only routes
- show the planned write or delete set before any write
- record ownership in a scope manifest so deletion can fail closed

## Scope Creation Boundary

A Docs Viewer scope is made from four parts:

- source root, such as `_docs_research/`
- scope config entry in `scripts/docs/docs_scopes.json`
- generated viewer/search outputs under `assets/data/docs/scopes/<scope>/` and `assets/data/search/<scope>/`
- optional read-only route page, such as `research/index.md`

The localhost docs-management server may create or update those files.
The public browser runtime must not.

Scope creation should run only through:

- `/docs/?mode=manage`
- the loopback docs-management server
- explicit write allowlists in the server
- normal rebuild commands after the write

Public read-only routes should keep using `docs_viewer_readonly_route.html`.
They should not expose create-scope controls, management endpoints, Docs Import, or local write capabilities.

## Route Adapter Choices

Use `docs_viewer_readonly_route.html` for public read-only routes.

Example route file:

```liquid
---
layout: default
title: "Research"
section: research
permalink: /research/
---

{% include docs_viewer_readonly_route.html
  search_placeholder='search research'
  search_aria_label='Search research'
%}
```

Use `docs_viewer_management_route.html` only for the local management shell.
In this repo, that route is `/docs/`.
The adapter requires `docs_viewer_management_enabled: true`, which is set by `_config.dev-studio.yml`; public builds leave the flag false and receive the read-only shell instead.

The management shell can switch scopes with the `scope` query parameter.
Public read-only routes ignore and normalize away `scope` and `mode` so they cannot become management routes by query string.

## Publishing Modes

### Public Read-Only Scope

Use this option when the scope should become part of the published static site.

Create and commit:

- source root and Markdown files
- `scripts/docs/docs_scopes.json` entry
- read-only route page
- generated docs/search JSON if the repo tracks generated outputs for the site

Then deploy through the normal static site workflow.
Readers use the public route, such as `/research/`.
Local edits still happen through `/docs/?scope=research&mode=manage`.

### Local-Only Scope Committed To Repo

Use this option when the scope should be available to local developers or Codex sessions, but not published as a public route.

Create and commit:

- source root and Markdown files
- `scripts/docs/docs_scopes.json` entry
- generated docs/search JSON if local workflows expect checked-in generated data

Do not create a public read-only route page.
The scope remains available through `/docs/?scope=<scope>&mode=manage` when the local server is running.

This is useful for private planning notes, local drafts, or internal review material that should move with the repo but not have a public URL.

### Local-Only Scope Not Committed

Use this option for private experiments or throwaway work.

Create locally:

- source root and Markdown files
- temporary scope config entry
- generated outputs as needed for local preview

Do not commit the source root, config entry, generated outputs, or route file.
The scope exists only in the local working tree.

This option needs clear cleanup expectations because generated files and config edits can otherwise look like accidental repo drift.
The management UI should label this mode as local-only and make the write set visible before creating files.

## Current Implementation State

Initial server-side foundation is in place:

- `scripts/docs/docs_scope_manifest.json` records existing scopes as system-owned
- `scripts/docs/docs_scope_manifest.py` owns manifest loading, backfill, validation, and preview planning
- `GET /capabilities` advertises scope lifecycle preview support
- `POST /docs/scopes/create-preview` reports a validated create write set
- `POST /docs/scopes/delete-preview` reports a manifest-backed delete plan and blocks system scopes

Apply/write behavior and the management UI are not implemented yet.

## Create Flow Contract

Minimum fields:

- scope id
- title
- source root
- default doc id
- public route path, only when publishing as public read-only
- whether to build inline search
- whether generated outputs should be written immediately

For public read-only scopes, the server should create the route page with `docs_viewer_readonly_route.html`.
For local-only scopes, the server should skip route creation.

The server response should list:

- files created
- files changed
- build commands run or suggested
- resulting management URL
- resulting public URL, only when a public route exists

Preview-only endpoints currently report this planned write set without writing files.
The apply endpoints should remain hidden until the allowlisted source-root, route-file, generated-output, and manifest-write implementation is complete.

## Safety Rules

- Scope creation is a local write action and must stay behind the loopback management server.
- Public routes must remain read-only even if `mode=manage` or `scope=<other-scope>` appears in the URL.
- The write server should validate scope ids and route paths before writing.
- The write server should refuse paths outside the configured repo allowlist.
- Local-only uncommitted scopes should be easy to identify in the response and cleanup guidance.
- Generated data should be rebuilt after scope config changes so `assets/docs-viewer/data/docs-viewer-config.json` stays current.

## Design Notes To Complete

Record final decisions here as the implementation lands:

- manifest schema and ownership semantics
- create endpoint payload and response contract
- delete endpoint payload and response contract
- publishing-mode behavior
- allowlisted file-write rules
- generated docs/search follow-through
- management UI controls, modal states, and result reporting
- manual verification workflow

## Open Implementation Notes

- Apply endpoints should remain hidden from capabilities until allowlisted writes are implemented.
- System-owned scopes must never be delete-eligible through this workflow.
- Public read-only scopes need route pages that use `docs_viewer_readonly_route.html`.
- Local-only scopes should not create public read-only route pages.
- Generated output choices need clear reporting so UI users are not left guessing whether a follow-up build is needed.

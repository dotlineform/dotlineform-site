---
doc_id: site-request-docs-viewer-new-scope-button
title: Docs Viewer New Scope Button Request
added_date: 2026-05-14
last_updated: 2026-05-14
ui_status: draft
parent_id: change-requests
sort_order: 213
---
# Docs Viewer New Scope Button Request

Status:

- requested

## Summary

Add a local-only New scope action to the Docs Viewer management route.

The action should let a local operator create a new Docs Viewer scope from `/docs/?mode=manage` without hand-editing the source root, scope config, route page, and generated output setup.
It should implement the future flow described in [Docs Viewer Route Creation](/docs/?scope=studio&doc=docs-viewer-route-creation).

## Goal

Create a management-only scope-creation workflow that writes the same files a developer would create by hand, while preserving the public read-only boundary for Docs Viewer routes.

The desired end state is:

- `/docs/?mode=manage` exposes a New scope control when local management capabilities are available
- the flow asks for publishing mode before writing files
- public read-only routes never expose scope-creation controls or management endpoints
- the docs-management server performs all writes through explicit allowlists
- the result clearly reports created files, changed files, build actions, and resulting URLs

## Scope

Included:

- New scope UI entry point in the Docs Viewer management shell
- local form or modal for scope metadata and publishing mode
- docs-management server endpoint for creating scope files
- validation for scope ids, source roots, default doc ids, route paths, and output choices
- optional route page creation for public read-only scopes
- rebuild or suggested rebuild behavior after scope config changes
- response reporting for created files, changed files, commands, and URLs

Excluded:

- public scope creation from read-only routes
- remote or hosted write behavior
- arbitrary filesystem writes outside the repo allowlist
- a general route/page generator beyond Docs Viewer scope creation
- source document import or bulk document migration

## Requirements

### Management-Only Entry Point

The New scope button should be available only when the Docs Viewer is running as the local management shell.

Allowed context:

- `/docs/?mode=manage`
- local docs-management server available
- server capability advertises scope creation

Disallowed contexts:

- public read-only routes such as `/library/` or `/analysis/`
- read-only Docs Viewer shells opened without management mode
- any route where management is attempted by query string alone

### Publishing Mode Choice

The flow should require a publishing-mode decision before writing files.

Initial modes:

- public read-only scope
- local-only scope committed to the repo
- local-only uncommitted scope

The UI should explain the write set for the selected mode before submission.

### Minimum Fields

Collect:

- scope id
- title
- source root
- default doc id
- public route path, only for public read-only scopes
- whether to build inline search
- whether generated outputs should be written immediately

Visible UI labels and action copy should come from `studio_config.json` `ui_text` where practical.

### File Creation Rules

For public read-only scopes, the server should create:

- source root
- scope config entry in `scripts/docs/docs_scopes.json`
- public route page using `docs_viewer_readonly_route.html`
- generated docs/search outputs if immediate writes are requested

For local-only committed scopes, the server should create:

- source root
- scope config entry in `scripts/docs/docs_scopes.json`
- generated docs/search outputs if local workflows expect checked-in generated data and immediate writes are requested

For local-only uncommitted scopes, the server should create only the requested local files and clearly label the result as local-only drift that may need cleanup.

Local-only scopes should not create a public read-only route page.

### Server Response

The result should list:

- files created
- files changed
- build commands run or suggested
- resulting management URL
- resulting public URL, only when a public route exists
- local-only cleanup guidance when files are not intended to be committed

## Safety Rules

- all writes must run through the loopback docs-management server
- scope ids must be validated before any write
- route paths must be normalized and validated before route creation
- source roots and generated output paths must resolve inside configured repo allowlists
- existing files should not be overwritten without an explicit conflict response
- public routes must remain read-only even when `mode=manage` appears in the URL
- generated docs/search data should be rebuilt or explicitly reported as stale after scope config changes

## Implementation Tasks

### Task 1. Define Server Capability And Endpoint Contract

Status:

- proposed

Add a docs-management capability for scope creation and define the endpoint payload, validation errors, dry-run behavior, and response shape.

Acceptance:

- the Docs Viewer can detect whether New scope is available
- unsupported environments hide or disable the action cleanly
- the endpoint can return a dry-run write set before performing writes

### Task 2. Build The Management UI Flow

Status:

- proposed

Add the New scope control and form to the Docs Viewer management shell.

Acceptance:

- the control appears only in management mode with local capability support
- publishing mode drives which fields are required
- route path input is shown only for public read-only scopes
- the write set is visible before submission
- validation errors are shown without writing files

### Task 3. Implement Allowlisted Scope File Writes

Status:

- proposed

Implement server-side creation for source roots, scope config entries, optional route pages, and optional generated outputs.

Acceptance:

- public read-only scopes use `docs_viewer_readonly_route.html`
- local-only scopes skip route creation
- existing-file conflicts fail safely
- paths outside allowlists are rejected
- the response distinguishes created and changed files

### Task 4. Align Rebuild And Search Follow-Through

Status:

- proposed

After a scope is created, run or suggest the required docs and search build commands for the selected mode.

Acceptance:

- `assets/docs-viewer/data/docs-viewer-config.json` is refreshed or reported as needing refresh
- generated docs payloads are written when requested
- inline search output is written only when enabled
- command reporting uses project-local script forms

### Task 5. Document The Completed Workflow

Status:

- proposed

When implemented, update the stable Docs Viewer route-creation and management docs with the actual UI and server behavior.

Acceptance:

- stable docs describe the New scope workflow accurately
- safety boundaries remain documented
- this request can be moved to completed requests or archive when all tasks are done

## Open Questions

- Should the first implementation support a dry-run preview only, then add writes in a later slice?
- Should local-only uncommitted scopes be tracked anywhere so cleanup is easier?
- Should generated outputs be written by default, or should the default be to suggest explicit build commands?
- Should source root creation include a default index document, or only create an empty source directory?

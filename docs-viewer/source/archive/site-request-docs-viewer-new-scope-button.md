---
doc_id: site-request-docs-viewer-new-scope-button
title: Docs Viewer New Scope Button Request
added_date: 2026-05-14
last_updated: 2026-05-15
ui_status: done
sort_order: 70000
viewable: true
---
# Docs Viewer New Scope Button Request

Status:

- implemented

## Summary

Add a local-only New scope action to the Docs Viewer management route.

The action should let a local operator create a new Docs Viewer scope from `/docs/?mode=manage` without hand-editing the source root, scope config, route page, and generated output setup.
Implementation details should be carried forward in [New Scopes Builder](/docs/?scope=studio&doc=docs-viewer-new-scopes-builder).

## Goal

Create a management-only scope lifecycle workflow that writes and deletes the same files a developer would manage by hand, while preserving the public read-only boundary for Docs Viewer routes.

The desired end state is:

- `/docs/?mode=manage` exposes a New scope control when local management capabilities are available
- the create flow uses a preview and save action, where save writes the new scope
- the flow asks for publishing mode before writing files
- scope-created files are recorded in a manifest
- user-created scopes can be deleted from the same management boundary
- public read-only routes never expose scope-creation controls or management endpoints
- the Docs management service performs all writes through explicit allowlists
- the result clearly reports created files, changed files, build actions, and resulting URLs

## Scope

Included:

- New scope UI entry point in the Docs Viewer management shell
- local form or modal for scope metadata and publishing mode
- Docs management service endpoint for creating scope files
- Docs management service endpoint for deleting eligible user-created scopes
- manifest-style JSON file that records files created for every scope
- retrospective manifest population for existing scopes
- validation for scope ids, source roots, default doc ids, route paths, and output choices
- optional route page creation for public read-only scopes
- automatic rebuild behavior after scope config changes
- response reporting for created files, changed files, commands, and URLs

Excluded:

- public scope creation from read-only routes
- remote or hosted write behavior
- arbitrary filesystem writes outside the repo allowlist
- a general route/page generator beyond Docs Viewer scope creation
- source document import or bulk document migration
- deleting system scopes or scopes not created through this tool

## Requirements

### Management-Only Entry Point

The New scope and Delete scope controls should be available only when the Docs Viewer is running as the local management shell.

Allowed context:

- `/docs/?mode=manage`
- local Docs management service available
- server capability advertises scope lifecycle actions

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

### Preview And Save Flow

The UI should create a new scope through a preview and save action.

Behavior:

- preview validates inputs and shows the planned write set
- save performs the write
- save runs the required docs/search follow-through automatically
- the user should not be expected to run CLI commands after using the UI

Dry-run behavior should remain available in the CLI/server contract for implementation safety and tests, but it should not be exposed as a separate UI mode.

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
- scope config entry in `docs-viewer/config/scopes/docs_scopes.json`
- public route page using `docs_viewer_readonly_route.html`
- generated docs/search outputs if immediate writes are requested

For local-only committed scopes, the server should create:

- source root
- scope config entry in `docs-viewer/config/scopes/docs_scopes.json`
- generated docs/search outputs if local workflows expect checked-in generated data and immediate writes are requested

For local-only uncommitted scopes, the server should create only the requested local files and clearly label the result as local-only drift that may need cleanup.

Local-only scopes should not create a public read-only route page.

Every create action should include a default welcome page in the new source root rather than leaving the source directory empty.

### Scope Manifest

Add a manifest-style JSON file that records the files owned by each Docs Viewer scope.

The manifest should include:

- scope id
- scope type, such as public or local
- whether the scope is user-created or system-owned
- whether the scope was created by this tool
- repo status at creation time for local scopes, such as tracked or untracked
- file records for source files, config files, route files, generated docs files, generated search files, and default welcome page files
- creation metadata useful for audit and deletion, such as created timestamp and tool version if available

Public scopes are always repo tracked.
Local scopes should record repo status at creation time.

The implementation should retrospectively populate the manifest for all existing scopes.
Existing scopes should be marked as system-owned unless there is explicit evidence that they were created by this tool.

### Delete Scope

Add a management-only Delete scope action for scopes created by this tool.

Delete eligibility:

- the scope must exist in the manifest
- the manifest must mark it as user-created
- the manifest must mark it as created by this tool
- system scopes must not be deletable through the UI or server endpoint

Delete behavior:

- the UI asks the operator to select an eligible user-created scope to delete; Delete scope is not implicitly scoped to the currently open Docs Viewer scope
- preview the manifest-backed delete plan before writing
- warn when manifest-listed files no longer exist
- continue deleting files that still exist
- update scope config and generated docs/search outputs as needed
- keep backups under the normal backup retention plan

Backups should not be deleted immediately as part of scope deletion.
They remain subject to the existing backup retention policy and should eventually be removed through that normal retention flow.

### Server Response

The result should list:

- files created
- files changed
- files missing, for delete actions where manifest records point to paths that no longer exist
- build commands run or suggested
- resulting management URL
- resulting public URL, only when a public route exists
- local-only cleanup guidance when files are not intended to be committed

## Safety Rules

- all writes must run through the loopback Docs management service
- scope ids must be validated before any write
- route paths must be normalized and validated before route creation
- source roots and generated output paths must resolve inside configured repo allowlists
- existing files should not be overwritten without an explicit conflict response
- delete actions must be driven by manifest records, not ad hoc path discovery
- system scopes must fail closed for delete requests
- public routes must remain read-only even when `mode=manage` appears in the URL
- generated docs/search data should be rebuilt or explicitly reported as stale after scope config changes

## Key Decisions

- Dry-run should exist in the CLI/server contract but should not be exposed as a separate UI mode.
- The UI uses preview and save; save writes the new scope and runs required follow-through.
- All scope types should be tracked in a manifest-style JSON file.
- Existing scopes should be retrospectively added to the manifest.
- The manifest should distinguish user-created tool scopes from system-owned scopes.
- Delete scope belongs in the same implementation and should only allow deletion of user-created tool scopes.
- Delete scope is a selected-target workflow; the current Docs Viewer scope is only the management shell context and must not be treated as the implicit delete target.
- Delete should warn about missing manifest files but continue deleting files that still exist.
- Backups remain under normal backup retention after scope deletion.
- New source roots should include a default welcome page.

## Implementation Tasks

### Task 1. Define Manifest Schema And Backfill Existing Scopes

Status:

- implemented

Add the scope manifest schema and populate it for all existing Docs Viewer scopes.

Progress:

- `docs-viewer/config/scopes/docs_scope_manifest.json` now records Studio, Library, and Analysis.
- Existing scopes are marked system-owned, not user-created, and not tool-created.
- The manifest uses repo-relative file records and records source roots, scope config, default docs, route files, generated docs output, and generated search output.
- `docs-viewer/services/docs_scope_manifest.py` can backfill a manifest from `docs-viewer/config/scopes/docs_scopes.json` when the manifest is missing.

Acceptance:

- every existing scope has a manifest record
- existing scopes are marked as system-owned by default
- public scopes are marked repo tracked
- local scopes record repo status where it can be determined
- manifest paths are repo-relative and stay inside known allowlists

### Task 2. Define Server Capability And Endpoint Contract

Status:

- implemented

Add docs-management capabilities for scope creation and eligible scope deletion.
Define endpoint payloads, validation errors, dry-run behavior, preview behavior, and response shapes.

Progress:

- `GET /capabilities` now advertises `scope_lifecycle` support.
- Per-scope capability data reports whether a manifest record exists and whether the scope is delete-eligible.
- `POST /docs/scopes/create-preview` validates inputs and returns a planned create write set.
- `POST /docs/scopes/create-apply` requires `confirm: true`, re-runs preview validation, and writes allowlisted create-scope files.
- `POST /docs/scopes/delete-preview` returns a manifest-backed delete plan and blocks system-owned scopes.
- `POST /docs/scopes/delete-apply` requires `confirm: true`, re-runs preview validation, and deletes eligible user-created scopes.
- `create_apply` and `delete_apply` are now advertised.

Acceptance:

- the Docs Viewer can detect whether New scope and Delete scope are available
- unsupported environments hide or disable the action cleanly
- the create endpoint can return a preview write set before performing writes
- the delete endpoint can return a preview delete plan before performing writes
- create and delete apply endpoints fail closed without explicit confirmation
- CLI/server dry-run remains available without becoming a separate UI mode

### Task 3. Build The Management UI Flow

Status:

- implemented

Add the New scope and eligible Delete scope controls to the Docs Viewer management shell.

Commands to be added to the Actions button:

- New scope
- Delete scope

Implementation approach:

- keep `docs-viewer/runtime/js/docs-viewer-management.js` as the management command coordinator
- add a dedicated scope lifecycle UI module, `docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js`
- keep endpoint wrappers in `docs-viewer/runtime/js/docs-viewer-management-client.js`
- have the scope lifecycle module own create-scope form rendering, publishing-mode field state, preview/apply result rendering, delete target selection, and delete preview/apply result rendering
- reuse the existing Docs Viewer management modal shell/helpers rather than adding a second modal framework
- expose narrow flow entry points from the new module, such as `openCreateScopeFlow(...)` and `openDeleteScopeFlow(...)`, for `docs-viewer-management.js` to call from the Actions menu

Progress:

- the Actions menu now includes capability-gated `New scope` and `Delete scope` commands
- `docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js` owns the scope create/delete modal flows
- the create flow collects scope metadata, switches public route visibility based on publishing mode, previews the write set, and applies only after confirmation
- the delete flow asks the operator to select an eligible user-created target scope before previewing deletion
- create/delete apply payloads send `confirm: true`
- preview and result modals show created, changed, deleted, missing, command, and URL records returned by the server

Acceptance:

- controls appear only in management mode with local capability support - implemented
- publishing mode drives which fields are required - implemented
- route path input is shown only for public read-only scopes - implemented
- the write set is visible before submission - implemented
- delete asks the operator to select an eligible user-created scope before previewing deletion - implemented
- the delete plan is visible before submission - implemented
- delete targets are limited to eligible user-created scopes - implemented
- validation errors are shown without writing files - implemented

### Task 4. Implement Allowlisted Scope File Writes

Status:

- implemented

Implement server-side creation for source roots, default welcome docs, scope config entries, optional route pages, optional generated outputs, and manifest updates.

Acceptance:

- public read-only scopes use `docs_viewer_readonly_route.html` - implemented for create apply
- local-only scopes skip route creation - implemented for create apply
- new scopes include a default welcome page - implemented for create apply
- existing-file conflicts fail safely - implemented through preview re-validation
- paths outside allowlists are rejected - implemented through preview re-validation
- the response distinguishes created and changed files - implemented
- the manifest records the created scope files - implemented

Progress:

- `POST /docs/scopes/create-apply` is implemented behind `create_apply: true`.
- Apply requires `confirm: true` and re-runs create-preview before writing.
- A backup bundle is created for the previous scope config and manifest files before non-dry-run writes.
- Delete apply re-runs delete-preview before writing and removes only manifest-owned scope paths while treating config and manifest as changed files.

### Task 5. Implement Manifest-Backed Scope Delete

Status:

- implemented

Implement server-side deletion for scopes that are manifest-backed, user-created, and tool-created.

Acceptance:

- system-owned scopes cannot be deleted
- missing manifest-listed files produce warnings but do not block deleting existing files
- deleted files are reported explicitly
- missing files are reported explicitly
- backups are left to the normal backup retention plan
- scope config and generated outputs are updated consistently

Progress:

- `POST /docs/scopes/delete-apply` is implemented behind `delete_apply: true`.
- Apply requires `confirm: true` and re-runs delete-preview before writing.
- System-owned scopes and scopes not created by the lifecycle tool remain blocked.
- Missing manifest-listed files are reported in `missing_files` and do not block deleting existing files.
- Scope config and manifest entries are removed after the manifest-owned paths are deleted.

### Task 6. Align Rebuild And Search Follow-Through

Status:

- implemented

After a scope is created or deleted, run the required docs and search build commands for the selected mode.

Acceptance:

- `docs-viewer/config/defaults/docs-viewer-config.json` is refreshed or reported as needing refresh - implemented for create apply through the docs rebuild command
- generated docs payloads are written when requested - implemented for create apply
- deleted scope generated payloads are removed by delete apply
- inline search output is written only when enabled - implemented for create apply
- command reporting uses project-local script forms - implemented for create preview/apply responses
- UI users are not required to run CLI commands after save or delete

Progress:

- Create apply runs `./docs-viewer/build/build_docs.rb --scope <scope> --write` when generated outputs are requested.
- Create apply runs `./docs-viewer/build/build_search.rb --scope <scope> --write` only when inline search is enabled.
- Delete apply runs the full docs output refresh for the remaining configured scopes after removing the deleted scope from config.

### Task 7. Document The Completed Workflow

Status:

- implemented

When implemented, update the stable Docs Viewer route-creation and management docs with the actual UI and server behavior.

Progress:

- [New Scopes Builder](/docs/?scope=studio&doc=docs-viewer-new-scopes-builder) now owns the technical design notes.
- The retired route-creation doc was folded into New Scopes Builder so implementation details have one stable home.
- Server apply-write behavior and the management UI flow are now documented in New Scopes Builder.

Acceptance:

- stable docs describe the New scope workflow accurately - implemented
- stable docs describe the Delete scope workflow accurately - implemented
- stable docs describe the scope manifest contract - implemented
- safety boundaries remain documented - implemented
- this request can be moved to archive when all tasks are done

---
doc_id: docs-viewer-new-scopes-builder
title: New Scopes Builder
added_date: 2026-05-15
last_updated: 2026-05-29
parent_id: docs-viewer
viewable: true
---
# New Scopes Builder

This document records the technical design and implementation notes for the Docs Viewer New Scopes Builder.
It should be populated as the implementation progresses and reviewed fully before the feature is treated as complete.

The product request is tracked in [Docs Viewer New Scope Button Request](/docs/?scope=studio&doc=site-request-docs-viewer-new-scope-button).

## Purpose

The New Scopes Builder is the local-management workflow for creating and deleting Docs Viewer scopes from `/docs/?mode=manage`.

It should:

- create the same files a developer would otherwise create by hand
- keep all write behavior behind the loopback Docs Viewer service
- preserve public read-only routes
- show the planned write or delete set before any write
- record ownership in a scope manifest so deletion can fail closed

## Scope Creation Boundary

A Docs Viewer scope is made from four parts:

- source root, such as `docs-viewer/source/research/`
- scope config entry in `docs-viewer/config/scopes/docs_scopes.json`
- generated viewer/search outputs, whose roots depend on publishing mode
- optional read-only route page, such as `research/index.md`, only for public read-only scopes

Public read-only scopes use generated outputs under:

- `assets/data/docs/scopes/<scope>/`
- `assets/data/search/<scope>/index.json`

Committed manage-mode scopes use generated outputs under:

- `docs-viewer/generated/docs/<scope>/`
- `docs-viewer/generated/search/<scope>/index.json`

Manage-mode scopes must not write generated docs/search runtime payloads under `assets/data/docs/scopes/` or `assets/data/search/`.
Those `assets/` roots are public static-site payload roots and are reserved for scopes that are explicitly public read-only.

The localhost Docs Viewer service may create or update those files.
The public browser runtime must not.

Scope creation should run only through:

- `/docs/?mode=manage`
- the loopback Docs Viewer service
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

Use `docs-viewer/shell/docs-viewer-shell.html` through the standalone Docs Viewer service for the local management shell.
In this repo, that route is `/docs/`.
The retired Jekyll `docs_viewer_management_route.html` adapter should not be restored; public builds use read-only route shells, while the standalone Docs Viewer service serves `/docs/` management locally.

The management shell can switch scopes with the `scope` query parameter.
Public read-only routes ignore and normalize away `scope` and `mode` so they cannot become management routes by query string.

## Publishing Modes

### Public Read-Only Scope

Use this option when the scope should become part of the published static site.

Create and commit:

- source root and Markdown files
- `docs-viewer/config/scopes/docs_scopes.json` entry
- read-only route page
- generated docs/search JSON under `assets/data/docs/scopes/<scope>/` and `assets/data/search/<scope>/index.json` if the repo tracks generated outputs for the site

Then deploy through the normal static site workflow.
Readers use the public route, such as `/research/`.
Local edits still happen through `/docs/?scope=research&mode=manage`.

### Committed Manage-Mode Scope

Use this option when the scope should be available to local developers or Codex sessions, but not published as a public route.

Create and commit:

- source root and Markdown files
- `docs-viewer/config/scopes/docs_scopes.json` entry
- generated docs/search JSON under `docs-viewer/generated/docs/<scope>/` and `docs-viewer/generated/search/<scope>/index.json` if local workflows expect checked-in generated data

Do not create a public read-only route page.
The scope remains available through `/docs/?scope=<scope>&mode=manage` when the local server is running.
The generated JSON is tracked runtime data, but it is not a public static asset because it lives under the Docs Viewer-owned `docs-viewer/` boundary rather than under `assets/`.

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

The scope lifecycle workflow now has server-side preview/apply endpoints and a management UI entry point:

- `docs-viewer/config/scopes/docs_scope_manifest.json` records existing scopes as system-owned
- `docs-viewer/services/docs_scope_manifest.py` owns manifest loading, backfill, validation, and preview planning
- `GET /capabilities` advertises scope lifecycle preview and apply support
- `POST /docs/scopes/create-preview` reports a validated create write set
- `POST /docs/scopes/create-apply` creates allowlisted scope files after explicit confirmation
- `POST /docs/scopes/delete-preview` reports a manifest-backed delete plan and blocks system scopes
- `POST /docs/scopes/delete-apply` deletes eligible user-created scopes after explicit confirmation
- the `/docs/?mode=manage` Actions menu exposes capability-gated `New scope` and `Delete scope` commands
- `docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js` owns the create/delete modal flows
- `docs-viewer/runtime/js/docs-viewer-management.js` remains the management command coordinator
- `docs-viewer/runtime/js/docs-viewer-management-client.js` owns the scope lifecycle endpoint wrappers

The stable documentation still needs a final pass after hands-on use, but the core lifecycle UI and server contracts are implemented.

## Manifest Design

Manifest file:

- `docs-viewer/config/scopes/docs_scope_manifest.json`

Schema version:

- `docs_scope_manifest_v1`

Top-level fields:

- `schema_version`: manifest schema id
- `tool_id`: current lifecycle tool id, `docs-viewer-scope-lifecycle`
- `updated_at`: UTC timestamp for the manifest payload
- `scopes`: scope ownership records

Scope record fields:

- `scope_id`: configured Docs Viewer scope id
- `scope_type`: `public`, `local`, or `local_uncommitted`
- `owner`: `system` or a future user/tool owner value
- `user_created`: whether the scope was created by a local operator
- `created_by_tool`: whether this lifecycle tool created the scope
- `tool_id`: creating tool id when applicable
- `repo_status_at_creation`: `tracked`, `untracked`, or `unknown`
- `created_at`: creation timestamp when known
- `updated_at`: manifest-record timestamp
- `files`: repo-relative file records owned by the scope
- `metadata`: audit metadata such as `backfilled`, `viewer_base_url`, and `default_doc_id`

File record fields:

- `kind`: file role, such as `source_root`, `scope_config`, `default_source_doc`, `route_file`, `generated_docs_root`, `generated_docs_index`, `generated_docs_payload_root`, or `generated_search_index`
- `path`: repo-relative path
- `action`: current manifest action, usually `track`; preview responses use actions such as `create`, `change`, or `delete`
- `exists`: whether the path existed when the record or preview was generated

Existing scopes are backfilled as system-owned records.
That means Studio, Library, and Analysis are visible in lifecycle capability data but are not delete-eligible.
Future created scopes must set both `user_created: true` and `created_by_tool: true` before delete can be available.

## Capability Contract

`GET /capabilities` includes a top-level lifecycle capability block:

```json
{
  "scope_lifecycle": {
    "manifest": true,
    "create_preview": true,
    "create_apply": true,
    "delete_preview": true,
    "delete_apply": true,
    "publishing_modes": ["public_readonly", "local_committed", "local_uncommitted"],
    "manifest_path": "docs-viewer/config/scopes/docs_scope_manifest.json"
  }
}
```

Apply flags are authoritative.
Create apply is advertised only after the allowlisted write implementation is available.
Delete apply is advertised only after the manifest-backed deletion implementation is available.
The UI should avoid showing save/delete apply controls before the server advertises the matching capability.

Each scope capability record also includes lifecycle state:

```json
{
  "scope_lifecycle": {
    "manifest_recorded": true,
    "owner": "system",
    "created_by_tool": false,
    "delete_eligible": false
  }
}
```

Delete eligibility is server-derived.
The client should not infer delete eligibility from scope ids, routes, or file locations.

## Create Preview Endpoint

Endpoint:

- `POST /docs/scopes/create-preview`

Required payload fields:

- `scope_id`
- `title`
- `source_root`
- `default_doc_id`
- `publishing_mode`

Conditional and optional payload fields:

- `public_route_path`: required for `public_readonly`
- `build_inline_search`: boolean, defaults true
- `write_generated_outputs`: boolean, defaults true

Validation rules currently implemented:

- `scope_id` must use lowercase letters, numbers, and single hyphen separators
- `scope_id` must not already exist in `docs-viewer/config/scopes/docs_scopes.json`
- `scope_id` must not already exist in the scope manifest
- `source_root` must be the single repo-relative `docs-viewer/source/<scope>` directory
- `default_doc_id` must use lowercase letters, numbers, and hyphens
- `publishing_mode` must be `public_readonly`, `local_committed`, or `local_uncommitted`
- `public_route_path` must use lowercase route segments with hyphens
- committed manage-mode generated docs output must not be under `assets/data/docs/scopes/`
- committed manage-mode generated search output must not be under `assets/data/search/`
- planned created paths must not already exist

Preview response fields:

- `ok`
- `schema_version`
- `action`
- `operation`
- `scope_id`
- `title`
- `publishing_mode`
- `build_inline_search`
- `write_generated_outputs`
- `planned_scope_config`
- `storage_contract`
- `created_files`
- `changed_files`
- `build_commands`
- `urls`
- `warnings`
- `summary_text`
- `dry_run`

The preview response uses file records with `kind`, `path`, `action`, and `exists`.
It reports planned generated docs/search outputs only when generated output writes are requested.
It reports a public URL only for public read-only scopes.
The `storage_contract` block is displayed before save so the operator can see whether generated output is public static asset data or manage-mode runtime data served by the local Docs Viewer service.

Expected preview storage paths:

- `public_readonly`: `assets/data/docs/scopes/<scope>/` and `assets/data/search/<scope>/index.json`
- `local_committed`: `docs-viewer/generated/docs/<scope>/` and `docs-viewer/generated/search/<scope>/index.json`
- `local_uncommitted`: the same non-public generated path shape as `local_committed`, but the resulting local worktree changes should not be committed

The planned source-scope config also stores browser-facing `scope_type` and `meta` values:

- `public_readonly` -> `public`
- `local_committed` -> `local`
- `local_uncommitted` -> `local_uncommitted`

The Docs Viewer scope dropdown maps these types through `docs_viewer.scope_type_badges` for emoji and shows the scope record `meta` beside the scope id.

## Create Apply Endpoint

Endpoint:

- `POST /docs/scopes/create-apply`

Payload fields:

- all create-preview fields
- `confirm: true`

Apply behavior:

- requires explicit confirmation
- re-runs create-preview validation before any write
- creates the source root and default welcome Markdown document
- appends the scope config entry to `docs-viewer/config/scopes/docs_scopes.json`
- creates a public read-only route page only for `public_readonly`
- writes a user-created, tool-created manifest record
- runs the docs build and, when requested, the docs search build after the config and source files are written

Apply response fields:

- `ok`
- `schema_version`
- `action`
- `operation`
- `scope_id`
- `title`
- `publishing_mode`
- `created_files`
- `changed_files`
- `deleted_files`
- `missing_files`
- `build_commands`
- `urls`
- `rebuild`
- `summary_text`
- `dry_run`

Dry-run server mode validates the apply request and returns the apply response shape without writing files or running rebuild commands.

## Delete Preview Endpoint

Endpoint:

- `POST /docs/scopes/delete-preview`

Payload fields:

- `scope_id`; `scope` is accepted as an alias

Delete preview is manifest-driven.
If the scope has no manifest record, the response is allowed false with a blocker.
If the manifest record is system-owned or was not created by this lifecycle tool, the response is allowed false with a blocker.

Eligible delete response fields:

- `ok`
- `schema_version`
- `action`
- `operation`
- `scope_id`
- `allowed`
- `blockers`
- `delete_files`
- `missing_files`
- `changed_files`
- `build_commands`
- `summary_text`
- `dry_run`

Missing manifest-listed files should be reported in `missing_files`.
They do not block deletion of files that still exist.

## Delete Apply Endpoint

Endpoint:

- `POST /docs/scopes/delete-apply`

Payload fields:

- `scope_id`; `scope` is accepted as an alias
- `confirm: true`

Apply behavior:

- requires explicit confirmation
- re-runs delete-preview validation before any write
- blocks system-owned scopes and scopes not created by the lifecycle tool
- deletes existing manifest-owned scope paths, excluding scope config and manifest files
- reports missing manifest-owned paths without blocking the delete
- removes the scope entry from `docs-viewer/config/scopes/docs_scopes.json`
- removes the scope record from `docs-viewer/config/scopes/docs_scope_manifest.json`
- refreshes docs viewer generated outputs for the remaining configured scopes

Apply response fields:

- `ok`
- `schema_version`
- `action`
- `operation`
- `scope_id`
- `created_files`
- `changed_files`
- `deleted_files`
- `missing_files`
- `build_commands`
- `urls`
- `rebuild`
- `summary_text`
- `dry_run`

Dry-run server mode validates the delete apply request and returns the apply response shape without deleting files, changing config/manifest state, or running rebuild commands.

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

Create preview reports this planned write set without writing files.
Create apply writes the allowlisted source-root, route-file, config, generated-output, and manifest changes after confirmation.
Delete apply removes manifest-owned scope files, updates config and manifest state, and refreshes generated docs output after confirmation.

## Management UI Flow

The management shell exposes scope lifecycle commands only when the local Docs Viewer service advertises the matching lifecycle capability.

`New scope` opens a dedicated modal flow that:

- collects scope id, title, source root, default doc id, publishing mode, generated-output choice, and inline-search choice
- shows the public route path field only for `public_readonly`
- previews the server-planned write set before enabling the save step
- sends `confirm: true` only from the final save action
- reports created files, changed files, build commands, and resulting URLs from the server response

`Delete scope` is a selected-target flow.
The current Docs Viewer scope is only the management shell context and is not the implicit delete target.
The UI asks the operator to choose from server-advertised scopes whose lifecycle capability record has `delete_eligible: true`.
After target selection, the flow:

- previews the manifest-backed delete plan
- shows deleted files, missing files, changed files, and build commands before confirmation
- sends `confirm: true` only from the final delete action
- reports the server apply result after deletion

Implementation ownership:

- `docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js` owns the modal body rendering, field state, preview summaries, selected delete target, and apply result summaries
- `docs-viewer/runtime/js/docs-viewer-management.js` owns Actions menu wiring, capability-gated command visibility, busy/status state, and management capability refresh after apply
- `docs-viewer/runtime/js/docs-viewer-management-client.js` owns the HTTP wrappers for create/delete preview and apply endpoints
- `docs-viewer/runtime/js/docs-viewer-management-modals.js` provides the reusable modal shell; the lifecycle flow does not define a separate modal framework

## Safety Rules

- Scope creation is a local write action and must stay behind the loopback management server.
- Public routes must remain read-only even if `mode=manage` or `scope=<other-scope>` appears in the URL.
- The write server should validate scope ids and route paths before writing.
- The write server should refuse paths outside the configured repo allowlist.
- Manage-mode scopes must keep generated docs/search payloads out of `assets/data/docs/scopes/` and `assets/data/search/`; config loading, lifecycle preview/apply, and Ruby builders fail closed if a manage-mode scope points there.
- Public read-only scopes are the only scopes that should use those public generated asset roots.
- Local-only uncommitted scopes should be easy to identify in the response and cleanup guidance.
- Generated data should be rebuilt after scope config changes so `docs-viewer/config/defaults/docs-viewer-config.json` and `docs-viewer/config/defaults/docs-viewer-public-config.json` stay current.

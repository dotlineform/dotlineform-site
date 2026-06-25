---
doc_id: docs-viewer-new-scopes-builder
title: New Scopes Builder
added_date: 2026-05-15
last_updated: 2026-06-24
parent_id: docs-viewer
viewable: true
---
# New Scopes Builder

The New Scopes Builder is the local-management workflow for creating and deleting Docs Viewer scopes from `/docs/`.

It should:

- create the same files a developer would otherwise create by hand
- keep all write behavior behind the loopback Docs Viewer service
- preserve existing public read-only routes
- show the planned write or delete set before any write
- record ownership in a scope manifest so deletion can fail closed

Current policy:

- `New scope` defaults to an external local scope
- public read-only scope creation is available through the local management lifecycle action
- local tracked scope creation is available through the same lifecycle action
- external local scope creation replaces the former local untracked mode
- user-created public scope deletion is available when the scope manifest records owned files
- public route shells are rendered from [Docs Viewer Public Route Shell Template](/docs/?scope=studio&doc=docs-viewer-public-route-shell-template)

## Scope Creation Boundary

A Docs Viewer scope is made from four parts:

- source root, such as `docs-viewer/source/research/`
- scope config entry in `docs-viewer/config/scopes/docs_scopes.json`
- generated viewer/search outputs, whose roots depend on publishing mode

Existing public read-only scopes use working generated outputs under:

- `docs-viewer/generated/docs/<scope>/`
- `docs-viewer/generated/search/<scope>/index.json`

and published snapshot outputs under:

- `site/assets/data/docs/scopes/<scope>/`
- `site/assets/data/search/<scope>/index.json`

Local tracked scopes use generated outputs under:

- `docs-viewer/generated/docs/<scope>/`
- `docs-viewer/generated/search/<scope>/index.json`

External local scopes store source and working generated outputs outside the repo under:

- `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/source/<scope>/`
- `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/docs/<scope>/`
- `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/search/<scope>/index.json`

The checked-in scope config stores `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer` marker paths, not user-specific absolute paths.
Create preview and apply fail before writing when `DOTLINEFORM_PROJECTS_BASE_DIR` is unset or when `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/` does not already exist as a readable and writable directory.

Local scopes must not write generated docs/search runtime payloads under `site/assets/data/docs/scopes/` or `site/assets/data/search/`.
Those `site/assets/` roots are public static-site payload roots and are reserved for scopes that are explicitly public read-only.

The localhost Docs Viewer service may create or update those files.
The public browser runtime must not.

Scope creation should run only through:

- `/docs/`
- the loopback Docs Viewer service
- explicit write allowlists in the server
- normal rebuild commands after the write

Public read-only routes should not expose create-scope controls, management endpoints, Docs Import, or local write capabilities.

## Route Adapter Choices

Public read-only route shells are checked-in static HTML under `site/`.
New public scopes must not create Markdown route files or generated Python source.
The public-scope lifecycle path renders `docs-viewer/templates/public-route/index.html` into `site/<route>/index.html` during the local write action and updates data/config route records.

Use `docs-viewer/shell/docs-viewer-manage.html` through the standalone Docs Viewer service for the local management shell.
In this repo, that route is `/docs/`.
Public builds use read-only route shells, while the standalone Docs Viewer service serves `/docs/` management locally.

The management shell can switch scopes with the `scope` query parameter.
Public read-only routes ignore and normalize away `scope` and `mode` so they cannot become management routes by query string.

## Publishing Modes

### Public Read-Only Scope

Use this option when the scope should publish a public read-only route under `site/`.

Public scope creation updates source/config records, public route metadata, published public payload roots, and a tracked static route shell.
It renders `site/<route>/index.html` from `docs-viewer/templates/public-route/index.html`.
It does not write Markdown route stubs or Python source.

Existing public scopes such as Library and Analysis remain manageable through `/docs/?scope=<scope>`.
Their `/docs/` Actions menu `Publish` command copies reviewed working JSON from `docs-viewer/generated/` into the tracked `site/assets/data/` files that public routes read.

### Local Tracked Scope

Use this option when the scope should be available to local developers or Codex sessions, but not published as a public route.

Create and commit:

- source root and Markdown files
- `docs-viewer/config/scopes/docs_scopes.json` entry
- generated docs tree, recently-added, by-id payloads, and search JSON under `docs-viewer/generated/docs/<scope>/` and `docs-viewer/generated/search/<scope>/index.json` if local workflows expect checked-in generated data

Do not create a public read-only route page.
The scope remains available through `/docs/?scope=<scope>` when the local server is running.
The generated JSON is tracked runtime data, but it is not a public static asset because it lives under the Docs Viewer-owned `docs-viewer/` boundary rather than under `site/assets/`.

This is useful for private planning notes, local drafts, or internal review material that should move with the repo but not have a public URL.

### External Local Scope

Use this option when the scope should be locally manageable but its source Markdown and generated JSON should not live in the repo.

Register in the repo:

- `docs-viewer/config/scopes/docs_scopes.json` entry
- `docs-viewer/config/scopes/docs_scope_manifest.json` ownership record

Create under `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/`:

- source root and default Markdown file
- generated docs tree, recently-added, by-id payloads, and search JSON when generated output writes are requested

Do not create a public read-only route page or public publish outputs.
The scope remains available through `/docs/?scope=<scope>` when the local Docs Viewer service is running.
Browser reads use management generated-data endpoints, not static URLs derived from filesystem paths.

This mode is useful for private planning notes, local drafts, or internal review material that should be registered in the central Docs Viewer config without storing source or generated payloads in the repo.

## Implementation State

The scope lifecycle workflow has server-side preview/apply endpoints and a management UI entry point:

- `docs-viewer/config/scopes/docs_scope_manifest.json` records existing scopes as system-owned
- `docs-viewer/services/docs_scope_manifest.py` owns manifest loading, backfill, validation, and preview planning
- `GET /capabilities` advertises scope lifecycle preview and apply support
- `POST /docs/scopes/create-preview` reports a validated create write set
- `POST /docs/scopes/create-apply` creates allowlisted scope files after explicit confirmation
- `POST /docs/scopes/delete-preview` reports a manifest-backed delete plan and blocks system scopes
- `POST /docs/scopes/delete-apply` deletes eligible user-created scopes after explicit confirmation
- the `/docs/` Actions menu exposes capability-gated `New scope` and `Delete scope` commands
- `docs-viewer/runtime/js/management/docs-viewer-scope-lifecycle.js` owns the create/delete modal flows
- `docs-viewer/runtime/js/management/docs-viewer-management.js` remains the management command coordinator
- `docs-viewer/runtime/js/management/docs-viewer-management-client.js` owns the scope lifecycle endpoint wrappers

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
- `scope_type`: `public` or `local`
- `owner`: `system` or a future user/tool owner value
- `user_created`: whether the scope was created by a local operator
- `created_by_tool`: whether this lifecycle tool created the scope
- `tool_id`: creating tool id when applicable
- `repo_status_at_creation`: `tracked`, `external`, or `unknown`
- `created_at`: creation timestamp when known
- `updated_at`: manifest-record timestamp
- `files`: repo-relative or external file records owned by the scope
- `metadata`: audit metadata such as `backfilled`, `viewer_base_url`, and `default_doc_id`

File record fields:

- `kind`: file role, such as `source_root`, `scope_config`, `scope_manifest`, `default_source_doc`, `route_file`, `generated_docs_root`, `generated_docs_index_tree`, `generated_docs_recently_added`, `generated_docs_payload_root`, `generated_search_index`, `published_docs_root`, or `published_search_index`
- `path`: repo-relative path or resolved external path label
- `location`: `repo` or `external`
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
    "publishing_modes": ["public_readonly", "local_external", "local_committed"],
    "manifest_path": "docs-viewer/config/scopes/docs_scope_manifest.json"
  }
}
```

- Apply flags are authoritative.
- Create apply is advertised only after the allowlisted write implementation is available.
- Delete apply is advertised only after the manifest-backed deletion implementation is available.
- The UI should avoid showing save/delete apply controls before the server advertises the matching capability.

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
- `default_doc_id`
- `publishing_mode`

Conditional and optional payload fields:

- `source_root`: required for `public_readonly` and `local_committed`; ignored for `local_external`
- `public_route_path`: required for `public_readonly`; ignored for local modes

Validation rules currently implemented:

- `scope_id` must use lowercase letters, numbers, and single hyphen separators
- `scope_id` must not already exist in `docs-viewer/config/scopes/docs_scopes.json`
- `scope_id` must not already exist in the scope manifest
- repo-backed `source_root` must be the single repo-relative `docs-viewer/source/<scope>` directory
- `default_doc_id` must use lowercase letters, numbers, and hyphens
- `publishing_mode` must be `public_readonly`, `local_external`, or `local_committed`
- `public_readonly` requires a valid `public_route_path`
- `local_external` requires `DOTLINEFORM_PROJECTS_BASE_DIR` and an existing readable/writable `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/` directory
- local tracked generated docs output must not be under `site/assets/data/docs/scopes/`
- local tracked generated search output must not be under `site/assets/data/search/`
- planned created paths must not already exist

Preview response fields:

- `ok`
- `schema_version`
- `action`
- `operation`
- `scope_id`
- `title`
- `publishing_mode`
- `planned_scope_config`
- `storage_contract`
- `created_files`
- `changed_files`
- `publish_files`
- `build_commands`
- `urls`
- `warnings`
- `summary_text`
- `dry_run`

The preview response uses file records with `kind`, `path`, `action`, and `exists`.
It always reports planned generated docs/search outputs.
It reports public route files only for `public_readonly`.
The `storage_contract` block is displayed before save so the operator can see whether generated output is public static asset data or local runtime data served by the local Docs Viewer service.

Expected preview storage paths:

- `local_committed`: `docs-viewer/generated/docs/<scope>/` and `docs-viewer/generated/search/<scope>/index.json`
- `local_external`: `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/docs/<scope>/` and `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/search/<scope>/index.json`
- `public_readonly`: working generated output under `docs-viewer/generated/`, plus public publish snapshots under `site/assets/data/`

The planned source-scope config also stores browser-facing `scope_type` and `meta` values:

- `local_committed` -> `local`
- `local_external` -> `local_external`
- `public_readonly` -> `public`

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
- creates public route files and route-registry records only for `public_readonly`
- creates external local source and generated output under `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/` for `local_external`
- writes local generated docs outputs, including `index-tree.json`, `recently-added.json`, and selected by-id payloads
- writes a user-created, tool-created manifest record
- runs the docs build and docs search build after the config and source files are written

Apply response fields:

- `ok`
- `schema_version`
- `action`
- `operation`
- `scope_id`
- `title`
- `publishing_mode`
- `storage_contract`
- `created_files`
- `publish_files`
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
- source root for repo-backed modes
- default doc id
- publishing mode

For `local_external`, the modal does not collect a source root or external data root.
The server derives the external source and generated-output paths from `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer`.
For local modes, the server skips public route creation.

The server response should list:

- files created
- files changed
- build commands run or suggested
- resulting management URL

Create preview reports this planned write set without writing files.
Create apply writes the allowlisted source-root, config, generated-output, route, publish, and manifest changes after confirmation.
Delete apply removes manifest-owned scope files, updates config and manifest state, and refreshes generated docs output after confirmation.

Scope lifecycle manifests record user-created route and generated-output paths such as scope-specific `index-tree.json`, `recently-added.json`, by-id payload directories, and search payloads.
They must not record shared public/manage entrypoints, route registries, CSS, UI text, or runtime modules as delete-owned scope files.

## Management UI Flow

The management shell exposes scope lifecycle commands only when the local Docs Viewer service advertises the matching lifecycle capability.

`New scope` opens a dedicated modal flow that:

- collects scope id, title, source root for repo-backed modes, default doc id, and publishing mode
- hides the source root field for `local_external`
- does not collect an external data root path
- defaults publishing mode to `local_external`
- includes `public_readonly`, `local_external`, and `local_committed` according to the server-advertised publishing modes
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

- `docs-viewer/runtime/js/management/docs-viewer-scope-lifecycle.js` owns the modal body rendering, field state, preview summaries, selected delete target, and apply result summaries
- `docs-viewer/runtime/js/management/docs-viewer-management.js` owns Actions menu wiring, capability-gated command visibility, busy/status state, and management capability refresh after apply
- `docs-viewer/runtime/js/management/docs-viewer-management-client.js` owns the HTTP wrappers for create/delete preview and apply endpoints
- `docs-viewer/runtime/js/management/docs-viewer-management-modals.js` provides the reusable modal shell; the lifecycle flow does not define a separate modal framework

## Safety Rules

- Scope creation is a local write action and must stay behind the loopback management server.
- Public routes must remain read-only even if a management query or `scope=<other-scope>` appears in the URL.
- The write server should validate scope ids and route paths before writing.
- The write server should refuse repo paths outside the configured repo allowlist.
- External local writes must stay under the resolved `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/` root.
- The checked-in scope config must store marker-rooted external local paths instead of user-specific absolute paths.
- Local scopes must keep generated docs/search payloads out of `site/assets/data/docs/scopes/` and `site/assets/data/search/`; config loading and lifecycle preview/apply fail closed if a local scope points there.
- Public read-only scopes are the only scopes that should use those public generated asset roots.
- Public read-only scope creation and deletion use the route shell template and manifest-owned file records; deletion must not remove shared runtime, shared CSS, UI text, route registry files themselves, or unrelated route shells.
- Delete Scope must block any scope referenced as `default_scope_id` by a management route, even when that scope is user-created.
- External local scopes should be easy to identify in responses and cleanup guidance.
- Generated data should be rebuilt after scope config changes so `docs-viewer/config/defaults/docs-viewer-config.json` and `docs-viewer/config/defaults/docs-viewer-public-config.json` stay current.

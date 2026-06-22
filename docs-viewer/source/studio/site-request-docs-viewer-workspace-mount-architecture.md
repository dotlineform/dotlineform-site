---
doc_id: site-request-docs-viewer-workspace-mount-architecture
title: Docs Viewer External Scope Data Roots Request
added_date: 2026-05-25
last_updated: 2026-06-22
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer External Scope Data Roots Request

Status:

- implemented

## Summary

Design external scope data roots so Docs Viewer can read and write a scope's source Markdown and generated JSON outside the current repo.

There is no current requirement for the scope definition itself to be private or external.
Local scopes can still be registered in the central Docs Viewer scope config under `docs-viewer/config/scopes/docs_scopes.json`.
The narrower requirement is only that selected local scopes can keep source Markdown, generated docs payloads, and generated search payloads outside the repo.

This request replaces the earlier broader workspace-mount framing.
A workspace abstraction may still become useful later, but it is not required to satisfy the current storage requirement.

## Goal

Make Docs Viewer able to resolve configured source and generated-output paths that are not rooted in the site repo.

The desired end state is:

- Docs Viewer application code and local scope data can live in different places
- central scope registration remains in the repo-owned Docs Viewer config
- repo-backed scopes keep the current path behavior
- selected local scopes can place source Markdown and working generated JSON under `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer`
- the New scope modal's former `local untracked` option is replaced by this external local scope mode
- browser reads for non-public generated data go through a Docs Viewer service URL contract, not static repo-relative files

## Scope Data Root Model

A configured local scope should continue to define its normal scope metadata in `docs-viewer/config/scopes/docs_scopes.json`.
For external local data, the scope config should be able to identify:

- `external_data_root`: `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer`
- source root
- generated docs root
- generated search root
- write policy, such as public read-only, local tracked, or external local data

For the current repo-backed scopes, these paths continue to map to existing repo-relative paths.
For an external local scope, the paths map to:

- source root: `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/source/<scope>/`
- generated docs root: `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/docs/<scope>/`
- generated search root: `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/search/<scope>/index.json`

The scope config and scope manifest should remain repo-owned unless a separate future requirement says scope registration itself must be private, portable, or user-specific.
The checked-in scope config stores the `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer` marker, not a user-specific absolute filesystem path.
The local process environment resolves that marker when builders, generated reads, lifecycle create/delete, and management actions access source or generated files.

## New Scope UI Contract

The Docs Viewer `New scope` action previously offered three scope creation modes:

- public
- local tracked
- local untracked

This request replaces `local untracked` with an external local scope mode.
The modal remains the UI surface for creating the scope record, but it does not collect a filesystem path.
External local scopes always use `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer`.
Create preview and apply fail before writing if `DOTLINEFORM_PROJECTS_BASE_DIR` is unset or if its `docs-viewer/` child does not already exist as a readable and writable directory.

The external local mode should make clear that:

- the scope registration is still written to the central repo-owned Docs Viewer scope config
- the scope manifest record remains repo-owned
- `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer` is where the scope's source Markdown and working generated docs/search payloads live
- public publishing paths are not configured for this mode
- delete previews and cleanup actions are constrained to the resolved external scope roots

## Why This Is More Than A Config Edit

A true non-repo local scope is still more than changing three strings in the scope config.

- The current Docs Viewer scope model assumes repo-relative source and generated paths.
- browser runtime fetches generated payload URLs from the current web origin; it cannot fetch arbitrary local filesystem paths
- local management, import, rebuild, watcher, manifest, and deletion helpers report or validate paths as repo-relative paths

That means `in repo, untracked` and `not in repo` are different implementation tiers.
`In repo, untracked` can mostly use the existing path model with better ignore rules and preview warnings.
It remains visible to repo tooling and can still be accidentally staged if ignore coverage is incomplete.
`Not in repo` needs path resolution and service-backed generated-data reads.

The implementation should avoid making the current repo-backed setup a legacy special case, but it does not need to introduce externally stored scope config or a full mounted-workspace model.

## Required Architecture Work

Required implementation work includes:

- safe fixed external-root configuration for source, generated docs, and generated search paths
- clear validation that distinguishes repo-relative paths from approved external local paths
- builder and search commands that can write to external roots
- Docs Viewer service endpoints that can serve non-public generated docs and search payloads from external roots
- browser config or runtime routing that uses those service endpoints for external local scopes instead of static repo-relative URLs
- import, rebuild, watcher, capability, delete, and cleanup paths that understand external source and generated data roots
- diagnostic reporting that presents external paths safely without implying they are repo-relative

Not required for the current request:

- storing `docs-viewer/config/scopes/docs_scopes.json` outside the repo
- storing the scope manifest outside the repo
- introducing a user workspace registry
- moving public published payloads outside the public static-site roots
- changing committed repo-backed scopes beyond the resolver support needed for shared path handling

## Tasks

1. Define the external path contract
   - represent external local paths with the `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer` marker
   - define which scope types may use external source and generated paths
   - define the replacement behavior for the former `local untracked` New scope mode
   - document that `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer` must already exist before preview/apply

2. Add shared path resolution
   - replace direct `repo_root / config.source`, `repo_root / config.output`, and `repo_root / config.search_output` call sites with a shared resolver
   - keep existing repo-relative scopes resolving to the same paths they use today
   - return enough path metadata for reports to distinguish repo-relative paths from external paths

3. Update scope config loading and validation
   - allow marker-rooted external paths for `source`, `output`, and `search_output`
   - keep `publish_output`, `publish_search_output`, media repo-asset paths, scope config, and manifest paths repo-relative
   - fail closed when an external path is missing, unsafe, or configured on an unsupported scope type

4. Update docs and search builders
   - make `build_docs.py` read source Markdown from resolved source roots
   - make `build_docs.py` write generated docs payloads to resolved output roots
   - make `build_search.py` read generated docs and write search JSON through resolved paths
   - avoid deriving browser URLs directly from external filesystem paths

5. Add service-backed generated-data reads
   - extend the Docs Viewer local service so index tree, recently added, by-id payloads, references, and search index can be served from resolved external roots
   - keep public read-only routes using published static payloads
   - ensure service responses preserve existing payload schemas and cache behavior where practical

6. Route browser runtime fetches for external local scopes
   - update generated browser config or runtime routing so external local scopes fetch generated data from Docs Viewer service endpoints
   - keep repo-backed local scopes working with the current local generated-data behavior
   - show clear load errors when the local service cannot access an external root

7. Update management lifecycle helpers
   - update source edit, import, rebuild, watcher, capabilities, delete, and cleanup paths to use resolved source and generated roots
   - keep scope config and manifest create/delete operations repo-owned
   - ensure delete previews do not remove files outside the configured external scope roots

8. Update New scope modal
   - replace the former `local untracked` option with the external local scope mode
   - do not show an external data root input for that mode
   - validate the fixed root before preview/apply and show clear errors for missing, unreadable, or unwritable roots

9. Update reports and UI status copy
   - label external roots clearly in capability and source-config reports
   - avoid presenting external paths as repo-relative paths
   - add warnings for external roots that are unreadable, unwritable, or outside approved locations

10. Add focused verification
   - add unit coverage for path resolution and validation
   - add builder tests for external source and generated output paths
   - add service/read tests for external generated docs and search payloads
   - add one management smoke path that opens an external local scope through `/docs/?scope=<scope>`
   - add focused UI coverage that the New scope external local payload does not submit an external root path

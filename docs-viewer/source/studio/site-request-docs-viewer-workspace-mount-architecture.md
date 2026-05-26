---
doc_id: site-request-docs-viewer-workspace-mount-architecture
title: Docs Viewer Workspace Mount Architecture Request
added_date: 2026-05-25
last_updated: 2026-05-25
ui_status: draft
parent_id: change-requests
sort_order: 11000
viewable: true
---
# Docs Viewer Workspace Mount Architecture Request

Status:

- requested

## Summary

Design a workspace mount architecture so Docs Viewer can read and write documentation data from either the current repo or an external application data workspace.

This is the larger architecture behind true local scopes.
If a user does not want generated JSON committed, they almost certainly do not want the source Markdown committed either.
True local scopes should therefore keep source, config, manifest, generated docs payloads, and generated search payloads outside the repo or under an ignored application-local data root.

## Goal

Make Docs Viewer able to mount a workspace instead of assuming every scope is rooted in the site repo.

The desired end state is:

- Docs Viewer application code and Docs Viewer data can live in different places
- the current repo-backed setup becomes one mounted workspace
- true local scopes can live outside the repo
- repo-backed workspaces and external workspaces use the same scope-resolution abstraction
- browser reads for non-public data go through a Docs Viewer service URL contract, not static repo-relative files
- this work can carry forward if Docs Viewer becomes a standalone application

## Workspace Model

A mounted workspace should define:

- workspace id
- workspace root
- source root
- generated docs root
- generated search root
- config root
- manifest root
- read mode, such as static assets or service-backed reads
- write policy, such as repo tracked, ignored local, or external application data

For the current repo-backed public workspace, the adapter can map to existing paths:

- workspace root: repo root
- source root: `docs-viewer/source/<scope>/`
- generated docs root: `assets/data/docs/scopes/<scope>/`
- generated search root: `assets/data/search/<scope>/index.json`
- config/manifest: `docs-viewer/config/scopes/...`
- read mode: static assets for public routes, service-backed for manage mode

For an external true-local workspace, the adapter could map to:

- workspace root: configured user/app data directory
- source root: `<workspace>/source/<scope>/`
- generated docs root: `<workspace>/generated/docs/<scope>/`
- generated search root: `<workspace>/generated/search/<scope>/index.json`
- config/manifest: `<workspace>/config/...`
- read mode: service-backed

## Why This Is More Than Config

A true non-repo local scope is more than a scope-config path change.

The current Docs Viewer scope model assumes repo-relative source and generated paths:

- `docs-viewer/services/docs_scope_config.py` rejects absolute paths and parent traversal for `source`, `output`, and import-media paths.
- source Markdown is loaded as `repo_root / config.source`
- generated docs payloads are loaded as `repo_root / config.output`
- generated search reads still assume `assets/data/search/<scope>/index.json`
- the docs builder derives browser `content_url` values from a repo-relative output path such as `/assets/data/docs/scopes/<scope>/by-id/<doc>.json`
- browser runtime fetches generated payload URLs from the current web origin; it cannot fetch arbitrary local filesystem paths
- local management, import, rebuild, watcher, manifest, and deletion helpers report or validate paths as repo-relative paths

That means `in repo, untracked` and `not in repo` are different implementation tiers.

`In repo, untracked` can mostly use the existing path model with better ignore rules and preview warnings.
It remains visible to repo tooling and can still be accidentally staged if ignore coverage is incomplete.

`Not in repo` needs an application data layer.

## Required Architecture Work

Required implementation work includes:

- safe external-root configuration for source, generated docs, generated search, local config, and local manifest data
- a local overlay registry so true local scopes do not modify tracked `docs-viewer/config/scopes/docs_scopes.json`
- service-backed reads for generated docs/search payloads outside public static `assets/`
- builder and search commands that can write to external roots without producing public static URLs
- a browser/runtime URL contract for local generated payloads served by the Docs Viewer service
- import, rebuild, watcher, capability, delete, and cleanup paths that understand external application data roots
- tests that prove true local scope files do not appear in normal repo staging workflows

This work should be treated as a product/application-data change, not as a small New Scope form tweak.

## Relationship To Committed Manage-Mode Storage

[Committed Manage-Mode Scope Storage Request](/docs/?scope=studio&mode=manage&doc=site-request-committed-manage-mode-scope-storage) is the near-term request for Studio and repo-tracked manage-mode scopes.

That request fixes the immediate `assets/` publication-boundary problem.
This request defines the broader workspace abstraction that would eventually subsume repo-backed and non-repo-backed scope storage under one resolver.

The two efforts should stay aligned:

- committed manage-mode storage should avoid hardcoding paths in ways that block workspace mounts later
- workspace mounts should treat the current repo-backed setup as one adapter, not as legacy special-case behavior

## Implementation Tasks

### Task 1. Define Workspace Schema

Status:

- not started

Define the workspace fields, allowed root types, read modes, and write policies.

### Task 2. Build Scope Resolution Through Workspaces

Status:

- not started

Replace direct `repo_root / config.source` and `repo_root / config.output` assumptions with a workspace-aware scope resolver.

### Task 3. Add Service-Backed Payload Reads

Status:

- not started

Define local service URLs for generated docs payloads, generated search payloads, references, and doc content in non-public workspaces.

### Task 4. Support External Source And Generated Roots

Status:

- not started

Update docs build, search build, import, rebuild, watcher, capability, and delete flows to operate against workspace-resolved paths.

### Task 5. Add True Local Scope Lifecycle

Status:

- not started

Update New Scope lifecycle behavior so true local scopes write only to external or ignored application-local data roots.

### Task 6. Verify Repo And External Workspace Parity

Status:

- not started

Add tests that mount:

- the current repo-backed workspace
- an external workspace outside the repo
- a manage-mode-only workspace with service-backed reads

## Acceptance Criteria

- Docs Viewer can mount at least one repo-backed workspace and one external workspace.
- Scope source/config/manifest/generated paths resolve through a workspace abstraction.
- True local scope files do not appear in normal repo staging workflows.
- Non-public workspace payloads are read through the Docs Viewer service, not public static `assets/`.
- The current repo-backed public Docs Viewer scopes continue to work.
- The architecture can support a future standalone Docs Viewer application without a second path model.

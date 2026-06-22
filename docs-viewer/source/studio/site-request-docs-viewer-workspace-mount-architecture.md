---
doc_id: site-request-docs-viewer-workspace-mount-architecture
title: Docs Viewer Workspace Mount Architecture Request
added_date: 2026-05-25
last_updated: 2026-06-22
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Workspace Mount Architecture Request

Status:

- requested

## Summary

Design a workspace mount architecture so Docs Viewer can read and write documentation data from either the current repo or an external application data workspace.

If a user does not want generated JSON committed, they almost certainly do not want the source Markdown committed either. True local scopes should therefore keep source, generated docs payloads, and generated search payloads outside the repo.

This request defines the broader workspace abstraction that would subsume repo-backed and non-repo-backed scope storage under one resolver.

## Goal

Make Docs Viewer able to mount a workspace instead of assuming every scope is rooted in the site repo.

The desired end state is:

- Docs Viewer application code and Docs Viewer data can live in different places
- the current repo-backed setup becomes one mounted workspace
- true local scopes can live outside the repo
- repo-backed workspaces and external workspaces use the same scope-resolution abstraction
- browser reads for non-public data go through a Docs Viewer service URL contract, not static repo-relative files

## Workspace Model

A mounted workspace should define:

- workspace id
- workspace root
- source root
- generated docs root
- generated search root
- write policy, such as repo tracked, ignored local, or external application data

For the current repo-backed workspace, the adapter should map to existing paths. For an external true-local workspace, the adapter could map to:

- workspace root: configured user/app data directory
- source root: `<workspace>/source/<scope>/`
- generated docs root: `<workspace>/generated/docs/<scope>/`
- generated search root: `<workspace>/generated/search/<scope>/index.json`
- config/manifest: `<workspace>/config/...`

## Why This Is More Than Config

A true non-repo local scope is more than a scope-config path change.

- The current Docs Viewer scope model assumes repo-relative source and generated paths.
- browser runtime fetches generated payload URLs from the current web origin; it cannot fetch arbitrary local filesystem paths
- local management, import, rebuild, watcher, manifest, and deletion helpers report or validate paths as repo-relative paths

That means `in repo, untracked` and `not in repo` are different implementation tiers. `In repo, untracked` can mostly use the existing path model with better ignore rules and preview warnings. It remains visible to repo tooling and can still be accidentally staged if ignore coverage is incomplete. `Not in repo` needs an application data layer.

Workspace mounts should treat the current repo-backed setup as one adapter, not as legacy special-case behavior.

## Required Architecture Work

Required implementation work includes:

- safe external-root configuration for source, generated docs, generated search, local config, and local manifest data
- builder and search commands that can write to external roots
- import, rebuild, watcher, capability, delete, and cleanup paths that understand external application data roots
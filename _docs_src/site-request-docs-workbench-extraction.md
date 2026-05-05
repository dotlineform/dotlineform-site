---
doc_id: site-request-docs-workbench-extraction
title: Docs Workbench Extraction Request
added_date: "2026-05-05"
last_updated: "2026-05-05"
parent_id: change-requests
sort_order: 26
---
# Docs Workbench Extraction Request

Status:

- proposed

## Summary

Explore whether the Docs Viewer, generated docs/search pipeline, local docs-management server, and scope-aware export/import workflow should become a reusable Docs Workbench toolkit that other repositories or local installs can track from a master version.

The current repo should stay the first consumer while the reusable boundary is tested.
The goal of this request is to define the product boundary, update model, configuration contract, and open questions before any extraction work starts.

## Problem

The docs viewer and export/import workflow are becoming a useful local operating surface, not only a site feature.
They combine:

- a static docs reader with scope-aware generated payloads
- generated search indexes
- local read/write server capabilities
- export, staging, preview, and import flows
- UI primitives and composition patterns for command results

That combination could be useful in other repos, but the implementation is currently mixed with dotlineform-specific routes, config, styling, and Studio workflow assumptions.

Copying files into another repo would create an unmanaged fork.
Any reused install needs a way to track a master version, receive fixes, and keep local project-specific config separate from reusable core behavior.

## Goals

- Define the reusable boundary for a first Docs Workbench version.
- Identify which code and docs stay project-local.
- Choose a pragmatic master-version and install-tracking model.
- Define the configuration and lifecycle contracts needed by downstream installs.
- Preserve the current local/public split: local write workflows can use a loopback server, while public builds remain static.
- Keep dotlineform as a real downstream consumer so extraction decisions are tested against existing workflows.

## Non-Goals

- Do not extract or package the system as part of this request.
- Do not redesign the docs viewer UI unless the extraction boundary requires a small interface cleanup.
- Do not generalize Catalogue, Library, or Analytics domain logic beyond the common export/import workflow shell.
- Do not require every downstream repo to use Jekyll in the long term, although Jekyll can be the first supported adapter.
- Do not solve hosted multi-user editing. The write workflows remain local-first unless a later request changes that boundary.

## Candidate Reusable Components

- Docs Viewer shell include, runtime, and route adapter contract.
- Docs index and payload builders.
- Docs search builder and generated search data contract.
- Local docs-management server generated-data reads.
- Export/import workflow shell: scope config, staging folder discovery, preview generation, result summary, and reopenable command result behavior.
- Shared UI primitives and composition patterns needed by the workflow.
- Smoke checks for static docs, local server reads, and export/import result display.
- Reference docs for install, configuration, update, and lifecycle contracts.

## Candidate Project-Local Components

- Source content roots and scope definitions.
- Route placement and site layout integration.
- Visual theme overrides and image choices.
- Studio dashboard structure and domain navigation.
- Catalogue, Library, Analytics, and tag-registry-specific data semantics.
- Per-scope export/import configs and preview/apply implementations.
- Any project-specific write allowlists.

## Master Version Model

The first model should prefer traceable source control over early packaging.

Candidate approach:

- Create or designate an upstream Docs Workbench repo as the master source.
- Track releases with version tags, a change log, and migration notes.
- Install into downstream repos with Git subtree or Git submodule first.
- Keep downstream repos responsible for project-local config, routes, and theme adapters.
- Add package-manager distribution only after the file boundary and config contract have settled.

### Install Shape Options

Git subtree:

- Better for repos that want vendored files in-tree and simple deployment.
- Easier to patch locally, but local patches need discipline to upstream.
- Works well if the reusable surface is mostly static assets, scripts, and docs.

Git submodule:

- Clearer separation from project-local files.
- Easier to see the exact upstream revision.
- Adds operational friction for clone, update, and local editing.

Package distribution:

- Cleaner for mature runtime libraries and command-line tools.
- Probably premature until the split between assets, scripts, server code, and docs is stable.
- May require more than one package if the toolkit keeps JavaScript, Python, and Ruby pieces.

## Open Questions

- What is the smallest useful first extraction boundary?
- Should the master version be split by concern, or remain one toolkit repo until the contracts settle?
- Should Jekyll be the only v0 adapter, or should the route/build interfaces be framework-neutral from the start?
- Which language owns the command-line entry points if the toolkit contains JavaScript runtime assets, Ruby builders, and Python local server code?
- How should downstream config describe scopes, source roots, generated output paths, search output paths, and export/import staging folders?
- How should project-local write allowlists be declared and audited?
- What is the stable import lifecycle contract: staged file discovery, preview generation, preview result selection, apply action, backups, and result reporting?
- Which UI primitives and composition patterns belong in the toolkit, and which should stay in the consuming site's design system?
- How should the toolkit expose theme variables without imposing a visual identity?
- How should downstream installs receive migrations for generated data shape changes?
- How should upstream changes be tested against dotlineform and at least one minimal fixture repo?
- Should dotlineform be converted into a downstream consumer only after a separate prototype repo proves the boundary?
- What license and visibility model is appropriate if the upstream repo starts from project-specific code?

## Investigation Tasks

1. Inventory current files and classify them as reusable core, adapter, or dotlineform-local.
2. Define the v0 product boundary for Docs Workbench.
3. Draft a config schema covering docs scopes, generated payloads, search, local server capabilities, and export/import workflows.
4. Prototype a minimal downstream install using either subtree or submodule.
5. Define update and migration workflow, including how downstream repos record the tracked upstream version.
6. Define verification checks that run in upstream and downstream contexts.
7. Decide whether to create a separate implementation request for extraction.

## Acceptance Criteria

This request can move from proposed to ready when it has:

- a written extraction boundary
- a recommended install-tracking model
- a list of files or modules to extract, adapt, or keep local
- a candidate config schema
- a migration and update plan
- a risk assessment for dotlineform as the first downstream consumer
- a follow-up implementation request if extraction is approved

## Related Docs

- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Docs Build Incremental Request](/docs/?scope=studio&doc=site-request-docs-build-incremental)
- [Local Docs Data Server Reads Request](/docs/?scope=studio&doc=site-request-local-docs-data-server-reads)
- [Library Import Export V2](/docs/?scope=studio&doc=library-import-export-v2)
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)

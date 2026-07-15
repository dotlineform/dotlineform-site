---
doc_id: docs-viewer-portable-setup
title: Portability Snapshot
added_date: 2026-05-11
last_updated: 2026-07-14
ui_status: deferred
summary: Inactive record of how far Docs Viewer portability thinking reached; not a maintained setup or compatibility contract.
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Portability Snapshot

## Status

Portability is not active development. There is no packaged Docs Viewer product, supported copy manifest, external compatibility target, or commitment to complete one.

Do not update this document for routine Docs Viewer changes. If portability becomes an actual project, start from the current code and a named target environment rather than treating this snapshot as a checklist.

The previous detailed file manifest and setup procedures were removed because every focused runtime change made them look authoritative while making them less trustworthy.

## As Far As We Got

The investigation established that Docs Viewer is composed from separable concerns:

```text
canonical Markdown + scope config
              |
              v
       docs/search builders
              |
              v
    generated JSON + reader shell

optional local management
    = loopback service + management entrypoint + write workflows
```

A public read-only reader is the smaller potential portability boundary. Local management adds Python services, configuration mutation, imports, lifecycle operations, filesystem containment, external workspace conventions, rebuild follow-through, and local credentials.

The current implementation remains repo-integrated:

- shared runtime and CSS are delivered from `site/docs-viewer/`
- canonical route/scope config and builders live under `docs-viewer/`
- public routes consume copied generated snapshots under `site/assets/data/`
- local management is served by the standalone loopback Docs Viewer service
- Python dependencies and repo layout are assumed by several build and management features

Within this repository, use [Scope Lifecycle](/docs/?scope=studio&doc=docs-viewer-new-scopes-builder) to create another configured public, committed-local, or external-local scope. That is a supported in-repo capability, not evidence that the whole application is portable.

## What Would Need A New Decision

Before resuming portability, decide:

1. the actual destination: another repo, a reusable package, or a standalone application
2. whether the target is read-only or includes local management
3. which config, templates, runtime assets, builders, generated schemas, and dependencies form the supported package boundary
4. how route generation, media, search, Python dependencies, and upgrades are installed
5. what compatibility and public-isolation tests the package promises

Only then should a fresh code-derived manifest or installer be produced. A static list of current modules is not a portability architecture.

## Current Code Starting Points

- public/manage delivery boundary: [Runtime Architecture](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- configuration owners: [Configuration And Extension Points](/docs/?scope=studio&doc=config-docs-viewer)
- source and generated layout: [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- public snapshot boundary: [Public Scopes](/docs/?scope=studio&doc=docs-viewer-public-scopes)
- Python requirements: [Dependencies](/docs/?scope=studio&doc=docs-viewer-dependencies)

If work resumes, add one focused delivery with one durable portability owner. Until then, this snapshot has no documentation follow-through obligation.

---
doc_id: site-request-docs-viewer-external-asset-lifecycle-ownership
title: External Asset Collection Lifecycle Ownership
added_date: 2026-07-14
last_updated: 2026-07-14
ui_status: planned
summary: Give scope lifecycle one explicit safe contract for user-owned external asset roots before inventory or UI work begins.
parent_id: site-request-docs-viewer-external-asset-collections
viewable: true
---
# External Asset Collection Lifecycle Ownership

## Outcome

Scope lifecycle can explicitly represent a user-owned external asset root, preserve it during scope deletion, and refuse any rename that would silently relocate it.

This request is complete when the ownership contract is implemented and tested. It does not partially implement the asset inventory feature.

## Why Now

This is EAC-01 in the [Docs Viewer Delivery Roadmap](/docs/?scope=studio&doc=docs-viewer-delivery-roadmap).

Current external-local media is preserved on delete but moved on rename. The manifest mainly describes lifecycle-owned paths. Inventory, reports, and enablement must not build on that ambiguity.

The [feature architecture](/docs/?scope=studio&doc=docs-viewer-external-asset-collections-architecture) describes the larger proposed structure. This request owns only the lifecycle boundary below.

## In Scope

- define a validated scope/manifest association for an enabled user-owned external asset root
- derive the root from the configured projects base and scope id; do not store an absolute path
- distinguish `ownership: user data` and `delete policy: preserve` from lifecycle-owned file records
- make delete preview name the preserved collection and delete apply leave it untouched
- block scope rename whenever the enabled association could be relocated; a future relocation workflow is a separate deliverable
- project only the server-owned lifecycle state needed to test and explain this contract
- add focused config, manifest, delete, rename, containment, and capability tests

Prefer the simplest current representation. Do not add migration aliases, unused versioning, or a general association framework without a second proven need.

## Not In Scope

- collection scanning or a shared filesystem inventory primitive
- the Processing inventory report
- local asset open/download routes
- New Scope or retrofit UI
- enable, disable, or relocation workflows
- wrapper documents, promotion, sub-scopes, editing, moving, or deleting assets
- public routes, R2 publication, caching, jobs, thumbnails, or content extraction

Those outcomes remain separate roadmap rows. Finding that one is useful does not widen this request.

## Code Authority To Inspect

- `docs-viewer/services/docs_scope_config.py`
- `docs-viewer/services/docs_scope_manifest.py`
- `docs-viewer/services/docs_scope_delete.py`
- `docs-viewer/services/docs_scope_rename.py`
- `docs-viewer/services/docs_media_storage.py`
- `docs-viewer/services/docs_management_capabilities_service.py`
- focused lifecycle and capability tests under `docs-viewer/tests/`

These are starting points, not an exhaustive update list. Exact implementation follows the current code.

## Done When

- one explicit server-owned record distinguishes the external collection from deletable lifecycle files
- path derivation is confined beneath the configured projects root and exposes no absolute path to the browser
- delete preview and apply demonstrably preserve the associated root
- rename preview blocks before any move when the association is enabled
- the focused verification set passes
- [Scope Lifecycle](/docs/?scope=studio&doc=docs-viewer-new-scopes-builder) records the shipped ownership and rename/delete behavior
- this request is closed completely; later asset work remains only on the roadmap

## Durable Documentation Boundary

[Scope Lifecycle](/docs/?scope=studio&doc=docs-viewer-new-scopes-builder) is the durable owner for this delivery. A later user-visible inventory request may create the focused External Asset Collections feature document, but this request does not require speculative updates across media, reports, endpoints, setup, or Processing docs.

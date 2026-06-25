---
doc_id: scripts
title: Scripts
added_date: 2026-04-23
last_updated: 2026-06-06
parent_id: dev-home
---
# Scripts

This page is the signpost for active script and runner documentation.
It should not duplicate command flags, output paths, endpoint contracts, or operational caveats that belong in the owning script docs.

Use this page to find the right owner:

- local runners, environment setup, and cloud runtime assumptions
- Admin checks, audits, activity, testing, and risk operations
- Docs Viewer builds, live rebuild, management services, import/export, and link checks
- catalogue source, scoped builds, write services, lookup exports, and field-registry checks
- media derivation and R2 publishing

For repo folder ownership, see [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership).
For environment bootstrap and local prerequisites, see [Local Setup](/docs/?scope=studio&doc=local-setup).
For test strategy and profile selection, see [Testing](/docs/?scope=studio&doc=testing) and [Run Checks](/docs/?scope=studio&doc=scripts-run-checks).

## Local Runtime

- [Local Runners](/docs/?scope=studio&doc=scripts-local-studio) covers `bin/local-studio`, `bin/local-admin`, `bin/local-all`, sibling services, ports, and local service lifecycle.
- [Local Admin App](/docs/?scope=studio&doc=local-admin-app) covers the active Admin app boundary for audits, risk, activity, and testing.
- [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments) covers shared local/cloud runtime expectations, environment variables, and R2-backed media workflows.

## Checks And Audits

- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks) is the entry point for check profiles and local run logs.
- [Audit Runner](/docs/?scope=studio&doc=audit-runner) covers the allowlisted audit runner used by Admin audits.

focused standalone audit commands:

- [Projection Contract Audit](/docs/?scope=studio&doc=scripts-audit-projection-contract),
- [Route Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-route-ready-state)
- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency),
- [CSS Token Audit](/docs/?scope=studio&doc=scripts-css-token-audit)

## Docs Viewer

- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder) covers docs and search payload builds for configured Docs Viewer scopes.
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher) covers local source watching and same-scope rebuild behavior.
- [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server) is the parent page for generated reads, import/rebuild, write actions, operations, and retired Data Sharing management endpoints.
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links) covers docs link checks.
- [Documents Package Preparation Script](/docs/?scope=studio&doc=scripts-docs-export) and [Documents Returned Package Script](/docs/?scope=studio&doc=scripts-docs-import) cover documents Data Sharing package export/import flows.

## Catalogue

- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json) covers focused catalogue source rebuilds, generated route payloads, and related search refresh behavior.
- [Catalogue Write Services](/docs/?scope=studio&doc=scripts-catalogue-write-server) is the parent page for write endpoints, build/lookup behavior, operations, and the service extraction history.
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source) covers source validation and source-adjacent inspection.
- [Catalogue Lookup Export](/docs/?scope=studio&doc=scripts-catalogue-lookup), [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry), and [Project State Report](/docs/?scope=studio&doc=scripts-project-state-report) cover focused catalogue maintenance utilities.

## Media

- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder) covers derivative image generation.
- [Publish Media To R2](/docs/?scope=studio&doc=scripts-publish-media-to-r2) covers previewing and uploading approved catalogue primary-image derivatives to Cloudflare R2.

---
doc_id: catalogue-field-registry-review
title: Catalogue Field Registry
added_date: 2026-05-01
last_updated: "2026-05-22"
parent_id: catalogue
sort_order: 4000
---
# Catalogue Field Registry

Route:

- `/studio/catalogue-field-registry/?mode=manage`

This Studio page is a read-only review surface for `assets/studio/data/catalogue_field_registry.json`.
It is hosted by the local Studio app server, not by a Jekyll route shell.

## Route Ready State

The page root `#fieldRegistryReviewRoot` implements the shared Studio ready-state contract:

- `data-studio-ready="false"` during initial registry loading
- `data-studio-ready="true"` after the registry has loaded or reached a stable unavailable state
- `data-studio-busy="false"` because this route has no route-level commands
- `data-studio-mode="registry"`
- `data-studio-service="available|unavailable"`
- `data-studio-record-loaded="true|false"`

## Purpose

Use this page to inspect the active field-to-artifact registry that catalogue build planning uses for field-aware previews and save-time public updates.

The page intentionally renders the registry source directly rather than recreating planner behavior in the browser.

The current registry includes the migrated work-detail media-section fields. `details_subfolder` and `project_filename` are source-media fields, while `section_title` and `sort_order` are parent work JSON section metadata fields.

The registry is a likely candidate for a future JSON Schema to validate static rule shape before deeper semantic verification runs.
That follow-up is tracked in [JSON Schema Adoption Request](/docs/?scope=studio&doc=site-request-json-schema-adoption).

## Behavior

The page:

- loads the registry path from `assets/studio/data/studio_config.json`
- displays the formatted registry JSON in a read-only text box
- accepts a field-name search
- when search is empty, shows the whole registry
- when search has an exact field-name match, shows the complete rule object that contains the field
- when no exact match exists, shows any complete rules whose field names contain the search text
- leaves the source registry unchanged

## Local App Migration

The page shell is mounted in the local Studio app server and reuses the existing `assets/studio/js/catalogue-field-registry-review.js` browser module.
The old Jekyll route shell has been retired.

Focused smoke coverage:

- `studio/tests/smoke/local_studio_app_catalogue_field_registry_route.py`

## Current Scope

This first review page is deliberately simple.

It does not:

- edit registry rules
- compute build plans
- group rules into a custom table or tree
- replace `./scripts/verify_catalogue_field_registry.py`

## Related References

- [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping)
- [Data Models: Catalogue](/docs/?scope=studio&doc=data-models-catalogue)
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)
- [JSON Schema Adoption Request](/docs/?scope=studio&doc=site-request-json-schema-adoption)

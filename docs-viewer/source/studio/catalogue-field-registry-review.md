---
doc_id: catalogue-field-registry-review
title: Catalogue Field Registry
added_date: 2026-05-01
last_updated: 2026-06-02
parent_id: studio
viewable: true
---
# Catalogue Field Registry

Route:

- `/studio/catalogue-field-registry/`

This Studio page is a read-only review surface for `studio/data/config/catalogue/catalogue-field-registry.json`.
It is hosted by the local Studio app server.

## Route Ready State

The page root `#fieldRegistryReviewRoot` participates in [Route Ready State](/docs/?scope=studio&doc=route-ready-state) with Studio attributes.
Route-specific details:

- no route-level commands set busy
- `data-studio-mode="registry"`
- `data-studio-service="available|unavailable"`
- `data-studio-record-loaded="true|false"`

## Purpose

Use this page to inspect the active field-to-artifact registry that catalogue build planning uses for field-aware previews and save-time public updates.

The page intentionally renders the registry source directly rather than recreating planner behavior in the browser.

The current registry includes the migrated work-detail media-section fields. `details_subfolder` and `project_filename` are source-media fields, while `section_title` and `sort_order` are parent work JSON section metadata fields.

## Behavior

The page:

- loads the registry path from `studio/app/frontend/config/studio-config.json` through `paths.data.studio.catalogue_field_registry`
- displays the formatted registry JSON in a read-only text box
- accepts a field-name search
- when search is empty, shows the whole registry
- when search has an exact field-name match, shows the complete rule object that contains the field
- when no exact match exists, shows any complete rules whose field names contain the search text
- leaves the source registry unchanged

## Local App Migration

The page shell is mounted in the local Studio app server and reuses `studio/app/frontend/js/catalogue-field-registry-review.js`.

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

- [Data Models: Catalogue](/docs/?scope=studio&doc=data-models-catalogue)
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)

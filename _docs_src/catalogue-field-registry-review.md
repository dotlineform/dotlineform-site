---
doc_id: catalogue-field-registry-review
title: "Catalogue Field Registry Review"
added_date: 2026-05-01
last_updated: 2026-05-01
parent_id: studio
sort_order: 235
---
# Catalogue Field Registry Review

Route:

- `/studio/catalogue-field-registry/`

This Studio page is a read-only review surface for `assets/studio/data/catalogue_field_registry.json`.

## Purpose

Use this page to inspect the active field-to-artifact registry that catalogue build planning uses for field-aware previews and save-time public updates.

The page intentionally renders the registry source directly rather than recreating planner behavior in the browser.

## Behavior

The page:

- loads the registry path from `assets/studio/data/studio_config.json`
- displays the formatted registry JSON in a read-only text box
- accepts a field-name search
- when search is empty, shows the whole registry
- when search has an exact field-name match, shows the complete rule object that contains the field
- when no exact match exists, shows any complete rules whose field names contain the search text
- leaves the source registry unchanged

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

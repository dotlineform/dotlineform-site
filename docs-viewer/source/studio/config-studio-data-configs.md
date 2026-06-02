---
doc_id: config-studio-data-configs
title: Studio Data Config Files
added_date: 2026-06-02
last_updated: 2026-06-02
parent_id: studio
viewable: true
---
# Studio Data Config Files

Config files:

- `studio/data/config/catalogue/catalogue-field-registry.json`
- `studio/data/config/runtime/activity-contract.json`

## Catalogue Field Registry

`catalogue-field-registry.json` maps catalogue fields to artifact/build consequences.
Catalogue services and review UI use it to explain which generated artifacts are affected by a proposed source edit.

Current readers include:

- `studio/services/catalogue/catalogue_field_registry.py`
- Local Studio field-registry review UI through the configured path in `studio/app/frontend/config/studio-config.json`
- catalogue build and source-change planning flows that need artifact impact ordering

Edit class: maintainer-editable domain config.

This is not user preference data.
Changing rules changes build planning and must be covered by focused catalogue registry tests.

## Activity Contract

`activity-contract.json` defines activity grouping and display contract data for Studio runtime activity.
It belongs to runtime data presentation and activity interpretation, not route boot or service endpoint configuration.

Edit class: code infrastructure.

Changing it should be paired with activity-log tests or runtime activity contract checks.

## Cleanup Review

For `catalogue-field-registry.json`:

- verify all configured artifact ids still map to active build artifacts
- remove rules for retired generated outputs
- keep fallback defaults aligned with catalogue generator behavior
- keep the file path resolved from `paths.data.studio.catalogue_field_registry` until a narrower resolver replaces that dependency

For `activity-contract.json`:

- verify each grouping/status value is still emitted by current services
- remove retired activity families
- keep visible copy in route UI-text bundles rather than in the activity contract


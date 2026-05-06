---
doc_id: scripts-verify-catalogue-field-registry
title: Catalogue Field Registry Verification
added_date: 2026-05-01
last_updated: "2026-05-06 20:49"
parent_id: catalogue
sort_order: 80
---
# Catalogue Field Registry Verification

Script:

```bash
./scripts/verify_catalogue_field_registry.py
```

Test wrapper:

```bash
tests/python/test_catalogue_field_registry.py
```

This read-only helper verifies representative catalogue field-registry build plans and checks that the registry stays aligned with the canonical catalogue source field sets.

## Purpose

Use this script after changing:

- `assets/studio/data/catalogue_field_registry.json`
- `scripts/catalogue_field_registry.py`
- `scripts/catalogue_source.py`
- `scripts/moment_sources.py`
- field-aware preview or save-time build planning
- the optional `catalogue` check profile in `./scripts/run_checks.py`

It loads the registry path through `assets/studio/data/studio_config.json`, then checks that target rules and fallback defaults still produce the expected artifact, generator, catalogue-search, and local-media selections.

It also verifies source/registry drift:

- registry fields must be known source fields or explicit verifier exemptions
- active editable source fields must have a `metadata_update` rule or explicit verifier exemption
- identity and derived fields must not be classified as normal metadata edits
- duplicate field ownership within a record family and operation fails
- optional omit-empty source fields keep their serialization behavior

## Checked Cases

The verification covers:

- work-local public metadata such as `downloads` and `links`
- work editor-only metadata such as `notes` and `provenance`
- work media source fields such as `project_filename`
- work search enrichment fields such as `medium_type`
- work display fields with a related series `sort_fields` dependency
- work publication and membership fields such as `series_ids`
- work-detail public section metadata such as `section_title` and `sort_order`
- work-detail source media fields such as `details_subfolder` and `project_filename`
- series publication fields and series notes
- moment display fields and moment media source fields
- unknown-field fallback
- mixed dependency-class fallback
- series saves that also change member work rows
- source/registry coverage for work, work-detail, series, and moment fields
- optional source serialization for work `project_subfolder`, detail `details_subfolder`, and detail `sort_order`

## Output

Successful output:

```text
catalogue field registry verification passed (17 checks)
```

The exact check count may increase as source/registry guardrails are added.

A failing check exits non-zero and reports the first mismatched plan field.

## Boundaries

This script verifies planner behavior and source/registry coverage. It does not make the registry the owner of source serialization. Field order, normalization, and omit-empty behavior still live in `scripts/catalogue_source.py` and `scripts/moment_sources.py`.

It does not write generated files, run local media generation, rebuild catalogue search, or verify browser UI behavior.

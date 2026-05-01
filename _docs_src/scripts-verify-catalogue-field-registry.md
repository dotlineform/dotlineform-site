---
doc_id: scripts-verify-catalogue-field-registry
title: "Catalogue Field Registry Verification"
added_date: 2026-05-01
last_updated: 2026-05-01
parent_id: scripts
sort_order: 75
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

This read-only helper verifies representative catalogue field-registry build plans.

## Purpose

Use this script after changing:

- `assets/studio/data/catalogue_field_registry.json`
- `scripts/catalogue_field_registry.py`
- field-aware preview or save-time build planning
- the optional `catalogue` check profile in `./scripts/run_checks.py`

It loads the registry path through `assets/studio/data/studio_config.json`, then checks that target rules and fallback defaults still produce the expected artifact, generator, catalogue-search, and local-media selections.

## Checked Cases

The verification covers:

- work-local public metadata such as `downloads` and `links`
- work editor-only metadata such as `notes` and `provenance`
- work media source fields such as `project_filename`
- work search enrichment fields such as `medium_type`
- work display fields with a related series `sort_fields` dependency
- work publication and membership fields such as `series_ids`
- work-detail public metadata and media source fields
- series publication fields and series notes
- moment display fields and moment media source fields
- unknown-field fallback
- mixed dependency-class fallback
- series saves that also change member work rows

## Output

Successful output:

```text
catalogue field registry verification passed (16 checks)
```

A failing check exits non-zero and reports the first mismatched plan field.

## Boundaries

This script verifies planner behavior. It does not write generated files, run local media generation, rebuild catalogue search, or verify browser UI behavior.

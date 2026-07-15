---
doc_id: scripts-verify-catalogue-field-registry
title: Catalogue Field Registry Verification
added_date: 2026-05-01
last_updated: 2026-07-15
parent_id: studio
viewable: true
---
# Catalogue Field Registry Verification

## Command

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/verify_catalogue_field_registry.py
```

Pytest wrapper:

```text
studio/tests/python/test_catalogue_field_registry.py
```

## What It Proves

The verifier loads the registry path from `studio-config.json` and checks two directions of agreement:

- representative fields select the intended public artifacts, generator modes, search work, local media, and fallback behavior;
- active Work, Series, and detail source fields are classified consistently as identity, derived, editable metadata, or explicit exemption.

It also rejects duplicate field ownership within a record family/operation and checks serializer omit-empty behavior for optional fields.

## When To Run It

Run it after changing:

- `catalogue-field-registry.json`;
- catalogue source fields or normalization;
- field-aware build or lookup planning;
- a field's public/search/media behavior;
- registry loading or fallback policy.

The script does not write source or generated files. It does not prove browser UI behavior or execute a catalogue build.

## Ownership Boundary

`catalogue_source.py` owns field existence and serialization. `catalogue_field_registry.py` owns dependency-plan interpretation. The JSON registry owns checked policy. The verifier ensures they agree without making any one of them a second copy of the others.

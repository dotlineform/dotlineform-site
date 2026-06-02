---
doc_id: site-request-json-schema-adoption
title: JSON Schema Adoption Request
added_date: "2026-05-03 14:35"
last_updated: 2026-05-26
ui_status: deferred
parent_id: change-requests
viewable: true
---
# JSON Schema Adoption Request

Status:

- proposed

## Summary

This change request proposes selective JSON Schema adoption for source-controlled configuration files.

The goal is not to add schemas for every data artifact.
The goal is to use schemas where a config file is hand-edited, structurally meaningful, and likely to fail in subtle ways if a key, option value, or nested shape drifts.

The first successful example is the Library export config schema:

- `studio/data/config/data-sharing/library-export-configs.schema.json`
- `studio/data/config/data-sharing/library-export-configs.json`

That pattern may be useful elsewhere, especially for compact control/config contracts such as search policy and the catalogue field registry.

## Spec

### Boundary

Use JSON Schema for files that are:

- source-controlled project configuration
- edited or reviewed by humans
- consumed by runtime or build logic
- constrained by known option values or required nested structures
- small enough that a schema remains readable and maintainable

Do not use JSON Schema by default for:

- large generated JSON payloads
- files where the generator code is the real contract
- canonical records whose field model is still changing too quickly
- data that already has better targeted validation through scripts or audits

### Primary Candidates

#### Search Policy

Candidate file:

- `assets/data/search/policy.json`

Why it is a good fit:

- compact runtime-facing config
- constrained option values
- loaded by public search behavior
- easier to validate before runtime than debug after page load

Likely schema coverage:

- enabled scopes and labels
- minimum query length
- debounce and result batch sizes
- supported messages and fallback text
- required route/runtime policy keys

Related doc:

- [Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)

#### Catalogue Field Registry

Candidate file:

- `assets/studio/data/catalogue_field_registry.json`

Why it is a good fit:

- hand-reviewed control config
- central to field-aware build planning
- current validation already exists through `./scripts/verify_catalogue_field_registry.py`
- a schema could catch static shape errors before deeper semantic checks run

Likely schema coverage:

- top-level registry version or metadata
- rule object shape
- field-name arrays
- allowed operation or target keys
- required artifact/generator references
- boolean and list field types

The schema should complement, not replace, the existing verifier.
The verifier should continue to own semantic checks such as source-field coverage, duplicate ownership, unknown registry fields, and build-planning expectations.

Related docs:

- [Catalogue Field Registry Review](/docs/?scope=studio&doc=catalogue-field-registry-review)
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)

### Secondary Candidates

Possible later candidates:

- `assets/studio/data/studio_config.json`
  useful but broad; start with narrow subschemas only if this is attempted
- `_data/pipeline.json`
  useful for media/env/path contract validation
- dedicated small Studio page configs if more are added

### Validation Model

Schema validation should be integrated into targeted checks rather than becoming a new manual-only step.

Preferred validation path:

- each schema lives next to the config it validates when practical
- config docs link both the config file and schema file
- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py` can later include schema validation in the smallest relevant profile
- deeper semantic validators remain responsible for checks that JSON Schema cannot express cleanly

## Open Questions

- Should schema files live beside their config files, under a shared `schemas/` directory, or case-by-case?
- Should schema validation be added to `quick`, only to subsystem profiles, or only to explicit scripts at first?
- Should `studio_config.json` get one broad schema later or several smaller schema fragments for stable sections?
- Should the catalogue field registry schema be written before or after the next registry shape change?

## Current Recommendation

Start with the two likely candidates:

1. Search policy schema.
2. Catalogue field registry schema.

Do not add schemas for generated docs/search indexes or broad catalogue records yet.
For those, keep using generator tests, audits, and targeted validation scripts.

Benefits:

- catches config typos before runtime
- makes config contracts easier to review
- gives future Studio UI work stable assumptions
- keeps semantic validators focused on behavior rather than basic shape

Risks:

- schemas can become stale if they duplicate unstable implementation details
- broad schemas may create maintenance drag without improving confidence
- schema validation can give false confidence if deeper semantic checks are skipped

## Implementation Tasks

### Task 1. Decide Schema Placement Convention

Choose whether schema files live beside config files or in a shared schema directory.
The Library export schema currently lives beside its config.

### Task 2. Add Search Policy Schema

Create a schema for `assets/data/search/policy.json`.
Keep it focused on static shape, required runtime keys, allowed scope entries, numeric policy values, and message fields.

### Task 3. Add Search Policy Validation Check

Add a small validation script or extend an existing search check so the policy schema is validated in the relevant check profile.

### Task 4. Add Catalogue Field Registry Schema

Create a schema for `assets/studio/data/catalogue_field_registry.json`.
Keep it focused on registry object shape and allowed field types while leaving source-coverage and build-planning semantics to the existing verifier.

### Task 5. Integrate Registry Schema Validation

Extend `./scripts/verify_catalogue_field_registry.py` or its wrapper checks so schema validation runs before semantic registry verification.

### Task 6. Document Schema Usage

Update Config, Search, Catalogue Field Registry, and check-profile docs once the first additional schemas are implemented.

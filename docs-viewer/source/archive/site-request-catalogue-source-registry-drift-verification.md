---
doc_id: site-request-catalogue-source-registry-drift-verification
title: Catalogue Source And Registry Drift Verification Request
added_date: 2026-05-02
last_updated: 2026-05-03
ui_status: done
sort_order: 52000
---
# Catalogue Source And Registry Drift Verification Request

Status:

- implemented

## Current Implementation

Implemented in `./scripts/verify_catalogue_field_registry.py`.

The verifier now checks:

- duplicate registry ownership by record family, operation, and field
- registry fields against known source field sets or explicit verifier exemptions
- editable source metadata fields against `metadata_update` registry coverage or explicit verifier exemptions
- identity and derived fields are not misclassified as normal metadata edits
- omit-empty serialization for work `project_subfolder`, detail `details_subfolder`, and detail `sort_order`
- detail `section_id` and `section_title` remain required/present during normalization even when blank

Source field ownership is exposed from:

- `scripts/catalogue_source.py` for work, work-detail, and series source records
- `scripts/moment_sources.py` for moment metadata source records

## Summary

This request tracks a follow-up verification layer between the canonical catalogue source schema and the field-aware build registry.

The current implementation has two separate contracts:

- `scripts/catalogue_source.py` defines source record serialization, field ordering, normalization, and omit-empty behavior
- `assets/studio/data/catalogue_field_registry.json` defines field-to-artifact build and invalidation dependencies

That separation is correct, because the registry is not a source serializer. But it creates a drift risk: a field can be added to one contract without being classified in the other.

This request should not block [Catalogue Media And Detail Section Schema Request](/docs/?scope=studio&doc=site-request-catalogue-media-section-schema). It is a follow-on guardrail so later schema and registry changes fail loudly when they diverge.

## Problem

Field names are currently maintained in more than one place.

Examples:

- adding `project_subfolder` to work source records also needs a registry rule
- migrating detail `project_subfolder` to `details_subfolder`, `section_id`, `section_title`, and `sort_order` also needs source field order and registry rules
- optional persisted fields need source serialization behavior that the registry does not describe
- derived or virtual fields may legitimately appear in planning without being writeable source fields

Without an explicit drift check, these mismatches are easy to miss until a save/build path uses conservative fallback, drops a field during write-back, or misreports the build scope.

## Goals

- keep source serialization and build dependency planning as separate contracts
- verify that registry fields are known to the source schema or explicitly classified as derived or virtual
- verify that active source fields are either covered by the registry or explicitly exempted
- verify omit-empty behavior for optional persisted fields such as `project_subfolder`, `details_subfolder`, and `sort_order`
- make `scripts/verify_catalogue_field_registry.py` fail when source/registry drift is introduced
- keep the check lightweight and executable without a broader test framework

## Non-Goals

- do not make `scripts/catalogue_source.py` read field order from the registry
- do not make the field registry responsible for JSON serialization
- do not block the media-section migration dry-run command
- do not require every derived or generated field to become a source field

## Proposed Direction

Extend the existing registry verification path instead of adding another disconnected script.

Candidate behavior:

- expose source field sets from `scripts/catalogue_source.py`
- define explicit derived or virtual field exemptions where needed
- check every registry `metadata_update` field against the relevant source family field set or exemption list
- check every source field that can be edited in Studio has a registry rule or an explicit no-build exemption
- keep `create_delete_identity` and `derived_update` checks separate from normal metadata-edit checks
- add focused assertions for optional omit-empty source fields

The check should report field-family context clearly, such as `work_detail.metadata_update.details_subfolder`.

## Task List

### Task 1. Define Schema/Registry Ownership Boundaries

Status:

- done

Document which contract owns:

- source field order
- source normalization
- omit-empty behavior
- build artifact dependencies
- derived fields
- virtual or operation-only fields

Acceptance checks:

- the docs explain why the registry does not drive source serialization
- the docs identify where to add a new source field and where to add its build dependency rule

### Task 2. Add Drift Verification

Status:

- done

Extend `scripts/verify_catalogue_field_registry.py` so it catches source/registry drift.

Expected checks:

- registry metadata fields exist in the corresponding source field list or an exemption list
- active editable source fields are classified in the registry or explicitly exempted
- duplicate registry ownership still fails
- error messages identify record family, operation, and field name

Acceptance checks:

- adding an unknown registry field fails the verifier
- adding an uncovered editable source field fails the verifier
- derived and virtual fields can be exempted explicitly without hiding source field drift

### Task 3. Verify Optional Source Serialization

Status:

- done

Add focused checks for optional persisted source fields.

Expected fields:

- work `project_subfolder`
- detail `details_subfolder`
- detail `sort_order`

Acceptance checks:

- non-empty values are preserved during normalized source write-back
- null, empty, or blank values are omitted from source JSON
- required fields such as `section_id` and `section_title` are not accidentally treated as optional omit-empty fields

### Task 4. Update Docs

Status:

- done

Update script and data-model docs after the verifier is implemented.

Expected docs:

- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)
- relevant data-model docs if source field ownership guidance changes

Acceptance checks:

- docs describe the drift check as a guardrail, not as the source of truth for serialization
- Studio docs payloads are rebuilt for the Studio scope

## Benefits

- fewer silent source/registry mismatches
- clearer maintenance workflow when adding catalogue fields
- preserves the correct separation between source serialization and build planning
- makes future schema migrations safer without adding heavy test infrastructure

## Risks

- the exemption model can become another maintenance surface if it is too broad
- overly strict checks could block legitimate derived or operation-only fields
- verification should stay focused enough that schema work remains easy to iterate

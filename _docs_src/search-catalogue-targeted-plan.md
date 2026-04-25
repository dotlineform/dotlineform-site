---
doc_id: search-catalogue-targeted-plan
title: "Catalogue Targeted Search Plan"
added_date: 2026-04-25
last_updated: 2026-04-25
parent_id: search
sort_order: 95
---
# Catalogue Targeted Search Plan

Status:

- follow-on planning document
- not implemented
- depends on the completed docs-domain incremental search phases
- should start with dependency rules before changing `scripts/build_search.rb`

## Purpose

Define the catalogue-specific path toward targeted search updates.

Catalogue targeted search is intentionally separate from the docs-domain implementation because catalogue records are not isolated one-file-to-one-search-entry records. Work, series, moment, tag, and generated payload changes can affect multiple search entries in ways that need explicit dependency rules.

## Current State

Current catalogue search behavior:

- `./scripts/build_search.rb --scope catalogue --write` performs a full rebuild
- `--only-doc-ids` is refused for `catalogue`
- `scripts/search/build_config.json` marks catalogue source families as full-rebuild-only
- generated catalogue search remains one combined artifact at `assets/data/search/catalogue/index.json`

This is correct for now. A full rebuild remains the operational escape hatch until catalogue affected-record rules are precise enough to trust targeted patching.

## Key Observations

Catalogue targeted updates are more complex than docs targeted updates.

Reasons:

- a work entry can depend on work index data, per-work payload data, series relationships, series titles, tag assignments, and tag labels
- a series title or series metadata change can affect the series entry and related work entries
- a moment entry is probably more isolated than works and series, but still needs explicit id and removal rules
- tag assignment changes can affect selected work and series entries
- tag registry label changes can affect every entry carrying that tag label unless an affected set is cheap and explicit
- `tag_labels` are serialized even though tag labels are not currently folded into `search_terms`
- generated public search artifacts should not gain operation provenance just to support targeted updates

## Proposed Builder Interface

Do not reuse `--only-doc-ids` for catalogue.

A catalogue-specific interface should name catalogue record identity explicitly. A likely first command shape is:

```bash
./scripts/build_search.rb --scope catalogue --write --only-records work:00001,series:009,moment:blue-sky --remove-missing
```

Open naming choices:

- `--only-records`
- `--only-catalogue-records`
- separate flags such as `--work-ids`, `--series-ids`, and `--moment-ids`

The separate-flag version is more verbose but easier to validate and may match existing catalogue generator command shapes better.

## Affected-Record Rules

Initial conservative rules:

- work source changes target the changed work entry
- per-work payload changes target the changed work entry
- moment source changes target the changed moment entry
- series source changes target the series entry plus related work entries
- work `series_ids` changes target the changed work entry and may require old and new related series entries only if serialized series summaries change
- tag assignment changes target explicit affected work and series entries when the assignment payload exposes them cheaply
- tag registry label changes fall back to full rebuild unless the affected set can be derived cheaply and explicitly
- catalogue index shape or source-family config changes fall back to full rebuild
- unknown source family, ambiguous id, parse failure, or missing current artifact falls back to full rebuild

These rules should be validated against actual `scripts/studio/catalogue_write_server.py` invalidation classes before implementation. The existing `single-record` and `targeted-multi-record` lookup-refresh paths are relevant prior art, but search should still own search-record generation and merge behavior.

## Builder Responsibilities

The search builder should own:

- rebuilding catalogue entries from current generated source artifacts
- loading the existing search artifact for targeted mode
- removing affected entries when `--remove-missing` is present and the source record no longer produces an entry
- merging changed entries into the existing artifact
- sorting deterministically
- recomputing header version and count
- reporting changed, removed, unchanged, skipped, and full-fallback counts

The search builder should not own:

- Studio write workflow decisions
- catalogue editor field-level invalidation classification
- backup creation
- UI messaging
- long-running operation logs

## Orchestration Responsibilities

Catalogue write/build orchestration should own:

- detecting which catalogue source records changed
- mapping source changes to affected catalogue search records
- deciding targeted versus full rebuild before invoking `scripts/build_search.rb`
- batching many source writes into one search update
- falling back to full rebuild when dependency state is ambiguous

## Validation Plan

Before enabling catalogue targeted search in live write flows:

- run full catalogue rebuild and save output
- run targeted catalogue update for representative work, series, moment, tag assignment, and tag registry cases
- compare targeted output against a full rebuild for the same final source state
- verify deterministic ordering and header version behavior
- verify removed or unpublished records are removed only when the targeted command explicitly allows removal
- confirm `catalogue` targeted mode still refuses ambiguous source-family changes
- update [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist) with catalogue-targeted checks

## First Implementation Slice

Recommended first slice:

1. decide the CLI shape
2. add catalogue record-id parsing without using it in live Studio writes
3. support targeted patching for isolated work and moment records only
4. keep series and tag changes full-rebuild-only
5. compare targeted output with full rebuild output in verification
6. document remaining catalogue dependency gaps

This provides a narrow proof of the merge/update mechanics without prematurely solving the hardest cross-record invalidation cases.

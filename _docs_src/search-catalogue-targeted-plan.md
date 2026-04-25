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

- first additive-only slice implemented
- depends on the completed docs-domain incremental search phases
- supports additive new work, new series, and new moment records only
- existing-record edits and removals still require a full catalogue search rebuild
- tags, tag assignments, and work details are out of scope

## Purpose

Define the catalogue-specific path toward targeted search updates.

Catalogue targeted search is intentionally separate from the docs-domain implementation because catalogue records are not always isolated one-file-to-one-search-entry records. Work, series, moment, and generated payload changes can affect search entries in ways that need explicit dependency rules.

## Current State

Current catalogue search behavior:

- `./scripts/build_search.rb --scope catalogue --write` performs a full rebuild
- `--only-doc-ids` is refused for `catalogue`
- `--only-records` supports additive catalogue inserts for `work`, `series`, and `moment`
- `scripts/search/build_config.json` marks the catalogue scope with `targeted_policy: "additive_only"` and `targeted_operations: ["create"]`
- generated catalogue search remains one combined artifact at `assets/data/search/catalogue/index.json`

A full rebuild remains the operational escape hatch for edits, removals, tag changes, work-detail changes, and ambiguous dependency states.

## Key Observations

Catalogue targeted updates are more complex than docs targeted updates.

Reasons:

- a work entry can depend on work index data, per-work payload data, series relationships, and series titles
- a series title or series metadata change can affect the series entry and related work entries
- a moment entry is probably more isolated than works and series, but still needs explicit id and removal rules
- `tag_ids` and `tag_labels` are serialized in the current catalogue search artifact but do not participate in matching or ranking
- tag search, tag-assignment search, and tag-label invalidation should stay out of the catalogue targeted-search slice
- work details are not separate public search entries and should stay out of scope to avoid noisy recall
- generated public search artifacts should not gain operation provenance just to support targeted updates

The biggest near-term win is additive creation. New work, new series, and new moment records can be inserted without a full rebuild because existing search entries do not need to change under the current schema.

## Proposed Builder Interface

Do not reuse `--only-doc-ids` for catalogue.

A catalogue-specific interface names catalogue record identity explicitly:

```bash
./scripts/build_search.rb --scope catalogue --write --only-records work:00001,series:009,moment:blue-sky
```

Accepted record kinds:

- `work`
- `series`
- `moment`

The command is additive-only. If the target entry is missing from the existing search artifact, the builder inserts it from the current generated catalogue source JSON. If the target entry already exists and is identical, the command is idempotent and reports it as unchanged. If the target entry already exists but differs, the builder refuses the targeted run and requires a full catalogue search rebuild.

`--remove-missing` is not supported for catalogue in this slice.

## Affected-Record Rules

Initial conservative rules:

- new work targets only the new work entry
- new series targets only the new series entry
- new moment targets only the new moment entry
- work source edits require full rebuild for now
- per-work payload edits require full rebuild for now
- moment source edits require full rebuild for now
- series source edits require full rebuild for now
- work `series_ids` edits require full rebuild for now
- tag assignment changes are out of scope for the first catalogue targeted-search implementation
- tag registry label changes are out of scope for the first catalogue targeted-search implementation
- work detail changes are out of scope for catalogue targeted search unless a later search schema intentionally adds detail-level records or fields
- catalogue index shape or source-family config changes fall back to full rebuild
- unknown source family, ambiguous id, parse failure, or missing current artifact falls back to full rebuild

These rules should be validated against actual `scripts/studio/catalogue_write_server.py` invalidation classes before implementation. The existing `single-record` and `targeted-multi-record` lookup-refresh paths are relevant prior art, but search should still own search-record generation and merge behavior.

## Builder Responsibilities

The search builder should own:

- rebuilding catalogue entries from current generated source artifacts
- loading the existing search artifact for targeted mode
- refusing removal requests in the additive-only first slice
- removing affected entries in a later slice only when deletion rules are explicit
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
- run targeted catalogue update for representative new work, new series, and new moment cases
- compare targeted output against a full rebuild for the same final source state
- verify deterministic ordering and header version behavior
- verify catalogue targeted mode refuses `--remove-missing`
- verify existing changed records are refused and routed to full rebuild
- confirm `catalogue` targeted mode still refuses ambiguous source-family changes, tag changes, and work-detail changes
- update [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist) with catalogue-targeted checks

## First Implementation Slice

Implemented first slice:

1. CLI shape is `--only-records kind:id,...`
2. catalogue scope policy is `targeted_policy: "additive_only"` with `targeted_operations: ["create"]`
3. catalogue record-id parsing validates `work`, `series`, and `moment`
4. targeted insertion supports new work records
5. targeted insertion supports new series records
6. targeted insertion supports new moment records
7. edits to existing records remain full-rebuild-only
8. tags, tag assignments, and work details remain out of scope
9. verification compares targeted output with full rebuild output
10. remaining catalogue dependency gaps stay documented for later slices

This provides a narrow proof of the merge/update mechanics without prematurely solving existing-record edits or the hardest cross-record invalidation cases.

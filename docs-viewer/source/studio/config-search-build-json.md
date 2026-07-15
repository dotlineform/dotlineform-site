---
doc_id: config-search-build-json
title: Catalogue Search Build Config
added_date: 2026-04-25
last_updated: 2026-07-15
parent_id: search-catalogue-infrastructure
viewable: true
---
# Catalogue Search Build Config

`studio/services/catalogue/search/build_config.json` is the Catalogue search dependency registry.

## It Owns

- source-family ids and their Catalogue ownership
- targeted-update policy and allowed operations per source family
- scope-level targeted policy
- mapping from every emitted index field to one or more source families
- whether a field is derived from those sources

`studio/services/catalogue/search/build_search.py` loads and validates the registry before constructing output. The build fails when it emits a field without a declared source family.

## Current Policy

Catalogue search is `additive_only` for `create`. New works and series can be merged into an existing index. Updates and deletes require a full same-domain rebuild.

The supported policy vocabulary also includes `record_update` and `full_rebuild`, but changing the declaration does not implement missing invalidation behaviour. Builder support and tests must change with the config.

## It Does Not Own

- record-construction algorithms
- ranking or normalization
- runtime labels, timing, or messages
- Docs Viewer search scopes
- generated-operation history

Those belong to the builder/runtime or to [Catalogue Search Policy](/docs/?scope=studio&doc=config-search-policy-json).

When adding a source or search field, update this registry first so the dependency boundary remains explicit. Read the JSON and its validator for the exact current inventory.

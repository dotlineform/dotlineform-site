---
doc_id: config-search-build-json
title: Search Build Config JSON
added_date: 2026-04-25
last_updated: "2026-05-11 21:30"
parent_id: search
---
# Search Build Config JSON

Config file:

- `scripts/search/build_config.json`

## Scope

`build_config.json` is the Catalogue search source-family and field-dependency contract used behind `studio/services/catalogue/search/build_search.rb --scope catalogue`.
Docs Viewer search no longer uses this file.

Current responsibilities include:

- declaring source artifact families used by Catalogue search
- declaring each source family's `targeted_policy`
- declaring `targeted_operations` for policies that allow targeted updates
- mapping emitted search fields to their source families
- documenting that current search artifacts stay combined per scope

## What calls it

Current caller:

- `scripts/search/build_search.rb`, reached through `studio/services/catalogue/search/build_search.rb --scope catalogue`

The Catalogue builder loads this config at startup, validates the config shape, and then checks that emitted entry fields have source-family declarations.

## When it is read

- once per `./studio/services/catalogue/search/build_search.rb --scope catalogue` invocation
- before build output is written or skipped

## Current boundaries

What stays here:

- source-family names
- scope eligibility for each source family
- targeted policy values such as `record_update`, `additive_only`, and `full_rebuild`
- field-to-source-family declarations
- Catalogue-only field dependency checks

What does not stay here:

- Docs Viewer scope lists, docs-search input paths, or docs-search field policy
- record-construction algorithms
- ranking rules
- runtime UI policy
- operation logs or targeted-update provenance

Those remain in builder code, search runtime code, CLI/server output, or the dedicated runtime policy files as appropriate.

## Targeted Policy Values

Current policy values:

- `record_update`
  Supported by the shared policy vocabulary and used by Docs Viewer search, but not currently declared in this Catalogue-owned config.
- `additive_only`
  Used by the first catalogue targeted-search slice, where only new work, series, and moment entries are safe to insert without changing existing records.
- `full_rebuild`
  Used when a source family or scope should not use targeted updates.

The policy value is intentionally more explicit than a boolean because catalogue can become partly targetable without making every catalogue source-family change safe for targeted updates.

Validation rejects the old `targeted` boolean form. Policies that allow targeted updates must declare `targeted_operations`; `full_rebuild` entries must omit it. Operation values must also match the policy: `record_update` allows `create`, `update`, and `delete`; `additive_only` allows `create`.

## Heavy-index readiness

The config exists so future body, summary, or prose-heavy indexing can add source-family declarations before adding heavier fields to the public search artifacts.
For Docs Viewer body or summary indexing, update the Docs Viewer search builder/config surfaces rather than this Catalogue config.

The first implementation deliberately avoids per-record checksums and sidecar payloads. The current fallback remains a full same-scope rebuild when a dependency cannot be invalidated cheaply and explicitly.

For the broader build flow, see [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline).

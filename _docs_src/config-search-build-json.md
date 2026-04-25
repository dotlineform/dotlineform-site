---
doc_id: config-search-build-json
title: "Search Build Config JSON"
added_date: 2026-04-25
last_updated: 2026-04-25
parent_id: config
sort_order: 55
---

# Search Build Config JSON

Config file:

- `scripts/search/build_config.json`

## Scope

`build_config.json` is the build-owned source-family and field-dependency contract for `scripts/build_search.rb`.

Current responsibilities include:

- declaring source artifact families used by each live search scope
- declaring whether each source family supports targeted updates or falls back to full rebuilds
- mapping emitted search fields to their source families
- documenting that current search artifacts stay combined per scope

## What calls it

Current caller:

- `scripts/build_search.rb`

The builder loads this config at startup for every scope, validates the config shape, and then checks that emitted entry fields have source-family declarations.

## When it is read

- once per `./scripts/build_search.rb` invocation
- before build output is written or skipped

## Current boundaries

What stays here:

- source-family names
- scope eligibility for each source family
- targeted versus full-rebuild dependency policy
- field-to-source-family declarations

What does not stay here:

- record-construction algorithms
- ranking rules
- runtime UI policy
- operation logs or targeted-update provenance

Those remain in builder code, search runtime code, CLI/server output, or the dedicated runtime policy files as appropriate.

## Heavy-index readiness

The config exists so future body, summary, or prose-heavy indexing can add source-family declarations before adding heavier fields to the public search artifacts.

The first implementation deliberately avoids per-record checksums and sidecar payloads. The current fallback remains a full same-scope rebuild when a dependency cannot be invalidated cheaply and explicitly.

For the broader build flow, see [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline).

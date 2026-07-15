---
doc_id: data-models-catalogue
title: Catalogue Architecture
added_date: 2026-04-01
last_updated: 2026-07-15
parent_id: studio
viewable: true
---
# Catalogue Architecture

## Stable Shape

The catalogue separates authoring source from the payloads optimized for Studio and the public site.

```text
canonical Works, Series, details, and optional prose
  -> catalogue services validate and mutate source
  -> lookup planner writes Studio search/list projections
  -> build planner writes public indexes and record payloads
  -> public route modules load only the payloads they need
```

[Catalogue Source Model](/docs/?scope=studio&doc=data-models-catalogue-source) owns the authoring boundary. [Catalogue Indexes And Payloads](/docs/?scope=studio&doc=data-models-catalogue-indexes) maps the important generated read models. [Public Catalogue Data Flow](/docs/?scope=studio&doc=data-flow) maps those read models to routes.

## Why It Is Split

- Canonical source is optimized for understandable, validated edits.
- Studio search and editor projections are optimized for local workflows.
- Public aggregate indexes avoid fetching every full record to render a list.
- Per-record public payloads carry richer Work or Series content only when a route selects it.
- Catalogue search has a flat search-oriented shape rather than bloating runtime indexes.

Generated data is disposable even when it is checked in. A generated payload does not become an authority because several consumers use it.

## Ownership Rules

- Work metadata and publication state belong to `works.json`.
- Series metadata, publication state, primary Work, and sort policy belong to `series.json`.
- Detail sections and records belong to one per-Work detail aggregate.
- Work and Series prose, when present, lives in the catalogue Markdown source tree.
- Field-to-artifact impact belongs to the catalogue field registry.
- Public Moments are a Docs Viewer scope; they are not an active Local Studio catalogue editor family.

## Change Method

For a source-field or workflow change:

1. update source normalization and validation;
2. update the field registry when generated impact changes;
3. update Studio projections or public serializers that consume the field;
4. update focused route/service behavior;
5. run source, registry, build-planning, runtime, and consistency checks appropriate to the blast radius.

Do not update every catalogue document. The durable owner is the source model, generated-payload map, workflow page, or focused command reference affected by the change.

## Known Weak Spots

- Several services normalize the full catalogue into in-memory maps even when source storage is per-Work.
- Studio combines generated list payloads with service-only focused projections, so configuration must keep those two read methods obvious.
- Build and lookup dependency planning are separate systems because their output families differ.
- Catalogue prose exists as an optional generator input but currently has no active Studio editing workflow.

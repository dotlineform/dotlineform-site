---
doc_id: ui-pattern-column-links
title: Column Links Pattern
added_date: 2026-05-05
last_updated: 2026-05-30
parent_id: ui-catalogue
---
# Column Links Pattern

This composition pattern covers compact route-link column groups used on Studio dashboard and catalogue entry pages.

Demo reference:

- [Column links pattern demo](http://127.0.0.1:8768/admin/ui-catalogue/demos/patterns/column-links/)

Current live examples:

- `/studio/catalogue/`

## Scope

Use this pattern when:

- a page is primarily routing the user into a small set of related work areas
- links naturally group into any small number of short categories
- category headings add useful scan structure
- individual links do not need descriptions, counts, or cards

Do not use this pattern for:

- long navigation lists
- content previews
- repeated records with metadata
- command buttons
- link groups where every item needs explanatory text

## Anatomy

The pattern combines labeled columns with stacked pill links.

The live pattern uses route-owned class names that follow the same structure as the demo:

- a column wrapper
- one labeled group per column
- compact pill anchors in each group

Additional column counts should be explicit in the owning route or shared CSS rather than inferred from content length.

The links are ordinary anchors styled as pills.
They should navigate, not run local commands.

## Lifecycle Contract

Column links are static route affordances.
They should not depend on local write-server data or delayed JS state.

If a page also displays metrics or dynamic readiness state, keep that behavior outside the column-link pattern.
The links should remain visible and usable while metrics load.

## Implementation Notes

Current implementation lives in:

- `assets/css/main.css`

Current demo implementation lives in:

- `admin-app/ui-catalogue/assets/css/ui-catalogue-demo.css`
- `admin-app/ui-catalogue/source/demos/patterns/column-links/index.md`

Current live pages use:

- `studioHomeLinks`
- `studioHomeLinks__column`
- `studioHomeLinks__pills`
- `studioHomeLinks__pill`

Keep link labels short enough to fit the pill treatment.
If labels need supporting copy, move to a different pattern rather than stretching this one into a card grid.

The UI Catalogue demo uses `uiCatalogueDemoColumnLinks*` classes. Treat those as demo-only pattern names, then map the structure into an owning live namespace such as `studioHomeLinks*`.

## Migration Notes

This pattern was first reused by Catalogue and Library dashboards, then adopted by the former Studio Analytics and Data Sharing dashboard routes. The Library, Analytics, and Data Sharing Studio dashboards have since been retired, but the pattern remains active on the listed Studio pages.
Future dashboard-like Studio entry pages should use this documented pattern instead of creating page-local route-card variants.

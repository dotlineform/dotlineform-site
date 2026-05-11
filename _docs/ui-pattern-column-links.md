---
doc_id: ui-pattern-column-links
title: "Column Links Pattern"
added_date: 2026-05-05
last_updated: "2026-05-11"
parent_id: ui-catalogue
sort_order: 120
---
# Column Links Pattern

This composition pattern covers compact route-link column groups used on Studio dashboard and catalogue entry pages.

Live reference:

- [Column links pattern page](/studio/ui-catalogue/column-links/)

Current live examples:

- `/studio/catalogue/`
- `/studio/library/`
- `/studio/analytics/`
- `/studio/ui-catalogue/`

## Scope

Use this pattern when:

- a page is primarily routing the user into a small set of related work areas
- links naturally group into two or three short categories
- category headings add useful scan structure
- individual links do not need descriptions, counts, or cards

Do not use this pattern for:

- long navigation lists
- content previews
- repeated records with metadata
- command buttons
- link groups where every item needs explanatory text

## Anatomy

The pattern has three layers:

- `catalogueDashboardRoutes` for the column wrapper
- `catalogueDashboardColumn` for each labeled group
- `catalogueDashboardPills` for the compact route links

Use `catalogueDashboardRoutes--three` when a dashboard needs three peer route groups.

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

Current live pages use:

- `catalogueDashboardRoutes`
- `catalogueDashboardColumn`
- `catalogueDashboardPills`

Keep link labels short enough to fit the pill treatment.
If labels need supporting copy, move to a different pattern rather than stretching this one into a card grid.

## Migration Notes

This pattern was first reused by Catalogue and Library dashboards, then adopted by the Analytics dashboard and UI Catalogue index.
Future dashboard-like Studio entry pages should use this documented pattern instead of creating page-local route-card variants.

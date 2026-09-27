---
draft: false
doc_id: d-20260720-161656-1357d0
title: Site
added_date: "2026-07-20 16:16:56"
last_updated: "2026-09-03 21:25:23"
summary: Entry point for understanding, changing, previewing, validating, and planning the public dotlineform site.
parent_id: ""

---
# Site

`site/` is the tracked public website and GitHub Pages deploy root. The public catalogue is centred on `/series/`, the Works home reached from `/`.

Public Docs Viewer routes share parts of the site shell but remain documented under [Docs Viewer](Docs_Viewer.md). This section owns the public catalogue experience and the site-wide shell around it.

## Understand The Site

- [Site Overview](Site_Overview.md) — product surface, execution path, ownership, extension method, and weak spots.
- [Public Catalogue Design](Public_Catalogue_Design.md) — navigation, presentation, interaction, responsive behaviour, and frontend ownership.
- [Public Route Model](Public_Route_Model.md) — stable catalogue URLs and query-state rules.
- [Site Shell Runtime](Site_Shell_Runtime.md) — shared head, header, navigation, theme, footer, and asset-loading boundary.
- [Public Catalogue Data Flow](Public_Catalogue_Data_Flow.md) — runtime payloads read by each catalogue route.

## Change Site Content

- [Studio](Studio.md) owns catalogue authoring and maintenance.
- [Catalogue Architecture](Catalogue_Architecture.md) owns the source-to-public-projection boundary.
- [Catalogue Search](Catalogue_Search.md) owns the public catalogue search surface and index.

The public browser never writes catalogue source. Studio validates and changes canonical records, then its catalogue services rebuild the public projections consumed by Site.

## Operate The Site

- [Public Site Preview](Local_Setup_Public_Site_Preview.md) — serve the checked deploy tree locally and run deploy-root validation.
- [Site Consistency Audit](Site_Consistency_Audit.md) — check catalogue projections, routes, links, and media relationships.
- [Testing](Testing.md) — choose focused runtime, browser-boundary, or visual evidence.
- [GitHub Actions](GitHub_Actions.md) — public-site validation and deployment workflow.

## Code Authority

- `site/series/`, `site/works/`, `site/work-details/`, `site/recent/`, and `site/catalogue/search/` for tracked route shells
- `site/assets/js/catalogue/` for public catalogue routes, components, navigation, and shared helpers
- `site/assets/css/main.css` and `site/assets/css/catalogue.css` for the current presentation
- `site-tools/` for deploy-root validation and static preview tooling

Use code, config, generated payloads, and focused tests for exact current fields and behaviour. These documents provide the stable map.

## Plan Site Work

- [Planned Features](Planned_Features.md) defines the shared planning model.

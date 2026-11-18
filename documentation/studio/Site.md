---
draft: false
doc_id: d-20260720-161656-1357d0
title: Site
added_date: "2026-07-20 16:16:56"
last_updated: "2026-11-18"
summary: Entry point for understanding, changing, previewing, validating, and planning the public dotlineform site.
parent_id: ""

---
# Site

`site/` is the tracked public website and GitHub Pages deploy root. `/` directly hosts the public Docs Viewer, which reads the current Catalogue. The former `/analysis/` route is retired without a redirect or alias. The frozen historical catalogue remains under `/archive/`.

Start with [How the site fits together](../guide/How_The_Site_Fits_Together.md). [Docs Viewer](Docs_Viewer.md) covers the current public reader, including the active Catalogue. [Catalogue Archive](Catalogue_Archive.md) covers the separate frozen site and its routes, data and media.

## Understand The Site

- [Public Docs Route Shell](Public_Docs_Route_Shell.md) — the active public entry point and its boot path.
- [Site Shell Runtime](Site_Shell_Runtime.md) — page shell, theme and asset loading.

The previous Catalogue is documented in [Public Catalogue Design](Public_Catalogue_Design.md), [Public Route Model](Public_Route_Model.md), [Public Catalogue Data Flow](Public_Catalogue_Data_Flow.md) and [Catalogue Search](Catalogue_Search.md).

## Change Site Content

- [Studio](Studio.md) owns Catalogue authoring. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md#current-workflow) follows a change from Studio to Working and the publication queue.
- [Publish and deploy](../guide/Publish_And_Deploy.md) explains how prepared changes reach the repository, public media and GitHub Pages.

## Operate The Site

- [Public Site Preview](Local_Setup_Public_Site_Preview.md) — serve the checked deploy tree locally and run deploy-root validation.
- [Testing](Testing.md) — choose focused runtime, browser-boundary, or visual evidence.
- [GitHub Actions](GitHub_Actions.md) — public-site validation and deployment workflow.

## Code Authority

- `site/index.html` for the public entry point and Docs Viewer route shell
- `docs-viewer/` for canonical shared/public Docs Viewer runtime code, explicitly projected into `site/docs-viewer/` through `site-tools/config/site-code-update.json`
- `site/assets/data/catalogue/` and `site/assets/data/docs/catalogue/` for published Catalogue records and documents
- `site/archive/series/`, `site/archive/works/`, `site/archive/work-details/`, `site/archive/recent/`, and `site/archive/search/` for frozen historical catalogue route shells
- `site/archive/assets/js/catalogue/` for archived catalogue routes, components, navigation, and shared helpers
- `site/assets/css/main.css` for the current site shell; `site/archive/assets/css/main.css` and `site/archive/assets/css/catalogue.css` for archived presentation
- `site-tools/` for deploy-root validation and static preview tooling

Use code, config, generated payloads, and focused tests for exact current fields and behaviour. These documents provide the stable map.

## Plan Site Work

- [Planned Features](Planned_Features.md) defines the shared planning model.

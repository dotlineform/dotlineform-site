---
draft: false
doc_id: d-20260331-000000-6d51e9
title: Site Shell Runtime
added_date: "2026-03-31 00:00:00"
last_updated: "2026-10-15 18:09:30"
summary: Shared public head, header, navigation, theme, footer, asset loading, and catalogue versus Docs Viewer shell boundary.
parent_id: d-20260720-161656-1357d0
---
# Site Shell Runtime

The active site has a tracked Docs Viewer shell at `site/index.html` and a standalone `site/404.html`. The reusable public-route template is maintained separately. GitHub Pages serves the committed files directly. [Public Docs Route Shell](Public_Docs_Route_Shell.md)

## Public Static Shell Responsibilities

The tracked home shell supplies the public reader mounts and entrypoint. The viewer runtime owns current navigation, document presentation and controls. The 404 page keeps its own small stylesheet and theme-toggle script. [CSS Ownership](CSS_Ownership.md#owners)

## Theme Bootstrap

The active HTML shells set the saved theme in their heads before loading the main styles. Keeping that early read ahead of first paint avoids flashing the wrong palette. Both use the projected shared palette.

## Shared Asset Versioning

The tracked shells spell out their stylesheet and entrypoint URLs and cache tokens. Update the appropriate shell when its asset loading changes. [Public code projection](Run_Checks.md#docs-viewer-site-code-projection)

## Public Nav

The root opens Docs Viewer directly. The previous Catalogue has independent routes, HTML and assets under `site/archive/`; active shell changes leave that snapshot intact. [Catalogue Archive](Catalogue_Archive.md)

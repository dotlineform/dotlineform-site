---
draft: false
doc_id: d-20260613-115624-3d377c
title: Docs Viewer Public Route Shell Template
added_date: "2026-06-13 11:56:24"
last_updated: "2026-11-20"
summary: The tracked root public Docs Viewer shell, configuration ownership, and maintenance boundary.
parent_id: d-20260424-000000-50b63f
---
# Public Docs Route Shell

The active public reader is `/`, served directly by tracked [site/index.html](../../site/index.html). GitHub Pages serves the committed `site/` files without a deploy-time build. The reusable [route template](../../docs-viewer/templates/public-route/index.html) is separate; editing it does not rewrite the installed shell. The former `/analysis/` URL has no alias.

## Owner

Site owns the installed HTML shell and 404. Docs Viewer owns reader boot, navigation, controls and configuration. Browser controllers resolve query state and document targets. Python projects configured browser settings and prepares selected document output through its own Build/Publish workflows.

[Route configuration](../../docs-viewer/config/routes/docs-viewer-routes.json) declares the public URL/base as `/`, with a [public-safe route record](../../site/docs-viewer/config/routes/docs-viewer-public-routes.json). The internal `analysis` id selects that record; it does not define another URL. [Workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json) owns the public viewer base, and generated local/public browser settings expose the appropriate reader base. Document/media storage stays with those existing owners.

## Shell Contract

The shell loads the palette, reader and public report CSS, applies stored theme in its head before first paint, and mounts header controls and Main beneath the viewer root. Index and Info share a wrapper so the reader CSS can place them in one sticky column at tablet widths. It identifies the route and public configuration URL, starts ready/busy false, and loads the public entrypoint. Public composition excludes management/Import/Review runtime and local service URLs. The 404 uses the shared palette, its own stylesheet/theme script and a home link to the root. [Public entrypoint](../../docs-viewer/runtime/js/public/docs-viewer-public.js) · [Info panel](Info_Panel.md) · [404](../../site/404.html)

## Maintenance

[site-code-update.json](../../site-tools/config/site-code-update.json) is the sole canonical-to-public runtime inventory: shared/public JS, public browser configuration, three reader styles, selected SVGs and Search Field JS/CSS. Shared source-directory membership does not automatically make a file public. Other shared pickers/lists and local Manage/Review styles remain outside the projection.

For a represented runtime/style/artwork change, edit canonical source, update the inventory if membership changes, run `bin/site-code-update`, inspect the exact tracked `site/` delta, then run `bin/site-code-update --check` and `bin/site-validate`. Adding a public CSS mask also requires its SVG in that explicit subset. Shell HTML and cache tokens are maintained directly; the template does not own the installed shell's version strings.

When moving a public route, align shell, route records, workspace/browser bases, 404 recovery and required-file inventory. Reload local apps to check canonical changes and use `bin/site-preview` to read the tracked public projection. Runtime projection and document Publish have separate owners; [Publish and Deploy](../guide/Publish_And_Deploy.md) explains when each is needed. Git commit, push and deployment remain explicit actions.

The legacy Catalogue archive was removed; the current live reader supplies the design reference. [Catalogue Archive](../deliveries/Catalogue_Archive.md#retirement-and-r2-cleanup) preserves its historical design, Git recovery point and dedicated-media deletion evidence.

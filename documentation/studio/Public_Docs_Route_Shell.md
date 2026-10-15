---
draft: false
doc_id: d-20260613-115624-3d377c
title: Docs Viewer Public Route Shell Template
added_date: "2026-06-13 11:56:24"
last_updated: "2026-10-15 18:09:30"
summary: The tracked root public Docs Viewer shell, configuration ownership, and maintenance boundary.
parent_id: d-20260424-000000-50b63f
---
# Docs Viewer Public Route Shell Template

The sole public Docs Viewer route is `/`, served directly by the tracked `site/index.html` shell. The shell mounts the public viewer without a redirect or intermediate page. The former `/analysis/` route is removed without an alias; old URLs are intentionally unsupported.

The shell is part of the canonical GitHub Pages deploy root and is maintained directly. It is not generated during deploy. The reusable `docs-viewer/templates/public-route/index.html` template remains separate from this installed shell; editing the template does not rewrite `site/index.html`.

## Owner

Site owns the tracked HTML shell and shared presentation. Docs Viewer owns public runtime boot, reader behavior and configuration. The browser resolves document query state and builds links using the configured viewer base. Python parses workspace configuration and prepares/publishes the configured files; moving the reader route requires no document rendering or media transfer.

`docs-viewer/config/routes/docs-viewer-routes.json` declares the public route with `route_path` and `viewer_base_url` set to `/`. Its public-safe record is maintained in `site/docs-viewer/config/routes/docs-viewer-public-routes.json`. The shell's `data-route-id="analysis"` matches the existing registry identity; that internal ID does not define a second URL or preserve the removed route.

`docs-viewer/config/workspace/docs-workspace.json` owns `public_viewer_base_url: "/"`. The local browser configuration exposes that public destination while retaining `/docs/` as its own reader base. The canonical public browser configuration uses `/` as its workspace viewer base and is projected into `site/` through `site-tools/config/site-code-update.json`.

Documents, collection manifests, Search and R2 media retain their existing storage locations. Root-independent document links and `docs-media:` identities resolve through the configured reader route and media root. Static-site validation checks the root shell and required public inputs without rendering them.

## Shell Contract

The installed shell includes:

- public site frame and base CSS
- Docs Viewer theme, reader and report CSS beneath `/docs-viewer/static/css/`
- Docs Viewer root with `data-route-id`
- `data-route-config-url="/docs-viewer/config/routes/docs-viewer-public-routes.json"`
- header controls mount with `data-docs-viewer-header-controls-mount`, `data-enable-search`, `data-search-placeholder` and `data-search-aria-label`
- Index, Main and Info panel mounts
- public runtime entrypoint: `/docs-viewer/runtime/js/public/docs-viewer-public.js`

Public access is controlled by route configuration and runtime composition. The shell loads only the public entrypoint and permitted shared/runtime report features. It exposes no management/import runtime, management CSS, localhost service URLs or source-editing/import/settings controls.

## Maintenance

Keep the shell, canonical/public route records, workspace/browser viewer bases, 404 home link and required-file inventory aligned when changing the public route. Project represented canonical files with `bin/site-code-update`, inspect the tracked `site/` delta, then run `bin/site-code-update --check` and `bin/site-validate`. Tests and browser checks follow the separately agreed [Testing](Testing.md) policy; a shell change does not automatically authorize test maintenance or browser automation. Git commit, push and public deployment remain explicit actions.

## Root Route Review

The 15 October 2026 move installs the existing reader shell at `/`, removes the homepage meta refresh and old route file, updates public URL configuration and points 404 recovery home. The shell's existing asset-version mechanism uses the new `docs-viewer-root-20261015a` token so returning browsers request the new route configuration instead of reusing the old versioned URL. The workspace parser now accepts the valid root directory URL while retaining its existing safe-path checks for non-root directories, rejection of authority/query/fragment forms and management-route exclusion. No alias, fallback, extra scan, document rebuild, media transfer or recovery machinery was added. The existing internal route ID and presentation class remain independent of the public URL.

Distinct source/diff and Redundancy And Defensive Behavior Review found and corrected the retained old asset-version token. No additional runtime changes were necessary: route selection and link construction already support `/`, the server only needed to accept that configured directory URL, and existing static validation already maps `/` to `index.html`. Focused Python lint/compilation, site-code projection/check and site validation passed. Read-only production configuration/projection diagnostics resolved the public base to `/` and Manage to `/docs/`; the existing browser URL builder produced root links for the actual configured default and both saved collection selections. No tests were added, changed or run, and browser interaction remains a manual review. This source change does not deploy itself.

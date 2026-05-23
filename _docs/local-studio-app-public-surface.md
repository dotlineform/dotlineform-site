---
doc_id: local-studio-app-public-surface
title: Public Published Surface
added_date: 2026-05-22
last_updated: 2026-05-23
parent_id: local-studio-app
sort_order: 1100
published: true
viewable: true
---
# Public Published Surface

This document defines the current dotlineform.com build surface while Studio is being separated from Jekyll hosting.

`public` means served on dotlineform.com.
It does not mean private repository access.
Canonical source data may remain in a public repo while still staying out of public runtime projections.

For the broader source/projection boundary, see [Projection Contract](/docs/?scope=studio&doc=data-models-projection-contract).

## Public Output

The public Jekyll build should include:

- home, about, recent, palette, and other public site pages
- public catalogue pages for works, series, work details, and moments
- public catalogue JSON projections under `assets/data/` and per-record public payloads
- public catalogue search output under `assets/data/search/catalogue/`
- public media and thumbnail assets that are intentionally served by the site
- shared public JavaScript under `assets/js/`
- shared public CSS under `assets/css/`
- Docs Viewer runtime files under `assets/docs-viewer/`
- public Docs Viewer browser config at `assets/docs-viewer/data/docs-viewer-public-config.json`
- public read-only Library route at `/library/`
- public read-only Analysis route at `/analysis/`
- generated Library docs payloads under `assets/data/docs/scopes/library/`
- generated Analysis docs payloads under `assets/data/docs/scopes/analysis/`
- generated Library docs search under `assets/data/search/library/`
- generated Analysis docs search under `assets/data/search/analysis/`

## Local-Only Output

The public Jekyll build should not include:

- `/studio/` routes
- `/docs/` local management route
- Studio app assets under `assets/studio/`
- generated Studio docs payloads under `assets/data/docs/scopes/studio/`
- generated Studio docs search under `assets/data/search/studio/`
- canonical catalogue source data under `assets/studio/data/catalogue/`
- Studio catalogue lookup data under `assets/studio/data/catalogue_lookup/`
- local scripts, tests, logs, or var output
- footer or nav links that point public users to `/studio/` or `/docs/`

## Current Enforcement

Public Jekyll builds use `_config.yml`.
That config excludes local-only Studio routes, local-management docs routes, Studio app assets, and Studio docs payload/search outputs.
It also points Docs Viewer routes at the public browser config, which includes only `library` and `analysis` scopes.

Local Studio development uses `bin/local-studio`, which serves Studio routes and Docs Viewer management directly through the local app server.
Public Jekyll preview/build remains on `_config.yml` and does not expose Studio management surfaces.

The public build surface can be checked after a public build with:

```bash
./scripts/checks/audit_public_build_surface.py --site-root /tmp/dlf-jekyll-build
```

## Public Read-Only Docs Viewer Rule

`/library/` and `/analysis/` are intentionally public read-only Docs Viewer installs.
They should keep using public generated docs payloads and public generated docs search.

`/docs/` is local management infrastructure.
It should not be published unless a separate curated read-only public docs install is explicitly defined later.

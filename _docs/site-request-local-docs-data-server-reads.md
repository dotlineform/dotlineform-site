---
doc_id: site-request-local-docs-data-server-reads
title: Local Docs Data Server Reads Request
added_date: "2026-05-03 21:56"
last_updated: "2026-05-04"
ui_status: "done"
parent_id: change-requests
sort_order: 25
---
# Local Docs Data Server Reads Request

Status:

- implemented

## Summary

This change request proposes moving local docs-viewer reads for generated docs and docs-search JSON through the localhost docs-management server while `bin/dev-studio` is running.

The goal is to preserve automatic local docs refresh behavior without making Jekyll watch every generated docs/search asset rewrite.

This follows the same local-runtime direction already used for mutable Catalogue editor data: local Studio workflows should read volatile working data through a local allowlisted server instead of through Jekyll-served static files when that static read path causes avoidable regeneration churn.

## Problem

The previous [Docs Build Incremental Request](/docs/?scope=studio&doc=site-request-docs-build-incremental) reduced docs churn by making docs payload writes incremental and by making the live docs watcher observe source roots rather than generated outputs.

That fixed the docs watcher loop, but it did not fully remove Jekyll watcher churn.

Current local behavior:

- a source doc changes under `_docs/`, `_docs_library/`, or `_docs_analysis/`
- `docs_live_rebuild_watcher.py` correctly rebuilds the matching generated docs payloads and docs-search index
- Jekyll still sees changed files under `assets/data/docs/scopes/...` and `assets/data/search/...`
- Jekyll performs its own regeneration pass even though those JSON files are runtime data, not Liquid source

Newly visible noise:

- Python test runs can create `tests/python/__pycache__/*.pyc`
- Jekyll currently sees those files and regenerates the site even though they have no site-runtime role

Observed effect:

- local no-op or near-no-op docs work can still trigger a Jekyll regeneration taking around 30 seconds
- the slow pass happens after the docs watcher has already done the useful docs/search rebuild

## Goal

Keep the local docs workflow live and automatic while reducing the files Jekyll needs to watch.

Desired outcome:

- docs source edits still rebuild same-scope docs payloads and same-scope docs search
- local docs viewer and Studio docs routes can read the rebuilt generated data immediately
- Jekyll does not regenerate just because generated docs/search JSON changed
- Jekyll does not regenerate because Python test cache files changed
- public/static builds remain unchanged and continue to serve generated JSON assets normally

## Spec

### Local Generated-Data Read Boundary

Add read-only docs-management endpoints for generated docs data.

Likely endpoints:

- `GET /docs/generated/index?scope=<scope>`
- `GET /docs/generated/payload?scope=<scope>&doc=<doc_id>`
  - implemented endpoint also accepts `doc_id=<doc_id>`
- `GET /docs/generated/search?scope=<scope>`

Supported scopes should match the docs-viewer scopes already supported by the generated payloads:

- `studio`
- `library`
- `analysis`

Endpoint behavior:

- resolve only allowlisted generated docs/search paths
- return JSON with `cache-control: no-store`
- never expose arbitrary filesystem paths
- never write source files or generated files
- return clear 404 or validation errors for missing scope, missing doc, or unsupported scope
- serve indexed non-viewable payloads for local manage-mode workflows; public visibility remains enforced by the generated index and search data

### Docs Viewer Runtime Behavior

When the local docs-management server is available, local docs-viewer reads should prefer server endpoints for:

- scope index JSON
- per-doc payload JSON
- scope search index JSON

The runtime should still support the existing static asset URLs for public/non-local use.

The local server-read path should be explicit and capability-driven:

- probe docs-management capabilities
- prefer server reads when the capability exists
- keep public/static docs routes functional without the local server
- avoid falling back to stale static generated data in workflows that explicitly require local write/server availability

### Jekyll Watch Exclusion

After server reads are in place, `bin/dev-studio` can use a local Jekyll config overlay that excludes generated docs/search data from the Jekyll watch surface.

Candidate exclusions for the local dev overlay:

- `assets/data/docs/scopes/`
- `assets/data/search/studio/`
- `assets/data/search/library/`
- `assets/data/search/analysis/`
- `tests/`

The `tests/` exclusion can be done earlier because it has no public site role.

The generated docs/search exclusions should wait until local server reads are available and verified.

### Public Build Boundary

Normal Jekyll build and public hosting behavior should not depend on the docs-management server.

The generated JSON files remain the public/static data contract for:

- `/docs/`
- `/library/`
- any future static docs-viewer route that uses the generated docs payloads

The server-read path is a local development optimization and local Studio runtime contract.

## Open Questions

- Should the docs viewer enable server reads only when `mode=manage`, or for all localhost docs-viewer reads while the server is available?
- Should `analysis` use the same generated-data endpoints immediately, or should the first implementation cover only `studio` and `library`?
- Should the local server read endpoint return raw generated JSON unchanged, or wrap it with metadata such as `ok`, `scope`, and `source`?
- Should generated docs/search exclusions live in `_config.yml`, or should `bin/dev-studio` pass a separate local-only Jekyll config overlay?
- Should the docs viewer display a small local-data warning if a server read fails and it falls back to static assets during local development?

Resolved:

- Server reads are enabled for all docs-viewer reads when the configured localhost docs-management server advertises generated-data read capability, not only in `mode=manage`.
- `studio`, `library`, and `analysis` use the same generated-data endpoints.
- Generated-data endpoints return the raw generated JSON unchanged.
- `bin/dev-studio` uses `_config.dev-studio.yml` as a local-only Jekyll overlay; normal builds keep `_config.yml`.
- The viewer falls back to static assets only when the local server capability probe is unavailable. Once generated-data reads are advertised for the scope, failed server reads surface as load errors rather than silently using stale static data.

## Task List

### Task 1. Exclude Test Artifacts From Jekyll

Status:

- implemented

Add `tests/` to the Jekyll exclusion set.

Reason:

- Python test caches and test fixtures are not site input
- excluding them removes a simple source of pointless local regeneration

Benefit:

- immediate reduction in noisy Jekyll watch events after Python checks

Risk:

- low; public site builds should not depend on `tests/`

Status note:

- implemented by adding `tests/` to `_config.yml` `exclude`
- this covers Python test caches and fixtures only; generated docs/search exclusions remain deferred until local server reads are available

### Task 2. Add Read-Only Generated Docs Endpoints

Status:

- implemented

Add allowlisted docs-management endpoints for generated docs index, generated per-doc payloads, and generated docs-search indexes.

Implemented endpoints:

- `GET /docs/generated/index?scope=<scope>`
- `GET /docs/generated/payload?scope=<scope>&doc_id=<doc_id>`; `doc=<doc_id>` is also accepted
- `GET /docs/generated/search?scope=<scope>`

Compatibility aliases remain for the earlier management reload paths:

- `GET /docs/index?scope=<scope>`
- `GET /docs/doc?scope=<scope>&doc_id=<doc_id>`
- `GET /docs/search?scope=<scope>`

Reason:

- local docs viewer needs a non-Jekyll read path before generated JSON can be removed from the local Jekyll watch surface

Benefit:

- creates the same kind of explicit local runtime boundary already used for mutable Catalogue data

Risk:

- endpoint path validation must stay strict so a browser request cannot read arbitrary local files

### Task 3. Teach Docs Viewer To Prefer Local Server Reads

Status:

- implemented

Update the docs viewer runtime so localhost/server-capable sessions can read generated docs data through the docs-management server.

Implementation note:

- the viewer probes `GET /capabilities`
- server reads are used when `capabilities.generated_data_reads` and the current scope's generated read flag are true
- index, payload, and search fetches use the generated endpoints with `cache: "no-store"`
- static generated JSON remains the fallback when no local server capability is available

Reason:

- generated docs/search data should remain fresh without forcing Jekyll to watch and regenerate from those files

Benefit:

- preserves the automatic local refresh model while reducing Jekyll work

Risk:

- docs viewer is shared between local and public routes, so capability detection and fallback behavior need to be clear and narrow

### Task 4. Add A Local Jekyll Watch Overlay

Status:

- implemented

Update `bin/dev-studio` to start Jekyll with a local-only config overlay that excludes generated docs/search data once server reads are verified.

Implementation note:

- `bin/dev-studio` defaults `JEKYLL_CONFIG` to `_config.yml,_config.dev-studio.yml`
- `_config.dev-studio.yml` carries the base exclusions plus generated docs/search exclusions
- public builds that use `_config.yml` alone still include generated docs/search JSON

Reason:

- the repo should not remove public generated JSON from normal builds, but local Jekyll serve does not need to watch it once the viewer reads through the local server

Benefit:

- avoids the expensive Jekyll regeneration wave after docs watcher output writes

Risk:

- if the overlay is too broad, local pages that still read static generated data may appear stale until the route is updated

### Task 5. Verify Live Local Behavior

Status:

- implemented

Verify the full local loop:

- edit one Studio source doc
- confirm the docs watcher rebuilds same-scope docs and targeted search
- confirm the docs viewer reads the updated index/payload/search data through the local server
- confirm Jekyll does not regenerate because generated docs/search JSON changed
- run Python import/export tests and confirm `tests/python/__pycache__` changes do not trigger Jekyll regeneration

Verification performed:

- focused docs-management tests cover generated-read capabilities, indexed payload reads, non-indexed payload rejection, payload path validation, and `Cache-Control: no-store`
- `assets/js/docs-viewer.js` passes `node --check`
- docs profile checks and browser smoke were run after implementation; see the current task close-out for exact commands

Reason:

- this request is about local workflow behavior, so command-level checks alone are not enough

## Related Docs

- [Docs Build Incremental Request](/docs/?scope=studio&doc=site-request-docs-build-incremental)
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

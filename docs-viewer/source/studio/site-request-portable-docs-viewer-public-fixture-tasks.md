---
doc_id: site-request-portable-docs-viewer-public-fixture-tasks
title: Portable Docs Viewer Public Fixture Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: urgent
parent_id: site-request-portable-docs-viewer
sort_order: 1010
viewable: true
---
# Portable Docs Viewer Public Fixture Tasks

This is the tracker for the public read-only fixture proof from [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer).

The slice should prove the static/read-only Docs Viewer contract outside dotlineform's incidental routes and generated data.
It should create or update an ignored local fixture, likely under `var/`, then serve and smoke-test it as a small outside host project.

This slice should prove route config, shell mounts, runtime assets, viewer CSS, UI text, generated docs payloads, generated search payloads, search/recent behavior, document routing, metadata info, and absence of management-only assets.
It should not implement local manage mode, backend writes, source editing, semantic-reference views, activity views, third-party visualization modules, plugin architecture, or a package-manager distribution story.

### steer (to be reviewed)

- Prefer an ignored fixture under `var/portable-docs-viewer-public/` unless inventory shows a better ignored local fixture home.
- Keep the fixture minimal: one public read-only route, one docs scope, a small parent/child docs tree, generated docs payloads, generated search payload, route config, UI text, runtime assets, and CSS.
- Copy or generate fixture files through a documented script or helper where practical so the fixture can be recreated consistently.
- Treat the fixture as an outside host project: it should not depend on dotlineform route shell paths, generated Studio payloads, semantic-reference data, management CSS, management JS, or local service endpoints.
- Use the same app/runtime/config shape as dotlineform public routes where possible, rather than creating a second fixture-only boot path.
- Keep management and write behavior out of this slice. A portable local manage fixture should be a later child tracker after the read-only contract is proven.
- Update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) only if the verified fixture changes the current copy/setup instructions.
- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for shared runtime files.
- This slice is fixture/proof work, not a feature layer.
- Keep public read-only portability first-class: one outside-project fixture should prove the viewer can boot and navigate without dotlineform incidental routes.
- Keep `docs-viewer/runtime/js/docs-viewer.js` as the stable public entrypoint.
- Keep route config and access projection as the app-shell gate; the fixture must avoid management-only CSS, JavaScript, shell markup, and service URLs.
- Keep generated docs/search payloads static and fixture-local.
- Keep backend reachability, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, rebuild behavior, and generated-data capability checks out of the fixture.
- Keep local manage fixture work separate.

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- Syntax checks:
  - JavaScript syntax checks for any changed runtime/fixture helper modules
  - Python syntax check for any changed fixture creation or smoke scripts
  - Ruby syntax check for any changed generator/build scripts
- Fixture creation verification:
  - create or refresh the ignored fixture under `var/portable-docs-viewer-public/`
  - verify expected fixture files exist without copying management-only CSS/JS or local service config
  - verify fixture route config points only at fixture-local public generated data and UI text
- Focused fixture smoke:
  - serve the fixture through a temporary local static server
  - verify route boot
  - verify default document rendering
  - verify document navigation/history
  - verify inline search
  - verify recently-added list
  - verify metadata info panel and info toolbar do not break
  - verify bookmark support does not block route boot
  - verify management-only shell, CSS, JS, mode, and service URLs are absent
- Regression checks when shared runtime, shell, route config, CSS, or generated-data assumptions change:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Docs-only follow-through when source docs change:
  - review generated docs payload status; let the docs watcher update generated payloads if it is running and do not revert watcher output

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory the current portable public install requirements from `docs-viewer/source/studio/docs-viewer-portable-setup.md`, `docs-viewer/config/routes/docs-viewer-routes.json`, `docs-viewer/config/defaults/docs-viewer-public-config.json`, `docs-viewer/config/ui-text/ui-text.json`, `_includes/docs_viewer_shell.html`, public route adapters, runtime assets, CSS assets, generated docs payloads, and generated search payloads. Deliverable: short implementation note listing the minimal public fixture copy set and what stays out of the fixture. |
| 2 | planned | Decide the ignored fixture location and file layout, expected to be `var/portable-docs-viewer-public/`. Document the fixture route path, scope id, route config path, generated docs path, generated search path, UI text path, runtime path, and CSS path. |
| 3 | planned | Create or update a repeatable fixture creation helper where practical. It should populate the ignored fixture from repo-owned runtime/config assets plus a tiny fixture docs/search dataset without using dotlineform generated Studio/Library/Analysis payloads as the source of truth. |
| 4 | planned | Add the minimal public route shell for the fixture. It should expose app mounts, route id/config URL, public CSS links, and the stable Docs Viewer entrypoint without management shell mounts or management CSS/JS. |
| 5 | planned | Add fixture-local route config and browser config. Preserve the app-shell route-config shape and public access projection while avoiding management mode, management service URLs, generated-read service URLs, and scope switching unless the fixture explicitly needs them. |
| 6 | planned | Add fixture-local generated docs payloads for a small parent/child tree. Include enough metadata to exercise default document loading, tree navigation, recently-added ordering, metadata info, and basic document content rendering. |
| 7 | planned | Add fixture-local generated search payloads. Include enough entries to exercise inline search result rendering, result links, no-result status, and recent/search route transitions. |
| 8 | planned | Add or update a focused portable public fixture smoke. Cover route boot, default document rendering, document navigation/history, inline search, recently-added list, metadata info panel, info toolbar continuity, bookmark support non-blocking behavior, and absence of management-only shell/assets. |
| 9 | planned | Keep local manage mode out of this slice. Do not copy management CSS/JS, management shell markup, local service URLs, backend capability checks, source write endpoints, imports, settings, scope lifecycle, delete/archive/move behavior, rebuild behavior, or generated-data service reads into the public fixture. |
| 10 | planned | Run focused fixture smoke and the proportional public Docs Viewer regression checks. Use elevated localhost/browser permissions for fixture and browser smokes when needed. |
| 11 | planned | Update owning docs after implementation: this tracker, the portable Docs Viewer request, Docs Viewer Portable Setup if setup instructions change, the app-shell request if the infrastructure sequence status changes, and any fixture/smoke docs introduced by the slice. |
| 12 | planned | Create or update the structured docs-log entry for this slice and record the entry id in this tracker. |

The closeout for this slice should confirm:

- the fixture lives under an ignored local path and can be recreated consistently
- the fixture uses the same public app/runtime/config shape as dotlineform public Docs Viewer routes
- the fixture boots without dotlineform route shells, generated Studio/Library/Analysis payloads, semantic references, or management assets
- route boot, document rendering, document navigation/history, inline search, recently-added, metadata info, info toolbar, and bookmark support work in the fixture
- management-only shell markup, CSS, JavaScript, mode handling, and service URLs are absent
- local manage fixture work remains deferred to a later tracker
- any hidden portability assumptions found by the fixture are documented as follow-up tasks

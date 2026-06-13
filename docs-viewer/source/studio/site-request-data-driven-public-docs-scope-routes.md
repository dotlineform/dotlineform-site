---
doc_id: site-request-data-driven-public-docs-scope-routes
title: Public Scope Lifecycle Site Retarget Request
added_date: 2026-06-12
last_updated: 2026-06-13
ui_status: done
parent_id: change-requests
viewable: true
---
# Public Scope Lifecycle Site Retarget Request

Status:

- done

## Summary

Retarget the existing Docs Viewer New Scope and Delete Scope actions so public read-only scopes work with `site/` as the canonical static deploy root.

The lifecycle actions already know how to create scope source docs, scope config, generated payloads, and scope manifests.
This request is not a new portable packaging feature.
It is the migration needed to replace the retired Jekyll Markdown route stub with the current `site/` route shell and public route config model.

For this repository, `site/` is the checked-in public deploy root.
Public Docs Viewer route shells are canonical static HTML files under `site/`, and the GitHub Pages workflow validates and uploads `site/` directly.
The lifecycle action should create or delete those tracked static files as source changes, not through a deploy-time build process.

## Context

The original public-readonly scope lifecycle was shaped by installing into a Jekyll site.
That is no longer the site model.
After the static-site migration, the repo-local target is `site/`.

The current dotlineform public site does not render public Docs Viewer route shells through a build step.
`site/library/index.html` and `site/analysis/index.html` are tracked static HTML route shells.
They load:

- `/docs-viewer/runtime/js/public/docs-viewer-public.js`
- `/docs-viewer/static/css/docs-viewer.css`
- `/docs-viewer/config/routes/docs-viewer-public-routes.json`
- public generated docs and search payloads under `/assets/data/docs/scopes/...` and `/assets/data/search/...`

The Docs Viewer runtime JavaScript ownership split also changed which files a public route shell may reference.
Public routes load site-owned runtime files under:

- `site/docs-viewer/runtime/js/public/`
- `site/docs-viewer/runtime/js/shared/`

Local-only management, import, and report modules live under `docs-viewer/runtime/js/` and are not part of public route shells.

The Docs Viewer New Scope lifecycle path still contains a retired public-route assumption: for public read-only scopes it plans and writes a Markdown route stub under the requested public route path.
That was appropriate for the previous Jekyll route model, but it is wrong for `site/`.
New Scope public-readonly creation is currently disabled until this path is retargeted.

## Problem

Public-readonly scope creation and deletion are blocked because the existing lifecycle actions still target the retired route model.

The current repo has three stale lifecycle assumptions:

- the old Jekyll/Liquid route stub model is retired
- dotlineform public Docs Viewer routes are canonical checked-in HTML files under `site/`
- New Scope public-readonly apply still has a legacy Markdown route-stub implementation path, now blocked

The existing New Scope action should create the same kind of scope files it already creates, but for public-readonly mode it must now also create the checked-in `site/<route>/index.html` shell and update the public route config.
The existing Delete Scope action should remove user-created public route records and tracked public route/output files owned by that scope.

This is a lifecycle retargeting problem, not a new static-site framework.

## Goals

- Make the existing New Scope public-readonly preview/apply work with `site/`.
- Make the existing Delete Scope action remove user-created public `site/` route and payload files safely.
- Replace legacy Markdown route stub creation with tracked static HTML route shell creation.
- Keep the public route shell small and route-specific.
- Keep route behavior in existing Docs Viewer config records.
- Ensure public scope lifecycle write sets clearly separate:
  - source docs
  - scope config
  - route config
  - working generated outputs
  - published public snapshots
  - canonical static route HTML under `site/`
- Preserve manage-mode scope creation behavior.
- Preserve public read-only behavior with no management assets, backend probes, or local write capability.
- Keep existing Library and Analysis public routes working during the transition.

## Non-Goals

- Do not generate Python scripts or Python route entries from the New Scope action.
- Do not reintroduce Jekyll, Liquid route stubs, or persistent Markdown public route files.
- Do not reintroduce a dotlineform public-site builder or copy step.
- Do not change public Docs Viewer runtime behavior unless required by the route-config refactor.
- Do not redesign Docs Viewer scope storage or workspace mounting; that belongs to the workspace-mount architecture request.
- Do not make every Docs Viewer scope public by default.
- Do not introduce a general plugin framework for arbitrary host behavior.
- Do not include local-only Docs Viewer management, import, or report runtime modules in public route shells.
- Do not add compatibility aliases for old flat Docs Viewer runtime URLs.
- Do not define an external Docs Viewer package format for other repositories.
  External packaging would need to include the site-owned public runtime, CSS, config, and payloads, but that is separate from this repo-local lifecycle retargeting request.

## Current Design Baseline

`site/` is the canonical public deploy root.
The public-site workflow runs static validation and uploads `site/`; it does not build or copy public artifacts.

Current public Docs Viewer routes:

- `site/library/index.html`
- `site/analysis/index.html`

Current public route registry:

- `site/docs-viewer/config/routes/docs-viewer-public-routes.json`

Current public runtime entrypoint:

- `site/docs-viewer/runtime/js/public/docs-viewer-public.js`

Current public/shared runtime modules:

- `site/docs-viewer/runtime/js/public/`
- `site/docs-viewer/runtime/js/shared/`

Current public generated payload roots:

- `site/assets/data/docs/scopes/<scope>/`
- `site/assets/data/search/<scope>/index.json`

The public route shell has a small static contract:

- a Docs Viewer root element
- `data-route-id`
- `data-route-config-url="/docs-viewer/config/routes/docs-viewer-public-routes.json"`
- public Docs Viewer CSS
- public Docs Viewer runtime entrypoint
- header controls mount attributes:
  - `data-docs-viewer-header-controls-mount`
  - `data-enable-search`
  - `data-search-placeholder`
  - `data-search-aria-label`

The route registry record then supplies scope, default document, viewer base URL, public payload URLs, UI config URLs, and panel settings.

## Design Direction

New public Docs Viewer scopes should be installed by the existing New Scope action creating a small repo-local file set and updating existing config.

The route install should create one new public route shell:

- `site/<route>/index.html`

It should update existing config records rather than create new code paths:

- Docs Viewer scope config
- Docs Viewer public route config

It should also create the scope's normal source and payload roots:

- source root under `docs-viewer/source/<scope>/`
- default source doc under `docs-viewer/source/<scope>/<default-doc-id>.md`
- working generated docs/search roots under `docs-viewer/generated/`
- published public docs root under `site/assets/data/docs/scopes/<scope>/`
- published public default by-id doc payload under `site/assets/data/docs/scopes/<scope>/by-id/<default-doc-id>.json` after build/publish
- published public search index under `site/assets/data/search/<scope>/index.json` when inline search is enabled

The action should keep the existing behavior of creating the public docs payload folder and default doc material needed for a new scope to load.

New public Docs Viewer route shells should use a creation-time route shell template.

The lifecycle flow should render a single canonical template into the new tracked route shell, for example:

- template: `docs-viewer/templates/public-route/index.html`
- output: `site/<route>/index.html`

After creation, the output HTML is a normal tracked `site/` file and part of the canonical deploy root.
It is not regenerated during deploy, and the public-site workflow still only validates and uploads `site/`.

The template is Docs Viewer-owned, not site-tools-owned.
It belongs under `docs-viewer/` because Docs Viewer management owns public scope creation, Docs Viewer route config defines what the shell loads, and the Docs Viewer runtime consumes the shell attributes and mount points.
Static-site validation is a separate deploy check; it should not own the source template or drive New/Delete Scope behavior.

The route shell template should own shared public Docs Viewer shell structure:

- site document frame needed for a dotlineform public page
- Docs Viewer root element and mount points
- public Docs Viewer stylesheet
- public Docs Viewer runtime entrypoint
- required route-shell `data-*` attributes
- no management CSS, management runtime, import runtime, report runtime, localhost service config, or write-capable controls

The creation flow should inject only route-specific shell values:

- page title
- body or nav active section value, if needed
- `data-route-id`
- route-specific search placeholder and aria label, if these remain shell-owned instead of route-config-owned

The route shell `data-*` contract should preserve what `/library/` and `/analysis/` already use:

- `data-route-id="<route-id>"`
- `data-route-config-url="/docs-viewer/config/routes/docs-viewer-public-routes.json"`
- `data-docs-viewer-header-controls-mount`
- `data-enable-search="true"`
- `data-search-placeholder="search <label>"`
- `data-search-aria-label="Search <Label>"`

Before implementation relies on that list, verify that each attribute is still read by the public Docs Viewer runtime.
If any current attribute is dead, remove it from the template and current installed route shells in the same retargeting change rather than preserving dead markup.

Scope and route behavior should stay in data/config records, not in copied shell logic.
The route registry should own default scope, default document, viewer base URL, payload URLs, UI config URLs, and panel settings.

Validation should prevent drift between installed public route shells and the canonical shell contract.
It should check the required shell structure and URLs across all public Docs Viewer route files rather than depending on reviewer memory.
Validation is also the right place to reject accidental management, import, or report runtime references in public route shells.

Copying an existing installed route shell, such as `site/library/index.html`, should be treated as a manual fallback only.
It should not be the documented lifecycle contract because it creates independent shell forks immediately.

If the public route shell contract changes later, maintenance tooling may update installed tracked route shells from the template as an explicit source edit.
That is still not a deploy build step.

## Implementation Decisions

The lifecycle retarget made these ownership decisions:

- Scope deletion removes public route records and canonical `site/` route shells for user-created public scopes.
- Scope deletion removes public docs/search payloads owned by the deleted scope.
- Route-specific search labels remain template inputs for now, matching the current installed public route shell contract.
- Public management access remains route-config behavior, not a static `data-allow-management="false"` shell attribute.

## Task Tracker

| Task | Status | Description |
| --- | --- | --- |
| 1 | done | Audited the existing New Scope and Delete Scope public-readonly paths and recorded the current file plan in this request. |
| 2 | done | Verified current public route-shell `data-*` readers. `data-allow-management="false"` had no public runtime reader, so it was removed from current public route shells and the template contract. |
| 3 | done | Added the canonical public route shell template at `docs-viewer/templates/public-route/index.html`. |
| 4 | done | Retargeted New Scope public-readonly preview/apply to render the template into `site/<route>/index.html` instead of creating a Markdown route stub. |
| 5 | done | Retargeted New Scope public-readonly preview/apply to update existing public route config registries for the new route. |
| 6 | done | Preserved creation of source root, default source doc, working generated roots, public docs payload root, and public search payload when enabled, including `site/assets/data/docs/scopes/<scope>/` and default doc material. |
| 7 | done | Retargeted Delete Scope to remove user-created public route config records, `site/<route>/index.html`, and public docs/search payloads owned by the scope. |
| 8 | deferred | Optional bulk refresh tooling for existing tracked route shells was not needed for the lifecycle retarget. The template renderer is available for New Scope creation. |
| 9 | done | Updated stable docs and route lifecycle tests. |

## Implementation Result

The existing New Scope and Delete Scope lifecycle actions now support public-readonly scopes against the `site/` static deploy root.

New Scope public-readonly now:

- accepts `publishing_mode: "public_readonly"`
- writes a tracked static route shell at `site/<route>/index.html`
- renders that shell from `docs-viewer/templates/public-route/index.html`
- updates existing Docs Viewer route registries for the new public route
- keeps source/default-doc/generated-output creation behavior
- syncs the initial rebuilt docs/search payloads into the configured public `site/assets/data/...` publish roots

Delete Scope now allows user-created public scopes and removes:

- the user-created public route shell
- the user-created public route records
- source docs and generated outputs recorded in the scope manifest
- public docs/search payloads owned by the scope

The public route shell contract now relies on route config for management access.
The dead public `data-allow-management="false"` attribute was removed from `site/library/index.html`, `site/analysis/index.html`, and the new template.

## Completed Verification

- Focused lifecycle and service tests: `$HOME/miniconda3/bin/python3 -m pytest -q docs-viewer/tests/python/test_docs_management_service.py docs-viewer/tests/python/test_docs_viewer_service.py`.
- Result: `62 passed`.
- Syntax check: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/services/docs_scope_manifest.py`.
- Static site validation: `bin/site-validate`.
- Result: `Site validation passed: 47 required files; 9 required directories; 44 Docs Viewer runtime modules`.
- Public browser smoke: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root site`.
- Result: public Docs Viewer read-only OK for `/library/` and `/analysis/`.

## Verification Expectations

- Focused tests for the public route shell contract.
- Focused tests or static scans proving each preserved public route-shell `data-*` attribute has an active public runtime reader.
- Focused tests proving all installed public Docs Viewer route shells match the canonical template contract.
- Focused Python tests for dotlineform static route validation and lifecycle planning.
- Focused tests proving New Scope public-readonly does not write Markdown route stubs or Python source.
- Focused tests for route config records produced or edited by the lifecycle path.
- Focused tests proving New Scope public-readonly renders `site/<route>/index.html` from the route shell template rather than copying an existing installed route.
- Focused tests proving New Scope public-readonly creates the public docs payload root under `site/assets/data/docs/scopes/<scope>/` and default doc material for the new route.
- Focused tests proving Delete Scope removes user-created public route files, route records, and payloads without touching shared public runtime or unrelated routes.
- `bin/site-validate` as a deploy-root sanity check after lifecycle changes.
- Public Docs Viewer browser smoke for existing `/library/` and `/analysis/`.
- A temporary fixture or test scope proving a new public read-only route can be installed without editing Python route code, requiring Jekyll/Liquid, or running a static-site build.

## Related Docs

- [Portable Scope Setup](/docs/?scope=studio&doc=docs-viewer-portable-scope-setup)
- [New Scopes Builder](/docs/?scope=studio&doc=docs-viewer-new-scopes-builder)
- [Public Scopes](/docs/?scope=studio&doc=docs-viewer-public-scopes)

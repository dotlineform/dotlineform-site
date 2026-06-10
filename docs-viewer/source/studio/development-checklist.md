---
doc_id: development-checklist
title: Development Checklist
added_date: 2026-05-23
last_updated: 2026-06-06
parent_id: dev-home
viewable: true
---
# Development Checklist

- Use this checklist when a change touches local routes, public/local URL boundaries, shared route helpers, or generated follow-through.
- Use the `development-workflow.md` doc when lifecycle decisions are needed.

## General Gates

Before editing:

- classify the work as feature, bugfix, refactor, documentation, generated-data change, UI change, or workflow change
- read the owning docs for the smallest runtime, script, data model, UI primitive, or workflow that explains the change
- use a change request when the work changes user workflow, spans multiple modules or generated artifacts, creates a convention/data model, or has unresolved tradeoffs
- keep implementation scoped to the owning runtime, script, data model, or UI primitive
- keep UI shell, validation, data mutation, generated-output behavior, config ownership, and docs ownership separate
- prefer shared modules, UI primitives, JS, and CSS over one-off route-local or duplicated inline patterns
- keep UI copy such as labels and status text in the appropriate config or UI-text file
- keep generated data flowing from source records through scripts; do not edit generated payloads as source

When pruning, moving, or widening checked-in config or browser-visible payloads:

- scan active code, config loaders, server routes, services, tests, and generated-default pipelines before removing keys or fields
- treat historical docs as explanation, not proof of current ownership
- do not move server-only source paths, write targets, adapter path contracts, output patterns, metadata contracts, activity metadata, or source-write scope into browser bootstrap config
- keep browser public/config endpoints on explicit whitelists when they project domain config
- prefer positive owner-contract tests that assert allowed keys or whitelisted payload shape

## Local Studio Route Migration

Before moving or adding a Studio route:

- classify the route family: Catalogue, Analytics, Docs Viewer, Data Sharing, Audit, operational report, UI Catalogue, or shared Studio shell
- put route shell rendering in the owning view module, not in `studio_app_server.py`
- add runtime view config in `studio/app/server/studio/studio_app_config.py`
- keep route entry modules as orchestration shells for boot, required elements, event wiring, state handoff, and route-ready projection
- keep service or mutation behavior in the owning API/domain modules
- preserve existing DOM ids, `data-role` hooks, ready-state attributes, and UI text contracts unless the slice intentionally changes them
- add or update a focused smoke for local app route readiness
- retire the old Jekyll route file once the local route is verified, unless there is a documented transition reason to keep it

## Public Link Resolver

Local Studio and public Jekyll preview are separate hosts.
Studio links to public content must not accidentally resolve on the Studio app host.

When a route adds or touches public-content links:

- use `buildPublicSiteUrl(config, path, params)` for general public routes such as `/library/` and `/analysis/`
- use `studio/app/frontend/js/catalogue-public-links.js` for public catalogue routes such as works, series, work details, and moments
- keep editor-to-editor and Studio navigation links on local Studio routes
- do not use relative public-content hrefs such as `/works/...`, `/series/...`, `/moments/...`, `/library/`, or `/analysis/` directly in migrated Studio route output
- do not default to `https://dotlineform.com` unless the action is explicitly a live-site action
- do not add compatibility redirects or first-party links for retired public catalogue routes
- do not add derivable URL fields to generated public payloads unless the exception is documented
- let missing public preview base config fail visibly rather than silently falling back to the Studio host
- add smoke assertions that public links start with the configured public preview base
- Future route families still need to use the helper if they add public links.

## Local App JavaScript And Docs Viewer Runtime

Before changing browser JavaScript:

- name the complete responsibility being added, changed, or moved
- name the owner module after the change
- keep route shells limited to boot, required elements, event wiring, state handoff, route-ready projection, and calls into focused owners
- do not let the current renderer, controller, or route shell become the owner by default
- do not add new responsibilities to large route or controller files by default
- create or extend a focused owner for complete responsibilities such as rendering, modal lifecycle, service orchestration, result shaping, validation, import/export flow, route-state projection, or domain logic
- prefer shared JS/CSS behavior over duplicated inline route logic
- when modifying CSS, check whether shared styles can be consolidated rather than adding another one-off rule
- do not keep compatibility paths, old runtime fields, broad callbacks, or legacy handoffs as an end state
- retarget tests and helpers to the current owner contract instead of preserving old fields for fixture convenience

When changing Docs Viewer runtime/app architecture:

- identify the app context, state domain, service adapter, controller, hosted-view context, or view model that owns the concept
- pair frontend app concepts with backend/service/generated-data contracts when the change crosses that boundary
- preserve public read-only behavior without management assets, backend capability probes, local generated-read URLs, write-capable handles, or management services
- preserve manage-mode backend authority for writes, imports, settings, scope lifecycle, rebuilds, source opening, and local-only data
- send feature-facing generated reads through `docs-viewer-generated-data-runtime.js`
- send management writes through `docs-viewer-management-client.js` and server-side management endpoints with validation
- do not add new feature lifecycle ownership to `docs-viewer-app-runtime.js`

## Generated Data

When a change touches generated outputs or generated contracts:

- use dry-run behavior before write runs unless the task explicitly requires writing
- verify the owning builder and generated output shape
- update generated-output contract fixtures and projection checks when the field contract changes
- update source docs in the owning scope, then let the docs watcher or explicit task follow-through regenerate payloads
- do not rebuild Docs Viewer payloads unless the slice explicitly calls for that follow-through

## Documentation

When updating docs:

- keep docs source flat under `docs-viewer/source/<scope>/*.md`; section grouping comes from `doc_id`, `parent_id`, and top-level section docs rather than source folders
- use Docs Viewer links for published doc references, such as `/docs/?scope=studio&mode=manage&doc=<doc_id>`
- keep raw repo paths for unpublished docs, literal output paths, scripts, JSON artifacts, `README.md`, `AGENTS.md`, and other non-doc files
- update the owning runtime, UI, script, or data-model doc when behavior, dependencies, build/write responsibilities, or generated contracts change
- document script-specific command usage, flags, outputs, and operational notes under the owning scope parent rather than spreading partial notes across unrelated docs

## Verification

Choose the smallest useful check set:

- docs-only source changes usually need source review only
- Python changes need a syntax check or focused pytest with the configured Python interpreter
- script or generator changes need dry-run behavior and a summary of what would be written
- data model or generated contract changes need builder/output-shape checks and affected-doc review
- UI/layout changes need desktop browser checks when practical. Only verify mobile behavior where public pages on the site (dotlineform.com) will be affected.
- broad behavior changes should use the narrowest relevant `run_checks` profile

Toolchain basics:

- run project commands from `dotlineform-site/`
- use the configured Python interpreter for Python entrypoints and checks
- use explicit rbenv shims for public Jekyll verification rather than relying on system Ruby or Bundler
- if a Jekyll server is already running, verify one-off builds against a separate destination instead of the default `_site/`

When sweeping for stale references:

- scan documents in `./docs-viewer/source/studio`
- scan active code, config, runtime assets, scripts, tests, and current owning docs relevant to the change
- scan active request or task docs when closing or updating that request

For defensive tests during refactors:

- use temporary tests to catch accidental compatibility shims, proxy paths, or retired write surfaces during migration
- remove temporary tests before closeout unless they enforce a current architecture contract
- phrase permanent assertions around the positive architecture that must hold, such as the owning service boundary, allowed route surface, capability model, or write contract
- do not keep adding permanent assertions that old behavior, retired files, removed fields, or obsolete calls do not happen; delete the old code path and test the current contract instead
- use the planned static-searches checks report for durable repo-wide inventory of existing tests that need review against this rule

## Security And Sanitization

Run a focused sanitization check when a change touches:

- credential handling, tokens, env vars, or examples that mention secrets
- logging or local-service writes
- generated docs payloads that may include local output
- docs/examples with system paths or commands
- source/write services, write allowlists, local CORS, or loopback binding

Security defaults:

- keep docs and examples machine-agnostic unless a local path is explicitly required
- keep script examples project-local and use current entrypoint families such as `docs-viewer/build/...`, `studio/commands/...`, `studio/services/...`, and `bin/...`
- do not publish machine-specific usernames, absolute filesystem paths, local mount details, credentials, tokens, or private keys
- keep local write-service logs minimal and do not use full payload or file-content dumps
- keep local write services bound to loopback with narrow write allowlists and localhost-only CORS

## Source Tree Ownership

When adding or moving repo source:

- use [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership) as the maintained ownership contract
- keep public Jekyll layouts, includes, route pages, public runtime files, public CSS/assets, and generated public payloads outside `studio/`
- keep Docs Viewer source, runtime, CSS, config, build code, and services together under `docs-viewer/`
- keep local working output, staging, and test logs under `var/` or other ignored output paths

## Closeout

At closeout:

- summarize changed files and the purpose of the change
- report any generated payloads updated
- update owning docs and any implementation plan, task tracker, or change request status that changed
- list remaining risks or follow-up tasks

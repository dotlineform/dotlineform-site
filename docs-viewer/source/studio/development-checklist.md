---
doc_id: development-checklist
title: Development Checklist
added_date: 2026-05-23
last_updated: 2026-07-14
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
- keep unresolved feature discussion in a concept document; do not jump from open questions into implementation
- put independently finishable outcomes, priority, and dependencies on the owning roadmap
- use a change request only for one roadmap outcome that is ready to implement and complete
- split an oversized outcome before implementation rather than accepting a half-finished request or hiding multiple deliveries in a task tracker
- keep implementation scoped to the owning runtime, script, data model, or UI primitive
- keep UI shell, validation, data mutation, generated-output behavior, config ownership, and docs ownership separate
- prefer shared modules, UI primitives, JS, and CSS over one-off route-local or duplicated inline patterns
- keep UI copy such as labels and status text in the appropriate config or UI-text file
- keep generated data flowing from source records through scripts; do not edit generated payloads as source
- local HTTP services may suppress successful access logs, but must retain service-labelled method, path, and status details for 4xx/5xx responses; use the shared quiet-error logging owner
- static preview servers may suppress `BrokenPipeError` and `ConnectionResetError` caused by client navigation, but must not swallow other file or socket failures
- after a working slice creates a sizeable new module, review its responsibility map and likely next-phase growth before continuing; allow straightforward first-pass implementation, then split stable responsibilities when later work would otherwise accumulate in the same owner

When pruning, moving, or widening checked-in config or browser-visible payloads:

- scan active code, config loaders, server routes, services, tests, and generated-default pipelines before removing keys or fields
- treat historical docs as explanation, not proof of current ownership
- do not move server-only source paths, write targets, adapter path contracts, output patterns, metadata contracts, activity metadata, or source-write scope into browser bootstrap config
- keep browser public/config endpoints on explicit whitelists when they project domain config
- prefer positive owner-contract tests that assert allowed keys or whitelisted payload shape

## Public Link Resolver

Studio links to public content must not accidentally resolve on the Studio app host.

When a route adds or touches public-content links:

- use `buildPublicSiteUrl(config, path, params)` for general public routes such as `/library/` and `/analysis/`
- use `studio/app/frontend/js/catalogue-public-links.js` for public catalogue routes such as works, series, work details, and moments
- keep editor-to-editor and Studio navigation links on local Studio routes
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
- select scope-owned CSS with `data-viewer-scope` when it must work on both a public scope route and `/docs/?scope=<scope>`; `data-route-id` identifies the shell, not the selected management scope
- do not keep compatibility paths, old runtime fields, broad callbacks, or legacy handoffs as an end state
- retarget tests and helpers to the current owner contract instead of preserving old fields for fixture convenience

When changing Docs Viewer runtime/app architecture:

- identify the app context, state domain, service adapter, controller, hosted-view context, or view model that owns the concept
- pair frontend app concepts with backend/service/generated-data contracts when the change crosses that boundary
- preserve public read-only behavior without management assets, backend capability probes, local generated-read URLs, write-capable handles, or management services
- preserve manage-mode backend authority for writes, imports, settings, scope lifecycle, rebuilds, source opening, and local-only data
- declare route features through the allowlisted `features` array; disabled features must not construct controllers, bind events, run startup phases, or require payload URLs
- keep configured-scope discovery separate from general viewer-settings loading so a non-scope provider does not need a synthetic scopes array
- send feature-facing collection reads through a named provider; the configured-scope provider delegates transport, retry, reload, and generated-read capability behavior to `docs-viewer-generated-data-runtime.js`
- send management writes through `docs-viewer-management-client.js` and server-side management endpoints with validation
- do not add new feature lifecycle ownership to `docs-viewer-app-runtime.js`

## Generated Data

When a change touches generated outputs or generated contracts:

- use dry-run behavior before write runs unless the task explicitly requires writing
- verify the owning builder and generated output shape
- update generated-output contract fixtures and projection checks when the field contract changes
- update source docs in the owning scope, then let the docs watcher or explicit task follow-through regenerate payloads
- do not rebuild Docs Viewer payloads unless the slice explicitly calls for that follow-through

## Docs Import And Data Sharing Ownership

Use these ownership boundaries before adding new Docs Viewer import, export, or data-sharing behavior.

Staged source imports:

- `docs_import_preview.py` owns staged source preview dispatch and per-format preview response shape.
- `docs_html_markdown.py` owns reusable HTML/SVG parsing, sanitization, and HTML-to-Markdown conversion.
- `docs_import_html_parser.py` owns import-preview HTML summaries built from the shared HTML conversion boundary.
- `docs_import_media.py` owns media path planning, inline media extraction, local media materialization, remote-publication preparation, and image/file media summaries.
- `docs_media_storage.py` owns scope-aware local media roots/routes, confined local media reads, complete-set Docs R2 preflight/publication, exact staged-file publishing, and safe media results/reports.
- `docs_import_markdown_package.py` owns markdown package discovery, package media planning, and package link rewriting.
- `docs_import_common.py` owns source-format constants and small shared helpers.
- `docs_import_source_service.py` owns the management API workflow: request interpretation, collection-preview dispatch, single-source collision and confirmation gates, rebuild calls, and response assembly.
- `docs_import_document.py` owns reusable `ImportContent` create/overwrite validation, allowed front-matter application, canonical source formatting, per-document media/source apply, target/search ids, and document result/activity shaping.
- `docs_import_data_sharing_documents.py` is the thin Data Sharing collection orchestration entrypoint.
- `docs_import_data_sharing_package.py` owns supported trusted-collection classification before generic JSON/JSONL fallback, safe Data Sharing staged-package intake, trusted export association, raw-row identity checks, and adapter normalization.
- `docs_import_collection_plan.py` owns wrapper-neutral typed collection state and complete write-free collision, parent dependency, hierarchy, record-error, media-summary, blocker, warning, and response planning.
- `docs_import_collection_decisions.py` owns the collection apply request allowlist, explicit decision parsing, package/collision identity revalidation, decision drift, skipped-parent checks, and write-free refreshed-plan response.
- `docs_import_collection_apply.py` owns package-order source/media mutation, asset-level best effort, partial source failure, one coordinated rebuild call, and batch apply activity.
- `docs_import_collection_result.py` owns body-free grouped collection results, safe generation projection, manual-copy instructions, report payload shaping, and marker-rooted report output.
- `docs_import_review_handoff.py` owns the read-only association from validated review-package identities to matching server-listed collection records; it validates package id, safe staged filename, manifest status/schema, and export identity without exposing preview paths or adding write authority.
- `docs_review_materialization.py` owns atomic publication of a complete persistent review package: derived source, package-local generated output, trusted manifest, temporary-package cleanup, and final timestamped-folder rename.
- `docs_import_source_helpers.py` owns replacement-preview mutation, viewer URLs, import path display, and import summary text.
- `docs_import_source_interactive.py` owns interactive HTML companion asset detection, overwrite checks, target planning, and materialization.
- `docs-html-import.js` owns the managed import host, source-family selection, identity-only review-package preselection/unavailable state, route-ready/busy projection, and dispatch to the separate single-source or collection owners.
- `docs-import-collection-controller.js` owns safe collection identity and target-scope state, preview/apply service commands, sequential record decisions, pre-apply cancellation, confirmation/applying/result state, and refreshed-plan handling.
- `docs-import-collection-view.js` owns the body-free collection plan, blocker, warning, record, decision, confirmation, applying, and grouped-result rendering.
- `studio/shared/python/json_markdown_report.py` owns deterministic JSON-compatible Markdown rendering and atomic caller-path writes without app-specific output, grouping, marker, template, plugin, or registry behavior.

New staged source formats:

- add substantial format-specific parsing to a dedicated module, such as a future DOCX, Word HTML, or PDF parser module
- keep `docs_import_preview.py` as the dispatcher and response-shaping layer
- keep media extraction and materialization in `docs_import_media.py` unless the new format needs a narrow parser-owned discovery step

Returned-package imports:

- `docs_import.py` is a CLI wrapper only.
- `docs_returned_import_common.py` owns returned-package paths, report skeletons, staged file listing, scope validation, and shared issue helpers.
- `docs_returned_import_files.py` owns JSON/JSONL parsing, returned-package headers, export metadata lookup, and envelope metadata extraction.
- `docs_returned_import_records.py` owns normalized returned document record shape.
- `docs_returned_import_profiles.py` owns profile-to-import-type matching and supported returned-import profile ids.
- `docs_returned_import_context.py` owns current Docs source context and current-library/current-scope enrichment.
- `docs_returned_import_parser.py` owns returned-package report assembly.

Returned apply actions:

- `docs_data_sharing/apply_common.py` owns shared apply input parsing, selected record handling, and apply identity.
- `docs_data_sharing/apply_summaries.py` owns summary update planning and writes.
- `docs_data_sharing/apply_hierarchy.py` owns hierarchy/parent update planning and writes.
- keep returned apply actions limited to their named field-update contracts; do not add full reviewed-document creation as a Data Sharing action. Hand validated packages to managed Docs Viewer Import instead.

Documents data-sharing adapters:

- `data-sharing/adapters/documents/families/documents.py` owns adapter routing, operation validation, action selection, and adapter-context projection.
- Docs prepare/export behavior stays under `docs_export*.py` and `docs_data_sharing/package.py`.
- Import support is profile-driven: export-only profiles must keep `supports_return_import` false until a matching returned import type and apply action exist.

Docs Review:

- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review) owns the durable `/docs-review/` product, package, editing, and authority boundary.
- [Data Sharing Full Document Export Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package) owns exact-Markdown export and asset/dependency packaging only. Keep its `supports_return_import` flag false and do not route it into returned-package review or Docs Import.
- [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec) owns the implemented staged-JSONL collection import contract, with explicit create, overwrite, or skip decisions in managed Docs Import.
- Returned review packages are persistent derived workspace artifacts, not Docs Viewer scopes, and must not be registered in scope config.
- Docs Review is a distinct local route/app context of the existing Docs Viewer application, not a copied `docs-viewer-review/` frontend.
- Reuse shared tree, routing, rendering, panel, and public-safe CSS primitives through explicit review app context, provider, and capability contracts; do not import management source-editor modules or CSS into Docs Review.
- Review-specific frontend orchestration belongs under `docs-viewer/runtime/js/review/`; it must not add feature lifecycle ownership to `docs-viewer-app-runtime.js` or review conditionals to the normal scope selector.
- `docs-viewer-review-controller.js` may hand the active validated `package_id` to managed Docs Import, but it must not resolve or send staged filenames, preview paths, target scopes, plans, decisions, or mutations.
- `docs_review_packages.py` owns safe validated-package list/read behavior, retained generated-output completeness checks, and repair only for missing or malformed derived JSON; it exposes no package source-read/write methods. `docs_review_build.py` owns the synthetic package-local builder and `docs_review_materialization.py` owns initial complete-package publication.
- Keep route dispatch thin in `docs_viewer_service.py` and management service dispatchers; do not put review business logic in the server.
- Docs Review is read-only: it must not expose package source read/write, canonical import apply, promotion, or general management authority; it may only hand a safe package identity to managed Docs Import.
- Docs Review preserves validated package hierarchy but does not edit it; keep `parent_id` and hierarchy changes outside the review route.
- Public entrypoints must not import review assets, receive review service URLs, or probe review capabilities.

When adding or changing import/export behavior:

- name the profile, import type, action id, and owning module before coding
- do not import parser or action helpers through CLI wrapper files
- do not add compatibility facades for old module names
- update focused tests to target the new owner module instead of preserving old import paths
- keep UI workflow state in management service orchestration and keep parser/apply modules independent of route UI details

## Documentation

When updating docs:

- keep docs source flat under `docs-viewer/source/<scope>/*.md`; section grouping comes from `doc_id`, `parent_id`, and top-level section docs rather than source folders
- use Docs Viewer links for published doc references, such as `/docs/?scope=studio&doc=<doc_id>`
- keep raw repo paths for unpublished docs, literal output paths, scripts, JSON artifacts, `README.md`, `AGENTS.md`, and other non-doc files
- update the owning runtime, UI, script, or data-model doc when behavior, dependencies, build/write responsibilities, or generated contracts change
- document script-specific command usage, flags, outputs, and operational notes under the owning scope parent rather than spreading partial notes across unrelated docs

## Verification

Choose the smallest useful check set:

- docs-only source changes usually need source review only
- Python changes need a syntax check or focused pytest with the configured Python interpreter
- script or generator changes need dry-run behavior and a summary of what would be written
- data model or generated contract changes need builder/output-shape checks and affected-doc review
- UI/layout changes need manual or temporary browser verification when practical, not new permanent workflow tests. Only verify mobile behavior where public pages on the site (dotlineform.com) will be affected.
- broad behavior changes should use the narrowest relevant `run_checks` profile

Toolchain basics:

- run project commands from `dotlineform-site/`
- use the configured Python interpreter for Python entrypoints and checks
- use `bin/site-validate` for public static-site deploy-root verification
- if `bin/site-preview` is already running, refresh the browser after editing checked-in `site/` files

When sweeping for stale references:

- scan documents in `./docs-viewer/source/studio`
- scan active code, config, runtime assets, scripts, tests, and current owning docs relevant to the change
- scan active request or task docs when closing or updating that request

Browser smokes:

Permanent smoke tests should focus on request payloads, server responses, generated data, route boot, module wiring, and ownership boundaries. Do not add permanent smoke coverage for modal timing, cursor state, button copy, focus movement, or layout.

Before adding or expanding any permanent test, apply the review gate:

- Can this be tested as pure function or service behavior?
- Can this be tested by a direct HTTP/API request?
- Is a browser required to verify a contract, or only to mimic user clicks?
- Will this fail because copy, layout, focus, hover state, or modal timing changed?

Choose the lowest layer that proves the durable contract. Skip tests that mostly mimic a user path unless browser acceptance coverage was explicitly requested.

1. **Do not default to full browser smokes for small UI/component amendments.**
   For changes like button placement, labels, CSS class ownership, or toolbar composition, use syntax checks plus a narrow DOM/component check.

2. **Do not expand end-to-end smokes while implementing the feature unless the feature explicitly changes that workflow contract.**
   Do not turn a UI adjustment into a modal workflow test update. That is the wrong cost profile.

3. **Separate visual verification from workflow verification.**
   A quick in-app Browser DOM snapshot or screenshot answers “does a control render correctly?” Full Playwright workflows answer a different question and should not be pulled in automatically.

4. **If a smoke test fails outside the changed contract, stop and report it instead of repairing the smoke opportunistically.**
   Fixing stale or brittle smoke infrastructure during unrelated UI work hides the cost and expands scope.

5. **Prefer component-level coverage for shared components.**
   For example, with `RecordListActions`, the useful check is: given actions with `appearance: "icon"`, it renders borderless icon buttons with `aria-label`, selection-disabled behavior, and emits action payloads. That should not require loading the full Studio Work editor route.

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
- keep public static route renderers, public runtime files, public CSS/assets, and generated public payloads outside `studio/`
- keep Docs Viewer source, runtime, CSS, config, build code, and services together under `docs-viewer/`
- keep local working output, staging, and test logs under `var/` or other ignored output paths

## Closeout

At closeout:

- summarize changed files and the purpose of the change
- report any generated payloads updated
- update the one durable owner whose behavior changed and any roadmap, task tracker, or request status that actually changed
- list remaining risks and separately finishable follow-up roadmap rows; do not leave later work inside a completed request

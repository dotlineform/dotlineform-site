---
doc_id: site-request-rubyless-app-runtimes-tasks
title: Rubyless App Runtimes Tasks
added_date: 2026-06-01
last_updated: 2026-06-01
ui_status: in-progress
parent_id: site-request-rubyless-app-runtimes
viewable: true
---
# Rubyless App Runtimes Tasks

This is the implementation tracker for [Rubyless App Runtimes Request](/docs/?scope=studio&doc=site-request-rubyless-app-runtimes).

## Just Done

- Added the current app-facing Ruby dependency map to the parent request.
- Moved implementation tasks into this child tracker.
- Added the Markdown library decision to the parent request, recommending `markdown-it-py` and explicitly rejecting Jekyll/Kramdown parity checks.
- Expanded this tracker into phased tasks with startup cleanup as Phase 0, explicit generated-output contract fixtures, no mixed builder mode, no hidden Ruby fallbacks, and no implicit cleanup.
- Clarified that generated docs/search payloads may be stale during migration because source Markdown remains readable directly.
- Removed disabled local-startup rebuild handling from `bin/local-studio`, including `DOCS_STARTUP_REBUILD_SCOPES`, `CATALOGUE_STARTUP_LOOKUP_REBUILD`, startup Ruby docs/search builder calls, startup catalogue lookup export, and related active docs/tests.
- Defined the cutover preflight for later builder/caller swaps.
- Pinned `markdown-it-py==3.0.0` in `requirements.txt` and recorded the initial no-plugin `MarkdownIt("commonmark")` renderer dependency contract.
- Added the shared Python Markdown renderer helper with CommonMark, built-in table support, explicit raw-HTML behavior, and no external renderer plugins.
- Added Docs Viewer v2 renderer acceptance fixtures for rendered HTML semantics and generated plain text without Jekyll/Kramdown parity checks.
- Added Docs Viewer v2 custom-token contract fixtures for media, interactive HTML, semantic references, invalid references, code-skip behavior, generated reference payloads, and generated search text.
- Added generated-output contract fixtures for Docs Viewer docs payloads, semantic reference payloads, docs search payloads, catalogue search payloads, and catalogue prose `content_html` without locking in current Jekyll/Kramdown markup.
- Added the Python Docs Viewer payload builder entrypoint at `docs-viewer/build/build_docs.py`, covering Markdown source loading, scope config, front matter, custom tokens, semantic references, Python Markdown rendering, generated docs payloads, reference payloads, targeted payload mode, browser config writes, and diagnostics. Callers still use the Ruby builder until the later orchestration swap task.
- Preserved Python Docs Viewer payload builder command behavior with focused checks for dry-run no-write mode, write mode browser config output, unchanged second writes, targeted `--only-doc-ids` CLI diagnostics, generated reference payload behavior, and concise front-matter failure output.
- Added the Python Docs Viewer search builder entrypoint at `docs-viewer/build/build_search.py`, covering generated docs index reads, viewability and manage-only filtering, current docs-search schema/version hashing, dry-run/write/force modes, scope-specific output paths, targeted `--only-doc-ids` patch/remove behavior, and failure handling for docs-incompatible targeted flags. Callers still use the Ruby builder until the orchestration swap task.
- Switched Docs Viewer rebuild orchestration to Python builders in the management rebuild helper, live rebuild watcher, and scope lifecycle build-command planning. The swap removes Bundler/Ruby detection and command construction from docs payload/search rebuild paths, keeps targeted docs/search behavior, and leaves Docs import Markdown validation for task 12.
- Replaced Docs import Markdown validation with the shared Python Markdown renderer/import sanitizer boundary for HTML, Markdown, Markdown package, text, SVG, image, and file-media previews. Docs import preview validation no longer detects Bundler or invokes `studio/shared/ruby/render_markdown_with_jekyll.rb`.
- Confirmed Analytics documents Data Sharing apply reaches the same Python Docs Viewer rebuild helper as Docs management writes, and added regression coverage that returned-package summary apply invokes `docs-viewer/build/build_docs.py` and `docs-viewer/build/build_search.py` rather than Bundler, Ruby, or `.rb` builders.
- Added the Python catalogue search builder entrypoint at `studio/services/catalogue/search/build_search.py`, covering the current catalogue search schema, config validation, dry-run/write/force modes, BLAKE2b content versioning, source JSON overrides, docs-only flag rejection, and additive-only `--only-records` targeted behavior. Callers still use the Ruby builder until the task 15 orchestration swap.
- Switched catalogue search caller orchestration to `studio/services/catalogue/search/build_search.py` through `catalogue_build_commands.py`. Scoped builds, field-aware previews, publication/delete follow-through, bulk build targets, and direct catalogue search rebuild helpers no longer resolve Bundler or invoke Ruby for catalogue search.
- Moved catalogue prose rendering in `studio/services/catalogue/generate_work_pages.py` to the shared Python Markdown renderer. Work, series, and moment `content_html` generation no longer invokes `studio/shared/ruby/render_markdown_with_jekyll.rb`; focused fixtures cover representative prose semantics without Jekyll/Kramdown markup lock-in.
- Confirmed `bin/local-studio` is Python/JS only, added a focused runner contract test for that boundary, and updated Local Studio runner/runtime docs so manual docs rebuild examples point at Python builders while Ruby/Bundler remains public-preview/build only.
- Updated check-profile and fixture command expectations for Python app builders. The `docs` run-check profile now invokes `docs-viewer/build/build_docs.py` and `docs-viewer/build/build_search.py`, docs-log fixtures cite the Python docs builder, and the named Docs Viewer/catalogue command-shape tests pass against Python builder expectations.
- Retired the shared app-facing Ruby Markdown/render helpers and the retired Ruby Docs Viewer payload builder that depended on them. `bin/public-site-preview` no longer loads the WEBrick reset filter through `RUBYOPT`; public-site preview can use raw `bundle exec jekyll serve` when no wrapper is needed.

## Next Task Steer

Continue with Phase 4 task 20: remove obsolete compatibility scaffolding and mixed-runtime knobs.

Docs Viewer app-facing generation paths are now Python-backed for payloads, docs search, Docs import validation, and Analytics documents Data Sharing apply. Catalogue search generation/caller orchestration and catalogue prose rendering now use Python. `bin/local-studio` is covered as a Python/JS-only runner, active check/test command-shape expectations point at Python app builders, and the shared Ruby Markdown/render helpers are retired. The next remaining work is to remove obsolete compatibility scaffolding, stale Ruby builder entrypoints, and mixed-runtime knobs.

## Implementation Steer

This migration must preserve and reinforce the JavaScript/Python app boundaries established while moving Studio and Docs Viewer toward JavaScript app models:

- browser JavaScript owns route UI, rendering, interaction state, route-state projection, modals, panels, client-side search UI, and app-shell orchestration
- Python owns local APIs, filesystem access, source writes, backups, generated payload builders, search builders, import/export helpers, process execution, allowlists, compact logs, and local service responses
- Ruby/Jekyll is manual public-site preview/build tooling only, not an app runtime or app-facing generator dependency

The current system is not risk-free. The risk policy, dashboard, and child inventories document remaining architectural, structural, workflow, and performance/cost work:

- [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy)
- [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard)

Do not use the Rubyless migration as a reason to widen route controllers, merge browser and backend responsibilities, add generic command runners, expose broad filesystem reads/writes, create new localhost services for behavior that belongs in the existing Studio or Docs Viewer service, or move generated-data ownership into browser code.

Assume current local operations can be paused while this migration is implemented. There is no requirement to support a mixed Ruby/Python app-generator economy during cutover. Prefer direct cutover of each builder/caller family over compatibility layers.

Generated docs/search payloads may be stale while the migration is in progress. That is acceptable: source Markdown remains readable directly, and generated payload freshness is restored as part of the verified cutover rather than protected through compatibility scaffolding.

Each implementation slice should reduce or hold steady the existing risk profile. If a temporary bridge is unavoidable, record it in this tracker with an owner, removal condition, and verification check. Do not add compatibility aliases, dual-write paths, broad fallbacks, mixed old/new builder dispatch, or hidden Jekyll/Ruby fallback paths to make the migration easier.

Any cleanup discovered during implementation should become an explicit task in this tracker. Do not leave cleanup as an implicit follow-up or fold it into vague closeout language.

## Cutover Preflight

Use this preflight before any later phase that changes builder implementations, builder callers, watcher behavior, or generated-output contracts.

Pause local services when the slice swaps a command entrypoint, service caller, watcher command, import/apply path, catalogue write follow-through, or generated-output schema. Prefer stopping `bin/local-all` so Local Studio, Local Analytics, UI Catalogue, Docs Viewer, public preview, and docs watcher children are not racing against partially changed code. If the slice affects only one isolated service, stopping that service is enough, but record that narrower choice in the closeout.

Before editing a caller family:

- identify the active Ruby command/helper being replaced
- identify the Python owner that will replace it
- identify the generated artifacts that may be stale during the slice
- identify the app routes or local services that should remain paused until verification completes
- choose the smallest focused checks that prove the current phase, not the full migration

Docs watcher expectations:

- keep `docs-viewer/services/docs_live_rebuild_watcher.py` as the long-running watcher service until a later task explicitly changes its command implementation
- do not run the watcher during a builder/caller swap unless the current phase is already verified
- when watcher behavior changes, verify both targeted docs-search updates and full same-scope fallback behavior

Generated docs/search payloads may be stale during the migration. That is acceptable while a phase is in progress because source Markdown remains readable directly, and freshness returns through the verified replacement builders rather than through mixed Ruby/Python fallback paths. Do not add hidden startup rebuilds, compatibility dispatch, dual-write behavior, or Ruby fallback branches to keep payloads fresh mid-cutover.

Restart services only after the current phase passes its focused verification and the tracker records any unresolved cleanup as an explicit task. If a service cannot safely restart without a follow-up task, leave it paused, record the blocker with owner/removal condition, and do not continue into adjacent feature work.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

### Phase 0: Startup Cleanup

| ID | status | action |
| --- | --- | --- |
| 1 | done | Remove disabled local-startup rebuild code paths, not just flags. Delete `DOCS_STARTUP_REBUILD_SCOPES` and `CATALOGUE_STARTUP_LOOKUP_REBUILD` handling from `bin/local-studio`/`bin/local-all`, including scope parsing, startup rebuild loops, catalogue lookup rebuild calls, related service wiring, startup messages, docs, and tests. Remove the actual calls to `docs-viewer/build/build_docs.rb`, `docs-viewer/build/build_search.rb`, and startup catalogue lookup rebuild from local app startup. Keep `docs-viewer/services/docs_live_rebuild_watcher.py` as the long-running docs watcher service. |
| 2 | done | Define the cutover preflight for later phases. Pause `bin/local-all` or affected services before builder/caller swaps, keep docs watcher expectations explicit, accept stale generated docs/search payloads during migration because source Markdown remains readable directly, and restart only after the current phase is verified. |

### Phase 1: Renderer And Fixtures

| ID | status | action |
| --- | --- | --- |
| 3 | done | Pin the Python Markdown renderer dependency. Add `markdown-it-py` to `requirements.txt` with an exact version, record any enabled renderer plugins in the builder docs/tests, and confirm the dependency loads through the configured Miniconda Python environment. |
| 4 | done | Build a shared Python Markdown rendering helper. Start from `MarkdownIt("commonmark")`, enable only syntax needed by current authored docs and acceptance fixtures, and keep raw HTML/sanitization behavior explicit. Do not add Jekyll/Kramdown parity fixtures or automated current-output comparison checks. |
| 5 | done | Add Docs Viewer v2 renderer acceptance fixtures before caller migration. Cover headings, links, lists, fenced code, inline code, raw HTML allowed by the current content model, tables if enabled, generated plain text, and HTML semantics directly rather than comparing against Jekyll/Kramdown output. |
| 6 | done | Add custom-token builder fixtures before caller migration. Cover media tokens, interactive HTML tokens, semantic reference tokens, invalid/missing/non-published references, code-block skip behavior, generated semantic reference payloads, and generated search text. |
| 7 | done | Add generated-output contract fixtures before implementation. Cover Docs Viewer `index.json`, Docs Viewer `by-id/*.json`, reference payloads, docs search payloads, catalogue search payloads, and catalogue prose `content_html` so the migration protects app contracts rather than current Jekyll/Kramdown markup. |

### Phase 2: Docs Viewer Builders And Callers

| ID | status | action |
| --- | --- | --- |
| 8 | done | Build the Python Docs Viewer payload builder that replaces `docs-viewer/build/build_docs.rb`. It should read Markdown source and scope config, parse front matter, apply the custom token pipeline, render document HTML/text through the shared Python renderer, write `index.json` and `by-id/*.json`, and preserve the generated Docs Viewer data shape. |
| 9 | done | Preserve Docs Viewer payload builder command behavior. Implement dry-run/write modes, scope selection, targeted `--only-doc-ids`, diagnostics, unchanged-file behavior, generated reference payloads, and failure messages needed by management workflows. |
| 10 | done | Build the Python Docs Viewer search builder that replaces `docs-viewer/build/build_search.rb`. It should consume generated docs payloads, preserve the current search index schema/version/hash behavior, support scope-specific writes, and support targeted docs-search updates where currently used. |
| 11 | done | Switch Docs Viewer rebuild orchestration to Python builders. Update `docs-viewer/services/docs_write_rebuild.py`, `docs-viewer/services/docs_live_rebuild_watcher.py`, `docs-viewer/services/docs_scope_manifest.py`, `docs-viewer/services/docs_management_service.py`, `docs-viewer/services/docs_management_mutation_service.py`, `docs-viewer/services/docs_management_import_service.py`, and `docs-viewer/services/docs_import_source_service.py` so docs payload/search rebuilds no longer detect Bundler or invoke Ruby. Keep the docs watcher service, but change its command implementation to Python builders with no Ruby fallback on Python failure. |
| 12 | done | Replace Docs import Markdown validation. Remove `docs_html_import.py` dependence on `studio/shared/ruby/render_markdown_with_jekyll.rb`; validate staged HTML, Markdown, Markdown package, text, SVG, image, and file-media previews through the Python renderer/sanitizer boundary. |
| 13 | done | Update Analytics documents Data Sharing apply path. Ensure `analytics-app/app/server/analytics_app/analytics_data_sharing_api.py` and `docs-viewer/services/docs_data_sharing/write.py` reach only the Python Docs Viewer rebuild path for returned document package apply. |

### Phase 3: Catalogue Search And Prose

| ID | status | action |
| --- | --- | --- |
| 14 | done | Build the Python catalogue search builder that replaces `studio/services/catalogue/search/build_search.rb`. Preserve the current catalogue search index contract consumed by public search and local app links, including dry-run/write modes, targeted-record behavior, config validation, and failure output. |
| 15 | done | Switch catalogue search callers to the Python builder. Update `studio/services/catalogue/catalogue_build_commands.py`, `catalogue_build_service.py`, `catalogue_json_build.py`, publication/delete flows, bulk flows, and affected tests so catalogue search rebuilds no longer resolve Bundler or invoke Ruby. |
| 16 | done | Move catalogue prose rendering to the shared Python Markdown renderer. Update `studio/services/catalogue/generate_work_pages.py` so work, series, and moment `content_html` no longer uses `studio/shared/ruby/render_markdown_with_jekyll.rb`; add focused fixtures for representative prose. |

### Phase 4: Launchers, Tests, Cleanup, And Docs

| ID | status | action |
| --- | --- | --- |
| 17 | done | Make `bin/local-studio` Python/JS only. Remove remaining Bundler detection and Ruby app-builder command assumptions; keep public preview URLs informational only. |
| 18 | done | Update check profiles and tests that assert Ruby command shapes. Move `docs-viewer/tests/python/test_docs_write_rebuild.py`, `test_docs_live_rebuild_watcher.py`, `test_docs_import_service.py`, `docs_viewer_management_workflows.py`, `studio/tests/python/test_catalogue_build_commands.py`, and docs-log fixture references to Python command/helper expectations. |
| 19 | done | Retire or isolate app-facing Ruby helpers. Remove app/data-generation use of `studio/shared/ruby/jekyll_markdown_renderer.rb`, `studio/shared/ruby/render_markdown_with_jekyll.rb`, and `studio/shared/ruby/jekyll_webrick_client_reset_filter.rb`. Any remaining Ruby helper use must be documented as public-preview-only. |
| 20 | planned | Remove obsolete compatibility scaffolding and mixed-runtime knobs. Delete or retire replaced Ruby builder dispatch options, Bundler override options used only by app builders, stale command examples in active app docs, and tests that exist only to preserve old Ruby command shapes. |
| 21 | planned | Add explicit cleanup tasks for any leftovers found during implementation. If a temporary bridge, stale generated path, obsolete helper, old docs reference, or retired test cannot be removed immediately, add a new row to this table before closeout with a concrete owner and removal condition. |
| 22 | planned | Update command/runtime docs. Describe Python Docs Viewer generation, Python docs search generation, Python catalogue search generation, Python catalogue prose rendering, app servers, docs watcher behavior, and live rebuilds; remove active-app examples for disabled startup rebuilds and Ruby app builders. |
| 23 | planned | Update dependency docs. Describe `markdown-it-py`, enabled renderer plugins, sanitizer boundaries, and the no-Jekyll-parity fixture policy. |
| 24 | planned | Update script inventories and risk docs. Record app-facing Ruby removal, remaining public-preview-only Ruby usage, changed ownership for generated builders, and any risk-evidence implications. |

### Phase 5: Audits And Verification

| ID | status | action |
| --- | --- | --- |
| 25 | planned | Audit app runtime Ruby references after migration. Use targeted source scans to confirm Studio, Docs Viewer management, Analytics, Data Sharing, catalogue build/search/prose generation, and UI Catalogue no longer depend on Ruby scripts or Bundler. Include at least these patterns: `bundle`, `exec ruby`, `build_docs.rb`, `build_search.rb`, `render_markdown_with_jekyll`, `jekyll_markdown_renderer`, `DOCS_STARTUP_REBUILD_SCOPES`, and `CATALOGUE_STARTUP_LOOKUP_REBUILD`. |
| 26 | planned | Verify no mixed builder mode remains. Scan for runtime switches, env flags, fallback branches, compatibility aliases, dual-write paths, or command dispatch that can choose between Ruby and Python app builders. Fail closeout if such a switch remains outside public-preview-only tooling. |
| 27 | planned | Verify Studio is JavaScript + Python only. `/studio/`, route shells, runtime config, catalogue editors, audits, activity, Docs links, and APIs should run from Python server + JS frontend + Python builders. |
| 28 | planned | Verify Analytics is JavaScript + Python only. Analytics routes, tag workflows, documents Data Sharing apply, runtime config, generated app data, and APIs should not depend on Ruby/Jekyll. |
| 29 | planned | Verify Docs Viewer management is JavaScript + Python only. `/docs/` management, source mutations, scope config, generated docs payloads, generated references, generated search, import preview/apply, and live rebuild watcher should all be Python/JS. Public `/library/` and `/analysis/` remain public-site preview concerns. |
| 30 | planned | Verify UI Catalogue is JavaScript + Python/static only. Serve demos without Jekyll and keep public-site integration checks separate. |
| 31 | planned | Run final acceptance and app verification. Include renderer/builder acceptance fixtures, generated-output contract fixtures, Docs Viewer payload/search checks, catalogue search contract checks, catalogue prose rendering checks, Local Studio smoke, Local Analytics/Data Sharing smoke, Docs Viewer management smoke, UI Catalogue smoke, and syntax/import checks for changed Python and JavaScript. |
| 32 | planned | Run separate public-site verification. Run an explicit Jekyll public-site build/preview check only to confirm the manual public preview/build layer still works, not to benchmark app Markdown rendering. |
| 33 | planned | Final closeout. Confirm there are no unresolved compatibility layers or implicit cleanup tasks, record remaining Ruby usage as public-preview-only or deferred public-site renderer work, update this tracker statuses, update the parent request if scope/risks changed, and add any required docs-log entry. |

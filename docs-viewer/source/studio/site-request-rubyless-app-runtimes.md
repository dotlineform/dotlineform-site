---
doc_id: site-request-rubyless-app-runtimes
title: Rubyless App Runtimes Request
added_date: 2026-05-30
last_updated: 2026-06-01
ui_status: in-progress
parent_id: change-requests
viewable: true
---
# Rubyless App Runtimes Request

Status:

- draft
- This request defines the path to a JavaScript + Python app/tooling stack.
- Treat the Docs Viewer work as Docs Viewer v2: choose the right Python/JavaScript rendering and authoring approach rather than preserving incidental proof-of-concept output.
- Ruby/Jekyll stays only as a manual public-site preview/build layer until the public site itself is replaced.

## Task Tracker

Use [Rubyless App Runtimes Tasks](/docs/?scope=studio&doc=site-request-rubyless-app-runtimes-tasks) for the implementation sequence, task status, and closeout tracking.

## Summary

Move app runtimes and app-facing generators to JavaScript + Python, and use the Docs Viewer builder replacement as the foundation for Docs Viewer v2.

The target is direct:

- browser UI and route shells are JavaScript
- local services, write APIs, generated-data builders, and app servers are Python
- Ruby/Jekyll is not used to make Studio, Analytics, Docs Viewer management, UI Catalogue, docs payload generation, or app search generation work
- Jekyll remains only for manual public-site preview/build, run explicitly by the user

This means replacing the Ruby builders and helpers that apps currently rely on, not merely proving that app startup can avoid Ruby. Where Docs Viewer v2 needs a better markdown library, custom token syntax, preprocessing pass, or renderer design, choose the practical solution and migrate the authored content deliberately.

## Context

The Ruby/Jekyll dependency in Docs Viewer generation was a pragmatic shortcut.

When `build_docs.py` was first built, piggy-backing on the local Jekyll server and Jekyll's Markdown converter saved development time. At that point Docs Viewer was a proof of concept, and using the existing public-site toolchain was a reasonable way to get Markdown rendered into usable HTML quickly.

The architecture has since become more complex:

- Studio, Analytics, Docs Viewer management, and UI Catalogue are now separate local app surfaces.
- Docs Viewer generation now owns custom tokens, semantic references, generated payloads, search input text, and management-mode source workflows.
- Local app startup and app verification should not be coupled to public-site preview tooling.
- The public site mostly consumes generated HTML/data assets and provides routing stubs for public pages.

The better direction now is consolidation around Python for generation and services, with JavaScript for browser apps. Jekyll can remain as the manually run public preview/build layer until the public site itself is replaced.

## Target Architecture

```text
Browser JavaScript
  - Studio app shell and route bodies
  - Analytics app shell and route bodies
  - Docs Viewer runtime and management UI
  - UI Catalogue demos

Python
  - local app servers
  - local write/read APIs
  - docs payload builder
  - search index builders
  - catalogue/public data builders needed by local apps
  - live rebuild watchers

Ruby/Jekyll
  - manual public site preview
  - manual public site build
```

Jekyll should consume generated assets; it should not be a dependency for generating app data or helping Docs Viewer function.

## Current Ruby Dependency Map

This is the current app-facing Ruby dependency surface found in Studio, Docs Viewer, and Analytics source modules. Public-site-only wrappers such as `bin/public-site-preview` and `bin/public-site-build` remain intentionally outside this app-runtime list.

Ruby scripts and helpers currently in the app/data-generation path:

- `docs-viewer/build/build_docs.py`
  - builds Docs Viewer payloads for configured scopes
  - directly requires `studio/shared/python/markdown_renderer.py`
  - owns current custom Docs Viewer token expansion before Markdown rendering
- `docs-viewer/build/build_search.py`
  - builds Docs Viewer search indexes for docs scopes
- `studio/services/catalogue/search/build_search.py`
  - builds the catalogue search index
- `studio/shared/python/markdown_renderer.py`
  - renders trusted Docs Viewer and catalogue prose Markdown through `markdown-it-py`

Docs Viewer direct dependencies:

- `docs-viewer/services/docs_write_rebuild.py`
  - runs `docs-viewer/build/build_docs.py`
  - runs `docs-viewer/build/build_search.py`
  - used for single-scope rebuilds, targeted docs/search rebuilds, and all-scope rebuilds
- `docs-viewer/services/docs_live_rebuild_watcher.py`
  - runs the Python Docs Viewer docs/search builders whenever watched source Markdown changes
- `docs-viewer/services/docs_html_import.py`
  - validates staged HTML, Markdown, Markdown package, text, SVG, image, and file-media import previews through the shared Python Markdown renderer/import sanitizer boundary
  - no longer detects Bundler or invokes `studio/shared/ruby/render_markdown_with_jekyll.rb`
- `docs-viewer/services/docs_scope_manifest.py`
  - emits Docs Viewer scope lifecycle build commands that name `docs-viewer/build/build_docs.py` and `docs-viewer/build/build_search.py`
  - create/delete apply paths execute the rebuilds through `docs_write_rebuild.py`
- `docs-viewer/services/docs_management_service.py`
  - manual `/docs/rebuild` and source-config write follow-through call `docs_write_rebuild.py`
- `docs-viewer/services/docs_management_routes.py`
  - exposes Docs Viewer management endpoints that dispatch rebuild, mutation, lifecycle, and import requests to the Ruby-backed services listed here
- `docs-viewer/services/docs_management_mutation_service.py`
  - create, metadata, viewability, move, delete, and multi-scope mutation follow-through calls `docs_write_rebuild.py`
- `docs-viewer/services/docs_management_import_service.py`
  - source import apply paths call `docs_write_rebuild.py`
- `docs-viewer/services/docs_import_source_service.py`
  - staged source import previews call `docs_html_import.py`
  - staged source import create/overwrite apply paths call `docs_write_rebuild.py`
- `docs-viewer/services/docs_data_sharing/write.py`
  - returned document package apply writes source Markdown and calls the injected `perform_source_write_and_rebuild` dependency

Studio direct dependencies:

- `bin/local-studio`
  - starts `docs-viewer/services/docs_live_rebuild_watcher.py`, which currently depends on the Python docs/search builders
- `studio/services/catalogue/catalogue_build_commands.py`
  - constructs `studio/services/catalogue/search/build_search.py --scope catalogue`
- `studio/services/catalogue/catalogue_build_service.py`
  - uses the catalogue build command helper for catalogue search rebuilds after scoped catalogue writes
- `studio/services/catalogue/catalogue_write_service.py`
  - catalogue write preview/apply routes call `catalogue_build_service.py`
- `studio/services/catalogue/catalogue_work_service.py`, `studio/services/catalogue/catalogue_series_service.py`, `studio/services/catalogue/catalogue_moment_service.py`, and `studio/services/catalogue/catalogue_work_detail_service.py`
  - scoped work, series, moment, and detail writes call `catalogue_build_service.py`
- `studio/services/catalogue/catalogue_bulk_service.py`
  - bulk-add workflows call `catalogue_build_service.py`
- `studio/services/catalogue/catalogue_publication_service.py` and `studio/services/catalogue/catalogue_delete_service.py`
  - publication/delete workflows call the Python catalogue search rebuild helper
- `studio/services/catalogue/catalogue_json_build.py`
  - adds the Python catalogue search builder to scoped JSON build command plans when `rebuild_search` is enabled
- `studio/services/catalogue/generate_work_pages.py`
  - uses the shared Python Markdown renderer to render source prose into `content_html` for series JSON, work JSON, and moment JSON payloads
- `studio/commands/run_checks.py`
  - the docs profile invokes `./docs-viewer/build/build_docs.py --scope studio --write`
  - the docs profile invokes `docs-viewer/build/build_search.py --scope studio --write`
  - docs-viewer smoke profiles still use Jekyll temp builds for browser smoke setup; that is verification/public-preview coupling, not a desired app runtime dependency

Analytics dependencies:

- `bin/local-analytics`
  - no direct Ruby, Bundler, Jekyll, or `.rb` script invocation
- `analytics-app/app/server/analytics_app/analytics_data_sharing_api.py`
  - no direct Ruby invocation; the documents Data Sharing handler injects `docs_write_rebuild.perform_source_write_and_rebuild`
  - returned document package apply now reaches the Python Docs Viewer docs/search builders through `docs-viewer/services/docs_data_sharing/write.py`
- `analytics-app/app/server/analytics_app/tag_services/*`
  - no direct Ruby script dependency found in the current tag registry, alias, group, assignment, promotion, activity, or route modules
- `analytics-app/app/frontend/js/*`
  - no direct Ruby script dependency found in the current browser modules

Current test/check references:

- `docs-viewer/tests/python/test_docs_write_rebuild.py`
  - asserts the Python Docs Viewer builder command shapes
- `docs-viewer/tests/python/test_docs_live_rebuild_watcher.py`
  - asserts the watcher calls the Python Docs Viewer builders
- `docs-viewer/tests/python/test_docs_import_service.py`
  - patches `validate_markdown_preview` and rebuild helpers around import workflows
- `docs-viewer/tests/smoke/docs_viewer_management_workflows.py`
  - patches Docs Viewer rebuild and Python Markdown validation helpers for management workflow smoke coverage
- `studio/tests/python/test_catalogue_build_commands.py`
  - asserts the Python catalogue search command shape
- `studio/tests/python/test_docs_logs_indexes.py`
  - records `docs-viewer/build/build_docs.py` as a related file in docs log index fixtures

## Goals

- replace the retired Ruby Docs Viewer payload builder with `docs-viewer/build/build_docs.py`, including the current custom Markdown token pipeline
- replace `docs-viewer/build/build_search.rb` with a Python Docs Viewer search builder
- replace `studio/services/catalogue/search/build_search.rb` with a Python catalogue search builder
- remove app-facing dependencies on `studio/shared/ruby/jekyll_markdown_renderer.rb`, `studio/shared/ruby/render_markdown_with_jekyll.rb`, and Jekyll server helper modules
- make docs live rebuilds call Python builders
- make local app launchers start Python/JS app runtimes only
- keep direct `bundle exec jekyll serve` / `bundle exec jekyll build`, Bundler, and Jekyll documented as public-site preview/build tooling only
- preserve the generated JSON shape and useful content semantics while allowing deliberate Docs Viewer v2 improvements to token syntax, preprocessing, rendering, and browser behavior

## Non-Goals

- replacing the public site renderer in this request
- removing `.ruby-version`, `Gemfile`, or Jekyll while the public site still uses them
- accidental app UI behavior changes caused only by swapping implementation language
- moving local write services into JavaScript
- making browser code write to the filesystem directly

## Current Custom Token Implementation

The current custom Markdown behavior is not a Jekyll plugin or a separate Ruby token library.

`docs-viewer/build/build_docs.py` owns the custom token pipeline directly:

- it parses front matter itself
- it resolves custom content tokens before calling the Markdown converter
- it calls `JekyllMarkdownRenderer.render_string(...)` only after token expansion
- it post-processes rendered HTML for image titles, Docs Viewer links, plain text, and generated metadata

The current custom content tokens are:

- media tokens, written as double brackets around `media:<path-or-id>`
  resolved before Markdown conversion through `resolve_media_tokens(...)`
- interactive HTML tokens, written as double brackets around `interactive-html:<filename.html> height=<pixels>`
  resolved before Markdown conversion into a sandboxed iframe through `resolve_interactive_html_tokens(...)`
- semantic reference tokens, written as double brackets around `ref:<kind>:<id>|<label>` with an optional `{action=link}` modifier
  resolved before Markdown conversion through `resolve_semantic_ref_tokens(...)`

Semantic reference tokens currently have additional behavior:

- supported kinds are `work`, `series`, and `moment`
- references resolve against catalogue records
- published targets become links
- missing, invalid, unsupported, or non-published targets become annotated spans
- reference records are emitted into generated reference payloads
- replacements intentionally skip fenced code blocks and inline code

The Python replacement should treat these as first-class builder features, not as Markdown library side effects.
Docs Viewer v2 may keep this syntax, adapt it, or replace it with a cleaner syntax if that is the pragmatic path. Any syntax change should include a migration path for existing authored docs.

## Docs Viewer V2 Target

The current rendered HTML is not a formal contract. It is the output from the proof-of-concept Docs Viewer builder: Markdown went in, HTML came out, and the viewer used it.

The replacement should not chase byte-for-byte parity with Jekyll/Kramdown or freeze incidental current markup.
Jekyll/Kramdown output is not the benchmark for the Python renderer, and the migration should not add automated comparison checks against current Jekyll-rendered HTML.

The target is a better Docs Viewer v2 content pipeline that supports what the site actually needs:

- generated Docs Viewer JSON payloads
- rendered `content_html` that preserves document meaning, links, headings, media, interactive embeds, and custom-token output
- generated plain text that is useful for search
- generated semantic reference payloads
- generated docs/search indexes
- browser behavior in Docs Viewer and public read-only installs
- room to change token syntax, preprocessing, renderer library, or viewer UI behavior when that is the best solution

The public site consumes generated HTML/data assets. Jekyll currently provides public routing stubs and public-site preview/build mechanics; it does not own critical Markdown-to-HTML conversion for the app surfaces covered by this request and should not define the Docs Viewer content-generation contract.

## Markdown Library Decision

The Python Docs Viewer builder should use a third-party Markdown library for Markdown parsing and HTML rendering. It should not hand-roll a Markdown parser.

Recommended default: use `markdown-it-py`, pinned in `requirements.txt`, with the smallest enabled syntax set that satisfies the acceptance fixtures.

Rationale:

- `markdown-it-py` has a CommonMark baseline, configurable parsing rules, and a plugin model. Its docs describe core support for GFM-style tables, strikethrough, task lists, and alerts, with additional plugins available through `mdit-py-plugins`.
- The token/rule architecture is a better fit for Docs Viewer v2 than treating Markdown as opaque text forever. The first implementation may still preprocess current custom tokens before rendering, but the library leaves room to move media, interactive HTML, and semantic reference handling into explicit parser/renderer rules later.
- CommonMark gives the app a clearer future contract than the current incidental Jekyll/Kramdown output. The request already accepts that generated HTML is not byte-for-byte stable, and does not treat current Jekyll/Kramdown output as a reference baseline.
- The project already accepts focused Python dependencies for Docs Viewer import behavior (`beautifulsoup4`, `lxml`, `bleach`, `Pillow`). A pinned Markdown renderer is a similar app-runtime dependency and is easier to reason about than keeping Ruby/Jekyll in the app path.

Pros of using a third-party Markdown library:

- avoids owning the full Markdown parsing surface, including nested lists, fenced code, raw HTML blocks, escaping, links, images, tables, and edge cases
- reduces implementation time and parser-bug risk
- gives a documented syntax baseline for future authoring guidance
- supports focused acceptance fixtures around document semantics instead of parser internals
- keeps Markdown rendering in-process in Python, without Bundler, Ruby, Jekyll site initialization, or subprocess helpers

Cons and controls:

- rendered HTML will differ from current Jekyll/Kramdown output in some cases; this is acceptable because current output is not the benchmark
- fixture checks should assert the desired Docs Viewer v2 semantics directly, not compare Python output to Jekyll/Kramdown output
- parser/plugin choices become a content contract; pin the package version and record enabled plugins in the builder tests/docs
- raw HTML output is not a sanitization boundary; keep import sanitization and viewer safety rules explicit, and use `bleach` where imported/untrusted HTML needs filtering
- custom Docs Viewer semantics should remain builder-owned, not hidden inside a third-party plugin with unclear output contracts
- dependency upgrades need fixture review for representative docs, custom tokens, search text, and semantic references

Candidate assessment:

| library | fit | notes |
| --- | --- | --- |
| `markdown-it-py` | preferred | CommonMark baseline, configurable rules, plugin architecture, GFM-adjacent options, and a token pipeline that can support Docs Viewer-specific renderer rules over time. |
| `Python-Markdown` (`markdown`) | acceptable fallback | Mature and extensible, but its docs explicitly say it is not a CommonMark implementation. Better fit for MkDocs-style ecosystems than for defining a new Docs Viewer v2 content contract. |
| `mistune` | acceptable fallback | Fast Python Markdown parser with renderers and plugins, but less aligned with the CommonMark/GFM-compatible ecosystem direction than `markdown-it-py` for this use case. |
| hand-rolled parser | not recommended | Too much syntax surface and too much long-term maintenance risk for little benefit. Use custom code only for Docs Viewer-specific tokens, metadata, generated references, post-processing, and search text extraction. |

Initial implementation guidance:

- add `markdown-it-py` to `requirements.txt` with an exact version
- start from `MarkdownIt("commonmark")`
- enable only syntax needed by current authored docs and acceptance fixtures, likely tables first if required
- keep current media, interactive HTML, and semantic reference token handling explicit in the Python builder
- add fixtures before switching callers, covering headings, links, lists, fenced code, inline code, raw HTML allowed by the current content model, tables if enabled, media tokens, interactive HTML tokens, semantic references, generated plain text, and generated reference payloads
- do not add Jekyll/Kramdown parity fixtures or automated current-output comparison checks
- treat catalogue prose rendering as a second consumer of the same Python Markdown rendering helper where practical, so work, series, and moment `content_html` stop using `render_markdown_with_jekyll.rb`

## Builder Replacement Details

### Python Docs Builder

The Python replacement for `docs-viewer/build/build_docs.py` should own:

- source discovery for configured scopes
- Markdown front matter parsing
- custom token expansion for media, interactive HTML, and semantic references
- Markdown to HTML rendering after token expansion
- plain-text extraction for search
- semantic reference record generation
- `viewable`, `parent_id`, `ui_status`, source path, content URL, and viewer URL projection
- writing `docs-viewer/generated/docs/<scope>/index.json`
- writing `docs-viewer/generated/docs/<scope>/by-id/<doc_id>.json`
- stable generated payload schema

The first implementation should include acceptance fixtures that cover representative Markdown, every custom token behavior, rendered HTML semantics, generated text, and semantic references before switching the watcher. If v2 changes token syntax, include migration fixtures for old and new authored forms.

### Python Docs Search Builder

The Python replacement for `docs-viewer/build/build_search.rb` should own:

- reading generated docs payloads
- applying viewability rules
- producing the current search index schema
- scope-specific writes
- stable version/hash calculation
- `--write` and dry-run modes matching current command behavior

### Python Catalogue Search Builder

The Python replacement for `studio/services/catalogue/search/build_search.rb` should own:

- reading canonical catalogue JSON
- producing the current catalogue search index contract
- preserving public search behavior
- supporting dry-run and write modes
- fitting the existing Python catalogue service/generator layout

## Verification

App/runtime verification:

- Local Studio home smoke.
- Local Studio catalogue editor route smoke.
- Local Analytics tag route smoke.
- Local Analytics/Data Sharing route smoke.
- Docs Viewer management smoke for `/docs/`.
- UI Catalogue smoke.
- Syntax/import checks for changed Python and JavaScript.

Docs Viewer v2 builder acceptance verification:

- generated docs index shape checks for a fixture scope
- generated docs by-id payload shape checks for representative docs
- rendered HTML/text checks for media, interactive HTML, and semantic reference behavior
- generated semantic reference payload checks
- docs search index shape checks for a fixture scope
- catalogue search index shape checks for representative catalogue records
- dry-run/write behavior checks for each replacement builder

Public-site verification, kept separate:

- explicit Jekyll build into a temporary destination
- public preview route checks for public pages
- public `/library/` and `/analysis/` checks

## Acceptance Criteria

The request is complete when:

- app runtimes and app-facing generators use JavaScript + Python
- Docs Viewer v2 generated docs payloads are built by Python
- Docs Viewer search indexes are built by Python
- catalogue search indexes used by apps/public search are built by Python
- local app startup does not use Ruby/Jekyll
- live rebuild watchers call Python builders
- remaining Ruby files and commands are documented as manual public-site preview/build only
- public-site Jekyll preview/build still works when explicitly run

## Known Risks

- Markdown rendering can differ when moving away from Jekyll/Kramdown. Docs Viewer v2 should not chase full Kramdown parity, freeze incidental current HTML, or use current Jekyll/Kramdown output as an automated comparison baseline. It should protect document meaning, links, media behavior, semantic references, and search text through explicit semantic fixtures.
- Custom token handling is part of the required builder behavior, but the exact syntax is open to change. Media, interactive HTML, and semantic reference behavior need explicit Python implementations, migration rules when syntax changes, and fixtures.
- Search index compatibility depends on matching text normalization, visibility filtering, and version/hash rules. Treat this as a contract, not an incidental implementation detail.
- Catalogue search affects public search behavior as well as local app links. Preserve the output schema before changing consumers.
- Some generated assets are shared between app runtime and public preview. The owner should be Python if apps need the asset; Jekyll should only consume it.
- Leaving Jekyll as manual preview means public-site checks remain Ruby-backed until a separate public renderer migration exists.

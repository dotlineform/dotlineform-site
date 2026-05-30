---
doc_id: site-request-rubyless-app-runtimes
title: Rubyless App Runtimes Request
added_date: 2026-05-30
last_updated: 2026-05-30
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

When `build_docs.rb` was first built, piggy-backing on the local Jekyll server and Jekyll's Markdown converter saved development time. At that point Docs Viewer was a proof of concept, and using the existing public-site toolchain was a reasonable way to get Markdown rendered into usable HTML quickly.

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

## Goals

- replace `docs-viewer/build/build_docs.rb` with a Python Docs Viewer payload builder, including the current custom Markdown token pipeline
- replace `docs-viewer/build/build_search.rb` with a Python Docs Viewer search builder
- replace `studio/services/catalogue/search/build_search.rb` with a Python catalogue search builder
- remove app-facing dependencies on `studio/shared/ruby/jekyll_markdown_renderer.rb`, `studio/shared/ruby/render_markdown_with_jekyll.rb`, and Jekyll server helper modules
- make docs live rebuilds call Python builders
- make local app launchers start Python/JS app runtimes only
- keep `bin/public-site-build`, Bundler, and Jekyll documented as public-site preview/build tooling only
- preserve the generated JSON shape and useful content semantics while allowing deliberate Docs Viewer v2 improvements to token syntax, preprocessing, rendering, and browser behavior

## Non-Goals

- replacing the public site renderer in this request
- removing `.ruby-version`, `Gemfile`, or Jekyll while the public site still uses them
- accidental app UI behavior changes caused only by swapping implementation language
- moving local write services into JavaScript
- making browser code write to the filesystem directly

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Build the Python Docs Viewer payload builder that replaces `docs-viewer/build/build_docs.rb`. It should read Markdown source and scope config, parse front matter, apply the custom token pipeline, render document HTML/text, write `index.json` and `by-id/*.json`, and preserve the generated Docs Viewer data shape. |
| 2 | planned | Switch Docs Viewer docs generation callers to the Python builder. Update live rebuild watcher, local app commands, docs, and tests so Docs Viewer payloads no longer require Ruby or Jekyll rendering. |
| 3 | planned | Build the Python Docs Viewer search builder that replaces `docs-viewer/build/build_search.rb`. It should consume generated docs payloads, preserve current search index schema/versioning behavior, and support scope-specific writes. |
| 4 | planned | Switch Docs Viewer search generation callers to the Python builder. Update live rebuild watcher, local app commands, docs, and tests so docs search no longer requires Ruby. |
| 5 | planned | Build the Python catalogue search builder that replaces `studio/services/catalogue/search/build_search.rb`. Preserve the current catalogue search index contract consumed by public search and local app links. |
| 6 | planned | Retire app-facing Ruby markdown/Jekyll helpers. Remove or isolate `studio/shared/ruby/jekyll_markdown_renderer.rb`, `studio/shared/ruby/render_markdown_with_jekyll.rb`, and `studio/shared/ruby/jekyll_webrick_client_reset_filter.rb` from app/data-generation paths. Any remaining use must be public-preview-only. |
| 7 | planned | Make `bin/local-studio` and related app launchers Python/JS only. They may expose configured public preview URLs, but they must not start, check, or require Jekyll for app health. |
| 8 | planned | Confirm Studio is JavaScript + Python only. `/studio/`, route shells, runtime config, catalogue editors, audits, activity, Docs links, and APIs should run from Python server + JS frontend + Python builders. |
| 9 | planned | Confirm Analytics is JavaScript + Python only. Analytics routes, tag workflows, Data Sharing flows, runtime config, generated app data, and APIs should not depend on Ruby/Jekyll. |
| 10 | planned | Confirm Docs Viewer management is JavaScript + Python only. `/docs/` management, source mutations, scope config, generated docs payloads, and generated search should all be Python/JS. Public `/library/` and `/analysis/` remain public-site preview concerns. |
| 11 | planned | Confirm UI Catalogue is JavaScript + Python/static only. Serve demos without Jekyll and keep public-site integration checks separate. |
| 12 | planned | Update command docs and runtime docs. Describe Ruby only under manual public preview/build, and describe Docs Viewer generation, search generation, catalogue search generation, app servers, and live rebuilds as Python/JS. |
| 13 | planned | Final closeout. Run app smoke checks, Docs Viewer v2 builder acceptance checks, catalogue search contract checks, and a separate manual-public-site/Jekyll build check. Record any remaining Ruby usage as public-preview-only or deferred public-site renderer work. |

## Current Custom Token Implementation

The current custom Markdown behavior is not a Jekyll plugin or a separate Ruby token library.

`docs-viewer/build/build_docs.rb` owns the custom token pipeline directly:

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

The target is a better Docs Viewer v2 content pipeline that supports what the site actually needs:

- generated Docs Viewer JSON payloads
- rendered `content_html` that preserves document meaning, links, headings, media, interactive embeds, and custom-token output
- generated plain text that is useful for search
- generated semantic reference payloads
- generated docs/search indexes
- browser behavior in Docs Viewer and public read-only installs
- room to change token syntax, preprocessing, renderer library, or viewer UI behavior when that is the best solution

The public site consumes generated HTML/data assets. Jekyll currently provides public routing stubs and public-site preview/build mechanics; it should not define the Docs Viewer content-generation contract.

## Builder Replacement Details

### Python Docs Builder

The Python replacement for `docs-viewer/build/build_docs.rb` should own:

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

- Markdown rendering can differ when moving away from Jekyll/Kramdown. Docs Viewer v2 should not chase full Kramdown parity or freeze incidental current HTML; it should protect document meaning, links, media behavior, semantic references, and search text.
- Custom token handling is part of the required builder behavior, but the exact syntax is open to change. Media, interactive HTML, and semantic reference behavior need explicit Python implementations, migration rules when syntax changes, and fixtures.
- Search index compatibility depends on matching text normalization, visibility filtering, and version/hash rules. Treat this as a contract, not an incidental implementation detail.
- Catalogue search affects public search behavior as well as local app links. Preserve the output schema before changing consumers.
- Some generated assets are shared between app runtime and public preview. The owner should be Python if apps need the asset; Jekyll should only consume it.
- Leaving Jekyll as manual preview means public-site checks remain Ruby-backed until a separate public renderer migration exists.

---
doc_id: site-change-log
title: Site Change Log
last_updated: 2026-03-31
parent_id: ""
sort_order: 110
---

# Site Change Log

## [2026-04-01] Made work prose optional in catalogue generation

**Status:** implemented

**Area:** scripts

**Summary:**  
`generate_work_pages.py` no longer treats missing work prose mappings or missing work prose source files as a reason to skip work page or work JSON generation.

**Reason:**  
Work prose files are intentionally rare in this repo. Missing prose should show up as absent page prose on the site, not block unrelated metadata, routing, or JSON refresh.

**Effect:**  
`_works/<work_id>.md` stubs and `assets/works/index/<work_id>.json` now continue to generate when `Works.work_prose_file` is empty, unresolved, or points at a missing file. In those cases the work payload is written without prose content rather than emitting a per-work warning and skipping the record.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)

**Notes:**  
This changes only the work-prose boundary. Series and moment prose handling still follows their existing rules.

## [2026-04-01] Added workbook-aware planning to the catalogue pipeline entrypoint

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now plans workbook-backed generation before it runs, using a persisted planner state file to infer affected work IDs, series IDs, and moment IDs instead of requiring those scopes to be supplied manually most of the time.

**Reason:**  
The previous pipeline wrapper still depended on the user to translate workbook edits into `--mode`, `--work-ids`, `--series-ids`, and `--moment-ids`. That made safe incremental rebuilds harder to reason about and kept future pipeline enhancements tightly coupled to manual operator knowledge.

**Effect:**  
Default `./scripts/build_catalogue.py` runs now compare workbook-backed source records against `var/build_catalogue_state.json`, print an execution plan, skip generate/search when nothing relevant changed, and persist the new planner state after successful write runs. Copy/srcset stages remain draft-driven for now, so published media-only changes still need explicit flags.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- `.gitignore`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**  
Removed workbook rows can still leave stale generated files behind. The planner currently improves incremental rebuild targeting, not deletion cleanup.

## [2026-03-30] Removed the docs compatibility mirror and legacy Studio doc-link fallback

**Status:** implemented

**Area:** architecture

**Summary:**  
Removed the flat Studio docs compatibility output and retired the old legacy-link fallback from the docs builder so the published docs data contract is now scope-owned only.

**Reason:**  
The repo now uses explicit scope-owned viewer routes and scoped docs JSON outputs. Keeping the old mirror and legacy path rewrite added dormant complexity without protecting any core site functionality.

**Effect:**  
The docs builder now writes only `assets/data/docs/scopes/studio/` and `assets/data/docs/scopes/library/`, legacy `/docs/.../` path rewriting is gone, Studio source-doc links now use `/docs/?scope=studio&doc=...`, and the shared docs viewer normalizes incoming Studio viewer URLs onto the scoped route.

**Affected files/docs:**  
- `scripts/build_docs.rb`
- `assets/js/docs-viewer.js`
- `AGENTS.md`
- `studio/index.md`
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)

## [2026-03-30] Documented when the shared docs viewer runtime should and should not fork

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a dedicated site-architecture note describing the current boundary between scope-specific docs route shells and the shared docs viewer runtime, including concrete examples of changes that should remain shell-level and the kinds of divergence that would justify a runtime fork later.

**Reason:**  
The docs system now serves both Studio and library scopes through one viewer runtime. The repo needed an explicit guardrail so future scope-specific changes can be evaluated against a stable “do not fork unless the product model changes” rule.

**Effect:**  
There is now a stable reference for deciding whether a new docs requirement belongs in route-shell composition, scope-owned data, a small shared option, or a true runtime split.

**Affected files/docs:**  
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Architecture](/docs/?scope=studio&doc=architecture)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)

**Notes:**  
The current recommendation remains to keep one docs viewer runtime and allow route-level shells to diverge as needed.

## [2026-03-30] Split the scripts reference into a high-level overview and child docs

**Status:** implemented

**Area:** documentation

**Summary:**  
Reduced the old scripts overview into the current [Scripts](/docs/?scope=studio&doc=scripts) navigation page and moved command-level script usage into dedicated child documents.

**Reason:**  
The single overview page had accumulated too much detailed operational content to remain useful as a quick architectural entry point.

**Effect:**  
The scripts docs are now easier to scan at the top level, while script-specific flags, outputs, and workflow notes have stable dedicated docs such as [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder), [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages), and [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server).

**Affected files/docs:**  
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
- `AGENTS.md`

**Notes:**  
Script-specific documentation should now be added to the relevant `scripts-*.md` child doc rather than expanding the overview again.

## [2026-03-30] Added config-backed docs media tokens for remote images

**Status:** implemented

**Area:** architecture

**Summary:**  
Extended the docs-data builder so docs bodies can use `[[media:...]]` tokens that resolve against `_config.yml` `media_base` before Markdown rendering.

**Reason:**  
Library docs need to support remotely hosted full-size images without hardcoding the full media origin in every document and without storing full-size docs images in the repo.

**Effect:**  
Docs can now stay as ordinary `.md` source files while embedding raw HTML and config-backed remote media URLs, keeping the repo aligned with the “repo holds text and thumbnails, R2 holds full media” principle.

**Affected files/docs:**  
- `scripts/build_docs.rb`
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**  
This change does not add native `.html` source ingestion. The intended authoring model remains `.md` files with YAML front matter, optionally containing raw HTML bodies.

## [2026-03-30] Made the docs library scope-aware and added a separate library docs route

**Status:** implemented

**Area:** architecture

**Summary:**  
Refactored the docs viewer data/build contract to support separate `studio` and `library` docs scopes, kept `/docs/` as the Studio docs route, and converted `/library/` from a stub page into a library-scoped docs viewer.

**Reason:**  
The existing docs system implicitly belonged to the Studio domain even though the code and data layout were still flat. Additional docs domains needed scope-owned routes and artifacts before library content could grow cleanly.

**Effect:**  
Studio docs now build into a scope-owned output tree under `assets/data/docs/scopes/studio/`, library docs have their own source root and scoped output tree, `/docs/?scope=studio&doc=...` is now the explicit Studio docs contract, and `/library/` now hosts the library docs viewer.

**Affected files/docs:**  
- `scripts/build_docs.rb`
- `assets/js/docs-viewer.js`
- `docs/index.md`
- `library/index.md`
- `_includes/docs_viewer_shell.html`
- `_docs_library_src/library.md`
- `_layouts/default.html`
- [Scripts](/docs/?scope=studio&doc=scripts)

## [2026-03-30] Added lightweight build-version cache busting to shared shell assets

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a lightweight build-version query token to shared shell CSS and JS asset URLs, using the current build timestamp rather than a separate fingerprint pipeline.

**Reason:**  
Local review was vulnerable to stale browser caches after JS/CSS renames or runtime changes, especially while the public search surface was moving and being renamed.

**Effect:**  
Shared shell assets now reload more reliably after a rebuild, the default layout publishes the current asset version in page metadata, and the search runtime can align its own module/data cache busting with that same build token.

**Affected files/docs:**  
- `_layouts/default.html`
- `_layouts/work.html`
- `_layouts/work_details.html`
- `_layouts/series.html`
- `_layouts/moment.html`
- `search/index.md`
- `assets/js/search/search-page.js`
- `assets/studio/js/studio-config.js`
- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)

**Notes:**  
This is a pragmatic cache-busting layer for the current static setup. It is not a full hashed-asset pipeline.

## [2026-03-30] Merged moments browsing into the works catalogue

**Status:** implemented

**Area:** works

**Summary:**  
Merged the public moments index UI into the `/series/` works catalogue so one catalogue page now switches between `works` and `moments` with shared view, sort, and pagination controls.

**Reason:**  
The separate moments index duplicated the same catalogue interaction pattern and made the top-level browsing navigation more fragmented than it needed to be.

**Effect:**  
The public top nav now exposes only `works`, `/series/` owns the combined catalogue UI, individual moment pages keep their existing `/moments/<moment_id>/` URLs, and the standalone `/moments/` landing page is no longer published.

**Affected files/docs:**  
- `series/index.md`
- `moments/index.md`
- `_layouts/default.html`
- `assets/css/main.css`
- `assets/studio/data/studio_config.json`
- [Data Flow](/docs/?scope=studio&doc=data-flow)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)

**Notes:**  
The main regression risk is state handling when switching between works and moments modes on the merged catalogue page.

## [2026-03-29] Normalized published site and Studio doc references to docs-viewer links

**Status:** implemented

**Area:** architecture

**Summary:**  
Updated published site and Studio docs so references to other published docs now use `/docs/?scope=studio&doc=...` links instead of raw filenames or legacy doc URLs.

**Reason:**  
The docs set is increasingly used through the in-site viewer. Linking published docs through the viewer makes cross-document navigation consistent and keeps repo file references reserved for actual source files and unpublished notes.

**Effect:**  
Published docs now read more cleanly as a connected documentation system, while literal output paths, unpublished docs, and non-doc repo files remain explicit where needed.

**Affected files/docs:**  
- [Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [CSS Audit Spec](/docs/?scope=studio&doc=css-audit-spec)
- [Studio](/docs/?scope=studio&doc=studio)
- [Tag Editor](/docs/?scope=studio&doc=tag-editor)
- [Series Tags](/docs/?scope=studio&doc=series-tags)

**Notes:**  
This change updates documentation navigation only; it does not change site runtime or pipeline behaviour.

## [2026-03-29] Established a dedicated site-wide change log for non-search history

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a dedicated [Site Change Log](/docs/?scope=studio&doc=site-change-log) plus supporting guidance so meaningful non-search site and Studio changes now have a focused historical record separate from search.

**Reason:**  
Search has become complex enough to justify its own subsystem log. The rest of the site still needs a concise historical record, but should not be mixed into the search log.

**Effect:**  
Future review of non-search development can now happen without reconstructing history from scattered commits or overloading the search change log.

**Affected files/docs:**  
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)
- [Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)
- `AGENTS.md`

**Notes:**  
This log should be updated for meaningful non-search site, Studio, and pipeline changes as part of normal close-out.

## [2026-03-20] Moved work-detail runtime to per-work JSON and retired the old aggregate work-details flow

**Status:** implemented

**Area:** works

**Summary:**  
Shifted work-detail runtime behaviour so work detail pages resolve from per-work JSON instead of relying on the old aggregate work details index flow.

**Reason:**  
The older aggregate flow added unnecessary coupling and no longer matched the JSON-first direction of the site data model.

**Effect:**  
Work detail runtime became simpler and closer to the canonical per-work data flow. The retired aggregate path and related sitemap/runtime dependencies were removed.

**Affected files/docs:**  
- `_layouts/work_details.html`
- `_layouts/work.html`
- `scripts/generate_work_pages.py`
- `scripts/audit_site_consistency.py`
- [Data Flow](/docs/?scope=studio&doc=data-flow)

**Notes:**  
This was part of the wider JSON-first site architecture shift.

## [2026-03-29] Search-specific history moved out of the general site history

**Status:** implemented

**Area:** architecture

**Summary:**  
Confirmed that search history should live in [Search Change Log](/docs/?scope=studio&doc=search-change-log) rather than the broader site log.

**Reason:**  
Search now has its own artifact, UI surface, policy surface, and document set, so combining it with wider site history would make both logs less useful.

**Effect:**  
The site log remains focused on the wider site and non-search Studio development, while search history is reviewed through its own dedicated log.

**Affected files/docs:**  
- [Search Change Log](/docs/?scope=studio&doc=search-change-log)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)
- [Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)

**Notes:**  
For changes that materially affect both areas, add short entries to both logs.

## [2025-08-19] Adopted JSON-first site data flow for works, series, and moments indexes

**Status:** implemented

**Area:** build pipeline

**Summary:**  
Shifted the main site toward generated JSON artifacts as the primary runtime data layer for works, series, and moments, with lighter collection stubs and index-driven runtime behaviour.

**Reason:**  
The site needed a more consistent and maintainable data flow than page-heavy or mixed-source runtime patterns.

**Effect:**  
The site now relies more heavily on generated JSON contracts and index artifacts, which simplified runtime logic and created a clearer basis for later features such as Studio tooling and search.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- `assets/data/works_index.json`
- `assets/data/series_index.json`
- `assets/data/moments_index.json`
- [Data Flow](/docs/?scope=studio&doc=data-flow)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**  
This entry summarizes the broader architectural shift rather than one single commit.

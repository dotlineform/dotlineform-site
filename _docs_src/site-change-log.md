---
doc_id: site-change-log
title: "Site Change Log"
last_updated: 2026-04-20
parent_id: ""
sort_order: 270
---
# Site Change Log

## [2026-04-20] Added design guidance to the panel primitive reference and refined the Studio landing composition

**Status:** implemented

**Area:** design system / primitive guidance

**Summary:**
Extended the panel primitive reference so it records design guidance as well as technical behavior, removed the hidden text-width cap from the shared panel-link copy, and narrowed the `/studio/` landing-page card grid so the short-copy entry panels sit in centered columns.

**Reason:**
The panel-link variation is a working design reference, not just a technical spec. The old text measure made the copy look like it was wrapping inside an invisible container, and the full-width equal-fill landing-page grid made short-copy cards feel too stretched.

**Effect:**
Panel-link copy now wraps to the panel width itself, the `/studio/` entry cards use a narrower centered composition, and the primitive docs now explicitly include design guidance where sizing and composition choices affect correct reuse.

**Affected files/docs:**
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [UI Primitive: Panel](/docs/?scope=studio&doc=ui-primitive-panel)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `assets/studio/css/studio.css`
- `assets/css/main.css`

**Notes:**
This keeps the other dashboard routes on the shared fixed-height panel-link variation without redesigning their grid width.

## [2026-04-20] Unified Studio landing/dashboard cards as a shared panel-link variation

**Status:** implemented

**Area:** design system / Studio dashboard UI

**Summary:**
Moved the clickable Studio landing page and analytics/library/search dashboard card styling out of the site-wide stylesheet and into the shared Studio primitive layer as a fixed-height panel-link variation with optional image fill.

**Reason:**
The same panel design had split into two duplicated route-local patterns, and the analytics/library/search version was auto-sizing to content instead of behaving like a deliberate design-time panel.

**Effect:**
`/studio/`, `/studio/analytics/`, `/studio/library/`, and `/studio/search/` now use the same shared panel-link primitive. The panel height is fixed, hover/focus behavior still applies to the whole card, and the panel primitive reference now defines the image-fill option and short-copy requirement.

**Affected files/docs:**
- [UI Primitive: Panel](/docs/?scope=studio&doc=ui-primitive-panel)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `assets/studio/css/studio.css`
- `assets/css/main.css`
- `studio/index.md`
- `studio/analytics/index.md`
- `studio/library/index.md`
- `studio/search/index.md`

**Notes:**
This intentionally favors future design consistency over preserving the old content-fit dashboard card behavior.

## [2026-04-20] Added explicit nested-panel support and strengthened the primitive-catalogue method

**Status:** implemented

**Area:** design system / primitive governance

**Summary:**
Extended the panel primitive reference with a deliberate nested-panel variation and updated the catalogue docs so primitive pages are treated as shared-system pressure tests rather than protective demos.

**Reason:**
Container primitives can validly compose with themselves. If the catalogue hides that case or explains it away as surrounding-environment noise, live pages can keep accumulating one-off compensation that masks shared primitive defects.

**Effect:**
Nested panels are now documented as a supported panel composition, direct child panels inherit a subordinate inner-surface treatment from the shared primitive, and the UI catalogue docs now state that shared defects should be fixed at source even when that exposes legacy drift.

**Affected files/docs:**
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [UI Primitive: Panel](/docs/?scope=studio&doc=ui-primitive-panel)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/ui-catalogue/panel/index.md`
- `_includes/studio_ui_catalogue_panel_demo.html`
- `_includes/ui_catalogue_notes/panel.md`
- `assets/studio/css/studio.css`

**Notes:**
This is an intentional shared-source change. A future cleanup pass should look for live pages that still compensate locally for panel composition.

## [2026-04-20] Corrected the panel primitive reference template to use a neutral demo surface

**Status:** implemented

**Area:** design system / Studio UI catalogue

**Summary:**
Updated the first UI primitive reference so shared panels are shown without enclosing section panels and with vertically stacked variants.

**Reason:**
The original page nested the live panel examples inside outer panel shells, which made the editor variant look like it overlapped its container and blurred the line between a primitive defect and a page-composition problem.

**Effect:**
The panel catalogue page now shows the primitive on a neutral surface, implementation notes focus on concrete code-level warnings, and the Studio UI docs now define neutral-surface rendering as the default pattern for future primitive pages.

**Affected files/docs:**
- [UI Primitive: Panel](/docs/?scope=studio&doc=ui-primitive-panel)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/ui-catalogue/panel/index.md`
- `_includes/studio_ui_catalogue_panel_demo.html`
- `_includes/ui_catalogue_notes/panel.md`
- `assets/studio/css/studio.css`

**Notes:**
This change improves the primitive-reference contract rather than changing the shared panel shell itself.

## [2026-04-19] Added the first UI catalogue and screenshot asset folders

**Status:** implemented

**Area:** design system / docs structure

**Summary:**
Added a dedicated UI catalogue parent doc with first-pass primitive child docs and matching versioned asset folders for screenshots and visual references.

**Reason:**
Shared primitives were becoming hard to keep visible inside larger framework docs, and visual component guidance needs a stable home for screenshots as the catalogue grows.

**Effect:**
[UI Catalogue](/docs/?scope=studio&doc=ui-catalogue) now sits under [Design](/docs/?scope=studio&doc=design), the first primitive docs cover `panel`, `button`, `input`, `list shell`, `toolbar`, and `modal shell`, and screenshot assets now have dedicated repo paths under `assets/docs/ui-catalogue/`.

**Affected files/docs:**
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Design](/docs/?scope=studio&doc=design)
- `assets/docs/ui-catalogue/`

**Notes:**
This establishes the structure for future per-primitive and more complex component docs.

## [2026-04-19] Revisited the CSS refactor strategy and restored it to the active design docs

**Status:** implemented

**Area:** design system / CSS governance

**Summary:**
Updated the CSS refactor guidance so it reflects the current UI-system direction rather than an older point-in-time cleanup note.

**Reason:**
The original refactor doc had drifted out of view during newer work and its `last_updated` date no longer reflected the fact that it had been revisited conceptually.

**Effect:**
[CSS Refactor](/docs/?scope=studio&doc=css-refactor) now records the current strategy: formalize tokens, primitives, compositions, and behavior boundaries first; avoid defaulting passive visual shells to JS web components; and keep the document visible from [Design](/docs/?scope=studio&doc=design).

**Affected files/docs:**
- [CSS Refactor](/docs/?scope=studio&doc=css-refactor)
- [Design](/docs/?scope=studio&doc=design)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)

**Notes:**
This is documentation and governance work, not a runtime UI change.

## [2026-04-19] Flattened the Studio docs source tree for Docs Viewer management

**Status:** implemented

**Area:** Docs Viewer / docs infrastructure

**Summary:**
Flattened Studio docs into `_docs_src/*.md` and aligned the builder and management planning with that flat-source model.

**Reason:**
Viewer-side docs management depends on front-matter-driven hierarchy rather than filesystem folders. Keeping Studio docs nested on disk would make tree edits more confusing and harder to validate.

**Effect:**
Studio docs now live directly under `_docs_src/`, the shared docs-builder contract rejects nested Markdown docs, and Docs Viewer management can treat the visible tree as metadata-only.

**Affected files/docs:**
- `_docs_src/*.md`
- `scripts/build_docs.rb`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Viewer Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)

**Notes:**
This was the enabling storage change for local Docs Viewer management.

## [2026-04-19] Consolidated Studio UI triage into rules and UI requests docs

**Status:** implemented

**Area:** Studio UI workflow

**Summary:**
Replaced the temporary UI polish punch-list workflow with a permanent Studio UI rules log and a dedicated UI requests section.

**Reason:**
IAB-driven UI work needs a durable way to distinguish one-off fixes from permanent rules, and the older punch-list format overlapped with that goal.

**Effect:**
[Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules) now captures issue triage and systemic rules, while [UI Requests](/docs/?scope=studio&doc=ui-requests) holds UI feature specs and task docs such as the Docs Viewer favourites request.

**Affected files/docs:**
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [UI Requests](/docs/?scope=studio&doc=ui-requests)
- [Site Docs](/docs/?scope=studio&doc=site-docs)

**Notes:**
This establishes the standing local-Codex UI workflow in place of PR-based tracking.

## [2026-04-19] Added shared Docs Viewer favourites for docs and library

**Status:** implemented

**Area:** Docs Viewer

**Summary:**
Added browser-style document favourites shared by `/docs/` and `/library/`.

**Reason:**
Frequently used docs needed a quicker return path than the tree alone, especially once the shared viewer started carrying search and management controls.

**Effect:**
The shared Docs Viewer now supports IndexedDB-backed favourites, star-based add/remove, compact editable bookmark pills, and a full-width viewer-level controls band above the index and content panels.

**Affected files/docs:**
- `_includes/docs_viewer_shell.html`
- `assets/js/docs-viewer.js`
- `assets/css/main.css`
- [Docs Viewer Favourites Spec](/docs/?scope=studio&doc=docs-viewer-favourites-spec)
- [Docs Viewer Favourites Task](/docs/?scope=studio&doc=docs-viewer-favourites-task)

**Notes:**
Private browsing still limits persistence, so this remains a browser-local feature rather than a hosted user-account feature.

## [2026-04-19] Implemented local Docs Viewer management mode

**Status:** implemented

**Area:** Docs Viewer / local server

**Summary:**
Added the first local-only management mode for the shared Docs Viewer.

**Reason:**
Managing docs directly from the viewer is faster than editing source files by hand, but it needs an explicit local write boundary and a clear opt-in mode.

**Effect:**
`/docs/` and `/library/` now expose manage mode behind `?mode=manage`, backed by `scripts/docs/docs_management_server.py` for create, archive, delete-preview, and delete-apply on flat source docs.

**Affected files/docs:**
- `scripts/docs/docs_management_server.py`
- `_includes/docs_viewer_shell.html`
- `assets/js/docs-viewer.js`
- `bin/dev-studio`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Notes:**
The feature is local-only and fails closed when the docs-management server is unavailable.

## [2026-04-19] Hardened Docs Viewer management reloads and move behavior

**Status:** implemented

**Area:** Docs Viewer / local server

**Summary:**
Refined Docs Viewer management so local development writes refresh reliably and drag/drop moves stay low-noise.

**Reason:**
The Jekyll dev server could continue serving stale docs assets after local writes, and early move behavior created too much sort-order and backup noise.

**Effect:**
Post-write reloads now fetch fresh docs/search payloads from the localhost docs-management server, create inserts after the currently selected doc, delete clears its completion banner when applied, backups are operation-scoped, drag/drop supports leaf-doc-only front-matter moves, sibling sort orders are left unchanged, and move skips search-index rebuilds.

**Affected files/docs:**
- `scripts/docs/docs_management_server.py`
- `assets/js/docs-viewer.js`
- `assets/css/main.css`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Notes:**
Only leaf docs are draggable; folders and docs with children remain fixed.

## [2026-04-19] Added Studio execution-prep coverage for the implemented routes

**Status:** implemented

**Area:** Studio testing workflow

**Summary:**
Added a dedicated Studio execution-prep checklist for the implemented Studio routes.

**Reason:**
The Studio surface had grown large enough that ad hoc testing no longer gave a reliable view of route coverage or failure triage.

**Effect:**
The execution-prep docs now spell out prerequisites, manual versus Codex execution, route coverage, public-runtime follow-through checks, responsive checks, and a failure-triage model.

**Affected files/docs:**
- [Studio End-To-End Checklist](/docs/?scope=studio&doc=new-pipeline-studio-end-to-end-checklist)
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)

**Notes:**
This is planning and operational guidance rather than a runtime feature.

## [2026-04-19] Completed internal generator cleanup for the JSON-led workflow

**Status:** implemented

**Area:** catalogue pipeline

**Summary:**
Removed the remaining workbook-oriented runtime path from the internal generator flow and aligned the bulk-import workbook configuration.

**Reason:**
The live catalogue workflow is now JSON-led, so the residual workbook branch and workbook-specific defaults were creating unnecessary complexity and stale assumptions.

**Effect:**
`generate_work_pages.py` now runs only the internal JSON-source path, moment-scoped rebuilds share that same internal boundary, `_data/pipeline.json` now points bulk import at `data/works_bulk_import.xlsx`, and the importer no longer assumes `data/works.xlsx`.

**Affected files/docs:**
- `scripts/generate_work_pages.py`
- `_data/pipeline.json`
- `/studio/bulk-add-work/`
- `AGENTS.md`
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)

**Notes:**
This closes out the workbook-oriented runtime assumptions without changing the hosted public site model.

## [2026-04-18] Implemented Studio shell foundations for the admin surface

**Status:** implemented

**Area:** Studio shell

**Summary:**
Added the first dedicated Studio shell and dashboard structure.

**Reason:**
Studio needed its own navigation and landing surface so internal tools could grow without distorting the public site navigation.

**Effect:**
The public nav stays user-facing, Studio now has its own admin nav, `/studio/` is a four-panel landing page, and domain dashboards now live under `/studio/catalogue/`, `/studio/library/`, `/studio/analytics/`, and `/studio/search/`.

**Affected files/docs:**
- `/studio/`
- `/studio/catalogue/`
- `/studio/library/`
- `/studio/analytics/`
- `/studio/search/`
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)

**Notes:**
Studio docs also gained a local `Rebuild docs` control alongside the shared docs viewer search field.

## [2026-04-18] Added the Studio moment import flow

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added the dedicated moment import workflow at `/studio/catalogue-moment-import/`.

**Reason:**
Moments needed a scoped import path that could preview and apply source-file changes without running a broader catalogue maintenance flow.

**Effect:**
The moment import UI now supports explicit source-file preview/apply, targeted moment rebuilds, catalogue-search rebuild, and first-pass activity/build reporting without folder scanning or srcset generation.

**Affected files/docs:**
- `/studio/catalogue-moment-import/`
- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)

**Notes:**
This was Phase 2 of the Studio implementation sequence.

## [2026-04-18] Added work-file and work-link editing to the Studio catalogue

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Extended the catalogue editor flow with work-file and work-link editing surfaces.

**Reason:**
Work files and work links needed the same source-backed local editing model as works and details.

**Effect:**
`/studio/catalogue-work/` now links into focused create/edit surfaces for work files and work links, canonical `work_files.json` and `work_links.json` now have local write endpoints, and the derived catalogue lookup layer can open those editors without loading the full source set.

**Affected files/docs:**
- `/studio/catalogue-work/`
- `work_files.json`
- `work_links.json`
- [Work Files](/docs/?scope=studio&doc=catalogue-work-files)
- [Work Links](/docs/?scope=studio&doc=catalogue-work-links)

**Notes:**
The surrounding Studio runtime/docs routing and local save-flow docs were updated to match these new surfaces.

## [2026-04-18] Added workbook-backed bulk work import for new works and details

**Status:** implemented

**Area:** Studio import workflow

**Summary:**
Added the bulk work import flow at `/studio/bulk-add-work/`.

**Reason:**
Even in the JSON-led catalogue workflow, a bounded import path is still useful for bringing in batches of new works and work details from workbook data.

**Effect:**
The bulk import UI now supports one-way preview/apply import from the configured workbook source into canonical JSON for new works and new work details.

**Affected files/docs:**
- `/studio/bulk-add-work/`
- `_data/pipeline.json`
- [Bulk Add Work](/docs/?scope=studio&doc=bulk-add-work)

**Notes:**
Later follow-up work moved the workbook path to `data/works_bulk_import.xlsx`.

## [2026-04-18] Completed Studio catalogue UI consistency and operational reporting refinements

**Status:** implemented

**Area:** Studio catalogue UI

**Summary:**
Refined the catalogue admin UI with more consistent navigation, layout, and reporting surfaces.

**Reason:**
As more Studio routes were added, the catalogue domain needed a clearer internal navigation model and better operational visibility.

**Effect:**
The Catalogue dashboard now uses grouped directional links, catalogue-domain pages share a cross-linked page nav, metadata editors use the left-label single-column layout, Catalogue Status sorts by header, work-file and work-link editors can be opened from dashboard search, `Catalogue Activity` remains source-side, `Build Activity` now records rebuild outcomes, and both pages use sortable operational lists with explicit scope/result columns and links back into the relevant workflow routes.

**Affected files/docs:**
- `/studio/catalogue/`
- `/studio/catalogue-status/`
- `/studio/catalogue-activity/`
- `/studio/build-activity/`
- [Catalogue Status](/docs/?scope=studio&doc=catalogue-status)
- [Catalogue Activity](/docs/?scope=studio&doc=catalogue-activity)
- [Build Activity](/docs/?scope=studio&doc=build-activity)

**Notes:**
This covers the Phase 3 and Phase 4 UI/reporting refinements in the Studio plan.

## [2026-04-18] Completed source-readiness, preview-media, and local-media generation refinements

**Status:** implemented

**Area:** Studio media workflow

**Summary:**
Extended Studio to report source readiness, show focused preview media, and surface local derivative generation state.

**Reason:**
Editing metadata alone was not enough once Studio started coordinating source prose, source media, generated previews, and local derivative generation.

**Effect:**
Work, series, and detail editors now surface source readiness in the summary rail, work and series offer narrow `Import prose + rebuild` actions, detail preview resolves its own source media path, work and detail editors show compact current-record previews, work-detail rows on the work editor use thumbnail-led navigation, scoped rebuilds run a bounded local thumbnail-generation step for works, work details, and moments, and Build Activity records generated local media alongside rebuild outcomes.

**Affected files/docs:**
- `/studio/catalogue-work/`
- `/studio/catalogue-work-detail/`
- `/studio/catalogue-series/`
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)
- [Build Activity](/docs/?scope=studio&doc=build-activity)

**Notes:**
This entry covers the later media/readiness refinements that followed the first editor surfaces.

## [2026-04-18] Completed internal generator refactor for live JSON rebuilds

**Status:** implemented

**Area:** catalogue generator

**Summary:**
Refactored the internal generator so live JSON rebuilds no longer materialize `works.xlsx`.

**Reason:**
The live rebuild path needed to align with canonical JSON source records instead of continuing to depend on an intermediate workbook materialization step.

**Effect:**
`generate_work_pages.py` now rebuilds from canonical source records with an explicit in-memory compatibility projection, and JSON-source write runs now persist mutable source updates back into canonical catalogue JSON rather than round-tripping through a workbook file.

**Affected files/docs:**
- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)

**Notes:**
`AGENTS.md` was updated to reflect the live JSON-led workflow and retire the older workbook-led entrypoint assumptions.

## [2026-04-17] Added derived catalogue lookup payloads for lightweight Studio editors

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added the derived lookup payload layer used by the Studio editors.

**Reason:**
Loading the full catalogue source set in the browser was too heavy for focused editor routes that only need lightweight search data plus a current record.

**Effect:**
Studio editors now use lightweight search indexes plus focused per-record lookup JSON rather than loading the full source browser payload.

**Affected files/docs:**
- derived catalogue lookup JSON under `assets/studio/data/`
- [Catalogue Search](/docs/?scope=studio&doc=search)
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)

**Notes:**
Later editor surfaces built on this lookup layer rather than on full-source browser loads.

## [2026-04-17] Added the Studio series editor and series-scoped rebuild flow

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added the first series editor route for the JSON-led catalogue workflow.

**Reason:**
Series-level metadata and membership needed the same local editing and scoped rebuild model as individual works.

**Effect:**
`/studio/catalogue-series/` now supports canonical `series.json` save flow, atomic membership writes into `works.json`, and series-scoped rebuilds for the current series, affected works, aggregate indexes, and catalogue search.

**Affected files/docs:**
- `/studio/catalogue-series/`
- `series.json`
- `works.json`
- [Catalogue Series](/docs/?scope=studio&doc=catalogue-series)

**Notes:**
This was the first series-specific editing surface in Studio.

## [2026-04-17] Added the work detail editor and grouped work-detail navigation

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added the work detail editor and integrated grouped detail navigation into the work editor.

**Reason:**
Work details needed their own source-backed edit surface while still being easy to reach from the parent work context.

**Effect:**
`/studio/catalogue-work-detail/` now supports canonical `work_details.json` save flow and parent-work scoped rebuilds, while `/studio/catalogue-work/` shows grouped work-detail navigation capped at ten visible rows per section with per-work detail search by id.

**Affected files/docs:**
- `/studio/catalogue-work-detail/`
- `/studio/catalogue-work/`
- `work_details.json`
- [Catalogue Work Detail](/docs/?scope=studio&doc=catalogue-work-detail)

**Notes:**
This built on the earlier single-work editor and scoped JSON rebuild path.

## [2026-04-17] Added the first canonical work editor and scoped JSON rebuild path

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added the first canonical single-work editor together with the scoped JSON-source rebuild flow.

**Reason:**
Studio needed a practical proof that individual work metadata could be edited safely against canonical JSON without relying on workbook editing.

**Effect:**
`/studio/catalogue-work/` became the first canonical work metadata editor, local preview/apply plus `Save + Rebuild` were added for work edits, Studio transport/config wiring gained separate catalogue local-service health probing, and the catalogue write server response now returns the normalized saved record plus saved timestamp for editor baseline refresh.

**Affected files/docs:**
- `/studio/catalogue-work/`
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Work](/docs/?scope=studio&doc=catalogue-work)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

**Notes:**
This was the first end-to-end canonical JSON editor in the Studio catalogue workflow.

## [2026-04-17] Added catalogue status and activity Studio pages

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added early Studio surfaces for JSON-led catalogue maintenance: Catalogue Status and Catalogue Activity.

**Reason:**
The new catalogue source workflow needs useful visibility before full editing UI exists. Non-published records should be discoverable without opening Excel, and local JSON-source saves or validation failures should be visible without reading raw server logs.

**Effect:**
`/studio/catalogue-status/` reads canonical catalogue source JSON and lists records where `status` is not `published`. `/studio/catalogue-activity/` reads `assets/studio/data/catalogue_activity.json`, a small feed updated by the Catalogue Write Server for source-save and validation-failure events. Studio config now exposes the source and activity data paths used by those pages.

**Affected files/docs:**
- `studio/catalogue-status/index.md`
- `studio/catalogue-activity/index.md`
- `assets/studio/js/catalogue-status.js`
- `assets/studio/js/catalogue-activity.js`
- `assets/studio/data/catalogue_activity.json`
- `scripts/catalogue_activity.py`
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Status](/docs/?scope=studio&doc=catalogue-status)
- [Catalogue Activity](/docs/?scope=studio&doc=catalogue-activity)

**Notes:**
The UI intentionally follows established Studio list and activity patterns. Refinement can happen after the first implementation is in use.

## [2026-04-17] Added the local catalogue source write service

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added a localhost-only Catalogue Write Server for the JSON-led catalogue pipeline.

**Reason:**
Studio catalogue editors need a narrow local write boundary before the UI can replace workbook editing. The first service increment proves that canonical source JSON can be updated safely without writing media, prose, generated public JSON, or search artifacts.

**Effect:**
`scripts/studio/catalogue_write_server.py` exposes `GET /health` and `POST /catalogue/work/save`. The save endpoint updates existing work records in `assets/studio/data/catalogue/works.json`, validates the full catalogue source set before writing, supports optional stale-record hash checks, creates timestamped backup bundles, and writes minimal local event logs. `bin/dev-studio` now starts this service alongside Jekyll and the Tag Write Server.

**Affected files/docs:**
- `scripts/studio/catalogue_write_server.py`
- `bin/dev-studio`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**
This service is intentionally narrow. Work detail, series, create, delete, bulk edit, import, and build endpoints remain later pipeline phases.

## [2026-04-01] Migrated moments from workbook rows to source-file front matter

**Status:** implemented

**Area:** moments pipeline

**Summary:**  
Moments are now sourced from `moments/*.md` front matter instead of the `Moments` worksheet in `works.xlsx`.

**Reason:**  
The old model duplicated moment metadata between source prose files and the workbook even though moments only need a small metadata surface and already have a canonical source file. Moving that metadata into front matter makes each moment self-contained, removes unnecessary workbook maintenance, and aligns the pipeline with how moment prose is actually authored.

**Effect:**  
`build_catalogue.py`, `copy_draft_media_files.py`, `generate_work_pages.py`, and the shared preflight now scan moment source files directly. Canonical moment metadata now lives in front matter as `title`, `status`, `published_date`, `date`, optional `date_display`, and optional `image_file`, with `moment_id` fixed by the filename stem. Moment publish writes now update source front matter while preserving the first `published_date`, missing source images are treated as optional, and the standalone `delete_moment.py` script now handles repo-side moment cleanup without requiring workbook rows.

**Affected files/docs:**  
- `scripts/moment_sources.py`
- `scripts/build_catalogue.py`
- `scripts/copy_draft_media_files.py`
- `scripts/generate_work_pages.py`
- `scripts/catalogue_preflight.py`
- `scripts/jekyll_markdown_renderer.rb`
- `scripts/delete_moment.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Copy Draft Media Files](/docs/?scope=studio&doc=scripts-copy-draft-media)
- [Delete Moment](/docs/?scope=studio&doc=scripts-delete-moment)

**Notes:**  
This change retires the `Moments` worksheet as a pipeline source. During the migration, older workbook-backed fallbacks were briefly retained and then removed once moment front matter had been completed across the source tree.

## [2026-04-01] Added a public recently added page and publication ledger

**Status:** implemented

**Area:** catalogue

**Summary:**  
Added a public `/recent/` page plus a generated `assets/data/recent_index.json` ledger for recent first-time series and work publications.

**Reason:**  
The public catalogue needed a lightweight way to surface newly published work without treating later title edits, series edits, or work moves as fresh additions. That requires a small persistent event ledger rather than a page derived only from current catalogue state.

**Effect:**  
`generate_work_pages.py` now records first-time `draft -> published` transitions into a capped recent-publications index, prunes entries whose target series or work has been deleted, and groups multiple newly published works in the same existing series into one entry anchored to the first work from that run. The public `/recent/` page renders that ledger, `/series/` now links to it with a `recently added` control, and series/work pages now show `← recently added` when opened from that route.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- `scripts/backfill_recent_index_from_git_history.py`
- `recent/index.md`
- `series/index.md`
- `_layouts/series.html`
- `_layouts/work.html`
- `assets/css/main.css`
- `assets/data/recent_index.json`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)

**Notes:**  
The initial `/recent/` ledger can be seeded from workbook git history with `scripts/backfill_recent_index_from_git_history.py`. That one-off backfill only records provable `draft -> published` transitions and drops any historic series entry that cannot be mapped confidently onto a current live series ID.

## [2026-04-01] Preserved tag assignments across series-id renames

**Status:** implemented

**Area:** build pipeline

**Summary:**  
`build_catalogue.py` now migrates matching `assets/studio/data/tag_assignments.json` series rows when series IDs are renamed.

**Reason:**  
During the numeric series-id migration, the planner correctly treated old slug-style series IDs as removed and new numeric series IDs as added, but the previous cleanup path deleted the old tag-assignment rows and the later generator pass recreated empty rows for the new IDs. That dropped curator tags and per-work tag overrides.

**Effect:**  
Before generation and stale cleanup, the wrapper now compares the existing `assets/data/series_index.json` to the current workbook and infers series-ID renames by matching title, `primary_work_id`, and member works. Matching tag-assignment rows are migrated to the new IDs instead of being deleted. True removals still prune tag-assignment rows as before.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- `assets/studio/data/tag_assignments.json`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)

**Notes:**  
This protects future series-ID renames. Existing lost tags had to be restored once from the previous commit's tag-assignment data.

## [2026-04-01] Scoped wrapper generation artifacts to the planned flow

**Status:** implemented

**Area:** build pipeline

**Summary:**  
`build_catalogue.py` now passes a narrower `--only` artifact list into `generate_work_pages.py` based on the planned scope instead of always letting the generator run every work-side artifact type.

**Reason:**  
The planner could correctly report no `WorkDetails` row changes while the later generator phase still dry-ran or rewrote all `_work_details/*.md` pages for selected works. That made the plan harder to trust and caused unnecessary noise during work-only migrations such as the numeric series-id transition.

**Effect:**  
Work-only runs now skip `work-details-pages` unless the work-details flow actually needs them. Aggregate indexes still rebuild as before, and work JSON can still include detail metadata without regenerating `_work_details` route stubs.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)

**Notes:**  
This only changes which artifact groups are requested from `generate_work_pages.py`. It does not change planner diff detection or the underlying detail JSON model.

## [2026-04-01] Added numeric series-id support to the catalogue pipeline

**Status:** implemented

**Area:** series model migration

**Summary:**  
The catalogue planner, workbook preflight, generator, and audit tooling no longer require `series_id` to be slug-safe.

**Reason:**  
`series_id` is being migrated toward a numeric catalogue-style identifier instead of a user-authored slug. The pipeline needed to stop treating series IDs as route slugs before the workbook can be bulk-migrated safely.

**Effect:**  
`build_catalogue.py`, `generate_work_pages.py`, and the shared workbook preflight now normalize numeric series IDs such as `1` to `001`, accept those values in `Works.series_ids`, `Series.series_id`, `SeriesSort.series_id`, and `--series-ids*` CLI filters, and still tolerate the current legacy slug-style series IDs during transition. Generated artifact naming continues to follow whatever normalized series IDs are present in the workbook.

**Affected files/docs:**  
- `scripts/series_ids.py`
- `scripts/catalogue_preflight.py`
- `scripts/build_catalogue.py`
- `scripts/generate_work_pages.py`
- `scripts/audit_site_consistency.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)

**Notes:**  
This is a transition step, not the workbook migration itself. The canonical workbook still needs to be bulk-edited from legacy slug-style series IDs to numeric series IDs before the site fully switches over.

## [2026-04-01] Preserved workbook formulas during generator writes

**Status:** implemented

**Area:** workbook writes

**Summary:**  
`generate_work_pages.py` now reads workbook values from a `data_only=True` workbook while saving updates through a separate non-`data_only` workbook.

**Reason:**  
The previous write path saved the same `data_only=True` workbook instance that was used for reading. That risks stripping formulas from the workbook when the generator updates status, `published_date`, or image dimensions.

**Effect:**  
Write runs now preserve existing workbook formulas while keeping the current generated-file and workbook-update behavior. This clears the way for supported formula-driven helper columns in `Works`, such as series-title lookup aids, without the generator destroying those formulas on save.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)

**Notes:**  
The generator still relies on Excel's cached formula values when reading with `data_only=True`. If a formula result has not been calculated and saved by Excel yet, the read value may still be empty or stale.

## [2026-04-01] Added a default post-plan confirmation prompt to build_catalogue

**Status:** implemented

**Area:** build pipeline

**Summary:**  
`build_catalogue.py` now pauses after printing `==> Build Plan` and asks `Continue? [Y|N]` unless `--no-confirm` is passed.

**Reason:**  
The build plan is now detailed enough to act as a real operator checkpoint. Adding an explicit confirmation step makes it easier to catch scope mistakes before copy, srcset, workbook, or generated-file work begins.

**Effect:**  
Interactive runs now require a simple confirmation after the plan. `--no-confirm` skips that prompt and continues immediately, which is the intended path for unattended invocations. `--plan` still exits after printing the plan without prompting.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)

**Notes:**  
This change affects orchestration behavior only. Generation logic and output contracts are unchanged.

## [2026-04-01] Shortened local path output in catalogue pipeline logs

**Status:** implemented

**Area:** build pipeline

**Summary:**  
Catalogue pipeline command echoes and step logs now avoid printing machine-specific absolute filesystem roots during normal runs.

**Reason:**  
The previous output was noisy and leaked long local absolute paths for interpreters, repo files, canonical source media, staged media, and temporary manifest files. That made routine logs harder to scan and less portable.

**Effect:**  
`build_catalogue.py`, `copy_draft_media_files.py`, `make_srcset_images.py`, and `generate_work_pages.py` now render repo-owned paths as repo-relative, canonical source paths as `[projects]/...`, staged and derivative media paths as `[media]/...`, and temporary paths as `[tmp]/...`. Runtime behavior is unchanged; this is a display-only logging cleanup.

**Affected files/docs:**  
- `scripts/display_paths.py`
- `scripts/build_catalogue.py`
- `scripts/copy_draft_media_files.py`
- `scripts/make_srcset_images.py`
- `scripts/generate_work_pages.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)

**Notes:**  
This change only affects human-readable output. The underlying commands and file writes still use the full resolved paths internally.

## [2026-04-01] Added fail-fast catalogue workbook preflight

**Status:** implemented

**Area:** validation

**Summary:**  
`build_catalogue.py` and `generate_work_pages.py` now run a shared workbook preflight before copy, generation, or workbook-write steps begin.

**Reason:**  
The catalogue pipeline could previously write work pages, stage media, or persist workbook status changes before a later workbook integrity error such as a missing `Series.primary_work_id` aborted the run. That made failures harder to recover from and left partial publish state behind.

**Effect:**  
Blocking workbook issues for actionable catalogue rows are now aggregated and reported before the run starts mutating outputs. The current preflight covers malformed IDs, unknown `Works.series_ids` references, missing or invalid `Series.primary_work_id` values, series primary works that are not members of the series, orphaned `WorkDetails.work_id` values, and invalid moment source filenames or front matter.

**Affected files/docs:**  
- `scripts/catalogue_preflight.py`
- `scripts/build_catalogue.py`
- `scripts/generate_work_pages.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**  
This change adds an earlier validation gate but does not relax the underlying generator requirements. It moves the failure point earlier and makes the errors easier to fix in one pass.

## [2026-04-01] Added a Studio-only work storage index

**Status:** implemented

**Area:** studio

**Summary:**  
Added `assets/studio/data/work_storage_index.json` so `/studio/studio-works/` can continue surfacing storage without putting curator-only storage data back into the public `works_index.json`.

**Reason:**  
The public works index was intentionally slimmed for runtime use, but the Studio works page still needs a fast bulk answer to “where is a work stored?”. A separate Studio-only lookup keeps that curator use case intact without re-expanding the public artifact.

**Effect:**  
`generate_work_pages.py` now writes a Studio-only storage map keyed by `work_id`, `studio-works.js` merges it into the existing row rendering and storage sort behavior, and `delete_work.py` removes stale entries from that Studio index during one-off deletions.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- `scripts/delete_work.py`
- `studio/studio-works/index.md`
- `assets/studio/js/studio-works.js`
- [Studio Works](/docs/?scope=studio&doc=studio-works)
- [Studio Scope](/docs/?scope=studio&doc=data-models-studio)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)

## [2026-04-01] Added `medium_caption` to derived catalogue search terms

**Status:** implemented

**Area:** search

**Summary:**  
Catalogue search now enriches work entries with `medium_caption` from per-work JSON, but keeps that value in derived search fields rather than exposing a new displayed result field.

**Reason:**  
The search builder already reads per-work JSON for work-only enrichment. Adding `medium_caption` improves public recall for material descriptions without re-bloating `works_index.json` or the visible result-row contract.

**Effect:**  
`build_search.rb` now reads `medium_caption` from `assets/works/index/<work_id>.json` and folds it into `search_terms` and `search_text` for work entries. Result rows still display `medium_type`, not `medium_caption`, and the serialized field inventory for catalogue search remains unchanged.

**Affected files/docs:**  
- `scripts/build_search.rb`
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules)
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist)

## [2026-04-01] Slimmed `works_index` and removed storage from public search

**Status:** implemented

**Area:** search

**Summary:**  
`works_index.json` no longer carries `storage` or `medium_type`, and public catalogue search no longer indexes or ranks on `storage`.

**Reason:**  
`works_index.json` is a shared runtime summary artifact and should stay as lean as possible. `storage` is no longer intended to be publicly searchable, and `medium_type` can be sourced directly from per-work JSON during the offline search build instead of being duplicated into the lightweight works index.

**Effect:**  
The lightweight works index now carries identity, title/year display, and series membership only. Catalogue search still exposes `medium_type`, but now resolves it from `assets/works/index/<work_id>.json`. `storage` has been removed from the public search artifact and from the current search ranking model.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- `scripts/build_search.rb`
- `assets/js/search/search-page.js`
- `scripts/delete_work.py`
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)

## [2026-04-01] Added work and series prose tracking to build_catalogue planning

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now fingerprints work, series, and moment prose source files as part of planner state, so prose-only edits can be picked up by the default planner path.

**Reason:**  
After workbook rows, source images, and removed-row cleanup were covered, prose files were the remaining practical catalogue inputs still outside the planner. Bringing them into scope makes the default build path more complete without widening cleanup scope to canonical source trees.

**Effect:**  
Planner state now tracks work prose resolved from `Works.project_folder` plus `Works.work_prose_file`, series prose resolved from `Series.primary_work_id` plus `Series.series_prose_file`, and moment prose resolved from `moments/<moment_id>.md`. Work, series, and moment prose changes now trigger generation targeting only. They do not trigger copy/srcset and do not force a catalogue search rebuild on their own.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)

**Notes:**  
Planner state migration now rewrites earlier prose-tracking baselines to include moment prose.

## [2026-04-01] Extended removed-row cleanup to local staged and derivative media

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now removes stale local media outputs under `DOTLINEFORM_MEDIA_BASE_DIR` when workbook rows are removed.

**Reason:**  
Cleaning only repo-owned route stubs and JSON still left stale staged inputs, srcset outputs, and staged downloads on the local media side. Those files are owned by the same catalogue pipeline and should be cleaned by the same removed-row pass.

**Effect:**  
Removed work, work-detail, and moment rows now also delete matching files from the local `make_srcset_images` input folders, the generated `primary/` and `thumb/` srcset folders, and staged work downloads under `works/files/`. Aggregate catalogue JSON and search rebuilds still run afterward from the current workbook state.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**  
This still does not touch canonical source media under `DOTLINEFORM_PROJECTS_BASE_DIR` or remote media such as R2.

## [2026-04-01] Added removed-row stale-artifact cleanup to build_catalogue

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now cleans up repo-owned generated artifacts when workbook rows are removed, instead of only warning that stale files may remain.

**Reason:**  
The planner already knew which workbook rows had disappeared. Turning that into concrete cleanup reduces drift in route stubs, per-record JSON, and Studio assignment data without requiring a separate manual delete pass for the common cases.

**Effect:**  
Removed work, work-detail, series, and moment rows now trigger deletion of the matching generated route stubs and per-record JSON files in the repo. The same pass also prunes removed series rows and removed per-work overrides from `assets/studio/data/tag_assignments.json`, then rebuilds aggregate indexes and catalogue search from the current workbook state.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Studio Scope](/docs/?scope=studio&doc=data-models-studio)

**Notes:**  
This first slice only cleans repo-owned generated artifacts and Studio assignment rows. External source media and derivative media cleanup still remain separate.

## [2026-04-01] Added explicit planner version metadata to build_catalogue state

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now writes `var/build_catalogue_state.json` with explicit top-level planner metadata so planner-state evolution is easier to reason about.

**Reason:**  
The planner state had already become important enough to deserve a clearer contract. Explicit versioning and a migration note make future planner changes easier to document and safer to evolve without turning state resets into the default workflow.

**Effect:**  
Planner state now includes `schema`, `planner_version`, and `migration_note`. Older compatible state files are still accepted, normalized in memory, and rewritten on the next successful write run.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)

**Notes:**  
This does not change canonical site data. It only makes the local planner-state contract more explicit.

## [2026-04-01] Added a curator-facing Studio build activity feed

**Status:** implemented

**Area:** studio

**Summary:**  
Added a curated build-activity journal and a Studio page at `/studio/build-activity/` so recent catalogue build runs can be reviewed without reading raw script logs.

**Reason:**  
The catalogue planner now has enough context to explain what changed and what it rebuilt. A lightweight recent-activity surface makes that information useful to the curator and creates a cleaner base for any later public “recent updates” work.

**Effect:**  
Successful non-dry-run `build_catalogue.py` runs now append a local journal under `var/build_activity/`, regenerate `assets/studio/data/build_activity.json`, and the new Studio page renders the latest entries with changed workbook/media groups plus action summaries.

**Affected files/docs:**  
- `scripts/build_activity.py`
- `scripts/build_catalogue.py`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `assets/studio/js/build-activity.js`
- `studio/build-activity/index.md`
- [Build Activity](/docs/?scope=studio&doc=build-activity)
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)

**Notes:**  
This feed is a local Studio summary surface, not the canonical low-level script log and not yet a public site history feed.

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

## [2026-04-01] Fixed moments index rebuild on scoped non-moment runs

**Status:** implemented

**Area:** scripts

**Summary:**  
Fixed a local-variable scoping bug in `generate_work_pages.py` that could crash scoped runs such as `--work-ids ...` when the script still rebuilt the global moments index JSON afterward.

**Reason:**  
The moments index rebuild path is meant to remain available even when moment page generation is not selected, but it was reusing column helper variables that were only initialized inside the moment-page branch.

**Effect:**  
Scoped work-only runs now complete normally while still allowing the global moments index pass to evaluate its inputs and write-skip correctly.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)

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
This was the first planner slice. Removed-row stale-artifact cleanup was added in a later follow-up on the same day.

## [2026-04-01] Extended catalogue planning to track canonical source media

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now fingerprints canonical source images for works, work details, and moments in addition to workbook-backed rows, so published media replacements can be picked up without manual ID scoping.

**Reason:**  
Workbook-only planning was enough for metadata changes, but it still left source-image edits outside the default build path. That kept routine image replacement work dependent on user-supplied flags and IDs.

**Effect:**  
The planner state now includes source-media fingerprints and can infer copy/srcset plus downstream generation scope from file changes. Existing planner state files that predate media tracking are treated as a baseline until the next write run updates them.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
- [Scripts](/docs/?scope=studio&doc=scripts)

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

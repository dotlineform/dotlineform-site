---
doc_id: site-change-log
title: Site Change Log
added_date: 2026-04-24
last_updated: "2026-05-08"
parent_id: ""
sort_order: 270
---
# Site Change Log

This page keeps the current site and non-search Studio change history compact enough to edit and review directly.
Older entries are kept in dated archive child docs so existing links to this document remain stable.

Archives:

- [Site Change Log Archive: May 2026](/docs/?scope=studio&doc=site-change-log-2026-05)
- [Site Change Log Archive: April 2026](/docs/?scope=studio&doc=site-change-log-2026-04)
- [Site Change Log Archive: March 2026 And Earlier](/docs/?scope=studio&doc=site-change-log-2026-03-and-earlier)

## [2026-05-08] Implemented R2 media upload automation

**Status:** implemented

**Area:** Catalogue / media publishing

**Summary:**
Added `./scripts/publish_media_to_r2.py`, a dry-run-first Cloudflare R2 publisher for catalogue primary-image derivatives.

**Files changed:**

- `scripts/publish_media_to_r2.py`
- `tests/python/test_publish_media_to_r2.py`
- `.gitignore`
- [Publish Media To R2](/docs/?scope=studio&doc=scripts-publish-media-to-r2)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [R2 Media Upload Automation Request](/docs/?scope=studio&doc=site-request-r2-media-upload-automation)
- [Change Requests](/docs/?scope=studio&doc=change-requests)

**Impact:**
Catalogue work, work-detail, and moment primary variants can now be previewed or uploaded to R2 from the CLI.
The publisher loads credentials from environment variables or gitignored local env files, skips unchanged objects, blocks changed remote objects unless `--force` is explicit, supports exact-id remote primary deletion with `--delete --write`, and keeps docs media publishing out of scope for this milestone.

## [2026-05-07] Clarified Docs Viewer draft visibility

**Status:** implemented

**Area:** Docs Viewer / Management

**Summary:**
Changed manage-mode draft visibility from a hidden `drafts` toggle and bold index styling to always-visible non-viewable docs with a `✏️` prefix, plus a checked-by-default `show viewable` toggle.

**Impact:**
The Edit modal status dropdown now includes `draft` across all scopes. Saving `draft` writes `viewable: false`; saving any non-draft status writes `viewable: true`.

## [2026-05-07] Fixed Studio mobile nav overflow

**Status:** implemented

**Area:** Studio / Navigation

**Summary:**
Moved secondary Studio header links behind the existing shared mobile `nav-more` menu and removed source-format suffixes from the Docs Import staged-file dropdown.

**Impact:**
Studio pages no longer force horizontal page overflow on mobile due to the full inline nav, while desktop keeps the full header link row.

## [2026-05-07] Refined Docs Import result panel layout

**Status:** implemented

**Area:** Studio / Docs Import

**Summary:**
Stacked Docs Import result fields vertically and reduced result message text to the small text token.

**Impact:**
Long staged media paths, R2 keys, and media tokens now use the full result-panel width and wrap more predictably on desktop and mobile.

## [2026-05-07] Refined Docs Import filename conflict UI

**Status:** implemented

**Area:** Studio / Docs Import

**Summary:**
Changed Docs Import collision recovery from an inline title prompt to a shared Studio modal for editing the replacement `doc_id`.

**Reason:**
The conflict is caused by an existing Markdown filename/doc_id, not by the imported document title. The UI should ask for the exact filename stem that will change.

**Files changed:**

- `scripts/docs/docs_management_server.py`
- `studio/docs-import/index.md`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `tests/python/test_docs_import_service.py`
- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
When a staged source would write a filename that already exists, `/studio/docs-import/` now opens a `File already exists` modal seeded with the colliding `doc_id`.
OK resubmits with `replacement_doc_id`, Replace explicitly overwrites the existing source file, Cancel leaves the import unwritten, and the imported document title is preserved.
The staged-file control is also constrained to half the content width on desktop so `publish into` sits beside it.

## [2026-05-07] Implemented Docs Import inline raster extraction

**Status:** implemented

**Area:** Studio / Docs Import

**Summary:**
Implemented extraction of inline raster data URLs from Docs Import sources into generated staged media files.

**Reason:**
Imported docs can contain very long `data:image/...;base64,...` Markdown image targets. Those should become normal docs media tokens with explicit staged files and manual R2 copy instructions.

**Files changed:**

- `scripts/docs/docs_html_import.py`
- `scripts/docs/docs_management_server.py`
- `studio/docs-import/index.md`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/data/studio_config.json`
- `tests/python/test_docs_import_service.py`
- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Docs HTML Inline Raster Media Request](/docs/?scope=studio&doc=site-request-docs-html-inline-raster-media)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
HTML and Markdown imports now rewrite Markdown-image-form inline PNG, JPEG, WebP, and GIF data URLs to <code>&#91;&#91;media:docs/&lt;scope&gt;/img/&lt;filename&gt;&#93;&#93;</code> tokens during preview.
On create or overwrite, the docs service decodes the planned images into `var/docs/import-staging/` with incrementing filenames such as `example-doc-image-01.png`, returns `inline_media_written`, and the Studio result panel lists staged paths, R2 keys, and media tokens for copying to R2.

## [2026-05-07] Implemented Docs Import source registry and media support

**Status:** implemented

**Area:** Studio / Docs Import

**Summary:**
Implemented the Docs Import source registry and expanded staged imports beyond HTML and Markdown.

**Reason:**
Docs Import needed a structured importer boundary before adding text, standalone SVG, R2-backed image wrappers, and downloadable file wrappers.

**Files changed:**

- `scripts/docs/docs_html_import.py`
- `scripts/docs/docs_management_server.py`
- `studio/docs-import/index.md`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/data/studio_config.json`
- `tests/python/test_docs_import_service.py`
- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Docs Import Source Registry And Media Support Request](/docs/?scope=studio&doc=site-request-docs-import-source-registry-media)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The route now lists HTML, Markdown, text, SVG, raster image, and file-media staged files.
Text imports autolink plain URLs, HTML and standalone SVG share SVG safety behavior, image and file imports generate <code>&#91;&#91;media:docs/&lt;scope&gt;/...&#93;&#93;</code> wrappers with manual R2 copy warnings, and source-stem collisions prompt for a replacement title instead of silently suffixing.

## [2026-05-07] Added duplicate stem handling to Docs Import media request

**Status:** proposed

**Area:** Studio / Docs Import

**Summary:**
Updated the Docs Import media request so proposed `doc_id` collisions prompt for a replacement title instead of auto-appending a suffix.

**Reason:**
When a staged file stem already matches an existing Markdown source file, the user should control the new title and resulting `doc_id` while still getting the current name as an easy starting point.

**Files changed:**

- [Docs Import Source Registry And Media Support Request](/docs/?scope=studio&doc=site-request-docs-import-source-registry-media)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The request now requires collision detection during preview, a replacement-title prompt seeded with the current name, server-side `doc_id` regeneration, and a second collision check before apply.

## [2026-05-07] Refined Docs Import media request around shared SVG and R2 links

**Status:** proposed

**Area:** Studio / Docs Import

**Summary:**
Updated the Docs Import media request so raw SVG files and SVG embedded in HTML share one sanitizer policy, plain text URLs become autolinks, and imported media wrappers point at expected R2 docs media keys.

**Reason:**
The import model should keep SVG behavior consistent across source formats and should match the current manual R2 media workflow instead of introducing a separate repo-local image copy path.

**Files changed:**

- [Docs Import Source Registry And Media Support Request](/docs/?scope=studio&doc=site-request-docs-import-source-registry-media)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The request now treats images and downloadable files as separate docs media classes, with image links under `docs/<scope>/img/` and file links under `docs/<scope>/files/`.
The generated Markdown points at <code>&#91;&#91;media:...&#93;&#93;</code> tokens while the actual R2 copy remains manual.

## [2026-05-07] Added R2 media upload automation request

**Status:** proposed

**Area:** Catalogue / media publishing

**Summary:**
Added a change request for replacing manual R2 media uploads with a script-managed publishing workflow.

**Reason:**
Catalogue primary derivatives are generated locally but still require a manual R2 handoff.
That is easy to miss today and would become harder to manage once docs imports can create media assets too.

**Files changed:**

- [R2 Media Upload Automation Request](/docs/?scope=studio&doc=site-request-r2-media-upload-automation)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The request proposes a dry-run-first R2 publisher, secure credential loading through local environment variables or gitignored secret files, catalogue primary-image support first, and a registry-style adapter path for future docs media.

## [2026-05-07] Added Docs Import registry and media support request

**Status:** proposed

**Area:** Studio / Docs Import

**Summary:**
Added a change request for making Docs Import format-extensible and supporting standalone text, SVG, and raster image files.

**Reason:**
The current source import flow now handles HTML and body-only Markdown, but future standalone media imports need a clearer registry boundary, asset-copy plan, and SVG safety policy before implementation.

**Files changed:**

- [Docs Import Source Registry And Media Support Request](/docs/?scope=studio&doc=site-request-docs-import-source-registry-media)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The request proposes a source importer registry, `.txt` import, standalone SVG wrapper-doc import, and raster image import that copies assets under `assets/docs/imports/<scope>/<doc_id>/` before generating wrapper Markdown.

## [2026-05-07] Enabled Markdown files in Docs Import

**Status:** implemented

**Area:** Studio / Docs Import

**Summary:**
Extended `/studio/docs-import/` so staged body-only Markdown files can be imported alongside staged HTML files.

**Reason:**
Some source material is already authored as Markdown and should not be forced through the HTML conversion path.

**Files changed:**

- `studio/docs-import/index.md`
- `studio/library/index.md`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/data/studio_config.json`
- `scripts/docs/docs_html_import.py`
- `scripts/docs/docs_management_server.py`
- `tests/python/test_docs_import_service.py`
- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
The import page now lists `.html`, `.htm`, `.md`, and `.markdown` files from `var/docs/import-staging/`.
Markdown imports are treated as body-only source, derive `doc_id` from the staged filename, derive title from the first `# H1` when present, and get normal Docs Viewer front matter during create or overwrite.

## [2026-05-07] Added a dense Studio list primitive variant

**Status:** implemented

**Area:** Studio UI / List Primitive

**Summary:**
Added `tagStudioList--dense` as a shared list primitive variant based on the `/studio/studio-works/` scan-table design.

**Reason:**
The works list density is useful beyond the works route, but copying `worksList__*` classes would mix page-specific semantics into unrelated Studio pages.

**Files changed:**

- `assets/studio/css/studio.css`
- `studio/ui-catalogue/list/index.md`
- `_includes/studio_ui_catalogue_list_demo.html`
- `_includes/ui_catalogue_notes/list.md`
- [List Primitive](/docs/?scope=studio&doc=ui-primitive-list)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
Studio pages can now opt into a dense sortable list with `--text-xs` type, no row dividers, and a bold title column while keeping their own column templates and row semantics.

## [2026-05-07] Aligned Studio Works with the dense list primitive

**Status:** implemented

**Area:** Studio UI / Catalogue Works

**Summary:**
Moved `/studio/studio-works/` onto `tagStudioList--dense` for its header, sortable buttons, rows, sort indicator, cell links, metadata cells, and bold title cell.

**Reason:**
Once the dense list became a shared primitive, the Studio works page no longer needed to own the same presentation through route-local `worksList__*` styling.

**Files changed:**

- `studio/studio-works/index.md`
- `assets/studio/js/studio-works.js`
- `assets/css/main.css`
- `assets/studio/css/studio.css`
- [Catalogue Works](/docs/?scope=studio&doc=studio-works)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The route keeps works-specific data loading, return links, and column templates while sharing the dense list type scale, row rhythm, sortable-header styling, indicator styling, and title emphasis.

## [2026-05-07] Added the Library Documents Studio page

**Status:** implemented

**Area:** Studio / Library

**Summary:**
Added `/studio/library-documents/` as a read-only dense-list review page for generated Library Docs Viewer records.

**Reason:**
Library document review needs a compact scan table with viewable and parent state without entering the export selection workflow.

**Files changed:**

- `studio/library-documents/index.md`
- `assets/studio/js/library-documents.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `studio/library/index.md`
- [Library Documents](/docs/?scope=studio&doc=library-documents)
- [Library](/docs/?scope=studio&doc=library)
- [Studio](/docs/?scope=studio&doc=studio)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
The Library dashboard now links to a document index under the HTML Import entry.
The page sorts by `doc_id`, `added_date`, and `title`, opens document links in Library manage mode, places parent and viewable status before the title, shows the export-style green viewable dot, marks parent docs with a tick, and filters independently by `viewable` and `parent`.

## [2026-05-06] Respected root sort order in Docs Viewer metadata edits

**Status:** implemented

**Area:** Docs Viewer / Management

**Summary:**
Changing a doc's parent to root in the metadata modal now preserves the visible `sort_order` value instead of converting the save request to append.

**Reason:**
The modal's append shortcut was intended for moving a doc into another parent while leaving the existing sort field untouched.
For root moves, that made the shown `sort_order` look ignored and placed the doc at the bottom of the root index.

**Files changed:**

- `assets/js/docs-viewer.js`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
Root reparenting now respects the sort field the user can see and edit.
Moving into a non-root parent still appends by default when the sort field is left unchanged.

## [2026-05-06] Quieted available Docs Viewer manage mode

**Status:** implemented

**Area:** Docs Viewer / UI

**Summary:**
The Docs Viewer no longer shows the "Manage mode is local-only" note after the local docs-management server is confirmed available.

**Reason:**
The visible note was only useful while manage mode was unavailable or still checking.
Once the local server is running and the management toolbar is enabled, it became persistent chrome rather than actionable status.

**Files changed:**

- `assets/js/docs-viewer.js`
- `assets/studio/data/studio_config.json`
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Impact:**
Manage mode still shows checking, server-unavailable, archive-unavailable, search-blocked, and operation-result notes.
The normal available state is quieter and leaves the management controls to carry the mode context.

## [2026-05-06] Preserved cross-scope Docs Viewer links

**Status:** implemented

**Area:** Docs / Builder

**Summary:**
The docs builder now keeps cross-scope viewer links on their original viewer route instead of resolving matching `doc` query values against the current build scope.

**Reason:**
The Studio `library` doc intentionally links to the public Library viewer at `/library/?doc=library`.
Because the Studio docs scope also has a `library` doc id, the previous link rewrite treated that public Library route as a same-scope Studio docs link and generated `/docs/?scope=studio&doc=library`.

**Files changed:**

- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Library](/docs/?scope=studio&doc=library)
- `scripts/build_docs.rb`

**Impact:**
Same-scope viewer links and relative `.md` links still normalize onto the current scope's viewer route.
Cross-scope links such as `/library/?doc=library` now keep their intended public destination.

## [2026-05-06] Ignored code-block links in Docs Broken Links

**Status:** implemented

**Area:** Docs / Validation

**Summary:**
The Docs Broken Links audit now skips links rendered inside code blocks.

**Reason:**
Code examples may intentionally contain illustrative docs URLs that are not live navigation and should not be reported as broken links.

**Files changed:**

- [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- `scripts/docs/docs_broken_links.py`
- `scripts/run_checks.py`
- `tests/python/test_docs_broken_links.py`

**Impact:**
The audit remains focused on navigable prose links while code samples can show obsolete, example, or placeholder docs URLs without creating maintenance findings.

## [2026-05-06] Removed title mismatches from Docs Broken Links

**Status:** implemented

**Area:** Docs / Validation

**Summary:**
The Docs Broken Links audit now reports only missing docs targets. The Studio route no longer renders title-mismatch filters or counts, and the CLI summary no longer includes `wrong title`.

**Reason:**
Visible link labels are not hard failures. They may intentionally shorten a title, preserve historical wording, or correct an outdated target title in context.

**Files changed:**

- [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
- `assets/studio/js/docs-broken-links.js`
- `assets/studio/js/studio-config.js`
- `assets/studio/data/studio_config.json`
- `scripts/docs/docs_broken_links.py`
- `scripts/docs/docs_management_server.py`

**Impact:**
The audit is focused on links that fail to resolve. Stale or intentionally different link text is left to editorial review rather than treated as a broken-link issue.

## [2026-05-06] Relaxed archived changelog title-link audits

**Status:** implemented

**Area:** Docs / Validation

**Summary:**
The Docs Broken Links audit now skips strict wrong-title checks for historical site-change-log archive docs while still reporting missing targets from those archives.

**Reason:**
Archived changelog entries preserve historical wording, so their link labels often intentionally differ from current document titles.
Missing targets are still useful maintenance findings, but exact title warnings from old entries were creating noise.

**Files changed:**

- [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
- [Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)
- `scripts/docs/docs_broken_links.py`

**Impact:**
This was superseded later on 2026-05-06 when title mismatches were removed from the broken-links audit altogether.
The archived-doc exception is no longer needed, but this entry remains as historical context for the intermediate behavior.

## [2026-05-06] Split the site change log into dated archive docs

**Status:** implemented

**Area:** Docs / Architecture

**Summary:**
Kept the stable Site Change Log doc as the current entry point and moved older entries into dated archive child docs.
The main log now carries the newest entries plus links to the May 2026, April 2026, and March 2026-and-earlier archives.

**Reason:**
The single source file had grown past 7,300 lines, making routine close-out edits, review, and docs payload inspection harder than necessary.
Keeping a compact current page preserves the existing docs-viewer link while moving historical reading into focused archive docs.

**Files changed:**

- [Site Change Log](/docs/?scope=studio&doc=site-change-log)
- [Site Change Log Archive: May 2026](/docs/?scope=studio&doc=site-change-log-2026-05)
- [Site Change Log Archive: April 2026](/docs/?scope=studio&doc=site-change-log-2026-04)
- [Site Change Log Archive: March 2026 And Earlier](/docs/?scope=studio&doc=site-change-log-2026-03-and-earlier)
- [Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)

**Impact:**
New change-log entries still go into the stable `site-change-log` doc first.
Older history remains published and searchable through archive child docs under the same docs-viewer section.

## [2026-05-06] Stabilized shared data export/import routes

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
Moved the active Studio export/import shells to `/studio/export/` and `/studio/import/`.
The browser modules, route-ready names, DOM ids, CSS classes, Studio config route keys, and UI text namespaces now use shared `data_export` and `data_import` naming.
The Library-specific export config file remains Library-named because it is the current documents-adapter config contract.

**Reason:**
The shared route shell should be the stable target before Catalogue and Analytics workflow requirements grow.
Keeping active routes neutral avoids preserving the old Library route names as compatibility aliases while still leaving Library domain docs and adapter configs explicit.

**Files changed:**

- [Studio Data Export](/docs/?scope=studio&doc=studio-data-export)
- [Studio Data Import](/docs/?scope=studio&doc=studio-data-import)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)
- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- `studio/export/index.md`
- `studio/import/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/js/data-import.js`
- `tests/smoke/data_export.py`
- `tests/smoke/data_import.py`

**Impact:**
Library dashboard links and future Catalogue/Analytics dashboard links all target the same shared shell with `scope=...`.
The old `/studio/library-export/` and `/studio/library-import/` pages are removed rather than retained as aliases.

## [2026-05-06] Closed export/import adapter boundary request

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
Completed the export/import adapter boundary documentation and verification pass.
The request now records the implemented Library documents adapter, normalized workflow folders, future Catalogue and Analytics stubs, and verification coverage.

**Reason:**
The adapter boundary should be visible in stable Library, script, config, and change-request docs before future data-domain work starts.

**Files changed:**

- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Impact:**
Standard checks now include adapter dispatch verification and a Studio smoke case for disabled future adapters.
The change request is marked implemented while Catalogue and Analytics behavior remains explicitly deferred.

## [2026-05-06] Added future export/import adapter stubs

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
Added explicit `catalogue` and `analytics` adapter stubs to the export/import adapter registry.
The stubs declare planned capabilities and placeholder workflow roots without implementing domain behavior.

**Reason:**
Future Catalogue and Analytics requirements need named extension points, but they should not be folded into the Library documents adapter or inferred by route code.

**Files changed:**

- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- [Export Import Adapters](/docs/?scope=studio&doc=config-export-import-adapters)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- `assets/studio/data/export_import_adapters.json`
- `scripts/docs/export_import_adapters.py`

**Impact:**
The current export/import pages read domain availability from the adapter registry and can show planned future domains as unavailable.
The docs-management service still dispatches only active capabilities, so stub adapters fail closed before document-specific code runs.

## [2026-05-06] Normalized export/import workflow folders

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
Moved Library export/import working artifacts to a data-domain-first layout under `var/studio/export-import/library/`.
The `documents` adapter now declares the Library export, staging, and preview roots used by the docs-management service.

**Reason:**
The shared export/import shell should not encode Docs Viewer folder names as the universal workflow layout.
Keeping folders under the adapter registry makes the path contract explicit and keeps future domains from inheriting document-specific paths.

**Files changed:**

- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- [Export Import Adapters](/docs/?scope=studio&doc=config-export-import-adapters)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)

**Impact:**
Exports now write under `var/studio/export-import/library/exports/`.
Staged import files are read from `var/studio/export-import/library/import-staging/`, and generated previews write under `var/studio/export-import/library/import-preview/`.
Old local files under the previous test folders are not migrated.

## [2026-05-06] Moved document import/export dispatch behind adapter config

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
Added the explicit export/import adapter registry and routed the Library document export/import behavior through the configured `documents` adapter.
The active import service endpoints are now neutral dispatch endpoints instead of Library-named service routes.

**Reason:**
The first implementation should target the shell-adapter architecture directly so old route names and migration artifacts do not become long-lived compatibility layers.

**Files changed:**

- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Export Import Adapters](/docs/?scope=studio&doc=config-export-import-adapters)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Impact:**
`data_domain` and `operation` now resolve exactly one configured adapter before the docs-management service runs document-specific import/export logic.
Unconfigured domains fail closed, and the removed Library-named import endpoints are not retained as aliases.

## [2026-05-05] Added export/import adapter boundary request

**Status:** proposed

**Area:** Studio / Data workflows

**Summary:**
Added a change request to adopt an adapter-based export/import architecture before more Library, Analytics, or Catalogue requirements are added to the shared workflow shell.
The current Library document workflow is identified as the first adapter implementation target.

**Reason:**
Library import/export is document-specific, while future Analytics and Catalogue workflows need domain-specific validation and apply behavior against structured site data.
The adapter boundary keeps shared lifecycle behavior reusable without making document preview semantics universal.

**Files changed:**

- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- [Change Requests](/docs/?scope=studio&doc=change-requests)

**Impact:**
Future export/import requirements now have a stable planning target that separates shared shell responsibilities from scope-specific adapter behavior.
Follow-up review resolved the initial direction: adapters map to data domains rather than route scopes, Library should use a general documents adapter with Library config, neutral export/import routes are preferred, and user-facing workflow folders should be data-domain-first.

## [2026-05-05] Added Docs Toolkit extraction request

**Status:** proposed

**Area:** Docs / Tooling

**Summary:**
Added a change request to explore whether the Docs Viewer, generated docs/search pipeline, local docs-management server, and scope-aware export/import workflow should become a reusable docs toolkit that other repositories can track from a master version.

**Reason:**
The combined docs viewer and export/import workflow is becoming a useful local tool beyond this site, but reuse needs a managed upstream model instead of copied files.

**Files changed:**

- [Docs Toolkit Extraction Request](/docs/?scope=studio&doc=site-request-docs-toolkit-extraction)
- [Change Requests](/docs/?scope=studio&doc=change-requests)

**Impact:**
The extraction idea now has a stable planning target with goals, non-goals, install-shape options, open questions, and acceptance criteria.

## [2026-05-05] Stabilized image-panel text across themes

**Status:** implemented

**Area:** Studio / UI

**Summary:**
Base Studio image panel links now keep their dark text treatment in both light and dark mode.
The existing `tagStudio__panelLink--imageContrast` modifier remains the explicit white-text variant for darker or busier images.

**Reason:**
Image panels are design-time compositions.
Keeping one text treatment avoids per-theme image swaps and makes image/overlay choice the design responsibility.

**Files changed:**

- `assets/studio/css/studio.css`
- `_includes/ui_catalogue_notes/panel.md`
- [Panel Primitive](/docs/?scope=studio&doc=ui-primitive-panel)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
`/studio/` image panels and the Panel primitive image examples stay legible in dark mode without changing source images.

## [2026-05-05] Fixed dark-mode Studio panel contrast

**Status:** implemented

**Area:** Studio / UI

**Summary:**
Studio panels now switch their surface, border, muted text, default-value, and control tokens together in dark mode.
This prevents light panels from combining with dark-mode muted text on routes such as `/studio/import/`.

**Reason:**
The previous token mix left field labels and disabled controls nearly invisible in dark mode because the panel stayed white while muted text became pale grey.

**Files changed:**

- `assets/studio/css/studio.css`
- [Panel Primitive](/docs/?scope=studio&doc=ui-primitive-panel)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Shared Studio panels and controls have coherent dark-mode contrast instead of relying on route-local overrides.

## [2026-05-05] Added aggregate public search

**Status:** implemented

**Area:** Search

**Summary:**
Direct `/search/` now works as an aggregate search across enabled dedicated-route scopes instead of showing the missing-scope message.
Explicit scoped search URLs remain supported for Catalogue, Library, Studio, and Analysis.

**Reason:**
The public search route should be useful when opened directly now that multiple generated search indexes exist.

**Files changed:**

- `assets/js/search/search-page.js`
- `assets/js/search/search-policy.js`
- `assets/data/search/policy.json`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Search](/docs/?scope=studio&doc=search)
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Change Log](/docs/?scope=studio&doc=search-change-log)
- [Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)

**Impact:**
Users can open `/search/` directly and search across Catalogue, Library, Studio docs, and Analysis results in one list.
The aggregate route does not show a visible `all` heading and does not fail the whole page when one enabled scope index is unavailable.
During `bin/dev-studio`, docs-domain search reads use the docs-management generated-search endpoint rather than Jekyll's dev-overlay output.

## [2026-05-05] Refined Search dashboard to column links

**Status:** implemented

**Area:** Studio / Search

**Summary:**
`/studio/search/` now matches the compact dashboard structure used by the other Studio domain dashboards.
The page keeps its metrics, removes intro and panel-card descriptive copy, and groups routes into `interface` and `documents` columns using the shared Column Links pattern.
The documents column links to the Search plan and Search change log.

**Reason:**
Search is a Studio domain entry page.
The shared column-link pattern is a better fit for routine navigation than bespoke descriptive panels.

**Files changed:**

- `studio/search/index.md`
- [Search Plan](/docs/?scope=studio&doc=new-pipeline-refine-search)
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Catalogue, Library, Analytics, and Search dashboards now share the same compact route-entry language.

## [2026-05-05] Added scoped data links to domain dashboards

**Status:** implemented

**Area:** Studio / Dashboards

**Summary:**
`/studio/catalogue/` now includes a `Data` column with export and import pills linked to the shared workflow routes with `?scope=catalogue`.
`/studio/library/` now makes its existing export and import pills explicit with `?scope=library`.
The Column Links pattern supports a three-column modifier for Catalogue while keeping two-column dashboards unchanged.

**Reason:**
After import/export became scope-aware, domain dashboards should route users directly to the relevant scoped data workflow instead of relying on defaults or leaving Catalogue without data entry points.

**Files changed:**

- `studio/catalogue/index.md`
- `studio/library/index.md`
- `assets/css/main.css`
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Catalogue, Library, and Analytics now all expose scoped data workflow links from their dashboards.

## [2026-05-05] Refined Analytics dashboard to column links

**Status:** implemented

**Area:** Studio / Analytics

**Summary:**
`/studio/analytics/` now matches the compact dashboard structure used by Catalogue and Library.
The page keeps its metrics, removes intro and panel-card descriptive copy, and groups routes into `Data` and `Tags` columns using the shared Column Links pattern.
Analytics import/export links point at the shared scope-aware data workflow shell.

**Reason:**
Analytics is a Studio domain entry page like Catalogue and Library.
The shared column-link pattern is a better fit for routine navigation than bespoke descriptive panels.

**Files changed:**

- `studio/analytics/index.md`
- [Analytics Plan](/docs/?scope=studio&doc=new-pipeline-refine-analytics)
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
The three main Studio domain dashboards now share the same compact route-entry language while preserving their domain-specific links.

## [2026-05-05] Made Library import/export routes scope-aware

**Status:** implemented

**Area:** Studio / Data workflows

**Summary:**
`/studio/export/` and `/studio/import/` now expose a scope selector for `library`, `catalogue`, and `analytics`.
Library remains the default scope.
Export config filtering now uses the selected scope and handles future scopes with no enabled configs without failing the page.
Import staged-file listing and preview generation now use `var/docs/import-staging/<scope>/` and `var/docs/import-preview/<scope>/` for the supported workflow scopes.
Source-write apply actions remain enabled only for Library.

**Reason:**
Catalogue and Analytics need the same export/stage/preview workflow shape for future LLM review work, but their record shapes, config details, and write actions are not defined yet.
The shared page and service infrastructure can support those scopes before the scope-specific contracts are designed.

**Files changed:**

- `studio/export/index.md`
- `studio/import/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/js/data-import.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `scripts/docs/docs_import.py`
- `scripts/docs/docs_management_server.py`
- `tests/python/test_docs_import_service.py`
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
The workflow shell is ready for Catalogue and Analytics configs.
Until those configs and source-write contracts exist, non-Library export scopes show no enabled configs and non-Library import scopes support staged preview only.

## [2026-05-05] Added UI Catalogue composition pattern pages

**Status:** implemented

**Area:** Studio / UI Catalogue

**Summary:**
The UI Catalogue index now uses the shared two-column route-link pattern already used by the Catalogue and Library dashboards.
It groups links into `Primitives` and `Composition Patterns`.
Added live UI Catalogue pages for the reopenable command result pattern and the column links pattern, plus a matching docs-viewer contract for Column Links.

**Reason:**
The catalogue index is a route-entry page, not a descriptive card surface.
Reusing the dashboard column-link composition keeps the UI system catalogue aligned with the pattern it is documenting.

**Files changed:**

- `studio/ui-catalogue/index.md`
- `studio/ui-catalogue/reopenable-command-result/index.md`
- `studio/ui-catalogue/column-links/index.md`
- `assets/studio/css/studio.css`
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Reopenable Command Result Pattern](/docs/?scope=studio&doc=ui-pattern-reopenable-command-result)
- [Column Links Pattern](/docs/?scope=studio&doc=ui-pattern-column-links)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Repeated Studio route-entry link groups now have a named composition pattern and a live reference page.

## [2026-05-05] Added UI framework and catalogue target docs

**Status:** implemented

**Area:** Docs / Design

**Summary:**
Added `UI` as the unified site-wide UI framework target under Design.
Added matching UI Catalogue child docs for button, input, list, and panel primitives, plus a composition-pattern doc for reopenable command results.
Updated the catalogue model so live primitive pages are visual references while matching docs hold implementation and lifecycle contracts.

**Reason:**
The old split between `UI Framework`, `Studio UI Framework`, `UI Catalogue`, and `Studio UI Rules` mixed framework guidance, primitive contracts, implementation notes, and historical decisions in one layer.
The new targets give stable destinations for moving durable content out of the rules log and retiring the artificial site-vs-Studio split.

**Files changed:**

- [Design](/docs/?scope=studio&doc=design)
- [UI](/docs/?scope=studio&doc=ui)
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Button Primitive](/docs/?scope=studio&doc=ui-primitive-button)
- [Input Primitive](/docs/?scope=studio&doc=ui-primitive-input)
- [List Primitive](/docs/?scope=studio&doc=ui-primitive-list)
- [Panel Primitive](/docs/?scope=studio&doc=ui-primitive-panel)
- [Reopenable Command Result Pattern](/docs/?scope=studio&doc=ui-pattern-reopenable-command-result)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Future UI work can file durable rules into framework, primitive, or composition-pattern docs instead of burying them in the Studio UI decision log.

## [2026-05-05] Refined Library import review UI

**Status:** implemented

**Area:** Studio / Library import

**Summary:**
The Library import route now keeps staged-file selection and preview/apply commands in one compact row.
It removes staged-file path/format/size/modified metadata from the page, removes generated preview-file paths from document row metadata, and shows preview/apply completion details in a shared modal with a single `Close` button.
The modal presents counts as a compact vertical label/value stack with right-aligned values and issues below the counts.
Preview completion messages now use context-aware singular/plural wording for generated preview files.
A small `results` button appears beside the preview success message while that message remains current, allowing the last preview result modal to be reopened.

**Reason:**
The route is now a repeated review/apply workflow.
Persistent file and result details made the page harder to scan after the document list became the main working surface.

**Files changed:**

- `studio/import/index.md`
- `assets/studio/js/data-import.js`
- `assets/studio/js/studio-modal.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `tests/smoke/data_import.py`
- [Library Import UI Refinements](/docs/?scope=studio&doc=library-import-ui)
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Library import is more compact and consistent with the Library export result-modal pattern.
The result modal no longer exposes source export id, generated timestamp, or preview-file paths in the main UI; those remain available through staged/generated files and service payloads when needed.

## [2026-05-04] Closed Library import/export v2 task list

**Status:** implemented

**Area:** Studio / Library import-export

**Summary:**
Marked the Library import/export v2 request as implemented and closed its documentation and verification task.
The request now points at the separate generated-parent-nodes follow-up for future hierarchy imports that need to create new Library grouping docs.

**Reason:**
The v2 task list now has implemented export filters, export formats, import previews, summary apply, hierarchy apply, docs updates, generated docs payloads, and verification coverage.
New parent-node creation is a distinct future source-creation contract rather than a loose extension of unknown `parent_id` handling.

**Files changed:**

- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Library Import Generated Parent Nodes Request](/docs/?scope=studio&doc=site-request-library-import-generated-parent-nodes)

**Impact:**
The current v2 implementation can be treated as closed.
Future generated parent-node work has its own request and should not be folded into the existing hierarchy apply contract without a new task pass.

## [2026-05-04] Added hierarchy apply for Library imports

**Status:** implemented

**Area:** Studio / Library import

**Summary:**
The Library import page can now apply selected staged `parent_id` values to canonical Library source documents.
`Apply hierarchy` enables only for selected document preview rows, runs a preflight against staged record indexes and current `_docs_library_src/` files, shows a shared OK/Cancel confirmation modal, then writes only selected parent-id changes.
The docs-management endpoint creates a timestamped `data-import-hierarchy-apply` backup under the existing `var/docs/backups/` root before writing and runs targeted Library docs-search updates for changed ids.
Generated Library docs data now treats unresolved imported source parents as root-level relationships so unknown external parents do not break `/library/`.

**Reason:**
Task 8 needed hierarchy writes separate from summary writes.
Keeping this parent-id-only preserves current `sort_order` and leaves future sort-order imports for the later file format that actually includes that field.

**Files changed:**

- `assets/studio/js/data-import.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/data/studio_config.json`
- `scripts/docs/docs_management_server.py`
- `scripts/build_docs.rb`
- `tests/python/test_docs_import_service.py`
- `tests/smoke/data_import.py`
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)

**Impact:**
Selected staged hierarchy rows can update Library source safely with preflight reporting, backups, and skipped/warning rows.
Full-content applies and imported `sort_order` writes remain separate future contracts.

## [2026-05-04] Added summary apply for Library imports

**Status:** implemented

**Area:** Studio / Library import

**Summary:**
The Library import page can now apply selected staged summaries to canonical Library source documents.
`Update summary` enables only for selected document preview rows, runs a preflight against the staged record indexes and current `_docs_library_src/` files, shows a shared OK/Cancel confirmation modal, then writes only the selected summary changes.
The docs-management endpoint creates a timestamped `data-import-summary-apply` backup under the existing `var/docs/backups/` root before writing and runs targeted Library docs-search updates for changed ids.

**Reason:**
Task 7 needed the first narrow source-write path before hierarchy writes.
Keeping the apply action summary-only makes the import flow useful for missing-summary cleanup without mixing it with full-content or relationship changes.

**Files changed:**

- `assets/studio/js/data-import.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/data/studio_config.json`
- `scripts/docs/docs_management_server.py`
- `tests/python/test_docs_import_service.py`
- `tests/smoke/data_import.py`
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)

**Impact:**
Selected staged summary rows can update Library source safely with preflight reporting and backups.
Hierarchy, `sort_order`, and full-content applies remain separate future contracts.

## [2026-05-04] Added selectable Library export formats

**Status:** implemented

**Area:** Studio / Library export

**Summary:**
Library export configs now declare selectable output formats with `target.supported_formats`, while `target.format` remains the default.
The Studio Library export page shows JSON and JSONL options, disables unsupported combinations, sends `target_format` to `POST /docs/export`, and shows the selected format in the result modal.
Document-row exports can now write JSON arrays as well as JSONL rows when the config supports both.

**Reason:**
Task 6 needed user-visible format choice without making broad format assumptions across every export pattern.
Keeping supported formats config-declared lets the CLI, service endpoint, and Studio UI share the same validation boundary.

**Files changed:**

- `assets/studio/data/library_export_configs.json`
- `assets/studio/data/library_export_configs.schema.json`
- `scripts/docs/docs_export.py`
- `scripts/docs/docs_management_server.py`
- `studio/export/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/css/studio.css`
- `tests/python/test_docs_export.py`
- `tests/python/test_docs_management_server.py`
- `tests/smoke/data_export.py`
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Impact:**
Summary and full-content exports default to JSONL but can be written as JSON arrays.
Parent-child relationship exports remain JSON-only.

## [2026-05-04] Added Library export list filters

**Status:** implemented

**Area:** Studio / Library export

**Summary:**
The Library export page now has `show all`, `no content`, and `not viewable` filter pills with counts.
The generated docs index now includes `content_text_length`, derived from rendered document HTML after plain-text extraction and title stripping, so the page can identify no-content docs without fetching every per-doc payload.
Select all now targets the currently visible filtered list; the export request still sends explicit selected doc ids and the export write path is unchanged.

**Reason:**
Library export review needs quick slices for empty generated docs and generated-but-hidden docs before output-format work starts.

**Files changed:**

- `scripts/build_docs.rb`
- `studio/export/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `tests/smoke/data_export.py`
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Docs Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)

**Impact:**
The UI can narrow selection without changing config definitions or service payload shape.
Generated docs index rows have one additional numeric metadata field.

## [2026-05-04] Added relationship metadata to full Library content exports

**Status:** implemented

**Area:** Studio / Library export

**Summary:**
The `library-full-document-content` export config now declares parent, ancestor, and child relationship fields alongside `source_text`.
Full-content JSONL rows include `parent_id`, `parent_title`, `ancestor_ids`, `ancestor_titles`, `child_ids`, and `child_titles` without adding a separate UI option.
`sort_order` remains deferred until external hierarchy files and import apply behavior support it.

**Reason:**
Library import previews can now build a staged hierarchy tree from full-content export files when relationship metadata is present.
Keeping the fields in the export config preserves the config/runtime contract and avoids adding another export-page control.

**Files changed:**

- `assets/studio/data/library_export_configs.json`
- `tests/python/test_docs_export.py`
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)

**Impact:**
Full-content exports are more useful as import-preview staging files and external review bundles.
Consumers should expect relationship fields in the full-content rows, but not `sort_order` yet.

## [2026-05-04] Aligned Library import with the export page shell

**Status:** implemented

**Area:** Studio / Library import

**Summary:**
Updated `/studio/import/` so its first v2 milestone uses the same compact command/list shell as `/studio/export/`.
The page now places Preview beside the staged-file selector, shows Select all and Clear pills, renders generated previews in the main selectable list area, and keeps future `Update summary` and `Apply hierarchy` actions visible but disabled.
Preview rows are ordered and indented from staged `parent_id` metadata when relationship data is available, and generated relationship-tree preview files appear as their own visible list row.
Preview files now use staged-file timestamp suffixes when present, include front-matter-like matched-config and staged-only sections, and generate a whole-tree preview whenever staged relationship metadata is available.

**Reason:**
Library import v2 should begin with review-oriented UI changes before source-write wiring.
Sharing the export page structure keeps the Library data workflows predictable while the apply contracts remain intentionally unavailable.

**Files changed:**

- `studio/import/index.md`
- `assets/studio/js/data-import.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `tests/smoke/data_import.py`
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
The import route now has the hierarchy-aware preview list needed before preview-file normalization and source-write contract work.
The main risk is that preview-row selection is currently review-only because source-write endpoints do not exist yet; the disabled action buttons make that boundary explicit.

## [2026-05-04] Added Studio backup retention on dev startup

**Status:** implemented

**Area:** Studio / local operations

**Summary:**
Added `scripts/studio_backup_retention.py` and wired it into `bin/dev-studio` startup.
The script prunes local Studio backup files by keeping the newest backups per target file: `20` for `var/studio/backups/` and `30` for `var/studio/catalogue/backups/`.

**Reason:**
This repo has no separate admin role, so local operational backups need a default retention policy that runs through the normal development entry point rather than relying on manual cleanup habits.

**Changes:**
`bin/dev-studio` now runs backup retention once at startup before long-running services start.
The cleanup skips unparseable backups, keeps whole catalogue transaction bundles when any contained target is still retained, and continues startup with a warning if cleanup fails.
Startup cleanup can be disabled with `DOTLINEFORM_BACKUP_RETENTION=off` or `DOTLINEFORM_BACKUP_RETENTION=0`.

**Files changed:**

- `bin/dev-studio`
- `scripts/studio_backup_retention.py`
- `tests/python/test_studio_backup_retention.py`
- `scripts/run_checks.py`
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
- [Studio Backup Retention](/docs/?scope=studio&doc=scripts-studio-backup-retention)
- [Studio Config And Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)

**Impact:**
Local backup folders should stop growing indefinitely during normal Studio use.
The main risk is accidental pruning of a backup that would have been useful for unusually old local recovery; the newest-N-per-target policy and skipped unparseable files keep that risk narrow.

## [2026-05-04] Cleaned staged catalogue thumbnails after asset copy

**Status:** implemented

**Area:** Catalogue / local media generation

**Summary:**
Scoped catalogue media builds now treat staged thumbnail derivatives as temporary files.
After a generated thumbnail is copied into `assets/works/img/`, `assets/work_details/img/`, or `assets/moments/img/`, the matching file under `var/catalogue/media/<kind>/srcset_images/thumb/` is removed.

**Reason:**
Primary derivatives under `var/catalogue/media/` remain the manual handoff point for remote media publishing until R2 upload is automated.
Staged thumbnails do not have the same handoff responsibility once the public asset-folder copy succeeds, so retaining them only grows local cache size.

**Changes:**
The local media planner no longer treats staged thumbnail paths as persistent currentness outputs.
It generates staged thumbnails only when public asset thumbnails need refresh, copies them to the asset folders, and then deletes the staged thumbnail intermediates.
The media build response records cleaned staged thumbnail paths for diagnostics.

**Files changed:**

- `scripts/catalogue_json_build.py`
- `tests/python/test_catalogue_media_cleanup.py`
- `scripts/run_checks.py`
- [Build Catalogue JSON](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

**Impact:**
Future media refreshes keep staged source images and staged primary derivatives, but no longer retain thumbnail intermediates after successful asset copy.
Existing staged thumbnail files can be removed manually or by a later retention cleanup.

## [2026-05-04] Routed local Docs Viewer data reads through the docs server

**Status:** implemented

**Area:** Docs Viewer / local Studio runtime

**Summary:**
The docs-management server now serves allowlisted generated docs index, payload, and docs-search JSON for Studio, Library, and Analysis scopes. The shared Docs Viewer prefers those server reads when the localhost capability is available, while public/static routes continue to use generated JSON assets directly.

**Reason:**
Generated docs/search rewrites are local runtime data changes, not Jekyll source changes. Moving local reads through the server lets `bin/dev-studio` stop making Jekyll watch those generated JSON trees.

**Changes:**
Added `GET /docs/generated/index`, `GET /docs/generated/payload`, and `GET /docs/generated/search` with raw JSON responses, strict scope/doc validation, and `Cache-Control: no-store`.
The Docs Viewer now probes generated-read capability and uses server reads for index, payload, and search data when available.
`bin/dev-studio` now starts Jekyll with `_config.yml,_config.dev-studio.yml`; the overlay excludes generated docs/search JSON and keeps public builds unchanged.

**Files changed:**

- `scripts/docs/docs_management_server.py`
- `assets/js/docs-viewer.js`
- `bin/dev-studio`
- `_config.dev-studio.yml`
- [Local Docs Data Server Reads Request](/docs/?scope=studio&doc=site-request-local-docs-data-server-reads)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)

**Impact:**
Local docs source edits can still rebuild generated docs/search data immediately, but Jekyll no longer needs to regenerate because those generated files changed during `bin/dev-studio`.

## [2026-05-04] Fixed Studio static docs/search reads under the dev overlay

**Status:** implemented

**Area:** Studio / local data reads

**Summary:**
`/studio/export/` now reads the generated Library docs index through the docs-management server when that service is available. The Studio dashboard also uses docs-management generated-data reads for Library docs count and docs-search metrics when running locally.

**Reason:**
The dev-only Jekyll overlay removes generated docs/search JSON from Jekyll output, so Studio pages must not fetch those static paths while `bin/dev-studio` is running.

**Files changed:**

- `assets/studio/js/data-export.js`
- `assets/studio/js/studio-dashboard.js`
- `assets/studio/js/studio-transport.js`
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

## [2026-05-04] Treated Archive as a normal Docs Viewer folder

**Status:** implemented

**Area:** Docs Viewer / docs search

**Summary:**
Renamed the Archive docs parent from `_archive` to `archive` and removed structural Archive behavior from the docs viewer, docs builder, docs search builder, Library export list, and docs-management server.

**Reason:**
The `viewable` flag now provides the visibility contract directly. Keeping `_archive` preserved a hidden-file naming problem and made Archive behave differently from other folders.

**Changes:**
Studio and Library Archive docs now use `doc_id: archive` and set `viewable: false`.
Generated viewer options no longer mark `archive` as non-loadable or manage-only.
Docs search excludes non-viewable docs rather than excluding `archive` by id.
The docs-management server lets `archive` be edited, moved, deleted when it has no children, and made viewable; the Archive command uses `archive` as its conventional destination parent and no-ops if invoked on `archive` itself.
Library export now includes generated Archive docs according to the same selection rules as other docs.

**Files changed:**

- `_docs_src/archive.md`
- `_docs_library_src/archive.md`
- `scripts/build_docs.rb`
- `scripts/build_search.rb`
- `scripts/docs/docs_management_server.py`
- `assets/js/docs-viewer.js`
- `assets/studio/js/data-export.js`
- `assets/studio/data/library_export_configs.json`
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Impact:**
Archive behavior is simpler and more consistent with the rest of the docs tree.
The main risk is accidental public exposure if `archive` or archived child docs are manually changed to `viewable: true`; that is now an explicit metadata decision rather than hidden structural behavior.

## [2026-05-04] Refined the Library export Studio UI

**Status:** implemented

**Area:** Library / Studio data export

**Summary:**
Applied the Library export UI refinements from [Library Export - UI refinements](/docs/?scope=studio&doc=library-export-ui).

**Reason:**
The export page needed less passive helper text, tighter command placement, and a dismissible result surface that focuses on counts and created files.

**Changes:**
The route now places `Run export` beside the export-pattern dropdown, keeps the missing-summaries checkbox under that dropdown, and shows Select all / Clear as checklist pills.
The selected-doc summary no longer reports missing-summary counts.
Completed export reports now open in a shared Studio modal with vertical counts, a filename-only read-only text box, optional warnings/issues, and one Close button.
The docs-management export summary now uses `document` or `documents` according to the exported count.

**Files changed:**

- `studio/export/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `scripts/docs/docs_management_server.py`
- `tests/python/test_docs_import_service.py`
- [Library Export - UI refinements](/docs/?scope=studio&doc=library-export-ui)
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
The page is denser and more command-oriented, with export completion details no longer occupying permanent page space.
The modal adds a small interaction step after successful exports, but keeps the main checklist workflow cleaner.

## [2026-05-04] Library relationship exports now respect checklist selection

**Status:** implemented

**Area:** Library / Studio data export

**Summary:**
Changed the Parent-child relationships export pattern from implicit all-matching selection to explicit selected-document selection.

**Reason:**
The `/studio/export/` page displayed the same hierarchical checklist for this pattern as for the other export patterns, but the config asked the export engine to include all matching docs.
That made selected branches irrelevant and produced whole-corpus exports.

**Changes:**
`library-parent-child-relationships` now uses `explicit_doc_ids`, while keeping descendant expansion so selecting a parent still exports its branch.
Whole-corpus relationship review remains available by selecting all in Studio or passing `--all` to the CLI.
Focused export coverage now asserts that the parent-child pattern respects a single selected doc.

**Files changed:**

- `assets/studio/data/library_export_configs.json`
- `tests/python/test_docs_export.py`
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Branch-level relationship exports now match the operator's checklist selection.
Large whole-corpus exports require an explicit Select all or `--all` action.

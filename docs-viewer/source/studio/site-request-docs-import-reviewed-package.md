---
doc_id: site-request-docs-import-reviewed-package
title: Docs Import Reviewed Package
added_date: 2026-07-11
last_updated: 2026-07-12
ui_status: proposed
summary: Move Docs Import to the W0-resolved shared drop-zone, import immutable staged Data Sharing JSONL as a collection, and retain a persistent read-only review projection.
parent_id: change-requests
viewable: true
---
# Docs Import Reviewed Package

## Status

Proposed follow-on to [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package) and the current [Docs Review](/docs/?scope=studio&doc=docs-viewer-review) implementation.

The current workflow already proves the persistent Docs Review package and renderer. This request simplifies the remaining import path and removes source editing from Docs Review.

## Decision

Treat the staged Data Sharing JSON/JSONL file as another Docs Import source format.

As a prerequisite, move every Docs Viewer import format to the existing shared drop-zone:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/
```

This folder is not exclusive to the Data Sharing application. It is the consistent user-facing import drop-zone. Which application or workflow uses a file depends on the file format, schema, trusted metadata, and the action the user invokes.

Keep the persistent preview package because JSONL is not convenient for a person to review and the review and import decisions may happen at different times. The preview package is a durable, read-only view projection; it is not the import source.

```text
immutable staged JSONL
  -> persistent read-only Docs Review projection
     -> import-preview/<package_id>/source/*.md
     -> import-preview/<package_id>/generated/...

immutable staged JSONL
  -> Docs Viewer collection import
     -> create, overwrite, or skip
     -> configured-scope Markdown
```

The staged file remains the authoritative returned package. Docs Import reads that file directly when the user later chooses to import it. A missing content field is authoritative as a preserve-existing or empty-new intent; it does not make the derived preview body import input.

## Artifact Roles

| Artifact | Role | Write authority |
| --- | --- | --- |
| `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/` | shared user drop-zone for all supported imports | user placement and Data Sharing staging producers |
| `<timestamped-file>.jsonl` inside that drop-zone | immutable returned package and collection import input | Data Sharing staging contract |
| `import-preview/<package_id>/manifest.json` | trusted association between the staged package and its view projection | preview producer only |
| `import-preview/<package_id>/source/*.md` | durable, human-readable, read-only build input | preview producer only |
| `import-preview/<package_id>/generated/` | durable Docs Review tree and document payloads | package-local builder only |
| configured Docs Viewer scope source | accepted import output | managed Docs Import only |

The preview `source/*.md` files must never become an alternative import authority. They exist to reuse the Docs Viewer builder and make the projection inspectable.

## Shared Import Drop-Zone

Retire Docs Viewer’s repo-local `var/docs/import-staging/` contract. HTML, Markdown, Markdown packages, text, SVG, images, downloadable files, interactive HTML companions, and supported Data Sharing JSON/JSONL collections should all be listed and resolved from:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/
```

The folder name reflects the existing workspace layout, not exclusive application ownership.

- A user can place an ordinary HTML, Markdown, media, or package source there for Docs Import.
- A user can place a returned JSON/JSONL file there for the appropriate Data Sharing validation/review workflow.
- Docs Import may list any file or direct-child package supported by its format registry.
- Data Sharing should list only files that satisfy its metadata and adapter contracts.
- Supported Data Sharing document JSON/JSONL can later be consumed by both the review workflow and Docs Import, each through its named action.
- Files without an applicable handler remain ordinary drop-zone files; their presence does not assign them to an application.

Do not copy files between a Data Sharing staging root and a Docs Viewer staging root. There is one configured root.

### Reuse The W0 Workspace Adapter

Use the external workspace adapter delivered by W0 of [Docs Viewer Architecture Assessment And Refactor Roadmap](/docs/?scope=studio&doc=site-request-docs-viewer-architecture-refactor-roadmap):

```python
from services.paths import configured_workspace_paths, marker_path

staging_root = configured_workspace_paths(repo_root).import_staging
```

This is the same `data-sharing/services/paths.py` contract already used by Docs Review to resolve `import_preview`.

Docs Import must:

- resolve the root through `configured_workspace_paths(repo_root).import_staging`
- honor the editable marker-rooted path in `data-sharing/config/adapters.json`
- expose `$DOTLINEFORM_PROJECTS_BASE_DIR/...` marker paths through `marker_path()` rather than absolute user paths
- use the W0 workspace status/error contract when the root is missing, invalid, unreadable, or unwritable
- disable only import-related capabilities when the external workspace is unavailable
- preserve filename, direct-child package, traversal, symlink, suffix, and containment checks against the resolved external root
- use isolated temporary project-base roots in tests

Do not add a second environment-variable reader, another staging-root setting, a Docs-specific path adapter, or a fallback to `var/docs/import-staging/`.

### Import Service Changes

The current import implementation derives paths from `STAGING_REL_DIR` and `repo_root`. Replace that assumption with an explicit resolved staging root shared across:

- staged source listing
- primary-source resolution
- Markdown package discovery and containment
- interactive HTML companion discovery
- inline raster output for `staging_manual`
- converted Markdown-package images and copied attachments
- preview/result path projection

External source paths cannot be displayed with repo-relative helpers. API results and activity diagnostics should use marker-rooted paths or artifact-relative filenames.

## Targeted Import Refactoring Boundary

The current importer is already modular enough at the service level. This request does not authorize a general import architecture rewrite.

Retain the existing layers:

- `docs_management_import_service.py` as the thin dependency adapter
- `docs_import_source_service.py` as the single-document workflow orchestrator
- `docs_import_preview.py` as the current format dispatcher and internal conversion/validation contract
- `docs_import_common.py` as the suffix-to-`source_format` metadata registry
- focused Markdown-package, media, interactive-asset, source-formatting, and write/rebuild helpers

Only four targeted changes are required.

### 1. Externalize The Existing Staging Root

Replace `STAGING_REL_DIR` and `repo_root` joins with an explicit W0-resolved staging root. This changes path authority, not format orchestration.

### 2. Add Schema-Aware JSON/JSONL Detection

Keep suffix detection for existing formats. Before generic `.json` or `.jsonl` file-media fallback, inspect supported Data Sharing header and trusted metadata contracts and select a new collection `source_format` when they match.

### 3. Add A Collection Orchestrator

Keep `handle_import_source()` for the existing one-source-to-one-document flow. Add a focused collection workflow for the one-JSONL-to-many-document case. A suitable focused module is `docs_import_data_sharing_documents.py`; exact names can follow current service conventions.

The collection workflow owns:

- the complete package record set
- create, overwrite, or skip decisions
- cross-record identity, parent, link, and media mapping
- batch result and failure reporting

It should call shared lower-level import services rather than invoke the single-document HTTP/service entrypoint once per record.

### 4. Extract Reusable Per-Document Plan And Apply Helpers

Extract only the common document operation currently embedded in `handle_import_source()`:

- collision lookup and action validation
- create/overwrite source formatting
- inline and package media materialization
- target-path writes
- rebuild follow-through
- logging and result shaping

The existing single-document orchestrator should use the extracted helpers too. This proves that ordinary import behavior remains on the same path while allowing the collection orchestrator to plan and apply several records.

### Explicitly Not Required

- no plugin framework or open-ended handler loader
- no conversion of `SourceImporter` into a callable-handler registry
- no wholesale replacement of the `generate_import_preview()` dispatcher
- no requirement to move every format function into a separate module
- no rewrite of existing HTML, Markdown, text, SVG, image, file, or Markdown-package behavior
- no change to existing single-document create/overwrite semantics beyond the staging-root migration

The implementation should prefer the smallest extraction that supports collection plans. Broader cleanup belongs in a separate request with independent evidence.

## Immutable Package Identity

A staged return and its preview folder form one immutable pair identified by export metadata and the timestamped package identity.

- Normal workflow never edits or replaces a staged JSONL file.
- A later return produces a new timestamped staged file and a new preview folder.
- The older pair does not become stale when a newer pair exists.
- Preview source is read-only and therefore cannot diverge through Docs Review edits.
- If the staged file is deleted, its persistent preview may remain viewable but import from that package is unavailable.
- A staged-file hash may be retained for provenance or corruption detection; it is not a lifecycle revision or staleness mechanism.

Do not add refresh polling, source revisions, stale-preview states, or preview/apply drift logic for the staged file.

## Why The Preview Package Remains

Ordinary staged Markdown and HTML are already human-readable outside Docs Viewer, so the current import flow can convert and save them without a separate user-facing content preview.

JSONL is different. It is an efficient multi-document transport but a poor reading surface. Docs Review provides the readable hierarchy, document renderer, media projection, and canonical comparison needed before the user decides whether to import.

That decision may happen much later. Materialize and build the preview once, then serve the persistent package-local generated tree on every later view. Do not parse and rebuild the complete JSONL each time a document is opened.

## Docs Review Changes

Docs Review becomes a read-only package viewer.

Remove:

- source mode and its toolbar control
- source reads and writes
- revision tokens and stale-revision handling
- Markdown save/rebuild behavior
- `review_source_read` and `review_source_write` capabilities
- source-editing endpoints, service methods, browser modules, and tests

Retain:

- validated package listing and selection
- the persistent package-local hierarchy and generated document reads
- rendered document navigation
- inventoried asset rendering
- canonical counterpart links
- package information and validation diagnostics
- initial package build or explicit repair when generated output is absent

Ordinary viewing must read the existing package-local generated output. Building is not part of every view request.

The preview `source/*.md` files should be treated like other generated workspace artifacts: inspectable and reproducible, but not editable through the product.

## Data Sharing JSONL Import Format

Register a schema-aware document-collection format before the current generic `.json`/`.jsonl` downloadable-file fallback. It uses the same resolved drop-zone as every other Docs Import format.

Extension alone is insufficient because Docs Import already accepts JSON and JSONL as ordinary downloadable files. Detection must inspect the package header and trusted metadata, for example:

- `record_type: data_sharing_header`
- supported package `schema_version`
- supported documents profile/import type
- matching trusted `export_id` metadata

If the staged file does not match a supported document-collection schema, retain the existing generic file-import behavior.

The collection importer should support both the compact returned-document format and the full-source format only where their field contracts are explicitly mapped. It must not infer a document package merely from arbitrary row fields.

## Future Standalone JSON/JSONL Collections

Data Sharing is the first collection wrapper, not a permanent prerequisite for collection import.

A future ChatGPT or other external workflow may create a new document collection directly as JSON or JSONL without receiving an exported Data Sharing seed. Docs Viewer should be able to support such a file through a separately declared standalone collection schema, for example `docs_import_collection_v1`.

That future format is not implemented by this request. The current design must nevertheless avoid assumptions that would prevent it:

- the shared normalized record must not require `export_id`, original canonical hashes, a Data Sharing profile, or trusted export metadata
- Data Sharing provenance belongs to the Data Sharing collection adapter, not the core Docs Import record
- a future standalone adapter can validate its own explicit schema and emit the same normalized records
- arbitrary JSON/JSONL must continue to use the generic downloadable-file fallback unless it declares a supported collection schema
- standalone collections use the same external import drop-zone and the same create/overwrite/skip workflow
- the wrapper may contain Markdown, HTML, or plain-text document bodies through an explicit `content_format`

Because JSONL is not convenient to read, a future standalone collection may also use the persistent read-only Docs Review projection. Its preview identity and validation contract would be defined by that collection schema rather than fabricated Data Sharing provenance.

## Collection Adapters And Normalized Import Content

Use wrapper-specific adapters that emit one shared Docs Import content contract.

```text
ordinary .md/.html/.txt reader ───────────────┐
Data Sharing JSON/JSONL adapter ──────────────┼─> ImportContent record(s)
future standalone collection adapter ─────────┘
                                                  -> body-format conversion
                                                  -> persistent review materializer when applicable
                                                  -> configured-scope import planning/apply
```

The generic `ImportContent` record should carry at least:

- source kind and stable source/record identity
- optional adapter-specific provenance
- proposed `doc_id`
- title
- body content when supplied or rehydrated for review
- explicit content intent distinguishing replace, preserve-existing, and empty-new
- `content_format`: `markdown`, `html`, or `plain_text`
- allowed front matter
- `parent_id`
- link and asset information
- source format/profile diagnostics

Body-format conversion then reuses the normal Docs Import paths:

- `markdown` uses the Markdown normalization/validation path
- `html` uses the HTML-to-Markdown conversion path
- `plain_text` uses the text path

These paths need content-based entrypoints beneath their current file-based wrappers so JSON/JSONL adapters can pass unwrapped strings without writing temporary files.

For supplied Data Sharing `canonical_markdown`, parse front matter once and keep it out of the body supplied to standard source formatting. For supplied compact `content`, use the declared profile mapping rather than treating arbitrary JSON fields as source.

Missing returned content is valid when the trusted export association supplies review context for an existing document or when an explicit new structural record supplies the required identity and metadata. For an existing document, apply reads the current configured canonical source and changes only the explicitly returned allowed front-matter fields, such as `parent_id`; it preserves the current body and unrelated front matter. Exported or rehydrated preview content is never written back. New structural documents with omitted content use a standard empty body. The adapter must carry this distinction into collection planning rather than normalizing every row into an unconditional body replacement.

The Data Sharing preview materializer and importer must call the same Data Sharing adapter. Future standalone schemas may use a different wrapper adapter, but all adapters converge on the same `ImportContent` contract and downstream conversion/write behavior.

## Reuse Of Existing Docs Import

Keep one implementation of:

- Markdown validation through the shared renderer
- configured-scope validation
- `doc_id` and filename collision detection
- standard source formatting
- inline raster data-URL detection, planning, retargeting, and materialization
- per-document atomic source writes
- Docs payload and search rebuild follow-through
- activity logging and result summaries

The existing importer handles one primary source at a time. Add a collection orchestration layer that converts normalized JSONL records into the same lower-level document write plans used by ordinary imports.

Useful extractions include:

- a content-based Markdown validation/media-planning function beneath path-based import wrappers
- a standard create-source formatter that accepts mapped parent and allowed metadata
- an overwrite-source formatter with explicit preservation rules
- a batch write/rebuild boundary accepting several planned target paths

Do not invoke the ordinary staged-filename endpoint once per record, copy preview Markdown into repo staging, or make the importer read `import-preview/<package_id>/source/`.

## Import Actions

Every package record has one of these actions:

- `create`: create a new configured-scope document when no identity or filename collision exists
- `overwrite`: replace the existing document that caused the collision
- `skip`: leave the record unimported

A proposed `doc_id` with no collision creates normally. A collision must not silently choose an action and must never offer `Create as new` or replacement-`doc_id` handling in the collection workflow.

Resolve all collision choices sequentially before any writes. Show one collision at a time with `Overwrite`, `Skip`, and `Cancel` buttons plus an unchecked `Apply to all` checkbox.

Clicking `Overwrite` or `Skip` affects only the current collision unless the checkbox is checked. With the checkbox checked, the selected action applies to every remaining unresolved document collision. It does not change earlier decisions, persist to later imports, apply to invalid-record decisions, or authorize media, attachment, or interactive-asset overwrites. `Cancel` always aborts the complete apply with no writes regardless of checkbox state.

After all choices are resolved, show one read-only final plan summary for confirmation. Do not add an editable collision table.

An invalid-front-matter or unsupported-content error may also offer an explicit per-record `Skip` or `Cancel`. This is an error disposition rather than general record selection, and the collision `Apply to all` checkbox does not apply. The user may attach an optional note to the skipped result, and apply must never choose this disposition silently.

Overwrite is a user decision, not a Data Sharing promotion operation. It does not require the preview file to be compared with canonical source or classified as a new revision.

### Create

- validate the final `doc_id` and filename
- map allowed title, summary, visibility, and parent fields
- use normal target-scope date defaults
- create standard Docs Viewer source

### Overwrite

- target only the existing document identified by the collision
- require explicit `Overwrite` confirmation, optionally applied to all remaining collisions through the collision checkbox
- preserve the target `doc_id`, filename, and `added_date`
- refresh `last_updated`
- apply the imported body and explicitly allowed front matter
- validate the imported parent in the target scope
- retain target-only metadata unless the import contract explicitly allows replacement

Follow the ordinary importer’s explicit overwrite model where possible. Do not introduce staged-package revision or stale-source checks that the existing import workflow does not otherwise require.

## Collection Mapping

Resolve the complete package before writing so related records remain coherent. The package already represents the user's exported selection, so the initial workflow imports every package record and does not provide per-record selection. Subset import may be reconsidered after the complete-package workflow has been used in practice.

The import plan should show:

- target scope
- every package record
- create, overwrite, or skip action
- imported identities and matching collision targets
- parent mapping
- media plans and manual-copy requirements
- blockers and warnings

Because the collection workflow does not rename colliding records, imported identities remain stable. Use the planned create/overwrite/skip set to validate parents against the documents that will exist after apply. A skipped parent must produce the documented blocker rather than an implicit identity rewrite.

Links embedded in body content pass through exactly as returned. Docs Import does not rewrite their text or targets, resolve them against the package or target scope, or emit blockers or warnings for unresolved links. Body-link consistency is the user's responsibility. This is separate from structural `parent_id` validation and media/attachment planning.

Resolve every non-empty `parent_id` against either an existing target-scope document or an explicit document record in the package. When no target document exists but the package supplies a valid record with that `doc_id`, create that parent from its supplied source/details during the same apply. This supports new chapters and multi-level grouping nodes without inventing placeholder documents.

If the parent exists in neither location, block the complete plan. Reject hierarchy cycles. A new structural parent is an ordinary package document using the same source validation, allowed front matter, collision handling, and result contract as any other new document; do not add a separate `new_parent_nodes` wrapper or infer a document from an unknown id alone. This absorbs the applicable behavior from [Library Import Generated Parent Nodes Request](/docs/?scope=studio&doc=site-request-library-import-generated-parent-nodes).

Full content is required on export because the external service needs document meaning to propose a useful hierarchy. It is not required on every returned row. A hierarchy-only return may omit content: existing documents receive a surgical allowed-front-matter update against current canonical source, while a supplied new parent is created with an empty body unless it includes content. The plan must state the content intent for each create or overwrite so omission cannot be mistaken for deletion or full-source replacement.

This planning is an import-action summary, not a second content-review surface. Docs Review already supplies the readable content review.

## Invalid Records And Body Warnings

Malformed package/schema data, unsafe or duplicate identities, missing parents, and hierarchy cycles block the complete plan because Docs Import cannot safely identify targets or construct a valid tree.

Invalid front matter and unsupported supplied content formats are record-level decision errors. Show them before apply and require the user to `Skip` that record or press `Cancel`. An optional user note is stored with the skipped record's result/activity entry. The collision `Apply to all` checkbox is unavailable for these decisions, and no invalid record is skipped implicitly.

Other non-structural body findings pass through without content transformation. Preserve any diagnostics already produced by normal parsing/rendering as non-blocking warnings and show them in the final batch result; do not add broad body-consistency validation. Internal body links follow the stricter O3 rule and are not resolved or warned about. Media and attachment failures follow the asset-level pass-through policy below.

## Batch Mutation And Generation Failure

The collection apply is not a batch transaction. Reuse the ordinary importer's per-document atomic write, but do not stage a collection rollback. If a later operation fails, completed canonical-source mutations remain and the result identifies applied, failed, and not-attempted records. Write ordering and stop/continue behavior are decided separately.

Docs Import invokes the normal Docs/search generation follow-through after source mutation. A generation failure does not roll back or reclassify successful source imports. Report it as a separate generation outcome and leave diagnosis, retry, and repair to the same generation workflow used after ordinary document creation.

Write records strictly in package JSONL order. Validate the complete hierarchy before apply, but do not reorder rows to place parents first or group operations by action. Each record reuses ordinary per-document source/media apply behavior rather than introducing a batch-specific media ordering model.

If an individual source write fails, stop at that record, preserve earlier writes under the no-rollback contract, and report later rows as not attempted. A skipped or failed asset operation is non-blocking and does not count as a source-write failure.

After the write phase, call the existing managed write/rebuild owner once with all affected paths and ids. It runs targeted Docs and search generation for the batch and suppresses the live watcher from performing duplicate managed-write rebuilds. A safe targeted-to-full fallback is normal rebuild behavior and should complete. An actual generation command failure stops generation and is reported under the separate O5 outcome; import adds no retry or recovery and does not rely on the watcher, although the watcher may later react independently after suppression is cleared.

## Images And Other Assets

Inline raster data URLs inside returned Markdown should use the existing Docs Import path:

1. parse the package JSONL record
2. detect supported PNG, JPEG, WebP, or GIF data URLs
3. plan target-scope media references
4. derive filenames from the stable record/target `doc_id`
5. decode and materialize through the shared media service during import

Current scopes use `staging_manual`, so results must continue to report the required media-store copy step.

Package binary files that are not embedded data URLs still require an explicit supported mapping. Validation of a preview asset proves safe package containment; it does not by itself authorize copying that file into a configured media store.

Media and attachment handling is asset-level best effort. If an otherwise trusted asset is unsupported, missing, colliding without existing per-asset authorization, or fails materialization, skip only that asset operation. Import the document, preserve its returned body token/reference unchanged when materialization cannot complete, continue the batch, and report a final warning plus any existing manual-copy instruction. The user is responsible for repairing unresolved references after import.

Applying document `Overwrite` to all remaining collisions never grants asset overwrite authority. This non-blocking policy also does not weaken package validation, containment, symlink, size, or execution-safety rules; unsafe package/file access remains rejected rather than attempted.

## Operation Size, Progress, And Cancellation

Keep collection import synchronous. Do not add progress reporting, background jobs, polling, or a separate result-retrieval flow. `Cancel` is available during collision/error decisions and final confirmation only. Once apply begins, it cannot be cancelled and runs until completion or failure under the documented write, asset, and generation contracts.

Retain existing intake, request, file, decoded-data, and security limits. Do not add speculative collection-specific record, package-size, or planned-write limits. If practical use exposes scale or timeout pressure, address progress and long-running operation support later as an app-wide or system-wide capability.

## UI And Authority

Docs Review may expose an `Import` handoff for the selected immutable package. That handoff passes a safe package/staged-file identity to managed `/docs/`.

Managed Docs Import owns:

- target scope selection
- complete-package planning
- create/overwrite/skip choices
- collision and mapping summary
- confirmation
- configured source and media writes
- rebuild and result reporting

Docs Review retains no configured-source mutation authority. Data Sharing retains no general Docs Viewer source-creation or overwrite authority.

## Management API Shape

Reuse `GET /docs/import-source-files` to list the reviewed collection as a safe staged-file record. Reuse `POST /docs/import-source` for both phases: `preview_only: true` returns the server-calculated collection plan; `preview_only: false` plus explicit per-record collision/error decisions performs synchronous apply and returns the final result.

Docs Review may pass a safe `package_id` only to preselect the matching server-listed record. Management requests use the safe `staged_filename` returned by the import listing, never a package path or preview-source path. `Apply to all` is expanded in the frontend into explicit decisions for remaining collisions.

The browser submits scope, safe staged identity, explicit actions, optional invalid-record notes, and ordinary activity context. It does not submit target paths, generated source, hierarchy/media plans, or an authoritative write plan. Apply rereads the immutable package and recomputes/revalidates current target state.

Do not add collection-specific routes, stored plans, plan ids/tokens, jobs, polling, or result retrieval. Any target drift requiring reconfirmation returns a refreshed plan without writes through the same POST contract.

## Apply Revalidation And Target Drift

Apply always rereads the immutable staged package and recomputes the current target plan. Do not capture source revision/body hashes, store a server plan, or add stale-revision handling.

Proceed without another confirmation when the submitted decisions still identify the same collision targets and the recomputed plan has the same target identities, parent resolutions, and blocker state. Current body or unrelated metadata changes do not force reconfirmation for preserve-existing rows; apply reads current canonical source and changes only the explicitly returned allowed front matter.

Return the refreshed plan with no writes when:

- a planned create now collides
- an overwrite/skip collision target changed or disappeared
- parent resolution or hierarchy validity changed
- a record gained or lost a blocking condition that changes the confirmed plan

Any new collision returns through the same sequential `Overwrite`/`Skip`/`Cancel` flow. This is immediate target-state revalidation, not revision management.

## Result Report And Activity

After a confirmed apply begins, return the synchronous result and write one Markdown report under:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/results/<timestamp>-<package-stem>-import-result.md
```

The `results/` child directory keeps the report visible in the user workspace without allowing direct-child staging discovery to list it as another Markdown import source.

Group documents under `Created`, `Overwritten`, `Skipped`, `Failed`, and `Not attempted`, omitting empty sections and preserving package order within each group. Include package identity, target scope, timestamp, overall source-mutation outcome, optional invalid-record notes, a separate generation outcome, warnings, and manual-copy instructions.

Write the report for completed, partially written, and generation-failed applies, but not for planning, rejected plans, or pre-write cancellation. Report-write failure is a non-blocking warning and never changes source/import outcomes.

Add the reusable cross-app helper `studio/shared/python/json_markdown_report.py` with:

```python
render_json_markdown_report(payload, *, title, section_order=None) -> str
write_json_markdown_report(path, payload, *, title, section_order=None) -> Path
```

It accepts JSON-compatible data, renders deterministic escaped headings/lists, preserves supplied order unless an explicit section order is provided, and writes atomically. It owns no output location, app semantics, marker paths, templates, plugins, or report registry. Callers validate and supply the destination path, which keeps the helper simple while leaving a reusable extension boundary.

Docs Import shapes the grouped result JSON, resolves the existing workspace staging `results/` path, calls the shared writer, and uses the existing marker-path and activity infrastructure. The apply response exposes the marker-rooted report path, and activity records carry that safe path plus grouped counts. Neither surface includes source bodies, full requests, or user-specific absolute paths.

## Security

- Resolve staged identities through Data Sharing’s safe staging and trusted metadata contracts.
- Never accept arbitrary filesystem paths from the browser.
- Require the staged file to match the preview package’s recorded export/package identity.
- Revalidate the JSONL schema, record shape, target scope, front matter, hierarchy, media plans, and collisions at import time.
- Enforce existing record, file, batch, and decoded-data limits; do not invent collection-specific thresholds in this request.
- Reject symlink and containment escapes.
- Do not execute returned scripts or grant package HTML same-origin authority.
- Do not treat persistent preview Markdown as trusted import input.
- Keep result reports below `import-staging/results/` and out of direct-child import-source discovery.

## Implementation Tracking

Prerequisite batch decisions, owner contracts, and targeted enabling refactors are tracked in [Docs Import Reviewed Package Preparation And Refactor](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-preparation-refactor).

Execution tasks and verification evidence are tracked separately in [Docs Import Reviewed Package Implementation](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-implementation).

This parent document remains the authority for product decisions, architecture boundaries, acceptance criteria, and non-goals. The preparation request may propose and resolve open decisions, but approved outcomes must be copied here. The implementation child may track progress but must not redefine these contracts.

## Acceptance Criteria

- a timestamped staged JSONL file produces one persistent, read-only Docs Review package
- every Docs Import format uses the configured `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/` drop-zone
- Docs Import resolves that root through the existing W0 workspace adapter
- no production import path falls back to repo-local `var/docs/import-staging/`
- repeated review reads use package-local generated output rather than reparsing the JSONL
- Docs Review cannot read or write editable source bodies
- a newer staged return creates a separate preview package and does not stale the older pair
- Docs Import recognizes supported Data Sharing JSONL as a document collection
- the importer reads the staged JSONL, never preview `source/*.md`
- non-colliding records can create, while collisions can only be explicitly overwritten or skipped
- supported hierarchy and embedded raster images are mapped through shared import services, while body links pass through unchanged
- configured source writes and rebuilds remain owned by managed Docs Import
- confirmed applies write a grouped Markdown result report under `import-staging/results/`, expose its marker-rooted path, and do not list it as another import source

## Non-Goals

- editing the persistent preview projection
- importing from preview Markdown
- reparsing the complete JSONL on every Docs Review navigation
- staged-file staleness or revision management
- implementing the future standalone document-collection schema
- automatic overwrite based only on matching `doc_id`
- replacement-ID or `Create as new` handling for collection collisions
- diff, merge, delete, or promotion semantics
- moving staged Data Sharing JSONL into repo-local Docs Import staging
- introducing a second Docs-specific staging root or external-workspace resolver
- automatic remote media upload
- executing returned content

## Related References

- [Docs Import Reviewed Package Preparation And Refactor](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-preparation-refactor)
- [Library Import Generated Parent Nodes Request](/docs/?scope=studio&doc=site-request-library-import-generated-parent-nodes)
- [Docs Import Reviewed Package Implementation](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-implementation)
- [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)
- [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import)
- [Media Handling](/docs/?scope=studio&doc=docs-viewer-media-handling)
- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review)
- [Docs Review Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-review)
- [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package)

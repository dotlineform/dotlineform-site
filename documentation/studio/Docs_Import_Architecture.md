---
draft: false
doc_id: d-20260514-164722-3de65e
title: Docs Import Architecture
added_date: "2026-05-14 16:47:22"
last_updated: "2026-10-20"
summary: Configuration, registries, source confinement, execution paths, extension methods, and weak spots for Docs Viewer imports.
parent_id: d-20260424-000000-50b63f

---
# Docs Import Architecture

Docs Viewer Collections reports have two management intake workflows: Import doc receives one browser-selected ordinary file, while Import docs reads selected sources and complete packages beneath the configured Projects base's `data-sharing` directory. Both require the menu's exact collection, independently of checked rows and displayed document state, and normalize ordinary sources through the same converters and document planning, media, source persistence and targeted generation owners. Empty collections support both intake actions; Catalogue retains its Studio/Regenerate ownership.

This document owns the stable architecture and extension method. [Docs Import](Docs_Import.md) owns the operator workflow. [HTML Import Mapping](HTML_Import_Mapping.md) owns the intended semantic-HTML conversion rules, and [Word Import Style Mapping](Word_Import_Style_Mapping.md) owns Word-style semantics. Exact fields, endpoint payloads, and tests remain code-owned.

## Execution Paths

```text
data-sharing source directory
    (default: data-sharing/import-staging)
          |
          v
server listing + source classification
          |
          +---------------- document source or Markdown package
          |                              |
          |                              v
          |                    preview / conversion / validation
          |                              |
          |                              v
          |                       ImportContent(replace)
          |                              |
          |                              v
          |                    plan one document -> media -> source write
          |                                              |
          |                                              v
          |                                        rebuild + result
          |
          +---------------- trusted collection
                                         |
                  +----------------------+----------------------+
                  |                                             |
          returned JSON/JSONL                         edited review folder
                  |                                             |
        package intake -> ImportContent              provenance -> ImportContent
                  |                                             |
                  +----------------------+----------------------+
                                         |
                              write-free complete collection plan
                                         |
                              whole-collection confirmation
                                         |
                                         v
                               reread and recompute server plan
                                         |
                           +-------------+-------------+
                           |                           |
                     ordered apply              atomic apply
                           |                           |
                           +-------------+-------------+
                                         |
                                 one rebuild -> result
```

Import docs consumes a body-free server candidate projection, retains one accepted Projects-relative marker within `data-sharing`, freezes the invoking collection for ordinary sources and confirms complete collection plans. Trusted collection candidates carry their server-resolved manifest target. The browser disables mismatched package/folder candidates using those supplied identities; existing server provenance owners enforce the same destination during planning/apply. The browser does not receive a physical source path; confinement, package classification, conversion, hierarchy/media plans and write authority remain with their server owners.

Import doc invokes `<input type="file">` synchronously from its action, with one pending File and a frozen destination owned by `docs-viewer-import-doc-workflow.js`. Confirmation sends one `POST /docs/import-doc` multipart request containing UTF-8 metadata and an opaque document part. The HTTP reader bounds the request before `docs_import_doc.py` parses the exact two-field envelope, accepted ordinary suffix and safe filename. It reuses the existing 64 MiB native file, 1 MiB metadata and 1 MiB overhead limits. The completed response carries only `ok`, exact `target`, committed `record` and converter `warnings`; converted bodies, media plans, temporary paths and staged-source fields are not returned. The frontend owns filename/type/size feedback and Cancel; the server owns the untrusted upload boundary and actual conversion.

Native confirmation shows only the filename and complete-folder guidance. HTML supplies `include_prompt_meta: true` without an option; existing Import retains its checked-by-default checkbox. Management busy state starts at submission, remains through committed/display completion and clears on request failure before the modal permits retry. The shared modal still owns submission controls and Cancel blocking; an idle confirmation has no waiting cursor.

Both intake endpoints require a configured collection at the request boundary. Native metadata accepts required `filename` and `collection`, plus optional `include_prompt_meta`; ordinary Index sibling placement and `after_doc_id` are removed. Collection menu callbacks reach the existing native picker synchronously, preserving browser user activation without a dynamic-import or request before selection. The workspace buttons, event-router import commands, displayed-context destination inference, unused parent-refresh helper and `?import=1` startup path are retired without aliases.

The native owner writes one request-local temporary converter input, then calls `import_ordinary_source` with that source root and companion discovery explicitly disabled. It does not use Data Sharing configuration, package recognition, a source listing, persistent staging or an OS picker. Reviewed Markdown and role-marked interactive companions are directed to existing Import. Both intake paths share `generate_import_preview`, `plan_import_document`, media materialisation and source writes. The plan retains its prepared SourceDoc; apply returns completed ordinary parentage, and the existing `rebuild_prepared_document_outputs` owner consumes both alongside the resolved destination. Final document generation avoids the former wrapper's target-source reread, ID rediscovery, workspace reload and subprocess build. Collection/package orchestration retains its separate flow. Ordinary create allocation carries one new identity before conversion without reading every target document; exact destination collision checks and the exclusive new-source writer retain their authority. Prepared SVG/raster bytes pass directly into media materialisation. Temporary converter input is removed only after awaited completion and is not an alternative Docs/Projects workspace.

## Import Media Preparation

The browser owns source selection, the destination and normal confirmation state. Python owns format conversion, SVG sanitization or raster decoding, exact configured media paths, writes and generation. One `ImportMediaPreparation` carries the resolved document-media owner, final document identity and prepared inline bytes through each conversion. Ordinary creation allocates its ID before conversion; collection planning supplies its already resolved create/overwrite ID. The standalone preview CLI resolves one media owner and lets conversion derive its preview identity from the source.

Converters construct media filenames, document-owned artifact identities and Markdown tokens once using that supplied owner and identity. Generated import filenames use `image-NN.<ext>` or `attachment-NN.<ext>` beneath the resolved document-ID folder, without repeating that ID in the basename. Existing saved filenames remain valid literal identities. Markdown-package image labels retain their source-derived wording independently of storage identity. Package filename collision checks use the exact configured document folder from the same preparation object; they do not derive a second destination identity from the preview summary. Media planners perform no workspace reloads, and document planning does not rebuild media plans or rewrite their tokens.

Each inline raster data URL is decoded once and each HTML-inline SVG is sanitized once per operation. Prepared immutable bytes are held separately from JSON preview metadata, keyed by media family and filename, and passed through the internal document plan to materialisation. The original HTML and base64 Markdown are no longer retained for re-extraction. Materialisation consumes those exact bytes without another source read, decode, SVG parse, positional count audit or fallback conversion. The preparation object remains in memory until its operation completes; there is no saved cache or cross-request handoff. A separate confirmed request still performs its own conversion.

The import helper performs the ampersand and XLink namespace conversion described in [Media And Asset Handling](Media_And_Asset_Handling.md#import-materialization) before the strict shared sanitizer, which remains the authoring owner for XML validity and SVG safety. Existing selected source/package confinement, document collision authority and media-write/transfer verification remain with their filesystem and storage owners. They prevent unsafe paths, unintended replacement and incomplete selected writes; this refactor adds no recovery, freshness checks or corpus inventory. Obsolete retargeting, media-link helper aliases and raw-source fallback interfaces have been removed without compatibility aliases.

## Configuration And Registries

### Source Directory And Staging Gate

`source_directory` is the canonical POSIX marker for one real directory beneath `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing`. Existing Import uses `lower_root="data-sharing"` for navigation and source resolution, with the browser picker rooted at the same marker. `studio/shared/python/projects_directories.py` validates requested path segments without following symlinks, confirms containment and lists safe direct-child directories. `data-sharing` is navigable/selectable with no parent; `.` and outside-root markers are unavailable to Import. Responses and diagnostics use relative markers.

Import staging remains the default:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/
```

This is a shared user drop-zone. Ordinary sources and Markdown packages may be selected from another accepted directory inside `data-sharing`. Candidate inventory and every preview/apply request bind the same `{source_directory, staged_filename}` pair, and the service resolves the exact direct child at its filesystem boundary. Native Import doc supplies bytes independently of this directory authority.

Trusted returned packages and edited review-source folders remain staging-only. A registered recognizer sees the untouched direct child first; outside staging, a recognized trusted source is projected as blocked and cannot fall through to ordinary handling. A remembered outside-root marker is cleared in the browser before opening staging; existing validation/fallback handles unavailable remembered directories inside the root. The source marker never supplies destination authority.

### Source Classification

Classification is code-owned and deliberately closed:

- `SOURCE_FORMAT_BY_SUFFIX` in `docs-viewer/services/docs_import_common.py` maps Word `.docx`, HTML, Markdown, and text suffixes to a document `source_format`.
- A direct-child directory is classified separately as `markdown_package` after package validation.
- Supported trusted document-package JSON/JSONL is classified under the retained serialized source-format id `data_sharing_documents` from trusted export metadata. Unregistered JSON/JSONL is not a Docs Import source.
- A complete edited Docs Review source folder is classified as `edited_review_sources` by strict provenance, retained-manifest, and trusted metadata validation before Markdown-package classification.
- `generate_import_preview()` in `docs_import_preview.py` performs explicit format dispatch.

Existing Import receives the resulting `source_format`; it does not recreate package classification. Native Import doc uses ordinary suffixes for picker/feedback, while its upload boundary accepts only the ordinary document allowlist. Registered collection recognizers retain existing Import and receive untouched candidates before generic Markdown front-matter stripping. This registry is an allowlist, not a plugin loader.

### Target Collection And Media Policy

`docs-viewer/config/workspace/docs-workspace.json` defines one workspace and its configured one-level sub-scopes. Import requires explicit `stage: working` and optional `sub_scope`; the shared managed-target resolver rejects retired scope fields, nested or unconfigured children, and returns the confined source root used throughout the run. Import media services derive the exact stage/child media owner through the common artifact-location adapter. Public projections are not import targets.

Configured sub-scopes retain their configured document and media ownership. Every materialisation resolves the exact stage/child media owner. Source-format registration does not decide where media is stored.

Trusted exports use `data_sharing_export_meta_v2`, with `stage: working`, optional `sub_scope`, capabilities, selected immutable IDs and prepared source versions. Import resolves that exact collection and compares complete membership before planning writes; an ordinary collection is an explicit empty child identity, not permission to import from another child. Scope-bearing old metadata, package envelopes and edited Review source folders are rejected with a re-export request. Recognizers retain old Review markers only to reject them before ordinary Markdown handling. No old package is upgraded or applied during the scope cutover.

Trusted collection Import is a separate, fail-closed policy. A
sub-scope omitting `supports_return_import` is not eligible. An explicit `true`
only makes a returned package or edited review-source folder import-capable
when its package profile also supports Docs Review and return Import.
Analysis/Tags is the first opted-in collection.

## The Core Contracts

| contract | owner | purpose |
| --- | --- | --- |
| confined Projects directory navigation | `studio/shared/python/projects_directories.py` | Validate canonical relative markers and list safe direct-child directories without import policy. |
| document-source allowlist and format mapping | `docs_import_common.py` | Classify ordinary document sources. |
| native document request and intake | `docs_import_doc.py` | Bound one ordinary upload and supply request-local converter input without directory/package discovery. |
| shared ordinary conversion and completion | `docs_import_source_service.py` | Carry the selected input, conversion, media and create plan through existing source/write/generation owners. |
| exact source inventory and dispatch | `docs_import_source_service.py` | Resolve the selected directory/direct-child pair, run recognizers first, and keep trusted sources staging-only. |
| conversion and preview validation | `docs_import_preview.py` | Produce Markdown and media intent without a source write. |
| body-free candidate projection | `docs_import_candidate_projection.py` | Project candidate kind, action state, exact target mode, safe diagnostics, and display label after recognizer-first classification. |
| exact collection adoption | `docs_management_document_target.py`, `docs_management_import_service.py` | Resolve one configured parent or child source root without fallback. |
| Word semantic-HTML adapter | `docs_import_docx.py` | Apply the repository Mammoth style/image policy without gaining write authority. |
| trusted documents-package intake | `docs_import_document_package.py`, `docs_import_document_package_content.py` | Verify wrapper provenance and emit wrapper-neutral records. |
| edited review-source intake | `docs_import_review_source_folder.py`, `docs_import_review_source_collection.py` | Validate a complete reviewed folder and emit overwrite-only normalized records. |
| wrapper-neutral document intent | `docs_import_content.py` | Represent one document independently of its trusted transport wrapper. |
| per-document plan and apply | `docs_import_document.py` | Validate a create/overwrite and perform its media/source mutation. |
| write-free collection plan | `docs_import_collection_plan.py` | Resolve all records, collisions, parents, warnings, and blockers. |
| whole-package confirmation, ordered apply, and result | `docs_import_collection_apply.py`, `docs_import_collection_result.py` | Revalidate the server-issued package plan, mutate, rebuild, and return the grouped result. |
| HTTP-facing request adoption | `docs_management_import_service.py` | Require the explicit source identity and exact managed destination before service dispatch. |
| app Import lifecycle and exact result refresh | `docs-viewer-management-import-controller.js`, `docs-viewer-import-doc-workflow.js`, `docs-viewer-management.js` | Own each intake action, frozen ordinary context, shared committed-record adoption and exact result display. |
| shared folder navigation | `shared/frontend/js/folder-picker.js` | Render app-neutral lazy breadcrumb, parent, direct-child, keyboard, and selectable-marker behavior through injected load/submit callbacks. |
| Docs Import source preference and fallback | `docs-viewer/runtime/js/import/docs-import-source-selection.js` | Revalidate the local marker, clear invalid state before staging fallback, and refresh exact candidates without owning destination. |
| browser candidate, Review, confirmation, and result UI | `docs-viewer/runtime/js/import/` | Validate the candidate projection, dispatch existing ordinary/collection owners, hand off one reviewable row, and present explicit destination links. |

These are navigation pointers, not a promise that every helper will remain in the same file.

## Normalized Document Intent

`ImportContent` is the seam between source-specific adapters and document planning. It carries source identity, title, allowed front matter, hierarchy, diagnostics, and one explicit content intent:

- `replace`: convert supplied Markdown, HTML, or plain text and use it as the target body
- `preserve-existing`: update allowed metadata or hierarchy while retaining the current body
- `empty-new`: create a structural document with no fabricated body

Ordinary document-source imports produce one `replace` content record for a newly allocated document after preview. Collection adapters may produce any of the three intents and may target existing documents explicitly. This prevents collection planning from inventing replacement content for hierarchy-only records and lets future trusted wrappers reuse document planning without reusing Data Sharing provenance.

Trusted collection adapters may supply permitted `title`, `parent_id`,
`summary`, and `publishable` intent when the exact destination supports Publish. The edited review-source adapter is
overwrite-only and maps body, title, and summary; parent and publishability are
eligible only where the destination contract permits them. Local destinations reject publication metadata. Configured child hierarchy, group,
status, and publication state remain destination-owned. For an unclaimed ordinary
Markdown source, a well-formed leading front-matter block is removed after
registered collection recognition; only scalar `title` can act as a fallback
and all other fields are ignored with diagnostics. Canonical formatting, local
identity, timestamps, target paths, collision targets, and default publishability
remain service-owned.

The body-free candidate listing is context-independent. Returned packages and
edited review-source folders are recognized from untouched staged candidates
and retain one exact resolved `{ stage: working }` or `{ stage: working, sub_scope }` target.
Ordinary rows declare display-context routing without carrying a target.
Missing legacy capabilities, invalid `false` / `true`, mismatched collections,
retired physical names, and unsafe provenance fail closed.

## Ordinary Source Path

An ordinary source follows one-document orchestration:

1. Resolve and classify one exact `{source_directory, staged_filename}` direct child, then adopt one validated Working target with optional `sub_scope`.
2. Allocate a fresh immutable local identity without loading or parsing the ordinary target collection, and carry the resolved destination into conversion.
3. Convert to Markdown, prepare inline media bytes and final media plans, and validate the Markdown through the shared Python renderer.
4. Plan any role-marked interactive companions; retain their existing replacement confirmation and exact write checks.
5. Convert the accepted preview to `ImportContent`, plan the new document, materialize media, atomically create source, and invoke the owning parent or confined child rebuild boundary.

The format converter never writes source or performs a rebuild. The Word adapter passes Mammoth's semantic HTML unchanged into the shared HTML converter; temporary HTML and base64 image bodies remain server-side while the public preview contains canonical Markdown and safe media-plan metadata. Interactive-companion replacement confirmation and endpoint authorization stay outside the converter.

Immediately before a replacement body is written, the per-document owner applies the shared Markdown blank-line rule: a line containing only Unicode whitespace becomes empty outside fenced code and explicit `<pre>` blocks. This contains hidden no-break spaces from exported notes without trimming prose, Markdown hard-break spaces, or literal examples.

For a sub-scope display, the report publishes the mounted collection to the
manage host; it does not own an Import control or workflow. The app-level
modal freezes that collection only for ordinary candidates and sends
`sub_scope` on every attempt. Trusted candidates ignore display context and
retain their manifest target. A successful response supplies a prevalidated
`viewer_url` and exact target. If that same child collection is mounted, the
host invokes its document- or collection-refresh callback; otherwise it leaves
the current route fixed and presents the result link. Public reports, checked
IDs, URL text, displayed documents, and the selected parent are not
destination sources.

## Collection Path

A collection source first passes its trusted wrapper owner: returned JSON/JSONL
uses document-package intake, while an edited review-source folder validates
the complete retained package and trusted sidecar contract. The generic
collection planner then processes every normalized record without exposing
bodies or generated source to the browser.

The plan resolves:

- create or collision state
- stable planned local identities for creates, including package-parent remapping
- server-planned create/overwrite actions
- record errors that block the whole package
- existing and package-supplied parent chains
- hierarchy blockers and cycles
- safe media summaries and unmapped asset warnings

Confirmed apply rereads the selected collection, recomputes the plan using the
server-issued receipts, and checks package or folder identity and planned
actions against current state. The grouped result is returned directly; apply
does not create a separate result document or result-specific log.

Returned-package apply is synchronous batch orchestration, not a transaction or
job system. Earlier writes survive a later source-write failure; later records
become not attempted. R2 publication failure blocks that record's source write
so a new media token is not committed without its media. Generation failure
remains separate from successful canonical mutations.

Edited review-source apply selects the other shared apply mode: overwrite-only
plans are completely prepared, exact canonical source snapshots are rechecked
inside one parent or child mutation boundary, and a write or rebuild failure
restores the complete selected source set and its projection. This atomicity is
a wrapper policy supplied through the common apply owner, not a generic promise
for all collection formats.

## Extension Methods

### Add An Ordinary Document Format

1. Add a code-owned allowlist entry and stable `source_format`.
2. Add a preview builder that returns normalized Markdown, warnings, validation, and optional media plans.
3. Dispatch it from `generate_import_preview()`.
4. Reuse `ImportContent`, fresh identity allocation, per-document create, writes, and rebuilds.
5. Add focused listing, preview, repeated-create, media, and service tests.

Do not add standalone media here. Image and opaque-download intake belongs to the source editor's staged-media service. Do not add a document format by extending only the browser suffix list or by giving a converter direct write access.

### Add A Collection Wrapper

1. Require an explicit, trusted, versioned wrapper contract.
2. Classify it through trusted package registration before ordinary document dispatch.
3. Normalize each record to `ImportContent` with explicit content intent.
4. Reuse the generic collection planner, whole-package confirmation, per-document apply, rebuild, and result contracts.
5. Add wrapper-specific UI only when its package confirmation genuinely differs.

A collection adapter should own provenance and schema interpretation. It should not fork document mutation rules.

### Add Or Change A Published Media Location

Register the media type's provider, confined path, served prefix, and required capabilities, then extend the focused location adapter only if the provider itself is new. Do not add publication policy to the document source mapping or a format converter.

## Why This Structure Exists

- A closed server registry makes accepted local files inspectable and testable.
- Wrapper-neutral `ImportContent` separates provenance from canonical mutation.
- Write-free planning makes collisions, hierarchy, and unsafe input visible before collection mutation.
- Replanning on confirmation prevents the browser from applying a stale plan.
- Shared per-document apply keeps ordinary and collection imports on the same source-formatting and mutation boundary.
- Media publication before source write prevents new R2 tokens from pointing at unpublished record-owned media.
- Revalidating the exact source pair on every request prevents a remembered or displayed marker from becoming filesystem authority.

## Weak Spots

- “Registry” is only partly accurate: `SOURCE_FORMAT_BY_SUFFIX` covers ordinary document suffixes, while Markdown packages and trusted collections have separate classification paths.
- Format metadata and preview dispatch are separate code structures, so a new ordinary format requires coordinated edits rather than one self-contained registration.
- The single-source and collection workflows share one endpoint and modal but have different orchestration and failure semantics.
- Returned-package apply is synchronous and partially durable; large packages
  have no progress, resume, rollback, or background job. Edited review-source
  folders have atomic source/rebuild rollback but still no job controls.
- Role-marked interactive companions are discovered across the selected source directory during an ordinary import rather than explicitly associated with one selected document.
- Embedded-media publication spans workspace configuration, artifact-location adapters, the shared SVG sanitizer, and focused media services. Looking only at the document source mapping gives an incomplete picture of import behavior.
- Returned Data Sharing packages and edited Docs Review source folders now
  prove two wrapper policies through the shared normalized planning/apply seam.

[Media Handling](Media_And_Asset_Handling.md) owns storage paths and materialization rules. [Docs Management Endpoints](Endpoint_Overview.md) owns the HTTP surface rather than this architecture summary.

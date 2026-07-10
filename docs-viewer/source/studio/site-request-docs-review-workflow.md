---
doc_id: site-request-docs-review-workflow
title: Docs Review Workflow
added_date: 2026-07-10
last_updated: 2026-07-10
parent_id: change-requests
viewable: true
---
# Docs Review Workflow

## Status

Approved approach; not yet implemented.

This request replaces the retired `Docs Review Local App` proposal. Docs Review will be a local review route of the existing Docs Viewer application, not a copied or independently evolving viewer application.

## Outcome

Provide a controlled workflow for externally revised Docs Viewer documents:

1. Export canonical documents through Data Sharing.
2. Edit and reorganize the returned content with an external service such as ChatGPT.
3. Stage the returned package.
4. Create a temporary review source folder from the complete staged package.
5. Open the folder in `/docs-review/`.
6. Build and inspect the temporary rendered documents.
7. Manually edit temporary Markdown or `parent_id` values where needed.
8. Rebuild the review folder.
9. Open canonical counterparts in `/docs/` in another tab when comparison is useful.
10. Validate and promote the reviewed folder into canonical Docs Viewer source.
11. Rebuild canonical Docs Viewer outputs.

The first promotion implementation updates existing canonical documents. Creating new chapter or parent documents is a required version 2 capability.

## Decision

Use the existing Docs Viewer application with a distinct local review route and app context:

- route: `/docs-review/`
- app context: `review`
- same local Docs Viewer service process
- shared Docs Viewer boot, shell primitives, tree, router, panel layout, document renderer, source-editor primitives, and CSS
- a thin review entrypoint/composition layer for review-only capabilities
- a review-folder data provider rather than a configured Docs Viewer scope
- focused review-folder and promotion backend services

Do not create a top-level `docs-viewer-review/` application or copy existing Docs Viewer runtime modules into a second frontend.

The distinct route remains important. It makes temporary review state visible, keeps review URL state separate from configured scope navigation, and prevents the normal `/docs/` management UI from acquiring review-folder conditionals.

## Benefits And Risks

Benefits:

- tree navigation, rendering, source editing, routing, and later viewer improvements remain shared
- review functionality can grow without recreating Docs Viewer features
- temporary writes and canonical writes have distinct capabilities and endpoints
- the public viewer remains isolated from local review assets and services
- promotion can reuse established Docs source formatting, validation, activity, and rebuild boundaries

Risks:

- the current runtime assumes a binary public/manage context and configured scope data
- local generated reads are currently coupled to management access
- search, recently added, bookmarks, and scope selection currently participate in shared startup
- review promotion changes canonical content and hierarchy in a batch, so server-side validation must be complete before writes begin
- version 1 cannot complete a returned hierarchy that depends on newly invented chapter nodes

The implementation should address these as explicit provider, capability, and validation seams. It should not add scattered `review` conditionals to the private app runtime.

## Route And URL Contract

Review URLs use folder identity, not scope identity:

```text
/docs-review/?folder=<folder_id>&doc=<doc_id>
/docs-review/?folder=<folder_id>&doc=<doc_id>&view=source
```

Rules:

- `folder` selects one temporary review folder.
- `doc` selects one document within the folder.
- `view=source` selects temporary Markdown source editing.
- absence of `view` selects the rendered document.
- review URLs must not use a synthetic configured scope such as `scope=library-review`.
- browser history and internal review links must preserve `folder`.
- the current folder id must not be held only in ephemeral JavaScript state.
- links to canonical counterparts use `/docs/?scope=<source_scope>&doc=<doc_id>` and may open in another tab.

The implementation may use a thin review shell or a shared local shell. Shell markup must remain limited to route identity, mounts, boot, and asset loading; it must not duplicate viewer behavior.

## App Context And Capability Model

Docs Viewer should support three explicit app contexts:

| context | route family | data authority | writes |
| --- | --- | --- | --- |
| `public` | `/library/`, `/analysis/`, and other public routes | public generated assets | none |
| `manage` | `/docs/` | configured scopes and management service | canonical management actions |
| `review` | `/docs-review/` | selected temporary review folder | temporary edit/build plus controlled promotion |

Route identity and visible controls do not grant backend authority. The backend capability response remains the source of truth.

Initial review capabilities:

- `review_folders_list`
- `review_generated_read`
- `review_source_read`
- `review_source_write`
- `review_build`
- `review_promotion_preview`
- `review_promotion_apply`

Review must not receive general capabilities for:

- arbitrary canonical source editing
- canonical delete
- scope creation or deletion
- hierarchy drag/drop against canonical source
- publish
- source settings
- HTML or package import
- public-site writes

Promotion is a named, validated capability. It is not general canonical write access.

## Shared Runtime And Data Provider

Add a data-provider seam to the existing Docs Viewer app composition. The provider supplies the selected collection's generated and source behavior without requiring the collection to be a configured scope.

The provider contract should support named methods equivalent to:

```text
readIndex()
readDocument(docId)
readSource(docId)             optional
writeSource(docId, revision, body) optional
build()                       optional
listCollections()             optional
selectCollection(id)          optional
```

The configured-scope provider retains current `/docs/` behavior. The review-folder provider adapts review-folder endpoints and wrapper payloads to the same viewer-facing contracts.

Feature-facing generated reads must continue through `docs-viewer-generated-data-runtime.js` or a provider boundary owned by its app composition. Review controllers must not bypass the generated-data owner by importing low-level fetch primitives directly.

Review route features are explicit:

- enabled: folder selection, tree, rendered document, source editing, parent editing, Build, canonical counterpart link, promotion
- disabled initially: scope selector, search, recently added, bookmarks, reports, public links, canonical management toolbar, folder deletion

Startup should skip disabled feature controllers and payload requirements. A missing search or recently-added URL must not force review to publish unused placeholder files.

The review entrypoint may import local source-editor and parent-picker primitives because `/docs-review/` is a local write-capable route. Public entrypoints must never import review or management assets.

## Ownership Boundary

### Data Sharing

Data Sharing owns only the handoff from returned package to temporary review source:

- validate the staged returned package and trusted export metadata
- derive the review folder id
- create or explicitly regenerate the complete review folder
- write `manifest.json`
- write one temporary source Markdown file per valid returned row
- report invalid or skipped returned rows

Data Sharing does not list folders for Docs Review, build review payloads, edit review Markdown, promote canonical source, or rebuild canonical Docs Viewer outputs.

### Docs Review Folder Service

The review-folder service owns:

- safe folder id validation and path resolution
- folder listing and manifest projection
- review source reads and writes
- review source revision checks
- generated review payload builds
- generated index and document reads
- stale or manually deleted folder behavior

### Docs Review Promotion Service

The promotion service owns:

- resolving the trusted target scope from the folder manifest and export metadata
- reading reviewed source and current canonical source
- classifying existing and new `doc_id` values
- constructing the proposed hierarchy graph
- validating the complete promotion plan
- merging explicitly promotable fields into canonical source
- coordinating canonical source writes and rebuilds
- returning a structured promotion receipt

The route/server layer should only validate transport concerns and delegate to these services.

## Review Folder Contract

Review folders remain temporary artifacts outside configured scope lifecycle:

```text
var/analytics/data-sharing/import-preview/<folder_id>/
  manifest.json
  source/
    <doc-id>.md
  generated/
    index-tree.json
    by-id/
      <doc-id>.json
```

Rules:

- folder ids are safe single path segments derived from trusted export metadata
- review folders are never added to `docs-viewer/config/scopes/docs_scopes.json`
- review folders are never published
- manual deletion is valid
- loading a deleted folder reports an ordinary not-found state
- opening or editing a review folder does not change the active configured `/docs/` scope
- regeneration from the staged package is explicit because it replaces manual review edits

The manifest remains the trusted handoff record and includes at least:

- `folder_id`
- `source_export_id`
- `source_scope`
- `profile_id`
- staged filename
- content format
- creation timestamp
- source file records
- returned record counts and issues

## Review Build

Build reads the selected folder's `source/*.md` and writes its `generated/` folder.

Use `DocsDataBuilder` directly as a library with a synthetic configuration. Do not invoke the CLI, add the folder to configured scope data, or use normal scope rebuild orchestration.

The review provider owns index and document reads. It must not depend on generated `content_url` values resolving as public static paths under `var/...`.

Build must:

- validate the selected folder and require at least one source Markdown file
- parse and validate every review document
- generate the tree and per-document rendered payloads
- preserve folder identity in review navigation
- return generated paths, document count, warnings, and a concise summary
- refresh the current tree and document after success

## Temporary Source Editing

The review source editor writes only temporary source under the selected folder.

It should reuse existing Docs Viewer source-editor interaction and rendering primitives through review-specific source services:

1. read the review source body and revision
2. edit Markdown
3. save only when the supplied review revision is current
4. preserve validated review front matter
5. rebuild the selected review folder
6. reload the rendered review document

`parent_id` must also be editable in the review workspace. Prefer reuse of the existing parent-picker/metadata primitives with a review-folder write service. A raw full-file editor is not required merely to change hierarchy.

Review edits must not call canonical `/docs/source/rebuild` or other normal scope write endpoints.

## Canonical Comparison

Docs Review does not provide a comprehensive diff or merge interface.

The intended comparison workflow is:

- keep the reviewed document open in `/docs-review/`
- open the canonical counterpart in `/docs/` in another tab
- compare visually as needed

Promotion confirmation may summarize changed bodies and parent relationships, but it does not render a line-by-line content diff.

The promotion preview/apply pair should retain a narrow optimistic revision check so canonical or review source cannot change between validation and write. A stale plan is rejected and must be validated again; no merge UI is required.

## Version 1 Promotion Contract

Version 1 promotes changes only to documents whose `doc_id` already exists in the trusted target scope.

Promotable fields:

- Markdown body from reviewed source
- `parent_id` from reviewed front matter, including an empty value that makes the document a root

Canonical fields preserved:

- `doc_id`
- canonical filename and source path
- `added_date`
- `title`
- `summary`
- `viewable`
- `ui_status`
- all other canonical front matter unless a later profile explicitly adds it to the promotion contract

Promotion-generated changes:

- set `last_updated` through the normal Docs source timestamp policy
- remove or ignore every `review_*` field

Do not copy a review Markdown file wholesale over canonical source. Promotion parses both sources and produces a canonical merge using only the allowed fields.

The primary action is `Promote reviewed folder`. It plans and applies the complete valid folder as one batch. Selected-document promotion is optional and may be added only if it validates the resulting whole-scope hierarchy after applying the selected overlay.

## Hierarchy Planning And Validation

Hierarchy is a batch contract, not a sequence of independent parent writes.

For promotion preview:

1. Load the current canonical document graph for the trusted target scope.
2. Overlay reviewed `parent_id` values for every promoted existing document.
3. Classify reviewed documents that do not yet exist canonically.
4. Validate the resulting graph before any source write.

Version 1 validation requires:

- every promoted `doc_id` exists canonically
- every non-empty proposed `parent_id` exists canonically
- no document is its own parent
- the resulting graph contains no cycles
- every reviewed source file parses successfully
- duplicate review `doc_id` values are rejected
- all target paths remain inside the configured canonical source root

A new reviewed document or a parent reference to a new reviewed chapter is classified as `requires_v2_create`. If the proposed hierarchy depends on it, version 1 promotion is blocked rather than silently dropping the node or leaving its children at root.

The confirmation summary should remain compact, for example:

```text
50 documents reviewed
42 document bodies changed
37 parent relationships changed
13 resulting roots
0 missing parents
0 cycles
2 new chapter documents require version 2
```

Parent changes may be listed as `doc_id: old_parent -> new_parent`. A content diff is not required.

## Promotion Apply And Rebuild

Promotion uses explicit preview/apply semantics:

- preview constructs the complete plan, validates it, and returns expected review/canonical revisions
- apply requires explicit confirmation and the expected revisions from preview
- apply revalidates the complete plan before writing
- all next source texts are prepared before the first canonical write
- writes use atomic source-write helpers and the shared Docs write/rebuild boundary
- failure before write leaves canonical source unchanged

When `parent_id` changes, rebuild the complete canonical docs index/tree so all ancestor and child placements are current. Search rebuild work may remain targeted to documents whose searchable content or metadata changed where the existing rebuild contract supports that safely.

The response should include:

- target scope
- promoted document ids
- body update count
- parent update count
- unchanged count
- resulting root count
- canonical paths written
- rebuild result
- resulting source revisions
- concise summary text

Promotion writes repository source. It does not automatically create a Git commit. Git commit/push remains a separate explicit repository workflow.

## Version 2: Create New Chapter Documents

New chapter or parent nodes are a required version 2 feature.

External reorganization will often need documents that were not in the original export, for example thematic chapter introductions that become parents of existing documents. Version 2 must allow the returned/reviewed folder to contain both:

- updates to existing canonical `doc_id` values
- new reviewed `doc_id` values to create canonically

Version 2 requirements:

- promotion preview classifies every document as create, update, or unchanged
- new `doc_id` values and filenames use canonical validation and collision rules
- new documents require a title and Markdown body
- new documents receive canonical `added_date`, `last_updated`, default visibility, and allowed front matter through normal source policy
- new documents may be parents or children of existing or other new documents in the same batch
- existing documents may be reparented to new chapter documents in the same batch
- graph validation includes current canonical documents plus every planned create and update
- cycles, self-parenting, missing parents, duplicate ids, and path collisions block the complete plan
- all create/update source texts are prepared before writes begin
- canonical create and update writes occur in one validated promotion operation
- the review UI clearly marks new chapters and the confirmation summary reports create and update counts
- no new document is created implicitly from a missing parent reference; it must have an explicit reviewed source document

Version 2 does not require a comprehensive content diff or automatic Git commit.

## Suggested Backend Surface

Exact route names may be refined during implementation, but ownership should remain explicit:

```text
GET  /docs-review/folders
GET  /docs-review/folders/index-tree?folder_id=<folder_id>
GET  /docs-review/folders/payload?folder_id=<folder_id>&doc_id=<doc_id>
GET  /docs-review/folders/source?folder_id=<folder_id>&doc_id=<doc_id>
POST /docs-review/folders/build
POST /docs-review/folders/source
POST /docs-review/folders/promotion-preview
POST /docs-review/folders/promotion-apply
```

Review-source writes require `folder_id`, `doc_id`, expected review revision, and the edited body or explicit metadata change.

Promotion endpoints require `folder_id`, confirmation state, expected plan revisions, and no arbitrary filesystem paths or caller-supplied target scope override.

## Proposed Repo Ownership

Review-specific code stays inside the existing Docs Viewer area:

```text
docs-viewer/
  runtime/js/review/
    docs-viewer-review.js
    docs-viewer-review-client.js
    docs-viewer-review-controller.js
    docs-viewer-review-provider.js
    docs-viewer-review-promotion.js
  services/
    docs_review_folders.py
    docs_review_promotion.py
  static/css/
    docs-viewer-review.css
```

The exact filenames may change, but the owners must remain separate:

- shared runtime owns generic app context, provider, routing, panel, tree, and document behavior
- review frontend owns folder selection, Build, temporary source service composition, canonical counterpart links, and promotion UI
- review folder service owns temporary filesystem behavior
- review promotion service owns canonical promotion planning and apply
- normal management modules retain general canonical management behavior

The current `docs_review_sessions.py` and tentative `docs-viewer-review-sessions-*` modules should be replaced or renamed into these current owners during implementation. Do not keep aliases or parallel old routes after callers and tests are migrated.

## Implementation Steps

### 1. Baseline And Retired Prototype Cleanup

- Inventory existing review-session services, routes, frontend modules, CSS, tests, and docs.
- Reuse path-validation and list/read behavior that fits this contract.
- Rename `session_id` to `folder_id` across the current owner surface.
- Replace `docs_review_sessions.py` with the review-folder owner rather than adding a facade.
- Remove the unused modal/delete prototype and old `/docs/review-sessions...` routes after callers and tests are migrated.
- Keep folder deletion out of version 1.

### 2. Complete The Review Folder Service

- Implement folder listing, manifest projection, safe resolution, index reads, payload reads, source reads, and stale-folder errors.
- Return raw viewer payloads through a stable review-provider response contract.
- Add review source revisions using the same digest principle as canonical source editing.
- Require a trusted manifest whose folder id and source scope agree with export metadata.

### 3. Implement Review Builds

- Construct a synthetic `DocsScopeConfig` for the selected folder.
- Call `DocsDataBuilder` directly with the review source and generated roots.
- Do not invoke `build_docs.py`, normal scope rebuild, search build, or publish.
- Return a structured build report.
- Ensure generated links and provider reads preserve folder identity.

### 4. Add The Review App Context And Provider Seam

- Extend access/app-context projection from public/manage to public/manage/review.
- Separate local generated-read authority from general management authority.
- Add the provider contract through app composition and the generated-data owner.
- Make scope config, search, recently added, bookmarks, reports, and management initialization conditional route features.
- Keep new lifecycle ownership out of `docs-viewer-app-runtime.js`; use focused app-context/provider owners.
- Add positive boundary tests proving public entrypoints do not import review or management assets.

### 5. Serve `/docs-review/`

- Add the review route to the existing local Docs Viewer server.
- Serve a shared or thin review shell with the stable Docs Viewer mounts.
- Add the route record and review feature projection.
- Add the thin review entrypoint and controller composition.
- Render folder selector, current folder metadata, Build, canonical counterpart link, tree, rendered document, source view, parent editing, status, and promotion action.

### 6. Add Temporary Markdown And Parent Editing

- Adapt the shared source editor to review source services.
- Save review bodies with optimistic review revision checks.
- Add review `parent_id` editing through a focused metadata/parent service.
- Preserve review front matter fields not owned by the edit.
- Rebuild and reload the selected review folder after successful edits.
- Confirm no review edit endpoint can resolve a canonical source path.

### 7. Implement Version 1 Promotion Preview

- Resolve target scope only through trusted review/export metadata.
- Parse every review source document.
- Match existing canonical documents by stable `doc_id`.
- Build the canonical graph with reviewed parent overlays.
- Classify new docs and new-parent dependencies as `requires_v2_create`.
- Validate paths, duplicates, missing parents, self-parenting, and cycles.
- Plan canonical body and `parent_id` merges while preserving other canonical front matter.
- Return compact counts, parent changes, blockers, expected revisions, and confirmation requirements without a content diff.

### 8. Implement Version 1 Promotion Apply

- Require explicit confirmation and expected plan revisions.
- Re-run the preview plan and reject stale inputs.
- Prepare every next canonical source text before writing.
- Apply body and hierarchy changes as one batch through atomic write helpers.
- Run the required canonical docs tree and search rebuild work.
- Record activity and return the promotion receipt.
- Provide canonical viewer links for promoted documents.

### 9. Focused Verification

Add service-level tests for:

- safe folder and document resolution
- symlink and path traversal rejection
- build output generation
- source revision reads and stale temporary writes
- folder-aware index/payload reads
- canonical target resolution from trusted metadata
- body-only and body-plus-parent promotion merges
- preservation of non-promoted canonical front matter
- root parent changes
- missing parents, self-parenting, duplicate ids, and cycle rejection
- new reviewed docs classified as version 2 blockers
- stale promotion plan rejection
- no canonical writes when preview validation fails
- canonical rebuild invocation after a confirmed batch

Add route/module checks for:

- `/docs-review/` shell and static asset serving
- review route boot with no configured-scope registration
- review entrypoint imports shared primitives and review owners rather than copied viewer modules
- public entrypoints do not import review assets
- `/docs/` manage behavior remains unchanged

Use one small browser smoke only for the durable integration boundary: load a prepared review folder, select a document, edit temporary source, rebuild, and confirm the promotion preview can be requested. Do not make detailed modal choreography or visual comparison a permanent browser contract.

### 10. Documentation And Closeout

- Update durable Docs Viewer runtime, route surface, module ownership, generated-data, source-write, and Data Sharing docs.
- Remove retired review-session terminology, routes, files, tests, and CSS.
- Do not leave compatibility aliases.
- Record generated payload status and focused verification results.
- Mark version 1 complete only when canonical promotion of existing documents and hierarchy changes is working end to end.

### 11. Version 2: New Chapter Creation

Status: deferred, required follow-up.

- Extend promotion planning with explicit create operations.
- Validate new ids, titles, filenames, front matter, and paths.
- Build the combined current/create/update graph.
- Apply creates and updates as one validated batch.
- Rebuild canonical outputs and return create/update receipts.
- Add focused tests for new parents of existing docs, nested new chapters, create collisions, and graph failure before write.

## Version 1 Acceptance Criteria

Version 1 is complete when:

- `/docs-review/` uses the shared Docs Viewer runtime without a copied frontend application
- review folders are selected by `folder` URL state and are not configured scopes
- the selected folder can be built and rendered
- temporary Markdown and `parent_id` can be edited and rebuilt
- the canonical counterpart can be opened in `/docs/`
- promotion preview validates the complete existing-doc graph without providing a comprehensive content diff
- confirmed promotion updates canonical bodies and `parent_id` values while preserving other canonical front matter
- hierarchy cycles, missing parents, unsafe paths, invalid source, and new-node dependencies block version 1 before writes
- canonical Docs Viewer outputs are rebuilt after promotion
- public routes load no review or management assets
- version 2 new chapter creation remains documented as a required next capability

## Non-Goals

Version 1 does not:

- create new canonical documents or chapter nodes
- provide side-by-side or line-by-line diff tooling
- merge concurrent content edits
- automatically create a Git commit or push changes
- publish public Docs Viewer outputs
- delete review folders through the UI
- treat review folders as configured scopes
- expose review behavior from the normal `/docs/` scope selector or management toolbar

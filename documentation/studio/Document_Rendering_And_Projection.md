---
draft: false
doc_id: d-20261003-000734-6cff69
title: Document Rendering And Projection
added_date: "2026-10-03 00:07:34"
last_updated: "2026-10-08 19:10:43"
summary: Remove redundant Working public-manifest generation and dependencies while preserving existing rendering and field contracts.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Document Rendering And Projection

Status: complete on 2026-10-03. Implementation, obsolete Working output removal, selected static checks, code review and durable documentation transfer are complete. Build/Publish execution and browser verification were not part of the selected evidence. This feature and its bounded delivery are parented to [Planned Features](Planned_Features.md).

The document model retains its existing field definitions, values, validation, rendering and publication rules. This delivery removes redundant work: Working collection builds previously generated a public `manifest.json` that neither Working readers nor Publish needed, and targeted builds maintained and compared two manifests. Builds now produce only their relevant collection manifest, making each workflow easier to inspect.

## Agreed Ownership

The dependency runs from Publish to Working. Working owns canonical sources and local generated output; its document builds operate independently of Preview's contents, existence and publication state. Working builds do not consult Preview, prepare its output, or maintain a public manifest for a future publication.

Publish consumes Working inputs, applies publication eligibility and any publication-specific source projection, and builds public document output in temporary storage. It then validates and replaces the prepared `preview/` snapshot and distributes that completed snapshot through the existing publication owner. Publication does not require Working to have generated a public collection manifest first.

| Operation | Document selection | Collection list output |
| --- | --- | --- |
| Complete Working collection build | All source documents in the requested collection, including drafts | `working/generated/collections/<collection>/documents/manage-manifest.json` |
| Targeted Working collection build | The supplied document IDs, with saved metadata preserving the rest of the collection | The same management manifest, updated for the selected IDs |
| Publish document preparation | Eligible documents selected by the publication owner | Public `manifest.json` in temporary build output, retained under `preview/collections/<collection>/documents/` |

Workspace paths in the table are relative to the configured `DOTLINEFORM_DOCS_BASE_DIR`. The intended result is one relevant collection manifest per operation: Working retains management output and Preview retains public reader output.

## Existing Rendering And Projection

Shared rendering already exists. Working collection builds and Publish's temporary collection builds use the same [CollectionDocsBuilder](../../docs-viewer/build/docs_builder/collection.py), which inherits the [common document builder](../../docs-viewer/build/docs_builder/pipeline.py) and its [document payload rendering](../../docs-viewer/build/docs_builder/payloads.py). The collection builder already has separate management and public manifest projection methods. The redundant work comes from invoking and maintaining both projections on every collection build.

The ownership principle remains that the caller selects which documents to render and which existing output projection to produce:

1. **Which documents to render.** The caller supplies the selected files or document records and the document identity/title context required to render them.
2. **Which output projection to produce.** Working uses the existing management projection; Publish uses the existing public projection. Their fields and derived values keep their current meanings.

The renderer continues using its existing output destination, templates, collection customisation and link/media context. This cleanup does not require a new rendering interface, configurable field schema or redesign of by-ID payloads. Broader renderer changes can be discussed separately if a concrete need emerges.

Shared code still validates the supplied identities, content and output contract. Preserve existing identity, date and metadata validation when removing the redundant public-projection path. Operation owners select the required existing projection so that the build produces only the relevant manifest.

## Watcher And Targeted Collection Builds

Application writes pass exact affected document IDs to the collection builder and await required generation. Source Save reuses the [exact-document rebuild owner](../../docs-viewer/services/docs_document_rebuild.py); external Markdown edits require explicit Rebuild. Document rendering and any required manifest update belong to the invoked build operation.

`manage-manifest.json` is the local collection index used by the collection list. A targeted build renders the selected documents, merges their list metadata into that saved index, removes selected entries and generated payloads for deleted documents, and preserves unselected document payloads. Reading the saved management manifest preserves rows for documents outside the requested build; keeping the list complete means retaining those rows, rather than rendering their sources again.

The builder writes the management manifest only when the resulting projection changes, such as after a title, projected date, draft, subject or customisation change, addition or deletion. A content change that leaves the list projection unchanged requires no manifest write.

The saved management manifest supplies collection membership and titles. A targeted Working build must validate the metadata it uses, but it should neither require a public manifest nor compare management and public membership. Missing or invalid required management metadata remains a visible prerequisite failure.

Targeted builds retain their existing relationship and selected-document follow-through. Search remains an explicit separate rebuild; this approach does not change Search or Recents ownership.

## Draft Metadata And Eligibility

Working document rendering does not filter the requested documents by `draft` or other publication eligibility. Draft documents still need local rendered output.

Working source validation and management projection retain the required boolean `draft` value for ordinary and other applicable collection documents. Manage displays that state, and Search/Recents use it under their own eligibility rules. Catalogue retains its existing fixed eligibility and source contract without a `draft` field.

Publish owns interpreting eligibility when selecting the prepared document set, including inherited draft exclusions, ordinary unpublishable exclusions and excluded collection hosts. The shared renderer receives that selected set. Carrying readiness metadata for local consumers and deciding publication membership are separate responsibilities.

## Delivered Implementation

The [collection builder](../../docs-viewer/build/docs_builder/collection.py) selects one existing projection from the operation's build role and reads/writes only that manifest. Targeted Working builds merge management metadata and use its membership and titles for rendering context. Identity/date validation is shared by both projections. Publication builds skip private subject projection entirely. Diagnostics identify the selected filename and one manifest change count.

The [Publish preparation owner](../../docs-viewer/services/docs_prepare_preview.py) continues capturing eligible source inputs and building fresh output in temporary storage. It does not consume Working's collection `manifest.json`. The [snapshot projection](../../docs-viewer/services/docs_preview_snapshot.py) retains its exclusion of management artifacts from the completed Preview artifact.

The local generated-read owner accepts only the management manifest and exact document payloads; Delete's generated-output description names the management manifest. The obsolete Working public manifests were removed from all four configured collection document outputs. [Generated Data Contracts](Generated_Data_Contracts.md#collection-manifest-ownership) now owns the durable lifecycle contract; the older dual-manifest document is explicitly labelled historical.

## Publish Impact

Removing Working's public collection manifest requires no change to Publish's input capture, eligibility selection, snapshot replacement or distribution workflow. Publish already invokes the shared builder with the Preview build role inside an isolated temporary workspace; the existing call identifies which projection that build needs.

The shared builder retains public `manifest.json` generation for the temporary publication build while Working emits only `manage-manifest.json`. Distribution continues to consume the public manifest from the completed Preview snapshot, with its existing fields and validation.

## Bounded Cleanup

- [x] Stop Working collection builds generating, writing or requiring `manifest.json`; use the existing management projection and its current fields.
- [x] Make targeted Working builds read, validate and merge only `manage-manifest.json`, using its membership and titles for rendering context. Remove the comparison between the two manifests.
- [x] Retain the existing public `manifest.json` projection for Publish preparation, with its current fields and validation.
- [x] Stop temporary publication builds generating `manage-manifest.json`, which snapshot projection previously discarded. Retain the public snapshot boundary's exclusion of management artifacts.
- [x] Remove obsolete Working public-manifest files and their local read route, and update affected diagnostics and management output descriptions. Preserve the management and public reader filenames at their respective owners without compatibility fallbacks.
- [x] Review the bounded change against existing validation, rendering and publication behavior, and update the durable manifest contract.

There is no field-definition or field-meaning redesign to resolve before this cleanup. Further discussion should address a concrete workflow question without turning the redundant-manifest removal into a wider rendering refactor.

## Delivery Steps

The delivered outcome is one relevant collection manifest per build operation, with targeted Working builds depending only on management metadata. Existing fields, rendered documents and publication behavior retain their current contracts. Each step's record captures the changed owners, selected evidence, findings and gate outcome.

### CM.0 Readiness

- [x] Confirm the shared collection builder, local generated readers and Publish preparation still support the agreed ownership and sequence.
- [x] Confirm the Working cleanup boundary and preserve unrelated changes.

Evidence budget: concise read-only source/config inspection; no builds or tests. Gate: the change remains removal of redundant work. Resolve any requirement for field changes or a broader renderer refactor before implementation.

Record: complete. Readers use management metadata and Publish builds fresh public output through the same collection builder. Readiness identified four obsolete Working public manifests and shared date/identity validation that needed preservation. No field or workflow redesign was needed. No unrelated worktree changes were present. Gate passed.

### CM.1 Builder Simplification

- [x] Select the existing management projection for Working and the existing public projection for temporary publication builds; build and write only the selected manifest.
- [x] Make targeted Working builds use only saved management metadata for merging, membership and title context; remove the dual-manifest comparison.
- [x] Preserve source and metadata validation, conditional manifest writes, selected document deletions, and existing relationship and selected-document follow-through.

Evidence budget: explicit-path Python lint for changed source and scoped source/diff review. Focus on lost validation, changed projections and accidental changes to unselected documents; expected cost is seconds to a few minutes, without workspace builds or network effects. Gate: both operation roles retain their existing output contracts, and Working has no public-manifest prerequisite. Record any execution evidence gap; test work follows a separately agreed specification under [Test Contract Discipline](Test_Contract_Discipline.md).

Record: complete. The collection builder and saved-metadata helper now maintain one operation-owned manifest. Existing date/identity validation moved into shared row construction; source loading, item rendering and relationship/selected-document follow-through remain with their existing owners. Targeted merging and conditional writes operate on the selected manifest alone. Final `bin/lint-python docs-viewer/build/docs_builder/collection.py` passed after source documentation updates. Gate passed with static/source-review evidence; full and targeted build execution was not selected.

### CM.2 Consumers And Generated Cleanup

- [x] Remove the Working public-manifest read route and update affected diagnostics, output descriptions and active references through their existing owners.
- [x] Remove obsolete public-manifest files only from configured Working collection document outputs; retain the public snapshot boundary's exclusion of management artifacts.

Evidence budget: focused reference searches, changed-source lint where needed, whitespace checking and inspection of the exact cleanup paths and generated delta. Expected cost is seconds to a few minutes; writes are confined to the obsolete Working outputs. A generator run must address a named remaining risk and have its command, writes and cost recorded before execution. Gate: active consumers use their correct manifest, obsolete Working files are removed, and cleanup introduces no fallback or wider deletion.

Record: complete. Generated-read allowlisting and Delete's output description now use the management manifest. Diagnostics report only the selected manifest. The four obsolete Working files were removed for `works`, `concepts`, `moments` and `catalogue`; management manifests and by-ID payloads were untouched. No Working completion receipt existed to invalidate. `bin/lint-python docs-viewer/build/docs_builder/collection.py docs-viewer/build/docs_builder/collection_metadata.py docs-viewer/services/docs_generated_reads.py docs-viewer/services/docs_management_mutations.py` and `git diff --check` passed. Focused consumer searches found no remaining active Working public-manifest dependency. No generator run was required for the obsolete-file cleanup. Gate passed.

### CM.3 Code Review

- [x] After implementation and its selected evidence, review the final bounded diff for redundant projection work, residual public-manifest dependencies, validation loss, ownership drift and unintended rendering or publication changes.
- [x] Resolve findings within this cleanup and rerun only evidence affected by a review change.

Evidence budget: bounded source/diff review; no additional suite or Build/Publish run by default. Gate: findings are resolved or recorded as explicit evidence limits, and completion claims match the inspected behavior.

Record: complete. Reviewed both build-role branches, shared row validation, saved-metadata merging, title/membership rendering context, selected-only removal, private subject generation, diagnostic consumers and package-source callers. Public preparation and distribution retain their existing contract, and the snapshot management-artifact exclusion remains. No compatibility aliases or unresolved code findings remain within this slice. Static lint/whitespace evidence is limited to the changed paths; no tests, browser checks, Build or Publish were run. Gate passed.

### CM.4 Closeout

- [x] Update [Generated Data Contracts](Generated_Data_Contracts.md) and directly affected manifest documentation to describe the shipped ownership and targeted-build prerequisites.
- [x] Record the completed output cleanup, selected checks and remaining evidence limits; recommend whether this feature document should be retained or retired after durable documentation transfer.

Evidence budget: documentation source review and reuse of accepted implementation evidence. Gate: the complete cleanup is delivered and the durable owner is current. Real Publish, Search rebuilds, public deployment, Git commit/push and document retirement remain separately requested actions.

Record: complete. Durable lifecycle ownership transferred to Generated Data Contracts, the Catalogue architecture paragraph was corrected, and Development Checklist retains the guardrail. The older public/Manage manifest document is labelled historical. Recommend retaining this feature document for the user's immediate review and any further clarification, then retiring it after review; its durable destinations are Generated Data Contracts and Development Checklist. No document files were deleted. Existing Preview/site output and Search remain unchanged; no runtime-code projection, Build, Publish, deployment, commit or push ran. Gate passed with the execution evidence limits recorded above.

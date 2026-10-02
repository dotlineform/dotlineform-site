---
draft: false
doc_id: d-20261003-000734-6cff69
title: Document Rendering And Projection
added_date: "2026-10-03 00:07:34"
last_updated: "2026-10-03 00:26:00"
summary: Remove redundant Working public-manifest generation and dependencies while preserving existing rendering and field contracts.
ui_status: planned
parent_id: d-20260428-000000-f5ff18
---
# Document Rendering And Projection

Status: approach agreed; delivery proposed; implementation has not started. This feature and its bounded delivery are parented to [Planned Features](Planned_Features.md).

The current document model works. The issue is redundant work: Working collection builds generate a public `manifest.json` that neither Working readers nor Publish need, and targeted builds then maintain and compare two manifests. Remove that redundant output and its dependencies while retaining the existing field definitions, values, validation, document rendering and publication rules. Keeping only relevant generated files makes each workflow easier to inspect.

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

The [watcher](../../docs-viewer/services/docs_live_rebuild_watcher.py) detects source changes and passes the affected document IDs to the collection builder. The watcher does not read or merge collection manifests. Document rendering and any required index update belong to the invoked build operation.

`manage-manifest.json` is the local collection index used by the collection list. A targeted build renders the selected documents, merges their list metadata into that saved index, removes selected entries and generated payloads for deleted documents, and preserves unselected document payloads. Reading the saved management manifest preserves rows for documents outside the requested build; keeping the list complete means retaining those rows, rather than rendering their sources again.

The builder writes the management manifest only when the resulting projection changes, such as after a title, projected date, draft, subject or customisation change, addition or deletion. A content change that leaves the list projection unchanged requires no manifest write.

The saved management manifest supplies collection membership and titles. A targeted Working build must validate the metadata it uses, but it should neither require a public manifest nor compare management and public membership. Missing or invalid required management metadata remains a visible prerequisite failure.

Targeted builds retain their existing relationship and selected-document follow-through. Search remains an explicit separate rebuild; this approach does not change Search or Recents ownership.

## Draft Metadata And Eligibility

Working document rendering does not filter the requested documents by `draft` or other publication eligibility. Draft documents still need local rendered output.

Working source validation and management projection retain the required boolean `draft` value for ordinary and other applicable collection documents. Manage displays that state, and Search/Recents use it under their own eligibility rules. Catalogue retains its existing fixed eligibility and source contract without a `draft` field.

Publish owns interpreting eligibility when selecting the prepared document set, including inherited draft exclusions, ordinary unpublishable exclusions and excluded collection hosts. The shared renderer receives that selected set. Carrying readiness metadata for local consumers and deciding publication membership are separate responsibilities.

## Current Implementation Gap

The [collection builder](../../docs-viewer/build/docs_builder/collection.py) currently generates both `manifest.json` and `manage-manifest.json`. Targeted builds load both saved files, compare their membership, and merge selected rows into both. The builder also takes collection membership and title context for rendering from the public projection, although the management manifest already contains that information. Working reader configuration selects the management manifest.

The [Publish preparation owner](../../docs-viewer/services/docs_prepare_preview.py) already captures eligible source inputs and builds fresh output in temporary storage. It does not consume Working's collection `manifest.json`. The [snapshot projection](../../docs-viewer/services/docs_preview_snapshot.py) currently excludes the management manifest from the completed Preview artifact.

The older [Sub-Scope Public And Manage Manifests](Sub_Scope_Public_And_Manage_Manifests.md) document describes a shared build producing both manifests followed by publication copying the public one. That records the earlier copy-based design; its retired paths and workflows are historical context, not the contract for this proposal.

## Publish Impact

Removing Working's public collection manifest requires no change to Publish's input capture, eligibility selection, snapshot replacement or distribution workflow. Publish already invokes the shared builder with the Preview build role inside an isolated temporary workspace; the existing call identifies which projection that build needs.

The shared builder change must retain public `manifest.json` generation for that temporary publication build while Working emits only `manage-manifest.json`. Distribution continues to consume the public manifest from the completed Preview snapshot, with its existing fields and validation.

## Bounded Cleanup

- [ ] Stop Working collection builds generating, writing or requiring `manifest.json`; use the existing management projection and its current fields.
- [ ] Make targeted Working builds read, validate and merge only `manage-manifest.json`, using its membership and titles for rendering context. Remove the comparison between the two manifests.
- [ ] Retain the existing public `manifest.json` projection for Publish preparation, with its current fields and validation.
- [ ] Stop temporary publication builds generating `manage-manifest.json`, which snapshot projection currently discards. Retain the public snapshot boundary's exclusion of management artifacts.
- [ ] Remove obsolete Working public-manifest files and their local read route, and update affected diagnostics and management output descriptions. Preserve the management and public reader filenames at their respective owners without compatibility fallbacks.
- [ ] Review the bounded change against existing validation, rendering and publication behavior, and update the durable manifest contract when implementation is complete.

There is no field-definition or field-meaning redesign to resolve before this cleanup. Further discussion should address a concrete workflow question without turning the redundant-manifest removal into a wider rendering refactor. This document records the proposed cleanup; runtime implementation remains separate.

## Delivery Steps

The complete outcome is one relevant collection manifest per build operation, with targeted Working builds depending only on management metadata. Existing fields, rendered documents and publication behavior retain their current contracts. The steps below are proposed; adding this plan does not start implementation. Each step's record will capture the changed owners, selected evidence, findings and gate outcome as work proceeds.

### CM.0 Readiness

- [ ] Confirm the shared collection builder, local generated readers and Publish preparation still support the agreed ownership and sequence.
- [ ] Confirm the Working cleanup boundary and preserve unrelated changes.

Evidence budget: concise read-only source/config inspection; no builds or tests. Gate: the change remains removal of redundant work. Resolve any requirement for field changes or a broader renderer refactor before implementation.

Record: pending.

### CM.1 Builder Simplification

- [ ] Select the existing management projection for Working and the existing public projection for temporary publication builds; build and write only the selected manifest.
- [ ] Make targeted Working builds use only saved management metadata for merging, membership and title context; remove the dual-manifest comparison.
- [ ] Preserve source and metadata validation, conditional manifest writes, selected document deletions, and existing relationship and selected-document follow-through.

Evidence budget: explicit-path Python lint for changed source and scoped source/diff review. Focus on lost validation, changed projections and accidental changes to unselected documents; expected cost is seconds to a few minutes, without workspace builds or network effects. Gate: both operation roles retain their existing output contracts, and Working has no public-manifest prerequisite. Record any execution evidence gap; test work follows a separately agreed specification under [Test Contract Discipline](Test_Contract_Discipline.md).

Record: pending.

### CM.2 Consumers And Generated Cleanup

- [ ] Remove the Working public-manifest read route and update affected diagnostics, output descriptions and active references through their existing owners.
- [ ] Remove obsolete public-manifest files only from configured Working collection document outputs; retain the public snapshot boundary's exclusion of management artifacts.

Evidence budget: focused reference searches, changed-source lint where needed, whitespace checking and inspection of the exact cleanup paths and generated delta. Expected cost is seconds to a few minutes; writes are confined to the obsolete Working outputs. A generator run must address a named remaining risk and have its command, writes and cost recorded before execution. Gate: active consumers use their correct manifest, obsolete Working files are removed, and cleanup introduces no fallback or wider deletion.

Record: pending.

### CM.3 Code Review

- [ ] After implementation and its selected evidence, review the final bounded diff for redundant projection work, residual public-manifest dependencies, validation loss, ownership drift and unintended rendering or publication changes.
- [ ] Resolve findings within this cleanup and rerun only evidence affected by a review change.

Evidence budget: bounded source/diff review; no additional suite or Build/Publish run by default. Gate: findings are resolved or recorded as explicit evidence limits, and completion claims match the inspected behavior.

Record: pending.

### CM.4 Closeout

- [ ] Update [Generated Data Contracts](Generated_Data_Contracts.md) and directly affected manifest documentation to describe the shipped ownership and targeted-build prerequisites.
- [ ] Record the completed output cleanup, selected checks and remaining evidence limits; recommend whether this feature document should be retained or retired after durable documentation transfer.

Evidence budget: documentation source review and reuse of accepted implementation evidence. Gate: the complete cleanup is delivered and the durable owner is current. Real Publish, Search rebuilds, public deployment, Git commit/push and document retirement remain separately requested actions.

Record: pending.

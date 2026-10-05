---
draft: false
doc_id: d-20260927-135604-05446e
title: Subject Associations
added_date: "2026-09-27 13:56:04"
last_updated: "2026-10-05 09:43:48"
summary: Manifest-owned subjects, in-memory report associations, exact navigation, and private/public generation boundaries.
parent_id: d-20260423-000000-d015e6
---
# Subject Associations

## Purpose And Review Boundary

This is the current-state inventory for document Subjects and their derived report associations. On 2026-10-03 Series was retired as a document Subject after the user reassigned every remaining declaration. Work, configured Folder and None are the supported choices. Record each data product's purpose, the UI actions that read or change it, its consumers, and its update/publication rules. Use the same questions when reviewing semantic tokens, document links, and their UI actions.

Reports derive associations in memory from optional scalar `subject` fields in each subject-enabled collection's private `manage-manifest.json`. An explicitly declared subject maps to the documents about that subject. The former `subject-associations.json` product is retired from every collection: no producer, generated-data read allowance, Preview validation or distribution branch remains. There is no replacement lookup file. Subjects do not collect semantic-token references, Markdown links, or all documents related through Catalogue membership.

The proposed UI idea is to present document relationships as **related links**, regardless of how they were derived. That is an exploration aim, not an implemented or agreed replacement model. This document records current behavior separately from questions for that review.

Catalogue remains a registered document collection. On 2026-10-03 the user retired the superseded proposal to remove Catalogue documents. Subject retirement does not change Catalogue Work IDs, Studio Series, Work-to-Series membership, report Series columns or Catalogue ownership.

## Key Data Files

All workspace paths below are relative to the configured `$DOTLINEFORM_DOCS_BASE_DIR`. [Workspace configuration](../../../docs-viewer/config/workspace/docs-workspace.json) resolves storage and collection ownership; these are external workspace files, not repository-owned generated documents.

| File | Purpose And Authority | UI Actions And Consumers | Update And Publication Rules |
| --- | --- | --- | --- |
| `working/source/collections/<collection>/documents/*.md` | Canonical document identities and configured subject declarations in front matter. Catalogue uses the Work ID as `doc_id`, with no separate `work_id`. | Assign/Change Subject writes the configured subject field group. Open Source permits direct file editing. Collection Regenerate can replace generated document source, including Catalogue Work documents. | Source changes feed collection document builds. Publish captures eligible source and builds temporary Preview output. Canonical Working source is not distributed as reader data. |
| `working/generated/collections/<collection>/documents/manage-manifest.json` | Private document list with optional scalar `subject` when projection is enabled, plus `subject_generation`. Subject omission means None. An independent `has_thumbnail: true` records an authored thumbnail, including when a Subject is present. Catalogue does not project document Subjects. | Exact-document Subject information and assignment; Projects' Folder/Work placement, Works' Work-derived Series coverage and Context Work-thumbnail selection. Catalogue browsing uses its Work-ID `doc_id` directly. | Collection builds maintain the rows and generation. Targeted builds merge selected rows with validated saved rows, preserving unselected metadata. Excluded from the completed Preview snapshot and public distribution. |
| `preview/collections/<collection>/documents/manifest.json` | Prepared public-reader list containing `doc_id`, `title` and date-only `last_updated`. Context rows include either authored `has_thumbnail: true`, otherwise Work-only scalar `subject`, otherwise neither; Folder paths and other private metadata are excluded. | Public collection readers use the selected thumbnail field. Omitted `subject` does not prove absence of a source Work association. | Working does not keep a public `manifest.json`. Publish builds the reader list in temporary storage, retains it in Preview and distributes it to the configured repository destination. |

Catalogue Works' private `working/generated/catalogue/reports/catalogue-works/metadata.json` supplies Work/Series display and search data. Each Work's definitive Catalogue document uses that exact Work ID as `doc_id`; the report composes its destination using the configured report host and existing route helper without reading a document manifest. Studio Work Save updates canonical records and the editor; Refresh Catalogue updates report metadata, while Catalogue Regenerate maintains the linked documents. [Catalogue Works](../Catalogue_Works.md) owns that distinction. Local and public browser configuration expose Catalogue's exact `report_host_doc_id`, without inferring a host from the current route or document tree.

## Subject And Association Shape

The recognized canonical declarations remain `work_id` → Work and `folder_path` → Folder. A document may declare at most one Subject. Generated management rows and committed response records project a string `subject` or omit it for None. They never emit an empty string, `null`, a None sentinel or a kind/key object. Present malformed values and the retired generated `authoring_subject` field fail validation without conversion or aliases. Multiple source declarations, invalid values and unsupported Folder declarations also fail. Document `series_id` fields are rejected even when blank; obsolete assignment field sets remain rejected. Studio Work `series_id` remains a separate Catalogue membership field.

Exactly five ASCII digits identify a Work, retaining leading zeros such as `"00635"`. Other valid decoded relative targets identify Folders when the exact collection supports them, such as `"projects/100 grasping hands"`. A source Folder declaration whose normalized target is bare five ASCII digits fails because that scalar form is reserved for Work identity. Folder normalization retains existing path safety: no absolute paths, backslashes, control characters, URL schemes, local-link markup, empty segments or traversal segments. Normalization checks neither Work registry membership nor folder existence, and never infers identity from titles, filenames, body text, selected rows or route context.

Subject-enabled management manifests contain immutable `doc_id`, presentation metadata, optional scalar `subject` and `subject_generation`. [Python Subject ownership](../../../docs-viewer/services/docs_document_subjects.py) and the [shared JavaScript classifier](../../../docs-viewer/runtime/js/shared/docs-document-subject.js) validate/classify that single input; consumers may derive ephemeral `{kind, key}` values for their own domain behavior. Project State groups valid Subjects, keeps every matching document, composes exact Manage links from the configured Works host, and preserves title/ID ordering. Its purpose-specific declared-subject response remains typed. Catalogue has no Subject projection or separate Work-to-document association: navigation uses its five-digit `doc_id` directly. There is no publishing-stage discriminator or persisted association payload. Source-field groups retain their own assignment identity and are not aliases for retired generated metadata.

Projects first scans every immediate physical project folder and retains unmatched folder rows. Work-subject documents are placed through their Work's canonical project folder and Series membership. Folder-subject documents are placed at the declared folder and may appear against every Series represented by Works there; that association is broader than an explicit Series declaration. The Works coverage report derives Series documentation through member-Work subjects only. Both reports keep plain-text Series columns, while their Docs cells retain exact document links.

Several documents may share a subject. That is valid for Project State. Every current Work requires one definitive Catalogue document with its Work ID as `doc_id`. A direct link loads that exact by-ID payload before any list manifest; a missing document is a destination error to repair through Regenerate, without a guessed target or old-ID alias.

## UI Action Map

| UI Action | Effect On Subject Data | Completion Or Freshness Boundary |
| --- | --- | --- |
| Assign Subject / Change Subject, including clearing it | Writes the exact document's configured front-matter field group, then rebuilds its collection outputs. | The management operation awaits its source-write and collection-build follow-through. Current assignment rejects non-empty Folder subjects, although existing Working Works folder declarations remain readable. |
| Open Source and edit canonical Markdown | A declaration change updates normalized subjects in the management manifest. | The Working watcher rebuilds affected document output independently after the file changes. |
| Source Editor Save | Saves validated source and supplies scalar committed metadata, including independent Subject and authored-thumbnail assignments, to retained readers. | Save completes at canonical source persistence; watcher generation is independent. |
| Working document Build or collection document rebuild | Recomputes normalized subjects and manifest generation. | A successful build owns the result. Targeted collection builds use merged saved metadata, preserving unselected documents. |
| Collection Regenerate | Rewrites collection-owned generated source and rebuilds document outputs and manifests. | Source regeneration and its owning rebuild are separate from Studio Work Save. |
| Document create, import, or delete with collection rebuild follow-through | Adds or removes exact manifest rows. | The source operation's collection build owns reconciliation. |
| Publish | Captures eligible source, builds temporary document output, validates/replaces Preview and distributes the completed snapshot. | One awaited Publish action. Management manifests remain private; no association artifact is generated. Git commit, push and Deploy Public are separate actions. |
| Open Catalogue Works | Reads private report metadata and composes Work ID/title links from each Work ID and the configured Catalogue report host. | No Catalogue document-manifest or mapping read; direct destinations load exact by-ID content. |
| Open Context (Working Works collection) | Uses the shared title/draft/selection list with authored thumbnails first, then existing Catalogue Work thumbnails for Work-subject rows. Its `working_works` contribution supplies document-detail Subject information, Assign Subject and Folder-only Open in Finder. | Committed Source/Subject changes reevaluate the retained row in memory, preserving filtering, sorting, paging and exact navigation. No Subject column or private Catalogue title-file read. The assignment picker reads generated Work targets through its separately owned Catalogue provider. |
| Project State Run/Refresh | Reads Works' management manifest, groups valid subjects and places documents against project folders and canonical Catalogue data. | Returns a newly assembled report without rebuilding or repairing its inputs. |
| Follow a document link or open a Series gallery | Uses the exact destination or the separate Media View owner. | Navigation only. |

## Generation And Publication Rules

The producer is [CollectionDocsBuilder](../../../docs-viewer/build/docs_builder/collection.py), using [docs_document_subjects.py](../../../docs-viewer/services/docs_document_subjects.py). Works always enables scalar Subject projection, including for empty builds; Catalogue does not. Other collections enable it through configured Subject support or recognized declarations in input documents. Current configuration/data enables only Works. Saved management-manifest generation also participates in targeted reconstruction. Targeted builds reject retired or malformed saved Subject metadata and require a complete collection Build rather than converting unselected rows. Required projection never depends on an obsolete file's presence.

The builder writes manifests only when their serialized bytes change. `subject_generation` remains a deterministic hash of collection identity and per-document scalar Subjects, including unassigned document IDs. It is not a receipt for document content, Catalogue state or composed URLs. Project State retains this field in its report generation. There is no cross-file receipt or membership comparison.

Working subjects include draft documents independently of publication readiness. Publish selects documents using explicit `draft`, ordinary `unpublishable.json` exclusions and inherited exclusions; exclusion of a collection's report host excludes the collection. [Preview preparation](../../../docs-viewer/services/docs_prepare_preview.py) rebuilds that eligible set in isolated temporary storage.

The configured Works publication owner removes authoring subject fields and retains only a valid Work declaration. Folder declarations are omitted; invalid, conflicting and retired Series declarations fail before projection. This specialization belongs to Works; other collection source fields are not globally stripped. Preview removes other Working collection customisations while retaining Works' derived Work-subject support.

The temporary publication builder resolves each public Context row's selected thumbnail: authored assignment emits `has_thumbnail: true` and omits `subject`, otherwise a Work declaration emits scalar `subject` and omits `has_thumbnail`, otherwise neither field is emitted. Management metadata can retain both independent assignments. The public list describes thumbnail selection and is not a complete Work-association inventory; it exposes no Folder values. By-ID rendering inputs and both media owners remain independent of this list projection. [Media And Asset Handling](../Media_And_Asset_Handling.md#assigned-document-thumbnails) owns storage, configured routes and presentation. Shared runtime projection does not update public document data; a new Publish must pair the runtime with the new public manifest before release.

[Snapshot assembly](../../../docs-viewer/services/docs_preview_snapshot.py) excludes management manifests and retains the existing reader payloads. [Repository distribution](../../../docs-viewer/services/docs_deploy_repo.py) consumes that completed snapshot. Neither operation has association-file handling. Search rebuilding remains separate.

## Active Consumer Owners

| Owner | Input And Responsibility |
| --- | --- |
| [Catalogue Works report](../../../docs-viewer/runtime/js/reports/catalogue-works-report.js) | Reads generated Work/Series report metadata and composes definitive Catalogue document links from each Work ID and the configured report host. The separate document-link reader is retired. |
| [Working collection subjects](../../../docs-viewer/runtime/js/management/docs-viewer-management-collection-working-subjects.js) | Context's document-detail Subject information, Work/Folder/None assignment and Folder-only Finder action. It does not contribute list rows or consume a private title map. |
| [Shared collection browsing](../../../docs-viewer/runtime/js/shared/docs-collection-browsing.js) | Classifies scalar Context Subjects and selects Work alternatives only when no authored thumbnail is assigned, using the configured Catalogue policy/base. No per-row Catalogue-record read or media probe. |
| [Project State producer](../../../docs-viewer/services/docs_project_state.py) | Groups valid Works management rows, then places documents through Folder or Work identities and derives Series membership from canonical Works. Invoked by Run/Refresh through `/docs/project-state`. |
| [Works coverage report](../../../docs-viewer/runtime/js/reports/works-report.js) | Retains Studio Series rows and joins documents through exact member-Work subjects. Folder and None supply no coverage; direct Series subjects are unsupported. |

## Artifact Retirement

Obsolete association files were removed from configured Working and Preview collection document owners. Cleanup preserved source, registrations, media, reader manifests, management manifests and unrelated output. Changing Preview bytes invalidates its completion receipt; the receipt was already absent at the association-file cutover. Subsequent explicit Publish operations rebuild and verify the completed snapshot through the ordinary publication owner.

Context's Subject column and its private `reports/works/manifest.json` reader/generator were retired on 2026-10-03. Series-subject retirement then removed the picker choice, field support, detail label/icon and direct report placement branches. Working source inspection found no Series declarations; its 244 Context rows contained 24 Work, 208 Folder and 12 None subjects. The existing complete Works docs-only dry-run rendered all 244 documents with zero proposed writes/removals, zero manifest changes and zero warnings, so no generated reconciliation was required. Tests and browser review remain separately scoped; no test or fixture was changed for this retirement.

The scalar cutover on 2026-10-05 retired generated authoring-subject objects and their production readers together. One complete Working Works docs-only build reconciled its 244 rows without source/media writes or by-ID changes. The current manifest has 25 Work, 208 Folder and 11 unassigned Subjects; one Work-subject row retains an independent authored-thumbnail flag. Public manifest data still requires a separately authorized Publish and user review. Older test fixtures still refer to retired representations; they were neither run nor changed and do not establish scalar-contract coverage.

## Questions For The Relationship Review

- Should a document's related links include other documents declaring the same exact subject, documents directly linked in its body, and documents reached through semantic-token references? Which Catalogue relationships should contribute?
- Should the UI show one destination once when several derivations find it, and what ordering or grouping would make that list useful?
- Can one presentation consume a consistent relationship projection while retaining derivation, direction, and exact identity for maintenance and explanation?
- Which relationships are useful publicly, and which depend on private subjects or local actions? Manage URLs and folder subjects need an explicit public/private boundary.
- Should collection-specific subject representations and exact Catalogue navigation remain separate projections of a shared model? Their current validation and cardinality requirements differ.

Review semantic-token data, document-link data, and their UI actions against the same purpose/action/consumer/rules structure before deciding the target model. No consolidation implementation or broader data migration is specified here.

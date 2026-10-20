---
draft: false
doc_id: d-20260927-135604-05446e
title: Subject Associations
added_date: "2026-09-27 13:56:04"
last_updated: "2026-10-20"
summary: Manifest-owned subjects, in-memory report associations, exact navigation, and private/public generation boundaries.
parent_id: d-20260423-000000-d015e6
---
# Subject Associations

## Purpose And Review Boundary

This is the current-state inventory for document Subjects and their derived report associations. On 2026-10-03 Series was retired as a document Subject after the user reassigned every remaining declaration. Work, configured Folder and None are the supported choices. Record each data product's purpose, the UI actions that read or change it, its consumers, and its update/publication rules. Use the same questions when reviewing semantic tokens, document links, and their UI actions.

Reports derive associations in memory from optional scalar `subject` fields in each subject-enabled collection's private `manage-manifest.json`. Projects captures its required metadata during explicit Refresh and composes placements from its own saved report snapshot. An explicitly declared subject maps to the documents about that subject. The former `subject-associations.json` product is retired from every collection: no producer, generated-data read allowance, Preview validation or distribution branch remains. Projects' snapshot contains report input facts, not a replacement Subject lookup or persisted placements. Subjects do not collect semantic-token references, Markdown links, or all documents related through Catalogue membership.

The proposed UI idea is to present document relationships as **related links**, regardless of how they were derived. That is an exploration aim, not an implemented or agreed replacement model. This document records current behavior separately from questions for that review.

Catalogue remains a registered document collection. On 2026-10-03 the user retired the superseded proposal to remove Catalogue documents. Subject retirement does not change Catalogue Work IDs, Studio Series, Work-to-Series membership, report Series columns or Catalogue ownership.

## Key Data Files

All workspace paths below are relative to the configured `$DOTLINEFORM_DOCS_BASE_DIR`. [Workspace configuration](../../../docs-viewer/config/workspace/docs-workspace.json) resolves storage and collection ownership; these are external workspace files, not repository-owned generated documents.

| File | Purpose And Authority | UI Actions And Consumers | Update And Publication Rules |
| --- | --- | --- | --- |
| `working/source/collections/<collection>/documents/*.md` | Canonical document identities and configured subject declarations. Catalogue uses Work ID as `doc_id`. | Source/Regenerate retain their configured authoring owners. | Working generation prepares public artifacts and queues completed effects. Canonical Markdown is not distributed. |
| `working/generated/collections/<collection>/documents/manage-manifest.json` | Private `docs` list with optional scalar `subject` when projection is enabled. Subject omission means None. An independent `has_thumbnail: true` records an authored thumbnail, including when a Subject is present. Catalogue does not project document Subjects. | Projects' Folder/Work placement, Works' Work-derived Series coverage and Context Work-thumbnail selection. Source assignment and Finder read the unsaved buffer through Source context. Catalogue browsing uses its Work-ID `doc_id` directly. | Collection builds maintain the rows. Targeted builds merge selected rows with validated saved rows, preserving unselected metadata. Excluded from the completed Preview snapshot and public distribution. |
| `preview/collections/<collection>/documents/manifest.json` | Public-reader identity/title/date list with authored thumbnail or Work-only Subject selection. | Public collection readers consume the chosen thumbnail field. | Upstream generation prepares the finished public manifest under Working publication output; Publish transfers queued bytes to Preview/public destinations. |
| `working/generated/reports/projects/metadata.json` | Private Projects snapshot of physical folders, Context IDs/titles/Subjects and refreshed Work/Series facts. | Projects reads it on opening and composes Subject-based placements in the browser. | Only Projects Run/Refresh gathers and replaces it; document/Catalogue changes wait for that action. It has no publication output. |

Catalogue Works' private `working/generated/catalogue/reports/catalogue-works/metadata.json` supplies Work/Series display and search data. Each Work's definitive Catalogue document uses that exact Work ID as `doc_id`; the report composes its destination using the configured report host and existing route helper without reading a document manifest. Studio Work Save updates canonical records and the editor; Refresh Catalogue updates report metadata, while Catalogue Regenerate maintains the linked documents. [Catalogue Works](../Catalogue_Works.md) owns that distinction. Local and public browser configuration expose Catalogue's exact `report_host_doc_id`, without inferring a host from the current route or document tree.

## Subject And Association Shape

The recognized canonical declarations remain `work_id` → Work and `folder_path` → Folder. A document may declare at most one Subject. Generated management rows and committed response records project a string `subject` or omit it for None. They never emit an empty string, `null`, a None sentinel or a kind/key object. Present malformed values and the retired generated `authoring_subject` field fail validation without conversion or aliases. Multiple source declarations, invalid values and unsupported Folder declarations also fail. Document `series_id` fields are rejected even when blank; obsolete assignment field sets remain rejected. Studio Work `series_id` remains a separate Catalogue membership field.

Exactly five ASCII digits identify a Work, retaining leading zeros such as `"00635"`. Other valid decoded relative targets identify Folders when the exact collection supports them, such as `"projects/100 grasping hands"`. A source Folder declaration whose normalized target is bare five ASCII digits fails because that scalar form is reserved for Work identity. Folder normalization retains existing path safety: no absolute paths, backslashes, control characters, URL schemes, local-link markup, empty segments or traversal segments. Normalization checks neither Work registry membership nor folder existence, and never infers identity from titles, filenames, body text, selected rows or route context.

Subject-enabled management manifests contain immutable `doc_id`, presentation metadata and optional scalar `subject`. [Python Subject ownership](../../../docs-viewer/services/docs_document_subjects.py) and the [shared JavaScript classifier](../../../docs-viewer/runtime/js/shared/docs-document-subject.js) validate/classify that single input; consumers may derive ephemeral `{kind, key}` values for their own domain behavior. Project State captures scalar management metadata during Refresh and composes its in-memory placements in the browser, keeping every matching document and using the existing exact Works viewer-link owner and title/ID ordering. Opening reads its saved snapshot; committed edits do not update its results until Refresh. Catalogue has no Subject projection or separate Work-to-document association: navigation uses its five-digit `doc_id` directly. There is no publishing-stage discriminator or persisted association payload. Source-field groups retain their own assignment identity and are not aliases for retired generated metadata.

Projects first scans every immediate physical project folder and retains unmatched folder rows. Work-subject documents are placed through their Work's canonical project folder and Series membership. Folder-subject documents are placed at the declared folder and may appear against every Series represented by Works there; that association is broader than an explicit Series declaration. The Works coverage report derives Series documentation through member-Work subjects only. Both reports keep plain-text Series columns, while their Docs cells retain exact document links.

Several documents may share a subject. That is valid for Project State. Every current Work requires one definitive Catalogue document with its Work ID as `doc_id`. A direct link loads that exact by-ID payload before any list manifest; a missing document is a destination error to repair through Regenerate, without a guessed target or old-ID alias.

## UI Action Map

| UI Action | Effect On Subject Data | Completion Or Freshness Boundary |
| --- | --- | --- |
| Source → Directives → Assign Subject, including clearing it | Applies the exact document's configured Subject field group to the unsaved Source buffer. | A write-free context request validates/prepares the change; Apply changes only the current buffer. Save owns source persistence and exact document/Links generation. Work and None are supported; Folder follows the exact collection's registered authoring fields and canonicalises input through its existing metadata owner. |
| Source → Directives → Open Subject folder | Opens the current buffer's valid Folder subject beneath the configured Projects root in Finder. | Menu opening reads the write-free Source context; Work, None, unsupported documents and invalid source leave the item disabled. Activation awaits the existing local-link service without writing source or generated data. |
| Open Source and edit canonical Markdown | A declaration change updates normalized subjects in the management manifest. | Application Source Save awaits the exact document build and fresh display; external edits require explicit Rebuild. |
| Source Editor Save | Saves validated source and supplies scalar committed metadata, including independent Subject and authored-thumbnail assignments, to retained readers. | Save awaits persistence, exact document/Links generation and fresh display. |
| Working document Build or collection document rebuild | Recomputes normalized subjects in manifest rows. | A successful build owns the result. Targeted collection builds use merged saved metadata, preserving unselected documents. |
| Collection Regenerate | Rewrites collection-owned generated source and rebuilds document outputs and manifests. | Source regeneration and its owning rebuild are separate from Studio Work Save. |
| Document create, import, or delete with collection rebuild follow-through | Adds or removes exact manifest rows. | The source operation's collection build owns reconciliation. |
| Publish | Consumes completed document/media/shared effects without source reads or projection. | One awaited action; private management/association data is excluded upstream. Git/public deployment remain separate. |
| Open Catalogue Works | Reads private report metadata and composes Work ID/title links from each Work ID and the configured Catalogue report host. | No Catalogue document-manifest or mapping read; direct destinations load exact by-ID content. |
| Open Context (Working Works collection) | Uses the shared title/draft/selection list with authored thumbnails first, then existing Catalogue Work thumbnails for Work-subject rows. Assign Subject and Open Subject folder belong to Source; the former Document Info contribution is retired. | Committed Source Save changes reevaluate the retained row in memory, preserving filtering, sorting, paging and exact navigation. No Subject column or private Catalogue title-file read. The assignment picker reads generated Work targets through its separately owned Catalogue provider. |
| Project State Run/Refresh | The service reads Works' management manifest and Refresh-owned Catalogue inputs and scans immediate project folders, then saves and returns its private metadata snapshot; the browser classifies subjects and composes placements/counts. | Opening reads only the saved snapshot. Committed document/Catalogue changes wait for explicit Projects Refresh; no build or input repair occurs. |
| Follow a document link or open a Series gallery | Uses the exact destination or the separate Media View owner. | Navigation only. |

## Generation And Publication Rules

The producer is [CollectionDocsBuilder](../../../docs-viewer/build/docs_builder/collection.py), using [docs_document_subjects.py](../../../docs-viewer/services/docs_document_subjects.py). Works always enables scalar Subject projection, including for empty builds; Catalogue does not. Other collections enable it through configured Subject support or recognized declarations in input documents. Current configuration/data enables only Works. Targeted builds reject retired or malformed saved metadata and require a complete collection Build rather than converting unselected rows. Required projection never depends on an obsolete file's presence.

The builder writes manifests only when their serialized bytes change. Collection manifests contain exactly one root `docs` field; the unused `subject_generation` hash and `customisation` envelope are retired. Reports consume completed rows directly. Project State's former `docs_project_state_report_v5` envelope is retired: its local service supplies scan time, folders, document metadata and saved Work/Series facts, with no generation hashes, report summary or assembled row audit. [Reports](../Reports.md) owns the current handoff and browsing lifecycle. The Works server registration still owns Subject authoring, validation and publication preparation; it supplies no browser descriptor or manifest extension. There is no compatibility shape or cross-file receipt comparison. A complete Works docs-only build reconciles the former manifest before targeted operations resume.

Working subjects include draft documents independently of publication eligibility. [Public preparation](../Builder.md#publish-preparation) applies draft, saved unpublishable and inherited collection-host eligibility upstream. Catalogue intrinsic eligibility and Work/media ownership remain separate.

The configured Works publication owner removes authoring subject fields and retains only a valid Work declaration. Folder declarations are omitted; invalid, conflicting and retired Series declarations fail before projection. This specialization belongs to Works; other collection source fields are not globally stripped. Preview removes other Working collection customisations while retaining Works' derived Work-subject support.

The existing collection public projector resolves Context's selected thumbnail: authored assignment emits `has_thumbnail: true`, otherwise a Work declaration emits scalar `subject`, otherwise neither. Management metadata can retain both independent assignments. Public rows expose no Folder values and are not a complete Work-association inventory. Public preparation retains the finished rows; Publish transfers their queued manifest.

Public preparation excludes management/association artifacts. [Selected publication](../../../docs-viewer/services/docs_selected_publication.py) transfers queued reader bytes without projection or content validation. Search rebuilding remains explicit.

## Active Consumer Owners

| Owner | Input And Responsibility |
| --- | --- |
| [Catalogue Works report](../../../docs-viewer/runtime/js/reports/catalogue-works-report.js) | Reads generated Work/Series report metadata and composes definitive Catalogue document links from each Work ID and the configured report host. The separate document-link reader is retired. |
| [Source editor](../../../docs-viewer/runtime/js/management/source-editor/source-editor.js) and [Subject modal](../../../docs-viewer/runtime/js/management/source-editor/subject-modal.js) | Current-buffer Folder/Work/None assignment and Folder-only Finder action through write-free Source context. The former Working collection Subject contribution and unused Document Info projection are retired. |
| [Shared collection browsing](../../../docs-viewer/runtime/js/shared/docs-collection-browsing.js) | Classifies scalar Context Subjects and selects Work alternatives only when no authored thumbnail is assigned, using the configured Catalogue policy/base. No per-row Catalogue-record read or media probe. |
| [Project State metadata owner](../../../docs-viewer/services/docs_project_state.py) and [browser composition](../../../docs-viewer/runtime/js/reports/project-state-data.js) | Opening reads only Projects' saved snapshot; Run/Refresh reads saved Working inputs and scans physical folders once before saving new metadata. The browser places Folder/Work subjects and derives Series membership from captured Work facts, without committed-document updates. |
| [Works coverage report](../../../docs-viewer/runtime/js/reports/works-report.js) | Retains Studio Series rows and joins documents through exact member-Work subjects. Folder and None supply no coverage; direct Series subjects are unsupported. |

## Artifact Retirement

The 2026-10-11 report simplification retired the manifest customisation envelope, Subject hash, Project State report hash, browser descriptors/loaders and unused collection extension hooks. Changed-owner lint and Python syntax passed. One complete Works docs-only build replaced its management manifest for 235 documents, with no by-ID or Links writes/removals and no warnings. Direct current-data production readers produced 205 Project State folder rows and 140 Work Document Coverage Series rows, 20 containing documents. Public code projection/check, site validation and bounded source review completed. This evidence does not exercise HTTP/browser transport, tactile controls, failure paths or synthetic edge cases. Existing Subject, Project State and collection tests still contain retired hash/envelope contracts; they remain unreviewed, unchanged and unexecuted under separate test-work approval. Restart Docs Viewer services and reload the viewer to adopt the revised producer/reader together.

Obsolete association files were removed from configured Working and Preview collection document owners. Cleanup preserved source, registrations, media, reader manifests, management manifests and unrelated output. Changing Preview bytes invalidates its completion receipt; the receipt was already absent at the association-file cutover. Subsequent explicit Publish operations rebuild and verify the completed snapshot through the ordinary publication owner.

Context's Subject column and its private `reports/works/manifest.json` reader/generator were retired on 2026-10-03. Series-subject retirement then removed the picker choice, field support, detail label/icon and direct report placement branches. Working source inspection found no Series declarations; its 244 Context rows contained 24 Work, 208 Folder and 12 None subjects. The existing complete Works docs-only dry-run rendered all 244 documents with zero proposed writes/removals, zero manifest changes and zero warnings, so no generated reconciliation was required. Tests and browser review remain separately scoped; no test or fixture was changed for this retirement.

The scalar cutover on 2026-10-05 retired generated authoring-subject objects and their production readers together. One complete Working Works docs-only build reconciled its 244 rows without source/media writes or by-ID changes. Its reconciled manifest contained 25 Work, 208 Folder and 11 unassigned Subjects; one Work-subject row retained an independent authored-thumbnail flag. The user subsequently confirmed successful Publish and accepted the local/public result on 2026-10-05. Older test fixtures still refer to retired representations; they were neither run nor changed and do not establish scalar-contract coverage.

## Questions For The Relationship Review

- Should a document's related links include other documents declaring the same exact subject, documents directly linked in its body, and documents reached through semantic-token references? Which Catalogue relationships should contribute?
- Should the UI show one destination once when several derivations find it, and what ordering or grouping would make that list useful?
- Can one presentation consume a consistent relationship projection while retaining derivation, direction, and exact identity for maintenance and explanation?
- Which relationships are useful publicly, and which depend on private subjects or local actions? Manage URLs and folder subjects need an explicit public/private boundary.
- Should collection-specific subject representations and exact Catalogue navigation remain separate projections of a shared model? Their current validation and cardinality requirements differ.

Review semantic-token data, document-link data, and their UI actions against the same purpose/action/consumer/rules structure before deciding the target model. No consolidation implementation or broader data migration is specified here.

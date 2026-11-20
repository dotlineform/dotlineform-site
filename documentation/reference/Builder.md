---
draft: false
doc_id: d-20260423-000000-c9f3ea
title: Builder
added_date: "2026-04-23 00:00:00"
last_updated: "2026-11-20"
parent_id: d-20260424-000000-50b63f
---
# Working generation and publication

Working generation turns configured Markdown and ready media into reader output, projects public eligibility and queues completed effects. Publish applies those selections to Preview and configured destinations. Deploy Public releases the committed `site/` snapshot. [Source organisation](Source_Organisation.md#storage-and-roles) · [Reader payloads](Generated_Data_Contracts.md) · [Publish and deploy](../guide/Publish_And_Deploy.md)

## Commands

From the repository root, use the project Python. For an external Markdown edit, rebuild the exact document. Add `--collection <id>` for a named collection.

```bash
python3 docs-viewer/build/build_docs.py --stage working --only-doc-ids <doc-id> --skip-media-builds --write
python3 docs-viewer/build/rebuild_working.py --write
python3 docs-viewer/build/build_search.py --stage working --write
```

The second command is **Full Working Build**, the maintenance operation that includes documents, referenced ready-media checks, Search and Recent. It requires `--write`. The first and third commands default to dry run without `--write`. A complete build for one owner uses `build_docs.py` with no ID selector. A standalone complete ordinary Build can update Recent from saved portfolio metadata. Search has its own whole-index command. `build_docs.py --diagnostics` adds machine-readable diagnostics. CLI document writes normally also regenerate browser configuration. [Document CLI](../../docs-viewer/build/docs_builder/cli.py) · [Full Working CLI](../../docs-viewer/build/rebuild_working.py) · [Search](Reader_Discovery_And_Return.md#payload-contract)

## Docs Build Flow

| | Exact document build | Full Working Build |
| --- | --- | --- |
| **Example** | Edit an ordinary page's title and body externally, including its full `last_updated` timestamp, then use Edit doc → Rebuild or select its ID on the CLI. | Change a shared renderer that affects the configured corpus, then run `rebuild_working.py --write`. |
| **Inputs** | Read the exact saved source and merge its metadata with the loaded tree or collection manifest. Source Save instead supplies its already prepared record. | Load canonical ordinary and non-Catalogue collection sources across configured owners, source order, Book placement and ready media. Catalogue Work generation stays with Regenerate. |
| **Working output** | Update the page's by-ID payload and changed metadata. Complete its Links and exact direct dependencies. The page keeps its saved source and dates on Rebuild. Search and Recent stay as saved. | Build the workspace relationships before rendering. Generate non-Catalogue documents, handle stale payloads and exact dependencies, update changed Selected, then generate Search and Recent from shared discovery inputs. |
| **Eligibility and queue** | If eligible, select the exact document and its referenced ready media for explicit Rebuild, along with any affected public metadata or dependent documents. Source Save selects new or changed media instead. If the edit removes eligibility, queue exact withdrawals. | Compare new eligibility with the saved public lists. Queue changed or restored documents, withdrawals and changed shared output. A changed referenced file can select its document even when the generated document bytes are unchanged. |
| **Publish** | Transfer the selected document/media and changed shared metadata. The existing Search/Recent files change only if another completed operation queued them. | Transfer the queued document and shared effects, including changed Search and Recent files, and clear each successful unit. |

### Exact generation

Management `POST /docs/rebuild-document` resolves one saved source and awaits its document/Links output and queue handoff. This is useful after an external edit or when a saved document needs rerendering. An exact CLI build reads only selected sources, using canonical `index-order.json` to determine ordinary placement and carrying unchanged saved navigation or manifest rows. Direct dependencies can include documents whose relationship record changed, restored public documents, and a Book host whose TOC or reading order changed. Generation follows those supplied targets without recursively walking related documents.

Local by-ID and management output can complete before a failed public handoff. Use the reported owner, ID, filename and phase to diagnose the failure. For `build_docs.py`, exit 3 means local generation completed with an incomplete publication handoff. After correcting the prerequisite, rerun the owning build. [Exact Rebuild service](../../docs-viewer/services/docs_document_rebuild.py) · [Generation orchestration](../../docs-viewer/services/docs_generation.py)

## Document Relationship Maintenance

The Links owner updates the selected document's authored outgoing edges and known neighbours' incoming edges before rendering. Ordinary authored links and supported Catalogue Work references contribute exact `{collection, doc_id}` destinations. Saved version-5 records live in `working/generated/documents/links-by-id/<doc_id>.json`. Each has `schema_version`, `self`, `incoming` and `outgoing`, with `collection`, `doc_id` and `title` on an endpoint. Outgoing rows also carry `explicit_doc_link`, true when any ordinary authored link reaches the destination. Records appear when relationships need them. Repeated targets are one edge, and deletion removes the saved record and known edge contributions. The separate Links report refresh and Broken Links audit have their own actions.

Related Links renders the already refreshed records into by-ID output. Build can render exact direct neighbours, including a Catalogue document whose incoming links changed. Dependency-only Catalogue documents use the Docs queue. Work media and Work-queue selection stay with Catalogue Regenerate. Public eligibility decides which bodies go out, while authored relation destinations can still be listed. [Related Links](Related_Links.md#generated-data-and-freshness) · [Links builder](../../docs-viewer/build/docs_builder/links_builder.py)

## Publish Preparation

Generation uses authored readiness, the configured tree and collection hosts, and one read of `working/source/unpublishable.json`. Ordinary `draft: true` and ignored ordinary IDs prune their branches without promoting descendants. A collection whose ordinary host is excluded has an empty eligible manifest. Authored collection drafts are withheld and Book projects its web edition from saved placement and readiness. Catalogue has intrinsic Work-document eligibility, subject to its host, with Catalogue media and canonical Work data owned separately. Management output retains authored membership. [Eligibility owner](../../docs-viewer/services/docs_publication_metadata.py) · [Book source and provenance](Source_Organisation.md#book-source-and-provenance)

The saved public tree and manifests supply the prior membership. An eligible changed document becomes a current selection. Losing eligibility queues a withdrawal, including previously eligible descendants or collection documents as applicable. Restoring an eligible branch selects its required document bodies and current media. A Draft or policy withdrawal preserves the Working source and owned media. Explicit Delete and saved-reference removal can additionally select exact owned file removals. [Media ownership and removal](Media_And_Asset_Handling.md#saved-ownership-and-exact-removals)

`working/docs-publish-pending.json` uses `docs_publish_pending_v1` and carries current/deleted document maps plus current/deleted shared outputs by owner. Document IDs are exact; collection and selected `media` or `removed_media` identify supplied effects. Shared keys select prepared navigation, manifests, Selected or changed discovery artifacts. Later completed effects merge with pending selections and cancel a superseded write or an exact removal restored with ready bytes. The operation saves the queue before applicable Working media unlinks. [Queue owner](../../docs-viewer/services/docs_publication_queue.py)

## Working Rebuild

Use Full Working Build for a corpus-wide renderer/configuration change, persistent referenced media edits or intentional reconciliation. It reuses loaded source records for the ready-media checks, links, document generation and discovery. The maintenance media comparison reads exact referenced Working and Preview files for otherwise unchanged eligible documents. A missing or differing Preview file selects the document and its referenced media. Missing Working input fails at its owner.

Full Working Build can regenerate a missing `working/generated/documents/index-tree.json` from the complete ordinary source and canonical Index order. Exact ordinary generation uses the saved tree to carry forward unselected rows. A missing management manifest for an exact collection build can call for complete collection reconciliation. [Full Working owner](../../docs-viewer/services/docs_working_rebuild.py) · [Generation inputs](../../docs-viewer/services/docs_generation.py)

Before its first write, Full Working Build reads the existing Docs publication queue, prepared public ordinary tree and prepared public manifests for the collections it rebuilds. Later eligibility comparisons reuse those views. Selected Catalogue dependencies read their own inputs. Restore missing publication state from a matching workspace backup before retrying. [Preparation inputs](../../docs-viewer/services/docs_publication_preparation.py) · [Workspace restore](Local_Setup.md#restore-the-docs-workspace)

Completed generation can persist document/shared effects before later phases run. Recent is queued before Search, and changed Search scopes are queued as written. Browser settings are regenerated near the end. `working/generated/build-manifest.json` records successful complete maintenance as `docs_working_build_v1` with `schema_version`, `stage` and `completed_at`. After invalidation, a later failed phase leaves no new receipt while completed files and queue selections remain available for inspection. Reload the reader after a successful maintenance run. [Recent payload](Generated_Data_Contracts.md#recent-contract) · [Discovery projection](../../docs-viewer/services/docs_discovery_selection.py)

## Preview And Deployment Boundary

**Actions → Publish** invokes one awaited empty-object `POST /docs/publish`. The publication phase reads both queues and applies Catalogue Work units, Docs document/media and shared effects, then Catalogue shared output. For selected Catalogue rendering it uses adopted Working Work data. Each unit applies its supplied files/removals to Preview and repository/R2 destinations and clears after successful verification. A missing selected media file blocks its write unit. An already absent removal target is complete. Empty queues skip transfers and proceed to the Git backups. Build, eligibility and discovery have their own owners upstream.

A transfer failure stops at the reported phase and target. Completed effects stay in place, and failed or unprocessed selections stay pending. Correct the owning input or destination and rerun Publish for the remaining selections. R2 effects occur during Publish. Review the site repository with `bin/site-preview` before running Deploy Public manually. [Publish owner](../../docs-viewer/services/docs_publish.py) · [Docs transfers](../../docs-viewer/services/docs_selected_publication.py) · [Catalogue transfers](Catalogue_Save_And_Refresh.md#per-work-publish)

After successful publication, Publish stages changes under `working/source/` and `working/assets/media/` and in the three Working queues. This covers saved drafts. It commits and pushes those changes to `main` in the private Docs data repository.

The site backup separately commits and pushes changes to the five canonical Studio Catalogue JSON files and the published output under `site/assets/data/docs/`, `site/assets/data/catalogue/` and `site/assets/data/search/`. This includes Work thumbnails. The site backup checks outgoing commits and stops if they touch other paths. Site code and runtime releases follow the ordinary review workflow.

Publish awaits both backups, including when the publication queues are empty. Successful backups are silent. Each Git failure is reported separately after publication and identifies a new commit kept locally when its push failed. The next Publish attempts to push eligible local backup commits even without new file changes. [Backup owner](../../docs-viewer/services/docs_publish_backup.py) · [Workspace restore](Local_Setup.md#restore-the-docs-workspace)

## Source Contract

Common source fields include exact `doc_id`, `title`, `added_date`, `last_updated` and optional `summary`. Ordinary and non-Catalogue collection documents have an explicit boolean `draft`. Ordinary `ui_status` is display metadata. Catalogue source has fixed intrinsic eligibility. The configured owner determines collection membership, with ordinary placement owned by `index-order.json`. Save owns source timestamp changes. An exact Rebuild consumes the saved values. [Source Save](Source_Editing.md#post-docssourcesave) · [Document identity and dates](Document_Identity.md#date-provenance) · [Source forms](Document_And_Catalogue_References.md)

### Document Date

Use Source **Add date** or edit the front matter. `[[date]]` displays `date_display` when supplied and otherwise `date`. Enter ISO or day/month/year in the dialog. Two-digit years mean 2000–2099. The editable default display uses the year alone for January 1 when an approximate date is wanted. Put the exact date in the display when needed. Date tokens are plain text, and an empty standalone token omits its paragraph. [Source editor directives](Source_Editing.md#directives)

### Book Table Of Contents

Place `[[toc]]` on its own line in the configured Book host. The host owns its surrounding prose while Book placement and the web edition select the list. Exact generation updates the host when entries or reading order change. [Book placement and provenance](Source_Organisation.md#book-source-and-provenance) · [TOC renderer](../../docs-viewer/services/docs_book_toc.py)

### Summary Block

Place `[[summary]]` on its own line, or insert it from Source **Directives → Summary**. Front matter accepts a single scalar, quoted newline escapes or an indented literal block using `|` or `|-`. Use spaces and leave blank lines between paragraphs. Build trims outer whitespace, normalizes line endings and preserves internal breaks. Restricted inline emphasis and escapes render into `summary_html`; HTML, links, images and other syntax stay literal. The directive and a pinned Info panel reuse that completed fragment. Empty Summary emits neither optional field nor block. [Info Panel](Info_Panel.md) · [Summary formatter](../../docs-viewer/build/docs_builder/summary_formatting.py)

[Design rationale](../design/Working_Generation_And_Publication.md) · [Delivery evidence](../deliveries/Single_Publish_Delivery.md#later-workflow-boundary)

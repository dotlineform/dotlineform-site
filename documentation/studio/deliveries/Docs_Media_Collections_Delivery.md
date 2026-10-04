---
draft: true
doc_id: d-20261004-153253-12e8a8
title: Docs Media Collections Delivery
added_date: "2026-10-04 15:32:53"
last_updated: "2026-10-04 16:41:40"
summary: Extend Docs Media to collection media with saved metadata regenerated only by Run/Refresh, reading each document owner once.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Docs Media Collections Delivery

Status: complete. The user accepted the result and approved closeout on 2026-10-04. Docs Media opens its saved collection snapshot, excludes thumbnails, shows an empty list when metadata is missing, and displays the selected-collection orphan/total counts beneath the refresh time. The refresh button tooltip is **Refresh**. Durable behavior is documented in Media And Asset Handling; retain this completed delivery for recent-delivery lookup pending manual archive.

Complete result: local [Docs Media](/docs/?doc=d-20260812-212735-6d9cf3) opens a saved combined media snapshot without scanning sources or media. Its Run/Refresh action regenerates that snapshot collection by collection, reading each document collection once and collecting references only within its own media owner.

This delivery is parented to [Planned Features](../Planned_Features.md). [Media And Asset Handling](../Media_And_Asset_Handling.md#docs-media-inventory-report) owns the durable media/report boundary; [Development Checklist](../Development_Checklist.md) and [Development Workflow](../Development_Workflow.md) govern implementation and closeout.

## Requirements

- Include the ordinary workspace and every named collection registered in the Working workspace configuration when Run/Refresh executes. Discover owners and labels from configuration rather than hardcoding the current collection list; changes in collection registration enter the saved report on its next successful Run/Refresh.
- Inventory each owner's configured ready-media roles beneath `$DOTLINEFORM_DOCS_BASE_DIR/assets/media/workspace/` or `assets/media/collections/<collection>/`, including `img`, `svg`, `files` and `html` where registered. Skip every owner's configured `thumbs/` family because its files are derived and outside this report. Retain registered build-source coverage through its separate configured locations.
- Read only the selected owner's documents when collecting that owner's references. During Run/Refresh, read each document collection once, extract references through the shared source parser and store each owner's inventory/reference datasets in one combined snapshot. The browser joins these saved datasets into rows.
- Follow the supported authoring model: Add image/file stores media in the current document's ordinary workspace or collection, and managed Docs media tokens resolve within that owner. Cross-collection reference discovery is outside this delivery; the old broad live-reference reader and its routes are retired, and generation loads each owner's own documents directly through the existing source model.
- Exclude thumbnail files and references from saved metadata, report rows, counts and search. Apply this exclusion at the report-generation boundary; preserve thumbnail registration, storage, authoring and shared reference extraction used by publication and other consumers. Do not infer document associations from filenames or attach build-source references through matching output basenames.
- Preserve exact `{collection, role, media_type, identity}` targets throughout data validation, row combination and Finder activation. Equal filenames in different collections or roles remain distinct files. Document links retain exact collection/document identities and use the existing viewer route helper.
- Add a sortable **Collection** column and a collection filter with **All** selected by default. Label the ordinary owner **Ordinary docs** and named owners with their configured titles. Retain Type, File name, Documents, search, sorting, refresh and Finder behavior; make owner labels searchable and use deterministic ordering when other sort values tie.
- Opening or reopening the report reads only its saved metadata. Search, collection filtering and sorting operate on the loaded snapshot without source scans, media listing or metadata writes. Show the snapshot's last-refreshed timestamp when one exists; missing metadata shows an empty list without a first-run prompt or invented timestamp.
- Display `Last refreshed: DD/MM/YYYY, HH:mm` in browser-local time, followed by a blank line and `<orphans>/<total> orphaned files.`. Both counts reflect the selected collection, or All, independently of search/sorting; an orphan is a displayable file with no associated document in the saved snapshot. Update counts when the collection selection changes or is restored.
- Keep Run/Refresh busy until all required owner reads, data validation, snapshot writing and browser row assembly finish. A failed owner scan identifies that owner, leaves the previous saved file untouched and reports failure. Previously loaded rows may remain visible with their previous timestamp; partial new data must not be presented as a successful refresh. A write or response failure also reports failure, without automatic retry or a successful-refresh claim.
- Preserve present unreferenced files with a blank Documents cell. Missing referenced files produce no inventory row and remain within Broken Links' boundary. Continue omitting `.gitkeep` storage placeholders and exact `.DS_Store` basenames through their existing inventory/display owners.

The scope is registered Docs document media and build sources, plus one derived local report artifact. Catalogue Work primary images, Work thumbnails and downloads under the separately owned `assets/works/` families, Projects originals, arbitrary filesystem discovery, media deletion, source migration, incremental reference indexes and persistent process caches are outside this result. Run/Refresh writes only its report metadata; it does not Build documents, rebuild Search, Publish or alter sources or stored media.

### Saved Metadata And Freshness

Persist one `metadata.json` at `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/reports/docs-media/metadata.json`, selected by the required server-only `media_report_metadata` workspace configuration key. This is replaceable Working report output, owned by Run/Refresh, with no second root or repository fallback. Opening the report never creates storage or generates missing data.

The `docs_media_metadata_v1` data carries `refreshed_at` in UTC and `owners`, each with `collection`, `title`, `files` and `documents`. File targets carry `{collection, role, media_type, identity}`; referencing documents carry `{target: {collection, doc_id}, title, references}`. Retain generic data responsibilities on the server and browser-owned joins, display exclusions, ordering and rendering. Filesystem paths, credentials, rendered rows, presentation URLs and publishing-stage fields do not belong in this artifact. The saved read is `GET /docs/media-metadata`; generation is an empty-object `POST /docs/media-refresh`.

Missing metadata displays an empty table and `0/0 orphaned files.` with Refresh available, without a first-run prompt. Unreadable, malformed or unsupported metadata displays an error with explicit refresh recovery. Neither condition falls back to live scanning. A valid empty snapshot remains a successful empty report with its saved timestamp.

The report deliberately describes its last successful scan until the next Run/Refresh. Source saves, media operations, document deletion, watcher passes, ordinary document/Search builds and Publish do not regenerate it. Remove this report's live document-label/deletion reconciliation so loaded rows remain consistent with the displayed snapshot time. Navigation still opens the current exact document, and Finder activation validates that the saved file target currently exists; a deleted target may therefore fail until the next refresh.

Ordinary builds must preserve the separately owned report artifact. It remains private Working output and is excluded from Preview capture, public distribution, Search and document/package exports. Generate and validate the complete datasets before writing the single file; do not add per-owner partial writes, backup copies, rollback, transactional swaps, automatic freshness checks or automatic retries. If a write failure leaves invalid saved metadata, its next read reports that error and an explicit Run/Refresh is the recovery path.

## Deliverables

- [x] Load each owner's own document collection once and reuse shared source reference extraction; retire the previous live report reads without aliases.
- [x] Add a configured private report-artifact location, a saved-metadata read and an explicit Run/Refresh operation that enumerates configured owners, reuses inventory/reference helpers and writes one complete combined snapshot.
- [x] Skip all configured `thumbs/` families during report inventory and omit thumbnail references from the saved datasets without changing other thumbnail consumers.
- [x] Open the report through its saved-metadata read and assemble browser rows from per-owner saved datasets; source/media scans occur only within Run/Refresh.
- [x] Add collection presentation, filtering and sorting, including exact ownership and deterministic ordering across combined rows.
- [x] Add last-refreshed, missing/invalid-metadata and failed-refresh states; replace live label/deletion reconciliation with snapshot freshness. Missing metadata has no prompt; the button tooltip is Refresh.
- [x] Preserve exact document navigation and Finder targets, unreferenced-file visibility and the private artifact boundary.
- [x] Update [Media And Asset Handling](../Media_And_Asset_Handling.md#docs-media-inventory-report) to describe the delivered coverage, saved artifact and explicit refresh ownership.
- [x] Complete code review, focused verification and required shared stylesheet projection/static-site checks.
- [x] Record user acceptance and close the manual review gate.

## Process

1. Open Docs Media in the local viewer. Read and display its saved metadata and last-refreshed time; show an empty list if metadata is missing, or an error if it is invalid.
2. Choose Run/Refresh when a current inventory is needed. The local service processes the ordinary owner and then each configured named collection, listing that owner's media and reading its documents once through the existing helpers.
3. After every owner succeeds, validate and save the combined datasets to `metadata.json`. Return the newly saved data to the browser for row assembly without repeating the source scan or requiring a second metadata read.
4. Display the completed report with All selected initially, preserving current search/filter/sort choices on a subsequent refresh. Those controls operate on the loaded snapshot.
5. Open a linked document or reveal a file in Finder through the current exact-target actions. After source, media or collection changes, use Run/Refresh explicitly; reopening the report continues to show its saved snapshot.

## Delivery Steps

### DMC 0 Readiness

- [x] Confirm the supported media-authoring ownership, current configured-owner discovery and broad service/report boundaries against the current product.
- [x] Inspect active consumers of `/docs/media-files`, `/docs/media-references` and their shared helpers. Only this report consumed the live routes; shared inventory/source extraction remains available to other consumers.
- [x] Confirm the configured metadata path, saved-read and Run/Refresh write owners, plus preservation by ordinary builds and exclusion from publication/export. Inspect callers before retiring live routes made unused by the report change.
- [x] Confirm that the report retains local-only capability while exposing configured owner titles and exact targets. Identify represented shared stylesheet follow-through.
- [x] Select scoped lint, source/diff review, projection/static-site checks and one read-only production-data diagnostic under [Testing](../Testing.md) and [Test Contract Discipline](../Test_Contract_Discipline.md). No test work is included.
- [x] Confirm readiness and obtain code implementation approval before promoting the delivery to active.

Verification budget: read-only source/config inspection only. No executable tests, benchmark, prototype or production edits are needed for this gate.

Gate: stop for a demonstrated supported cross-owner consumer, missing configuration/storage authority, another lifecycle owner that would refresh/delete/distribute this artifact, or a requirement that would widen the report beyond registered Docs media and its single snapshot. Resolve that scope before implementation.

Record: requirements and implementation approval confirmed on 2026-10-04. Source/configuration review found no other production consumer of the old live report routes. Working Build completion inventories required an explicit report-directory exclusion; source capture and publication already select their own inputs and do not consume this report.

### DMC 1 Owner-Local Generation And Persistence

- [x] Load only each owner's source collection once per generation and reuse `source_media_references()` for body media. Omit thumbnail references returned by that shared helper.
- [x] Skip configured `thumbs/` inventories for this report while preserving shared inventory/reference capability for other consumers.
- [x] Keep the generic file listing, safe payload identities, selected-owner validation and exact document identities under their current owners.
- [x] Remove the broad cross-collection reference scan and fields or work made unnecessary by that change. Retain no compatibility layer for the previous coverage.
- [x] Implement the configuration-owned metadata location, validated saved read and explicit Run/Refresh writer. Process every configured owner once and serialize only complete generic datasets with their refresh time.
- [x] Handle missing metadata as empty data, invalid snapshots and owner-scan/write failures as errors; preserve the prior file on scan failure. Keep report reads free of generation and keep other builds/publication/export outside this artifact's lifecycle.
- [x] Retire unused report live-read routes/call paths within scope after inspecting their consumers; retain shared helpers where the snapshot generator or another active consumer uses them.

Verification budget: explicit-path Python lint and source review of the changed configuration/read/write owners and callers. If current-data evidence is needed, select one bounded diagnostic through the production helpers, recording coverage, cost and omissions before running it. A persisted-artifact diagnostic needs an explicitly isolated writable workspace and agreed write effects; this document does not authorize refreshing the real report, creating new assertion scripts or tests, or writing sources/media. No failure-branch coverage is implied by a successful current-data diagnostic.

Gate: generation reads each owner once and writes complete private metadata; saved reads perform no scan/write and return sufficient exact identities for the browser. Stop if an active caller genuinely requires a different ownership contract or another lifecycle can consume/delete this artifact unexpectedly.

Record: completed in `docs_media_metadata.py`, workspace configuration and management routes. The saved read returns `metadata: null` when absent. Generation validates complete owner datasets before its single direct write and returns those same datasets. Working Build inventories exclude the configured report directory. Explicit-path Python lint passed; a read-only production generator/browser assembly diagnostic found 497 display rows and 370 document links across Ordinary docs, Context, Concepts, Moments and Catalogue, with no thumbnail rows. The saved artifact was absent during that diagnostic and was not written by Codex. The diagnostic did not exercise persistence, failure branches or Finder effects.

### DMC 2 Combined Report

- [x] Mount from saved metadata and combine independently validated owner rows without filename collisions. Run/Refresh invokes the explicit generation/write operation and uses its completed returned snapshot.
- [x] Add Collection display/sorting/filtering and owner-label search through the existing report controls and styling owners.
- [x] Display the last-refreshed header and selected-collection orphan/total counts, plus missing/invalid-snapshot/refresh-failure states. Retain exact document/Finder targets and busy/error handling until the complete refresh result is displayed; missing metadata shows no prompt and the button tooltip is Refresh.
- [x] Remove automatic mount scans and live document-label/deletion reconciliation. Reopening, filtering or sorting must not trigger source reads, media listing or persistence.
- [x] Preserve the local/public boundary. Project the represented shared stylesheet change with `bin/site-code-update`, inspect its exact tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`.
- [x] Record user acceptance and closure of the manual review gate.

Verification budget: explicit-path JavaScript lint, bounded source/diff review and conditional projection/static-site checks. These checks address syntax, mount-versus-Run wiring, owner-key preservation, local capability isolation and tracked projection correctness; visual fit and interaction remain user review. No browser suite or test changes are included.

Gate: opening reads saved data, and only Run/Refresh generates and persists it. User manual review covers the initial empty list, last-refreshed time and header spacing, orphan/total counts across collection selection and unchanged by search, reopening the saved report, explicit refresh after a change, All/collection filtering, search/sorting, duplicate-filename clarity, thumbnail exclusion, document navigation, file reveal and error presentation. Record any pending manual gate explicitly.

Record: implementation and explicit-path JavaScript lint completed, including the final header/count change. The old shared three-column Docs Media selector was removed; its four-column layout, filter styling and header spacing are local-only. The sole public projection delta is that shared selector removal. Projection check passed with 102 represented files unchanged; static-site validation passed. The user accepted the result and approved closeout on 2026-10-04. Scenario-level manual results were not reported, and Codex performed no browser interaction or visual/Finder review.

### DMC 3 Code Review

- [x] Review the bounded code/config/documentation/projection delta for repeated document reads, automatic mount/freshness work, mixed-owner joins, duplicated parsing, stale callers, compatibility residue, partial writes/success claims and unintended publication/export coupling.
- [x] Confirm server helpers retain their generic inventory/reference behavior, the snapshot generator owns persistence and report-specific thumbnail exclusion, and the browser owns joins, ordinary display exclusions, ordering and document links.
- [x] Resolve findings and repeat only evidence affected by review changes.

Verification budget: source/diff review; reuse completed implementation evidence unless a finding introduces a concrete reason to rerun it.

Gate: resolve material findings before closeout. No unrelated cleanup or unapproved test work enters the delivery.

Record: review removed unused report-host IDs from the saved schema, required Working generation and an exact empty-object refresh request, retained exact collection/document routes and deterministic row tie-breaking, and confirmed that old live routes have no compatibility aliases. The report keeps loaded rows/time on failed refresh and displays no first-run prompt for missing metadata. Lint and the production-data assembly diagnostic were repeated for the affected final code.

### DMC 4 Closeout

- [x] Update the durable media/report owner with collection coverage, the configured saved artifact, selected-owner reference semantics, Run/Refresh ownership, explicit staleness and failure recovery.
- [x] Record completed evidence, user acceptance and remaining evidence limits.
- [x] Present the retain-or-retire recommendation for this delivery document, transferring lasting details to Media And Asset Handling. Retain this document pending an explicit archive/deletion decision.
- [x] Report code delivery separately from any later Publish, deployment, commit or push, each requiring its own explicit action.

Verification budget: document/source review and a bounded whitespace check; do not repeat implementation checks without a new reason.

Gate: the user accepts the combined report, material review findings are resolved, the durable owner is current and evidence limits are recorded. No document deletion occurs without approval.

Record: closed with user acceptance on 2026-10-04. Lasting details are in Media And Asset Handling, with configuration/report integration pointers updated. Retain this completed delivery and its Ad-hoc Deliveries link for recent-delivery lookup until manual archive. Code, lint, source review and projection/static-site evidence are complete; focused whitespace checks cover the closeout edits. Codex did not write the real report metadata or exercise persistence, browser/Finder behavior or failure recovery. No tests, Docs/Search rebuild, Publish, deployment, commit or push ran.

## Follow-on

None required for this result. Test migration, missing-reference rows, media cleanup, Catalogue-owned Work media and cross-collection media reuse require their own scope if later requested. Incremental snapshot maintenance, watcher/Build integration, background refresh and persistent process caching are separate future requirements; this delivery owns one explicitly regenerated saved report.

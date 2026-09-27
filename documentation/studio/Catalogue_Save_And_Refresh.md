---
draft: false
doc_id: d-20260927-223812-8042fc
title: Catalogue Save And Refresh
added_date: "2026-09-27 22:38:12"
last_updated: "2026-09-27 23:05:11"
summary: Target the existing Works editor as a hosted Docs Viewer view on one server; review migration order, reusable Save/Refresh separation and optional canonical by-ID storage before Related Galleries.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Save And Refresh

## Target: Host The Existing Works Editor

The target is the existing Works editor loaded into a view beneath the Docs Viewer top-row toolbar, served by one local HTTP server. Preserve its design, layout, controls, modals, editing behavior and domain services. Its own Series browser and Work panels remain the editor's interface; do not redesign it around the Docs Index and document views. The Docs shell owns the surrounding toolbar and view placement. A separate page route is not required.

The host owns entering, leaving and releasing the editor view, with the existing unsaved-change and busy-operation protections respected. The editor occupies the appropriate main area without having to fit the ordinary document/Index layout. Shared theme and outer chrome need one owner, while editor controls and workflows remain with their existing modules. Mounting, styles and cleanup must be reviewed as integration work; preserving user-visible behavior does not imply that the existing whole-page bootstrap can be imported unchanged.

The local server should compose Docs and Catalogue request handling and reuse the existing Catalogue services. This target removes the separate Studio HTTP-server requirement without recreating the editor's business logic in Docs controllers. Preserve exact write authority, request validation and local-only asset boundaries; the public Docs runtime must not acquire editor code or Catalogue mutation capability.

This hosting target is the intended direction. Canonical by-ID storage below remains an option rather than a prerequisite. The Save/Refresh boundary is reusable under either hosting or storage choice. Implementation and its delivery order still require review.

## Agreed Direction

**Save updates everything needed to keep the Works editor current. Everything else belongs to a separate explicit Refresh Catalogue operation.** Resolve and implement this boundary before [Related Galleries](Related_Galleries.md).

The Works editor must remain current throughout editing and after reopening. Generated readers may deliberately show the last refreshed Catalogue until Refresh completes. The canonical by-ID option below could make individual Working Docs records current directly after Save while leaving aggregate and derived views dependent on Refresh. This follows the existing separation between document editing and explicit Docs Search rebuilds.

This is a proposed change. [Catalogue Build And Lookup Refresh](Catalogue_Build_And_Lookup_Refresh.md) remains the durable authority for current implementation and will describe the new boundary when delivered. The current combined Save still performs consumer generation and lookup refresh.

## Ownership Boundary

| Operation | Required outcome |
| --- | --- |
| Save and definition mutations | Persist validated canonical Work/Series/Gallery data and exact memberships; return current records/revisions; update editor lists, pickers, labels, membership views and required image previews |
| Refresh Catalogue | Reconcile generated Work/Series/Gallery records, shared title/discovery lookups, private Docs report/subject metadata and retained exported lookups that are unnecessary for editor freshness |
| Public publication and media transport | Retain their existing separate owners; local Refresh does not imply publication, upload, commit or deployment |

Classify each existing output by its actual consumer. Any lookup genuinely required by the editor belongs to Save until its reader has an explicitly implemented alternative. An export unused by the editor does not belong to Save merely because the current completion chain writes it. Immediate freshness must come from canonical service responses and current editor reads, without requiring consumer JSON to have been refreshed.

Required editor media preparation, dimensions and version updates stay with Save under their existing owner. Metadata-only or membership-only changes should not trigger unrelated media work. Review generated-JSON dependencies in media completion before moving that JSON generation out of Save. Current Save has no R2 transport responsibility; this proposal does not introduce one.

## Option: Canonical By-ID Records In Working Source

Consider making individual Work and Series records canonical beneath the configured Docs workspace's `working/source/`, replacing the aggregate `works.json` and `series.json` authorities. Studio currently hosts the Works editor; Docs Viewer is the downstream Catalogue consumer. The proposal is one Catalogue authority in the Docs workspace, with Studio providing the editing and mutation service. Exact family directories and record schemas remain review decisions.

Save would write the exact canonical source record and complete editor freshness. Working Docs Viewer would read that source through its local reader rather than wait for regeneration of a separate Working consumer record. Titles, descriptive metadata and other directly stored values could therefore be available immediately after Save without making consumer generation part of Save. Public/Preview readers would still receive a prepared consumer projection that excludes private authoring fields and preserves the external workspace boundary.

The existing generated by-ID JSON cannot simply be promoted unchanged. It omits authoring fields such as project-media references, storage location and provenance, and includes calculated presentation data. Canonical records must retain the complete authoring information. Series member lists, related Gallery IDs, search/discovery indexes and copied labels remain derived data; define where Refresh owns these and how a reader combines them with current source. Storing a derived value per Work does not make it an independently editable source relationship.

| Concern | Aggregate canonical files | Canonical by-ID source option |
| --- | --- | --- |
| Selected Work read/save | Read the Works map; metadata changes replace the Works file | Read/write the exact Work file |
| Working Docs record freshness | Generated consumer record waits for Refresh under the proposed split | Direct source fields can be current after Save |
| Complete search, validation and rebuild | Load complete maps from a small number of files | Read the source inventory or use a deliberately maintained aggregate read model |
| Bulk changes | Replace the Works map once for its changed records | Coordinate multiple exact record writes |
| Derived relationships and public preparation | Require generation | Still require generation |

This option may remove an unnecessary Working copy and reduce selected-record I/O. It does not eliminate aggregate read models or automatically solve whole-Catalogue editor search, validation and bulk-write costs. Compare those dependencies and recovery behavior before choosing; no performance improvement has been measured.

Moving canonical records from their current Git-owned location into external Working source also requires an agreed history, backup and migration owner. Gallery definitions and exact membership storage must fit the same authority model; do not retain a second editable aggregate authority or add fallback reads between old and new storage.

The option changes the Refresh output set and freshness messages, so evaluate it within the Save/Refresh review before fixing the delivery scope. Keeping aggregate canonical storage remains a valid option. Neither choice is approved for implementation by this document.

## User Workflow

1. Edit and Save. The editor shows the saved values immediately, including affected browser/list and picker values. Unsaved edits and any incomplete editor/media step remain distinct from a confirmed canonical save.
2. Show a clear status such as **Saved · Catalogue refresh needed**. The status applies to the Catalogue, independently of the selected Work, and must remain meaningful after reopening.
3. Select **Refresh Catalogue** when downstream readers should receive current data. Run one awaited operation with visible busy, success or failure feedback. Keep editing unavailable while it runs.
4. On success, show the completed refresh state. On failure, preserve the saved canonical changes and report that consumer refresh is incomplete. Never imply that a failed Refresh lost a confirmed Save.

Use the same distinction for create, bulk edits, Series/Gallery definition changes and deletion. Until Refresh, a generated reader can retain an older title, membership or deleted record. This lag is intentional and must be clear in the UI. If the canonical by-ID option is selected, distinguish current individual source values from older aggregate or derived views rather than describing all Working Catalogue data as stale. A button and browser reload alone are insufficient unless they actually rebuild the owned reader data.

Refresh should cover its consumer outputs coherently from current canonical inputs. Choose complete versus targeted generation after reviewing actual cost and dependencies; the user-visible operation remains one Refresh. Do not assume a pending-publication ledger, background queue or automatic rebuild after every Save. The minimal freshness-status mechanism and recovery behavior are implementation decisions requiring review.

Docs Search keeps its independently owned explicit rebuild. Catalogue Refresh does not silently rebuild Docs documents or Search.

## Review Before Delivery

- Review hosting the complete existing editor beneath the Docs toolbar on one server, including boot/config adaptation, layout/style scope, event cleanup, view return and existing unsaved/busy behavior. Preserve the editor's design and workflow.
- Trace every Works editor read and mutation response, including lists, titles, memberships, reopening and media preview, and identify the minimum synchronous Save completion.
- Compare aggregate canonical storage with canonical Work/Series by-ID records in `working/source/`, including direct Working reads, derived-field ownership, bulk writes, complete validation and source history/recovery.
- Classify the existing generation, lookup, report-metadata and media calls against that boundary; remove editor dependencies on deferred outputs before separating them.
- Define the complete Refresh output set, its freshness indicator and visible partial-failure result. Review whether the existing separate maintenance commands can share one operation owner.
- Review whole-corpus projection and current/former Gallery co-member selection against the simpler Refresh boundary. Performance claims need evidence; a targeted write does not establish a small computation.
- Specify a bounded delivery and proportionate verification. Test creation or changes require a separately agreed specification; editor interaction remains a manual acceptance gate.

The earlier [Save And Targeted Publish](Catalogue_Save_And_Targeted_Publish.md) proposal remains deferred. Its pending-publication record, incremental Publish operation and older media assumptions are not requirements for this local Save/Refresh separation.

## Does Work On The Current App Advance The Target?

Judge each change by the owner that will survive the move. Existing Catalogue services already sit behind the Studio HTTP adapter, while editor behavior sits behind its page bootstrap. Hosting, operation ownership and canonical storage are separate changes; combining them all would make failures and behavior differences harder to attribute.

| Work | Contribution to the target |
| --- | --- |
| Make the existing editor mount/release as a hosted view and compose one local server | Directly delivers the intended hosting target |
| Separate canonical/editor Save completion from downstream Refresh in reusable Catalogue services | Advances the desired operation boundary and can survive the hosting move |
| Remove unnecessary Save-time exports or generation through that agreed boundary | Useful when it delivers the complete Save/Refresh outcome and remains independent of the current shell |
| Optimize the current server bootstrap, duplicate output or record-specific invalidation without an agreed destination | May need replacement during hosting or storage change; defer unless it fixes a current concrete problem |
| Change canonical storage to by-ID files in Working source | A distinct authority/storage migration; useful only if that option is selected, rather than automatically required by one server |

Save refactoring is therefore meaningful progress when it creates a reusable operation boundary. It does not itself deliver the hosted editor. Repeated adjustments to the current completion chain can still be wasted if they optimize outputs that the selected source model would remove. Prefer a complete, reusable slice over further isolated rebuild dependencies.

The recommended approach is to establish the hosting target with current data and Save behavior, then refine operations in that host. This moves the product to its intended home without simultaneously changing source authority and Save semantics. If review finds that a complete service-only Save/Refresh separation is independently worthwhile and simpler to deliver first, it can precede hosting, provided the same services are reused unchanged by the new host. A measurable current problem or a genuine hosting dependency should justify changing the order.

No whole-system rewrite is required. Preserve useful current behavior and services; retire the former dedicated server/bootstrap only when their replacement is accepted. Avoid transitional aliases, duplicate editable authorities and two competing Save/Refresh owners.

## Suggested Order

1. Confirm the target boundaries and review the hosting seams, editor data dependencies and canonical by-ID option. Choose bounded deliveries; do not begin speculative optimization while these choices remain unclear.
2. Recommended first implementation: host the existing editor beneath the Docs toolbar and compose one local server, retaining current canonical storage and Save behavior. Accept view switching and editor parity, then retire the replaced standalone host. A justified service-only Save/Refresh delivery may precede this as described above.
3. Deliver Save/Refresh separation through the reusable Catalogue services, with editor freshness and clear UI accepted. Update [Catalogue Build And Lookup Refresh](Catalogue_Build_And_Lookup_Refresh.md) to the implemented boundary.
4. If selected, deliver canonical by-ID storage as its own complete migration. Resolve that choice before optimizing storage-specific reads/writes; it is not automatically a gate for Related Galleries.
5. Resume Related Galleries after the Save/Refresh prerequisite, using the accepted host/data owners and resolving its explicit Gallery-to-Series association and IDs-only reader design separately.

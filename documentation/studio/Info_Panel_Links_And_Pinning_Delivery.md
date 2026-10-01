---
draft: false
doc_id: d-20260913-151251-cbee5b
title: Info Panel Related Links And Pinning - Delivery
added_date: "2026-09-13 15:12:51"
last_updated: "2026-10-01 17:31:33"
summary: Open an always-pinned document panel from the generated related-links section, showing only its title, optional summary and related list while the reader browses other documents.
ui_status: done
parent_id: d-20260902-102745-8379ea
---
# Info Panel Related Links And Pinning - Delivery

## Requirements

Deliver one outcome: a reader intentionally opens a document's related links beside the main pane and keeps that document's context while browsing the destinations. The Info panel is always pinned to the document whose related-links pin opened it. Closing the panel ends that context; a rendered document's related-links pin is its only reopening action.

Complete, accepted and closed on 2026-10-01. Reader pinning and unfiltered targets are implemented, the approved Working docs-only reconciliation and public runtime projection are complete, and bounded code review is recorded below. The user confirmed matching local/public presentation, accepted the Info panel's reader purpose and explicitly approved closeout. [Unified Analysis And Catalogue Presentation](Analysis_And_Catalogue_Presentation.md) remains the feature parent. [Info Panel](Info_Panel.md) is the primary durable owner. This delivery is ready for manual archive; Source simplification, Publish, deployment and Git actions remain separate.

### Opening From Document Content

- Add a pin button beside the optional H3 heading of each non-empty generated related-links section. Keep the heading's authored text from `[[links|related links]]` or another supplied label.
- With `[[links|]]` or whitespace-only heading text, show the pin without heading text, followed by the existing list.
- If there are no qualifying related links, render no heading, list or pin. There is then no way to open the panel from that document, even when it has a summary. A document without the directive also has no pin.
- Remove the rendered-document toolbar's **i** button. Do not add another reader entry point or automatically open the panel on document selection.
- Opening captures the exact document represented by that section, including a collection document displayed inside a report. It does not navigate the main pane or substitute the report host for its detail document.
- Give the pin an accessible action label such as **Pin related links**. It opens a captured context; it is not an unpin toggle.

### Panel Presentation

Replace the current metadata presentation with:

```text
Document title                         [Close]

Optional document summary

Document A
Document B
Document C
```

- Put the captured document's title in the shell's top row, replacing **Info**. The title wraps within the space before the right-hand close button, which remains vertically centred against the title.
- Show a non-empty `summary` directly beneath the title, without a **Summary** caption. Omit absent or blank summaries without placeholder text.
- Below the summary, show the same related list as the captured document, without its section heading or another pin button. Preserve the existing collection icons, A–Z title ordering, exact `{collection, doc_id}` destinations and deduplication rules. Concepts participate in this same list; there are no pills or collection groups.
- Remove all other rendered-panel metadata and ancillary sections, including IDs, dates, operational fields and diagram-source links. The panel contains only the title, optional summary, related list and close control.
- Keep the close control on the right. Its label and tooltip are **Close**, replacing **Hide info panel**. There is no pin/unpin control inside the panel.
- Missing summary or list content produces no caption or empty-state message. If both are absent, the body is empty while the title and Close remain visible. Normal opening requires a non-empty related section, so an empty list alone never creates an opening action.

### Captured Context And Lifetime

| State or action | Behaviour |
| --- | --- |
| Click a document's pin | Open its captured title, summary and related list. The panel is always pinned. |
| Navigate in the main pane or follow a panel link | Change the main document while retaining the captured panel context, even when the destination has no related links. |
| Click another document's pin | Replace the captured panel context with that document's title, summary and list. |
| Click the pin for the already captured document | Leave the panel open; do not treat the action as Close or unpin. |
| Close | Close the panel and release the captured context. Subsequent navigation does not reopen it. |

Retain the captured data and exact navigation context independently of the original document mount. A replaced target or closed panel must not receive late updates belonging to an earlier capture. There is no state in which the rendered panel follows the current main document. Full page reload clears the capture; persistent pins, cross-tab synchronization and bookmarkable panel state are outside this delivery.

### Data, Public Routes And Source Boundary

Use the title, summary and generated related section from the document already loaded by the reader. Do not fetch separate Links records, collection manifests or neighbouring documents to populate the panel, derive another relationship graph, or reintroduce the retired Links view/API. [Related Links](Related_Links.md) and [Builder](Builder.md) retain authored relationship construction and Build freshness ownership, subject to the revised target policy below. This delivery adds no Subject matching, token families or relationship expansion.

Link destinations are an authoring choice. Draft is a temporary indication of unfinished document work across potentially discontinuous editing sessions; the current large draft population does not define the intended long-term operating model. Tracking whether every destination is ready for publication is the author's responsibility. Do not maintain target-readiness scans, filtering or publication gates to compensate for forgotten draft states.

- Do not filter document-link picker targets or authored relationship endpoints by `draft`, ordinary `unpublishable.json` membership, inherited publication exclusion or membership in the prepared public document set. Picker discovery reads the metadata needed to identify and label targets without making their draft state a selection prerequisite.
- Preserve incoming and outgoing related-list entries for omitted destinations. Self-link removal, exact-identity deduplication, title sorting, configured collection ownership and structural validation remain normal list/data rules; they do not establish target publication readiness.
- Publish still selects which document bodies it includes under the owning draft and ignore policy. Capture the relationship records needed by those documents with their incoming/outgoing target rows intact. Excluding a target's body does not remove its title or link from another document's related list, include its body, or block publication.
- Do not read linked documents to validate their draft state, require target existence during relationship construction, add readiness warnings or rewrite unavailable destinations. A public link to a document omitted from the snapshot remains visible and receives the normal unavailable-document response when followed. The author can finish/include that document or change the authored link.
- The same unfiltered generated list supplies the document section and captured panel. A list containing only unpublished destinations is still non-empty and therefore still has its heading/pin, subject to the authored heading text.

Working relationship/picker selection no longer reads ordinary ignore policy, and captured related-list rows are no longer filtered against prepared target IDs. Picker discovery reads identity/title metadata without validating draft readiness. Ordinary source loading, editing and preparation continue validating each document's own required front matter. [Related Links](Related_Links.md) and [Builder](Builder.md) describe the implemented target policy; publication of newly generated content still requires its own Publish request.

Apply the reader behaviour to ordinary and configured collection documents available in local Manage and the public viewer. Publish captures persisted relationships and embeds the retained lists in completed Preview document output; distribution carries that same snapshot to the public site without another target filter. The panel reuses those prepared sections and their configured local/public routes. Preview remains a physical publication artifact, with no browser stage or preview read route. Public readers use deployed static assets without local service calls, capability probes or Working fallback.

The Source editor temporarily retains its current metadata/token panel and **i** button until [Source Editor And Token Modals - Delivery](Source_Editor_And_Token_Modals_Delivery.md) replaces those workflows. Entering Source ends the captured reader context; it must not freeze or retarget the authoring session. Returning to rendered content leaves the reader panel closed until a related-links pin is used. The Source delivery owns final removal of the authoring panel integration.

Shared browser code remains canonical under `docs-viewer/`, with its tracked public projection under `site/docs-viewer/`. Update the explicit public inventory only if its runtime boundary changes. Real Publish, deployment, commit and push remain separately requested actions.

## Deliverables

- [x] A pin beside each non-empty document related-links heading, including the heading-free form, with empty sections still suppressed.
- [x] A rendered panel containing the captured document title, optional uncaptioned summary and existing related list, plus Close.
- [x] Captured context retained across document navigation and replaced only by another pin action; Close releases it.
- [x] Removal of the rendered-document **i** action and previous metadata presentation, while Source retains its separate temporary editing workflow.
- [x] Local/public integration and the required tracked runtime projection using already generated document content.
- [x] Removal of link-target draft/publication filtering from picker/relationship selection and captured related-list expansion, while retaining document-body publication eligibility.
- [x] Proportionate static verification, user interaction/layout acceptance, code review and durable transfer to Info Panel.

## Process

1. Open Doc A with a non-empty related-links section and click its pin. The main pane remains on A; the panel shows A's title, available summary and related list.
2. Follow panel links to B and C. The main pane changes while the panel continues to describe A.
3. Click C's related-links pin to replace the panel with C's context. A heading-free directive still provides its pin; an empty section provides none.
4. Close the panel. Navigate again and confirm it remains closed until a document's related-links pin is used.
5. Retain a link to an unfinished document omitted from the public snapshot. The referring document's section/panel still lists that destination; following it uses the normal unavailable response. The referring document remains publishable without a target-readiness gate.
6. Repeat with an exact collection detail and in local/public presentation. Review long-title wrapping, Close alignment, missing summary and the existing collection icons manually.
7. In local Manage, enter Source and use its existing editing workflow. Return to the document with the reader panel closed. The separate Source delivery later replaces this authoring panel.

## Delivery Steps

### IRP-0 — Readiness

- [x] Confirm generated-section reuse, exact ordinary/collection targets, captured state ownership and main-pane link activation against current owners.
- [x] Confirm pin/heading suppression, shell title/Close layout and removal of rendered metadata without changing authored relationship extraction.
- [x] Confirm removal of draft/ignore/prepared-membership checks for link targets, with document-body eligibility and source-schema validation retained by their existing owners.
- [x] Confirm local/public route composition, non-viewer consumers of generated content and the temporary Source transition boundary.
- [x] Confirm the bounded implementation sequence and proportionate verification budget. Stop if this requires a publication redesign, another relationship graph or a general history/cache framework.

Gate: complete; implementation and the separately named Working docs-only reconciliation approved on 2026-10-01. Verification: specification and broad owner comparison only, with no prototype, executable tests or generated writes during readiness. Record: safe to implement within the existing relationship, preparation, document-mount, route and panel owners.

Readiness decisions: reuse each loaded payload's title/summary and copy its generated list at pin activation, preserving resolved routes and icons independently of the document mount. Add the opening control during local/public reader mounting so exported content and Docs Review retain their static lists. Ordinary mounting and collection-detail mounting already expose their own payloads and exact targets; use both rather than inferring a detail from the selected report host. The shared route listener already handles links throughout the app root, including the panel. The panel controller owns capture and release; its hosted view renders the captured summary/list, and the shell projects the captured title. Navigation updates must leave reader capture intact. Existing host request invalidation provides the lifecycle boundary for replacement and Close. Source entry releases reader capture; Source exit closes the authoring panel instead of reopening rendered metadata. Retire the rendered metadata view/control paths without compatibility aliases, retaining Source's separate views.

Approved implementation order and verification budget: **IRP-1**, then **IRP-2**, then **IRP-3**, followed by bounded **IRP-4** review. Remove ordinary ignore checks from relationship maintenance and picker discovery, use identity/title metadata discovery without the full source loader's draft validation, and retain captured incoming/outgoing rows without prepared-target filtering. Keep source editing/build validation and body eligibility unchanged. The approved full Working docs-only reconciliation restores suppressed relationships and refreshes embedded sections without rebuilding Search or running Publish. Use explicit-path Python/JavaScript lint and source/diff review, then the required runtime projection, projection check and site validation. Static checks should cost seconds to a few minutes; full-build cost depends on the configured document set and is not benchmarked at readiness. The relevant picker, relationship and preparation Python tests still use retired scope contracts and are not selected as current evidence. No test authoring, migration, suite or browser automation is proposed. Manual local/public review remains the interaction/layout gate; additional real Build, Publish, deployment, commit and push retain their separately named authorization boundaries.

### IRP-1 — Unfiltered Link Targets

- [x] Remove ordinary publication exclusions from document-link picker selection and authored relationship endpoint maintenance; do not make target draft validity a picker prerequisite.
- [x] Preserve the captured incoming/outgoing summaries for published documents without filtering their destinations against prepared IDs.
- [x] Keep exact identity/schema validation, authored labels, self-link removal and deduplication; keep document-body preparation eligibility separate.
- [x] Confirm any required full Working relationship reconciliation to restore relationships previously suppressed by the removed policy. Treat it as an explicit build operation, not a new scan during ordinary linking or panel opening.

Gate: implementation complete. Record: explicit-path Python lint passed and source review retained exact identity, path confinement and body eligibility. The approved docs-only reconciliation processed 5,204 documents across ordinary and all four configured collections, restored seven relationships in twelve changed records, updated two Catalogue sections and refreshed the 56-record non-empty aggregate, with zero warnings. Collection rendering after the final relationship updates reused persisted records without another relationship refresh. Search and Publish were not run. Retired-scope picker/relationship/preparation tests are not current coverage and were neither changed nor run; real omitted-target publication was not exercised by Codex.

### IRP-2 — Document Pin And Captured Panel

- [x] Add the pin to non-empty related sections and remove the rendered **i** control, retaining Source's temporary control.
- [x] Project the captured title into the shell, lay out the wrapping title and centred Close control, and render only optional summary and the existing list.
- [x] Retain the exact captured context across main navigation; implement replacement, repeated-pin and Close behaviour through the existing panel lifecycle owners.
- [x] Keep capture independent of disposed document mounts and reject late work after replacement or closure.
- [x] End reader capture on entering Source and preserve the existing authoring workflow until its separate delivery.

Gate: complete; reader panel accepted at user closeout on 2026-10-01. Record: explicit-path lint passed for the changed JavaScript files, including the subsequent Search label follow-through. Bounded source review confirms ordinary/detail callbacks carry loaded payloads and exact targets, pins copy only the list, main navigation leaves capture intact, and Source mode transitions close it. The rendered metadata module and shared rendered **i** registration are removed; the Source control is management-only. No browser checks or new/changed tests were run. User acceptance covers the delivered reader outcome; individual interaction edge cases were not itemized as separate manual results.

### IRP-3 — Public Projection And Presentation Review

- [x] Confirm public composition reuses its loaded document sections and configured navigation without management services or additional data fetching.
- [x] Confirm retained links to omitted targets do not cause target-readiness reads, list suppression or publication warnings/gates.
- [x] Project changed shared runtime files with `bin/site-code-update`, inspect the exact tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`.
- [x] Record user acceptance of the local/public reader and presentation; distinguish overall acceptance from separately itemized edge-case coverage.

Gate: complete; local/public presentation accepted on 2026-10-01. Record: public inventory replaces the retired metadata module with the related-links owner and adds existing pin artwork; route defaults use the new view, while Docs Review retains static content. The exact site runtime delta was inspected; projection check and site validation passed. After the requested refinements, the user confirmed they could switch between Manage and public without noticing a presentation difference and accepted the Info panel's purpose. Long-title, missing-summary, heading-free/empty-section, repeated-pin, replacement and Close cases were not individually itemized in that confirmation. Static review confirms no capture reads or management handles. Codex did not run a real Publish; public content publication remains a separately requested operation.

Accepted presentation refinements are incorporated into shared CSS: loose Info line spacing and the public list row gap on both surfaces, document link colours/states, a pin matching inline icon size, the public H1 size, and Manage's gap below the Related Links heading. Screenshot comparison identified further host/browser differences in body paragraph margins and generated Related Links heading/list styles; shared token-based rules now use the public paragraph margins, heading typography and row gap on both surfaces. Public and Manage site Search now use the same `search` placeholder and `Search` accessible label. [CSS Ownership](CSS_Ownership.md) records the explicit shared-style boundary.

### IRP-4 — Code Review

- [x] Review the bounded diff for exact target ownership, retained-context lifetime, dead metadata/control paths, duplicate list rendering, compatibility residue and public leakage.
- [x] Confirm the panel contains no heading/pin copied from the document section and no remaining rendered opening path through **i**.
- [x] Confirm target-publication filtering is removed without weakening exact identity/schema validation, changing document-body eligibility or moving Source authoring ownership.
- [x] Resolve findings and repeat only affected evidence; separately scope any required test changes.

Gate: bounded review complete. Findings resolved: retain explicit picker source-symlink rejection after removing the full source loader; render absent captured body content without placeholders; keep the Source default resolver to one read and no rendered fallback; update the public required-file inventory alongside removal of the metadata view. The projection manifest's sorted-file validation caught and corrected the new module's initial placement. Affected lint and public projection/validation were repeated after review changes. No compatibility aliases, second graph, target-readiness checks, public service calls or additional reader opening path were introduced. User presentation acceptance is recorded in IRP-3; separately itemized interaction cases and real omitted-target publication remain evidence limits.

### IRP-5 — Closeout

- [x] Confirm user acceptance of the delivered reader workflow and explicit closeout.
- [x] Transfer implemented behaviour into Info Panel and reconcile Related Links, Builder and the document-link picker owner for the removed target filters. Keep the separate Source delivery proposed until its readiness/implementation is approved.
- [x] Update the feature parent's current state.
- [x] Recommend this delivery for manual archive after acceptance and durable transfer.
- [x] Distinguish implementation/public projection from any separately authorized Publish, deployment, commit or push.

Gate: complete; the user explicitly approved closeout on 2026-10-01 after accepting the matching local/public presentation and useful reader panel. Durable owners and the feature parent's current state are updated. Recommend this completed delivery for the next manual documentation archive. No separate working-note or verification sibling was created. No Publish, deployment, commit or push occurred. Closeout reused the recorded implementation evidence without rebuilding or running tests.

## Follow-on

- **Source editing:** [Source Editor And Token Modals - Delivery](Source_Editor_And_Token_Modals_Delivery.md) owns complete Markdown editing, existing-token modal editing and retirement of Source's panel and **i** control. Suggested order is the reader panel first, Source simplification second.
- **Document link strength:** [Document Link Strength](Document_Link_Strength.md) retains separate strength authoring and persistence work. It must be reassessed against the flat generated list before implementation; this delivery adds no weighting, filtering or visualisation.
- **Broader icons/navigation:** use [Shared Icons](Shared_Icons.md) for the pin artwork and existing toolbar foundation. Wider icon migration, Media View navigation and general history/caching remain separately scoped.

---
draft: false
doc_id: d-20260913-151251-cbee5b
title: Info Panel Related Links And Pinning - Delivery
added_date: "2026-09-13 15:12:51"
last_updated: "2026-10-01 15:05:39"
summary: Open an always-pinned document panel from the generated related-links section, showing only its title, optional summary and related list while the reader browses other documents.
ui_status: proposed
parent_id: d-20260902-102745-8379ea
---
# Info Panel Related Links And Pinning - Delivery

## Requirements

Deliver one outcome: a reader intentionally opens a document's related links beside the main pane and keeps that document's context while browsing the destinations. The Info panel is always pinned to the document whose related-links pin opened it. Closing the panel ends that context; a rendered document's related-links pin is its only reopening action.

The revised requirements were agreed on 2026-10-01. This replaces the earlier following/pin-toggle interaction, concept-pill presentation and proposed Subject-based relationship expansion. Reuse the generated document-only list described in [Related Links](Related_Links.md); the separate per-document Links view and read endpoint are already retired. Implementation has not started, and this delivery remains proposed pending **IRP-0 — Readiness**. [Unified Analysis And Catalogue Presentation](Analysis_And_Catalogue_Presentation.md) remains the feature parent. [Info Panel](Info_Panel.md) is the primary durable destination at closeout.

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

Current implementation still applies the ordinary ignore policy in Working relationship/picker selection and filters captured related-list targets against prepared IDs. Removing those policies is a proposed change in this delivery, not a claim about shipped behaviour. Ordinary source loading, editing and preparation continue validating each document's own required front matter; this proposal removes readiness validation as a condition of linking to it. [Related Links](Related_Links.md) and [Builder](Builder.md) describe the current filtering until implementation and durable transfer are complete.

Apply the reader behaviour to ordinary and configured collection documents available in local Manage and the public viewer. Publish captures persisted relationships and embeds the retained lists in completed Preview document output; distribution carries that same snapshot to the public site without another target filter. The panel reuses those prepared sections and their configured local/public routes. Preview remains a physical publication artifact, with no browser stage or preview read route. Public readers use deployed static assets without local service calls, capability probes or Working fallback.

The Source editor temporarily retains its current metadata/token panel and **i** button until [Source Editor And Token Modals - Delivery](Source_Editor_And_Token_Modals_Delivery.md) replaces those workflows. Entering Source ends the captured reader context; it must not freeze or retarget the authoring session. Returning to rendered content leaves the reader panel closed until a related-links pin is used. The Source delivery owns final removal of the authoring panel integration.

Shared browser code remains canonical under `docs-viewer/`, with its tracked public projection under `site/docs-viewer/`. Update the explicit public inventory only if its runtime boundary changes. Real Publish, deployment, commit and push remain separately requested actions.

## Deliverables

- [ ] A pin beside each non-empty document related-links heading, including the heading-free form, with empty sections still suppressed.
- [ ] A rendered panel containing the captured document title, optional uncaptioned summary and existing related list, plus Close.
- [ ] Captured context retained across document navigation and replaced only by another pin action; Close releases it.
- [ ] Removal of the rendered-document **i** action and previous metadata presentation, while Source retains its separate temporary editing workflow.
- [ ] Local/public integration and the required tracked runtime projection using already generated document content.
- [ ] Removal of link-target draft/publication filtering from picker/relationship selection and captured related-list expansion, while retaining document-body publication eligibility.
- [ ] Proportionate static verification, user interaction/layout review, code review and durable transfer to Info Panel.

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

- [ ] Confirm generated-section reuse, exact ordinary/collection targets, captured state ownership and main-pane link activation against current owners.
- [ ] Confirm pin/heading suppression, shell title/Close layout and removal of rendered metadata without changing authored relationship extraction.
- [ ] Confirm removal of draft/ignore/prepared-membership checks for link targets, with document-body eligibility and source-schema validation retained by their existing owners.
- [ ] Confirm local/public route composition, non-viewer consumers of generated content and the temporary Source transition boundary.
- [ ] Confirm the bounded implementation sequence and proportionate verification budget. Stop if this requires a publication redesign, another relationship graph or a general history/cache framework.

Gate: present concise read-only readiness for implementation approval; remain proposed until it is safe to implement. Verification: specification and broad owner comparison only, with no prototype, tests or generated writes. Record: revised requirements agreed on 2026-10-01; readiness not started.

### IRP-1 — Unfiltered Link Targets

- [ ] Remove ordinary publication exclusions from document-link picker selection and authored relationship endpoint maintenance; do not make target draft validity a picker prerequisite.
- [ ] Preserve the captured incoming/outgoing summaries for published documents without filtering their destinations against prepared IDs.
- [ ] Keep exact identity/schema validation, authored labels, self-link removal and deduplication; keep document-body preparation eligibility separate.
- [ ] Confirm any required full Working relationship reconciliation to restore relationships previously suppressed by the removed policy. Treat it as an explicit build operation, not a new scan during ordinary linking or panel opening.

Gate: linking and rendered related lists follow the author's references independently of target readiness. Verification: bounded source review and the smallest justified existing picker/relationship/preparation selection after inspecting its coverage and side effects. Separately approve any test changes or real build/publication action; record evidence limits when no executable selection is justified. Record: not started.

### IRP-2 — Document Pin And Captured Panel

- [ ] Add the pin to non-empty related sections and remove the rendered **i** control, retaining Source's temporary control.
- [ ] Project the captured title into the shell, lay out the wrapping title and centred Close control, and render only optional summary and the existing list.
- [ ] Retain the exact captured context across main navigation; implement replacement, repeated-pin and Close behaviour through the existing panel lifecycle owners.
- [ ] Keep capture independent of disposed document mounts and reject late work after replacement or closure.
- [ ] End reader capture on entering Source and preserve the existing authoring workflow until its separate delivery.

Gate: the complete reader interaction is available for local review. Verification: select explicit-path lint and any justified existing state/route evidence after inspecting their documented coverage; layout, copy, focus and navigation feel remain manual. New or changed tests require their own approved specification under [Testing](Testing.md) and [Test Contract Discipline](Test_Contract_Discipline.md). Record: not started.

### IRP-3 — Public Projection And Presentation Review

- [ ] Confirm public composition reuses its loaded document sections and configured navigation without management services or additional data fetching.
- [ ] Confirm retained links to omitted targets do not cause target-readiness reads, list suppression or publication warnings/gates.
- [ ] Project changed shared runtime files with `bin/site-code-update`, inspect the exact tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`.
- [ ] Record user review of main and collection documents, long titles, missing/blank summary, heading-free sections, empty sections, repeated pins, replacement and Close.

Gate: user acceptance in local Manage and public-site preview. Verification: required projection/validation and manual presentation review within the agreed budget; real Publish or deployment requires its own request. Record: not started.

### IRP-4 — Code Review

- [ ] Review the bounded diff for exact target ownership, retained-context lifetime, dead metadata/control paths, duplicate list rendering, compatibility residue and public leakage.
- [ ] Confirm the panel contains no heading/pin copied from the document section and no remaining rendered opening path through **i**.
- [ ] Confirm target-publication filtering is removed without weakening exact identity/schema validation, changing document-body eligibility or moving Source authoring ownership.
- [ ] Resolve findings and repeat only affected evidence; separately scope any required test changes.

Gate: present review findings, resolutions and remaining limitations. Verification: bounded code/diff review and selected affected checks. Record: not started.

### IRP-5 — Closeout

- [ ] Confirm acceptance of the intentional pin/open, captured title/summary/list, navigation, replacement and Close workflow.
- [ ] Transfer shipped behaviour into Info Panel and reconcile Related Links, Builder and the document-link picker owner for the removed target filters. Keep the separate Source delivery proposed until its readiness/implementation is approved.
- [ ] Update the feature parent and recommend this delivery for manual archive after durable transfer.
- [ ] Distinguish implementation/public projection from any separately authorized Publish, deployment, commit or push.

Gate: explicit user closeout. Verification: reuse accepted implementation evidence; documentation-only closeout needs bounded source review, with no automatic build or test run. Record: not started.

## Follow-on

- **Source editing:** [Source Editor And Token Modals - Delivery](Source_Editor_And_Token_Modals_Delivery.md) owns complete Markdown editing, existing-token modal editing and retirement of Source's panel and **i** control. Suggested order is the reader panel first, Source simplification second.
- **Document link strength:** [Document Link Strength](Document_Link_Strength.md) retains separate strength authoring and persistence work. It must be reassessed against the flat generated list before implementation; this delivery adds no weighting, filtering or visualisation.
- **Broader icons/navigation:** use [Shared Icons](Shared_Icons.md) for the pin artwork and existing toolbar foundation. Wider icon migration, Media View navigation and general history/caching remain separately scoped.

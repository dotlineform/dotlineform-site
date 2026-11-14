---
draft: false
doc_id: d-20261114-213618-b4856c
title: Book Publication
added_date: "2026-11-14 21:36:18"
last_updated: "2026-11-14"
summary: Proposed workflow for copying private Book chapters into a draft edition and publishing an authored table of contents.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Book Publication

**Proposed.** Continue the design before readiness and implementation. [Planned Features](../Planned_Features.md) · [Private Book curation](library_structure.md)

## Requirements

Book remains the permanent private working area for compiling chapters. Completed chapters can be copied into a separate named collection for release through the normal Docs draft and Publish workflow.

The proposed collection ID is `book-published`, compatible with existing document and managed media routes. Its entry point is an authored table of contents (TOC), initially titled **Book draft** and marked draft. The TOC serves as the collection host and gives readers chapter links in the author's chosen order. The host's draft status keeps the entire release collection private while chapters are being marked ready. Chapter browsing starts from the TOC and uses the common document reader. The authored TOC takes the place of the standard collection report.

Each copy creates a fresh destination ID and starts as a draft. The copied chapter owns the managed media it needs to render independently of private Book. Same-title copies can coexist while the author prepares the next version. Before release, the author can switch the TOC link to the new copy and delete the superseded draft from the publication collection. Private Book remains the source for substantive editorial work. Small corrections to published chapters can use ordinary Source Save and Publish so chapter URLs stay stable.

## Proposed Deliverables

- A configured release collection with its own document and media storage, a draft TOC host in the ordinary Index, and the normal chapter draft controls.
- A Book action that copies the chosen chapters into the release collection and supplies their new identities for linking from the TOC.
- An authored TOC that works in Manage and in the public reader, with a way for readers to return to it from a chapter.
- A first-release workflow that prepares the eligible TOC, chapters, and media through the existing Working generation and publication queue.

## Editorial Workflow

1. Finish a chapter in private **Book** and copy it to **Book draft**. Open the new draft for review.
2. Edit the TOC to link to the destination chapter. For a revised pre-release copy, point the TOC at the new ID before deleting the superseded draft.
3. Mark the chapters linked from the TOC ready. Give the TOC its final title and check the links against the chapters intended for release before clearing the host's draft status.
4. Use the ordinary Publish action to apply the queued outputs and review the prepared public reader. Repository deployment follows the existing release workflow.

## Decisions Before Readiness

- **TOC authoring.** Decide how the copy action helps place or link a new chapter, and how the author finds unlinked and superseded drafts when the TOC is the entry point.
- **Reader navigation.** Decide whether the initial edition needs TOC return alone or also Previous and Next in TOC order. Agree the labels in Manage and the public reader.
- **Copy boundaries.** Decide whether the action supports one chapter, a checked batch, or both. Agree which metadata and thumbnails carry over, and how chapter links that still point into private Book are handled.
- **Release review.** Decide how to check that each TOC link lands on an eligible release chapter and whether alternate ready chapters can be published without a TOC entry. Decide whether released chapters participate in Search and Recent.

## Delivery Steps

- [ ] **Readiness.** Confirm the TOC host, editorial controls, identity and media handoff, and release review. Check the current eligibility path with a draft host and ready chapters. The browser owns selection and TOC authoring; Python owns configured copying, media adoption, and generation. Agree the smallest verification scope before implementation.
- [ ] **Implementation.** Register the release collection and TOC, add the chapter copy action, and connect the chosen Manage and reader navigation. Demonstrate the draft-to-ready release handoff with representative chapters and referenced media.
- [ ] **Code review.** Trace exact source and destination IDs, chapter media independence, TOC links, and the transition from a draft host to eligible public output. Apply the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review).
- [ ] **Closeout.** Record what was verified in Working and public preview, note remaining editorial decisions, and update the durable owners for collection browsing and publication.

## Follow-On

Substantial post-release revisions, multiple editions, and downloadable editions can be scoped once the first release workflow has been reviewed.

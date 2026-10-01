---
draft: false
doc_id: d-20261001-121208-7ef21d
title: Catalogue Token Links Delivery
added_date: "2026-10-01 12:12:08"
last_updated: "2026-10-01 13:52:05"
summary: Build Catalogue Work token references as document relationships and retire the semantic usage index and report.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Token Links Delivery

Status: complete; user accepted the delivery and approved closeout on 2026-10-01. Parented to [Planned Features](Planned_Features.md).

## Requirements

Help readers explore the portfolio through one document relationship graph. Supported Catalogue Work image and Work Media View text-link tokens contribute ordinary outgoing links to `{collection: "catalogue", doc_id: "<work_id>"}`, with reciprocal incoming links maintained by the existing Links builder. Related links continues to present unique document relationships. Gallery Media View tokens create no link record; Media View already supports Gallery exploration.

For every document link, build the relationship without validating destination existence or link validity. Remove routine destination-validation reads and code; titles are presentation metadata and must not gate relationship creation. Link validity belongs to authoring and the separate Broken Links audit. Preserve explicit document deletion cleanup: remove the deleted document's record and its associated relationships. Retain Catalogue self-reference suppression and existing deduplication.

Keep authored token syntax, image presentation, Source Info editing, Media View and Subject ownership. Retire stored occurrence text, source positions and occurrence reporting; these fields have no current functional consumer in the usage index.

Every Catalogue subdocument ends with `[[links|related links]]`, separated from its existing Work image token by a blank line. Update the Catalogue body generator so creation and regeneration retain this structure, and regenerate all existing Catalogue sources. For Work `00001`:

```md
[[catalogue:image:work:00001|use_work_title_caption=true&include_work_metadata=true&placement=left&fill_width=true]]

[[links|related links]]
```

## Deliverables

- Work token references maintained in `generated/documents/links-by-id/` through the existing incremental owner, without another relationship store or lookup table.
- Catalogue source bodies containing the Work image followed by the Related links directive, maintained by the existing body generator for new and regenerated documents.
- Retirement of `generated/documents/semantic-tokens/index.json`, its producer, build prerequisites, read endpoint and snapshot handling, with no aliases.
- Retirement of the Semantic Tokens report registration, loader, service/configuration wiring and report document `d-20260912-110653-264748`.
- Reconciled existing Work relationships and obsolete generated output, plus current [Builder](Builder.md), [Related Links](Related_Links.md) and affected token/report documentation.

## Process

Authors insert and edit Catalogue tokens as today. Save writes source; the watcher or an explicit document Build refreshes Work relationships before rendering Related links. Image and Media View activation retain their current behavior. Explicit document deletion continues to clean up the graph. Broken Links remains an independent authoring audit.

### Full Rebuild Sequence

Manage's **Rebuild docs and Search** already includes Catalogue. It builds Context, ordinary documents, Concepts, Moments, then Catalogue, followed by Search. That existing order supports the following sequence:

1. Each contributing document build refreshes outgoing relationships and reciprocal incoming relationships. It writes Links JSON only when its content differs from the saved record.
2. The Catalogue build refreshes its own relationships before rendering. The Related links directive uses the refreshed records already held in memory to list documents referencing each Work. It needs no extra Links-file change check or second read.
3. The build renders every Catalogue document, including its image and Related links section, then compares the complete new document JSON with the saved JSON. It writes only differing payloads; unchanged files retain their modification times.

For example, document A adds an image of Work `00001`. Its build adds A to that Work's incoming links. Catalogue `00001` then renders A in its Related links section and its JSON changes, even though the Catalogue Markdown itself is unchanged. Comparing the final document JSON captures changes from both source content and relationship data.

A full Docs Build renders existing sources; it does not regenerate their bodies. After changing the Catalogue body generator, use full Catalogue Regenerate once to add the directive to every existing source. Subsequent full Docs rebuilds render those directives using the sequence above. During initial reconciliation, populate contributing Work relationships before rendering the Catalogue sections.

## Delivery Steps

### CTL 0 Readiness

- [x] Confirm the current Links, token rendering, Catalogue body generation, report retirement and generated-output owners against this scope.
- [x] Confirm title handling supports relationship creation without destination checks and identify only the affected verification selection.

Gate passed: approved implementation uses the existing Links owner, Catalogue Regenerate and report/source deletion owners. Titles are optional presentation metadata. No Gallery document work or new store layer. Follow [Development Checklist](Development_Checklist.md).

### CTL 1 Implementation

- [x] Add Work token relationships and remove routine target-validity checks for document links, preserving deletion cleanup.
- [x] Append the Related links directive in the Catalogue body generator and regenerate every existing Catalogue source through its owner.
- [x] Remove the semantic usage index and complete report retirement while retaining token authoring/rendering and Broken Links.
- [x] Populate existing Work references before rebuilding Catalogue related sections; remove obsolete usage output and refresh affected embedded Related links.
- [x] Update durable owners and any required runtime/configuration projections.

Gate: complete relationship and retirement behavior. Verification budget: explicit-path lint/syntax, bounded source/output review and whitespace checks; represented shared-runtime changes also require site-code projection/check and site validation. Expect seconds to minutes plus bounded review; reconciliation writes Working output. Record exact selected evidence and cost before execution. Test creation, changes or runs need separate agreement under [Testing](Testing.md); UI review remains manual.

Gate passed: Context, ordinary documents, Concepts and Moments reconciled before full Catalogue Regenerate updated and built all 4,616 Catalogue documents, with no warnings. The obsolete Working index and report host were removed through their owning boundaries, and the workspace Links aggregate was refreshed. Static evidence passed: explicit-path Python lint and `py_compile` for all 16 changed Python files; JavaScript lint for `docs-viewer-reports.js` and `docs-viewer-report-service.js`; parsing both changed JSON configurations; and `git diff --check`. These checks took under a second in the recorded final selection; generation and bounded review had their separate costs. No changed runtime file is represented in the public code inventory, so no site-code projection was required. No tests were created, changed or run.

### CTL 2 Code Review

- [x] Review Work/Gallery separation, self-reference omission, deduplication, reciprocal updates, preserved deletion cleanup and absence of destination-validity gates.
- [x] Confirm every Catalogue source ends with exactly one Related links directive, regeneration preserves it and rendered sections include recorded incoming references.
- [x] Check retirement completeness, unnecessary reads and compatibility residue; resolve findings and repeat only affected checks.

Gate passed: bounded source/configuration review found no remaining usage-index producer, reader, prerequisite, route or report loader. Review corrected stale build-order and prerequisite documentation. Direct generated-data inspection found exactly one closing directive in all 4,616 sources, 20 Catalogue records with 21 incoming relationships, zero outgoing relationships and zero empty Catalogue records. Work `00520` renders its two recorded Context references. Missing destinations and reciprocal deletion/move behavior were reviewed in source; no synthetic mutations or automated test coverage were added.

### CTL 3 Closeout

- [x] Confirm Working generated follow-through and record remaining omissions.
- [x] Transfer the final contract to durable owners and recommend archiving this delivery after acceptance.
- [x] Accept the delivered outcome and confirm explicit closeout.

Gate passed: user approved closeout. Existing implementation and review evidence remains the completion evidence; no separate manual-review result was recorded. Publish, Search rebuild, deployment, commit and push remain separate actions.

Restart the local Studio/Docs Viewer services and reload the reader to load the changed runtime. Catalogue Work `00520` provides a current incoming-links example. Preview and the tracked public snapshot were not rewritten; their next authorized Publish adopts the new content and retirement. Search and Recents were intentionally not rebuilt. No Publish, deployment, commit or push occurred. This delivery is ready for manual archiving; [Builder](Builder.md), [Related Links](Related_Links.md), [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md), [Reports](Reports.md) and the [Development Checklist](Development_Checklist.md) retain the final contract.

## Follow-on

None currently required. Broader Save/Build performance work remains outside this delivery.

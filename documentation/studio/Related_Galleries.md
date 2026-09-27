---
draft: false
doc_id: d-20260927-221737-07fbbf
title: Related Galleries
added_date: "2026-09-27 22:17:37"
last_updated: "2026-09-27 22:17:37"
summary: Proposed per-Work related Gallery IDs, explicit Gallery-to-Series association, shared title lookup, and review of Studio Save versus general rebuild responsibilities.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Related Galleries

## Intended Behaviour

Work Media View should display **Related galleries**: the Galleries the Work belongs to, plus the Galleries belonging to the Work's own Series. Deduplicate by exact Gallery ID. Gallery membership and a Gallery's association with a Series are separate relationships.

A Gallery does not become related merely because another Work in the same Series belongs to it. Changing one Work's Gallery memberships changes that Work's related list; it does not change the related lists of other Works. A Work's own explicit Gallery memberships remain related even when those Galleries belong to a different Series.

Keep the related IDs in each generated Work by-ID JSON. Do not introduce an aggregate Work-to-related-Galleries lookup or scan other Work records in the browser. Store IDs rather than copied Gallery titles, and resolve display titles through a shared Gallery title lookup. Renaming a Gallery should not require rewriting these related-ID arrays.

This document proposes implementation and identifies decisions still needed. It does not authorise code, source-data migration, generation, publication or a change to the current Save workflow.

## Current Model And Missing Relationship

[Catalogue Source Model](Catalogue_Source_Model.md) and [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md) describe the current owners. Canonical `works.json` supplies each Work's required `series_id`; `galleries-by-work.json` supplies its exact Gallery memberships. Gallery definitions in `galleries.json` currently contain only `gallery_id` and `title`; the validator rejects additional fields. There is no explicit Gallery-to-Series association in the current model. Galleries may contain Works from different Series.

The proposed meaning therefore needs an explicit canonical relationship defining which Series a Gallery belongs to. One candidate is an exact `series_id` on the Gallery definition. Whether that association is required, optional, or supports more than one Series must be agreed before implementation. A Gallery's owning Series need not constrain which Works can be members unless that becomes a separately agreed requirement.

Existing Gallery associations must be assigned or reviewed explicitly. Neither matching numeric IDs, matching titles, historical overview Galleries nor the Series of member Works is authority for a Gallery-to-Series assignment. Do not manufacture assignments during generation or add a fallback that infers them.

## Proposed Read Model

For a Work `W`, compute:

```text
related_gallery_ids(W) = distinct(
    saved Gallery memberships of W
    + Galleries explicitly associated with W.series_id
)
```

Emit `work.related_gallery_ids` as an always-present array in `works/index/<work_id>.json`, using exact canonical Gallery IDs and deterministic ID ordering. It is a replaceable derived field, not another editable membership authority. Keep exact memberships distinguishable from related IDs so neither the Work editor nor another consumer mistakes a related Gallery for a saved membership.

Use a shared Gallery ID-to-title read model for labels. The existing `galleries/galleries_index.json` already provides Gallery IDs, titles and member counts and is a candidate owner; its transport and rebuild policy need review. This is a Gallery registry shared by readers, rather than a large relationship map keyed by every Work. A Gallery rename updates that registry and its individual Gallery record while the Work's related IDs remain unchanged.

Media View reads the selected Work's related IDs, resolves their labels and opens the selected exact Gallery through the existing Gallery reader. Direct Work entry establishes no Gallery browsing sequence until a Gallery is selected. Public reads use published records and lookup data; local reads use Working. Neither surface infers missing relationships or falls back to canonical data. An unavailable title lookup or unknown Gallery ID should produce a visible error under the agreed reader contract.

Current `work.galleries` embeds Gallery IDs and titles. Adding an IDs-only related field alone would not remove that existing rename dependency. The implementation must review consumers and decide whether exact memberships also become an IDs-only field, with their titles resolved through the same registry. Avoid maintaining duplicate titled and untitled representations merely for compatibility.

## Save And General Rebuild

Current [Catalogue Build And Lookup Refresh](Catalogue_Build_And_Lookup_Refresh.md) describes a combined synchronous Save. `catalogue_output_service.py` completes media, generated output, private report/subject metadata and Studio lookups after canonical persistence. `generate_work_pages.py` constructs the full Catalogue projection in memory even for selected output, considers aggregate indexes and shared policy, and writes changed versions. The output selector also considers current and former Gallery co-members. Private Studio lookup refresh currently uses a full refresh. A small selected write therefore does not necessarily mean a small computation.

Review these responsibilities before attaching another derived relationship to Save. Distinguish canonical persistence and immediate editor updates, selected by-ID consumer projection, shared title/discovery lookup generation, private report/subject metadata, and media completion. They have different dependencies and need not all use one full rebuild.

| Change | Effect on related-ID arrays | Other generated data to consider |
| --- | --- | --- |
| One Work's Gallery memberships change | Recompute that Work only; other Works' related lists are unaffected | Exact affected Gallery member records/counts |
| One Work changes Series | Recompute that Work using its new Series association | Former/current Series member records |
| Gallery title changes | No related-ID changes | Shared title registry and individual Gallery record; eliminate existing copied-title dependencies if adopting the IDs-only design |
| Gallery is created or its Series association changes | Related IDs may change for Works in the affected owning Series | Gallery registry and Gallery record |
| Gallery is deleted | Remove its ID wherever it is a membership or related reference | Canonical membership cleanup, Gallery record deletion and registry refresh |
| Unrelated Work metadata changes | No related-ID changes | Only the read models that actually project those fields |

Creating, deleting or reassigning a Gallery's Series association is different from editing one Work's membership. Such definition changes can affect many Work by-ID records because the materialised Series-related list changes. They must not be confused with the rejected rule that propagates one Work's memberships to its Series peers.

A possible split is for Save to persist canonical changes, return current editor values and complete the explicitly retained direct outputs, while an explicit general rebuild reconciles broader derived Work records and shared lookups. The general rebuild must include affected Work by-ID related arrays, not just the title registry, when Gallery-to-Series associations change. Keep materialised relationships in Work records even when a rebuild computes them together.

Choose the freshness boundary deliberately. If shared lookup or broad relationship generation moves out of Save, Docs Viewer can show older titles or related IDs until rebuild; deletion can leave a stale ID until reconciliation. Decide whether that delay is acceptable, or whether specific definition operations must synchronously complete their affected outputs. Save and rebuild need clear separate success/failure results and one explicit owner each. Do not introduce background work or a pending-change system merely to implement this proposal.

The deferred [Save And Targeted Publish](Catalogue_Save_And_Targeted_Publish.md) proposal also considers removing lookup generation from Save, but it proposes a broader publication lifecycle. This document does not resume it or assume that a general lookup rebuild should become Publish. Decide local read-model maintenance separately from Preview, public distribution, commit and deployment.

## Decisions Before Delivery

- Define and assign the canonical Gallery-to-Series relationship, including unassigned or multiple-Series cases and whether cross-Series membership remains unrestricted.
- Agree the IDs-only fields for exact memberships and related Galleries, the shared title lookup owner, and removal of copied-title dependencies.
- Define what Studio Save must complete immediately and what an explicit general rebuild owns, including private Studio lookups, consumer indexes, report metadata and related Work projections.
- Agree acceptable Docs Viewer freshness after Save and how definition creation, reassignment and deletion reach a consistent reader state.
- Review the existing output-selection expansion and whole-corpus computation against those dependencies before designing the implementation slice.

Once these decisions are settled, specify a bounded delivery covering canonical association authoring/validation, generated per-Work IDs, lookup and Save/rebuild ownership, and Media View consumption. Test changes require their own agreed specification. This proposal was produced by read-only inspection and a repository documentation edit; implementation and live lifecycle evidence remain separate work.

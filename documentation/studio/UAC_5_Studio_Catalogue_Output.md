---
draft: false
doc_id: d-20260905-210539-32bda1
title: UAC 5 - Complete Studio Catalogue Output
added_date: "2026-09-05 21:05:39"
last_updated: "2026-09-05 23:53:11"
summary: "Complete Studio Catalogue output, accepted full data and durable guidance; ready for further Docs Viewer design."
ui_status: done
parent_id: d-20260908-171728-3c539a
---
# UAC 5 - Complete Studio Catalogue Output

## Outcome

Complete. Studio manages the full external Catalogue through ordinary Save, import and delete. The user accepted new-Work Save and the corrected Work preview, completed the thumbnail copy, and authorized code review and closeout. The Studio Catalogue production pause is lifted.

Both deliverables are complete:

1. A working Studio workflow that persists validated canonical edits and completes affected generated data and required media, with coherent membership and deletion cleanup.
2. Complete Work, Series and Detail JSON, discovery indexes, thumbnails and media references beneath `$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/generated/`.

## Settled Boundaries

- Works have optional singular `series_id`; ungrouped Works and empty Series are valid. Catalogue records have no publication state or primary-Work prerequisite.
- Save is the only ordinary completion action. Create, bulk, Detail-section, import and delete operations share the output-completion owner after the canonical transaction.
- Output/media or lookup failure keeps the saved canonical change and reports the incomplete step. A failed later editor read must not claim the canonical save failed. Fix the cause and use the ordinary owning operation; no automatic rollback or retry workflow is required.
- Full JSON maintenance uses current records and existing media references/versions. It reports missing thumbnails and performs no primary conversion/upload, thumbnail copy, version promotion or private lookup refresh. Initial thumbnails were copied once by the user in iCloud.
- Staging is `catalogue/media-staging/`; final thumbnails are `catalogue/generated/works/thumbs/` and `catalogue/generated/work_details/thumbs/`. Media-free records do not require staging. Missing configured roots have no fallback tree.
- Studio remains canonical owner. No active producer writes the frozen site/media archive or rebuilds the old public Catalogue pages, Recent or Catalogue Search.
- Docs provider switching, subject tools, tokens, reports, Gallery Lists, Media View integration, Build, Search, Publish and Deploy Repo are outside this delivery. Generated Catalogue availability is not public acceptance.

## Completed Steps

### 5.1 — Implement The Producer And Studio Workflow

- [x] Complete Work v6, Series v5, ordered nested Details and the three indexes through the existing producer; integrate Save/import/delete, required media and exact cleanup.
- [x] Preserve canonical validation, identity and revisions; remove retired publication/build machinery and obsolete tests.

Focused generator, service/API and fake-transport checks passed. The user committed this implementation as `027504145`.

### 5.2 — Generate The Full Catalogue And Accept Studio

- [x] Populate complete current JSON, complete the user's thumbnail copy and verify coverage.
- [x] Record user acceptance of new-Work Save and the Work preview fix; reuse focused evidence for other mutation behavior.

The accepted current-data comparison contains 1,935 Works, 139 Series and 2,681 Details in 2,077 JSON files. Every payload matches canonical records. All 4,616 required thumbnails are present with no unexpected files and match the archive counterparts; all 4,621 archived thumbnails remain unchanged. Large Detail cases include `00389` (523), `01050` (367), `00459` (256) and `01721` (119). Empty Series are covered by controlled fixtures.

The JSON-only maintenance correction and accepted preview fix are committed as `631b6fb52`. The earlier population snapshot containing test Work `01943` is historical and must not override later Studio edits.

### 5.3 — Code Review

- [x] Review producer, media, mutations, editor responses, tests and ownership boundaries.
- [x] Resolve all four findings: unnecessary staging for media-free records, misleading saved-response errors, obsolete staged-preview state, and unused public-producer helpers/tests.

Thirty distinct Python cases passed across affected runs, along with five direct saved-response formatting assertions, changed-source lint, 252 local Studio imports, check-runner syntax and whitespace checks. No unresolved Stage 5 finding remains. The user committed the review fixes as `4ca8c7c53`.

### 5.4 — Closeout

- [x] Transfer current producer, media and editor operations to durable guidance.
- [x] Reconcile Delivery Sequence, Change Backlog and the feature parent; lift the Studio production pause.
- [x] Hand the full data and payload description back to UAC 3 and record retention recommendations.

Closeout is documentation-only. Source/ownership review, 32 distinct local document targets, the 11 active Catalogue POST routes and watcher projections for all 16 changed documents passed. Implementation evidence was reused. No media processing, remote writes, manual Docs/Search build, public deployment, commit or push ran during closeout.

## Durable Transfer

| Responsibility | Current owner |
| --- | --- |
| Source identity, membership and architecture | [Catalogue Source Model](Catalogue_Source_Model.md), [Catalogue Architecture](Catalogue_Architecture.md) |
| Save, maintenance, output failure and private lookups | [Catalogue Build And Lookup Refresh](Catalogue_Build_And_Lookup_Refresh.md) |
| Consumer JSON, indexes and media references | [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md) |
| Work and Series workflows | [Catalogue Work Editor](Catalogue_Work_Editor.md), [Catalogue Series Editor](Catalogue_Series_Management.md) |
| Mutation/completion services and API surface | [Catalogue Services](Catalogue_Services.md), [Local Studio APIs](Local_Studio_APIs.md) |
| Derivatives, remote transport and confirmed versions | [Catalogue Media Pipeline Config](Catalogue_Media_Pipeline_Config.md), [Publish Media To R2](Publish_Media_To_R2.md) |
| Field/output inventory | [Catalogue Field Registry](Catalogue_Field_Registry.md) |

Manual evidence is the confirmed new-Work Save and preview acceptance, not exhaustive manual use of every editor action. Large-collection Save latency has not been measured. These limits are retained in the durable workflow guidance and `var/uac-5/code-review.md`; current coverage is in `var/uac-5/current-coverage.json`.

## Retain Or Retire

- Recommend archiving [UAC 4](UAC_4_Catalogue_Data_And_Editors.md) and this UAC 5 delivery: their canonical/editor and producer/media conclusions are transferred to the durable owners above.
- Temporary `var/uac-4/` and `var/uac-5/` working evidence is disposable after the user no longer needs closeout comparison. It is not runtime input.
- Retain the feature parent, Delivery Sequence, Change Backlog and UAC 3 design documents for the remaining unification work. No planning document or working evidence was deleted during this closeout.

## Next Outcome

[UAC 3](UAC_3_Tokens_Reports_And_Data_Model.md) is ready for the next bounded full-data design slice: token destinations, reports, Gallery Lists, selection and difficult Work/Series/Detail cases. Generated `documents` arrays remain empty; no canonical document is chosen. The coordinated local Docs provider switch and accepted public Catalogue-dependency projection require later deliveries. Batch New doc and public cutover remain in [Delivery Sequence](Analysis_Catalogue_Delivery_Sequence.md).

Retain the post-migration question about whether a Work needs a canonical image, including the `00389` photo-collection example. This closeout does not change that model.

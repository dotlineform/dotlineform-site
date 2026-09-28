---
draft: false
doc_id: d-20260927-221737-07fbbf
title: Related Galleries
added_date: "2026-09-27 22:17:37"
last_updated: "2026-09-28 18:47:00"
summary: Related Galleries implementation and durable contracts are ready; local visual review and retain-or-retire decision remain.
ui_status: in_progress
parent_id: d-20260428-000000-f5ff18
---
# Related Galleries

## Complete Result

Work Media View displays **Related galleries**: the Galleries explicitly assigned to that Work, followed by Galleries explicitly associated with the Work's Series. It removes duplicate links by exact Gallery ID. A Gallery's Work membership and its relevance to all Works in a Series are independent authoring decisions. A curated Gallery can contain Works from several Series without becoming related to every Work in any of them.

The Gallery New and Edit modals offer a checkbox labelled **Relates to all works in this series**. It applies only to the exact Series shown in the current Works editor context. Checking it adds that Series–Gallery association; unchecking it removes that association. The checkbox does not add or remove Works from the Gallery, change a Work's Series, or alter any other Series–Gallery association.

The [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) split is in place. RG.1 seeded and validated the canonical pairs, RG.2 implemented Gallery authoring and deletion ownership, RG.3 added the generated index and local/public reader configuration, RG.4 added Work Media View consumption, and RG.5 reviewed the complete code path. The user manually added a Gallery and toggled the checkbox at the RG.2 gate. RG.4 interaction and visual outcomes remain unrecorded; publication has not begun under this delivery.

## Canonical Association And Authoring

Studio owns a new canonical `studio/data/canonical/catalogue/series-galleries.json` containing exact Series–Gallery pairs. Keep the pairs unique and deterministically ordered, validate both IDs against current canonical definitions, and allow a Gallery to have no Series association or distinct associations with more than one Series. `galleries-by-work.json` remains the sole authority for Work membership. The new file records only the broader Series relevance decision.

The file was seeded once on 28 September 2026 from validated canonical Gallery membership: each Gallery's member Works identified one exact Series, yielding 302 pairs across 139 Series. The seed operation stopped on an empty or mixed-Series Gallery rather than guessing. After seeding, Work membership changes do not create, remove or infer Series–Gallery pairs. Matching numbers or titles never establish an association.

New Gallery defaults to unchecked. Edit Gallery loads the saved checkbox value for the displayed Series; changing that pair leaves any pair for another Series alone. The modal should name the exact Series beside the checkbox so its scope is clear. Bulk selection is already confined to Works listed in one Series, so its displayed Series is the exact context without another cross-Series check. When creating a Work with no Series, disable the checkbox. Saving a new Gallery and its checked association is immediate and independent of the still-unsaved Work draft; discarding that draft does not undo either saved definition or association.

The synchronous modal workflow has no pair-specific freshness or revision check. Gallery Save still uses its existing definition revision, and Gallery deletion still uses its existing definition and complete-member checks. A malformed or unknown saved pair fails exact canonical validation.

Removing a Work's Series assignment or deleting a Work leaves Series–Gallery pairs unchanged, even if no Work in that Series currently belongs to the Gallery. Unchecking the checkbox removes only the displayed Series–Gallery pair. Deleting a Gallery removes all of its pairs in the same canonical transaction as the Gallery deletion. Deleting a Series definition removes all of that Series' pairs in the same transaction; the existing rule still permits Series deletion only when it has no member Works. A stale or unknown pair is an error to repair, not a reason to infer a replacement.

## Generated Index And Media View

Refresh Catalogue derives a new compact Series-to-Galleries index from the canonical pair file and Gallery definitions. The consumer path is `working/generated/catalogue/series-galleries-index.json`, selected for Preview/public distribution. Key entries by exact Series ID and include the associated exact Gallery IDs and current titles in deterministic order; include an empty list for a valid Series with no associations. The index does not contain Work member lists and does not reuse the retired `series/series_index.json` schema. A Gallery title change updates index labels on Refresh.

The selected Work by-ID record already supplies `series_id` and its direct `work.galleries` ID/title links. Media View reads the new index for that exact Series, combines direct links first with Series links, and deduplicates by Gallery ID. It loads a Gallery by-ID record only when that link is opened; it does not scan other Work records, infer associations from Gallery membership, or add a per-Work `related_gallery_ids` field. If the Work has no Series, only its direct Gallery links appear. Missing or invalid required index data fails visibly rather than silently showing a partial related list. Exact Gallery membership remains distinguishable from Series relevance in all consumers.

Save persists the pair with the Gallery definition mutation and updates the Works editor's current canonical view. It invalidates the existing Refresh receipt but does not generate consumer JSON. Refresh includes the canonical pair file in its source revision, writes and verifies the new index, and makes the latest links available to local Docs Viewer. Docs Publish captures that selected index with the other Catalogue JSON; public readers see it after the ordinary publication and deployment steps. Neither Save nor Media View writes Work by-ID related arrays, and there is no separate background refresh or compatibility alias.

## Delivery Steps

### RG.0 — Readiness

- [x] Confirm the current Gallery New/Edit Series context, canonical transaction owner, Refresh receipt and generated/public artifact inventory; recheck the one-Series-per-Gallery seed condition against current canonical data.
- [x] Confirm the complete outcome and stop on an ambiguous seed, an unavailable exact Series context, or a consumer path that would require a second association authority.

**Gate:** the canonical pair and reader responsibilities are coherent against the current owners. This is a read-only checkpoint; it does not seed data or change code.

### RG.1 — Canonical Pairs And Initial Seed

- [x] Add strict canonical pair validation, an exact read model, transaction allowlisting and Refresh-receipt input ownership.
- [x] Seed current pairs from validated Gallery membership once, inspect the resulting Series/Gallery coverage, and keep the file as the only editable authority for Series relevance thereafter.

**Gate:** every saved pair has valid exact identities, the seed has no inferred or ambiguous association, and Save correctly marks generated output as needing Refresh. Review the canonical write before proceeding.

RG.1 evidence: the exact reader accepted 302 pairs for 302 Galleries and 139 Series, the new canonical path is allowlisted, and the existing Refresh status reports `needed: true` from the revised source revision. Refresh validates the pair file before writing a completion receipt. Focused Python lint, syntax, JSON and whitespace checks passed. No test or fixture was changed, and no Gallery pair Save, generated index or Publish operation was run.

### RG.2 — Gallery Authoring

- [x] Add **Relates to all works in this series** to New/Edit Gallery for the displayed exact Series, with New unchecked and no-Series Work creation disabled.
- [x] Save or remove only that pair alongside the Gallery definition operation; preserve unsaved Work edits, remove all pairs on Gallery or Series deletion, and leave pairs unchanged on Work deletion or Series reassignment.

**Gate:** the modal and service agree on exact Series scope and report saved or failed outcomes truthfully. Human review covers the checkbox wording, disabled state and modal behavior.

RG.2 evidence: the exact Gallery read returned its saved Series association; the service plans a changed pair alongside the Gallery definition, removes all Gallery pairs on Gallery deletion, and includes Series pair removal in the Series deletion transaction. The Work draft and Work deletion paths do not write the pair file. Focused Python and JavaScript lint, Python syntax and whitespace checks passed. No test or fixture was changed. The user added Gallery `307` and toggled the checkbox in the live modal, then approved continuation; its saved pair state is unchecked. The no-Series disabled state was not separately reviewed.

### RG.3 — Generated Index And Publication Selection

- [x] Generate and validate the new Series-to-Galleries index from canonical pairs and Gallery titles during Refresh; add it to the explicit Catalogue preparation/distribution inventory and reader configuration.
- [x] Keep missing or invalid inputs visible, preserve the current Refresh receipt and Publish boundaries, and verify that changing a pair does not rewrite per-Work related data.

**Gate:** a completed Refresh exposes the exact local mapping; the selected public artifact has the same prepared bytes when Publish is separately authorised. Do not Publish merely to close this local step.

RG.3 evidence: Refresh completed with a verified `catalogue_series_galleries_index_v1` map of all 139 valid Series. The local GET dispatcher read that exact map; Gallery `307` had no saved pair. The explicit Catalogue inventory selected `series-galleries-index.json` byte-for-byte from Working. Refresh wrote the new index, Gallery index and one Gallery by-ID record, with zero Work by-ID rewrites. The generator passes canonical pairs only into the separate index projection; Work by-ID projection has no pair input or related array. Focused lint, syntax, JSON and whitespace checks passed. Preview/public byte equality and Media View behavior await their separately authorised steps.

### RG.4 — Media View Consumption

- [x] Read the selected Work's exact Series and direct Galleries, resolve its Series links from the new index, present direct links first, and deduplicate by exact Gallery ID.
- [x] Keep Gallery by-ID reads on activation, handle no-Series Works and unavailable index data explicitly, and preserve existing Media View navigation and return behavior.

**Gate:** local Media View shows the intended distinct links for direct, Series-related, cross-Series curated and no-Series cases. The user reviews the interaction and visual result.

RG.4 evidence: the shared Work projector reads the index only for a Work with an exact Series, requires that Series entry, and combines direct Gallery links before distinct Series links. The presentation labels direct links **Contains this Work** and Series links **Related to this Series** under **Related galleries**; Gallery by-ID loading still occurs only on link activation, and the existing Gallery page and return controls remain in place. Work `00001` supplies a current local example: direct Gallery `009`, plus Series-related Gallery `144`. The canonical source currently has no no-Series Work or cross-Series curated Gallery, so those visual cases and all tactile interaction remain for the user to review. Focused JavaScript lint, whitespace, site-code projection check and site validation passed; no test or fixture was changed.

### RG.5 — Code Review

- [x] Review the bounded canonical, editor, generator, reader, config, documentation and generated changes for duplicate authority, stale proposal remnants, aliases and incomplete deletion paths; resolve findings.

**Gate:** findings are resolved and any affected evidence is refreshed. Test or fixture changes require their own agreed specification; ordinary lint, syntax, JSON, whitespace and selected existing checks are chosen only for credible risks at implementation.

RG.5 evidence: the review retained `series-galleries.json` as the only editable Series-relevance authority and left Work membership, Work reassignment and Work deletion independent. Gallery and Series deletion remove their owned pairs in the existing canonical transactions; no pair-specific freshness check or alias was added. Refresh source reading was restored to its established order, and the delivery no longer calls the implemented index path proposed. Preview capture now validates the selected index schema, exact ordered identities, titles, count and content version from its captured JSON bytes; direct local reading and inventory selection passed for the 139-Series Working index. Current canonical validation passed with 139 Series, 303 Galleries and 302 pairs. Focused Python and JavaScript lint, Python syntax, JSON, whitespace, site-code projection and site validation passed. One temporary Working HTML presentation proof embeds an old `docs_media_view_v1` payload without the now-required Gallery list; it is not accepted authoring syntax and was not changed or given a compatibility fallback. No permanent test or fixture was changed.

### RG.6 — Closeout

- [x] Record selected focused evidence and material limits; update the durable [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md) and [Catalogue Media View](Catalogue_Media_View.md) owners for the implemented local behavior.
- [ ] Confirm the local result with the user, then present this proposed delivery for retain-or-retire review.

**Gate:** the complete local result and its durable contracts are reviewable. Publish, commit, push and deployment remain separate explicit actions.

RG.6 evidence and limits: the durable index, reader and implementation-checklist contracts now describe the explicit pair authority, generated index, conditional Work read, distinct direct/Series link presentation and separate publication boundary. RG.1–RG.5 record the selected canonical, Refresh, local reader, code review, lint, syntax, JSON, projection and site-validation evidence. The user manually exercised the Gallery checkbox during RG.2; the Work Media View interaction and visual result, including the no-Series and cross-Series cases unavailable in current canonical data, remain unconfirmed. No permanent test or fixture was changed or run for this delivery. The new public index has been selected for distribution but has not been prepared or deployed; Preview/public byte equality is not claimed. Final local acceptance and the proposed delivery's retain-or-retire decision await user review.

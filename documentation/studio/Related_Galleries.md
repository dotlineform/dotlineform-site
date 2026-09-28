---
draft: false
doc_id: d-20260927-221737-07fbbf
title: Related Galleries
added_date: "2026-09-27 22:17:37"
last_updated: "2026-09-28 17:31:55"
summary: Proposed explicit Series-Gallery associations, Gallery checkbox authoring, a generated Series-Galleries index, and deduplicated Work Media View links.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Related Galleries

## Complete Result

Work Media View displays **Related galleries**: the Galleries explicitly assigned to that Work, followed by Galleries explicitly associated with the Work's Series. It removes duplicate links by exact Gallery ID. A Gallery's Work membership and its relevance to all Works in a Series are independent authoring decisions. A curated Gallery can contain Works from several Series without becoming related to every Work in any of them.

The Gallery New and Edit modals offer a checkbox labelled **Relates to all works in this series**. It applies only to the exact Series shown in the current Works editor context. Checking it adds that Series–Gallery association; unchecking it removes that association. The checkbox does not add or remove Works from the Gallery, change a Work's Series, or alter any other Series–Gallery association.

This is a proposed delivery. The [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) split is already in place; implementation, canonical seeding, generated output and publication have not begun under this proposal.

## Canonical Association And Authoring

Studio owns a new canonical `studio/data/canonical/catalogue/series-galleries.json` containing exact Series–Gallery pairs. Keep the pairs unique and deterministically ordered, validate both IDs against current canonical definitions, and allow a Gallery to have no Series association or distinct associations with more than one Series. `galleries-by-work.json` remains the sole authority for Work membership. The new file records only the broader Series relevance decision.

At implementation, seed the file once from current canonical Gallery membership: for each Gallery, collect its member Works' Series IDs and create a pair only when they identify one exact Series. A read-only inspection on 28 September 2026 found all 302 current Galleries have members in exactly one Series. Recheck before writing; stop on an empty or mixed-Series Gallery instead of guessing. After seeding, Work membership changes do not create, remove or infer Series–Gallery pairs. Matching numbers or titles never establish an association.

New Gallery defaults to unchecked. Edit Gallery loads the saved checkbox value for the displayed Series; changing that pair leaves any pair for another Series alone. The modal should name the exact Series beside the checkbox so its scope is clear. When creating a Work with no Series, disable the checkbox. Saving a new Gallery and its checked association is immediate and independent of the still-unsaved Work draft; discarding that draft does not undo either saved definition or association.

Removing a Work's Series assignment or deleting a Work leaves Series–Gallery pairs unchanged, even if no Work in that Series currently belongs to the Gallery. Unchecking the checkbox removes only the displayed Series–Gallery pair. Deleting a Gallery removes all of its pairs in the same canonical transaction as the Gallery deletion. Deleting a Series definition removes all of that Series' pairs in the same transaction; the existing rule still permits Series deletion only when it has no member Works. A stale or unknown pair is an error to repair, not a reason to infer a replacement.

## Generated Index And Media View

Refresh Catalogue derives a new compact Series-to-Galleries index from the canonical pair file and Gallery definitions. The proposed consumer path is `working/generated/catalogue/series-galleries-index.json`, with a matching selected Preview/public artifact. Key entries by exact Series ID and include the associated exact Gallery IDs and current titles in deterministic order; include an empty list for a valid Series with no associations. The index does not contain Work member lists and does not reuse the retired `series/series_index.json` schema. A Gallery title change updates index labels on Refresh.

The selected Work by-ID record already supplies `series_id` and its direct `work.galleries` ID/title links. Media View reads the new index for that exact Series, combines direct links first with Series links, and deduplicates by Gallery ID. It loads a Gallery by-ID record only when that link is opened; it does not scan other Work records, infer associations from Gallery membership, or add a per-Work `related_gallery_ids` field. If the Work has no Series, only its direct Gallery links appear. Missing or invalid required index data fails visibly rather than silently showing a partial related list. Exact Gallery membership remains distinguishable from Series relevance in all consumers.

Save persists the pair with the Gallery definition mutation and updates the Works editor's current canonical view. It invalidates the existing Refresh receipt but does not generate consumer JSON. Refresh includes the canonical pair file in its source revision, writes and verifies the new index, and makes the latest links available to local Docs Viewer. Docs Publish captures that selected index with the other Catalogue JSON; public readers see it after the ordinary publication and deployment steps. Neither Save nor Media View writes Work by-ID related arrays, and there is no separate background refresh or compatibility alias.

## Delivery Steps

### RG.0 — Readiness

- [ ] Confirm the current Gallery New/Edit Series context, canonical transaction owner, Refresh receipt and generated/public artifact inventory; recheck the one-Series-per-Gallery seed condition against current canonical data.
- [ ] Confirm the complete outcome and stop on an ambiguous seed, an unavailable exact Series context, or a consumer path that would require a second association authority.

**Gate:** the canonical pair and reader responsibilities are coherent against the current owners. This is a read-only checkpoint; it does not seed data or change code.

### RG.1 — Canonical Pairs And Initial Seed

- [ ] Add strict canonical pair validation, an exact read model, transaction allowlisting and Refresh-receipt input ownership.
- [ ] Seed current pairs from validated Gallery membership once, inspect the resulting Series/Gallery coverage, and keep the file as the only editable authority for Series relevance thereafter.

**Gate:** every saved pair has valid exact identities, the seed has no inferred or ambiguous association, and Save correctly marks generated output as needing Refresh. Review the canonical write before proceeding.

### RG.2 — Gallery Authoring

- [ ] Add **Relates to all works in this series** to New/Edit Gallery for the displayed exact Series, with New unchecked and no-Series Work creation disabled.
- [ ] Save or remove only that pair alongside the Gallery definition operation; preserve unsaved Work edits, remove all pairs on Gallery or Series deletion, and leave pairs unchanged on Work deletion or Series reassignment.

**Gate:** the modal and service agree on exact Series scope and report saved or failed outcomes truthfully. Human review covers the checkbox wording, disabled state and modal behavior.

### RG.3 — Generated And Published Index

- [ ] Generate and validate the new Series-to-Galleries index from canonical pairs and Gallery titles during Refresh; add it to the explicit Catalogue preparation/distribution inventory and reader configuration.
- [ ] Keep missing or invalid inputs visible, preserve the current Refresh receipt and Publish boundaries, and verify that changing a pair does not rewrite per-Work related data.

**Gate:** a completed Refresh exposes the exact local mapping; the selected public artifact has the same prepared bytes when Publish is separately authorised. Do not Publish merely to close this local step.

### RG.4 — Media View Consumption

- [ ] Read the selected Work's exact Series and direct Galleries, resolve its Series links from the new index, present direct links first, and deduplicate by exact Gallery ID.
- [ ] Keep Gallery by-ID reads on activation, handle no-Series Works and unavailable index data explicitly, and preserve existing Media View navigation and return behavior.

**Gate:** local Media View shows the intended distinct links for direct, Series-related, cross-Series curated and no-Series cases. The user reviews the interaction and visual result.

### RG.5 — Code Review

- [ ] Review the bounded canonical, editor, generator, reader, config, documentation and generated changes for duplicate authority, stale proposal remnants, aliases and incomplete deletion paths; resolve findings.

**Gate:** findings are resolved and any affected evidence is refreshed. Test or fixture changes require their own agreed specification; ordinary lint, syntax, JSON, whitespace and selected existing checks are chosen only for credible risks at implementation.

### RG.6 — Closeout

- [ ] Record selected focused evidence, material limits and the local/manual outcome; update the durable [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md) and [Catalogue Media View](Catalogue_Media_View.md) owners when the behavior ships.
- [ ] Confirm the local result with the user, then present this proposed delivery for retain-or-retire review.

**Gate:** the complete local result and its durable contracts are reviewable. Publish, commit, push and deployment remain separate explicit actions.

---
draft: false
doc_id: d-20261004-225006-3e9736
title: Subject And Context Thumbnails Delivery
added_date: "2026-10-04 22:50:06"
last_updated: "2026-10-04 23:02:59"
summary: Replace generated authoring-subject objects with one optional scalar subject field and display Work thumbnails in local and public Context lists.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Subject And Context Thumbnails Delivery

## Current And Next State

Status: proposed. The user requested this delivery document on 2026-10-04 after agreeing the shared scalar Subject direction and local/public Context thumbnail outcome. Documentation is authorized; implementation, test work, Working reconciliation, Publish, commit, push and deployment have not been authorized by this planning request.

Complete result: subject-enabled management rows and management response records use one optional `subject` string independently of authored-thumbnail assignments. Publish resolves thumbnail precedence for each public Context row and emits either `has_thumbnail: true`, a Work-valued `subject`, or neither. Local and public Context prefer an explicitly authored document thumbnail, then use the existing Work thumbnail when no authored assignment exists and the document has a Work subject. Source thumbnail metadata and Subject assignment update a retained local Context list through the existing committed-record notification.

Approved precedence on 2026-10-04: authored thumbnail first, otherwise Work thumbnail. The user created an Add image thumbnail for a Context document that also has a Work subject; source and management metadata confirm both assignments. This resolves the competing-thumbnail decision without changing either media owner.

Public manifest refinement on 2026-10-04: Publish emits only the selected thumbnail's field. Management rows may retain both fields; public Context rows never need both. An authored-thumbnail public row omits its Work subject even when the source declares one, so the reader manifest is not a complete public Work-association inventory.

Next: complete SCT-0, summarize the bounded implementation and Working reconciliation, and obtain implementation approval. Public verification requires a separately authorized Publish followed by user review through site-preview; do not treat shared runtime projection alone as delivery of updated public document data.

This standalone delivery is parented to [Planned Features](../Planned_Features.md). [Subject Associations](../data/subject-associations.md) owns Subject meaning and consumers, [Generated Data Contracts](../Generated_Data_Contracts.md#collection-manifest-ownership) owns manifest lifecycle, and [Media And Asset Handling](../Media_And_Asset_Handling.md) owns thumbnail storage and existing presentation. Follow [Development Checklist](../Development_Checklist.md) and [Development Workflow](../Development_Workflow.md).

## Requirements

### One Generated Subject Field

- Replace the generated row/API field `authoring_subject: {kind, key}` with optional scalar `subject`. Apply the management representation to every currently subject-enabled collection and the metadata/committed-response records its consumers use; do not silently enable Subject support in other collections.
- Exactly five ASCII digits represent a Work ID. Retain a string, including leading zeros: `"subject": "00635"`.
- A valid decoded relative folder target represents a Folder subject: `"subject": "projects/100 grasping hands"`. Preserve the current normalization, path safety and collection-specific Folder capability rules.
- In management metadata, omission represents None. Public manifest omission follows the thumbnail-selection rules below and does not prove the source has no Work subject. Do not emit an empty string, `null`, a `none` sentinel or an empty object. Reject malformed present values rather than interpreting them as None or coercing them into strings.
- Reserve a bare five-digit value for Work identity. Reject a Folder declaration whose normalized value would collide with that form; do not reinterpret it as a Work or automatically rewrite the source. Other valid relative folder targets remain supported. Current inspected Context Folder values contain path separators, so the proposed reservation has no observed collision.
- Retain explicit `work_id` and `folder_path` declarations in canonical Markdown, their existing assignment field group and collection capabilities. This delivery changes generated/read representations, not authoring syntax. Source validation still rejects conflicting declarations, invalid values and retired document `series_id` fields.
- Put classification and validation in the existing Subject owners for Python and JavaScript. Consumers may derive a typed internal value when needed; do not persist a second kind/key object or duplicate regex/path heuristics throughout reports and renderers.
- Retire the old generated row/API field and its readers together, without a compatibility alias or dual-shape fallback. Source fields and management assignment-group identity are separate owned contracts and are not aliases for the retired generated field.

Update subject-generation calculation, targeted manifest reconstruction and report validation coherently. Keep the existing generation marker's ownership and purpose; this delivery does not introduce another association index, cross-file receipt, Work registry lookup or stored thumbnail URL. None remains a valid document state and contributes no Subject-derived report placement.

### Public Projection

Publish builds the eligible Works/Context reader manifest and resolves authored-first thumbnail selection while generating each row. The public fields are mutually exclusive:

| Source state | Public thumbnail field |
| --- | --- |
| Authored thumbnail assigned, with any Subject | `has_thumbnail: true`; omit `subject` |
| No authored assignment and a valid Work subject | `subject: "00635"`; omit `has_thumbnail` |
| No authored assignment and Folder or None | Neither field |

Keep management `subject` independent of authored assignment: a management row can have both `subject` and `has_thumbnail: true` so editing, clearing assignments and association reports retain the full input state. Public rows describe the selected thumbnail only and do not expose Folder subjects. This selection applies to the public Context list, not to source declarations, private reports or by-ID rendering inputs. Keep Folder paths, management capabilities, drafts and other private authoring metadata out of public manifest rows. Other collections' existing public projection boundaries remain unchanged.

For example, a public Context row without an authored thumbnail becomes:

```json
{
  "doc_id": "d-20260801-212422-43b47c",
  "title": "10,000",
  "last_updated": "2026-10-03",
  "subject": "00635"
}
```

Do not add a separate public `work_id` field or publish the management manifest. Working continues to own only `manage-manifest.json`; temporary publication builds own public `manifest.json`, which reaches completed Preview and the configured repository destination through Publish. Do not hand-edit Preview or repository document payloads, create a Working public manifest, or weaken existing publication eligibility.

### Context Thumbnail Selection

- Select one thumbnail locally using authored-first precedence: if `has_thumbnail === true`, use the authored `<doc_id>-thumb.webp` from the exact Context document media owner; otherwise, if scalar `subject` is a Work ID, use that Work's Catalogue thumbnail; otherwise, reserve an empty slot when the collection needs thumbnail alignment. Publish applies the same precedence when projecting public rows, so the public reader renders the single selected field. An authored assignment takes precedence even when the document also has a Work subject.
- Resolve the Work alternative from scalar `subject` using the existing configured Catalogue thumbnail policy and local/public thumbnail base; for the current policy, Work `00635` resolves to `00635-thumb-96.webp`. Resolve authored thumbnails through the configured document-media root. Never hardcode an external workspace path, public host or rendition naming policy in the renderer.
- Reuse the existing decorative 64×64px collection thumbnail presentation, contain sizing, corners, spacing, lazy loading and asynchronous decoding. The image remains inside the document navigation control and opens the exact Context document with the title.
- Folder and None rows may display their authored thumbnail but make no Work-thumbnail request. When the full Context manifest contains any authored or Work-subject thumbnail, reserve aligned empty slots for rows without either across filtering and pagination. Collections without any applicable thumbnails retain compact text rows.
- Select by metadata, not image-request success. Missing image responses hide the selected artwork while preserving the slot and navigation; do not request a second thumbnail after an error. The Work alternative applies only when there is no authored assignment.
- Preserve the existing meaning of `thumbnail` and `has_thumbnail`: they describe an authored document assignment, not an inferred Work-thumbnail presence flag. Keep Source Add image, optional Create thumb and stored bytes with their current owner, and preserve authored-thumbnail behavior in other collections and Catalogue's Work-ID document-thumbnail behavior.
- Do not read every document, fetch a Catalogue record per row, probe the filesystem, infer subjects from titles, or generate/copy Work thumbnails merely to render the list. A syntactically valid Work ID does not require a registry-membership check to normalize its Subject.
- Use committed metadata after Subject changes and Source thumbnail-assignment changes to reevaluate the retained Context row without a discovery scan on Back. Clearing the authored assignment reveals the Work thumbnail when a Work subject remains; changing or clearing the Work subject preserves an authored thumbnail. Preserve filtering, sorting, paging, selection, title/draft presentation, exact routes and the current/caller retention model.

Catalogue already owns the existing Work-thumbnail production and public distribution; authored document thumbnails retain their existing document-media reference capture and distribution. Preserve both independently, including capturing an authored thumbnail for an eligible Work-subject document. Check that prepared Catalogue inventory supplies the referenced Work renditions through that owner; do not introduce another media producer, hidden body image, thumbnail copy tree or asset-discovery fallback. Presentation tolerance for a missing image does not relax Publish's existing required-asset validation.

### Existing Consumers And Scope

Projects' Folder/Work placement, Works coverage through member-Work subjects, Subject detail/assignment and committed-record notifications must consume the scalar representation without changing their domain behavior. Derived reports may retain purpose-specific typed internal or response data where that is their own contract; the simplified document metadata must be their single Subject input.

This delivery adds no Subject column, Series subject, folder assignment capability, source-field migration, document-image migration, Search schema/coverage change, new relationship product or generic thumbnail feature for Index, Search and Recents. Stored media, document identities, authored timestamps and readiness remain with their current owners. Test changes and execution require their own agreed scope; the product delivery does not authorize them implicitly.

## Deliverables

- [ ] Shared scalar Subject projection and validation in management manifests and response records, with all existing Subject consumers cut over and the old generated representation removed.
- [ ] Publish-owned public Context thumbnail selection, emitting either `has_thumbnail: true`, Work-only scalar `subject`, or neither through existing preparation and distribution owners.
- [ ] Configured local/public Context thumbnails with authored-first precedence, Work-subject alternative and committed Subject/thumbnail-change reconciliation using shared collection presentation.
- [ ] Complete docs-only Working reconciliation for affected subject-enabled collection manifests, preserving canonical source and media.
- [ ] Required shared/public runtime projection, focused evidence, user manual review and distinct bounded code review.
- [ ] Current durable Subject documentation, with manifest/media references updated only where the changed contract requires it.

## Process

1. Declare `work_id` or supported `folder_path` in canonical source, or use the existing Assign Subject action. Clearing the declaration gives None.
2. Working generation projects one scalar `subject` or omits it. Existing Subject details and association reports classify it through their shared owner.
3. Open Context locally. A row with an authored assignment displays its document thumbnail; otherwise a Work-subject row displays the existing Work thumbnail. Rows without either reserve aligned slots when applicable. Follow the title or image to the same exact document.
4. Change or clear a Subject through Assign Subject, or save a thumbnail assignment in Source, and return to the retained caller. The confirmed record reevaluates that row's thumbnail in memory using authored-first precedence. Clearing an authored assignment retains stored media and permits the Work alternative; changing a Work subject does not replace an authored thumbnail.
5. When separately authorized, run normal Publish. It selects the authored or Work thumbnail while building eligible public Context rows, emits only that thumbnail's field, completes Preview and distributes the same manifest and existing referenced media. Management rows retain their independent Subject and authored-thumbnail state.
6. Review the public result through site-preview. Commit, push and Deploy Public remain separate explicit actions.

## Delivery Steps

### SCT-0 — Readiness

- [ ] Confirm the scalar/public privacy rules against current source, Subject, builder, management-response, report and collection-list owners.
- [ ] Confirm every affected subject-enabled management collection, absence of ambiguous Folder declarations, existing thumbnail policy/transport and integration of the approved authored-first precedence.
- [ ] Confirm the cutover/reconciliation order and public runtime/data release hold; summarize the implementation and obtain approval.

Verification budget: bounded read-only source/config inspection and existing-data diagnostics. No prototypes, generated writes, executable tests or browser automation are needed for readiness.

Gate: stop for a real Folder-value ambiguity, inability to preserve the approved authored-first precedence, unavailable configured workspace, or a requirement that would expand source syntax, assignment capabilities or media production. Do not reopen the settled scalar representation, thumbnail precedence or public Folder exclusion without new evidence.

Record: proposed. Discussion established the field shape, privacy rule and thumbnail outcome; current source inspection confirms separate management/public manifests, existing Subject consumers and configured Catalogue thumbnail transport. On 2026-10-04 the user selected authored-first precedence after a real Context document demonstrated both assignments; its authored file, source assignment and generated presence flag were inspected. The subsequent public-manifest refinement assigns mutually exclusive thumbnail-field projection to Publish while preserving both independent fields in management rows. Implementation readiness and approval remain pending.

### SCT-1 — Subject Projection And Consumer Cutover

- [ ] Implement omission/Work/Folder scalar projection and boundary validation, preserving authoring declarations and exact capabilities.
- [ ] Update management metadata/committed records, report readers, detail/assignment and retained-list consumers together; remove old generated field handling without aliases.
- [ ] Update targeted merge/reconstruction and Subject-generation handling so no old-shape unselected rows survive the completed reconciliation.
- [ ] Project the chosen public Context thumbnail through the owning publication builder: authored `has_thumbnail: true`, otherwise Work-valued `subject`, otherwise neither; never both.

Verification budget: changed-path Python/JavaScript lint and bounded source review addressing parser agreement, omission, Folder collision rejection, public privacy and report/management wiring. Record exact changed targets and costs after owner inspection. An existing generator diagnostic or test selection must be separately identified and accepted before execution; no new test code or broad suite is included.

Gate: production consumers agree on the scalar contract, absent management Subjects mean None, and public Context rows contain only the selected thumbnail field without Folder values. Do not leave old/new shape fallbacks to bridge an incomplete cutover.

Record: not started.

### SCT-2 — Context Thumbnails And Retained Changes

- [ ] Select authored document thumbnails first, then resolve Work alternatives from scalar Subjects with configured policy/routes and the existing collection thumbnail helper.
- [ ] Preserve empty-slot alignment, missing-image navigation without request-based fallback and other collection-thumbnail behavior.
- [ ] Reconcile committed Subject and authored-thumbnail assignment changes, clearing and filtered/paged list state through the existing caller owner.

Verification budget: changed-path JavaScript lint and bounded source review of local/public policy transport, row identity and committed-change wiring. Visual alignment, click behavior and retained-list interaction remain user manual review; no browser test is added or run automatically.

Gate: local and public readers use the same authored-first thumbnail rule through their configured routes, preserving `has_thumbnail` meaning and both media owners without per-row record reads, image generation or navigation ownership changes.

Record: not started.

### SCT-3 — Generated Follow-Through And Public Review

- [ ] Reconcile affected Working collection output through justified complete docs-only collection builds, selecting the exact owners first. A global manifest-contract change justifies complete reconciliation; skip registered media producers and preserve source dates.
- [ ] Run `bin/site-code-update` for represented changed runtime/configuration files, inspect its exact tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`.
- [ ] Record Working scalar/None/report evidence and the limits of static public verification. Leave Search unchanged and do not edit generated JSON as authority.
- [ ] When separately authorized, run Publish and review eligible public Context rows and their thumbnails through site-preview, including mutually exclusive fields for authored-only, Work-only and both-assignment inputs, omission of both fields for unassigned Folder/None rows, and navigation.

Verification budget: the selected docs-only Working builds write replaceable output only for named affected collections; cost depends on their source volume and must be stated before running. Runtime projection writes only configured tracked destinations; projection/site validation are existing diagnostics with expected seconds-to-minutes cost. Before any Publish, state its real Preview, repository and remote-media effects. No test execution or browser automation is implied.

Gate: old management rows are fully reconciled and the public runtime is paired with new public manifest data before release. Public capability remains unverified until the separately authorized Publish and manual review; that gate cannot be replaced by a source diff or runtime projection check.

Record: not started. Publish and user public review are pending separate authorization.

### SCT-4 — Code Review

- [ ] Independently review the final bounded production, configuration and generated delta after implementation and selected evidence.
- [ ] Resolve duplicated classification, public privacy leaks, stale consumers, compatibility residue, targeted-merge inconsistencies and missing failure behavior within the approved scope.
- [ ] Record findings, resolutions and remaining evidence limits; rerun only checks affected by review changes.

Verification budget: focused source/diff review, with no repository-wide audit or automatic test expansion.

Gate: the complete Subject-to-thumbnail flow has clear owners, runtime/data cutover is coherent and no old generated representation remains active. Distinguish source/static evidence from user-confirmed local/public behavior.

Record: not started.

### SCT-5 — Closeout

- [ ] Transfer shipped Subject shape, classification, privacy and consumer rules to Subject Associations; correct directly affected manifest/media documentation without duplicating the specification.
- [ ] Record exact completed evidence, manual acceptance, public publication status and material omissions; close only the complete local/public outcome.
- [ ] Update Planned Features and recommend retaining this delivery for recent-work lookup until manual archive. Do not delete it without approval.

Verification budget: bounded documentation/source review and completion-evidence reconciliation. Do not repeat implementation checks merely for status bookkeeping.

Gate: no unfinished consumer cutover, generated reconciliation or public review is hidden inside a completed delivery. Commit, push and public deployment remain separately authorized.

Record: not started.

## Follow-on

None currently specified. New Subject types, source-syntax consolidation, thumbnail presentation in other reports, media cleanup or permanent test work require separately agreed scope; they are not prerequisites manufactured by this delivery.

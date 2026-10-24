---
draft: false
doc_id: d-20261024-000000-c21a76
title: Bulk Source Folder Relinking
added_date: "2026-10-24 00:00:00"
last_updated: "2026-10-24"
parent_id: d-20260428-000000-f5ff18
---
# Bulk Source Folder Relinking

## Requirements

Relink selected Works to one destination folder after their unchanged originals have been moved. Keep each Work's existing filename and all prepared media, dimensions, versions and staging flags. The user explicitly approved folder selection in bulk mode without image regeneration. Retain ordinary metadata and Gallery/Series editing in the same Save.

## Deliverables

- Bulk folder selection, with project-parent or direct-subfolder destinations and the existing configured media-source choice.
- Browser-owned matching of saved filenames against the already loaded destination list; Cancel and missing files preserve the draft.
- An explicit source-folder request alongside ordinary bulk metadata/memberships, persisted through current transaction and metadata-only completion owners.
- Durable behavior in [Catalogue Work Editor](../Catalogue_Work_Editor.md#relink-source-folder), lifecycle ownership in [Catalogue Save And Refresh](../Catalogue_Save_And_Refresh.md#work-media-authoring) and the maintained [Development Checklist](../Development_Checklist.md).

## Process

Move original files, select their Works in the displayed Series, choose a destination with either folder-open button beside project folder or project subfolder and confirm it. Both buttons share the same picker and relink action. To choose the other configured media source, use the media-source button, which opens its destination picker without changing the draft until confirmation. Save persists the common location with each saved filename and existing media retained; normal Refresh/Regenerate/Publish remain separate.

## Delivery Steps

- [x] **0 — Readiness:** the approved outcome fits the existing metadata-only bulk owner. The browser already holds selected records and the picker supplies destination filenames; Python owns only canonical persistence and existing queue effects. Main risks are draft loss on Cancel, unintended filename/media edits and accidentally entering single-Work image processing. Public runtime, real file moves, content verification, new media production and test changes are outside scope.
- [x] **1 — Implementation And Static Verification:** a focused browser owner records confirmed folder intent; the reused local modal accepts caller-owned folder rules and validation over its completed selection. Bulk Save accepts exactly the destination envelope and retains its existing no-media completion path. Verification budget: explicit changed-source JavaScript/Python lint, Python compilation, whitespace and bounded source review; seconds-long local checks with no live services, application writes or test code. Seven JavaScript owners and both changed Python files passed lint; both Python files compiled and whitespace checks passed. Review refinements passed focused lint for their three affected JavaScript owners. Evidence remains static.
- [x] **2 — Code Review:** completed the distinct final source/diff and mandatory Redundancy And Defensive Behavior Review. Traced confirm/Cancel, missing filenames, source choice, selection/success reset, combined Save, exact optional omission and unchanged filenames/media/dimensions/flags through existing completion. Source-only effects select Work metadata/private sources without adding media candidates or erasing previously queued image work. Removed obsolete source-wrapper visibility bookkeeping and the reused modal's empty-selection fallback; the new source-picker opener retains click-event isolation. Browser filename matching, the exact request envelope, existing picker confinement and ordinary target/write/queue requirements have concrete owners; no repeat source checks, extra listings, content hashes, image processing, compatibility aliases or recovery policy were added. No unresolved source findings remain. [Catalogue Work Editor](../Catalogue_Work_Editor.md#relink-source-folder) records durable behavior and evidence limits; the implementation is ready for user interaction review.
- [ ] **3 — Manual Acceptance And Closeout:** restart Local Studio and reload the editor. Confirm root/subfolder choices, differing filenames, missing-file feedback, Cancel with existing draft changes, configured-source choice, successful folder-only/combined Save and retained images/dimensions/versions. Live Save, filesystem changes, UI interaction and downstream lifecycle execution are unexercised by Codex; tests remain unchanged and unrun. Retain until ordinary-use acceptance, then recommend archive. Git and publication actions remain separate.

## Follow-on

The project-folder button uses the same picker and relink owner as the subfolder button. Source review confirmed stored control references, shared busy-state handling and bulk-only visibility for the added button; New Work keeps its existing subfolder import control. Focused lint passed for both changed JavaScript owners and whitespace checks passed. This adds no requests, server behavior, validation or media processing; UI interaction remains a manual check.

No additional product scope or test work is proposed. The source-folder action trusts unchanged originals and does no content verification or automatic repair.

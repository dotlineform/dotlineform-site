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

Relink one saved Work or multiple selected Works to a destination folder after unchanged originals have been moved. Keep each Work's existing filename and all prepared media, dimensions, versions and staging flags. The user approved bulk folder selection without image regeneration and its extension to single saved Works. Retain ordinary metadata and Gallery/Series editing in the same Save; separately requested image or attachment work retains its existing completion.

## Deliverables

- Single/bulk folder selection, with project-parent or direct-subfolder destinations and the existing configured media-source choice.
- Browser-owned matching of saved filenames against the already loaded destination list; Cancel and missing files preserve the draft.
- One shared source-folder request alongside single/bulk metadata/memberships, persisted through current transaction owners. Folder-only changes select metadata effects; single Save retains required processing for actual image/attachment changes.
- Durable behavior in [Catalogue Work Editor](../Catalogue_Work_Editor.md#relink-source-folder), lifecycle ownership in [Catalogue Save And Refresh](../Catalogue_Save_And_Refresh.md#work-media-authoring) and the maintained [Development Checklist](../Development_Checklist.md).

## Process

Move original files, open one saved Work or select multiple Works in the displayed Series, choose a destination with either folder-open button beside project folder or project subfolder and confirm it. Both buttons share the same picker and relink action. To choose the other configured media source, use the media-source button, which opens its destination picker without changing the draft until confirmation. Save persists the location with each filename and existing media retained; normal Refresh/Regenerate/Publish remain separate.

## Delivery Steps

- [x] **0 — Readiness:** the approved outcome fits the existing metadata-only bulk owner. The browser already holds selected records and the picker supplies destination filenames; Python owns only canonical persistence and existing queue effects. Main risks are draft loss on Cancel, unintended filename/media edits and accidentally entering single-Work image processing. Public runtime, real file moves, content verification, new media production and test changes are outside scope.
- [x] **1 — Implementation And Static Verification:** a focused browser owner records confirmed folder intent; the reused local modal accepts caller-owned folder rules and validation over its completed selection. Bulk Save accepts exactly the destination envelope and retains its existing no-media completion path. Verification budget: explicit changed-source JavaScript/Python lint, Python compilation, whitespace and bounded source review; seconds-long local checks with no live services, application writes or test code. Seven JavaScript owners and both changed Python files passed lint; both Python files compiled and whitespace checks passed. Review refinements passed focused lint for their three affected JavaScript owners. Evidence remains static.
- [x] **2 — Code Review:** completed the distinct final source/diff and mandatory Redundancy And Defensive Behavior Review. Traced confirm/Cancel, missing filenames, source choice, selection/success reset, combined Save, exact optional omission and unchanged filenames/media/dimensions/flags through existing completion. Source-only effects select Work metadata/private sources without adding media candidates or erasing previously queued image work. Removed obsolete source-wrapper visibility bookkeeping and the reused modal's empty-selection fallback; the new source-picker opener retains click-event isolation. Browser filename matching, the exact request envelope, existing picker confinement and ordinary target/write/queue requirements have concrete owners; no repeat source checks, extra listings, content hashes, image processing, compatibility aliases or recovery policy were added. No unresolved source findings remain. [Catalogue Work Editor](../Catalogue_Work_Editor.md#relink-source-folder) records durable behavior and evidence limits; the implementation is ready for user interaction review.
- [ ] **3 — Manual Acceptance And Closeout:** restart Local Studio and reload the editor. Confirm root/subfolder choices, differing filenames, missing-file feedback, Cancel with existing draft changes, configured-source choice, successful folder-only/combined Save and retained images/dimensions/versions. Live Save, filesystem changes, UI interaction and downstream lifecycle execution are unexercised by Codex; tests remain unchanged and unrun. Retain until ordinary-use acceptance, then recommend archive. Git and publication actions remain separate.

## Follow-on

### Single Work Extension

- [x] **Implementation And Verification:** both folder-field controls and the source selector now use the relink picker for a saved single Work. Shared draft intent replaces the bulk-only state/API without aliases; ordinary image selection releases that intent. Single Save sends location once through the shared server envelope and carries its known relink target into existing media selection. Only location changes are excluded from image preparation; actual filename changes, explicit regeneration and required attachment preparation remain active. Eight JavaScript owners and four Python owners passed focused lint; all four Python owners compiled and whitespace checks passed. Relevant refinements received focused lint only. This remains seconds-long static verification without test code, application writes or live services.
- [x] **Source Review:** completed distinct code and mandatory Redundancy And Defensive Behavior Review. Traced single/bulk selection and Save reset, Cancel, exact source identity including spaces, unchanged/restored location, location-once request shaping, shared envelope parsing, carried relink targets, ordinary filename/explicit-regeneration/attachment selection, saved-but-incomplete adoption and queue merge preservation. Removed the unused bulk-dirty override and bulk-only API/state names; kept one browser intent owner and one server envelope reader. Required picker filename matching, path confinement, exact request/target/write boundaries and selected media checks retain their existing owners without another directory listing, original-file probe, content hash, corpus audit or generic bypass. No unresolved source findings remain. Live behavior still requires the manual gate below.
- [ ] **Manual Acceptance:** restart Local Studio and reload. Confirm single folder-only Save, unchanged filename/media/dimensions/version, missing names, Cancel, source choice, restoring the original location, combined metadata/download edits and explicit image replacement/regeneration. Bulk behavior and the New Work import control remain within the same manual boundary. Live Save and browser interaction remain unrun by Codex; no test work is included.

Both folder-field buttons share the same picker and relink owner in saved single and bulk editing, with stored control references and shared busy-state handling. New Work keeps its existing subfolder import control. UI interaction remains a manual check.

No additional product scope or test work is proposed. The source-folder action trusts unchanged originals and does no content verification or automatic repair.

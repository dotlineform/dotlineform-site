---
doc_id: studio-ui-rules
title: "Studio UI Rules And Decision Log"
added_date: 2026-04-24
last_updated: 2026-04-27
parent_id: design
sort_order: 30
---
# Studio UI Rules And Decision Log

This document is the working record for Studio UI issues, decisions, and permanent standards that emerge from real fixes.

Use it to separate:

- one-off page corrections
- repeated issues that should become shared Studio rules
- local Codex changes that would otherwise disappear without PR discussion

Use this as the single capture surface for Studio UI work:

- open UI observations from IAB review
- one-off route corrections
- systemic findings that should become permanent rules
- local Codex change notes for UI work that did not go through PR review

## UI Rule Log 2026-04-27 / UI-041

- status: adopted
- route: `/studio/catalogue-work/`, `/studio/catalogue-work-detail/`, `/studio/catalogue-moment/`
- issue: replacing an existing source image and regenerating srcset derivatives was still possible through scripts, but the Studio editor pages only exposed media generation as part of save/update flows.
- triage: repeated catalogue-editor workflow gap
- reasoning: media readiness panels already show the resolved source path, so the refresh command belongs beside that path rather than behind a fake metadata edit or a broader site update action. The command should describe the local derivative boundary and avoid implying remote primary upload.
- outcome: added `Refresh media` to work, detail, and moment media readiness panels. The action calls `POST /catalogue/build-apply` with `media_only: true` and `force: true`, refreshes thumbnails, stages primary variants for publishing, and leaves metadata/page/json/search outputs unchanged.
- files changed:
  - `assets/studio/js/catalogue-work-editor.js`
  - `assets/studio/js/catalogue-work-detail-editor.js`
  - `assets/studio/js/catalogue-moment-editor.js`
  - `assets/studio/data/studio_config.json`
  - `scripts/catalogue_json_build.py`
  - `scripts/studio/catalogue_write_server.py`
  - `_docs_src/catalogue-work-editor.md`
  - `_docs_src/catalogue-work-detail-editor.md`
  - `_docs_src/catalogue-moment-editor.md`
  - `_docs_src/scripts-build-catalogue-json.md`
  - `_docs_src/scripts-catalogue-write-server.md`
  - `_docs_src/site-change-log.md`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - open each editor with an existing record, confirm `Refresh media` appears in the media readiness panel when source media exists, and confirm dirty forms disable the action
  - run a media-only build request and confirm only local image derivative steps run
- follow-up:
  - define a separate R2 publishing workflow before using this action to imply remote primary image replacement

## UI Rule Log 2026-04-27 / UI-040

- status: adopted
- route: `/studio/catalogue-moment/`
- issue: the moment editor could save and rebuild existing moments but delete only removed source metadata, leaving generated artifacts, media, and search records behind.
- triage: local workflow completion for the catalogue editor family
- reasoning: moment delete should match the user-facing meaning of deleting the item. The write service should preview server-side impact, block on validation issues, confirm in the browser, apply with record-hash conflict protection, and remove generated/site artifacts plus search entries in the same operation.
- outcome: added a Delete command to the moment editor and extended the shared catalogue delete preview/apply endpoints to support `kind: "moment"` with generated artifact cleanup, local media cleanup, moments-index update, and catalogue search rebuild.
- files changed:
  - `studio/catalogue-moment/index.md`
  - `assets/studio/js/catalogue-moment-editor.js`
  - `assets/studio/data/studio_config.json`
  - `scripts/studio/catalogue_write_server.py`
  - `_docs_src/catalogue-moment-editor.md`
  - `_docs_src/scripts-catalogue-write-server.md`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - open `/studio/catalogue-moment/?moment=keys`, confirm Delete is disabled when the local catalogue server is unavailable, then run delete preview/apply against the write server in dry-run mode for a known moment
- follow-up:
  - decide whether work/detail/series Studio deletes should adopt the same generated-artifact/search cleanup boundary

## UI Rule Log 2026-04-27 / UI-039

- status: adopted
- route: `/studio/catalogue-moment/`
- issue: existing moments had no normal editor surface, so routine metadata changes depended on the import page or direct JSON edits.
- triage: local workflow completion for the catalogue editor family
- reasoning: import and edit are different workflows. The import page should stay file-driven for introducing staged prose, while the editor should reopen one canonical source record, show readiness, save metadata, and run the same scoped update model as work and series editors.
- outcome: added a dedicated moment editor with search/open, source metadata fields, save plus optional site update, readiness panels, and staged prose import.
- files changed:
  - `studio/catalogue-moment/index.md`
  - `assets/studio/js/catalogue-moment-editor.js`
  - `assets/studio/data/studio_config.json`
  - `assets/studio/js/studio-config.js`
  - `_docs_src/catalogue-moment-editor.md`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - open `/studio/catalogue-moment/?moment=keys` and confirm the record loads, save controls are disabled when the local server is unavailable, and readiness sections render without overlapping the summary rail

## UI Rule Log 2026-04-26 / UI-038

- status: adopted
- route: `/studio/catalogue-new-work/`, `/studio/catalogue-work/`, `/studio/catalogue-new-series/`, `/studio/catalogue-series/`
- issue: the work and series forms still exposed legacy prose filename fields after prose publication moved to ID-derived `_docs_src_catalogue/` Markdown.
- triage: local workflow cleanup with shared editor-family impact
- reasoning: fields that no longer control publication should not stay in main edit forms. Keeping them visible would imply that changing the value affects public prose, while the actual workflow is staged Markdown import plus scoped site update.
- outcome: the new/edit work and series forms no longer render or submit `work_prose_file` or `series_prose_file`; prose remains available through the import readiness/action flow.
- files changed:
  - `assets/studio/js/catalogue-new-work-editor.js`
  - `assets/studio/js/catalogue-work-editor.js`
  - `assets/studio/js/catalogue-new-series-editor.js`
  - `assets/studio/js/catalogue-series-editor.js`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - inspect the four catalogue work/series routes and confirm the legacy prose filename fields are absent

## UI Rule Log 2026-04-26 / UI-037

- status: adopted
- route: `/studio/catalogue-work/`, `/studio/catalogue-series/`
- issue: the catalogue prose import success message still said generator lookup was a future task after generator lookup had been implemented.
- triage: local workflow copy correction
- reasoning: command success copy must describe the current workflow state. Completed implementation notes should not remain visible in user-facing status messages because they make a successful action look incomplete.
- outcome: work and series prose import success copy now says the imported source will publish on the next site update.
- files changed:
  - `assets/studio/data/studio_config.json`
  - `assets/studio/js/catalogue-work-editor.js`
  - `assets/studio/js/catalogue-series-editor.js`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - import staged work or series prose and confirm the success message no longer refers to a future generator task

## UI Rule Log 2026-04-26 / UI-036

- status: adopted
- route: `/studio/analytics/`, `/studio/library/`, `/studio/docs-import/`
- issue: the shared docs HTML import page still had a Library-specific route name, and the Analytics dashboard represented one related tag-tool cluster as four equal route-entry panels.
- triage: local dashboard information architecture refinement
- reasoning: route names should describe the workflow rather than one default scope when the page supports multiple docs scopes. Dashboard panels should represent meaningful user choices; closely related maintenance links can live as plain links inside one panel when separate cards create visual noise.
- outcome: the import route is now `/studio/docs-import/`, Analytics links to it with `scope=analysis`, Library links to it with `scope=library`, and the four Analytics tag route-entry panels were merged into one Tag tools panel with plain links.
- files changed:
  - `studio/docs-import/index.md`
  - `studio/analytics/index.md`
  - `studio/library/index.md`
  - `assets/studio/js/studio-config.js`
  - `assets/studio/data/studio_config.json`
  - `_docs_src/user-guide-docs-html-import.md`
  - `_docs_src/studio-runtime.md`
  - `_docs_src/studio.md`
  - `_docs_src/scripts-docs-management-server.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/analytics/` and confirm it has one Analysis import panel, one Tag tools panel with four plain links, and one Analytics plan panel
  - inspect `/studio/library/` and confirm its Import panel links to `/studio/docs-import/?scope=library`
  - open `/studio/docs-import/?scope=analysis` and `/studio/docs-import/?scope=library` and confirm the selector defaults to the requested scope
- follow-up:
  - use scoped query defaults for future cross-scope command pages when a dashboard enters the command with a natural domain default

## UI Rule Log 2026-04-26 / UI-035

- status: adopted
- route: `/studio/docs-import/`
- issue: the Docs HTML Import page and importer helper only exposed `studio` and `library`, even though the shared docs-management server and public viewer now support the `analysis` docs scope.
- triage: local allowlist drift with shared-scope impact
- reasoning: scope selectors must stay aligned with the docs-management write allowlist and the generated viewer scopes. A Studio command page should not silently coerce a valid scope such as `analysis` back to `library`.
- outcome: the import scope selector now includes `analysis`, the page preserves `?scope=analysis`, the HTML import helper accepts `_docs_src_analysis`, and new Analysis imports follow Library import defaults with `published: true` and `viewable: false` for manage-mode review.
- files changed:
  - `assets/studio/js/docs-html-import.js`
  - `assets/studio/data/studio_config.json`
  - `scripts/docs/docs_html_import.py`
  - `scripts/docs/docs_management_server.py`
  - `_docs_src/user-guide-docs-html-import.md`
  - `_docs_src/scripts-docs-management-server.md`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - open `/studio/docs-import/?scope=analysis` and confirm the scope selector remains on `analysis`
  - import a staged HTML file into `analysis` and confirm `Open viewer` opens `/analysis/?doc=<doc_id>&mode=manage`
- follow-up:
  - add parent-placement controls later if Analysis imports need to land directly under a nested section instead of the root-level review queue

## UI Rule Log 2026-04-25 / UI-034

- status: adopted
- route: `/docs/?mode=manage`, `/library/?mode=manage`
- issue: docs-viewer drag/drop reorder could appear to do nothing when sibling docs already had duplicate `sort_order` values, because the requested move wrote placement metadata without creating a unique visible order.
- triage: shared docs-viewer management refinement
- reasoning: the viewer should make a reorder action visibly true after drop. Preserving every sibling's existing sort value creates less write noise, but it allows old metadata collisions to keep producing unpredictable or unchanged order.
- outcome: drag/drop move now normalizes the destination sibling set to sparse unique `sort_order` values after every successful move. The one-step Undo record stores every doc whose placement changed and restores those records through one bulk restore endpoint.
- files changed:
  - `assets/js/docs-viewer.js`
  - `scripts/docs/docs_management_server.py`
  - `_docs_src/docs-viewer-management.md`
  - `_docs_src/scripts-docs-management-server.md`
  - `_docs_src/ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - create or find sibling docs with duplicate `sort_order` values, drag one after the other, and confirm the visible order changes
  - use index Undo and confirm every touched sibling returns to its previous parent/order
  - confirm move writes still trigger targeted same-scope search updates rather than full search rebuilds

## UI Rule Log 2026-04-25 / UI-033

- status: adopted
- route: `/docs/?mode=manage`, `/library/?mode=manage`
- issue: docs-viewer drag/drop placement made accidental child moves too likely because "after" was only a narrow lower-edge zone with a subtle row shadow.
- triage: shared docs-viewer interaction refinement
- reasoning: reordering needs an explicit insertion affordance, while parent creation should remain available without dominating the target row.
- outcome: row-position targeting now uses upper half for "inside" and lower half for "after"; the after state renders a visible insert line after the target row, and drop handling trusts the last highlighted target if the final drop event cannot resolve a row cleanly. Manage-mode capability probing also retries briefly so a page loaded during dev-server startup can become writable without a manual refresh.
- files changed:
  - `assets/js/docs-viewer.js`
  - `assets/css/main.css`
  - `_docs_src/docs-viewer-management.md`
  - `_docs_src/ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - in manage mode, drag over the lower half of a row and confirm a visible insert line appears after that row
  - drag over the upper half of a row and confirm the inside highlight appears
  - load manage mode before the docs-management server is ready and confirm controls become available after the server starts

## UI Rule Log 2026-04-25 / UI-032

- status: adopted
- route: `/docs/?mode=manage`, `/library/?mode=manage`
- issue: metadata-modal parent changes preserved the doc's previous `sort_order`, so moving a doc into another sibling set could place it unexpectedly relative to that new parent's children.
- triage: shared docs-viewer management refinement
- reasoning: parent changes and sibling ordering are related enough that the default should be predictable, while still allowing explicit numeric ordering when the user edits the sort field.
- outcome: when the metadata modal changes `parent_id` and the `sort_order` field is left at its original value, the client sends an append request and the docs-management server stores the next sparse sibling order under the new parent.
- files changed:
  - `assets/js/docs-viewer.js`
  - `scripts/docs/docs_management_server.py`
  - `_docs_src/docs-viewer-management.md`
  - `_docs_src/scripts-docs-management-server.md`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - edit a doc's parent in manage mode without changing `sort_order` and confirm it appears as the last child under the new parent
  - edit a doc's parent while changing `sort_order` manually and confirm the explicit value is preserved

## UI Rule Log 2026-04-25 / UI-031

- status: adopted
- route: `/docs/?mode=manage`, `/library/?mode=manage`
- issue: docs-viewer drag/drop could not populate an empty node because "drop inside" was inferred from existing children, so empty intended sections such as Archive behaved only as sibling targets.
- triage: shared docs-viewer interaction refinement
- reasoning: tree editability should not depend on a separate source schema flag or on whether a node already has children. Any doc node can become a parent through the viewer, while nodes remain loadable unless they are already special non-loadable docs such as `_archive`.
- outcome: drag/drop now uses row position: the upper/main row area moves inside the target node, while the lower edge moves after it. The index toolbar adds an icon-only one-step Undo for the most recent successful move in the current viewer session.
- files changed:
  - `_includes/docs_viewer_shell.html`
  - `assets/js/docs-viewer.js`
  - `assets/css/main.css`
  - `assets/studio/data/studio_config.json`
  - `_docs_src/ui-request-docs-viewer-index-drag-undo-task.md`
  - `_docs_src/docs-viewer-management.md`
  - `_docs_src/ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - in manage mode, drag a root doc onto empty Archive and confirm it becomes a child
  - use the index Undo action and confirm the doc returns to its prior parent/order
  - drag a doc onto an ordinary node without children and confirm that node gains a child while remaining loadable
- follow-up:
  - consider a more explicit visual drop-zone affordance if row-position targeting proves too subtle in manual use

## UI Rule Log 2026-04-24 / UI-030

- status: adopted
- route: `/docs/?mode=manage`, `/library/?mode=manage`
- issue: making one draft/non-viewable docs-viewer page viewable can leave it undiscoverable if a parent remains non-viewable, while making a parent viewable may or may not imply that descendants should also appear.
- triage: local workflow refinement
- reasoning: viewability is a tree workflow, not only a single-doc field toggle. The UI should preserve the one-button action but make implicit tree effects explicit before writing source files.
- outcome: `Make viewable` now detects non-viewable ancestors and prompts before including them. If the selected doc has descendants, it prompts for `all` or `selected`; cancel writes nothing. The action sends one bulk docs-management request so the source changes and docs/search rebuild happen once.
- files changed:
  - `assets/js/docs-viewer.js`
  - `assets/studio/data/studio_config.json`
  - `scripts/docs/docs_management_server.py`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - open a non-viewable child under a non-viewable parent in manage mode and confirm the ancestor prompt appears before write
  - open a non-viewable parent with children and confirm `selected`, `all`, and cancel paths behave as described
- follow-up:
  - replace native browser prompts with a structured modal if more docs-management bulk actions are added

## UI Rule Log 2026-04-24 / UI-029

- status: adopted
- route: `/studio/library/`, `/studio/docs-import/`
- issue: Studio-originated links into the Library viewer opened the public read-only route, even though the user had entered from an admin workflow and usually needed manage-mode controls.
- triage: local pattern refinement
- reasoning: route context matters. Public navigation to `/library/` should remain user-facing, but links that start inside Studio are admin links and should preserve that operational context when crossing into the shared Library viewer.
- outcome: the Library dashboard panel now opens `/library/?mode=manage`, and docs HTML import result viewer URLs for Library docs now append `mode=manage`.
- files changed:
  - `studio/library/index.md`
  - `scripts/docs/docs_management_server.py`
  - `_docs_src/studio-runtime.md`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - open `/studio/library/` and confirm the Library panel points to `/library/?mode=manage`
  - complete a Library import on `/studio/docs-import/` and confirm `Open viewer` opens `/library/?doc=<doc_id>&mode=manage`
- follow-up:
  - keep public header/nav Library links read-only unless they are explicitly part of a Studio/admin workflow

## UI Rule Log 2026-04-24 / UI-028

- status: adopted
- route: `/studio/docs-import/`
- issue: the import result confirmed the imported `doc_id` and exposed a viewer link, but the post-import review actions were not optimized for the two natural follow-ups: opening the Markdown source in the editor and checking the rendered viewer without losing the import page.
- triage: local pattern refinement
- reasoning: result panels should turn stable identifiers into direct workflow actions when the action is unambiguous. For import completion, the `doc_id` identifies the source doc and should open that source through the existing local docs-management boundary, while viewer links should preserve the command page state by opening a separate tab.
- outcome: the result `doc_id` now opens the Markdown source in VS Code via the docs-management `POST /docs/open-source` endpoint, and the result viewer link opens in a new browser tab.
- files changed:
  - `assets/studio/js/docs-html-import.js`
  - `assets/studio/js/studio-transport.js`
  - `assets/studio/data/studio_config.json`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - complete an import on `/studio/docs-import/`
  - click the result `doc_id` and confirm the source Markdown opens in VS Code
  - click `Open viewer` and confirm the viewer opens in a new browser tab while the import page remains open
- follow-up:
  - apply the same result-action pattern to future Studio command pages when a completed result exposes a stable source identifier and a separate public/runtime view

## UI Rule Log 2026-04-23 / UI-014

- status: adopted
- route: `/studio/docs-import/`
- issue: after selecting a different staged HTML file, the page could still show the previous file's success result, overwrite state, or warnings, which made the new selection look as if it had already been imported.
- triage: systemic
- reasoning: this is a shared command-page state-boundary rule. When a primary source selector changes, any result state derived from the previous selection becomes stale and should be cleared immediately unless the page is explicitly designed for side-by-side comparison.
- permanent rule: on Studio command pages, changing the primary selected source item must clear stale result, warning, and confirmation state from the prior selection. Keep durable user inputs such as toggles or scope selectors only when they are still valid across selections.
- enforcement point: Studio command/result pages such as `/studio/docs-import/` and future pages that load/apply one selected source item at a time
- files changed:
  - `assets/studio/js/docs-html-import.js`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - import one staged file on `/studio/docs-import/`
  - change the staged-file selector to a different file
  - confirm the prior result card, warnings list, and overwrite state clear immediately while the scope and prompt/meta toggles stay unchanged
- follow-up:
  - apply the same rule to future Studio pages that perform single-item preview/apply flows from a selector

## UI Rule Log 2026-04-23 / UI-013

- status: adopted
- route: `/studio/docs-import/`
- issue: after an overwrite succeeded, the import page could still show the earlier collision warning in its final warnings list, which made the success state read as contradictory even though the write had already completed.
- triage: systemic
- reasoning: this is a command-feedback boundary issue, not just a wording glitch. Warning copy that belongs only to a pre-confirmation state must not leak into the final success state, otherwise the user cannot tell whether the action really completed.
- permanent rule: for Studio command flows with preview or confirmation steps, the final success payload and final success UI must only show warnings that still apply after completion. Pre-confirmation blockers or overwrite warnings must be cleared or filtered once the action succeeds.
- enforcement point: Studio command/result pages such as `/studio/docs-import/` and the corresponding localhost server responses
- files changed:
  - `scripts/docs/docs_management_server.py`
  - `scripts/docs/docs_html_import.py`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - run a collision import on `/studio/docs-import/`
  - confirm the overwrite-required warning appears before confirmation
  - confirm the final success state does not keep the same collision warning afterward
- follow-up:
  - apply the same rule to future preview-then-apply Studio flows if they add multi-step confirmation states

## UI Rule Log 2026-04-23 / UI-012

- status: adopted
- route: `/studio/library/`, `/studio/docs-import/`
- issue: the Library dashboard had drifted after docs reorganization. One panel still pointed to an older planning stub, and another panel linked to a nonexistent Library docs target instead of a valid current workflow.
- triage: systemic
- reasoning: dashboard entry cards are route-entry actions, not decorative placeholders. When a domain dashboard link no longer resolves to a real maintained route or live doc surface, the fix should happen at the dashboard contract level rather than leaving stale panels in place. The better route-entry action for Library admin work is the import workflow itself.
- permanent rule: Studio dashboard panel links must always point to a current maintained route or live docs surface. If a dashboard domain lacks a valid target, remove the panel rather than leaving a dead doc/viewer link in place, and prefer real workflow entry points over legacy planning stubs.
- enforcement point: Studio dashboard routes, especially `studio/library/index.md`, and future dashboard-panel reviews
- files changed:
  - `studio/library/index.md`
  - `studio/docs-import/index.md`
  - `assets/studio/js/docs-html-import.js`
  - `assets/studio/css/studio.css`
  - `assets/studio/data/studio_config.json`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/library/` and confirm the dashboard now exposes `Published library` plus `Import`
  - confirm there is no remaining broken `Library docs` dashboard panel
  - inspect `/studio/docs-import/` and confirm the page uses shared Studio panel, field, button, and status patterns
- follow-up:
  - if another Studio dashboard still points at a stale plan/doc stub, replace it with a live workflow entry or remove it

## UI Rule Log 2026-04-22 / UI-011

- status: adopted
- route: `/studio/catalogue-work/`
- issue: the first Save plus Update rollout exposed that source-only work fields such as `notes` could disappear after save or reload because the editor rebuilt its editable baseline from focused lookup JSON rather than from the canonical work source record
- triage: systemic
- reasoning: the visible failure appeared on one route, but the underlying problem was a boundary mistake between canonical editing state and derived runtime context. Lookup payloads exist to support previews, related lists, and readiness guidance; they are not a safe source of truth for editable Studio forms.
- permanent rule: when a Studio editor mixes canonical source data with derived runtime lookup data, editable field baselines and stale-write protection must come from the canonical source record. Derived lookup payloads may enrich previews, related-record navigation, and readiness panels, but they must not overwrite source-only form state after save or reload.
- enforcement point: `assets/studio/js/catalogue-work-editor.js`, the corresponding editor docs, and future catalogue editors that consume both canonical source JSON and lookup payloads
- files changed:
  - `assets/studio/js/catalogue-work-editor.js`
  - `_docs_src/catalogue-work-editor.md`
  - `_docs_src/site-change-log.md`
  - `_docs_src/studio-ui-rules.md`
- local verification:
  - build the site to a separate destination
  - open `/studio/catalogue-work/?work=00001`
  - verify `Save` with `Update site now` off leaves pending publication and preserves the edited source field
  - verify a fresh-page `Save` with `Update site now` on keeps the edited source field and reports immediate publication success
  - verify the test record is restored afterward
- follow-up:
  - audit the detail/file/link/series editors for the same canonical-source versus lookup-state boundary if they add source-only fields later
  - prefer smoke tests against the current running write-service code, not an older long-lived localhost process

## Purpose

Use this document to:

- capture open UI issues as they are found
- record the triage note for a UI issue
- decide whether the issue is local or systemic
- capture the permanent rule when the issue should affect future work
- record where the rule is enforced
- leave a short local change log when work is done directly with Codex instead of through PR review

## Triage Labels

Every UI issue should start with one triage note:

- `one-off`
  The problem belongs to one route or one piece of markup only.
- `systemic`
  The problem exposes a shared primitive, token, layout pattern, or behavior that should be corrected at the design-system level.
- `pending`
  The issue has not yet been classified.

## Local Workflow

Because the primary workflow is local Codex work rather than PR-based review, each systemic fix should leave evidence in this document.

For local work, record:

- the route where the issue was seen
- the triage note
- the reasoning behind the classification
- the exact shared rule or non-rule decision
- the files changed
- the local verification method
- any follow-up work still needed

If a similar issue appears a second time, promote it to `systemic` unless there is a clear reason not to.

## Workflow

Use this sequence for Studio UI work:

1. Capture the issue here when it is observed in IAB or local browser testing.
2. Add the initial triage note as `pending`, `one-off`, or `systemic`.
3. Fix the issue locally.
4. Update the same entry with the outcome:
   - keep it `local-only` if it was truly route-specific
   - mark it `adopted` if it became a permanent Studio rule
5. Record the files changed and the local verification method.

## Standing Instruction

For every Studio UI issue reported and fixed:

1. Fix the issue.
2. Decide whether it is `one-off` or `systemic`.
3. Update this document with a new or amended entry.
4. Record the route, issue, triage, reasoning, files changed, verification method, and any permanent rule adopted.
5. If the issue is systemic, prefer changing the shared primitive, token, or pattern rather than adding a page-specific workaround.
6. Rebuild docs if this document changed.

## Working Rule

Use this decision test:

- if the fix should change only one route, keep it local
- if the fix changes a shared class, shared token, shared layout primitive, or common interaction, record it here as a permanent rule

## Entry Template

```text
## UI Rule Log YYYY-MM-DD / UI-###

- status: open | adopted | local-only | superseded
- route:
- issue:
- triage: pending | one-off | systemic
- reasoning:
- permanent rule:
- enforcement point:
- files changed:
- local verification:
- follow-up:
```

## Current Rules And Log

Add new entries at the top of this section.

## UI Rule Log 2026-04-22 / UI-027

- status: adopted
- route: `/studio/catalogue-work/`, `/studio/catalogue-work-detail/`, `/studio/catalogue-work-file/`, `/studio/catalogue-work-link/`, `/studio/catalogue-series/`
- issue: the catalogue editor family exposed separate top-level `Save` and `Rebuild` buttons even though the real user-facing distinction was usually “save source only” versus “save and publish/update now”. The `Rebuild` label leaked internal pipeline language into the main editing flow.
- triage: systemic
- reasoning: deferred publication is a legitimate workflow, especially for draft-heavy bulk editing, but the main command surface should describe that product choice rather than the underlying build mechanism.
- permanent rule: in catalogue editors, the primary command should be `Save`, paired with an adjacent `Update site now` choice that controls whether the save also publishes runtime changes immediately. If publication remains pending after save, expose `Update site now` as a secondary follow-up action near the runtime status rather than as a peer primary button.
- enforcement point: `studio/catalogue-work/index.md`, `studio/catalogue-work-detail/index.md`, `studio/catalogue-work-file/index.md`, `studio/catalogue-work-link/index.md`, `studio/catalogue-series/index.md`, their editor scripts, and `assets/studio/data/studio_config.json`
- files changed:
  - `studio/catalogue-work/index.md`
  - `studio/catalogue-work-detail/index.md`
  - `studio/catalogue-work-file/index.md`
  - `studio/catalogue-work-link/index.md`
  - `studio/catalogue-series/index.md`
  - `assets/studio/css/studio.css`
  - `assets/studio/js/catalogue-work-editor.js`
  - `assets/studio/js/catalogue-work-detail-editor.js`
  - `assets/studio/js/catalogue-work-file-editor.js`
  - `assets/studio/js/catalogue-work-link-editor.js`
  - `assets/studio/js/catalogue-series-editor.js`
  - `assets/studio/data/studio_config.json`
  - `assets/studio/js/studio-config.js`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - confirm the main action row on each catalogue editor now shows `Save`, `Delete`, and an `Update site now` toggle instead of a top-level `Rebuild` button
  - confirm a follow-up `Update site now` action appears only when runtime publication is pending
- follow-up:
  - none

## UI Rule Log 2026-04-21 / UI-026

- status: adopted
- route: Studio UI audit remediation tracking
- issue: the conformance spec and UI Audits section defined how to record findings, but they did not yet make it explicit where post-audit remediation progress and unresolved design decisions should live. That risked burying open work or pushing audit follow-up into the site change log.
- triage: systemic
- reasoning: audit docs should remain living records until a page is settled. That keeps findings, cleanup, remediation status, and unresolved decisions together without creating a separate ticket system.
- permanent rule: Studio UI audit docs must include explicit `Remediation Status` and `Open Decisions` sections. Keep post-audit remediation and unresolved decisions in the audit doc itself. Use [Site Change Log](/docs/?scope=studio&doc=site-change-log) only for implemented outcomes, and promote items into [UI Requests](/docs/?scope=studio&doc=ui-requests) only when they become real shared design/spec tasks.
- enforcement point: `_docs_src/studio-ui-conformance.md`, `_docs_src/ui-audits.md`
- files changed:
  - `_docs_src/studio-ui-conformance.md`
  - `_docs_src/ui-audits.md`
  - `_docs_src/ui-audit-catalogue-moment-import-20260421.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - confirm the conformance spec now requires `Remediation Status` and `Open Decisions`
  - confirm the current moment-import audit doc uses both sections
- follow-up:
  - use the same structure for future page audits

## UI Rule Log 2026-04-21 / UI-025

- status: adopted
- route: Studio shared input default-text treatment
- issue: Studio placeholder and default-value text was using the same muted tone as ordinary labels and helper text, which made default text too close to entered content. That was especially noticeable beside native empty date fields, whose browser-supplied placeholder parts already appear lighter.
- triage: systemic
- reasoning: default text is not the same semantic layer as ordinary muted UI copy. It needs a lighter dedicated tone so search placeholders, file placeholders, disabled values, and default-value displays all read clearly as unentered or unavailable state.
- permanent rule: Studio inputs should use a dedicated lighter default-text tone for placeholder text, default-value displays, and disabled values. Do not reuse the ordinary muted label/meta tone for default text.
- enforcement point: `assets/studio/css/studio.css`, `_docs_src/studio-ui-framework.md`, `_includes/ui_catalogue_notes/input.md`
- files changed:
  - `assets/studio/css/studio.css`
  - `_docs_src/studio-ui-framework.md`
  - `_includes/ui_catalogue_notes/input.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - confirm search placeholders on `/studio/catalogue-work/` are visibly lighter than entered text
  - confirm the file placeholder on `/studio/catalogue-moment-import/` uses the same lighter default-text treatment
  - confirm the input primitive page still demonstrates muted default text clearly
- follow-up:
  - none

## UI Rule Log 2026-04-21 / UI-024

- status: adopted
- route: Studio UI audit outcome selection
- issue: the conformance spec defined the possible page-audit outcomes, but it did not state which result should win when a page has both a real covered-area non-conformance and additional coverage gaps.
- triage: systemic
- reasoning: reviewers need one explicit precedence rule so outcome selection stays consistent. Without it, the same page could be reported as either `non-conforming` or `blocked by coverage gaps` depending on reviewer preference.
- permanent rule: if a page has any real non-conformance in a covered area, the overall audit outcome is `non-conforming`. Coverage gaps must still be reported, but they do not replace or soften that result. Use `blocked by coverage gaps` only when the unresolved issues are coverage-only.
- enforcement point: `_docs_src/studio-ui-conformance.md`
- files changed:
  - `_docs_src/studio-ui-conformance.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - confirm the conformance spec pass/fail section now defines outcome precedence explicitly
  - confirm the rule log records the precedence rule as permanent guidance
- follow-up:
  - none

## UI Rule Log 2026-04-21 / UI-023

- status: adopted
- route: Studio UI audit record storage
- issue: after adding the shared conformance spec, the repo still lacked a defined home and naming convention for the resulting page-level audit outputs. Without that, audit results would drift into ad hoc files or be lost in conversational history.
- triage: systemic
- reasoning: conformance reviews need durable, searchable records that are clearly separate from standards docs and change logs. A dedicated root docs-viewer section keeps audit evidence visible without conflating it with implementation history.
- permanent rule: save formal page-level Studio UI conformance reviews under the root [UI Audits](/docs/?scope=studio&doc=ui-audits) section. Use `ui-audit-<page-key>-<yyyymmdd>` doc ids and file names unless a later shared rule replaces that convention.
- enforcement point: `_docs_src/ui-audits.md` and `_docs_src/studio-ui-conformance.md`
- files changed:
  - `_docs_src/ui-audits.md`
  - `_docs_src/studio-ui-conformance.md`
  - `_docs_src/design.md`
  - `_docs_src/studio-ui-start.md`
  - `_docs_src/site-docs.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - confirm the new root-level section appears near the change log in docs navigation
  - confirm the conformance spec now states where audit outputs should be saved
- follow-up:
  - create the first real page-audit doc using this convention once the next formal conformance review is run

## UI Rule Log 2026-04-21 / UI-022

- status: adopted
- route: Studio UI audit workflow
- issue: the current Studio UI docs were strong enough to guide implementation and individual fixes, but there was no single conformance contract that made “check whether page X conforms to the full Studio standards” a repeatable, properly scoped audit. That left coverage gaps, fixability, and cleanup follow-up too implicit.
- triage: systemic
- reasoning: once multiple shared primitives and permanent rules exist, page review should not depend only on memory or expert judgment. The repo needs one explicit audit contract that defines authoritative sources, coverage states, required finding categories, and cleanup expectations.
- permanent rule: Studio page-level UI audits should use the shared conformance spec. Audit output must distinguish non-conformance from coverage gaps, report whether fixes belong in shared or local code, and record redundant CSS/markup cleanup that becomes possible after a fix.
- enforcement point: `_docs_src/studio-ui-conformance.md`, plus signposting from `design.md`, `studio-ui-start.md`, `ui-catalogue.md`, and `studio-ui-framework.md`
- files changed:
  - `_docs_src/studio-ui-conformance.md`
  - `_docs_src/design.md`
  - `_docs_src/studio-ui-start.md`
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect the docs viewer entries and confirm the conformance spec is reachable from the main Design/Studio UI entrypoints
  - confirm the new doc defines coverage states, audit workflow, output requirements, and cleanup reporting
- follow-up:
  - add published primitive pages for list shell, toolbar, and modal shell so more pages can eventually qualify for full conformance rather than covered-scope conformance only

## UI Rule Log 2026-04-21 / UI-021

- status: adopted
- route: `/studio/catalogue-work/`, `/studio/catalogue-work-detail/`, `/studio/catalogue-work-file/`, `/studio/catalogue-work-link/`, `/studio/catalogue-series/`, `/studio/bulk-add-work/`
- issue: the current-record panels in the catalogue editor family, plus the bulk-add-work workbook/preview-summary values, were still using the older muted `tagStudioForm__readonly` surface for display-only values. That now conflicts with the shared Readonly Display rule and creates styling/font-size drift between related Studio info panels.
- triage: systemic
- reasoning: these surfaces are display-only by design. They are not temporarily unavailable inputs and they are not editable form surfaces. The clearer shared contract is the Readonly Display treatment: keep the field shell and border, remove the filled background, and keep normal text styling. Leaving the older readonly surface here would preserve a distinction that the product no longer intends.
- permanent rule: display-only Studio value surfaces such as catalogue current-record panels, import-workbook paths, preview summaries, and readiness bodies should use the Readonly Display pattern. Reserve `tagStudioForm__readonly` for other cases only when a deliberately muted boxed surface is still part of the interaction design.
- enforcement point: the current-record renderers in `assets/studio/js/catalogue-work-editor.js`, `catalogue-work-detail-editor.js`, `catalogue-work-file-editor.js`, `catalogue-work-link-editor.js`, `catalogue-series-editor.js`, the bulk import route/template, and the shared Studio UI framework docs
- files changed:
  - `assets/studio/js/catalogue-work-editor.js`
  - `assets/studio/js/catalogue-work-detail-editor.js`
  - `assets/studio/js/catalogue-work-file-editor.js`
  - `assets/studio/js/catalogue-work-link-editor.js`
  - `assets/studio/js/catalogue-series-editor.js`
  - `assets/studio/js/bulk-add-work.js`
  - `studio/bulk-add-work/index.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect each catalogue editor current-record panel and confirm the values use transparent Readonly Display shells rather than muted filled boxes
  - inspect `/studio/bulk-add-work/` and confirm the workbook path and preview summary values use the same treatment
  - confirm links inside those display shells still inherit the surrounding text styling
  - confirm summary/readiness typography remains consistent across work, detail, file, link, and series editors
- follow-up:
  - review remaining non-catalogue uses of `tagStudioForm__readonly` separately rather than assuming every readonly surface should change with this rule

## UI Rule Log 2026-04-21 / UI-020

- status: adopted
- route: `/studio/catalogue-new-work/` and the shared work/series editor family
- issue: numeric metadata fields were still being rendered as native `type="number"` widgets, and catalogue-form label alignment depended on local top padding rather than an explicit shared rule. That mixed an implementation assumption into the UI and left label placement vulnerable to drift.
- triage: systemic
- reasoning: the primitive contract should follow user intent, not storage type. A numeric value often still wants the plain text-box presentation. Likewise, label placement needs a stable shared rule: centered against single-line controls and top-aligned only for multiline ones. Padding-based compensation obscures that rule and becomes fragile over time.
- permanent rule: across Studio form rows, numeric data should default to plain input boxes unless step controls are an explicit part of the interaction. In two-column field layouts, labels should be vertically centered with single-line controls and top-aligned only for multiline controls. Use explicit alignment classes rather than ad-hoc padding.
- enforcement point: `assets/studio/css/studio.css`, the shared work/series editor renderers under `assets/studio/js/`, the input primitive page, and the Studio UI framework docs
- files changed:
  - `assets/studio/css/studio.css`
  - `assets/studio/js/catalogue-new-work-editor.js`
  - `assets/studio/js/catalogue-new-series-editor.js`
  - `assets/studio/js/catalogue-work-editor.js`
  - `assets/studio/js/catalogue-series-editor.js`
  - `studio/ui-catalogue/input/index.md`
  - `_includes/studio_ui_catalogue_input_demo.html`
  - `_includes/ui_catalogue_notes/input.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/catalogue-new-work/` and `/studio/catalogue-new-series/` and confirm numeric fields still look like plain text boxes
  - confirm single-line field labels are centered with their inputs
  - confirm multiline field labels stay top-aligned
  - inspect the input primitive page and confirm the increment example is clearly optional rather than implied by numeric data
- follow-up:
  - if a future Studio task genuinely needs step actions, add them deliberately as page intent rather than deriving them from schema type

## UI Rule Log 2026-04-21 / UI-019

- status: adopted
- route: `/studio/ui-catalogue/input/`
- issue: the Studio catalogue did not yet publish a shared input primitive page, so field width, label placement, stepped numeric controls, and the distinction between disabled and always-readonly values were still implicit and at risk of drifting route by route.
- triage: systemic
- reasoning: text fields, dropdowns, and stepped numeric controls all express the same user intent of assigning one field value. The stable shared contract is the field shell plus an explicit composition wrapper for width and label layout. Without that separation, future page work would either overload `.tagStudio__input` with layout behavior or keep reinventing local wrappers.
- permanent rule: keep `.tagStudio__input` as the shared field shell and use `tagStudioField` for width, label placement, and add-on controls. Text inputs, selects, and stepped numeric controls should keep the same height as the small Studio button. Disabled means temporarily unavailable; values that are always display-only should use `tagStudio__input--readonlyDisplay` instead.
- enforcement point: `assets/studio/css/studio.css`, `studio/ui-catalogue/input/index.md`, `_includes/studio_ui_catalogue_input_demo.html`, `_includes/ui_catalogue_notes/input.md`, and the shared Studio/UI catalogue docs
- files changed:
  - `assets/studio/css/studio.css`
  - `studio/ui-catalogue/index.md`
  - `studio/ui-catalogue/input/index.md`
  - `_includes/studio_ui_catalogue_input_demo.html`
  - `_includes/ui_catalogue_notes/input.md`
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - build the site to a separate destination
  - inspect `/studio/ui-catalogue/input/` on desktop and mobile widths
  - confirm text input, select, and increment controls share one row height
  - confirm disabled and readonly-display states remain visually distinct
- follow-up:
  - adopt the shared field wrapper on live Studio routes only when a route review shows the current local field composition is drifting
  - if a future field needs richer adornments, extend the shared field wrapper rather than pushing layout rules into `.tagStudio__input`

## UI Rule Log 2026-04-20 / UI-015

- status: adopted
- route: `/studio/catalogue-work-file/`, `/studio/catalogue-work-link/`, `/studio/catalogue-series/`
- issue: the remaining editor-family pages with the shared `Open` / `Save Source` / `Save + Rebuild` / `Delete Source` row still had the longer first-pass labels and had not yet adopted the standard default button width.
- triage: systemic
- reasoning: these pages use the same partial-page editor-panel pattern as the work and work-detail editors, so keeping one editor-family action-row contract is more important than treating each page as a separate styling decision. The shorter `Rebuild` label still needs explicit supporting docs because it continues to save current edits before rebuilding scoped runtime output.
- permanent rule: across the catalogue editor family, the main editor action row should use the small button size, the standard default width, and the shortest accurate labels that fit that width. Document the save-then-rebuild behavior explicitly wherever `Rebuild` could otherwise be ambiguous.
- enforcement point: `studio/catalogue-work-file/index.md`, `studio/catalogue-work-link/index.md`, `studio/catalogue-series/index.md`, the matching runtime/config files under `assets/studio/`, and the three editor docs under `_docs_src/`
- files changed:
  - `studio/catalogue-work-file/index.md`
  - `studio/catalogue-work-link/index.md`
  - `studio/catalogue-series/index.md`
  - `assets/studio/data/studio_config.json`
  - `assets/studio/js/studio-config.js`
  - `assets/studio/js/catalogue-work-file-editor.js`
  - `assets/studio/js/catalogue-work-link-editor.js`
  - `assets/studio/js/catalogue-series-editor.js`
  - `_docs_src/catalogue-work-file-editor.md`
  - `_docs_src/catalogue-work-link-editor.md`
  - `_docs_src/catalogue-series-editor.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect each route and confirm `Open`, `Save`, `Rebuild`, and `Delete` all use the standard button width
  - confirm pressing `Enter` in the search input still opens the current file/link/series selection
  - inspect the related docs viewer pages and confirm the shorter labels are explained accurately
- follow-up:
  - keep member-list and add-member controls on the series page out of this rule unless they are reviewed explicitly

## UI Rule Log 2026-04-20 / UI-016

- status: adopted
- route: `/studio/catalogue-series/`
- issue: the member-work section duplicated its own heading, exposed both a `work_id` link and an `Open work` button for the same navigation target, showed member search even when the capped list was not truncated, and had not aligned `Add Work` / `Remove` with the current default-width button standard.
- triage: systemic
- reasoning: this section mixes navigation and membership commands inside a capped list surface. Keeping one heading, one navigation affordance, and conditional search makes the section easier to read and matches the work-detail list pattern already adopted elsewhere.
- permanent rule: in capped record lists, only show local search when the list is actually truncated. If a row already has a clear link to the target record, do not duplicate the same navigation inside the row action cluster. Keep row actions focused on local state changes.
- enforcement point: `studio/catalogue-series/index.md`, `assets/studio/js/catalogue-series-editor.js`, `assets/studio/data/studio_config.json`, `assets/studio/js/studio-config.js`, and `_docs_src/catalogue-series-editor.md`
- files changed:
  - `studio/catalogue-series/index.md`
  - `assets/studio/js/catalogue-series-editor.js`
  - `assets/studio/data/studio_config.json`
  - `assets/studio/js/studio-config.js`
  - `assets/studio/css/studio.css`
  - `_docs_src/catalogue-series-editor.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/catalogue-series/?series=139` and confirm the section has one `member works` heading
  - confirm the search row sits below the heading and only appears when more than 10 members are present
  - confirm member rows use the `work_id` link for navigation and only keep membership action buttons
- follow-up:
  - review whether `Make primary` should adopt a shared width rule separately rather than inferring it from this pass

## UI Rule Log 2026-04-20 / UI-017

- status: adopted
- route: `/studio/catalogue-new-work/`, `/studio/catalogue-new-work-detail/`, `/studio/catalogue-new-work-file/`, `/studio/catalogue-new-work-link/`, `/studio/catalogue-new-series/`
- issue: the Studio create-page family had drifted into a mix of older `Create Draft …` fallback labels, and some pages were missing the matching `ui_text` config blocks entirely. The create buttons also had not yet adopted the shared default width.
- triage: systemic
- reasoning: these routes form one family of create surfaces and should share one visible command contract. If the runtime reads `ui_text.<page_id>.create_button`, the config block should exist and the page should not depend on fallback text as the effective source of truth.
- permanent rule: across Studio create pages, the primary create button should use the label `Create` and the shared default width. If a Studio runtime reads config-backed UI text, the corresponding `studio_config.json` and `studio-config.js` block must exist.
- enforcement point: the five `studio/catalogue-new-*` page templates plus the matching create-page runtimes and config files under `assets/studio/`
- files changed:
  - `studio/catalogue-new-work/index.md`
  - `studio/catalogue-new-work-detail/index.md`
  - `studio/catalogue-new-work-file/index.md`
  - `studio/catalogue-new-work-link/index.md`
  - `studio/catalogue-new-series/index.md`
  - `assets/studio/data/studio_config.json`
  - `assets/studio/js/studio-config.js`
  - `assets/studio/js/catalogue-new-work-editor.js`
  - `assets/studio/js/catalogue-new-work-detail-editor.js`
  - `assets/studio/js/catalogue-new-work-file-editor.js`
  - `assets/studio/js/catalogue-new-work-link-editor.js`
  - `assets/studio/js/catalogue-new-series-editor.js`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect each create page and confirm the button label resolves as `Create`
  - confirm each create button uses the shared default width
- follow-up:
  - leave the fuller create-page doc rewrite for the broader page review rather than updating those docs piecemeal here

## UI Rule Log 2026-04-20 / UI-018

- status: adopted
- route: `/studio/bulk-add-work/`
- issue: the bulk import page runtime already used `getStudioText(..., "bulk_add_work.*")`, but there was no matching `ui_text.bulk_add_work` block, so the visible page copy and action labels were still coming from fallback strings. The action buttons also had not yet adopted the shared default width.
- triage: systemic
- reasoning: this is the same config-backed UI-copy issue already surfaced on other Studio pages. The bulk import page should follow the same rule: visible runtime copy comes from config, and shared command buttons use the shared width unless a later page review establishes a deliberate exception.
- permanent rule: if a Studio runtime reads `ui_text.<scope>.*`, the matching config block must exist in both config sources and should include the visible runtime copy actually used by the page. On the bulk import page, action labels should stay concise and use the shared default button width.
- enforcement point: `studio/bulk-add-work/index.md`, `assets/studio/js/bulk-add-work.js`, `assets/studio/data/studio_config.json`, and `assets/studio/js/studio-config.js`
- files changed:
  - `studio/bulk-add-work/index.md`
  - `assets/studio/js/bulk-add-work.js`
  - `assets/studio/data/studio_config.json`
  - `assets/studio/js/studio-config.js`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/bulk-add-work/` and confirm the visible headings, labels, and status-capable copy resolve from config
  - confirm the buttons read `Preview` and `Import`
  - confirm both buttons use the shared default width
- follow-up:
  - leave the broader bulk-import page wording and structure review for a later pass

## UI Rule Log 2026-04-20 / UI-014

- status: adopted
- route: `/studio/catalogue-work-detail/`
- issue: the work-detail editor still used the longer first-pass action labels `Save Source`, `Save + Rebuild`, and `Delete Source`, and its main panel actions were not yet using the standard default button width.
- triage: systemic
- reasoning: this editor follows the same partial-page editor-panel pattern as the work editor, so the same small-size/default-width button contract should apply. Shortening the labels also required the doc to explain that `Rebuild` still saves current edits before rebuilding the affected parent-work scope.
- permanent rule: on Studio editor panels such as the work and work-detail editors, command buttons should prefer the small size, the standard default width, and the shortest accurate labels that fit the shared width. If the shorter label hides important behavior, clarify the supporting doc rather than expanding the label again.
- enforcement point: `studio/catalogue-work-detail/index.md`, `assets/studio/data/studio_config.json`, `assets/studio/js/studio-config.js`, `assets/studio/js/catalogue-work-detail-editor.js`, and `_docs_src/catalogue-work-detail-editor.md`
- files changed:
  - `studio/catalogue-work-detail/index.md`
  - `assets/studio/data/studio_config.json`
  - `assets/studio/js/studio-config.js`
  - `assets/studio/js/catalogue-work-detail-editor.js`
  - `_docs_src/catalogue-work-detail-editor.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/catalogue-work-detail/` and confirm `Open`, `Save`, `Rebuild`, and `Delete` all use the standard button width
  - confirm pressing `Enter` in the search input still opens the current detail selection
  - inspect `/docs/?scope=studio&doc=catalogue-work-detail-editor` and confirm the save/rebuild roles are stated explicitly
- follow-up:
  - review the series/file/link editors separately rather than assuming every editor should rename its actions identically

## UI Rule Log 2026-04-20 / UI-013

- status: adopted
- route: `/studio/catalogue-work/`
- issue: the detail/file/link navigation sections were still mixing navigation entry points with button styling, and the detail search field was always visible in the header even when no detail rows were hidden.
- triage: systemic
- reasoning: these sections are navigation surfaces, not command rows. The `new` actions should read as links, not buttons, and the detail search only adds value when the fixed per-section limit is hiding rows from the page. Moving the search below the heading also keeps the section header cleaner.
- permanent rule: on navigation-summary sections, route-entry actions should render as links rather than command buttons. Per-section search should appear only when it is needed to reach items that are not already visible within the fixed on-page list limit.
- enforcement point: `studio/catalogue-work/index.md`, `assets/studio/js/catalogue-work-editor.js`, `assets/studio/data/studio_config.json`, `assets/studio/js/studio-config.js`, `assets/studio/css/studio.css`, and `_docs_src/catalogue-work-editor.md`
- files changed:
  - `studio/catalogue-work/index.md`
  - `assets/studio/js/catalogue-work-editor.js`
  - `assets/studio/data/studio_config.json`
  - `assets/studio/js/studio-config.js`
  - `assets/studio/css/studio.css`
  - `_docs_src/catalogue-work-editor.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/catalogue-work/?work=<id>` for a work with more than 10 detail rows and confirm the detail search appears below the section title
  - inspect the same route for a work with 10-or-fewer detail rows and confirm the detail search is hidden
  - confirm `new work detail →`, `new file →`, and `new link →` render as links rather than button-shaped controls
- follow-up:
  - when the site-wide link primitive is defined, review whether these route-entry links should adopt that shared treatment instead of keeping a page-local style

## UI Rule Log 2026-04-20 / UI-012

- status: adopted
- route: `/studio/catalogue-work/`
- issue: the work editor’s main action buttons were still using longer first-pass labels such as `Save Source`, `Save + Rebuild`, and `Delete Source`, and none of the actions in that editor panel were using the standard default button width.
- triage: systemic
- reasoning: within a partial-page editor panel, the small button size is already the right scale. The remaining drift was mainly label length and width consistency. The shorter labels also forced the doc to explain the current behavior more clearly, especially that `Rebuild` still saves current edits before running the scoped rebuild flow.
- permanent rule: within a Studio editor panel, command buttons should prefer the small button size and the standard default width unless a specific override is justified. Use the shortest accurate labels that fit the shared width. If an action label becomes shorter but more behaviorally ambiguous, fix the supporting doc copy rather than re-expanding the label.
- enforcement point: `studio/catalogue-work/index.md`, `assets/studio/data/studio_config.json`, `assets/studio/js/studio-config.js`, `assets/studio/js/catalogue-work-editor.js`, and `_docs_src/catalogue-work-editor.md`
- files changed:
  - `studio/catalogue-work/index.md`
  - `assets/studio/data/studio_config.json`
  - `assets/studio/js/studio-config.js`
  - `assets/studio/js/catalogue-work-editor.js`
  - `_docs_src/catalogue-work-editor.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/catalogue-work/` and confirm `Open`, `Save`, `Rebuild`, and `Delete` all use the standard button width
  - confirm pressing `Enter` in the search input still opens the current work selection, and the `Open` button remains a small explicit alternative
  - inspect `/docs/?scope=studio&doc=catalogue-work-editor` and confirm the save/rebuild roles are stated explicitly
- follow-up:
  - review the other catalogue editor pages later for the same label-width cleanup, but do not assume they should all rename their actions without checking the local docs

## UI Rule Log 2026-04-20 / UI-011

- status: adopted
- route: `/studio/series-tag-editor/`, `/studio/ui-catalogue/button/`
- issue: the series tag editor’s button-related status and warning text was rendering in a shared message area far above the `Add` / `Save` controls, which made the feedback feel detached from the related field and commands.
- triage: systemic
- reasoning: command feedback belongs to the command area, not to a distant generic message block. The button primitive needs to state that placement rule explicitly, and the live series tag editor should follow it so the primitive page reflects a real page pattern.
- permanent rule: button-related status, warning, and success copy must stay adjacent to the related command area. Place it on the same row only if space allows; otherwise put it in a dedicated row immediately below the relevant button row. Keep broader page context hints separate from local command feedback.
- enforcement point: `studio/series-tag-editor/index.md`, `studio/ui-catalogue/button/index.md`, `_includes/studio_ui_catalogue_button_demo.html`, `_includes/ui_catalogue_notes/button.md`, and the button/message guidance in `studio-ui-framework.md`
- files changed:
  - `studio/series-tag-editor/index.md`
  - `assets/studio/css/studio.css`
  - `studio/ui-catalogue/button/index.md`
  - `_includes/studio_ui_catalogue_button_demo.html`
  - `_includes/ui_catalogue_notes/button.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/series-tag-editor/` on desktop and mobile and confirm the feedback row sits directly below the `Add` / `Save` row inside the editor panel
  - inspect `/studio/ui-catalogue/button/` and confirm the first example and canonical markup show local button feedback placement
- follow-up:
  - review modal command feedback after the basic page sweep and apply the same adjacency rule where relevant

## UI Rule Log 2026-04-20 / UI-010

- status: adopted
- route: `/studio/series-tag-editor/`, `/studio/ui-catalogue/button/`
- issue: the series tag editor’s `Add` and `Save Tags` buttons sit directly beside the tag input field, which makes them the clearest live use case for the small command-button pattern. The label `Save Tags` also overstates the action relative to the button-width guidance.
- triage: systemic
- reasoning: this is the first direct live-page adoption of the new button contract, so the primitive page should show the same field-row pattern explicitly. The page fix and the primitive reference need to move together or the pattern stays abstract.
- permanent rule: when a command button sits beside a text field in the same row, use the small button size and the standard default width unless a specific override is justified. Prefer the shortest accurate label that fits the shared width, for example `Save` rather than `Save Tags`.
- enforcement point: `studio/series-tag-editor/index.md`, `studio/ui-catalogue/button/index.md`, and `_includes/ui_catalogue_notes/button.md`
- files changed:
  - `studio/series-tag-editor/index.md`
  - `studio/ui-catalogue/button/index.md`
  - `_includes/studio_ui_catalogue_button_demo.html`
  - `_includes/ui_catalogue_notes/button.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/series-tag-editor/` and confirm `Add` and `Save` are the same default width beside the tag field
  - inspect `/studio/ui-catalogue/button/` and confirm the first example now shows the field-row pattern explicitly
- follow-up:
  - use the same field-row rule when reviewing other input-adjacent buttons during the wider button sweep

## UI Rule Log 2026-04-20 / UI-009

- status: adopted
- route: `/studio/ui-catalogue/button/`
- issue: the first button primitive draft was still mixing command buttons with navigation-style anchor buttons and toolbar-forward assumptions. The requirement is actually narrower: buttons are commands only, toolbar is optional and separate, and the initial contract should stay minimal.
- triage: systemic
- reasoning: keeping the primitive small is more important than speculating about future button families. The button page should establish role boundaries, two sizes, standard width guidance, and modal default-action behavior without pulling in link patterns, toolbar patterns, or special destructive styling.
- permanent rule: Studio buttons are command controls only. Navigation actions should move to a link pattern. The shared button contract currently defines two sizes, a standard width target, bold default-modal action, and no special destructive styling by default. Do not use a panel as the grouping device when buttons need a boundary.
- enforcement point: `studio/ui-catalogue/button/index.md`, `_includes/studio_ui_catalogue_button_demo.html`, `_includes/ui_catalogue_notes/button.md`, `assets/studio/css/studio.css`, and the button guidance in `studio-ui-framework.md`
- files changed:
  - `studio/ui-catalogue/button/index.md`
  - `_includes/studio_ui_catalogue_button_demo.html`
  - `_includes/ui_catalogue_notes/button.md`
  - `assets/studio/css/studio.css`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/ui-catalogue/button/` on desktop and mobile
  - confirm the page no longer shows anchor-as-button or toolbar-subset examples
  - confirm modal default action is bold and default-width behavior is shown with `OK` and `Cancel`
- follow-up:
  - run a later consistency sweep on live Studio pages for navigation-like buttons and overlong labels such as `Save Tags`

## UI Rule Log 2026-04-20 / UI-008

- status: adopted
- route: `/studio/ui-catalogue/button/`
- issue: Studio currently uses one shared command-button class across editor pages, modal actions, and toolbar-style action rows, but the role boundary is still blurry because clickable pills and docs-viewer management buttons sit nearby as similar-looking controls.
- triage: systemic
- reasoning: the button primitive needs to establish scope before visual refinement. The immediate problem is not missing color variants; it is unclear ownership of command buttons versus pills and toolbar subsets. The first primitive page should therefore capture the shared baseline and the drift explicitly, rather than pretending the emphasis system is already solved.
- permanent rule: the button primitive covers command buttons only. Clickable pills are a separate primitive. Modal actions stay within the button primitive, but toolbar remains an optional composition primitive to define separately.
- enforcement point: `studio/ui-catalogue/button/index.md`, `_includes/studio_ui_catalogue_button_demo.html`, `_includes/ui_catalogue_notes/button.md`, and the shared `tagStudio__button` baseline in `assets/studio/css/studio.css`
- files changed:
  - `studio/ui-catalogue/button/index.md`
  - `_includes/studio_ui_catalogue_button_demo.html`
  - `_includes/ui_catalogue_notes/button.md`
  - `studio/ui-catalogue/index.md`
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/ui-catalogue/button/` on desktop and mobile
  - confirm the page establishes the command-button baseline and explicitly excludes clickable pills from this primitive
- follow-up:
  - refine the button contract toward smaller role boundaries and a clearer size/width model once the first page is in place

## UI Rule Log 2026-04-20 / UI-007

- status: adopted
- route: `/studio/`
- issue: the Studio landing page needed real panel-background image assignments, but the chosen source width is a design-time decision that should stay visible and adjustable rather than being embedded as hardcoded width-specific filenames in the page markup. The data shape also needed to make clear that a route can share a default width without forcing every panel to use the same source size, and that the asset naming convention is deliberate.
- triage: systemic
- reasoning: the image-fit behavior belongs to the primitive, while the chosen source asset and width belong to the page composition. On Jekyll-rendered pages, that design choice should be expressed through shared data so future panel-size changes do not require searching for scattered literal filenames.
- permanent rule: keep Jekyll-rendered Studio panel-link background-image selections in shared page data such as `_data/studio_panel_images.json`. Treat widths like `800` or `1200` as explicit design variables for the route, not implicit primitive defaults. Use a page-level default width plus optional per-panel overrides, and keep the asset filename pattern explicit as `{asset_id}-{variant}-{width}.{format}`.
- enforcement point: `_data/studio_panel_images.json`, `studio/index.md`, and the panel primitive notes/docs
- files changed:
  - `_data/studio_panel_images.json`
  - `studio/index.md`
  - `_includes/ui_catalogue_notes/panel.md`
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/config-studio-config-json.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/` on desktop and mobile
  - confirm all four landing panels render with background images from `assets/studio/img/panel-backgrounds/`
  - confirm the page markup reads the chosen image width from `_data/studio_panel_images.json`
- follow-up:
  - if another Jekyll-rendered landing/dashboard page adopts image panels, add its route-specific image choices to the same data file or a closely related shared data source

## UI Rule Log 2026-04-20 / UI-006

- status: adopted
- route: `/studio/ui-catalogue/panel/`
- issue: the image-fill panel-link example had drifted into treating white text as the default primitive behavior, even though dark text is the site-wide default. The catalogue also was not yet showing the contrast override as an explicit reusable code pattern.
- triage: systemic
- reasoning: the image-fill behavior and the contrast treatment are different concerns. The primitive should stay neutral by default and the working reference should show common design-led overrides in code when they materially affect how the primitive is applied on real pages.
- permanent rule: `tagStudio__panelLink--image` keeps the default dark text and centered `cover` image behavior. Use `tagStudio__panelLink--imageContrast` as the explicit override when a selected image needs white text and a stronger overlay. Studio panel-link background images should be selected at design time from `assets/studio/img/panel-backgrounds/`.
- enforcement point: `.tagStudio__panelLink--image` and `.tagStudio__panelLink--imageContrast` in `assets/studio/css/studio.css`, plus the panel primitive examples and notes
- files changed:
  - `assets/studio/css/studio.css`
  - `assets/studio/img/panel-backgrounds/.gitkeep`
  - `studio/ui-catalogue/panel/index.md`
  - `_includes/studio_ui_catalogue_panel_demo.html`
  - `_includes/ui_catalogue_notes/panel.md`
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/ui-catalogue/panel/` and confirm the base image panel keeps dark text
  - confirm the contrast override example uses white text and a stronger overlay
  - confirm the code samples show both the neutral image variant and the explicit contrast override
- follow-up:
  - add actual design-time background image files under `assets/studio/img/panel-backgrounds/` before wiring image panels onto live Studio routes
## UI Rule Log 2026-04-20 / UI-005

- status: adopted
- route: `/studio/`, `/studio/ui-catalogue/panel/`
- issue: the shared panel-link variation was constraining paragraph copy with an internal text-measure cap, which made the text look like it was wrapping inside an unspecified inner column. On the `/studio/` landing page, the equal-fill two-column layout also made the short-copy entry panels feel over-wide and visually sparse.
- triage: systemic
- reasoning: both issues affect how the primitive should be reused, not just how it is coded. The panel-link contract needs explicit design guidance as well as CSS behavior so the working reference can steer page composition instead of documenting code in isolation.
- permanent rule: primitive definitions may include design guidance when layout choices materially affect correct reuse. For panel-link cards, copy should wrap to the panel width, and short-copy landing-page entry panels may use narrower centered columns instead of full-width equal-fill tracks.
- enforcement point: `.tagStudio__panelLink` in `assets/studio/css/studio.css`, `/studio/` layout rules, and the panel primitive docs
- files changed:
  - `assets/studio/css/studio.css`
  - `assets/css/main.css`
  - `_includes/ui_catalogue_notes/panel.md`
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/` and confirm the entry panels are narrower and centered
  - confirm panel-link copy wraps to the card width rather than an implicit inner measure
  - inspect `/studio/ui-catalogue/panel/` and confirm the design-guidance notes are present
- follow-up:
  - if another panel-link route feels too sparse or too dense, adjust the shared composition guidance first before introducing route-local overrides

## UI Rule Log 2026-04-20 / UI-004

- status: adopted
- route: `/studio/`, `/studio/analytics/`, `/studio/library/`, `/studio/search/`
- issue: the Studio landing page and the analytics/library/search dashboards were using two duplicated card-panel patterns. The analytics/library/search cards also sized themselves to content, which made panel height drift with copy instead of staying a deliberate design object.
- triage: systemic
- reasoning: these cards are a real panel variation, not a one-off page layout. Keeping them duplicated in `assets/css/main.css` would keep the primitive hidden and encourage local drift. The intended behavior is fixed-height, whole-panel-clickable static navigation with optional image fill.
- permanent rule: clickable panel-navigation cards must use the shared Studio panel-link variation in `assets/studio/css/studio.css`. Their height is fixed at design time, and copy must be edited to fit the panel rather than stretching the panel to fit content.
- enforcement point: `.tagStudio__panelLink` and `.tagStudio__panelLink--image` in `assets/studio/css/studio.css`
- files changed:
  - `assets/studio/css/studio.css`
  - `assets/css/main.css`
  - `studio/index.md`
  - `studio/analytics/index.md`
  - `studio/library/index.md`
  - `studio/search/index.md`
  - `studio/ui-catalogue/panel/index.md`
  - `_includes/studio_ui_catalogue_panel_demo.html`
  - `_includes/ui_catalogue_notes/panel.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/ui-catalogue.md`
- local verification:
  - inspect `/studio/`, `/studio/analytics/`, `/studio/library/`, and `/studio/search/`
  - confirm the clickable panels share one fixed-height treatment
  - confirm panel height stays stable when card copy differs slightly
  - confirm hover/focus states still treat the whole panel as the click target
- follow-up:
  - if a future dashboard panel needs more room, add an explicit shared size modifier instead of letting content auto-size the card

## UI Rule Log 2026-04-20 / UI-003

- status: adopted
- route: `/studio/ui-catalogue/panel/`
- issue: panel nesting is a real container use case, so treating the first apparent nested-shell problem as a pure demo-environment artifact would hide a shared composition requirement.
- triage: systemic
- reasoning: for this project, the primitive catalogue is meant to expose hidden one-off fixes in live pages. If a primitive fails in the catalogue but looks fine on a route, that route may simply be compensating for the primitive locally. The catalogue should pressure the shared source rather than preserve legacy behavior by default.
- permanent rule: when a primitive can validly compose with itself, test that case in the catalogue and prefer fixing the primitive or shared composition contract over documenting page-local compensation. Future design reliability takes priority over preserving accidental legacy behavior.
- enforcement point: `ui-catalogue.md`, primitive docs under `_docs_src/`, and shared primitive CSS when the failure is systemic
- files changed:
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `studio/ui-catalogue/panel/index.md`
  - `_includes/studio_ui_catalogue_panel_demo.html`
  - `_includes/ui_catalogue_notes/panel.md`
  - `assets/studio/css/studio.css`
- local verification:
  - build docs payloads and the site to a separate destination
  - inspect the nested panel example on `/studio/ui-catalogue/panel/`
  - confirm the inner panel reads as subordinate containment without page-local overrides
- follow-up:
  - use the same rule when defining future primitives that can self-compose
  - audit live pages for obsolete local compensation after shared primitive fixes land

## UI Rule Log 2026-04-20 / UI-002

- status: adopted
- route: `/studio/ui-catalogue/panel/`
- issue: the first panel primitive reference wrapped the live examples in outer `.tagStudio__panel` sections and arranged the variants in a horizontal comparison grid. That made the editor variant appear to overlap its container and made edge inspection noisy.
- triage: systemic
- reasoning: the visible defect came from the primitive catalogue template, not from the shared `tagStudio__panel--editor` variant itself. If the catalogue page introduces nested-shell artifacts, future page work can inherit false assumptions about which primitive is broken.
- permanent rule: primitive catalogue pages must show shared primitives in a neutral wrapper by default, use vertical variant stacking, and keep notes focused on implementation constraints and composition warnings. When self-composition is a real use case, add it deliberately as its own variation rather than letting it appear accidentally through the page shell.
- enforcement point: `studio/ui-catalogue/*`, `_includes/studio_ui_catalogue_*.html`, and the primitive-catalogue guidance in `studio-ui-framework.md`
- files changed:
  - `studio/ui-catalogue/panel/index.md`
  - `_includes/studio_ui_catalogue_panel_demo.html`
  - `_includes/ui_catalogue_notes/panel.md`
  - `assets/studio/css/studio.css`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/ui-catalogue.md`
- local verification:
  - build the site to a separate destination
  - inspect `/studio/ui-catalogue/panel/` on desktop and mobile widths
  - confirm each panel variant sits on a neutral surface with no enclosing panel shell
  - confirm self-composition cases are shown only when intentionally added in the markup
- follow-up:
  - apply the same neutral-surface template to future primitive pages
  - if a primitive still shows a defect after neutral rendering, fix the primitive rather than documenting around it

## UI Rule Log 2026-04-19 / UI-001

- status: adopted
- route: `/studio/catalogue-work/`
- issue: the `New Detail` action looked visually inconsistent beside the shared Studio search input and adjacent section actions; the reported symptom was non-standard button height
- triage: systemic
- reasoning: the first pass treated the issue as local layout only, but the more important finding was that shared Studio buttons were not explicitly using `border-box` sizing. That meant anchor-backed buttons using `tagStudio__button` could render at a different effective height from standard Studio controls even when they appeared to share the same class.
- permanent rule: shared Studio action controls must derive their geometry from the shared primitive, not from route-specific compensation. If a control uses `tagStudio__button`, its height and box model must match the Studio control token contract whether the element is a native `<button>` or an `<a>` styled as a button.
- enforcement point: `assets/studio/css/studio.css` in the shared `.tagStudio__button` rule
- files changed:
  - `assets/studio/css/studio.css`
  - `studio/catalogue-work/index.md`
- local verification:
  - inspect the route in the in-app browser at `/studio/catalogue-work/`
  - compare `New Detail`, `New File`, `New Link`, and nearby search/input controls
  - confirm the shared control height is visually consistent after refresh
- follow-up:
  - when a future UI issue touches a shared primitive, record the decision here even if the visible defect was first reported on one route
  - prefer fixing shared primitives before adding page-specific overrides

### Example Triage Note For This Issue

Use this structure when the issue first appears:

```text
route: /studio/catalogue-work/
problem: `New Detail` button appears visually inconsistent; reported symptom is non-standard height
initial triage: pending
first hypothesis: local layout mismatch in the work-details header row
after inspection: systemic
reason: shared `tagStudio__button` sizing contract is incomplete for anchor-backed buttons
action: fix shared button primitive, then record permanent rule in studio-ui-rules.md
```

### Subsequent Actions For This Issue

1. Fix the immediate UI defect.
2. Decide whether the root cause lives in page markup or a shared primitive.
3. If shared, update the shared primitive rather than compensating on one route.
4. Add or update the rule entry in this document.
5. Recheck the original route and at least one sibling route that uses the same primitive.

---
doc_id: modal-responsibility-extraction-plan
title: Modal Responsibility Extraction Plan
added_date: 2026-05-15
last_updated: 2026-05-15
ui_status: done
parent_id: ui-request-modal-composition-pattern
sort_order: 10
hidden: false
---
# Modal Responsibility Extraction Plan

Status:

- complete

## Summary

Extract modal responsibilities from large Studio and Docs Viewer route controllers before redesigning or migrating the modal composition pattern.

This plan supports [Modal Composition Pattern Request](/docs/?scope=studio&doc=ui-request-modal-composition-pattern) and the maintainability direction in [Studio JavaScript Payload Inventory](/docs/?scope=studio&doc=studio-javascript-payload-inventory).

## Reason

Modal code is currently embedded across several large route files. Rendering, event wiring, route state, validation, focus behavior, service calls, and reload/status handling are often close together.

That was a reasonable outcome of quick iterative development, but it makes modal pattern redesign harder to review. If the project redesigns the modal shell while modal code is still buried in mixed controllers, each migration risks becoming both a UI-pattern change and a large-file refactor.

The extraction should happen first so the modal pattern work can focus on shell contracts, CSS vocabulary, return contracts, and parity between Studio and Docs Viewer.

## Scope

Extract modal responsibilities across all current files with modal behavior. Do not leave known modal code in a "still to extract later" state unless a blocker is recorded here.

In scope:

- modal rendering helpers
- modal descriptor builders
- route-local modal validation
- modal open, close, Escape, backdrop, and focus handling
- modal event/lifecycle wiring
- modal-specific CSS ownership notes
- native browser dialog replacement candidates

Out of scope:

- redesigning the canonical modal shell
- changing modal visual design
- migrating modals to the new final pattern
- broad route-controller cleanup unrelated to modal responsibilities
- changing service endpoints only to fit modal extraction

## Extraction Boundary

The extraction should clarify ownership without moving domain behavior into modal modules.

Modal modules may own:

- shell/body/action rendering helpers
- local field descriptors and option descriptors
- local completeness validation for modal inputs
- modal lifecycle helpers
- result object construction

Route controllers or opener commands should continue to own:

- create, update, delete, archive, rebuild, import, and write actions
- service payload assembly beyond local modal values
- service calls
- reload and route navigation
- management/status messages
- route busy state
- activity logging

## Initial File Set

Review and extract modal responsibilities from these files:

- `assets/docs-viewer/js/docs-viewer-management.js`
- `assets/docs-viewer/js/docs-html-import.js`
- `assets/studio/js/tag-studio.js`
- `assets/studio/js/tag-registry.js`
- `assets/studio/js/tag-aliases.js`
- `assets/studio/js/series-tags.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/data-sharing-prepare.js`
- `assets/studio/js/data-sharing-review.js`
- `assets/studio/js/activity-log.js`
- `assets/studio/js/studio-modal.js`

Add files if the inventory finds additional modal behavior.

Additional files found during implementation inventory:

- `assets/docs-viewer/js/docs-viewer-management-modals.js`
- `assets/studio/js/catalogue-editor-action-modals.js`
- `assets/studio/js/catalogue-work-editor-modals.js`
- `assets/studio/js/tag-studio-modals.js`
- `assets/studio/js/tag-registry-modals.js`
- `assets/studio/js/catalogue-work-actions.js`
- `assets/studio/js/catalogue-work-detail-actions.js`
- `assets/studio/js/catalogue-series-actions.js`
- `assets/studio/js/catalogue-moment-actions.js`

## Work Slices

1. Inventory modal responsibilities.
   Record each modal, owner file, current lifecycle, event wiring, CSS namespace, native dialog use, and domain-action boundary.
2. Identify extraction targets.
   Decide which render helpers, descriptor builders, validation helpers, and lifecycle helpers should move to route-local modal modules or shared modal modules.
3. Extract route-local modal modules.
   Move modal-specific code out of mixed controllers while preserving behavior. Name route-local modal modules consistently as `*-modals.js` unless there is a documented reason not to. This is a maintainability issue more than a performance issue, so predictable naming matters.
4. Replace native browser dialogs as part of extraction.
   Convert `window.prompt()`, `window.confirm()`, and `window.alert()` modal behavior to extracted transient modal code rather than deferring it to the later pattern migration.
5. Extract shared modal helpers only where repetition is clear.
   Keep shared helpers small and aligned with the later canonical shell direction.
6. Verify route behavior.
   Use focused browser checks for each route with modal behavior, including representative modal screenshots where practical.
7. Update this plan.
   Mark completed extractions and record any files intentionally left unchanged with reasons.

## Implementation Progress

Completed slices:

- Extracted the Docs HTML import filename-conflict modal from `assets/docs-viewer/js/docs-html-import.js` into `assets/docs-viewer/js/docs-html-import-modals.js`.
  The modal module now owns the transient host, shell/actions rendering, local replacement `doc_id` validation, focus entry, Escape/cancel behavior, and result object construction.
  The import route still owns status messaging, import retries, overwrite confirmation payloads, service calls, and route busy state.
- Replaced native Studio catalogue action confirmations in `assets/studio/js/catalogue-work-actions.js`, `assets/studio/js/catalogue-work-detail-actions.js`, `assets/studio/js/catalogue-series-actions.js`, and `assets/studio/js/catalogue-moment-actions.js`.
  These routes now use `assets/studio/js/catalogue-editor-action-modals.js`, a small transient confirmation wrapper over `openConfirmModal()`.
  The helper owns body-line normalization and the modal confirmation result; the route action modules still own prose import, publication, delete, service calls, status updates, and navigation.
- Replaced Docs Viewer management native browser dialogs in `assets/docs-viewer/js/docs-viewer-management.js`.
  The route now uses `assets/docs-viewer/js/docs-viewer-management-modals.js` for transient confirm, text-input, and choice modals covering make-viewable parent/descendant decisions, new doc title entry, archive confirmation, and delete confirmation.
  The modal module owns shell rendering, focus entry and return, Escape/cancel behavior, local text/choice result collection, and delete preview body formatting.
  The management controller still owns create, archive, delete, viewability writes, service calls, busy state, messages, context menu behavior, and index reloads.
- Extracted the Docs Viewer management embedded modal lifecycle slice from `assets/docs-viewer/js/docs-viewer-management.js` into `assets/docs-viewer/js/docs-viewer-management-modals.js`.
  The modal module now owns metadata modal open/close/focus behavior, metadata status option rendering, metadata parent picker popup state/rendering/keyboard selection, import modal cancel-button insertion and close behavior, settings modal shell/status/warning state, embedded modal root-click/Escape handling, and modal form/control listener wiring.
  The management controller still owns metadata payload validation and save decisions, parent option source data, settings config read/write service calls, import modal module initialization, route busy state, route messages, context/manage action menus, index reloads, and navigation.
- Extracted the Series Tags offline session and import modal rendering from `assets/studio/js/series-tags.js` into `assets/studio/js/series-tags-modals.js`.
  The modal module owns the session modal shell/body/actions rendering, import modal shell/body/actions rendering, import preview review rows, resolution select descriptors, and local modal copy lookup.
  The route still owns modal open/close event wiring, session copy/download/clear actions, import file parsing, preview/apply service calls, route busy state, status messages, assignments reloads, and local session cleanup.
- Extracted the Series Tags modal event/lifecycle wiring from `assets/studio/js/series-tags.js` into `assets/studio/js/series-tags-modals.js`.
  The modal module now owns session/import close-role handling, session action trigger dispatch, import choose-file trigger handling, import action trigger dispatch, import file change dispatch, and import resolution change dispatch.
  The route still owns opening the modals from route actions, session copy/download/clear behavior, import file state reset, import resolution state updates, import file parsing, preview/apply service calls, route busy state, status messages, assignments reloads, and local session cleanup.
- Extracted the Data Sharing Prepare result modal from `assets/studio/js/data-sharing-prepare.js` into `assets/studio/js/data-sharing-prepare-modals.js`.
  The modal module owns the result modal shell/body/actions rendering, output file display formatting, count rows, warning/error list rendering, close-role wiring, and modal clearing helper.
  The route still owns scope/config selection, package payload assembly, prepare service calls, route busy state, success/error status messages, and local result reset timing.
- Extracted the Activity Log detail notice modal from `assets/studio/js/activity-log.js` into `assets/studio/js/activity-log-modals.js`.
  The modal module owns detail item filtering, fallback body text selection, notice modal labels, and the shared notice modal invocation.
  The route still owns feed loading, entry lookup, sorting, list rendering, click dispatch, and route ready state.
- Extracted the Data Sharing Review result and apply-confirmation modals from `assets/studio/js/data-sharing-review.js` into `assets/studio/js/data-sharing-review-modals.js`.
  The modal module owns result notice body rendering, result count rows, modal issue-list rendering, result close labels, apply confirmation labels/body construction, and shared modal invocations.
  The route still owns returned package loading, preview row rendering, selection state, preflight/apply service calls, apply result payload shaping, activity context, status updates, and route busy state.
- Extracted the Series Tag Editor save preview modal from `assets/studio/js/tag-studio.js` into `assets/studio/js/tag-studio-modals.js`.
  The modal module owns the save preview shell/body/actions rendering, modal ref collection, resolved payload population, patch snippet population, open state, close helper, and local modal copy lookup.
  The route still owns editor diff construction, no-change handling, save mode probing, local/offline persistence, clipboard status messaging, route busy state, and editor rendering.
- Extracted the Series Tag Editor save modal event wiring from `assets/studio/js/tag-studio.js` into `assets/studio/js/tag-studio-modals.js`.
  The modal module now owns save modal close click handling and patch-copy trigger dispatch.
  The route still owns diff construction, save/probe decisions, local/offline persistence, clipboard write behavior, status wording, route busy state, and editor rendering.
- Extracted the Catalogue Work Editor embedded entry, embedded delete confirmation, and build preview modals from `assets/studio/js/catalogue-work-editor.js` into `assets/studio/js/catalogue-work-editor-modals.js`.
  The modal module owns embedded entry shell rendering, local field validation/status, Escape/Enter/cancel/save lifecycle, embedded delete confirmation invocation, build preview shell/body/actions rendering, build preview close/Escape lifecycle, and modal result construction.
  The route still owns draft mutation from returned modal results, editor refresh, work lookup/selection, save/delete/publication/build actions, route busy state, and work readiness rendering.
- Extracted the first Tag Registry modal slice from `assets/studio/js/tag-registry.js` into `assets/studio/js/tag-registry-modals.js`.
  The modal module owns import, patch, edit, new, demote, and delete modal shell/body/actions rendering, modal ref collection, and simple modal show/hide helpers.
  The route still owns registry filtering/list rendering, modal field population, local validation, delete impact preview loading, demote target selection, import parsing/submission, edit/create/delete/demote service calls, patch result handling, status messages, and route busy state.
- Extracted the second Tag Registry modal slice from `assets/studio/js/tag-registry.js` into `assets/studio/js/tag-registry-modals.js`.
  The modal module now owns edit/new/delete/demote modal field population, open/close reset lifecycle, new-tag group key rendering, demote selected-target UI rendering, demote popup show/hide lifecycle, delete tag meta rendering, and delete preview state reset.
  The route still owns tag lookup, validation decisions, import parsing/submission, delete impact service preview, demote match lookup/selection rules, create/edit/delete/demote service calls, list/control rendering, status message decisions, and route busy state.
- Extracted the third Tag Registry modal slice from `assets/studio/js/tag-registry.js` into `assets/studio/js/tag-registry-modals.js`.
  The modal module now owns delete impact preview count/link rendering and delete impact status rendering.
  The route still owns delete impact service preview loading, affected-series lookup, stale preview protection, delete service calls, and route busy state.
- Extracted the fourth Tag Registry modal slice from `assets/studio/js/tag-registry.js` into `assets/studio/js/tag-registry-modals.js`.
  The modal module now owns import selected-file display and import result status rendering.
  The route still owns import availability decisions, file parsing, import submission, patch fallback decisions, patch-copy success/error decisions, and route busy state.
- Extracted the fifth Tag Registry modal slice from `assets/studio/js/tag-registry.js` into `assets/studio/js/tag-registry-modals.js`.
  The modal module now owns import, patch, edit, new-tag, demote, and delete modal event/lifecycle wiring, including modal close clicks, selected import file hookup, patch-copy trigger hookup, new-tag group selection UI, demote popup dismissal, Escape blur behavior, and demote tag-chip add/remove trigger dispatch.
  The route still owns import mode state, patch-copy success/error decisions, tag lookup, new-tag and demote validation decisions, demote match lookup and selection rules, delete impact preview loading, import parsing/submission, edit/create/delete/demote service calls, patch fallback decisions, route busy state, route ready state, and list/control rendering.
- Extracted the sixth Tag Registry modal slice from `assets/studio/js/tag-registry.js` into `assets/studio/js/tag-registry-modals.js`.
  The modal module now owns demote tag-search popup option rendering, truncated-match indicators, escaping, and empty-result popup hiding.
  The route still owns demote tag match lookup inputs, match filtering rules, popup selection handling, validation decisions, import parsing/submission, edit/create/delete/demote service calls, patch fallback decisions, route busy state, route ready state, and list/control rendering.
- Extracted the first Tag Aliases modal slice from `assets/studio/js/tag-aliases.js` into `assets/studio/js/tag-aliases-modals.js`.
  The modal module owns import, patch, promotion, demote, and edit modal shell/body/actions rendering, modal ref collection, import selected-file/result rendering, patch snippet modal UI, promotion open/close/status/group-key rendering, and edit/demote popup visibility/status helpers.
  The route still owns alias lookup, validation decisions, import availability, import parsing/submission, create/edit/delete/promote/demote service calls, tag match lookup and selection rules, patch fallback decisions, route busy state, route ready state, and list/control rendering.
- Extracted the second Tag Aliases modal slice from `assets/studio/js/tag-aliases.js` into `assets/studio/js/tag-aliases-modals.js`.
  The modal module now owns edit/create/demote modal field population, open/close reset lifecycle, edit/demote selected-target chip rendering, edit/demote group key rendering, and validation result display application.
  The route still owns alias and tag lookup, edit/demote validation decisions, tag match lookup and selection rules, import parsing/submission, create/edit/delete/promote/demote service calls, patch fallback decisions, route busy state, route ready state, and list/control rendering.
- Extracted the third Tag Aliases modal slice from `assets/studio/js/tag-aliases.js` into `assets/studio/js/tag-aliases-modals.js`.
  The modal module now owns edit/demote tag-search popup option rendering, truncated-match indicators, escaping, and empty-result popup hiding.
  The route still owns tag match lookup inputs, match filtering rules, popup selection handling, validation decisions, import parsing/submission, create/edit/delete/promote/demote service calls, patch fallback decisions, route busy state, route ready state, and list/control rendering.
- Extracted the fourth Tag Aliases modal slice from `assets/studio/js/tag-aliases.js` into `assets/studio/js/tag-aliases-modals.js`.
  The modal module now owns import, patch, promotion, edit, and demote modal event/lifecycle wiring, including modal close clicks, selected import file hookup, patch-copy trigger hookup, promotion group selection UI, search popup dismissal, Escape blur behavior, and tag-chip add/remove trigger dispatch.
  The route still owns import mode state, patch-copy success/error decisions, alias and tag lookup, edit/demote validation decisions, tag match lookup and selection rules, import parsing/submission, create/edit/delete/promote/demote service calls, patch fallback decisions, route busy state, route ready state, and list/control rendering.

Inventory notes:

- No `window.prompt()`, `window.confirm()`, or `window.alert()` uses remain under `assets/studio/js` or `assets/docs-viewer/js` after this slice.
- The catalogue action modules were added to the extraction file set because native confirmation dialogs lived outside the original modal file list.
- Final route-file scan found no remaining avoidable modal rendering or lifecycle bulk in the audited route/controllers. Remaining modal references are route bridge calls into extracted modal modules or shared transient modal helpers, with route-owned copy/payload/service decisions preserved.
- `assets/studio/js/studio-modal.js` remains the shared transient modal and frame helper. It is intentionally not extracted further in this plan; it is the next pattern-redesign target.
- Non-modal suggestion/autocomplete popups, such as tag/work search suggestions, remain route or feature-owned. They are part of inline editing/search workflows rather than modal composition, so they are out of this extraction's completion boundary.

Verification completed:

- JavaScript syntax checks passed for changed modal/action modules.
- JSON validation passed for changed Studio UI text files.
- Focused Playwright checks covered the Docs HTML import conflict modal result contract and the catalogue action modal helper's cancel, primary, Escape, and multiline body behavior.
- Focused Playwright checks covered the Docs Viewer management modal helper's confirm, Escape cancel, text input result, choice result, delete preview body formatting, and cleanup behavior.
- Focused module contract checks covered the Docs Viewer management modal controller's metadata open/submit/close result contract, parent picker popup rendering/selection/ID resolution, import modal cancel insertion/close behavior, and settings loading/field/warning/error state.
- Focused module contract checks covered the Series Tags modal helper's session count rendering, hidden/open state, escaped status/file/review text, conflict resolution selection, and import review rows.
- Focused module contract checks covered the Series Tags modal helper's session/import close handling, session/import action dispatch, import choose-file trigger, import file selection dispatch, and import resolution change dispatch.
- Focused module contract checks covered the Data Sharing Prepare result modal helper's success/failure titles, output filename normalization, count unit labels, escaped files/issues, close action cleanup, and explicit clearing helper.
- Focused module contract checks covered the Activity Log details modal helper's detail item filtering, fallback body text, escaped title/body/close labels, and close cleanup through the shared notice modal.
- Focused module contract checks covered the Data Sharing Review modal helper's result title/summary/count/issues rendering, escaped labels/body text, notice close cleanup, apply confirmation body construction, and primary confirmation result.
- Focused module contract checks covered the Series Tag Editor save preview modal helper's shell roles, escaped labels, hidden/open state, ref collection, resolved payload population, patch snippet population, and close helper.
- Focused module contract checks covered the Series Tag Editor save modal helper's close click handling and patch-copy callback dispatch.
- Focused module contract checks covered the Catalogue Work Editor modal helper's embedded entry shell roles and escaping, entry validation status, save result contract, close cleanup, build preview labels/body, and Escape close behavior.
- Focused module contract checks covered the Tag Registry modal helper's modal shell roles, escaped labels, ref collection, import show/hide state, patch snippet population, patch close helper, and delete show/hide helper.
- Focused module contract checks covered the Tag Registry modal helper's edit field population/reset, new-tag group rendering/status updates, demote selected-target rendering and popup reset, and delete preview state reset.
- Focused module contract checks covered the Tag Registry modal helper's delete impact count/link rendering, empty-series fallback, escaping, and impact status rendering.
- Focused module contract checks covered the Tag Registry modal helper's selected import file display, result clearing on file selection, empty-file reset, and import result status rendering.
- Focused module contract checks covered the Tag Registry modal helper's import, patch, edit, new-tag, demote, and delete event wiring, including modal close state changes, selected file display, patch-copy callback dispatch, new-tag group selection rendering, demote popup Escape/dismiss behavior, and demote tag add/remove callback dispatch.
- Focused module contract checks covered the Tag Registry modal helper's demote popup option rendering, escaped popup labels and IDs, truncated indicator, and empty-result popup hiding.
- Focused module contract checks covered the Tag Aliases modal helper's modal shell escaping, ref collection contract, selected import file display, import result clearing, patch show/hide behavior, promotion group-key rendering/status updates, and popup show/hide helpers.
- Focused module contract checks covered the Tag Aliases modal helper's edit/create/demote open state, field population, selected target chip rendering, group key rendering, validation-driven warning/status/button state, focus entry, and close reset lifecycle.
- Focused module contract checks covered the Tag Aliases modal helper's edit/demote popup option rendering, escaped popup labels and IDs, truncated-match indicator, and empty-result popup hiding.
- Focused module contract checks covered the Tag Aliases modal helper's import, patch, promotion, edit, and demote event wiring, including modal close state changes, selected file display, patch-copy callback dispatch, promotion group selection rendering, popup Escape/dismiss behavior, and tag add/remove callback dispatch.
- Final close-out scans covered route/controller modal references, native browser dialog usage, shared modal helper usage, and intentionally retained non-modal popup references.
- Browser smoke against the running Docs Viewer route confirmed this plan renders with `complete` status.

## Completion Criteria

- every current modal implementation has an owner and extracted or explicitly justified modal code boundary
- native browser dialog uses are replaced as part of extraction
- large route controllers no longer contain avoidable modal rendering and lifecycle bulk
- domain actions remain owned by route commands or openers
- the modal composition redesign can proceed without first untangling embedded modal code
- permanent modal pattern docs can reference clean implementation examples
- no compatibility layers or migration artifacts remain after each extraction slice unless explicitly approved for a specific blocker

## Risks

- extracting before the final modal pattern could create temporary modules that will change again during redesign
- moving lifecycle code can introduce focus, Escape, or close regressions
- local write flows can regress if domain action ownership moves accidentally
- Docs Viewer portability may require duplicated extraction shapes rather than a shared Studio dependency

## Verification

For each extraction slice:

- design cleanly scoped test scripts upfront where practical, before moving code
- run syntax checks for changed JavaScript where available
- open the affected route in the Codex app browser or an equivalent browser check
- verify representative modal open, close, Escape, cancel, focus, and action behavior
- capture or reference screenshots for UI audit evidence when the route has modal behavior

## Decisions

- Route-local modal modules should use consistent `*-modals.js` naming by default.
- Native browser dialog replacement is part of extraction, not deferred to later modal pattern migration.
- There is no special first experimental route. The extraction applies across all modal-owning files, and the approach should be treated as implementation work rather than a proof-of-concept.
- The project accepts the migration risk of doing this cleanly: no compatibility layers, no migration artifacts, and no deliberate old/new modal pattern coexistence after a slice is complete.

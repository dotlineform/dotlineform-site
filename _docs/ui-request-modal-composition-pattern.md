---
doc_id: ui-request-modal-composition-pattern
title: Modal Composition Pattern Request
added_date: 2026-05-10
last_updated: 2026-05-15
ui_status: in-progress
parent_id: change-requests
sort_order: 190
hidden: false
---
# Modal Composition Pattern Request

Status:

- In progress
- Extraction prerequisite complete
- Next phase: define the canonical shell contract and migrate current modal pages

## Summary

Define a shared modal composition pattern for Studio and Docs Viewer interfaces (see [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue))

The pattern should make modals consistent as UI containers while keeping domain actions owned by the page or command that opens the modal.

The review should also explain the current implementation spread. Existing Studio and Docs Viewer modals use several reasonable but different approaches, and that variety now makes the codebase harder to understand, harder to discuss when requirements change, and harder to extend safely.

This is not only future-facing guidance. The modal composition migration applies to all current Studio and Docs Viewer modal surfaces. Migration should be tracked and completed at page or route level, so a route with multiple modals is reviewed and migrated as one coherent UI surface unless a concrete implementation blocker requires a narrower temporary slice.

## Reason

Recent Docs Viewer management work exposed a useful boundary: the Edit button should own the write action, while the modal should only collect and return selections. That boundary keeps mutation behavior near the page command that requested it and prevents modal components from becoming hidden application controllers.

The same principle should be made explicit across Studio UI guidance so future modals do not drift into inconsistent shells, duplicated controls, or action ownership that is hard to audit.

The current differences are understandable. Some routes pre-render persistent hidden modals and delegate events to modal or route containers. Some routes create transient modal DOM and wire listeners directly after render. Docs Viewer management has static shell modals with a mix of delegated close handling and direct form/button handlers. Docs HTML import has an import-specific transient modal frame. Each choice fits a local lifecycle or historical constraint, but the combined effect is too many implementation shapes for a shared UI concept.

This also makes the associated CSS harder to reason about. It is not always clear whether a style belongs to a shared modal shell, a route-specific workflow, a transient modal helper, or legacy Docs Viewer management markup. In some cases modal behavior is mostly defined by shared classes; in others it depends on local markup and local event wiring. That makes it difficult to know whether extending a modal should reuse, delegate, replace, or preserve the existing implementation.

## Goals

- define one consistent modal shell for Studio and Docs Viewer management surfaces
- keep modal controls visually and behaviorally consistent with equivalent controls on the page
- define modals as selection/input collectors that return values to the opener
- keep create/update/delete/archive/show actions owned by the page control or command that opened the modal
- document when a modal may validate local input versus when validation belongs to the owning page/service flow
- update UI audit guidance so page audits check modal composition patterns, not only page-level controls
- reduce the implementation surface to two preferred modal composition patterns, or at most three if the inventory proves a distinct third pattern is justified
- map every current Studio and Docs Viewer modal page to the preferred patterns
- produce and maintain a page-by-page migration tracker with planned, in-progress, and done states
- migrate all current modal-owning pages toward the chosen shell, CSS, focus, action-row, validation, and ownership contracts

## Non-Goals

- creating a new modal framework before inventorying current modal usage
- changing service endpoints only to fit the modal pattern
- using modal guidance as a substitute for route-specific workflow design
- redesigning modal workflows unless redesign is needed to avoid throwaway migration code, prevent new technical debt, or remove a blocker to the shared composition contract

## Current Implementation Context

The preparatory modal extraction is complete. See [Modal Responsibility Extraction Plan](/docs/?scope=studio&doc=modal-responsibility-extraction-plan).

Current modal implementations now fall into these broad groups:

- Shared Studio helper modals: `assets/studio/js/studio-modal.js` renders transient confirm, detail-confirm, patch-preview, and notice modals, then wires the current primary/cancel buttons directly. These work well for simple promise-style flows where the caller awaits a result.
- Route-local Studio modal modules: Tag Registry, Tag Aliases, Tag Studio, Series Tags, Catalogue Work Editor, Data Sharing Prepare, Data Sharing Review, Activity Log, and catalogue action confirmations now route modal rendering, event wiring, or transient invocations through `*-modals.js` helpers. Route controllers still own service calls, busy state, reloads, validation decisions, and list/control rendering.
- Docs Viewer modal modules: Docs Viewer management now delegates transient confirm/text/choice modals and embedded metadata/import/settings modal lifecycle to `assets/docs-viewer/js/docs-viewer-management-modals.js`. Docs HTML import delegates filename-conflict resolution to `assets/docs-viewer/js/docs-html-import-modals.js`.
- Static or route-owned shell details remain where they are implementation constraints, especially Docs Viewer management shell markup and portable `docsViewer__*` CSS. Those details should still follow the shared modal composition contract.
- Non-modal suggestion/autocomplete popups remain feature-owned. They support inline editing/search workflows and are not part of the modal composition boundary.

No `window.prompt()`, `window.confirm()`, or `window.alert()` uses remain under `assets/studio/js` or `assets/docs-viewer/js`.

The issue is no longer embedded modal bulk in route controllers. The remaining issue is that extracted modal helpers still use several locally valid shell shapes, CSS vocabularies, and helper APIs. The next phase should choose the stable shared shell contract, decide which existing helper is canonical, and document how Studio and portable Docs Viewer implementations stay visually and behaviorally aligned.

Once the shell contract is chosen, the migration should not stop at representative examples. Representative pages can still be used to prove implementation details, but every current modal page remains in scope until the tracker marks it done.

## Pattern Target

The review should define two preferred modal composition patterns if possible:

1. Transient result modal.
   Use this for confirm, notice, conflict-resolution, and short form modals that are opened by a command, collect a small result, and then close. The opener owns the domain action. The modal helper owns shell rendering, Escape/backdrop/cancel behavior, focus handling, and the returned result contract.
2. Route-owned workflow modal.
   Use this for persistent route tools with complex internal controls, popups, staged state, file inputs, or repeated route-level re-rendering. The route owns workflow state and domain actions. The shared pattern still owns shell structure, action-row composition, close affordances, focus/escape rules, and CSS boundaries.

Only add a third preferred pattern if the inventory proves a durable distinction that cannot be cleanly represented by those two. A possible third candidate is a static shell modal for server-rendered or layout-owned surfaces such as Docs Viewer management, but the review should first test whether this is only an implementation detail of the route-owned workflow pattern.

## Canonical Implementation Direction

The canonical base should be the modal implementation shape that can meet the most complex requirements, not the smallest helper that fits simple confirmations.

The current closest base is the shared Studio modal frame contract in `assets/studio/js/studio-modal.js`: `renderStudioModalFrame()`, `renderStudioModalActions()`, and modal hosts created or owned by the route. This shape supports arbitrary body content, action rows, close roles, route-owned workflow state, file inputs, popups, async flows, and simple confirm or notice dialogs.

The canonical shell contract is documented in [Modal Shell Primitive](/docs/?scope=studio&doc=ui-primitive-modal-shell). Use that primitive as the migration target for both Studio implementation and portable Docs Viewer equivalents.

The higher-level simple helpers such as `openConfirmModal()`, `openNoticeModal()`, `openTextInputModal()`, and `openChoiceModal()` should be treated as convenience APIs on top of the shared shell, not as separate modal patterns. They are useful for simple cases, but they should not define a different shell, CSS vocabulary, or action ownership model.

The target is one shell contract and one modal CSS vocabulary, not separate shells for simple, medium, and complex modals. Simple and medium modals should use the same shell as complex modals, with less content and thinner helper APIs. This avoids encouraging new local patterns every time a modal starts simple and later gains validation, extra controls, async behavior, or workflow state.

Under this direction:

- the shared shell owns modal structure, backdrop, dialog role, title wiring, action-row composition, close affordances, responsive sizing, focus behavior, and Escape handling
- route-owned workflow modals own route state, local control rendering, validation that belongs to the local input flow, and the domain command that consumes the modal result
- transient result helpers own a small result contract but still render through the same shell and CSS vocabulary
- Docs Viewer management should either adopt the same shell contract directly or be documented as a route-owned workflow modal using the same composition rules

Native browser dialogs such as `window.prompt()`, `window.confirm()`, and `window.alert()` should not be treated as modal composition patterns for Studio or Docs Viewer management UI. Existing uses have been replaced during the extraction phase. New native browser dialog usage should be treated as a regression unless it is a deliberate non-Studio fallback documented in the owning feature.

For example, Docs Viewer Actions -> New now uses a transient result modal that collects a title and returns a cancel or value result. The modal owns the title input, local required-title validation, OK/Cancel controls, focus behavior, and Escape handling. The Docs Viewer command continues to own `createManagedDoc()`, management status, index reload, and error handling.

## Docs Viewer Portability

Docs Viewer remains part of the current Studio environment and repo, so from a design and requirements perspective a modal is just a modal wherever it appears in the current site. Requirements should not need to special-case Docs Viewer as a different modal design system.

At implementation time, Docs Viewer has a portability constraint. It may need its own shell renderer, static shell markup, `docsViewer__*` class namespace, CSS bundle, and runtime assumptions so it can remain portable outside the Studio shell. That implementation separation is allowed, but it should not create separate modal composition rules.

Docs Viewer and Studio should therefore share the same modal composition contract, not necessarily the exact same implementation files.

Shared contract requirements include:

- modal anatomy: backdrop, dialog, title or title/meta header, body, status or validation area, and action row
- open, close, cancel, backdrop, and Escape behavior
- focus entry and focus return
- action ownership, where the modal collects values and the opener performs writes, rebuilds, archive/delete operations, and reload flows
- button/action-row vocabulary and relative visual weight
- validation and message placement
- responsive sizing rules
- UI audit expectations

Docs Viewer may keep portable implementation details such as:

- `docsViewer__*` class names
- Docs Viewer-specific CSS files
- Docs Viewer-specific shell renderers or static shell markup
- runtime code that avoids a hard dependency on Studio JS or CSS

This creates effective duplication that must be managed deliberately. The duplication is a portability tradeoff, not a reason for visual or behavioral drift. Studio should keep the canonical implementation source, while Docs Viewer should keep a portable implementation of the same contract. UI reviews should check parity between the two.

## Return Contract Documentation

Modal-return contracts should be documented API-first, with prose used to explain the design intent and review boundaries.

Where a modal workflow is reusable, the preferred documentation should be the JavaScript helper API itself. Developers should be able to inspect existing code and see the expected implementation shape without translating prose into a fresh local pattern. The API should make the ownership boundary visible:

- the opener calls a modal helper or renders the shared modal shell
- the modal collects input, selection, or confirmation state
- the modal returns a cancel result or a structured value result
- the opener owns the domain action, service payload assembly, write call, reload, and status handling

The existing `openConfirmModal()` and `openNoticeModal()` helpers are examples of this direction for simple flows, but the review should define whether a more general transient-result helper is needed for small input and selection modals. That helper should still render through the canonical shell and CSS vocabulary.

Prose remains necessary for:

- design intent
- accessibility and focus requirements
- ownership boundaries
- when local modal validation is appropriate
- when a route-owned workflow modal should use the shared shell without fitting a small helper API
- migration and audit rules

The final pattern should not remain only in this change request. Once reviewed, stable decisions should be migrated into the permanent Studio UI and UI audit documentation so `/docs/` remains the reliable source of implementation guidance. Completed change requests should capture the discussion trail, while permanent docs should carry the durable contract used for future work.

## Proposed Pattern

Modal shell:

- use the same structural shell for title, optional metadata, body, action row, close behavior, focus return, and Escape handling
- keep backdrop, close button, action alignment, and responsive sizing consistent
- avoid page-specific modal chrome unless a real workflow difference requires it

Controls:

- use the same primitive style and state behavior as equivalent page controls
- keep labels, selected states, disabled states, listbox sizing, checkboxes, and validation messages consistent with page-level controls
- use configured UI text for visible labels and action copy

Ownership:

- the opener owns the action
- the modal returns selections, input values, or a cancel result
- the modal may perform local completeness checks such as required text or valid option selection
- the modal should not directly perform domain writes, rebuilds, archive/delete operations, or other service mutations
- service payload assembly belongs to the opener or page-level command handler

Audit coverage:

- UI audits should include a modal composition section when the audited route opens modals
- audits should check shell consistency, control consistency, focus/escape behavior, responsive fit, and action ownership
- audit findings should distinguish route-specific workflow issues from shared modal-pattern issues
- UI audits should require a modal screenshot or browser check whenever a route has modal behavior

## Modal Audit Target

The target state is that UI audits include modal screenshots or Codex app browser checks whenever the audited route has modal behavior.

Current UI conformance work is still too prose-request based. It has not consistently used the Codex app browser to inspect route state, open modals, capture visual evidence, or verify interaction details. That is acceptable as a current gap, but the modal composition pattern should set a higher target because modal consistency depends on visual shell, focus behavior, responsive fit, and action placement that prose review alone can miss.

Modal audit checks should cover:

- at least one screenshot or browser inspection of each modal pattern used by the route
- desktop and mobile fit when the modal body has meaningful layout or scrolling risk
- close button, cancel button, backdrop, and Escape behavior
- focus entry and focus return
- validation and status-message placement
- action ownership, especially that writes and reloads remain owned by the opener or page command
- parity between Studio and Docs Viewer portable implementations where applicable

Screenshots add maintenance overhead, so the audit requirement should be proportional. A route with only one simple confirm modal may need a single focused screenshot/check. A route with workflow modals, file inputs, popups, or async result states should capture the representative states that define the modal behavior.

As part of making this operational, the review should update `user-guide.md` or the relevant UI audit guidance so modal screenshots and browser checks become part of the expected UI conformance workflow rather than an optional afterthought.

## Next Steps

1. Choose the canonical shell contract.
   Start from `assets/studio/js/studio-modal.js`, especially `renderStudioModalFrame()` and `renderStudioModalActions()`, unless the review finds a missing requirement from the extracted route-local modules.
2. Define the two preferred composition patterns.
   Keep the target to transient result modals and route-owned workflow modals unless a concrete extracted example proves a durable third pattern is needed.
3. Write stable guidance under the UI composition-pattern docs.
   The guidance should include shell anatomy, focus/return behavior, Escape/backdrop behavior, action-row vocabulary, validation placement, result contracts, and action ownership.
4. Update UI audit guidance to include modal composition checks.
   Audits should check representative modal screenshots or browser states, not only page-level controls.
5. Maintain the page-level migration tracker.
   Prioritize easiest pages first when useful for momentum, but keep all current modal pages in scope.
6. Decide CSS ownership and naming.
   Clarify which modal rules become shared Studio shell rules, which stay route-local, and how `docsViewer__*` portable equivalents maintain parity.
7. Record permanent API examples.
   Document helper API shapes for confirm/notice/input/choice/result flows so future work copies an existing contract rather than inventing another local pattern.

## Modal Extraction Prerequisite

The modal-focused extraction pass across current modal-owning files is complete.

This follows the maintainability direction from [Studio JavaScript Payload Inventory](/docs/?scope=studio&doc=studio-javascript-payload-inventory). That inventory already flags long mixed route controllers that combine mutation orchestration, modal composition, generated-data reads, and rendering. Modal code is part of that maintainability problem because rendering, event wiring, validation, state transitions, and domain writes are often embedded in the same large files.

The extraction covered current files with modal responsibilities rather than leaving a known "still to extract" modal set. Completing the extraction as a preparatory phase lets the actual modal pattern redesign start from cleaner ownership boundaries and avoids mixing architectural decisions with large-file untangling.

The extraction stayed modal-focused. It separated modal rendering helpers, descriptors, local modal validation, and modal event/lifecycle wiring where appropriate, while keeping route orchestration and domain writes owned by the route command or opener. It did not attempt broad cleanup of every route-controller concern.

The completed extraction is tracked in [Modal Responsibility Extraction Plan](/docs/?scope=studio&doc=modal-responsibility-extraction-plan).

## Migration Review

The review should extend beyond inventory and classify each existing modal against the new preferred patterns.

For each page-level migration unit, record:

- current owner and file locations
- current modal set and implementation group
- proposed target pattern or patterns used on that page
- whether openers or modal helpers currently own domain actions
- CSS namespace and whether styling should remain route-local, move to the shared shell, or remain as a portable Docs Viewer equivalent
- migration risk, especially for local write flows, file inputs, async service calls, focus handling, and generated Docs Viewer management markup

The migration plan should be incremental but page-level. A page or route can be prioritized because it is low risk, but completion should mean all modals on that page have been checked and migrated together. Splitting one page into smaller modal slices should be exceptional and should leave a clear temporary tracker note.

Shared helpers can still be implemented once and reused across several pages. The tracker state should remain page-based: a shared helper change does not mark a page done until the page's current modals have been visually and behaviorally checked against the contract.

## Migration Tracker

Status values:

- `planned`: current modal page identified but not started
- `in-progress`: route is actively being migrated or verified
- `done`: all current modals on that page follow the chosen shell, focus, action-row, validation, CSS, and action-ownership contracts
- `blocked`: page cannot be completed without an explicit design, portability, service, or route-lifecycle decision

The priority order is easiest-first where practical, not scope reduction. Every row is required before this request can be considered complete.

| Priority | Status | Page / route | Current modal set | Primary owner files | Migration notes |
| --- | --- | --- | --- | --- | --- |
| 1 | planned | `/studio/activity/` | Activity detail notice modal | `assets/studio/js/activity-log.js`, `assets/studio/js/activity-log-modals.js` | Low-risk transient notice flow; good first proof for simple result/notice behavior. |
| 2 | planned | `/studio/data-sharing/prepare/` | Prepare result modal | `assets/studio/js/data-sharing-prepare.js`, `assets/studio/js/data-sharing-prepare-modals.js` | Low-risk result modal with structured body content and no domain write inside the modal. |
| 3 | planned | `/studio/data-sharing/review/` | Review result notice modal and apply confirmation modal | `assets/studio/js/data-sharing-review.js`, `assets/studio/js/data-sharing-review-modals.js` | Covers notice plus confirmation helpers on one page; verify returned-package apply remains route-owned. |
| 4 | planned | `/studio/catalogue-work-detail/` | Catalogue action confirmations for prose overwrite, publication, and delete flows | `assets/studio/js/catalogue-work-detail-editor.js`, `assets/studio/js/catalogue-work-detail-actions.js`, `assets/studio/js/catalogue-editor-action-modals.js` | Mostly shared transient confirmations; page completion should still verify all current detail-editor modal flows. |
| 5 | planned | `/studio/catalogue-series/` | Catalogue action confirmations for prose overwrite, publication, and delete flows | `assets/studio/js/catalogue-series-editor.js`, `assets/studio/js/catalogue-series-actions.js`, `assets/studio/js/catalogue-editor-action-modals.js` | Similar to work-detail route; keep series membership and publication writes owned by page actions. |
| 6 | planned | `/studio/catalogue-moment/` | Catalogue action confirmations for publication, delete, and related moment actions | `assets/studio/js/catalogue-moment-editor.js`, `assets/studio/js/catalogue-moment-actions.js`, `assets/studio/js/catalogue-editor-action-modals.js` | Similar shared confirmation path; verify moment import/apply ownership does not move into modal helpers. |
| 7 | planned | `/studio/analytics/series-tag-editor/` | Save preview modal | `assets/studio/js/series-tag-editor-page.js`, `assets/studio/js/tag-studio.js`, `assets/studio/js/tag-studio-modals.js` | Single persistent preview modal; confirm clipboard/status behavior stays route-owned. |
| 8 | planned | `/studio/analytics/series-tags/` | Offline session modal and import modal | `assets/studio/js/series-tags.js`, `assets/studio/js/series-tags-modals.js` | Moderate complexity because file import, review rows, conflict resolution, and session actions share one page. |
| 9 | planned | `/studio/catalogue-work/` | Embedded download/link entry modals, embedded delete confirmation, build preview modal, and catalogue action confirmations | `assets/studio/js/catalogue-work-editor.js`, `assets/studio/js/catalogue-work-editor-modals.js`, `assets/studio/js/catalogue-work-actions.js`, `assets/studio/js/catalogue-editor-action-modals.js` | Complex route-owned workflow page; migrate all work-editor modals together unless a specific blocker is recorded. |
| 10 | planned | `/studio/analytics/tag-registry/` | Import, patch, edit, new-tag, demote, delete, and detail confirmation modals | `assets/studio/js/tag-registry.js`, `assets/studio/js/tag-registry-modals.js`, `assets/studio/js/studio-modal.js` | Complex route-owned workflow page with popups inside modals and local write flows. |
| 11 | planned | `/studio/analytics/tag-aliases/` | Import, patch, promotion, demote, edit/create, delete, and detail confirmation modals | `assets/studio/js/tag-aliases.js`, `assets/studio/js/tag-aliases-modals.js`, `assets/studio/js/studio-modal.js` | Similar complexity to Tag Registry; verify promote/demote/delete write ownership remains in route commands. |
| 12 | planned | `/docs/?mode=manage` | Metadata, import, settings, transient confirm/text/choice, and Docs HTML import filename-conflict modals | `_includes/docs_viewer_shell.html`, `_includes/docs_import_shell.html`, `assets/docs-viewer/js/docs-viewer-management.js`, `assets/docs-viewer/js/docs-viewer-management-modals.js`, `assets/docs-viewer/js/docs-html-import.js`, `assets/docs-viewer/js/docs-html-import-modals.js`, `assets/docs-viewer/css/docs-viewer-management.css` | Highest portability risk. Keep Docs Viewer portable implementation if needed, but require parity with the shared composition contract. |
| 13 | planned | `/studio/ui-catalogue/demos/` | Demo modal pattern | `studio/ui-catalogue/demos/`, `assets/ui-catalogue/js/ui-catalogue-demo.js`, `assets/ui-catalogue/css/ui-catalogue-demo.css` | Demo route should be updated after the production contract is stable so examples do not preserve obsolete modal anatomy. |

## Benefits

- keeps modal UX predictable across Studio and Docs Viewer surfaces
- prevents modal components from hiding mutation behavior
- makes UI audits more useful for composed workflows, not just standalone page controls
- reduces duplicated modal styling and one-off interaction fixes

## Risks

- too much abstraction could slow route-specific workflow fixes
- converting existing modals in bulk could introduce regressions in local write flows
- action ownership needs clear naming so code does not become harder to follow

## Open Questions

- Should `renderStudioModalFrame()` become the canonical shell as-is, or does it need a small accessibility/focus/action-row refinement before standardization?
- Should Docs Viewer management keep static portable shell markup while matching Studio composition rules, or migrate more of its shell rendering into portable JS helpers?
- Which extracted route-local modal should be the first complex workflow example in permanent guidance?
- Should modal-return contracts be documented as JavaScript helper APIs, prose rules, or both?

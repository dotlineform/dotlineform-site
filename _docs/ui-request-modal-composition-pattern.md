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

## Summary

Define a shared modal composition pattern for Studio and Docs Viewer interfaces (see [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue))

The pattern should make modals consistent as UI containers while keeping domain actions owned by the page or command that opens the modal.

The review should also explain the current implementation spread. Existing Studio and Docs Viewer modals use several reasonable but different approaches, and that variety now makes the codebase harder to understand, harder to discuss when requirements change, and harder to extend safely.

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
- map existing Studio and Docs Viewer modals to the preferred patterns before starting broad migration work
- produce an implementation plan for migrating existing modal code and CSS toward those patterns

## Non-Goals

- converting every existing modal in the first implementation slice
- creating a new modal framework before inventorying current modal usage
- changing service endpoints only to fit the modal pattern
- using modal guidance as a substitute for route-specific workflow design

## Current Implementation Context

Current modal implementations appear to fall into these broad groups:

- Shared Studio helper modals: `assets/studio/js/studio-modal.js` renders transient confirm, detail-confirm, patch-preview, and notice modals, then wires the current primary/cancel buttons directly. These work well for simple promise-style flows where the caller awaits a result.
- Pre-rendered Studio route modals: Tag Registry, Tag Aliases, and Tag Studio render one or more hidden modal frames as part of the route shell, keep references to their controls, and delegate some events to route or modal containers. These work well for persistent route tools with internal controls, popups, and multiple modal states.
- Re-rendered Studio modal hosts: Series Tags and some result modals render modal HTML into a host as state changes. Host-level delegation helps the handlers survive repeated `innerHTML` replacement.
- Catalogue editor transient modals: Catalogue Work Editor creates short-lived modal DOM for embedded entries and build previews, then wires direct listeners for that modal instance. This is simple for tightly scoped edit operations but differs from the shared helper contract.
- Docs Viewer management modals: Metadata, Import, and Settings modals are static markup in the Docs Viewer shell. Management code uses delegated root close handling plus direct form and button handlers. Metadata editing already follows the desired ownership boundary: the modal collects payload values, then the opener save flow performs the write.
- Docs HTML import conflict modal: The HTML import route has a separate modal host, frame renderer, CSS namespace, and direct button listeners for filename conflict resolution.
- Native browser dialogs: Some Docs Viewer management actions, such as creating a new doc from the Actions menu or context menu, currently use `window.prompt()`. Archive and delete flows also use native confirmation dialogs in places. These dialogs are locally simple but visually and behaviorally outside the Docs Viewer UI.

The issue is not that any one implementation is wrong. The issue is that the codebase now has enough valid local approaches that it is difficult to tell which one should be used for a new requirement, which old one should be extended, and which CSS layer is authoritative.

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

The higher-level simple helpers such as `openConfirmModal()` and `openNoticeModal()` should be treated as convenience APIs on top of the shared shell, not as separate modal patterns. They are useful for simple cases, but they should not define a different shell, CSS vocabulary, or action ownership model.

The target is one shell contract and one modal CSS vocabulary, not separate shells for simple, medium, and complex modals. Simple and medium modals should use the same shell as complex modals, with less content and thinner helper APIs. This avoids encouraging new local patterns every time a modal starts simple and later gains validation, extra controls, async behavior, or workflow state.

Under this direction:

- the shared shell owns modal structure, backdrop, dialog role, title wiring, action-row composition, close affordances, responsive sizing, focus behavior, and Escape handling
- route-owned workflow modals own route state, local control rendering, validation that belongs to the local input flow, and the domain command that consumes the modal result
- transient result helpers own a small result contract but still render through the same shell and CSS vocabulary
- Docs Viewer management should either adopt the same shell contract directly or be documented as a route-owned workflow modal using the same composition rules

Native browser dialogs such as `window.prompt()`, `window.confirm()`, and `window.alert()` should not be treated as modal composition patterns for Studio or Docs Viewer management UI. Existing uses should be classified as migration debt and moved to transient result modals using the canonical shell, unless kept temporarily as explicit fallback behavior.

For example, Docs Viewer Actions -> New should become a transient result modal that collects a title and returns a cancel or value result. The modal should own the title input, local required-title validation, OK/Cancel controls, focus behavior, and Escape handling. The Docs Viewer command should continue to own `createManagedDoc()`, management status, index reload, and error handling.

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

## First Implementation Slice

1. Inventory existing Studio and Docs Viewer modals.
2. Identify the shared shell already closest to the desired pattern.
3. Write the stable pattern under the UI composition-pattern docs.
4. Update UI audit guidance to include modal composition checks.
5. Convert only one representative modal if needed to prove the guidance.

## Modal Extraction Prerequisite

Before redesigning or migrating the modal shell pattern, do a modal-focused extraction pass across all files that currently own modal responsibilities.

This follows the maintainability direction from [Studio JavaScript Payload Inventory](/docs/?scope=studio&doc=studio-javascript-payload-inventory). That inventory already flags long mixed route controllers that combine mutation orchestration, modal composition, generated-data reads, and rendering. Modal code is part of that maintainability problem because rendering, event wiring, validation, state transitions, and domain writes are often embedded in the same large files.

The extraction should cover all current files with modal responsibilities rather than leaving a set of known "still to extract" modal code. Completing the extraction as a preparatory phase lets the actual modal pattern redesign start from cleaner ownership boundaries and avoids mixing architectural decisions with large-file untangling.

Extraction should stay modal-focused. It should separate modal rendering helpers, descriptors, local modal validation, and modal event/lifecycle wiring where appropriate, while keeping route orchestration and domain writes owned by the route command or opener. It should not become a broad cleanup of every route-controller concern.

Track this prerequisite in [Modal Responsibility Extraction Plan](/docs/?scope=studio&doc=modal-responsibility-extraction-plan).

## Migration Review

The review should extend beyond inventory and classify each existing modal against the new preferred patterns.

For each modal, record:

- current owner and file locations
- current implementation group
- proposed target pattern
- whether the opener or modal currently owns the domain action
- CSS namespace and whether the styling should remain route-local or move to the shared shell
- migration risk, especially for local write flows, file inputs, async service calls, focus handling, and generated Docs Viewer management markup

The migration plan should be incremental. It should identify one low-risk representative modal for each preferred pattern, migrate or adapt it first, then use that result to refine the shared guidance before moving broader route families.

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

- Which current modal shell should become the canonical base?
- Should the Docs Viewer metadata modal and Studio command-result modal share the exact same shell, or only the same composition rules?
- Should modal-return contracts be documented as JavaScript helper APIs, prose rules, or both?
- Should UI audits require a modal screenshot/check whenever a route has modal behavior?

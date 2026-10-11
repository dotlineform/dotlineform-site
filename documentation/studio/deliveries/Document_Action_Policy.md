---
draft: false
doc_id: d-20261010-223124-29fae8
title: Document Action Policy
added_date: "2026-10-10 22:31:24"
last_updated: "2026-10-11 00:00:00"
parent_id: d-20260428-000000-f5ff18
summary: Frontend action availability for Catalogue Work, collection-host and private-report documents, with concrete service operation validation.
ui_status: done
---
# Document Action Policy

## Current State

Implemented and source-reviewed on 2026-10-11 after the user authorized simplification of the original server-backed policy accepted on 2026-10-10. The existing frontend action resolver preserves the restrictions; server policy and guards are removed. Focused checks and the required shared runtime projection passed. The [Runtime](../Docs_Viewer_Runtime.md#document-action-policy) owns current extension guidance. No document data, Search, publication eligibility or queues changed; new manual acceptance is not claimed.

## Requirements And Decisions

- Catalogue Work documents retain only Star and Copy link; Catalogue New, package preparation and selection controls remain omitted. Regenerate remains available.
- Configured collection hosts and the 15 explicit private-report documents omit Delete, Star and Draft. Future unlisted public reports retain defaults, including Star. No hierarchy validation is added.
- Extend the existing frontend action registry/context/resolver for exact document, collection and selection targets; menus, shortcuts and contributions consume its visibility/enablement result.
- Remove the separate JSON policy, Python matcher, browser policy resolver, capability projection and endpoint guards. Editorial availability is a frontend product responsibility.
- Retain service path confinement, identity, request/revision, source/schema, authoring-workspace and operation validation. Direct service callers use those requirements; Catalogue draft remains intrinsically unsupported.
- Keep completed Catalogue document-only publication handoffs, temporary capability/busy/readiness rules, publication eligibility and source generation with their existing owners. Workspace actions remain independent of document restrictions.
- No test work is authorized. UI interaction and live service write/failure scenarios remain manual evidence gaps. Publish, deployment, commit and push remain separate explicit actions.

## Delivery Steps

- [x] DA-0 — User authorized the simplification; inspected existing action/control owners, service validation and bounded removal references.
- [x] DA-1 — Existing frontend resolver owns restrictions and resolves exact targets, Index subtrees and collection selections. Host IDs use existing browser configuration; private-report identities stay explicit.
- [x] DA-2 — Removed server policy/config/capability projection and service guards, retaining operation validation and generation/publication follow-through.
- [x] DA-3 — Focused changed-source lint, Python syntax, reference/whitespace inspection and required public projection/site validation passed.
- [x] DA-4 — Distinct final source/diff review completed; obsolete policy-arrival refresh plumbing removed and affected lint rerun. Durable docs and evidence limits match the final implementation.

## Verification And Review

Selected evidence is changed-source JavaScript/Python lint and Python compilation, plus reference/source inspection. These checks address stale imports, missing callbacks, syntax and resolver integration without document/API writes or browser startup. The required shared runtime projection uses `bin/site-code-update`, exact projected-diff inspection, `bin/site-code-update --check` and `bin/site-validate`. Expected cost is seconds to a few minutes; site validation cost is not benchmarked. No tests, fixtures, harnesses or profiles are created or changed.

`bin/lint-js` passed for all eleven changed JavaScript source files. `bin/lint-python` and Python compilation passed for all seven changed service files. Removed-owner references and added-source private-path/credential inspection found no stale production references or new sensitive values. `git diff --check` passed. `bin/site-code-update` changed only `site/docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js`; its exact diff was inspected. `bin/site-code-update --check` and `bin/site-validate` passed.

Integration review kept workspace operations outside Catalogue restrictions, preserved entry to package selection with no checked rows and avoided repeated Index subtree resolution. Distinct final source/diff review checked exact/captured targets, unchanged restriction identities, retained service validation and publication handoff, public import isolation and deleted-owner references. It found obsolete capability-triggered action reprojection; that hook, its captured owner and pass-through promise were removed. The affected two-module JavaScript lint and final whitespace check passed after the cleanup. No compatibility aliases or alternate policy APIs remain.

Follow-up inspection of the reported Catalogue menu confirmed that the local service serves the current action definitions, management controller and Edit menu bytes. Source review confirms that restricted items receive `hidden`, while Star retains transient availability. JavaScript responses have a one-day cache lifetime, so cached modules remain a possible cause of the reported disabled entries; the active browser was not inspected and the cause is not confirmed.

No tests, browser automation, live service writes or failure scenarios ran. Restart Docs Viewer and hard-refresh its page after adopting the change. No Docs/Search build or Publish is required; commit, push and deployment were not performed.

## Completion Gates

- [x] Frontend restrictions use the existing action-resolution path and exact configured identities.
- [x] Server editorial policy is removed and concrete operation validation remains.
- [x] Selected checks and required shared runtime projection pass.
- [x] Distinct final review is recorded and durable documentation matches the final implementation.

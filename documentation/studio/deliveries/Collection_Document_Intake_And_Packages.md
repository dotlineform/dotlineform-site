---
draft: false
doc_id: d-20261020-075219-60ad8c
title: Collection Document Intake And Packages
added_date: "2026-10-20 07:52:19"
last_updated: "2026-10-20"
parent_id: d-20260428-000000-f5ff18
---
# Collection Document Intake And Packages

Parent: [Planned Features](../Planned_Features.md). Durable owners: [Docs Import](../Docs_Import.md), [Package Prepare](../Package_Prepare.md) and [Toolbar Model](../Toolbar_Model.md). Status: implemented, statically verified and reviewed on 2026-10-20; awaiting user normal-use confirmation after restarting Docs Viewer services and reloading Manage.

## Agreed Result And Ownership

The user established that the Index contains structural/report documents and no normal document content needing import or export. Collections reports' Actions menus own Export, Prepare package, Import doc and Import docs. Export and Prepare package consume existing checked IDs. Both imports capture the exact collection without a checked-selection requirement, including an empty collection. Catalogue retains Export and its existing Studio/Regenerate authoring boundary.

The browser owns the invoking collection, checked IDs, summary/limit choices, synchronous native file selection, confirmation and completion feedback. Python owns configured-path authority, source discovery/conversion, media materialisation, selected package rendering/output, canonical source persistence, exact generation and its existing queue handoff. Requests never infer a destination from a displayed document or Index row. No ordinary Index import/Prepare path, descendant expansion, sibling-placement parameter or compatibility alias remains in the application.

The independent ordinary Working CLI and returned-package formats remain as previously scoped. Ordinary CLI packages have no application Import entry point. A trusted collection package or edited Review folder keeps its recorded collection; mismatches remain visible but unavailable from another collection. Existing server provenance checks retain mutation authority.

The user-approved follow-up separates selection from Actions: Select (`list-check.svg`) appears before Actions and is replaced by All/Clear/Done while checkboxes are visible. Done clears selection and restores Select. Opening Actions has no selection effect, preserving direct access to both imports.

## Completion Gates

- [x] Implement the clarified collection-only application boundary for both imports, Export and Prepare package.
- [x] Preserve exact checked selections, profile/format/summary options, collection restrictions and native picker user activation.
- [x] Remove Index package dispatch/loader, workspace import controls/dispatch, displayed-context inference, native sibling placement and unscoped import startup.
- [x] Consolidate application package metadata/rendering to collection inputs; preserve the independent CLI/shared producer and returned formats.
- [x] Remove unused import terminal-refresh code and legacy `files` discovery projection with its duplicate package/folder recognition pass.
- [x] Update current workflow, architecture, endpoint, placement and durable checklist owners.
- [x] Complete focused lint/syntax/import diagnostics, whitespace review and required public-runtime projection/check/site validation.
- [x] Complete distinct source/diff review and the mandatory Redundancy And Defensive Behavior Review.
- [x] Separate selection entry from Actions with the approved Select icon button and existing Done behavior.
- [ ] User normal-use confirmation after restarting Docs Viewer services and reloading Manage: all four menu items, both imports in an empty collection, checked package preparation, cancellation/completion, destination-matching packages and Catalogue restrictions.

## Verification Budget And Limits

Use changed-owner JavaScript/Python lint, Python compilation/module-import diagnostics and bounded source/diff review to catch syntax, removed-symbol and integration mistakes. Use the required public projection, projection check and static-site validation because shared startup/callback wiring changed. These local commands should take seconds to a few minutes, write only bytecode/tool caches and the exact tracked shared-runtime projection, and perform no browser interaction, source mutation, generation, package write or network transfer. [Testing](../Testing.md) and [Test Contract Discipline](../Test_Contract_Discipline.md) own evidence policy; no tests, fixtures, harnesses or temporary regression scripts are authorised or changed. Historical tests of retired Index/ordinary-import APIs remain unreviewed and are not current verification evidence.

## Code Review And Redundancy And Defensive Behavior Review

Distinct final review traced collection action resolution/registration, empty/checked selections, Catalogue restrictions, synchronous native picker activation, committed/terminal refresh, exact package destination matching, collection request resolution, selected-source rendering and the retained independent CLI/shared producer. Import menu registrations use collection targets and `emptyState: enabled`; Export/Prepare retain selection targets and disabled-empty behavior. Native selection reaches `input.click()` synchronously through the registrar/runtime/controller callbacks, with no awaited load or request. Existing returned-package and Review-folder planning already enforce the exact collection, so no duplicate server provenance pass was added.

Removed unnecessary work and compatibility residue: the second Index package loader/dispatch and capability projection; subtree discovery/expansion and ordinary renderer branches in application preparation; browser checks repeating the options service's selected-source/collection handoff; cached dynamic-import wrapper and export-function audit; unused browser returned-list/profile helpers; workspace import buttons/event dispatch, displayed-context inference, sibling placement, unscoped startup and dead ordinary terminal refresh. The unused `files` compatibility projection repeated package/Review-folder recognition and directory listing alongside `candidates`; the current classifier is now the sole discovery response owner. No alias, fallback target, automatic repair, freshness protocol or recovery mechanism was added.

Retained safeguards and costs: request parsing and exact configured collection/ID syntax bind external requests to their actual filesystem owners; selected path/symlink and filename/source-ID checks protect confined reads. Native request/part bounds and suffix/filename checks protect upload intake before conversion. Existing conversion/sanitization, exclusive source writes, media verification, profile/format/output collision checks and trusted returned-package confirmation remain with their established owners. They perform their required selected work without a new corpus audit, build or extra discovery request. Candidate mismatches are a browser membership choice using supplied manifest identity; destination labels continue showing that identity rather than an unavailable placeholder.

Review found and fixed the mismatched-candidate label dependency and removed the duplicate discovery projection and unused package-browser helpers. No unresolved implementation finding remains in this bounded source review. Manual browser behavior and live service operations remain unexercised; historical tests reference removed APIs and require a separately approved migration.

## Selected Evidence

- `bin/lint-js` passed for all 22 changed canonical JavaScript owners; the last client/view-only cleanup passed its focused two-file rerun.
- `bin/lint-python` and `$HOME/miniconda3/bin/python3 -m py_compile` passed for all six changed Python owners: package `selected_sources.py`/`service.py`, `docs_import_doc.py`, `docs_import_document.py`, `docs_import_source_service.py` and `docs_management_import_service.py`.
- With `.env.local` exported and project service/build paths supplied, direct imports passed for package service, native import, staged source import, management import and the management service. These diagnostics made no operation request or source/package write.
- `bin/site-code-update` changed exactly three tracked shared runtime projections: app composition, app context and app runtime. The inspected delta removes unscoped import startup and forwards collection import callbacks; no private management module enters the public graph. `bin/site-code-update --check` and `bin/site-validate` passed, covering the configured 105 projected files and required static boundaries.
- `git diff --check` passed. No tests, browser automation, live imports, package output, document/Search generation, Publish, commit, push or deployment ran.

## Separate Select Control Follow-Up

Implemented on 2026-10-20 in the existing management collection contribution and local management stylesheet. Select enters the existing browser selection owner; the existing projection swaps Select for checkboxes and All/Clear/Done before Actions. Actions no longer calls selection entry. Done uses the existing owner to clear checked IDs/range state, restores Select and returns focus to it; entering selection focuses All, or Done if All is unavailable. The existing `list-check.svg` receives one local CSS mask rule. No new selection state, persistence, service request, validation or recovery path is added.

Verification budget: one changed-owner JavaScript lint, whitespace check and bounded source/diff review, expected to take seconds with no application writes or network. `bin/lint-js docs-viewer/runtime/js/management/docs-viewer-management-collection-default-contribution.js` and `git diff --check` passed. The two changed runtime owners are local-only and outside the public projection inventory; no public projection or site build ran. Tests and browser automation remain unchanged and unrun. Manual confirmation covers icon placement, the controls/checkbox swap, Actions independence, Done clearing/restoration and direct import access.

Distinct source/diff review and Redundancy And Defensive Behavior Review traced idle/active/Done projection, empty-list focus, existing busy availability, checked-ID clearing and independent import/selection action dispatch. One existing selection owner remains authoritative. The change removes Actions' implicit state transition and adds only the local Select control, mask and projection; it adds no server work, duplicate validation, inventory read, persisted flag or compatibility branch. Shared hidden-button styling already handles Select, and existing collection-control styling handles All/Clear/Done. No unresolved source-review finding remains; tactile/visual behavior remains for user confirmation.

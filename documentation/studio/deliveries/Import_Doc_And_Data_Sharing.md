---
draft: false
doc_id: d-20261017-000000-7d86a1
title: Import Doc And Data Sharing
added_date: "2026-10-17"
last_updated: "2026-10-17"
parent_id: d-20260428-000000-f5ff18
---
# Import Doc And Data Sharing

Parent: [Planned Features](../Planned_Features.md). Durable owners: [Docs Import](../Docs_Import.md) and [Docs Import Architecture](../Docs_Import_Architecture.md).

## Current And Next State

Implemented and reviewed on 2026-10-17; awaiting user normal-use acceptance. Import doc uses browser-native single-file selection and inserts immediately after the current ordinary document, sharing its parent; existing Import is rooted at `data-sharing` with `data-sharing/import-staging` as its default. Both reuse the existing converters and document persistence owners.

Next: restart the Docs Viewer service, reload Manage and exercise native single-file imports and existing folder/package workflows. Earlier Index sorting and Import-breadcrumb changes in the dirty worktree remain preserved. No test work was requested or approved.

## Requirements And Deliverables

- [x] Add Import doc beside Import in Manage Actions. Invoke a single-file browser input synchronously from the action click; accept Word, HTML, Markdown and text files from any user-selected location. Hold the selected File through confirmation containing only the filename and complete-folder guidance. Cancel releases it without an upload or document write. Busy state starts at submission and clears on request failure; keep it through committed/display completion after success.
- [x] Freeze the current ordinary-document destination using existing collection rules; Catalogue remains outside ordinary document authoring. Native HTML includes obvious prompt/meta blocks automatically; existing Import retains its checked-by-default option and choice across candidate/folder selection. Import always creates a new document. Reuse committed-record adoption, Index refresh and exact displayed-result handling; report display failures separately from a completed import.
- [x] Capture the mounted ordinary document when Import doc opens. Insert immediately after that anchor with the same parent using Position's existing `insert_node` helper, keeping any anchor subtree intact. Carry completed hierarchy into generation and the committed record; omit a redundant parent request, membership audit or separate Position operation. No current ordinary document retains root append; flat named collections and existing Import retain their placement.
- [x] Use one bounded multipart upload on confirmation. Reuse native upload limits and basename safety. Use only a request-local temporary converter input, retaining embedded media and cleanup after awaited persistence/generation. Native intake has no staging-directory preference, listing, package recognition, companion-file discovery or OS-service picker bridge. JSON/JSONL, folder sources, reviewed source sets and interactive companions retain existing Import.
- [x] Extract one ordinary source completion owner shared by uploaded and staged sources. Reuse existing format converters, media planning, exact create/source writers and targeted generation. Carry completed conversion into media materialisation and the prepared SourceDoc/applied parentage into the existing in-process exact builder. Omit target-source rereads, ID rediscovery, configuration reload, subprocess builds and the target-collection scan used only for random-ID allocation; the exact planner and exclusive new-source write retain collision authority.
- [x] Constrain existing Import listing, inventory and apply to `data-sharing`; retain existing supported sources and staging-only package/review rules. The default is `data-sharing/import-staging`; remembered folders inside the root remain valid, while outside-root preferences are cleared before opening staging. Keep browser/server roots aligned.

## Delivery Steps

### ID.0 — Readiness

- [x] Confirm native Studio selection, existing ordinary/collection Import branches, shared converters, document/media writers, browser action/modal owners and configured directory confinement.

Record: ready. Existing Import selects one candidate, including directories and trusted complete collections. Native Import doc is ordinary single-file intake and can share the existing ordinary conversion/planning/apply flow after transport selection. The upload requires its own byte/field boundary; configured Docs ownership stays authoritative, and temporary converter input is not a replacement workspace. No public reader module or deployment artifact is involved.

### ID.1 — Implementation And Focused Evidence

- [x] Implement both browser flows and their narrow server boundaries.
- [x] Extract/reuse ordinary-document completion and remove target-corpus discovery from create allocation.
- [x] Update durable workflow/architecture and implementation guardrails.
- [x] Complete selected static/import checks.

Verification budget: changed-path Python/JavaScript lint, Python compilation, `git diff --check`, service `--help` import/startup diagnostic and bounded source/diff review. These diagnose syntax, module imports, route/transport/selection agreement and ownership at small local cost, with ignored caches only and no live workspace/queue/media writes or network access. Service help exits before binding a port. No tests, fixtures, temporary regression scripts, browser automation, live imports, Build, Search refresh or Publish are included. Manual gates cover native picker/Cancel, accepted single-file formats and embedded media, HTML options, destination/create semantics, retained views, package/folder Import and root-bounded navigation.

Record: `bin/lint-js` passed for all nine changed frontend owners. `bin/lint-python` and `python3 -m py_compile` passed across all nine changed Python owners, including focused rechecks after review corrections to native intake, shared ordinary completion, prepared document/apply, dependency wiring and warning presentation. `python3 docs-viewer/services/docs_viewer_service.py --help` passed with the configured environment before and after prepared-generation wiring. `git diff --check` passed. Initial lint found two unused extraction locals and an unused upload-model import; these were removed. Evidence is static/import-only, with no executed conversion, import, media or browser outcome claim.

Sibling-placement evidence: changed-path JavaScript lint passed for management composition, native workflow and client; Python lint and compilation passed for native intake, shared ordinary completion and source apply. The configured service `--help` diagnostic and `git diff --check` passed. Source review traced the mounted action context through frozen confirmation, optional `after_doc_id`, the canonical hierarchy write, completed parent map, prepared source, committed record and targeted metadata order. No test code, fixture or browser automation was added or changed; nested/root placement and retained-view interaction remain manual acceptance gates.

Prompt/meta default evidence: focused JavaScript lint passed for the existing Import browser owner and native Import doc workflow; `git diff --check` passed. Existing Import's HTML checkbox starts checked and sends the user's explicit boolean; native HTML supplies true automatically. No tests or live imports ran for this default-only change.

Confirmation evidence: focused JavaScript lint passed for native workflow and management composition; `git diff --check` passed. Source review confirms the normal body contains only the escaped filename and requested folder guidance, native HTML supplies its inclusion flag automatically, and busy state begins at submission. Idle confirmation, request failure/retry and completed display remain manual interaction checks; no browser automation or live import was run.

### ID.2 — Code Review

- [x] Review the final bounded implementation and reused converters/writers after selected evidence.
- [x] Complete the mandatory Redundancy And Defensive Behavior Review; record findings, removals and justified retained boundaries.

Record: the distinct post-evidence review traced action dispatch/user activation, Cancel and pending-file release, frozen destination/authoring gates, UTF-8 filename/opaque-byte upload agreement, HTTP byte limits, exact field parsing, request-local converter input, every ordinary format, embedded media, common create/apply/generation, committed/display completion, Data Sharing navigation/list/inventory/apply boundaries and retained package/Review consumers. Ordinary uploads never enter package discovery or companion-directory scans. The new action is management-only and no represented public runtime file changes.

Resolved findings: remove unused extraction locals/imports; remove the corpus read and retrying allocator used only to choose a new immutable ID; retain converted HTML Markdown/SVG inputs for media processing; carry the planner's prepared SourceDoc and the writer's completed tree into the existing exact generation owner, replacing ordinary Import's subprocess/workspace/source rereads and ID rediscovery during final generation. Existing converter/media projection configuration remains with the reused media owner. Package consumers ignore the returned tree and gain no unused parent-map traversal. Return only committed target/record and warnings for native intake, omitting the staged envelope and unused converted-body/media-plan payload. Surface converter warnings after successful native import and close its confirmation before retained/display follow-through, so a display failure does not invite another source import from the same modal.

Retained boundaries and cost: the HTTP owner bounds the single request before parsing; its parser owns field shape, safe basename, supported file representation and byte budgets. Existing provenance/role recognition prevents standalone reviewed Markdown or companion scripts being treated as ordinary native documents; converters own actual document parsing and new-source validity. Their selected-file classification reads are bounded to this one source, with no source or target corpus audit. Configured destination authority/confinement, root-bounded filesystem resolution, exclusive create writes, existing media sanitization/transfer completion and exact generation remain with their established owners. No freshness pass, extra metadata endpoint, compatibility alias, persistent upload receipt, rollback/retry state or additional document ledger was added. Existing collection provenance/planning and ordinary failure/retry semantics remain with their current owners. These outcomes have source/static evidence; imports, package operations, failures and tactile presentation remain unexercised.

Sibling-placement review: the frontend owns the mounted displayed anchor and freezes its identity before native selection. The server adds only request identity/ordinary-versus-flat authority parsing and the required canonical insertion, reusing Position's existing helper. The source writer still reads/writes the hierarchy once, and generation consumes the already completed parent map. No extra by-ID/source fetch, parent lookup request, membership audit, source corpus scan, separate move, freshness check or recovery layer was introduced. Missing anchors fail through the existing insertion helper; they are not silently relocated. Review removed an unnecessary reconstruction of the original ImportContent that would have repeated its constructor validation after persistence. Only the prepared SourceDoc, completed plan parent and committed summary receive the resolved parent; incoming source content remains unchanged. Focused Python lint/compilation was repeated for that correction. Existing staged/package callers retain their supplied-parent insertion, and named collections retain their flat placement. No compatibility alias was found or added in the changed path.

Prompt/meta default review: defaults remain frontend-owned and reuse the existing explicit request/converter flag. Removed the presentation-time reset that cleared the checkbox whenever an HTML candidate was not selected; otherwise initial empty selection and format changes would undo the new default or the user's choice. Both flows send false for non-HTML; native HTML sends true without an option in its simplified confirmation. No server default, validation, additional call or fallback was added. Manual acceptance should check initial HTML selection, opt-out and switching away from/back to HTML in existing Import, plus native HTML inclusion.

Confirmation review: removed unused destination/anchor labels from native workflow settings along with their presentation. The captured destination/anchor still pass unchanged to persistence. Busy ownership now covers actual submission and successful display completion, clearing before a failed request becomes an idle retryable confirmation. Shared modal submission controls already block duplicate submit/Cancel while running; no additional state machine, cursor override, request, validation or recovery behavior was added. Filename HTML escaping remains at the display boundary. This review followed focused lint/whitespace evidence.

### ID.3 — Closeout

- [x] Reconcile code/evidence claims and record remaining manual review.
- [ ] Record user normal-use acceptance.

Record: implementation/review complete, manual acceptance pending. Confirm native chooser and both Cancel paths, ordinary/collection destinations, insertion immediately after nested/root documents including an anchor with children, the frozen displayed anchor despite different Index focus, no-current-document root append, each supported single-file format, HTML prompt/meta handling, embedded raster/SVG/Word media, conversion warnings, imported-document opening and retained views; then check existing Data Sharing folder/package/Review use and default/remembered-folder navigation. No tests were created, changed or run. No live Import, Build, Search refresh, Publish, media write, public projection, commit or push ran. Changed browser owners are local management/import modules outside the public code inventory; no `site-code-update` projection is required. Documentation was edited directly without generating Working documents or Search.

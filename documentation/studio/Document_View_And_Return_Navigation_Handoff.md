---
draft: false
doc_id: d-20261003-155555-59d4a7
title: Document View And Return Navigation - Handoff
added_date: "2026-10-03 15:55:55"
last_updated: "2026-10-03 19:19:18"
summary: Completed and accepted exact-reader and two-view navigation delivery, selected static evidence and separate public release requirements.
ui_status: done
parent_id: d-20261003-111241-1a513e
---
# Document View And Return Navigation - Handoff

Temporary evidence for [the completed delivery](Document_View_And_Return_Navigation_Delivery.md). DVR-0–5 were accepted and closed on 2026-10-03; the user then approved DVR-6's two-view follow-on and accepted its closeout with “great, ok to close”. DVR-0–6 are complete and closed. Durable behavior belongs to Runtime, Search and collection-list architecture; the delivery and this handoff are ready for manual archive, and public release remains separately authorized.

## DVR-6 Continuation

Retain the current document/report and one immediate caller. Opening a third releases the oldest; Back restores the caller, consumes that return context and releases the document being left. Repeated list → Work → Back cycles reuse the same list. List → Work A → Doc B releases the list; Back restores Work A with no earlier toolbar Back. Reopening the discarded list through Index loads it again. Native browser older/Forward destinations reload the exact URL without retained state.

Media, Table, Diagram and expanded Report Content Detail stay within their current document and add no document history entry. Their local Back restores the document's position/focus and preserves its caller. Following a document link records the underlying document as caller. Hosted presentation suspend/resume history was removed.

Changed canonical modules are `docs-viewer-navigation.js`, `docs-viewer-route-workflow.js`, `docs-viewer-document-controller.js`, `docs-viewer-document-view-coordinator.js`, `docs-viewer-main-view-host.js`, `docs-viewer-content-detail-view.js`, `docs-viewer-app-runtime.js`, `docs-collection-report.js` and `docs-viewer-diagram-detail.js`, all under `docs-viewer/runtime/js/shared/`. The controller bounds payloads/mounts and owns report subscription lifetimes; discarded/refreshed records release subscriptions, collection lifecycles and adapters. Late report registrations cannot retain a released mount. Retained callers keep receiving committed updates. Source discard and exact identities keep their existing owners.

`bin/lint-js` passed for these nine files. `bin/site-code-update` changed exactly their nine public projections; `bin/site-code-update --check` passed for 101 files and `bin/site-validate` passed for 62 required files, 7 directories and 71 runtime modules. The bounded code review covered the pair/Back transition, repeated list reuse, Source cancellation, browser destinations outside the pair and asynchronous mount cleanup. These checks took less than a second each. No test work, browser automation, live mutation experiment, document/Search rebuild or publication was performed for DVR-6.

The user accepted DVR-6 and authorized closeout without individually reporting each manual scenario. Further normal-work checks include repeated list → Work → Back controls/position; list → Work A → Doc B → Back without earlier Back; reopening a discarded list through Index; Media returning within its document and preserving its caller; dirty Source cancellation; direct/reloaded first documents hiding Back; older browser destinations loading their exact URLs. Earlier accepted checks and static evidence do not establish those individual follow-on interactions.

## Completed Changes

- New shared `docs-viewer-document-target.js` and `docs-viewer-navigation.js` own exact identity and browser-history restoration. Router/workflow, controller, view coordinator, Content Detail and application composition now use one reader for ordinary/named documents. Document roots, models and presentation lifecycles remain with their owners; per-entry snapshots retain controls, scroll, focus and independent Index state. User review corrected initial loading: default/direct ordinary documents select their matching visible tree row once; named documents select no host, and later document links retain independent tree state.
- `docs-collection-report.js` is list-only. Collection contributions mount exact-document actions through the common reader. Source, Draft/Ready, Delete, New and Import target exact identity. Projects, Works, collection lists, Index, Search/Recent, Selected, Docs Media and workspace Links consume confirmed committed metadata/deletions in memory. Projects/Works retain existing membership inputs; returns perform no discovery scan.
- Build/render/link-location, broken-link, public projection, export and Review owners use `doc` or `collection`/`doc`. Review retains selected-package authority and existing safe package IDs. Host-plus-`subdoc`, scope/stage document routes and duplicate collection readers are retired without aliases. Existing packages/bookmarks using retired routes need replacement through their owner.
- Metadata/source/draft/create/import services return complete summaries from validated in-memory metadata. Source notifications cannot turn successful persistence into failed Save; listener errors are reported separately. Import summaries identify only confirmed commits, including supported partial results. Ordinary Delete includes confirmed descendants.
- Browser configuration's ordinary `document_url_template` is owned by `build/docs_builder/browser_config.py` and projected to canonical defaults. The two new shared modules are registered in `site-tools/config/site-code-update.json`; represented public code is projected under `site/docs-viewer/`. Local report/service modules remain excluded from public code.
- The approved Working source cutover changed nine active links in Beauty, Insert Doc link, 10,000, _a links test B and 3 symbols (book), plus reference text in Data Model and Reports. Exact IDs and unrelated content were preserved. External source/output lives only in the configured Docs workspace.
- Runtime, Search, collection-list architecture and Development Checklist describe the implemented model. The superseded View Caching and History and Subject Associations Retirement deliveries were removed with user approval. Catalogue stays; future Subject work, wider resource/media caching and previous/next traversal remain separate.
- Manual-review follow-ups corrected visibility selectors for the retained document mount: Source keeps its editor visible while hiding rendered children; Content Detail hides the calling document while showing its presentation. Initial ordinary-document Index selection was also restored. The user subsequently confirmed general navigation and Source opening, plus changing a title and the list updating; detailed visual/failure cases were not individually confirmed.

## Evidence And Commands

Changed-file `bin/lint-js <paths>` passed for 53 canonical/new JavaScript files; `bin/lint-python <paths>` passed for 20 Python files. Relevant follow-up selections passed after review fixes. Lint took less than a second per selection. `git diff --check` passed. A focused added-line path/credential scan found no machine paths or credential material. No tests, temporary regression scripts, browser automation or live mutation experiments were run.

With `.env.local` exported, `build_docs.py --stage working --write --skip-media-builds` and the same command with each `--collection works|concepts|moments|catalogue` completed for 41 ordinary, 244 Works, 246 Concepts, 57 Moments and 4,616 Catalogue documents, with zero warnings. Use the pinned Python interpreter per project instructions. These full builds were selected for the global route/render contract; they updated replaceable Working output and canonical generated browser configuration, with no media build. They completed in a few seconds across the corpus. An ordinary rerun was required to correct the browser-config projection owner, rather than to demonstrate idempotence. Generated ordinary/named by-ID output contains no `subdoc=` route. Do not repeat builds without a new reason.

`bin/site-code-update` projected and its tracked delta was inspected. `bin/site-code-update --check` passed for 101 projected code files. `bin/site-validate` passed for 62 required files, 7 required directories, 71 runtime modules and the retained public route files. These prove code projection/deploy-root integrity; they do not prove interaction or migrate existing public snapshot configuration/data.

## Acceptance And Separate Work

On 2026-10-03 the user confirmed general navigation, opening Source editor, changing a title and the list updating, then authorized closeout. Further testing will be part of normal work. Detailed scroll/focus, Source cancellation, Subject/readiness changes, Delete/Import, failure recovery and public/Review cases were not individually confirmed; acceptance does not claim exhaustive coverage.

**Public release requires an authorized Publish before using or releasing the new public runtime.** The tracked public runtime is updated, but existing Preview/site browser configuration and generated links still belong to the previous prepared snapshot and are incompatible with this cutover. Publish must prepare and distribute the new configuration/documents together. Do not hand-edit generated public data, add compatibility aliases or commit/deploy the runtime by itself.

Search's saved index, body postings and coverage are unchanged. Search rebuild, Publish, commit, push and deployment were not performed. Tests were not migrated or run; examples in `docs_viewer_stage_target_contract.mjs`, `docs_viewer_subscope_report_contract.mjs`, `docs_viewer_document_link_contract.mjs` and `docs_viewer_project_state_contract.mjs` still refer to retired route/helper contracts. Any test work needs its own agreed specification; do not change production to satisfy those old assumptions.

DVR-0–6 are accepted and closed. This closeout changed only delivery/handoff status and Runtime's acceptance record; bounded source/diff review reused existing implementation evidence, with no repeated executable verification. Code review is not applicable to these status-only edits. Retain the delivery and this handoff for manual archive. Preserve unrelated worktree changes, and select only evidence warranted by subsequent fixes or release. Publish, deployment, commit and push still require explicit action.

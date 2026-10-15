---
draft: false
doc_id: d-20261015-185301-72bca9
title: Quiet Loading States
added_date: "2026-10-15 18:53:01"
last_updated: "2026-10-15"
parent_id: d-20260428-000000-f5ff18
---
# Quiet Loading States

Parent: [Planned Features](../Planned_Features.md). Durable owner: [Runtime](../Docs_Viewer_Runtime.md#three-surfaces). The user explicitly requested identification and removal of loading-type messages across Manage/Public, including remaining collection reports, document images and equivalent modal messages.

## Agreed Result

Transient loading, running, preparing, searching, creating, planning, applying, reconciling and availability-check text is removed at the frontend presentation owners. Errors, completion results, empty states, action labels, request lifetimes, busy/disabled controls, existing busy cursors and accessibility state remain. Python persistence, generation and transfer owners are unchanged. There is no global message filter, CSS hiding rule, new loading framework, fallback, validation or recovery behavior.

| Surface | Removed text and owning boundary |
| --- | --- |
| Reports | Generic local/public loader notices; public collection loading; Works, Catalogue Works, Series/Galleries, Docs Media, Links, Project State, Uncataloged Files, Missing Source Files and Work resource runs. |
| Shared reader | Recent/Search pending text; inline Catalogue image requests and Media View member/gallery selection. Existing document navigation was already quiet. |
| Management | New/Rebuild/Publish/Delete/Open progress; Catalogue Regenerate modal body; checking/busy/waiting tooltips for context/Index/collection controls. |
| Source and packages | Source loading/Save/media-option notices, Insert doc link loading placeholder, and package option/preparation messages. |
| Import and Export | Import boot/source inventory, ordinary multi-file progress, conversion, Review preparation, collection planning/apply/report-refresh text and apply panel; dated snapshot preparation/export. |
| Review | The separate package Build status is also quiet, consistently with the shared reader and Import Review handoff. |

The only control-state adjustment separates disabled flags from transient explanatory strings. Context actions retain global busy/service, exact-document, collection-readiness and Selected-readiness conditions at both render and invocation. Index actions retain capability/target/editor/workflow guards. Collection package preparation retains its in-flight flag. Startup and picker status nodes start empty/hidden and remain available to their existing error owners. Removed message-only source-title and import-progress metadata are no longer passed through action/import calls.

## Completion Gates

- [x] Readiness and explicit edit authorization: inventoried canonical JavaScript, route markup, configuration, media rendering and the shared folder picker. Existing user/default cleanup was already dirty and is preserved.
- [x] Remove transient text from 31 canonical JavaScript modules, preserving busy/error/completion behavior and explicit disabled flags; project four changed public modules through the existing inventory.
- [x] Focused evidence: explicit 31-file JavaScript lint passed. `bin/site-code-update` changed only the public report loader, collection report, media detail and Search controller projections; their exact tracked deltas were inspected. `bin/site-code-update --check`, `bin/site-validate` and whitespace checks passed. Source searches leave loading only in lifecycle state, image-loading policy and comments; remaining ellipsis text labels actions that open dialogs. No test code was changed or run.
- [x] Distinct source/diff review and mandatory Redundancy And Defensive Behavior Review traced message setters, report/error paths, media retry/disposal, Import startup/error visibility, modal busy controls and control-state consumers/dispatch. It confirmed disabled flags remain authoritative when tooltip reasons are empty. No unresolved production findings remain.
- [ ] User manual acceptance after force reloading Manage and public preview: navigate collection reports, display/open document images and Media View, use Search/Recent and the normal Source/picker/Import/Export/package/Regenerate actions as needed. Confirm quiet in-flight display and retained busy/error/completion behavior during ordinary use. Review package Build remains a separate manual observation if used.

Verification budget: changed-source lint, bounded literal/reference/diff review, inventory-owned code projection, projection check, site validation and whitespace checking. Expected execution cost is seconds, with source-review effort proportional to the distributed UI owners; only tracked public JavaScript projection writes are required. No browser/server startup, live API/authoring/transfer call, document/media/Search build or external workspace mutation is justified for this text removal. New or changed tests remain separately approved under [Test Contract Discipline](../Test_Contract_Discipline.md).

## Review And Closeout

Implemented and reviewed; manual acceptance remains open. The mandatory review retained operation guards because they prevent duplicate actions or actions without loaded targets/selections. Request/response checks, path/identity authority, media acquisition, rendering and retained-view disposal were not broadened. Clearing status uses existing setters so old errors do not persist into a new attempt; error and result text is not suppressed. No server work, additional reads/requests, corpus scans, refreshes, tests or compatibility paths were added.

The prior default-document cleanup remains intact, including its already projected app-runtime change. This delivery adds exactly four public-module projections, with no configuration, document data, Search, media or Preview output changes. No automated tests, browser/manual actions, service restart, Publish, deployment, commit or push were performed. Retain this delivery and its Planned Features link through manual acceptance; the Runtime and Development Checklist paragraphs hold the durable rule.

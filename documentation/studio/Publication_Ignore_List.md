---
draft: false
doc_id: d-20260913-191339-834d6a
title: Publication Ignore List
added_date: "2026-09-13 19:13:39"
last_updated: "2026-10-16"
summary: Use Working source/unpublishable.json for ordinary-document ID exclusions alongside draft, retire per-report access, and let Unpublishable read and open that exact JSON file in VS Code.
ui_status: done
parent_id: d-20260908-171728-3c539a
---
# Publication Ignore List

## Current Generation Ownership

`working/source/unpublishable.json` is the single exclusion-policy input. Working index generation reads it once per operation and carries the exact ID set in memory through ordinary/collection projection and required dependent generation. Exact Save/Rebuild/Position follow-through uses the current policy, as complete builds do. Editing the list therefore affects the next index generation; no saved policy copy or change record is kept in `index-tree.json` or another generated file.

Saved public indexes provide previous membership for withdrawal/restoration decisions. The policy excludes ordinary roots and descendants; an excluded collection host excludes its collection. Catalogue documents retain fixed intrinsic eligibility. Generation queues completed document/manifest effects; Publish only consumes those selections and never reads the policy. Search/Recent retain their separate explicit refresh owners. [Builder](Builder.md#publish-preparation) owns the current generation handoff; the delivery terminology and evidence below are historical.

## Original Delivery Direction

Publication selection should be explicit and easy to inspect. For ordinary scope documents, Pre-publish excludes draft documents, documents whose exact `doc_id` is in the publication ignore list, and all their descendants. The concept of `publishable` does not apply to sub-scope documents: they are outside the ignore-list lookup and retain their separate draft and report-host handling. Documents do not carry a separate `publishable` field, and publication does not infer exclusions from report blocks, report IDs or other indirect metadata.

The direction, completed implementation and closeout were accepted on 2026-09-13. The JSON array of `doc_id` values, its `unpublishable.json` location, the ordinary-document boundary and removal of per-report `access` are settled. The initial list contains the 12 ordinary Working documents explicitly marked `publishable: false`, plus Projects (`d-20260805-155400-4c341f`), Missing Source Files (`d-20260807-175649-62020b`), Catalogue Works (`d-20260810-222148-99daec`) and Docs Media (`d-20260812-212735-6d9cf3`), as approved on 2026-09-13.

On 2026-09-15 the user approved extending Pre-publish ignore exclusions to descendants. The list remains a flat array of explicit IDs; Pre-publish computes the excluded subtrees without adding child IDs to the file. This supersedes the original exact-ID-only publication exclusion recorded in the 2026-09-13 acceptance evidence below. Working link discovery and relationship generation retain their existing exact-ID ignore rule.

The ignore list supplements existing draft behavior. A draft or explicitly ignored ordinary document and its descendants are excluded. Any excluded sub-scope report host also excludes its collection, including a host beneath an ignored ancestor. Draft exclusion does not require an entry in the ignore list. A listed parent can therefore keep a development branch unpublished independently of its draft state.

The `.gitignore` analogy describes a visible, centrally edited exclusion list. It does not imply Git's path-pattern syntax. Docs sources already live in the configured external Docs workspace, outside the website repository. The ignore file belongs in that workspace, independently of Git tracking.

## JSON ID List And Location

Use a simple JSON array of immutable `doc_id` strings at the configured Working source root:

```text
$DOTLINEFORM_DOCS_BASE_DIR/working/source/unpublishable.json
```

Runtime resolution uses the explicit Docs workspace source container. The source-control relocation moved this file alongside hierarchy, Recent exclusions and Selected membership; no old documents-directory location or historical scope path is a fallback. [Source Organisation](Source_Organisation.md#source-controls) owns current storage; the original delivery's lifecycle terminology below remains historical.

Example shape:

```json
[
  "d-20260810-222148-99daec",
  "d-20260909-160530-224efe"
]
```

The whole file is the array, with no wrapper object or per-document properties. `[]` is an explicitly empty ignore list. Read the IDs into a set and test exact membership to identify explicitly ignored documents; duplicate IDs have no additional effect. Pre-publish expands those ordinary roots through document `parent_id` relationships. Removing a root from the list makes its descendants eligible again unless draft state or another listed ancestor/document still excludes them. Use ordinary JSON parsing and validate the string IDs. No paths, globs, directory rules, negation, nested ignore files or report-type inference are needed.

This file is Working-source policy data, not a Markdown document or generated report payload. The shared readers and Open in VS Code action target this one file. Pre-publish reads it from Working; it is not copied into Pre-publish, Published or public document output as another policy copy.

The list applies only to the scope's ordinary documents. Determine collection ownership through the configured source collection; sub-scope documents do not acquire a publishable state or participate in this lookup. Titles and report hosts do not substitute for document identity.

## One Selection Point

| Owner | Responsibility |
| --- | --- |
| `unpublishable.json` | Explicit ordinary-document `doc_id` roots; Pre-publish excludes each root and its descendants. |
| Document `draft` | The document-level eligibility toggle for both ordinary and sub-scope documents. A draft is omitted; the ignore list additionally applies to ordinary documents only. |
| Pre-publish | Apply the ordinary-document ignore set and the applicable draft state once, then prepare the selected sources, documents and indexes. |
| Publish | Accept the complete prepared snapshot without independently deciding document eligibility. |
| Deploy | Distribute the accepted snapshot without another document eligibility check. |
| Public report runtime | Run only supported public reports and show an unavailable-report message when support is absent. |

Retire `publishable`, Set Publishable and report-based publication exclusions rather than adding the ignore file beside them. Remove eligibility dependencies on that retired field from generated data and its consumers through an explicit implementation cutover. Retain ordinary identity, data validation and existing content sanitisation responsibilities; those do not become hidden publication selectors.

Publication must not scan report blocks to decide which documents to include, strip a report because it is considered an unsuitable document, or infer a new eligibility rule from its type. Forgetting to ignore an internal report may leave a publicly visible document whose report cannot run. That is the accepted outcome; do not add automatic report exclusion to prevent it. Public report registration and loader capability remain separate from document inclusion.

The prepared document set supplies downstream indexes and related-document projections. Published/public consumers do not rescan Working sources or add their own exclusion policy. Editing the ignore file or toggling draft changes the next Pre-publish result; Published and the website retain their current snapshots until the ordinary Publish and deployment actions occur.

## Report Availability Without Per-Document Access

Remove `access` from report blocks and their generated JSON descriptors. A document identifies the report and its inputs; the viewer's registry and registered loaders determine whether that report can run in the current environment.

For example, the Works declaration becomes:

```text
:::report
id: docs_subscope
sub_scope: works
:::
```

- Manage runs its registered report implementation with the capabilities supplied by the Manage context. Public runs only an explicitly registered public implementation; the public loader allowlist remains.
- An unsupported report retains the existing unavailable-report behaviour. Publishing its containing document neither supplies an implementation nor grants local service access.
- Retire per-report `access` validation and projection, the Pre-publish local-to-public conversion and report-type exclusion, and Deploy's access-based report stripping. Publication does not rewrite report declarations to make them runnable.
- Carry the removal through report-source creation/parsing, document models, generated descriptors, runtime consumers, document-location resolution and sub-scope lifecycle checks. Preserve exact report ID, configured collection ownership, host identity and route/service capability checks; these responsibilities do not depend on a per-document access flag.
- Works must remain usable in both Manage and public through the existing `docs_subscope` implementations. No publication-time exception or compatibility `access` default should replace the removed field.

The coordinated source/code cutover is implemented and accepted. Active source report declarations have had `access` removed; parser, runtime, public metadata and tracked runtime projections follow the new contract. Generated document payloads have been reconciled.

## Shared Working Link Reads

The Insert doc link target-list service and the links builder use the same Python reader for the exact ignored-ID set. The browser modal receives the filtered target list through its existing service; it does not read the filesystem or implement another parser. Load the small set once per operation and apply the ordinary-document membership check at the existing source/target selection points.

Ignored ordinary documents are omitted from Working link discovery and generated relationships. Sub-scope documents are outside that ignore check. Drafts remain linkable in Working, for both ordinary and sub-scope documents; Pre-publish separately applies draft exclusion when preparing its selected set. Share the ignore decision without imposing publication readiness on authoring.

An ignore-file edit is visible to a fresh target-list request and subsequent ordinary link builds. Existing relationships do not need reconciliation in response to the edit. If anything consequential changes, the user will run a full refresh manually. This is an agreed operating rule, not an unresolved implementation requirement; add no automatic refresh, change-triggered reconciliation or special repair machinery for ignore-list changes.

## Unpublishable Report

Retain the exact [Unpublishable report](/docs/?doc=d-20260909-160530-224efe), `d-20260909-160530-224efe`, as the local view of the publication ignore list.

- Read the configured Working `source/unpublishable.json` and show Title and Document ID columns. Look up each title only from that listed ID's canonical ordinary Working source header, validating its front-matter identity; retain IDs with missing sources and leave their titles unavailable. Stop reading at the closing header delimiter. Use the shared front-matter syntax parser without source-model Subject/readiness/report validation or body preparation. Carry the authored title directly without another coercion or trim. Do not scan document front matter for `publishable`, derive exclusions from report blocks, enumerate collection documents or turn this into a report of every draft document.
- Provide an **Open in VS Code** link that opens that exact `unpublishable.json` in its configured external workspace location. The link targets the ignore file, not the Unpublishable report's Markdown source or a generated copy.
- Reuse the local file-opening owner with an explicit configured target. Explicit VS Code opening skips preferred-Markdown-editor discovery; the default-editor action retains that discovery. Keep the file identity exact and the operation local; this does not grant the browser a generic arbitrary-path editor.
- Edit the file in VS Code. The report is a reader, with no second editable list or publication-eligibility toggles.
- **Refresh** rereads the same file and listed source titles so edits become visible. Report refresh does not run Pre-publish, Publish, Deploy or a scope-wide document scan.
- Distinguish an empty list from an unavailable or unreadable file. Do not silently display an older list or read a substitute location.

This replaces the previous service's ordinary-Working-source scan for explicit `publishable: false`. The report description now identifies its actual JSON input; it does not claim sub-scope or draft coverage.

The server loads Working configuration once, supplies it to the shared policy reader and reads only the listed source headers. The policy reader owns JSON and immutable-ID validation and deduplicates the editable list. Its validated IDs form direct-child Markdown candidates for the existing confined-source resolver, retaining symlink/confinement and missing-file handling without another ID-shape check. Source-header parsing and the exact front-matter ID comparison belong to this filesystem read boundary. Other source-domain validity remains with authoring/import owners. There is no server display sort, generated report snapshot, Index lookup, cache or background refresh.

The browser consumes completed service rows without repeating envelope/schema/stage, identity, uniqueness or title-type audits; the report service retains HTTP/JSON and success-envelope handling. One browser sort per load places available titles first in numeric-aware, case-insensitive ascending order, then exact document ID; unavailable titles follow. Literal labels use `textContent`; each row's existing exact local document URL is shared by its Title and Document ID cells. Opening and Refresh show no loading message; controls remain busy until completion, and count, empty and failure messages remain explicit. Refresh clears prior rows before reading and reports failure visibly, preserving the existing empty/error semantics.

One busy state serializes Refresh and Open in VS Code. Register retained-view disposal before the initial read and use disposal alone to reject late success/error and further actions. A detached retained report remains valid and can complete while another document is displayed; returning with Back keeps that completed view and enabled controls. No request versions, DOM-connection/current-document gates, abort/retry owner or extra subscription is needed.

The bounded work is one policy read, one confined header read per listed existing source and one browser sort per opening/Refresh. Open in VS Code is a separate exact-file action and does not read or validate the policy content. On 2026-10-14, focused Python/JavaScript lint and Python compilation passed. A read-only production invocation built the current 14 report rows with no missing sources and fed them directly to `readUnpublishableDocuments`, yielding title order from Broken Links to Work Links. The existing `open_publication_ignore(..., dry_run=True)` action returned the VS Code receipt without launching an editor. These diagnostics exercise real policy/header reads, module wiring and display sorting, with no synthetic inputs, assertions or test code; they do not prove HTTP/DOM behavior or editor launch. [Unpublishable Optimisation](deliveries/Unpublishable_Optimisation.md) records review and manual acceptance. Tests, fixtures, harnesses and profiles remain unchanged and unrun.

The distinct Redundancy And Defensive Behavior Review covered fresh/empty/missing-source/error reads, literal titles and stable sorting, Refresh clearing, editor success/failure, immediate disposal and detached retained completion. It also traced the shared policy/parser/confinement, report-service, controller and editor helpers. Review removed the duplicate ID-shape check by supplying policy-validated IDs directly to the existing confined-source resolver; affected lint, compilation and current-data composition passed again. Necessary boundary safeguards remain shared policy parsing/ID validation, source confinement/symlink rejection, header syntax and exact source identity, HTTP/JSON/success handling, local capability and fixed editor authority. No actionable findings remained. No new audit, source-domain validation, compatibility layer, recovery, cache or background work was introduced. Live HTTP, empty/missing/error rendering, Back/disposal and real editor launch remain manual acceptance limits after service restart and page reload.

## Workflow

1. Open Unpublishable to inspect the explicit publication exclusions.
2. Choose Open in VS Code, edit the actual ignore file and save it.
3. Refresh the report to read the saved list.
4. For a document-level temporary eligibility change, toggle that document's `draft` state.
5. If anything consequential changes, run a full refresh manually. Refreshing the Unpublishable report itself only rereads the ignore file and its listed source titles.
6. Run Pre-publish when ready to prepare the new selected set. Review it, then use the ordinary Publish and deployment actions.

## Implementation Rules

- Do not invent problems that do not need solving.
- Fail cleanly on errors.
- Do not touch anything not directly connected to this delivery.
- Do not invent things.

The agreed scope is implemented, and directly affected durable guidance describes the shipped behavior.

## Accepted Result

The user accepted the completed result and authorised closeout on 2026-09-13, after the Title column, A–Z ordering and one-off Working Links backfill. No implementation or acceptance gate remains. The user's testing direction is retained: affected tests omit report-description, menu-label, status-message and rendered-cell copy assertions; data, identity and service/module boundary checks remain.

The 16-ID ignore file, strict shared reader, separate draft subtree exclusions, Unpublishable Refresh/Open in VS Code actions, Working link reads and coordinated `publishable`/report `access` retirement are implemented. Publish retains index shape, collection identity and media validation while accepting the complete prepared set. Directly affected durable guidance has been updated.

The requested Title column is implemented alongside Document ID, with both linking to the exact Working document. The table sorts by Title A–Z, ignoring case. Focused verification passed: 15 Python service checks, the JavaScript data/request contract, changed-source lint and whitespace checks. These checks cover title data and identity handling, without UI copy assertions.

Verification: 658 Python checks passed across 44 affected test files; eight older fixture failures remain and were independently reproduced against unchanged HEAD. They concern source-based Catalogue fixtures, an unseeded Links fixture, an old external workspace path, a child-import validation expectation and four unconfigured report-service fixtures. No new failing case remains in the affected run. Changed production lint passed for 42 Python and 19 JavaScript files; five focused JavaScript contract checks, tracked runtime projection verification, site validation and whitespace checks passed. UI design was not tested automatically.

Generated document payloads were reconciled across all 15 configured collections with registered media producers skipped. Inspection of 2,081 generated document JSON files found no `publishable` keys or per-report `access`. Working Build recorded 222 warnings about existing missing Links records; the existing skip behavior was retained. The live read-only Pre-publish preview selects 314 documents (ordinary 4, Works 3, Concepts 250, Processing 0, Moments 57). Search, Pre-publish application, Published snapshots, deployment, Git commit and push were not run.

The user subsequently approved a one-off backfill and complete Working Links refresh. On 2026-09-13 this created the 221 missing records (220 Works and one ordinary document), updated four existing records and removed four obsolete ordinary records now on the ignore list. All 588 eligible documents now have Links records, including 251 drafts. The refreshed aggregate contains 20 documents, with 18 directed relationships and 20 occurrences. Exact ownership, schema/counts, reciprocal relationships, aggregate agreement and unchanged source/ordinary generated payloads were verified. The normal Links refresh then ran in dry-run mode across all five Working collections with zero warnings and zero proposed writes or removals. The earlier missing-record warnings are resolved; routine Build creation rules are unchanged. Preview, result and normal-refresh evidence are retained under `var/verification/publication-ignore-list/working-links-backfill-*.json`.

The ignored handoff `var/handovers/publication-ignore-list-20260913.md` and evidence under `var/verification/publication-ignore-list/` retain commands, exact baseline failures, generated diagnostics and accepted outcomes. Closeout reuses that completed evidence; its only verification is source review and confirmation of watcher-generated status updates.

- [x] Readiness: confirm the existing source, Pre-publish, Publish, Deploy, report and link owners; approve the initial 16 IDs and preserve draft descendant/host exclusion.
- [x] Implement the shared configured ignore-file reader and coordinated retirement of `publishable` and report `access`, including directly affected source and runtime consumers.
- [x] Verify changed selection, parser, report and link contracts using focused service/generator checks; inspect required public runtime projections and record existing test exceptions.
- [x] Review the bounded code, tests, config, source and generated changes; resolve findings with only affected checks repeated.
- [x] Update directly affected durable guidance and present the result for manual review.
- [x] Acceptance: the user accepted the delivered result, including the requested Title/A–Z follow-ups and completed Links backfill, and authorised closeout.
- [x] Closeout: mark this delivery done, update the parent outcome, identify durable owners and retain the delivery for manual archive.

Publication snapshots change only through separately requested Pre-publish, Publish and deployment actions. Git commit and push remain separate actions. The eight independently reproduced baseline fixture failures remain known maintenance issues; they are not new failures or unfinished work in this delivery.

## Closeout And Retention

| Material | Outcome and durable destination |
| --- | --- |
| Publication Ignore List | Complete; retain for manual archive. Publication policy and lifecycle live in [Analysis Documents](Analysis_Documents.md) and [Builder](Builder.md). The reader, title ordering and local edit workflow remain owned by the report runtime and described in [Reports](Reports.md). |
| Unified Analysis And Catalogue Presentation | Retain as the active parent for other outcomes; its Publication Ignore List entry records this accepted completion. |
| Local handoff and verification artifacts | Retain as ignored delivery evidence. Stable Links creation/backfill conclusions are recorded in Builder; test-policy conclusions are recorded in Development Checklist and Test Contract Discipline. |

No separate concept, proposed architecture or verification document was created beneath this delivery. No document was deleted or archived automatically.

### Verification Budget

| Contract or credible risk | Lowest adequate evidence | Permanent test change? | Why needed |
| --- | --- | --- | --- |
| Exact ignore-file reads, ordinary ownership, errors and fresh report/link requests | Focused Python service and links-builder tests | Update affected tests; add focused reader cases | Prevent fallback reads, sub-scope exclusions and stale/invalid lists. |
| Draft descendant/host exclusion and one prepared publication set | Focused Pre-publish, Publish and Deploy tests | Update affected tests | Preserve draft behavior and remove downstream eligibility decisions. |
| Report declarations and environment-owned availability | Parser/generator tests and existing JavaScript contract checks | Update affected tests | Remove access fields while preserving configured host and public loader boundaries. |
| Retired field consumers in authoring/packages and tracked runtime projection | Focused existing contract checks, changed-source lint, site-code-update check and site validation | Update only affected contracts | Detect remaining field dependencies and missing shared/public assets. |

Manual UI review remains with the user; no browser-suite expansion or Search rebuild is part of ordinary source-edit follow-through.

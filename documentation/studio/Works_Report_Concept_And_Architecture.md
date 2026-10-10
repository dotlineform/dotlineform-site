---
draft: false
doc_id: d-20260810-115737-741620
title: Works Report Concept And Architecture
added_date: "2026-08-10 11:57:37"
last_updated: "2026-10-10 21:39:15"
summary: Refresh-owned Series membership and generated Context documents supply local Work Document Coverage.
parent_id: d-20260424-000000-50b63f
---
# Works Report Concept And Architecture

## Purpose

Work Document Coverage (`works`) answers one bounded question: which refreshed Catalogue Series have no Context document about a member Work? Each row represents one Series. The Series column remains plain text and the Docs column retains exact document links.

The report respects Studio's Refresh boundary. Catalogue Save changes canonical authoring data and queues its effects; only Refresh advances this report's generated Catalogue input. Context documents retain their separate Save/Build boundary. The report observes these two generated inputs and never reads canonical Catalogue records.

| report | row authority | question answered |
| --- | --- | --- |
| Projects (`project_state`) | immediate physical project folders | Which folders need organising or associating with Catalogue Works and Context documents? |
| Work Document Coverage (`works`) | private refreshed Series/member-Work manifest | Which Series have no member-Work documentation? |

## Ownership And Flow

```mermaid
flowchart LR
    accTitle: Works report ownership and coverage flow
    accDescr: Studio Refresh writes a private Series membership manifest. The report joins it with the separately generated Context management manifest and renders local Series documentation coverage.

    canonical["Canonical Catalogue source<br/>Work.series_id"]
    refresh["Refresh Catalogue"]
    catalogueManifest["Private coverage manifest<br/>Series IDs, titles and Work IDs"]
    docsBuild["Context Save / Build"]
    projects["Working Context Manage manifest<br/>title, target and subject"]
    browser["Works browser module<br/>join, sort and render"]
    report["Works report<br/>Series | Docs"]
    canonical --> refresh --> catalogueManifest --> browser
    docsBuild --> projects --> browser
    browser --> report
```

Canonical Catalogue JSON owns Series definitions and Work-to-Series membership. Refresh projects those facts into `working/generated/catalogue/reports/work-document-coverage/manifest.json`, relative to the configured Docs workspace. Context front matter owns document Subjects, and its generated management manifest carries each document's optional scalar `subject`, title and exact identity.

The coverage manifest is private Working output, excluded from the public artifact inventory and publication queue. It has no public consumer. The report does not use public file presence to establish or suppress a row.

## Coverage Rule

For one refreshed Series `S`, the report derives:

```text
Docs(S) = exact Work-subject Context documents whose subject
          is one of S.work_ids in the saved coverage manifest
```

The result is deduplicated by exact `{collection: "works", doc_id}` identity. A Series is undocumented exactly when `Docs(S)` is empty.

One matching Work-subject document supplies coverage for the Series row. The browser does not diagnose the other member Work IDs, calculate per-Work gaps or require every member Work to have documentation. Folder and None subjects contribute no coverage. Direct Series subjects are rejected by the shared subject reader, rather than retained as another association path. Draft Context documents still count in this local report.

Only saved manifest Series establish rows, including Series with no Works. Unknown Work subjects and Works with no Series contribute no coverage. Documents never invent a Series.

## Exact Browser Inputs

The browser loads two local generated projections:

- the private coverage manifest through parameter-free `GET /docs/work-document-coverage`, using `catalogue_work_document_coverage_v1`; and
- the configured private Working `works` management manifest, containing current document identity, title, date, optional draft/thumbnail flags and optional scalar `subject`, with `working_works` identity and `subject_generation`.

The coverage manifest has a header containing only `schema` and `generated_at_utc`, followed by a `series` array. Each Series contains exactly `series_id`, `title` and ascending distinct `work_ids`. Series are ordered by exact ID, every defined Series is included, and a Work belongs to at most one Series. No Work title, year, Gallery, media, revision, count or content-version fields are persisted.

The saved-file reader validates this minimal schema and membership identities within Working storage. The browser validates the Catalogue schema and the IDs, labels and memberships it consumes; it does not validate unused Studio editor fields. Context manifest validation retains its existing owner. Docs Viewer serves the saved coverage file without consulting canonical records, generating output, or requiring Local Studio to be running. Missing or invalid data asks for [explicit coverage maintenance](#coverage-maintenance); there is no canonical or public fallback.

## Refresh Selection

Work creation/deletion and Series reassignment, plus Series creation/rename/deletion, select the manifest in the existing v5 updates queue's `shared_outputs`. Every canonical Work requires one Series; empty Series definitions remain valid. Work mutations capture both former and new Series endpoints before persistence/removal. Year, Work title, image and Gallery-only edits do not select this file. Existing mutation owners supply these known effects; Refresh does not rediscover them.

When selected, Refresh reads/validates the saved manifest once and keys its Series rows and existing Work membership in that same pass. It updates only queued current Series definitions, removes explicit deleted Series and merges metadata-selected queued current Works plus every queued Work deletion. Candidates include already-refreshed Works until shared completion. For each candidate, the saved membership supplies its former Series and the loaded current Work supplies its final Series; a changed membership requires its former/new endpoints to be queued. Refresh removes that candidate from the former row and inserts it into the final row without scanning canonical Works for complete member lists. New Series start with empty membership plus their queued assignments. A rename preserves members, removal of the last Work retains an empty Series row, and unrelated saved rows retain their values without canonical joins.

Only changed selected row values/removals produce an ordered complete JSON write. Unchanged candidates preserve bytes and generation time. A Series-definition-only coverage selection needs Series but no canonical Works, unless another selected output requires them. Saved-file parsing/validation, selected member-list ordering and changed-file serialization remain costs proportional to their inputs. Normal Refresh trusts Save-owned canonical checks and excludes coverage from full generation. Missing/invalid saved input fails after required Work handoffs and retains shared selections; there is no full-projection fallback. The completed-shared handoff excludes this private file from public selection, then removes its updates selection. Refresh retains completed effects on failure for diagnosis and an explicit rerun.

The 2026-10-10 cutover queued only this manifest from empty queues and ran Refresh, writing one file at `2026-10-10T17:25:07Z`; publication selection remained empty. Ordinary sources, documents, media and Search were not regenerated.

## Coverage Maintenance

Complete baseline generation or repair of missing/invalid saved coverage is explicit:

```bash
python3 studio/services/catalogue/catalogue_json_build.py --write --work-document-coverage
```

This validates the existing updates queue and complete canonical Work/Series inputs, then projects only the private coverage manifest using the same Series row builder as merging. All queued current/deleted Works must already be refreshed; normal Refresh attempts coverage merging after their handoffs, so a coverage-file failure leaves this prerequisite reachable. The command clears only the coverage output selector after success, preserving Work candidates/readiness, shared Series/Gallery endpoints, unrelated selectors, both lifecycle times and the entire publication queue. It performs no media handoff/production, document/Search build or Publish. Failure retains completed effects and unconsumed selection for diagnosis and explicit retry. Readers and ordinary Refresh never invoke maintenance automatically.

## Subject Composition

The browser accepts Work, Folder and None subject records from the shared reader. Only an exact Work present in saved Series membership contributes a document. Invalid or retired subject data fails manifest validation; unknown Work targets, missing Series membership, Folder and None supply no coverage.

Document presentation contains the exact Working Works target, current manifest title, existing Manage URL and declared Work subject `{kind, key}`. The shared Work subject icon describes the document's declaration; it is not an inferred coverage or publication state.

## Browser Composition And Failure

On mount, the browser fetches both complete generated inputs, performs the exact in-memory join and renders one complete result. Each row contains:

- exact Series identity and its current plain-text title; and
- zero or more exact linked Context documents with current title and declared Work subject.

Rows sort by normalized Series title and exact `series_id`. Documents sort by normalized title, exact subject kind/key, and `doc_id`. Identity, label, and activation target remain distinct. Opening/reloading the report reads saved inputs; retained mounts keep their Catalogue input until reloaded. Existing committed Context document changes update that mount's document side and recompose coverage against the same saved Catalogue membership.

The final document-coverage rows remain ephemeral browser state; only Catalogue membership is persisted. The endpoint reads the saved file and does not perform the document join. If either required input is unavailable or invalid, the current mount shows one contained error and no partial or older rows.

## Embedded Local Report

One ordinary human-authored document declares the focused local report. The existing report registry and browser loader mount it. `docs-viewer-report-service.js` supplies the read-only saved-manifest request; the endpoint and report remain management-only and absent from the public runtime inventory.

The table is:

| Series | Docs |
| --- | --- |
| one exact plain-text refreshed Series title | zero or more exact Context document links with Work subject cues |

Blank Docs cells remain visible and identify Series without member-Work documentation. Series titles have no navigation control. Document links use `?collection=works&doc=<doc-id>` through the existing exact-document reader.

The report does not add grouping, per-Work coverage, coverage percentages, automatic exception labels, arbitrary filters or public display. Search, sorting controls and clipboard transforms require an explicit later product decision.

## Relationship To Existing Owners

Compact Work/Gallery indexes and full Work by-ID data retain their own consumers. Coverage uses its dedicated private Catalogue manifest and the existing Context manifest. Context's separately retired `reports/works/manifest.json` title lookup is not recreated. Projects and other canonical inspection reports retain their existing boundaries; changing them is a separate outcome.

## Verification And Limits

Changed-source Python/JavaScript lint and Python syntax passed. The production GET dispatcher read the newly generated manifest, and the existing browser normalization/composition functions accepted 140 Series, 4,619 member Works and 235 Context documents, producing 140 rows, 20 with coverage. This is current-data diagnostic evidence; browser transport/presentation, committed-document subscriptions, empty Series, mutation execution and partial failures were not exercised. Restart Local Studio and Docs Viewer services and force-reload Docs Viewer to adopt the changed owners; no Publish is required.

The subsequent 2026-10-10 row-merging slice passed lint/syntax for its five changed Python modules, CLI help/import startup and whitespace checks. Read-only real-data projection through the shared full builder matched the saved v1 manifest: 140 Series and 4,619 member Works, with no empty Series in this data. The production saved reader accepted it; both queues were empty and lifecycle times were preserved. No schema conversion or generated-output write was needed. Bounded code review covered queued creation/reassignment/deletion, empty Series, definition-only rename, reused identities, final-value no-ops, readiness-independent retries, exact endpoint agreement, single saved read/direct changed write, maintenance ordering and private/public ownership. These mutation/no-op/failure paths, the maintenance write command and HTTP/browser behavior were not executed; tests were neither created, changed nor run. Restart Local Studio and Docs Viewer services to adopt the shared Python validator and changed handoff. No public projection or Publish is required.

The existing `docs-viewer/tests/python/test_works_report_contract.py` still asserts former live lookup inputs and retired scope/target plumbing. It is unreviewed for the current report boundary and was neither changed nor run. Test work requires separate approval under [Testing](Testing.md).

## Not In Scope

- one row per Work or identification of undocumented member Work IDs;
- treating the absence of one Work document as a gap when another member-Work document covers the Series;
- Folder-subject placement, physical directory scanning, Finder activation, or Project State changes;
- semantic-token mentions, content scans, title matching, or relationship expansion beyond exact current Work membership;
- `analysis/works` editorial documents, lineage stage, `publishable`, public document locations, or public Catalogue presentation;
- public Catalogue JSON as publication authority or a report input, and projection-integrity auditing;
- a server-side document-coverage join, saved final report rows or a public manifest;
- a new canonical association store, generic graph/query layer or compatibility reader;
- mutation, repair, assignment, Copy, Publish, Delete, or automatic refresh hooks; or
- changing canonical Work, Series, Subject, collection or public-route contracts.

---
draft: false
doc_id: d-20261013-210028-8b3c2f
title: Docs Viewer App Roadmap
added_date: "2026-10-13 21:00:28"
last_updated: "2026-11-18"
summary: Proposed capability releases for a standalone Mac and iPad Docs Viewer, aligning with the existing apps one capability at a time and progressing towards local management.
ui_status: proposed
parent_id: d-20261118-235100-64ad2e
---
# Docs Viewer App Roadmap

## Status And Current Baseline

Proposed Mac/iPad Docs Viewer capabilities under [Planned Features](README.md). This roadmap approves no implementation, release scope or test work. DVA.R1 is the next candidate; later rows may be reordered or split.

The maintained native app has a SwiftUI entry that opens [AboutView](../../app/dotlineform/Features/About/AboutView.swift), a bundled About page and an About-specific [WebKit message/reply host](../../app/dotlineform/WebKit/WebKitHost.swift). The App-owned cloud operation is separate. Current source does not install Docs Viewer resources, a Docs workspace reader or native document management. [App README](../../app/README.md) and [App instructions](../../app/AGENTS.md) own build, signing and Mac/iPad review.

The web reader/provider and local HTTP/Python operations are implemented. Its single Working/Preview model, exact ordinary/collection identities and completed publication effects are the behaviour reference, not a native implementation. [Runtime](../reference/Docs_Viewer_Runtime.md) · [Source organisation](../reference/Source_Organisation.md) · [Generated contracts](../reference/Generated_Data_Contracts.md)

## Agreed Direction

Core Docs reading and supported local management run in the app without a local HTTP server, Python process, repository checkout or remote compute. Deliberate remote-content access and a later selected publication destination retain their own network boundary. Reuse appropriate reader JavaScript; Swift owns the native shell, authorized access and required native execution. This is not a requirement to rewrite every interaction in SwiftUI.

Bundle selected canonical resources through one owned build boundary and record the accepted resource revision. Keep loaded-state choices and interaction in the frontend; supply narrow native operations rather than recreating HTTP routing or a general filesystem framework. Missing access or unsupported inputs disable/stop their operation visibly, with no manufactured workspace or hidden server fallback.

Studio keeps Catalogue authoring and Refresh. Native reading may consume completed Catalogue data, but a native Catalogue editor or Studio/Docs merger is outside this roadmap. Separate metadata discovery, selected preparation, rendering, persistence and transfer only as the next actual capability needs them. Carry resolved inputs/effects; reused builders/context loaders must not conceal unrelated corpus work. [Design rationale](../design/Native_Reader_Capabilities.md)

## Capability Releases

These are capability labels, not bundle versions or App Store/TestFlight/distribution commitments. One release is active at a time; create its bounded deliveries only when ready.

| Release | Proposed complete outcome |
| --- | --- |
| DVA.R1 | Read ordinary generated documents: explicitly authorized workspace, ordinary Index and exact navigation through bundled reader resources on Mac/iPad. Declare supported content and limitations; no source writes or generation. |
| DVA.R2 | Display one agreed Docs-owned media family, initially images, through the native resource/access owner. Other families and Catalogue/Projects media require their own additions. |
| DVA.R3 | Read one chosen named collection with exact host/collection/document identities, saved metadata and required presentation. Other collections remain separate additions. |
| DVA.R4 | Search saved data for supported targets through the existing format/provider seam. Declare treatment of unsupported results; no Search generation or freshness scan. |
| DVA.R5 | Inspect an ordinary document's exact saved source with authorized reads and captured identity, without Save or generation capability. |
| DVA.R6 | Complete one mutation independent of body rendering, such as Star/Unstar, including persistence and required prepared/publication effects. Projection/queue prerequisites belong here rather than blocking the earlier reader. |
| DVA.R7 | Rebuild one supported ordinary source locally through an agreed parser/rendering strategy, exact document/Links output, publication handoff and fresh display. Bound tokens/reports; preserve source bytes/dates; no Python or implicit full build. |
| DVA.R8 | Save a supported Source edit using that preparation owner, completing source persistence, generation and handoff with phase-specific reporting. Persisted source alone is not a complete Save. |

Saved Recent/Selected, more media/collections, New/Draft/Position/Delete, Subject authoring, media intake, import/export/packages, Search/full generation and publication remain later candidates. Each needs its own complete boundary; they are not a catch-all management phase. Small native presentation refinements may extend an accepted capability.

Native preparation must explicitly own Markdown/front matter, tokens/reports, Links, dates, media references and public projection for its supported inputs. Choose Swift or portable JavaScript by responsibility; current Python is the behaviour reference. A later management release must agree queue ownership, access and destinations. Git and public deployment stay separate. [Publish preparation](../reference/Builder.md#publish-preparation)

## Release Alignment And Acceptance

At release start, agree supported document/collection/media cases and reference their current behaviour owners/repository revision. Acceptance records the exact resource revision, working cases, platform limits and next addition. Pin that selected capability rather than freezing the whole website or copying a corpus.

Web additions outside the active capability wait. Defects in supported behaviour receive bounded corrections. A required data/behaviour change that invalidates the baseline needs an explicit rescope, prerequisite or deferral decision. Do not conceal divergence with aliases, normalization or duplicated domain rules; the app's bundled capabilities govern availability, without a new runtime version handshake or audit framework.

Only refactor a web seam used by the selected native path. Keep website behaviour usable and remove demonstrated hidden work/duplicated decisions. [Development Workflow](../development/Development_Workflow.md) and the [Redundancy Review](../development/Development_Checklist.md#redundancy-and-defensive-behavior-review) own method, including reused native bridge/execution helpers and necessary access, confinement, parsing, escaping and transfer checks.

Use current App instructions and separately agreed test/live-write scope. A build or bridge success does not establish document capability. Acceptance may accumulate through agreed normal use, with unexercised cases visible; Mac and physical-iPad presentation remain manual. A completed release remains useful if later work pauses and is not reopened merely because the website adds features.

## Historical Ideas And Next Decision

Earlier [App Home](../app/d-20260829-212459-c17eb8.md), [Roadmap](../app/d-20260902-143007-05a794.md), [v0.2 Single Scope](../app/d-20260903-183129-18e663.md) and [v0.3 Scope Selection](../app/d-20260903-183219-aa278b.md) retain ideas/evidence. Their Published/scope storage, versions and unfinished checklists do not define this capability. Leave those records/identities intact until separately reviewed; reconcile reused ideas and old tests against current owners.

For DVA.R1, the earlier recommendation is read-only access to existing generated Working content. Agree direct authorized access or an explicitly imported app workspace; decide how configuration and media owners reach the app without machine environment/repository assumptions. Then bound ordinary reading cases, resource packaging and Mac/iPad acceptance. Keep readiness read-only and concise; if implementation uncertainty remains, propose a small complete delivery instead of a prototype or general prerequisite refactor.

---
draft: false
doc_id: d-20261013-210028-8b3c2f
title: Docs Viewer App Roadmap
added_date: "2026-10-13 21:00:28"
last_updated: "2026-10-13 21:00:28"
summary: Proposed capability releases for a standalone Mac and iPad Docs Viewer, aligning with the existing apps one capability at a time and progressing towards local management.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Docs Viewer App Roadmap

## Purpose And Status

Develop a standalone Docs Viewer within the existing Swift Mac and iPad app, first as a useful reader and ultimately with local management capabilities. Preserve the established document model and interaction design, align one capability at a time, and improve the existing implementation only where the next capability needs a clearer boundary. A large prerequisite refactor is not realistic or required.

This is the proposed feature and release-roadmap entry point under [Planned Features](Planned_Features.md). The user has requested this approach and roadmap; no native implementation, release scope or new test work is approved by this document. Only the next bounded capability is made ready for implementation. Later releases describe direction and can be reordered or split before approval.

The existing browser apps remain in normal development. Their design is close to the intended result and is expected to improve through additions and local refinements. They do not need a new coordinated release programme or integration of Studio with Docs Viewer. The Swift app needs explicit capability releases so it can align with a known behavior baseline instead of continually chasing both apps' latest changes.

## Current Starting Point

[App README](../../app/README.md) and [App instructions](../../app/AGENTS.md) own the current native project: one Swift 6 target for native Mac and iPad, a SwiftUI shell and a WebKit host for bundled content with a typed message/reply boundary. The host currently supports the About feature; Docs Viewer integration and native workspace access are not implemented. The existing App-owned cloud workload is independent and does not establish a requirement to use cloud Python for Docs Viewer.

Docs Viewer has canonical reader JavaScript/styles, separate compositions and an injectable collection-provider seam, described in [Runtime Architecture](Docs_Viewer_Runtime.md). Its public reader consumes generated assets independently of local management services. Current management still calls HTTP/Python operations. Reusing that management composition unchanged would carry those dependencies into the app.

Current Docs storage is the single configured Working source/generated workspace and read-only Preview publication artifact. Ordinary and named-collection targets retain exact identities. Older scope/sub-scope selectors, local Published storage and Preview browsing are retired. [Source Organisation](Source_Organisation.md) and [Generated Data Contracts](Generated_Data_Contracts.md) describe the current owners; inspect the selected capability's code/configuration when preparing its release.

## Direction And Boundaries

- Core Docs reading and implemented local management must run within the app without a local HTTP server, Python process, repository checkout or remote compute service. Network access for remote content or a later explicitly selected publication destination retains its own capability boundary.
- Reuse the established reader and appropriate JavaScript interaction owners. Swift owns the native shell, authorized workspace access and required native execution. A Swift app can retain WebKit presentation without requiring every control or domain rule to be rewritten in SwiftUI.
- Bundle selected canonical resources through an explicit owned build boundary. Do not maintain a manual second copy of the Docs Viewer runtime or load changing repository files at application launch. Each accepted app release contains a known resource revision.
- Keep browser-owned choices and loaded-state validation with the frontend. Supply narrow document operations through a browser HTTP adapter or a native typed bridge; keep transport mechanics out of ordinary interaction logic. Do not recreate HTTP routing inside the app merely to preserve endpoint-shaped callers.
- Separate metadata discovery, selected preparation, rendering, persistence and transfer when the current capability needs that seam. Carry resolved inputs and completed effects forward. Reused full builders, context loaders, constructors and default-input branches must not silently add unrelated loading, rendering or audits.
- Preserve Studio's Catalogue authoring and Refresh ownership. The app may consume their completed generated data as a reading capability is added; this roadmap does not absorb Studio editing into Docs Viewer or approve a native Catalogue editor.
- Implement complete supported operations and expose only their declared capabilities. Missing access or unsupported input stops or disables the relevant operation visibly; it does not select a fallback workspace, invoke a hidden server or imply support for an unimplemented workflow.

Apple's [message/reply bridge](https://developer.apple.com/documentation/webkit/wkscriptmessagehandlerwithreply) and [custom resource handler](https://developer.apple.com/documentation/webkit/wkurlschemehandler) provide mechanisms for app-owned operations and resources. Select the smallest mechanism needed by the actual first reader path. These mechanisms do not require a generic filesystem/network abstraction or a new platform framework.

Workspace selection is an early product decision. The initial recommendation is read-only access to existing Working generated content beneath an explicitly authorized workspace, with source access added for later management. Resolve how its configuration and media owners are supplied without environment-variable or repository-path assumptions. On iPad, [directory access](https://developer.apple.com/documentation/uikit/providing-access-to-directories) involves a user-selected directory and scoped access. Choose direct shared-workspace access or an explicitly imported app workspace before implementation; do not silently manufacture a replacement root or revive old Published/scope storage.

## Historical Documents

Earlier App documents are sources of ideas and recorded evidence, not the current native Docs Viewer specification. Their titles, old version numbers and completed checkpoints do not authorize new work or prove that the proposed reader exists. Reconcile any reused idea with current code, storage, ownership and the capability being delivered. Current project/build instructions remain authoritative at their maintained owners.

- [App Home](../app/d-20260829-212459-c17eb8.md) retains the useful shared-reader/native-host direction, but its older summary and routing do not establish today's content or release boundary.
- [Earlier Roadmap](../app/d-20260902-143007-05a794.md) contains planning guidance; current [Planned Features](Planned_Features.md), [Development Workflow](Development_Workflow.md) and [Development Checklist](Development_Checklist.md) own this roadmap's delivery method.
- [v0.2 — Single Scope](../app/d-20260903-183129-18e663.md) contains useful narrow-adapter and canonical-resource ideas alongside superseded Published/scope/sub-scope assumptions and validation expectations. Retain the ideas only after explicit reconciliation; do not implement that proposal wholesale.
- [v0.3 — Scope Selection](../app/d-20260903-183219-aa278b.md) contains relevant permission/access ideas, while its selected Published-scope model is obsolete for this proposal.

Leave those documents and their identities intact unless their update or retirement is separately requested. New capability deliveries route from this document and state any historical idea deliberately adopted. They do not reopen every historical feature or inherit its unfinished checklist. Old test specifications likewise require review against the new capability before reuse.

## Release Model And Alignment

A Docs Viewer App release is an accepted, versioned capability baseline for the current Mac/iPad development app. It does not imply App Store, TestFlight, notarization or other distribution work. `DVA.R1`, `DVA.R2` and subsequent labels identify this roadmap's capability releases; they are not replacements for historical App version numbers or a decision about bundle versioning.

Keep one capability release active at a time. Its small deliveries may establish a necessary boundary before completing the user-facing capability, but each delivery must have a finishable result. Create only the current release's delivery documents when their scope is ready; do not pre-create a large refactor programme or detailed plans for every future release. A release that becomes too broad is split before further work proceeds.

At the start of a release, agree its supported document/collection/media cases and reference the current behavior owners and relevant repository revision. Pin this selected capability baseline for the release; do not freeze the whole website or copy a corpus as an implementation prerequisite. Record the exact runtime/resource revision when the release is accepted. Later web additions remain candidates for a later app release rather than automatically expanding the active one.

Classify a relevant web change proportionately: a compatible change outside the active capability waits; a bug affecting supported behavior receives a bounded fix; a required data/behavior change that invalidates the active baseline requires an explicit rescope, prerequisite or deferral decision. Do not resolve divergence by adding compatibility aliases, silent normalization, duplicate domain rules or another reconciliation pass.

Keep a compact support/alignment record for each accepted capability: what works, the referenced behavior/resource revision, platform-specific limitations and the next intended addition. This is development/release bookkeeping, not a runtime version handshake, corpus audit or new compatibility system. The app's actual bundled capabilities govern availability.

## Proposed Capability Releases

The sequence below is a candidate order, with no dates or implementation commitments. Each row is one capability outcome, not a promise of complete parity with the web apps. If a row still requires too much work, narrow its supported cases or split its independently useful outcomes before approval.

| Release | Capability outcome | Alignment and boundary |
| --- | --- | --- |
| DVA.R1 | Read ordinary generated documents in the standalone app. | Open one explicitly authorized content workspace, load its ordinary Index and open/navigate exact document targets through bundled reader resources on Mac and iPad. Define supported content cases and visible limitations. No source writes, generation or local server. |
| DVA.R2 | Display one agreed Docs-owned media family, initially images. | Resolve referenced identities through the native resource owner with declared access. Additional families and separately owned Catalogue/Projects media require their own scoped additions; do not inventory unrelated media. |
| DVA.R3 | Read one chosen named collection. | Align its exact host/collection/document identities, saved metadata and required presentation/data reads. Other collections are separate capability additions, not automatically enabled. |
| DVA.R4 | Search saved data for supported reading targets. | Consume the existing saved Search format through the reader/provider boundary. Declare treatment of results outside the app's supported targets. Do not add Search generation or freshness scans. |
| DVA.R5 | Inspect an ordinary document's saved source. | Add authorized exact source reads and captured-target presentation, with no Save affordance or implied generation capability. |
| DVA.R6 | Complete one management mutation independent of body rendering. | Choose an action such as Star/Unstar only after its persistence and required prepared/publication effects can complete locally. Preserve dates and report actual effects. Selected projection/queue requirements can be a prerequisite for this release without blocking the earlier reader. |
| DVA.R7 | Rebuild one supported ordinary document locally. | Establish the chosen source/parser/rendering strategy and complete exact document/Links generation, required publication handoff and fresh display. Preserve source bytes/dates. Explicitly bound supported tokens/reports; do not invoke Python or broaden to a full build. |
| DVA.R8 | Save a supported ordinary Source edit locally. | Reuse the completed preparation owner, adding source persistence and the existing authoring/completion semantics. Complete generation and required handoff before reporting success. Source persistence alone is not a complete Save capability. |

Saved Recent/Selected presentation, additional media/collections, New, Draft, Position, Delete, Subject authoring, media intake, import/export/package tools, explicit Search/full generation and publication remain later capability candidates. Select and order them by user value and established prerequisites. Each is a separate release or bounded delivery; they are not one catch-all management phase. Native UI refinements can be small additions to an accepted capability without forcing its wholesale replacement.

Native document preparation is a substantive boundary. Markdown/front matter, custom tokens, reports, Links, dates, media references and public projection need an explicit implementation strategy for the declared supported inputs. Choose Swift or reusable portable JavaScript by responsibility; Python's current implementation is a behavior reference, not a reason to embed it in the app. Establish a semantic owner and extension method for each transferred responsibility so web and native implementations do not silently drift.

[Incremental Document Publish](deliveries/Incremental_Document_Publish.md) supplies the proposed completed-artifact/selected-effects boundary for later native generation and publication. It is not a prerequisite for ordinary native reading. A management release that needs its queued handoff waits for that specific owner/contract or agrees a separately scoped prerequisite. Native Publish remains a later capability with explicit destination/access decisions; Git and public deployment retain their separate ownership.

## Retrospective Changes To The Existing Apps

Each native capability selects the smallest existing seam it needs. Keep the website usable throughout and preserve its established behavior. A narrow provider/client extraction can be justified by a real native consumer, while unrelated controllers and services remain with their current owners.

For a selected capability, distinguish the domain operation from its HTTP translation; make required inputs/output/effects explicit; retain loaded-state decisions in the frontend; and remove hidden full-context work encountered on that actual path. Improve cohesion when it removes a demonstrated dependency or duplicated decision. File counts, shorter modules or a generalized service framework are not delivery outcomes.

Review the changed path and reused helpers under the mandatory [Redundancy And Defensive Behavior Review](Development_Checklist.md#redundancy-and-defensive-behavior-review). Include native bridge/native execution code in the same ownership review. Necessary file access, confinement, escaping, parsing and selected output/transfer completion remain at their actual boundaries; porting must not multiply domain validation or maintenance audits.

## Evidence And Acceptance

Use current [App instructions](../../app/AGENTS.md) for native build, signing and Mac/iPad review boundaries. Select proportionate evidence for the changed capability; test creation/migration and live writes require their separately agreed scope. A passing build or a working bridge does not prove document reading or management behavior.

End-to-end confirmation can accumulate through agreed normal use. Accept and record the supported capability and observed outcomes, with unexercised cases visible. Unexpected slowness, unnecessary calls or rejection of valid work triggers focused investigation of that operation. Do not make every app release wait for application-wide regression evidence or add a monitoring/auditing framework to compensate.

An accepted release remains useful if later roadmap work pauses. Later web additions do not retroactively make it unfinished. A demonstrated defect in its supported behavior is handled as a bounded correction, with any material change to the supported baseline recorded.

## Next Release Decision

The next candidate is DVA.R1. Before its implementation is approved, agree the native content/access model, ordinary reading cases, required bundled resource boundary and meaningful Mac/iPad acceptance. Confirm that current App foundation work is adequate for that specific capability rather than automatically carrying forward every earlier App Shell task.

Keep that readiness step read-only and concise. If it exposes implementation uncertainty, propose a small explicit implementation delivery with a concrete outcome instead of requiring a prototype or general refactor before approval. Record the agreed DVA.R1 baseline here and link its delivery once approved; leave later capability releases proposed.

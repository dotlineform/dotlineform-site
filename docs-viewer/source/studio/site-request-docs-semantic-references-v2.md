---
doc_id: site-request-docs-semantic-references-v2
title: Docs Semantic References v2 Request
added_date: 2026-05-27
last_updated: 2026-06-02
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Semantic References v2 Request

Status:

- proposed
- this needs to happen **before** semantic-token insertion in [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)
- the separate [Docs Viewer Markdown Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-markdown-editor) can define source editing/rebuild behavior without waiting for this registry work
- product and maintenance direction now belongs with Analytics
- current v1 implementation still runs through Docs Viewer build/runtime/report code

## Summary

Revisit and extend [Docs Semantic References Request](/docs/?scope=studio&doc=site-request-docs-semantic-references) using the clarified Docs Viewer app/backend and module architecture.

Current v1 behavior is documented in [Semantic References Implementation](/docs/?scope=studio&doc=docs-viewer-semantic-references-implementation).
Use that implementation doc as the stable baseline for this request.
The original v1 request is now historical context, not the current implementation contract.

Since then, the broader Docs Viewer direction has become clearer:

- semantic links are dotlineform/Studio-specific integrations, not portable Docs Viewer core
- Docs Viewer validates supported semantic types and actions, not target-object existence
- target ids are opaque host ids; missing objects can behave like ordinary broken public links
- semantic-reference support needs a concrete registry artifact that defines supported reference types, object ownership, target-data reads, route/surface behavior, and diagnostics
- browser-safe repo/generated data should be read directly by browser modules where practical
- manage-mode authoring tools should be optional modules that can be omitted from portable installs
- panel modules can display relationship data, but host projects must provide that data unless Docs Viewer later defines document-derived data classes

V2 should first review the v1 implementation against those decisions, then define the semantic-reference registry before adding editor or future hosted relationship views.

## Baseline Implementation

The current implementation doc records these baseline facts:

- authored `[[ref:...]]` tokens are parsed from Docs Viewer Markdown source
- the parser, resolver, rendered output, generated artifacts, targeted build behavior, and report runtime are currently Docs Viewer-owned
- Analytics owns the product direction for future semantic-reference maintenance and modules
- there is no semantic-reference registry today; supported kinds, actions, ownership assumptions, route construction, and target-data reads are hard-coded in the builder
- current v1 behavior is catalogue-aware: missing or non-published catalogue targets warn and render as inert spans
- current v1 generated artifacts include `target_status`

V2 starts from that baseline and must make an explicit alignment decision:

- either keep the current catalogue-aware behavior and document it as intentional host validation
- or refactor v1 so allowed semantic types/actions always produce route-derived links, leaving missing target detection to link-health audits and Analytics/editor support data

## Reason

The v1 semantic-reference request was written before the current app-shell, panel-module, and browser-safe read rules were clarified.
Some v1 language and possibly some implementation details imply tighter resolver validation than the current product model needs.

The next work should avoid building on accidental assumptions.
Before adding editor support, target pickers, tag references, graph views, or richer reports, the project should confirm that semantic references now follow the intended boundary:

- type/action validation belongs to Docs Viewer semantic-reference parsing
- object existence belongs to Studio/public site data and ordinary link health
- semantic support reads should stay browser-side when they can read generated repo artifacts
- source writes and rebuilds remain backend responsibilities
- dotlineform-only semantic modules should be optional and absent from portable installs

## Goals

- audit v1 implementation and docs against the clarified semantic-reference model
- refactor v1 only where needed to remove stale assumptions about target-existence validation
- define a concrete semantic-reference registry artifact
- define the browser-readable Studio support data needed by the semantic-reference editor
- keep semantic support reads modular and client-side where they can consume generated/static repo artifacts
- define supported semantic type metadata for editor controls and panel modules
- make object ownership and surfacing explicit per semantic type
- clarify how unsupported semantic types/actions are diagnosed
- preserve existing generated relationship artifacts unless a concrete v2 need requires a schema change
- keep semantic links and editor tooling repo-specific, not portable Docs Viewer core
- prepare for future info-panel/reference views without choosing a graph or visualization library now

## Non-Goals

- no portable generic semantic-link engine
- no downstream host-extension contract in this slice
- no full object-existence validation by Docs Viewer
- no requirement that `work:99999` fail just because no matching work exists
- no public authoring UI
- no new visualization library integration
- no broad rewrite of the docs builder beyond needed alignment/refactoring
- no source editor implementation in this request, except defining the data/support contract it needs

## Clarified Model

Semantic references are host-owned relationship markers.

In this repo:

- Studio owns works, series, moments, tags, and related data
- the public dotlineform site owns the public routes those ids resolve to
- Docs Viewer owns parsing the authored token, rendering a link for allowed semantic types/actions, and emitting relationship artifacts
- Docs Viewer does not own whether a given target id exists

Examples:

- `[[ref:work:00001|work]]` is syntactically valid when `work` is an allowed semantic type
- `[[ref:work:99999|missing work]]` is also syntactically valid, even if it links to a public 404
- `[[ref:work-detail:00001-001|detail]]` is invalid when `work-detail` is not an allowed semantic type

The semantic-reference editor should use generated/browser-safe Studio support data to help authors choose real targets, but that picker assistance is not the same as Docs Viewer treating target existence as a validity rule.

## Semantic Reference Registry

V2 needs a concrete registry artifact.
The registry should be the source of truth for what a semantic reference means in this repo.

The registry should answer:

- what semantic reference types exist
- what object family each type points at
- which app or data domain owns those objects
- which app owns reference maintenance and surfacing
- how a target id is normalized
- how a link href is derived
- whether target existence is validated by the builder, suggested by editor support data, or left to link-health audits
- which browser-safe data source, local API, or generated artifact supplies labels and picker/search options
- where the reference can be surfaced, such as rendered docs links, management reports, Analytics views, source editor controls, or future reference panels
- which actions are allowed for that type
- what diagnostics are produced for unsupported types, unsupported actions, malformed ids, missing support data, or missing target objects

The registry can be JSON, or a generated JSON artifact if some fields must be derived.
It should be browser-readable when it contains only public-safe metadata.
It should not expose protected source data just to make the browser UI convenient.

Possible shape:

```json
{
  "schema": "semantic_reference_registry_v1",
  "types": [
    {
      "type": "work",
      "label": "Work",
      "object_owner": "studio",
      "reference_owner": "analytics",
      "id_policy": "catalogue_work_id",
      "route_helper": "public_work",
      "allowed_actions": ["link"],
      "target_existence_policy": "link_health",
      "target_data": {
        "read_mode": "browser_generated_json",
        "source": "assets/data/works_index.json"
      },
      "surfaces": {
        "rendered_docs_link": true,
        "docs_report": true,
        "source_editor_picker": true,
        "analytics_reference_view": true
      }
    }
  ]
}
```

The exact field names can change during implementation, but the artifact should preserve these boundaries:

- type/action support belongs to the registry
- object ownership is explicit
- target existence policy is explicit
- target support data is explicit
- surfacing is explicit
- portable Docs Viewer can omit this repo-specific registry and therefore omit repo-specific semantic-reference tools

## Proposed Implementation Steps

### 1. Review And Align V1

Tasks:

- inspect the v1 builder parser, resolver, rendered output, generated relationship artifacts, tests, and docs
- identify code or tests that validate object existence rather than semantic type/action support
- identify code or docs that treat semantic links as portable Docs Viewer core
- identify reads that go through local server endpoints only to proxy browser-safe repo artifacts
- decide whether each finding requires code refactor, docs correction, or no action

Acceptance:

- v1 behavior is documented against the clarified model
- any required refactor tasks are listed before editor implementation depends on them
- unsupported semantic types/actions are clearly separated from missing target objects
- no new editor or panel work depends on unresolved v1 ambiguity

### 2. Define Semantic Reference Registry

Tasks:

- define a browser-readable or generated JSON registry shape for supported semantic reference types
- include type id, label, object owner, reference owner, id normalization policy, route helper, allowed actions, target existence policy, support-data source, and surfaces
- define how the registry answers what a semantic reference is and where it can appear
- define how Docs Viewer, Analytics, and editor modules read the registry without hardcoding inline lists
- keep the metadata dotlineform-specific unless a future host-extension contract is created
- decide whether the registry lives as static config, generated config, or a generated support artifact

Acceptance:

- editor, report, Analytics, and panel modules can ask which semantic types are supported without hardcoding inline lists in route code
- object ownership, reference ownership, target-data source, and surfacing policy are explicit for every type
- target existence handling is explicit and no longer inferred from builder implementation details
- unsupported type diagnostics have a single source of truth
- portable installs can omit this registry and therefore omit semantic-link authoring features

### 3. Define Browser-Safe Target Picker Support Data

Tasks:

- identify the smallest browser-readable Studio support data needed for work, series, and moment target picking
- define each support-data source through the semantic-reference registry
- prefer existing generated/static repo artifacts when safe and practical
- avoid adding local server read endpoints for data already available as browser-safe generated JSON/config
- define how labels, ids, and optional search fields are normalized for picker use
- define what happens when picker data is missing or stale

Acceptance:

- source editor can populate target options without server-proxy reads of browser-safe repo data
- target ids remain opaque host ids
- target picker support can assist authors without changing Docs Viewer validity semantics
- picker behavior can be traced back to the registry entry for each semantic type

### 4. Align Diagnostics And Audits

Tasks:

- derive supported type/action diagnostics from the semantic-reference registry
- define diagnostics for unsupported semantic types, unsupported actions, malformed tokens, and generated artifact problems
- define how ordinary broken semantic-link hrefs are handled by existing or future broken-link audits
- update report language so missing targets are link-health issues, not parser validity errors

Acceptance:

- build diagnostics do not imply Docs Viewer validates target existence
- broken-link auditing can still surface missing public targets where useful
- semantic-reference reports distinguish unsupported tokens from normal broken hrefs
- diagnostics are consistent across builder, reports, editor controls, and Analytics consumers because they share the registry

### 5. Prepare Panel/Module Consumers

Tasks:

- define the read helper surface that future info-panel/reference modules can consume
- make helper behavior registry-driven where it depends on type, owner, route, support data, or surface availability
- keep helpers in a clearly identifiable optional module/folder when repo-specific
- do not introduce D3.js, Cytoscape.js, or graph-specific contracts in this slice
- document how a missing semantic module is omitted from portable installs

Acceptance:

- future panel modules can consume generated relationship artifacts through browser-side helpers
- portable Docs Viewer core does not require dotlineform semantic modules
- relationship data remains available for future graph/reference views without prematurely choosing a visualization stack
- panel/module eligibility can be determined from registry surface metadata

## Architecture Notes

### Browser Reads

Semantic support data should prefer direct browser reads from repo-generated/static artifacts.
Use local service reads only for source files, protected data, external workspaces, capability checks, or data that cannot or should not be exposed as browser assets.

### Optional Modules

Repo-specific semantic support should live in clearly identifiable optional modules.
For example:

```text
docs-viewer/runtime/js/modules/semantic-references/
docs-viewer/runtime/js/modules/source-editor/
```

If these modules are absent or disabled, Docs Viewer core should not show their views/actions.

### Portability

Portable Docs Viewer can support optional modules conceptually, but dotlineform semantic links are not portable core.
A future host-extension contract could allow another project to provide equivalent semantic type metadata and target data.
That contract is out of scope for v2.

## Open Questions

- What v1 code currently checks object existence, publication status, or resolver status?
- What is the exact semantic-reference registry file path and schema?
- Which registry fields are static config and which, if any, are generated from source data?
- Should the registry initially include only `work`, `series`, and `moment`, or should it define planned `tag` support as disabled/future metadata?
- Does the generated relationship artifact schema need a small status field change, or can v2 preserve it unchanged?
- What existing generated data is enough for work/series/moment picker support?
- Should tag support be part of v2, or should v2 only make the current work/series/moment model editor-ready?
- Should graph/reference panel planning stay in this request, or get its own later request once data and UI needs are clearer?

## Risks

- v2 could become a generic semantic-link platform instead of a dotlineform integration cleanup
- editor work could depend on stale v1 assumptions if review/refactor is skipped
- target picker assistance could be mistaken for target-existence validation
- new local server reads could be added for data that should remain browser-side
- generated artifact changes could cause unnecessary rebuild churn

Mitigations:

- make review/alignment the first task
- keep target ids opaque to Docs Viewer validity checks
- document semantic support as repo-specific optional modules
- prefer browser reads for browser-safe repo artifacts
- preserve generated schemas unless a concrete consumer requires a change
- keep visualization and graph work out of v2 implementation

## Verification

V2 implementation should add or update focused checks for:

- supported semantic type/action validation
- unsupported semantic type diagnostics
- syntactically valid but missing target ids rendering as normal links
- generated relationship artifact stability after single-doc edits
- browser-side semantic support data normalization
- no service read added for browser-safe repo support data without a documented reason

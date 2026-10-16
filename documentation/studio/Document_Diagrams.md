---
draft: false
doc_id: d-20260719-123719-fb7565
title: Document Diagrams
added_date: "2026-07-19 12:37:19"
last_updated: "2026-10-15"
summary: Author, build, publish, render, inspect, and extend scope-owned Mermaid diagrams in Docs Viewer.
parent_id: d-20260424-000000-50b63f

---
# Document Diagrams

## Purpose

Docs Viewer uses Mermaid for authored architecture and workflow diagrams that benefit from durable, reviewable source. It supports two source contracts:

- canonical `.mmd` plus a same-basename sanitized SVG for reusable or independently managed diagram media;
- one accessible fenced `mermaid` block for a diagram that belongs only to its document.

Studio uses the accessible fenced block as its working default for Mermaid-authored, document-owned diagrams. Choose canonical `.mmd` plus persistent SVG when the diagram needs an independently managed media identity or stable served URL. Finished SVG remains the direct-media option for authored or imported vectors, and imported local documents retain that media contract until an explicitly selected migration chooses a different canonical source.

Canonical Markdown and Working payloads retain Mermaid fences. Managed readers render them in memory. Eligible Working generation prepares the public light/dark SVG pairs and replaces only its public payload copy; queue-only Publish transfers those completed document/media bytes without rendering or source reads.

Finished SVG and Mermaid source share the source editor's **Add image…** action but keep different contracts. A staged `.svg` is already-finished vector media; a staged `.mmd` is retained as canonical source and rendered before its SVG token is returned.

The static-media workflow is shipped for every scope. Fenced Mermaid rendering is available in managed local scopes and in managed Working views of public scopes, including Analysis. Fenced Mermaid public projection is shipped for configured public scopes.

## Dependency And Registration

The feature-local Node package root is `docs-viewer/build/mermaid/`:

- `package.json` pins the direct Mermaid CLI dependency;
- `package-lock.json` is the resolved dependency authority;
- `mermaid-config.json` owns shared renderer settings;
- `node_modules/` is local, ignored installation output.

Install the locked dependency tree from the repository root:

```bash
npm ci --prefix docs-viewer/build/mermaid
```

[Runtime Dependencies](Runtime_Dependencies.md) owns Node package-root policy. [Local Setup Toolchain](Local_Setup_Toolchain.md) owns the supported Node/npm baseline and environment checks.

Registration has two layers:

1. `docs-viewer/build/docs_builder/media_builds.py` allowlists the code-owned `mermaid` producer implemented by `docs-viewer/services/docs_mermaid_media.py`.
2. Each participating scope opts in through reciprocal external build-source and managed-media records in `docs-viewer/config/scopes/docs_scopes.json`.

```json
"media": {
  "build_sources": {
    "mermaid": {
      "producer": "mermaid",
      "publishes_to": "svg"
    }
  }
}
```

The same scope's `media.types.svg` record must declare:

```json
"build_inputs": ["mermaid"]
```

Studio and Analysis configure the standalone Mermaid producer in both Working and Pre-publish. The source is `$DOTLINEFORM_DOCS_BASE_DIR/scopes/<scope>/<stage>/source/media/build-source/mermaid/`; the derived SVG is in that stage's `generated/media/svg/`. Each configured sub-scope has its own corresponding `<stage>/source/sub-scopes/<sub-scope>/media/` and `<stage>/generated/sub-scopes/<sub-scope>/media/` boundary and inherits the producer registration. Scope configuration owns these resolutions.

## Author Workflow

Use Source Editor **Add image…** to select a native accessible `.mmd` file. Intake renders/verifies its source and SVG through the configured owner and inserts a token into the unsaved buffer. Source Save persists the buffer and completes exact generation. Cancelling retains stored media but supplies no unsaved-document publication reference. Original files remain untouched.

Document Info's managed source links open registered persistent sources. The watcher is retired: an external persistent-source edit requires **Rebuild docs and Search**. Source Save and exact Rebuild skip registered media production.

## Repository Workflow

Workspace configuration owns each ordinary/collection boundary. Ordinary persistent sources live under `working/assets/media/workspace/build-source/mermaid/` and ready SVGs under `working/assets/media/workspace/svg/`; collections use `working/assets/media/collections/<id>/`. Do not infer retired scope roots or edit generated SVG by hand.

External Markdown requires exact owning generation. Persistent `.mmd` changes require the explicit full media/docs build described in [Source Organisation](Source_Organisation.md#explicit-external-edit-and-media-rebuilds). Only referenced registered sources are produced. Generation queues completed public references upstream.

## Source And Publication Contract

Persistent diagrams retain their independent `.mmd` identity; fenced diagrams belong to a document/ordinal. The pinned renderer owns sanitization, accessible SVG output and responsive geometry. Persistent media retains its neutral presentation; public fences use the shared light/dark Docs palette.

Eligible generation supplies complete public document/media effects. Publish applies selected bytes/removals through Preview to configured destinations, leaves unselected bytes intact and never regenerates diagrams. Markdown and `.mmd` source stay private. Eligibility belongs upstream; document-media deletion remains manual.

## Code Authority And Extension

- dependency and renderer settings: `docs-viewer/build/mermaid/`
- producer implementation: `docs-viewer/services/docs_mermaid_media.py`
- producer registry and full/targeted invocation: `docs-viewer/build/docs_builder/media_builds.py`
- workspace/media locations: `docs-viewer/config/workspace/docs-workspace.json`
- native author intake: `docs-viewer/services/docs_source_media_service.py`
- rendered source discovery/opening: `docs-viewer/services/docs_diagram_source_service.py`
- explicit persistent-source rebuild: Manage **Rebuild docs and Search**, through `docs-viewer/services/docs_working_rebuild.py`
- public fence identities/source plans: `docs-viewer/services/docs_public_mermaid_projection.py`, with per-document records retained by public preparation
- selected pair renderer/upstream integration: `docs-viewer/services/docs_public_mermaid_producer.py`, `docs_mermaid_preparation.py` and `docs_publication_preparation.py`
- prepared payload/selected publication: `docs-viewer/services/docs_public_mermaid_payload.py`, `docs_selected_publication.py` and `docs_publish.py`
- prepared image theme selection in Manage and Public: `docs-viewer/runtime/js/public/docs-viewer-public-themed-diagrams.js`
- exact diagram target, presentation, and temporary-resource lifecycle: `docs-viewer/runtime/js/shared/docs-viewer-diagram-detail.js`
- historical publication selection: [Mermaid Publication Test Coverage](Mermaid_Publication_Test_Coverage.md); retired snapshot/transaction contracts require separate review before relying on those tests
- external-local browser loading boundary: `docs_viewer_external_inline_mermaid_route.py`
- focused contracts: `docs-viewer/tests/python/test_docs_mermaid_media.py`, `test_docs_staged_media_service.py`, `test_docs_diagram_source_service.py`, with watcher tests now unreviewed retirement residue

To add another build-source type, register one code-owned producer and managed target, add the reciprocal `media.types.<type>.build_inputs` declaration, and test full builds, targeted builds, intake, explicit regeneration, materialisation verification, and reader-runtime exclusion together.

## Examples

- [Configuration And Extension Points](Configuration_And_Extension_Points.md) uses inline Mermaid to demonstrate configuration, executable ownership, generated projection, and runtime capability.
- [Docs Import](Docs_Import.md) uses inline Mermaid to demonstrate document intake, embedded media, source-editor media, publication, source writing, and rebuild boundaries.

## Fenced Document Workflow

Author a fenced `mermaid` block when the diagram belongs to that document. Managed Working rendering retains its existing document-title/ordinal accessibility fallback and warning for missing authored directives. Public preparation retains the authored `accTitle`/`accDescr` requirement at its producing owner.

Eligible Working generation uses the existing source planner and shared theme/renderer/sanitizer owners. Saved per-document source plans let unchanged fences reuse completed SVG pairs; intentional full builds regenerate them. Ineligible documents do not run or validate this public projection. Restoration prepares exact saved sources whose current public form is unavailable.

Public pairs use the Working owner's SVG namespace under `projection-assets/mermaid/<doc-id>--mermaid-<ordinal>/{light,dark}.svg`, preserving exact stable identities. The producer renders complete selected pairs in temporary files, checks SVG accessibility/geometry and verifies stored bytes. It adds no namespace scan, rollback snapshot or persistent Mermaid manifest. Removed references do not delete stored pairs.

Prepared public HTML contains light/dark image URLs and no Mermaid source fence. Its document queue entry includes both variants as SVG references. Publish transfers selected bytes through Preview and compares exact remote size/ETag; neither Publish nor the public reader invokes Mermaid. Persistent `.mmd` production remains separately registered.

Local Working readers retain lazy managed inline rendering, mounted-document cancellation and visible parser/runtime errors. Public readers choose the prepared image for the active theme. There is no Preview browsing stage or managed/public stage selector.

Cutover can copy eligible baseline pairs from completed Preview into Working without rerendering or republishing. The current baseline contains zero fenced diagrams, so static/import evidence does not establish exercised SVG production. New projection and failure scenarios remain manually unverified; no tests or browser automation were added.

## Reader Detail View

Supported rendered diagrams receive one overlaid **Open diagram** button while the diagram body remains ordinary document content. The button requests the shared `content-detail` main view with one exact mount-bound diagram target. The diagram adapter moves the accepted persistent image or managed-inline host into the expanded viewport and **Back to document** restores that same presentation and invocation focus.

A configured persistent SVG retains its stable served URL. A projected public Mermaid image retains the active light or dark variant and refreshes through the public theme owner. A successfully rendered managed-local inline Mermaid host retains the adapter-owned direct SVG, including its responsive `viewBox`, visible presentation, title, and description. Theme refresh while the detail view is active updates the moved presentation through those existing owners.

The existing `main-view` toolbar contributes **Open in new tab** only while the active adapter supplies a valid target. Persistent diagrams use their stable served URL, public-themed diagrams use the active prepared variant, and managed-inline diagrams use a temporary standalone `image/svg+xml` Blob. Theme refresh replaces the relevant toolbar target, and Back, navigation, document replacement, and adapter release revoke temporary resources before ownership ends.

The shared adapter accepts generated persistent and themed markers plus the managed-inline adapter's successful host. Public readers compose the shared adapter for persistent and themed projections; Manage additionally composes inline Mermaid rendering and resource creation; Review retains its returned-package composition. The component button and icon-only toolbar link use the same pill and external-open glyph language, remain native controls with **Open diagram** or **Open in new tab** accessible labels and tooltips, and keep visible keyboard focus. The expanded viewport provides scalable keyboard-focusable inspection at supported desktop widths and in both themes. Public projected diagrams own their separate narrow-width acceptance.

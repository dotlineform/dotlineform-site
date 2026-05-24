---
doc_id: site-request-docs-viewer-shell-extraction
title: Docs Viewer Shell Extraction Request
added_date: 2026-05-23
last_updated: 2026-05-24
ui_status: draft
parent_id: change-requests
sort_order: 10020
viewable: true
---
# Docs Viewer Shell Extraction Request

Status:

- planned follow-up
- related to, and narrower than, the active [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- should follow Studio source-tree reorganization rather than run alongside it

## Summary

Separate Docs Viewer runtime, server/services, Docs Viewer source files, config, and associated assets from the Studio-hosted implementation after Studio localization and Studio source-tree reorganization are stable.

During the Studio source-tree reorganization, the current Docs Viewer remains hosted inside Studio.
Current Docs Viewer code, server/services, source config, UI text, CSS, associated assets, and Docs Viewer source Markdown may move under a clear internal Studio home such as `studio/docs-viewer/` because Studio owns canonical data and the local Docs Viewer server until extraction.
They should not be scattered across unrelated Studio folders; the existing Docs Viewer localization work should remain visible as an extraction-ready boundary.
Canonical publishing Markdown such as `_docs_catalogue/` is Studio-owned site source, not Docs Viewer-owned source, and is not part of the later Docs Viewer extraction.
Generated docs/search JSON consumed by public installs such as `/library/` and `/analysis/` remains in the public Jekyll site output paths.

This follow-on request is what makes Docs Viewer truly portable.
Extraction means moving the Docs Viewer runtime, server/services, Docs Viewer source contract, source config, management behavior, and associated assets out of Studio into a reusable boundary such as `docs-viewer/`, with Studio becoming one possible host shell rather than the owner.

## Boundary Decision

Until this extraction starts, Docs Viewer is Studio-hosted for source-tree ownership.
That interim placement does not mean Docs Viewer is permanently a Studio subsystem.
Studio may host Docs Viewer, configure Docs Viewer, and enable management/write affordances, but the extraction target is an independent Docs Viewer package boundary.

The extraction should distinguish:

- Docs Viewer core: document loading, navigation, search, rendering, reports, bookmarks, generated data contract, UI text, and read-only viewer behavior
- Docs Viewer management: import, settings, source-config reports, management-only controls, and docs write API contracts
- Docs Viewer source: source Markdown, scope config, source-side metadata, and local write/rebuild assumptions needed to generate Docs Viewer payloads
- Studio shell: Local Studio navigation, app chrome, runtime config handoff, management-mode enablement, and local app API wiring
- Portable shell: standalone route/page wrapper that can load relative config and generated docs/search payloads without Studio
- Public generated output: generated docs/search JSON read by `/library/`, `/analysis/`, and other public installs, stored where the consuming Jekyll site publishes it

## Target Direction

After extraction, the likely target shape is:

```text
docs-viewer/
  core/
  static/
  shells/
    studio/
    portable/
  data-contract/

studio/
  app/
    shells/
      docs-viewer/
```

The exact layout should be revisited when this request starts.
The starting point for this request should assume the Studio source-tree reorganization has moved the current Docs Viewer implementation under a clear internal Studio home such as `studio/docs-viewer/`.
The first implementation should move that coherent Docs Viewer subtree out of `studio/` deliberately, without changing generated payload locations unless the config contract is ready to support that move.

## CSS Ownership Direction

Docs Viewer currently works in public `/library/` and `/analysis/` because those routes inherit public `assets/css/main.css` from the site layout before loading Docs Viewer CSS.
Local Studio `/docs/` similarly inherits public `main.css` and Studio CSS from the Studio shell before loading Docs Viewer CSS.

That is acceptable for the current integrated site, but it is a portability boundary.
The shell extraction should make the CSS base explicit:

- Docs Viewer reusable CSS should remain under the Docs Viewer boundary and use Docs Viewer-prefixed tokens for viewer, report, and management UI
- public read-only installs may inherit the public site base intentionally through their public route shell
- Studio-hosted management may inherit Studio shell CSS intentionally through the Studio shell
- a portable read-only shell should either provide a Docs Viewer-owned base stylesheet or document the small host-supplied base contract it requires
- Docs Viewer reusable CSS must not depend on Studio-only classes, and portable Docs Viewer installs must not require dotlineform public `main.css` unless that file is deliberately part of the host integration

## Implementation Tasks

- Inventory current Docs Viewer JS, CSS, includes, browser config, UI text, generated payload assumptions, and Studio integration points.
- Inventory the Docs Viewer files that the Studio source-tree reorganization placed under `studio/`, including runtime code, server/services, Docs Viewer source Markdown, source config, UI text, CSS, assets, tests, and management endpoints.
- Define the shell contract: required DOM roots, config attributes, route parameters, events, management capability flags, and write API endpoints.
- Define the canonical source contract for portable installs: where source Markdown and scope config live, which source files are copied or generated, and which generated JSON/search payloads remain in the consuming Jekyll site's public output paths.
- Define the CSS shell contract: which base typography, theme, container, link, and spacing tokens are provided by the host shell versus by Docs Viewer-owned CSS.
- Move reusable Docs Viewer runtime, server/services, canonical source handling, config, UI text, CSS, and associated assets out of Studio into the Docs Viewer boundary.
- Keep or create Studio-specific shell code inside Studio so Local Studio can continue hosting Docs Viewer management after extraction.
- Add a minimal portable shell that can load relative Docs Viewer config and generated docs/search payloads without the Studio app server.
- Add or identify a Docs Viewer-owned base stylesheet for portable installs if the host shell contract is not enough.
- If a standalone Docs Viewer launcher is still useful, define it here as part of the portable shell contract rather than as a Local Studio migration fallback.
- Verify Studio-hosted Docs Viewer management mode still works after the shell split.
- Verify a portable read-only fixture can load a docs corpus without Studio navigation or Studio runtime config.
- Update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) with the resulting copy/install contract.

## Acceptance Criteria

- Studio can still host `/docs/` management mode through the Local Studio app server.
- Public read-only `/library/` and `/analysis/` installs remain functional.
- Reusable Docs Viewer runtime, server/services, canonical source contract, config, UI text, CSS, and assets are no longer physically owned by Studio.
- Reusable Docs Viewer files are not dependent on Studio navigation, Studio app chrome, or Studio-only runtime config.
- Reusable Docs Viewer CSS is not dependent on Studio-only selectors or on dotlineform public `main.css` except where a public route shell intentionally supplies that file as the host base.
- A portable shell exists with a documented minimum config and generated-data contract.
- The active [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer) is updated with the extraction outcome.

## Related References

- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Studio Source Tree Reorganization Request](/docs/?scope=studio&doc=site-request-studio-source-tree-reorganization)
- [Studio Local Vanilla Web App Request](/docs/?scope=studio&doc=site-request-studio-local-vanilla-web-app)

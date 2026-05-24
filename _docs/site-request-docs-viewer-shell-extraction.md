---
doc_id: site-request-docs-viewer-shell-extraction
title: Docs Viewer Shell Extraction Request
added_date: 2026-05-23
last_updated: 2026-05-24
ui_status: planned
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

Separate Docs Viewer reusable runtime/core concerns from the Studio-hosted shell after Studio localization and Studio source-tree reorganization are stable.

The current Docs Viewer remains portable as a product goal, but the immediate Local Studio migration hosts Docs Viewer management through the Studio app server.
That is acceptable for the current phase.
The follow-up extraction should make the shell boundary explicit so Docs Viewer can keep working inside Studio while a later portable install can provide its own standalone shell.

## Boundary Decision

Docs Viewer should not become a Studio subsystem.
Studio may host Docs Viewer, configure Docs Viewer, and enable management/write affordances, but the reusable viewer runtime and data contract should remain independent.

The extraction should distinguish:

- Docs Viewer core: document loading, navigation, search, rendering, reports, bookmarks, generated data contract, UI text, and read-only viewer behavior
- Docs Viewer management: import, settings, source-config reports, management-only controls, and docs write API contracts
- Studio shell: Local Studio navigation, app chrome, runtime config handoff, management-mode enablement, and local app API wiring
- Portable shell: standalone route/page wrapper that can load relative config and generated docs/search payloads without Studio

## Target Direction

The likely target shape is:

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
The first implementation should avoid changing generated payload locations unless the config contract is ready to support that move.

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
- Define the shell contract: required DOM roots, config attributes, route parameters, events, management capability flags, and write API endpoints.
- Define the CSS shell contract: which base typography, theme, container, link, and spacing tokens are provided by the host shell versus by Docs Viewer-owned CSS.
- Move or wrap Studio-specific shell code so it is clearly separate from reusable Docs Viewer runtime code.
- Add a minimal portable shell that can load relative Docs Viewer config and generated docs/search payloads without the Studio app server.
- Add or identify a Docs Viewer-owned base stylesheet for portable installs if the host shell contract is not enough.
- If a standalone Docs Viewer launcher is still useful, define it here as part of the portable shell contract rather than as a Local Studio migration fallback.
- Verify Studio-hosted Docs Viewer management mode still works after the shell split.
- Verify a portable read-only fixture can load a docs corpus without Studio navigation or Studio runtime config.
- Update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) with the resulting copy/install contract.

## Acceptance Criteria

- Studio can still host `/docs/` management mode through the Local Studio app server.
- Public read-only `/library/` and `/analysis/` installs remain functional.
- Reusable Docs Viewer runtime files are not dependent on Studio navigation, Studio app chrome, or Studio-only runtime config.
- Reusable Docs Viewer CSS is not dependent on Studio-only selectors or on dotlineform public `main.css` except where a public route shell intentionally supplies that file as the host base.
- A portable shell exists with a documented minimum config and generated-data contract.
- The active [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer) is updated with the extraction outcome.

## Related References

- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Studio Source Tree Reorganization Request](/docs/?scope=studio&doc=site-request-studio-source-tree-reorganization)
- [Studio Local Vanilla Web App Request](/docs/?scope=studio&doc=site-request-studio-local-vanilla-web-app)

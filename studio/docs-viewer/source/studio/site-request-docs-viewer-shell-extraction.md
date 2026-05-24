---
doc_id: site-request-docs-viewer-shell-extraction
title: Docs Viewer Shell Extraction Request
added_date: 2026-05-23
last_updated: 2026-05-24
ui_status: in-progress
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

Separate Docs Viewer runtime, server/services, Docs Viewer source files, config, shell, and associated assets from the current integrated implementation after Studio localization and Studio source-tree reorganization are stable.

During the Studio source-tree reorganization, the current Docs Viewer remains in its existing Studio-integrated location.
Current Docs Viewer code, server/services, source config, UI text, CSS, associated assets, and Docs Viewer source Markdown may move under a clear internal Studio home such as `studio/docs-viewer/` because Studio owns canonical data and the local Docs Viewer server until extraction.
They should not be scattered across unrelated Studio folders; the existing Docs Viewer localization work should remain visible as an extraction-ready boundary.
Canonical publishing Markdown such as `_docs_catalogue/` is Studio-owned site source, not Docs Viewer-owned source, and is not part of the later Docs Viewer extraction.
Generated docs/search JSON consumed by public installs such as `/library/` and `/analysis/` remains in the public Jekyll site output paths.

This follow-on request is what makes Docs Viewer truly portable.
Extraction means moving the Docs Viewer runtime, server/services, Docs Viewer source contract, source config, management behavior, shell, and associated assets out of Studio into a self-contained `.docs-viewer/` folder.
Studio is not a Docs Viewer host after extraction.
Instead, Studio and Jekyll-hosted pages are peer consumers that discover Docs Viewer through repo-owned config and link to the Docs Viewer service when it is running.
Docs Viewer starts and stops independently of Local Studio.

## Boundary Decision

Until this extraction starts, current Docs Viewer files remain under Studio for source-tree ownership.
That interim placement does not mean Docs Viewer is permanently a Studio subsystem.
The extraction target is an independent Docs Viewer service boundary under `.docs-viewer/`, not a Studio subsystem and not a Studio shell.
The host repo owns the integration config that tells local pages where the Docs Viewer service is available and which public or local-only document links should point to it.
Docs Viewer advertises its running local host location through that config, including the active port or base URL, so that Local Studio, Live Preview pages, and generated Jekyll pages can link to:

- public read-only Docs Viewer pages served by the Docs Viewer service
- local-only manage-mode Docs Viewer pages served by the Docs Viewer service

The extraction should distinguish:

- Docs Viewer core: document loading, navigation, search, rendering, reports, bookmarks, generated data contract, UI text, and read-only viewer behavior
- Docs Viewer management: import, settings, source-config reports, management-only controls, and docs write API contracts
- Docs Viewer source: source Markdown, scope config, source-side metadata, and local write/rebuild assumptions needed to generate Docs Viewer payloads
- Docs Viewer shell: standalone route/page wrapper and local service entrypoint owned by `.docs-viewer/`, able to load relative config and generated docs/search payloads without Studio
- Host integration config: repo-owned config that records the Docs Viewer service base URL, public link behavior, manage-mode availability, generated data locations, and source/write capability flags
- Studio integration: Local Studio navigation and UI links that point to the Docs Viewer service when it is running, without embedding or hosting the Docs Viewer shell
- Live Preview integration: Jekyll-hosted pages that can link to Docs Viewer-hosted documents through the advertised Docs Viewer base URL
- Public generated output: generated docs/search JSON read by `/library/`, `/analysis/`, and other public installs, stored where the consuming Jekyll site publishes it

## Target Direction

After extraction, the likely target shape is:

```text
.docs-viewer/
  core/
  shell/
  services/
  static/
  config/
  data-contract/
  source/

studio/
  app/
    integrations/
      docs-viewer/

config/
  docs-viewer-host.json
```

The exact layout should be revisited when this request starts.
The starting point for this request should assume the Studio source-tree reorganization has moved the current Docs Viewer implementation under a clear internal Studio home such as `studio/docs-viewer/`.
The first implementation should move that coherent Docs Viewer subtree out of `studio/` deliberately, without changing generated payload locations unless the config contract is ready to support that move.
The host repo config should be the bridge between existing generated payload locations and the independent Docs Viewer service.
For this repo, the local development shape may include three independently running services:

- Live Preview
- Local Studio
- Docs Viewer

This repo should provide a single shell script that can start all three services for local work while still allowing each service to be started and stopped independently.

## CSS Ownership Direction

Docs Viewer currently works in public `/library/` and `/analysis/` because those routes inherit public `assets/css/main.css` from the site layout before loading Docs Viewer CSS.
Local Studio `/docs/` similarly inherits public `main.css` and Studio CSS from the Studio shell before loading Docs Viewer CSS.

That is acceptable for the current integrated site, but it is a portability boundary.
The shell extraction should make the CSS base explicit:

- Docs Viewer reusable CSS should remain under the Docs Viewer boundary and use Docs Viewer-prefixed tokens for viewer, report, and management UI
- public read-only installs may inherit the public site base intentionally through their public route shell
- Docs Viewer management must be styled by Docs Viewer-owned CSS or an explicit host base contract, not by implicit Studio shell inheritance
- the Docs Viewer shell should either provide a Docs Viewer-owned base stylesheet or document the small host-supplied base contract it requires
- Docs Viewer reusable CSS must not depend on Studio-only classes, and portable Docs Viewer installs must not require dotlineform public `main.css` unless that file is deliberately part of the host integration

## Implementation Tasks

- Inventory current Docs Viewer JS, CSS, includes, browser config, UI text, generated payload assumptions, and Studio integration points.
- Inventory the Docs Viewer files that the Studio source-tree reorganization placed under `studio/`, including runtime code, server/services, Docs Viewer source Markdown, source config, UI text, CSS, assets, tests, and management endpoints.
- Define the standalone Docs Viewer shell contract: required DOM roots, config attributes, route parameters, events, management capability flags, write API endpoints, advertised service URL, and local start/stop behavior.
- Define the canonical source contract for portable installs: where source Markdown and scope config live, which source files are copied or generated, and which generated JSON/search payloads remain in the consuming Jekyll site's public output paths.
- Define the CSS shell contract: which base typography, theme, container, link, and spacing tokens are provided by the host shell versus by Docs Viewer-owned CSS.
- Define the repo-owned host config that records Docs Viewer availability, base URL/port, public link behavior, manage-mode availability, generated payload locations, and source/write capability flags.
- Move reusable Docs Viewer runtime, server/services, canonical source handling, config, UI text, CSS, shell, and associated assets out of Studio into `.docs-viewer/`.
- Replace Studio-specific Docs Viewer hosting code with Studio integration/link code that points to the advertised Docs Viewer service when available.
- Add the independent Docs Viewer launcher/start-stop path as part of the `.docs-viewer/` service contract.
- Add or identify a Docs Viewer-owned base stylesheet for standalone Docs Viewer pages if the host shell contract is not enough.
- Add a repo-level shell script that starts Live Preview, Local Studio, and Docs Viewer together while preserving independent service lifecycles.
- Verify Studio can link to Docs Viewer management mode through the advertised local Docs Viewer service.
- Verify Jekyll-hosted pages can link to Docs Viewer-hosted public read-only pages through the advertised local Docs Viewer service.
- Verify the standalone Docs Viewer shell can load a docs corpus without Studio navigation, Studio runtime config, or the Local Studio app server.
- Update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) with the resulting copy/install contract.

## Acceptance Criteria

- Docs Viewer is self-contained under `.docs-viewer/`.
- Docs Viewer runs in its own shell/service and starts/stops independently of Local Studio.
- The host repo has repo-owned config that advertises the running Docs Viewer local host location, including base URL or port.
- Local Studio links to Docs Viewer-hosted management pages when the Docs Viewer service is running, without hosting the Docs Viewer shell.
- Jekyll-hosted pages can link to Docs Viewer-hosted public read-only pages through the advertised service location.
- This repo can optionally start Live Preview, Local Studio, and Docs Viewer together through one shell script while keeping them independent services.
- Public read-only `/library/` and `/analysis/` installs remain functional.
- Reusable Docs Viewer runtime, server/services, canonical source contract, config, UI text, CSS, and assets are no longer physically owned by Studio.
- Reusable Docs Viewer files are not dependent on Studio navigation, Studio app chrome, or Studio-only runtime config.
- Reusable Docs Viewer CSS is not dependent on Studio-only selectors or on dotlineform public `main.css` except where a public route shell intentionally supplies that file as the host base.
- A standalone Docs Viewer shell exists with a documented minimum config and generated-data contract.
- The active [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer) is updated with the extraction outcome.

## Related References

- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Studio Source Tree Reorganization Request](/docs/?scope=studio&doc=site-request-studio-source-tree-reorganization)
- [Studio Local Vanilla Web App Request](/docs/?scope=studio&doc=site-request-studio-local-vanilla-web-app)

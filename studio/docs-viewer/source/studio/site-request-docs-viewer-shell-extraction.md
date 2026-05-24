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

- in progress
- related to, and narrower than, the active [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- should follow Studio source-tree reorganization rather than run alongside it
- implementation tasks are tracked in [Docs Viewer Shell Extraction Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-shell-extraction-tasks)

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

## Config Ownership Decision

Use a split config model so Docs Viewer remains portable while this repo can advertise and integrate a local Docs Viewer service:

- `var/local/site.env` owns local runtime/service settings, including the Docs Viewer host, port, base URL, and manage-mode enablement.
- `_config.yml` owns only static Jekyll integration defaults that public or generated pages need at build/render time, such as whether Docs Viewer links are enabled and fallback link behavior.
- `.gitignore` should ignore generated runtime advertisement files, PID/log files, temporary service state, and Docs Viewer cache/build output if those files are produced.
- `.docs-viewer/config/` owns Docs Viewer defaults and schema, including route names, generated-data contract defaults, shell defaults, and the capability model.
- Add a tracked repo integration config such as `config/docs-viewer.yml` only if `_config.yml`, `var/local/site.env`, and Docs Viewer-owned config are not enough.

The host repo may require `var/local/site.env` as a prerequisite for running Docs Viewer locally.
Docs Viewer-owned config should not contain this repo's local port state.

## Packaging Decision

Keep `.docs-viewer/` as tracked source in this repo for the initial extraction.
Do not turn it into a submodule, external package, or separately versioned dependency until the standalone Docs Viewer service works locally and the boundary has been proven by focused checks.

The tracked folder should still be shaped like a portable package boundary:

- no hidden dependency on Studio paths, Studio shell, or Studio runtime config
- no repo-local host, port, or service-state defaults inside `.docs-viewer/`
- repo-specific integration kept outside `.docs-viewer/` where practical
- scripts and tests written so future packaging is a mechanical follow-up, not a second architecture rewrite

## Service Location Decision

Use static local service location config for the initial extraction.
`var/local/site.env` should contain the configured Docs Viewer host, port, and either an explicit or derived base URL.
The Docs Viewer launcher should start from those values, and Studio/Jekyll integration should link to the same configured location.

For v1:

- do not dynamically allocate a port
- do not require a runtime advertisement writer
- fail clearly if the configured port is unavailable
- keep local link behavior deterministic for tests and manual use

Future options can be revisited after the standalone service works locally:

- Docs Viewer launcher writes a runtime advertisement file on start
- a shared local service manager writes the active base URL for all local services
- Docs Viewer supports dynamic port allocation for external packaging or multi-repo use
- Studio and Jekyll pages probe the configured service before rendering Docs Viewer links

## Link Failure Decision

For v1, Studio and Jekyll pages should render Docs Viewer links from configured static values without probing whether the Docs Viewer service is running.
If Docs Viewer is not running, links should fail normally through the browser or local server.

Do not add disabled-link UI, warning badges, availability polling, or fallback routing for this slice.
The normal failure is acceptable operational feedback that the missing local service should be started, matching how Live Preview links already behave in local development.
Service-aware link UX can be reconsidered later only if normal browser/server failures prove confusing or risky.

## Route Ownership Decision

Docs Viewer owns one built-in local route: `/docs/`.
That route is served by the Docs Viewer service and is the manage-mode browser page.

Additional public read-only scopes are created or registered from Docs Viewer manage mode, including through the New Scope action.
Those scopes map to repo/Jekyll-hosted routes such as `/library/` and `/analysis/`.
At runtime and build time, those host routes use scripts, generated-data contracts, and scope machinery owned by `.docs-viewer/`, but the pages themselves are hosted by the repo/Jekyll route.

Therefore extraction should not treat Docs Viewer as replacing `/library/` or `/analysis/` with Docs Viewer-hosted pages.
Docs Viewer provides the manage route and the scope creation/registration machinery; public scope routes remain host-repo routes installed or registered by Docs Viewer.

## Manage Mode Locality Decision

Manage mode is local-only for the initial extraction.
The built-in `/docs/` manage route is served by the local Docs Viewer service and should bind to loopback for v1.
Manage and write capabilities should be enabled through explicit local capability config, not inferred from public route context.

Do not design this slice around a deployed live manage-mode server.
The working host assumption is a GitHub Pages-style Jekyll site with `_config.yml`, generated/static routes, and public read-only scope pages.
New Scope should continue to create or register static/Jekyll-compatible routes such as `/library/` and `/analysis/`.

Future server-backed manage mode can be considered later as a separate product and hosting decision.
It should not be an implied requirement of the Docs Viewer shell extraction.

## Service Runner Decision

Use a lightweight repo script for the v1 "start all" workflow, modeled on the existing `bin/local-studio` runner pattern.
The script should start Live Preview, Local Studio, and Docs Viewer as independent child processes while preserving each service's ability to be started and stopped separately.

The v1 runner should:

- load `var/local/site.env`
- validate configured static ports before startup
- print the service URLs it starts
- trap `EXIT`, `INT`, and `TERM`
- clean up child processes on shutdown
- fail clearly if a required port is unavailable
- fail clearly if a managed child process exits unexpectedly

Do not introduce daemonization, persistent PID files, restart loops, log rotation, or a third-party process manager for v1.
A proper process supervisor can be reconsidered only if the shell runner becomes unreliable or service lifecycle requirements grow.

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
- Apply the config ownership decision across `var/local/site.env`, `_config.yml`, `.gitignore`, and `.docs-viewer/config/`, adding tracked repo integration config only if needed.
- Keep `.docs-viewer/` tracked as repo source for this extraction while avoiding hidden Studio and repo-local runtime dependencies inside that boundary.
- Use static Docs Viewer host, port, and base URL settings from `var/local/site.env` for v1, with clear startup failure when the configured port is unavailable.
- Render configured Docs Viewer links without service availability probing; if Docs Viewer is not running, let links fail normally.
- Preserve route ownership: Docs Viewer service owns built-in `/docs/` manage mode, while public read-only scopes such as `/library/` and `/analysis/` remain repo/Jekyll-hosted routes installed or registered through Docs Viewer scope machinery.
- Keep manage mode local-only for v1 through loopback binding and explicit local capability flags; public scope routes remain static/Jekyll-compatible read-only routes.
- Add a `bin/local-studio`-style lightweight "start all" runner for Live Preview, Local Studio, and Docs Viewer with static port validation, signal cleanup, and clear child-process failure behavior.
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

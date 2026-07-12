---
doc_id: docs-viewer-runtime-boundary
title: Runtime
added_date: 2026-03-31
last_updated: 2026-07-11
summary: Durable public, manage, review, shared-runtime, service-authority, and asset-boundary contract for Docs Viewer installations.
parent_id: docs-viewer
---
# Docs Viewer Runtime

## Purpose

This document records the durable boundary between public read-only Docs Viewer installs, the local/manage Docs Viewer install, the local returned-package review install, and shared lower-level runtime code.

Detailed route, payload, and module ownership tables live in:

- [Runtime Surfaces](/docs/?scope=studio&doc=docs-viewer-runtime-surfaces)
- [Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts)
- [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership)
- [JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)

The boundary exists so the repo can keep adding scope-specific docs behavior without forking stable viewer primitives or leaking local/manage tooling into public-reader routes.

## Boundary Summary

Public read-only installs should be lightweight deliverables that import only the data, JavaScript, CSS, and browser-visible config they need.
Local/manage installs can keep the full management surface, local-service workflows, report tooling, source editing, imports, settings, and scope lifecycle behavior.
Local/review installs receive only package-rooted generated reads/repair, inventory reads, canonical comparison links, and the identity-only managed-import handoff.

The durable boundary is:

- public surface is only what the public entrypoint imports, the public shell renders, and public route/config records expose
- manage surface is only what the manage entrypoint imports, the manage shell renders, and management capability checks plus server-side endpoints authorize
- review surface is only what the review entrypoint imports, the review shell renders, and independently gated review endpoints authorize
- shared core is not public surface by itself
- route config, hosted-view records, and generated-data payload names are visibility and composition metadata, not proof that a module, stylesheet, report, service, or data payload belongs in public

Current model:

- public, manage, and review routes load separate entrypoint assets
- route families may diverge at the route-shell and shell-composition level
- all three route families share lower-level core modules only when those modules do not grant authority beyond the receiving route
- public route shells render only public-safe mounts and config
- the local manage shell renders management-capable mounts and receives manage-owned renderer bundles from the manage entrypoint
- the local review shell renders the shared viewer mounts and receives only the read-only returned-package provider and package toolbar controller without source mode or general management UI

## App Context And Authority

Current app context is explicit:

```text
kind: public | manage | review
routeAccess
featurePolicy
serviceAvailability
backendCapabilities
```

The public, manage, and review entrypoints supply the expected app kind. Route config declares `app_kind`, and boot rejects an entrypoint/route mismatch. The implemented `review` context is the local non-management `/docs-review/` route described by [Docs Review](/docs/?scope=studio&doc=docs-viewer-review).

Route access owns presentation and composition only:

- scope-query availability
- management UI composition
- hosted-view and display-mode access requirements

Service context projects independent named surfaces:

- `generatedData`: always present, using either static generated assets or an optional local generated-read base URL
- `source`: absent unless a source service URL is supplied
- `management`: absent unless a management service URL is supplied
- `config`: browser-safe config asset access

Local generated reads no longer depend on management UI or management service presence. Source services no longer derive from management app identity. The current service happens to advertise source and management together when management is enabled, but the browser contract does not require that coupling.

Backend capabilities authorize operations. Route config, registered views, visible controls, and service URLs do not.

## Public, Manage, And Review Install Policy

Docs Viewer should split public and local/manage deliverables at the entrypoint and shell-composition level, while keeping genuinely shared lower-level primitives.
The review route follows the same rule: it reuses public-safe viewer primitives and imports only its read-only package workflow through the review entrypoint. Source-editor modules and management CSS remain manage-only.

Shared modules remain appropriate for:

- route URL helpers
- generated-data read primitives
- search normalization
- tree and visibility helpers with public-safe inputs
- renderer primitives that do not import management controls
- hosted-view lifecycle helpers with explicit public/manage access checks

Shared modules are not appropriate places for:

- local-service endpoint calls
- management write authority
- management controls or modal markup
- report registry loading
- source editing
- import/write workflows
- scope lifecycle actions
- manage-only CSS assumptions

Default feature flow:

1. Build new Docs Viewer capabilities in local/manage first unless the request is explicitly public-only.
2. Keep the capability behind the manage entrypoint, management shell, management UI text, management CSS, and management service contracts.
3. Promote a capability to public only through a named public-promotion step.
4. In that promotion step, choose the exact public modules, CSS, config, data contract, route records, and tests.
5. Add tests that prove manage-only assets and data do not load on public routes after promotion.

Promotion should be explicit because public scopes are public-reader installs, not local tools with disabled controls.
Do not implement a new feature by adding it to one broad runtime and then hiding it from public with scattered mode checks.
Access checks still matter for graceful unavailable states, but they are not a substitute for not shipping manage-only assets to public routes.

Reports are the reference example.
The manage install can keep the full report framework, local-service reports, source/config audits, semantic-reference reports, broken-link audits, and admin tables.
Public installs should not load report runtime, report CSS, or report registry data until a specific public report is promoted.
When that happens, only the selected public-safe report loader, public-safe data source, minimum report renderer/CSS, route config, and asset-load tests should move across.
Manage-only reports must remain absent from public entrypoint imports and public route loads.

Public promotion acceptance should include:

- public route network/import assertions for JS, CSS, route config, UI text, report metadata, and generated data
- public DOM assertions that management controls, source-editor controls, import hosts, settings controls, scope lifecycle controls, and local-service status surfaces are not rendered
- manage smoke coverage proving the full management surface still loads through the manage entrypoint
- source docs describing what was promoted and why it is public-safe

## Route Capability Boundary

Current route rules:

| Route | Install type | Management | Scope query | Data authority |
| --- | --- | --- | --- | --- |
| `/docs/` | local/manage | enabled by route | allowed | standalone Docs Viewer service and generated-read paths |
| `/library/` | public read-only | disabled | ignored/normalized away | public static generated payloads |
| `/analysis/` | public read-only | disabled | ignored/normalized away | public static generated payloads |

Additional route rules:

- `/docs/` is the only management route; it is served by the standalone Docs Viewer service.
- `/docs/` can switch the loaded docs scope with `?scope=studio`, `?scope=library`, or `?scope=analysis`.
- `/library/` and `/analysis/` are public read-only viewer routes and do not render management controls, configure write-capable management mode, or load management-only CSS.
- public read-only viewer routes avoid publishing or loading management-only JS/CSS, the HTML import modules, the local manage-capable route registry, management base URLs, local generated-read service base URLs, and backend capability probes.
- local `bin/local-studio` links to the configured Docs Viewer service but does not serve Docs Viewer management, generated reads, or Docs Viewer assets.
- canonical internal docs links stay read-only-safe and omit any management query; the `/docs/` shell is management-capable by route identity.

Route surface details live in [Docs Viewer Runtime Surfaces](/docs/?scope=studio&doc=docs-viewer-runtime-surfaces).

## Controller And Hosted-View Lifecycle Contract

Docs Viewer controllers and hosted views use a practical lifecycle, not a framework-level plugin system.

Controller terms:

- `create`: assemble a controller with explicit refs, callbacks, state-domain inputs, services, and config values.
- `initialize`: run startup work that should not happen at construction time, such as bookmark storage loading or management capability checks.
- `bind`: attach DOM/window event listeners for the controller's owned surface. Bind is a startup phase and should be called once.
- `update` or `project`: render or project current state after selected document, route state, panel state, or capability state changes.
- `dispose`: optional cleanup for controllers that gain a shorter lifetime than the route or own external subscriptions, timers, workers, observers, or hosted resources.

Hosted-view terms:

- `load`: optional lazy module load or factory step.
- `mount`: render into an explicit mount element from an explicit hosted-view context.
- `update`: refresh an already-mounted view from a new explicit context.
- `unmount`: clear the active mounted view when switching views or closing a panel.
- `close`: host action that marks the panel closed and unmounts the active view.
- `dispose`: final cleanup for the active view if the host itself is discarded.

Lifecycle rules:

- Use lifecycle methods only where they reduce coupling or clarify phase ownership.
- Keep stateless render/project helpers stateless.
- Public-safe hosted views must mount without management services, backend probes, local generated-read service base URLs, write-capable service handles, or management CSS/JS.
- Manage-only hosted views may receive explicit management service or capability inputs, but visibility and registration do not imply write authority.
- Manage-owned document extras may mount report surfaces; public entrypoints must not supply report extras unless a named public-promotion request defines the public report assets and tests.
- Main-view source-editor service slots must be omitted from public contexts and supplied only through explicit management-capable context construction.
- Route-config hosted-view records are metadata/capability declarations only. They must not load arbitrary modules, override built-in or repo-owned ids, or create plugin behavior.
- Backend writes remain behind named management endpoints with server-side validation.
- Future feature views should attach through panel/controller contracts and explicit context or service inputs, not by modifying route shell markup or reading broad runtime state.
- Do not turn hosted-view records into a plugin platform, third-party loader, source editor, semantic-reference editor, or visualization extension point without a separate request.

Module owner details live in [Docs Viewer Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership).

## Generated Data Boundary

Generated-data rules:

- Feature-facing controllers consume named generated-data read methods from `docs-viewer-generated-data-runtime.js` through explicit controller or report-context inputs.
- Config loading consumes `docs-viewer-config-service.js`; the config controller must not import `docs-viewer-data.js` directly.
- Low-level fetch/retry helpers in `docs-viewer-data.js` are primitives behind `docs-viewer-generated-data-runtime.js` and `docs-viewer-config-service.js`.
- Static asset URL projection belongs in `docs-viewer-asset-url.js`; callers should not import `docs-viewer-data.js` only to add asset versions.
- Public routes must not carry management/tooling metadata only because a shared runtime helper can read it.
- Public and manage generated payload shapes are owned by explicit generated-data contracts, not by incidental current renderer needs.

Generated payload details live in [Docs Viewer Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts).

## Scope-Specific Differences

These are normal route-shell differences and should not force a runtime fork:

- scope-specific inline search controls or other shell actions
- different viewer data URLs
- different base routes and default docs
- whether the route shell enables management mode
- whether the route shell exposes scope switching
- surrounding page context and navigation state
- scope-specific copy or small shell-level layout changes
- distinct source trees and generated JSON artifacts
- scope-specific viewer options in generated docs payloads, such as manage-only structural roots

These are not good reasons to split the runtime:

- adding or removing a button in one scope page
- changing page-level copy
- changing which scope-owned JSON tree the viewer loads
- adding small optional shell parameters to the shared include
- keeping Studio and library docs in separate source roots
- hiding a structural tree branch in one scope when that rule can be expressed as generated scope-owned data

If the difference can be expressed through data, route-shell composition, or a small include option, the runtime should stay shared.

## Potential Fork Triggers

A fork only becomes justified if the scopes stop being the same kind of viewer.

Examples:

- one scope stays a tree-based docs viewer while another becomes faceted browsing
- one scope wants timeline or gallery navigation instead of a docs tree
- one scope needs a richer content renderer with annotations, embedded canvases, or interactive reading tools
- one scope needs a different page anatomy than the sidebar-plus-content viewer
- one scope needs nested route segments rather than `?doc=...`
- one scope needs version switching, compare state, or multi-pane state in the URL
- one scope remains small while another needs chunked indexes, lazy subtree loading, or other large-corpus behavior
- one scope stays read-only while another needs editing affordances, advanced keyboard navigation, or persistent review state

## Preferred Response Before Forking

If a new requirement appears, prefer these steps in order:

1. express it as scope-owned data
2. express it as route-shell divergence
3. add a narrow optional include parameter
4. add a narrow runtime option if the core viewer model is still the same
5. fork only if the viewer model itself has diverged

Use one runtime while the scopes are still:

- tree-index driven
- document-viewer shaped
- compatible with the same URL/state contract
- compatible with the same loading strategy

Consider a fork only when a new scope would otherwise force the shared runtime to carry a second competing model of navigation, rendering, or interaction.

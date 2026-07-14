---
doc_id: docs-viewer-public-scopes
title: Public Scopes
added_date: 2026-03-31
last_updated: 2026-07-14
summary: Working-to-published data flow and management-isolation guarantees for public read-only Docs Viewer routes.
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Public Scopes

A public scope is locally managed canonical content delivered through a fixed read-only static route. It shares reader code with `/docs/`, but it does not share the management entrypoint, local service configuration, or working generated-data source.

## Data Flow

```text
canonical Markdown
docs-viewer/source/<scope>/
          |
          | build / local write follow-through
          v
working docs + search
docs-viewer/generated/
          |
          | explicit Publish
          v
tracked public snapshots
site/assets/data/
          |
          v
fixed public static route
site/<route>/index.html
```

Canonical source is the authority. Working generated data is the local review surface. Published snapshots are the files deployed for public reads. Publishing does not deploy the site or mutate source; it copies the reviewed working docs/search projection and removes stale copied payload files.

## Public And Management Boundaries

| concern | public route | local `/docs/` route |
| --- | --- | --- |
| scope | Fixed by public route config. | Selected from configured scopes. |
| runtime entrypoint | Public only. | Management contributions load after local context is established. |
| data reads | Published `site/assets/data/` snapshots. | Working generated-data service reads. |
| services | No local service base URLs. | Loopback Docs Viewer service. |
| controls | Reader controls only. | Capability-gated editing, import, publish, and lifecycle controls. |
| query state | `scope` and management `mode` cannot widen the route. | `scope`, `doc`, and supported management state are meaningful. |

The static shell identifies a public route id and loads `site/docs-viewer/config/routes/docs-viewer-public-routes.json`. That browser-safe registry fixes the scope, viewer base URL, published payload URLs, and public UI features. The public viewer config is a filtered projection and contains no localhost management base URLs.

UI absence is not the sole security boundary. Public routes cannot load the management entrypoint, and mutation endpoints remain available only from the loopback service.

## Publish Workflow

For a configured public scope, local management exposes one Publish command through the toolbar and Actions menu.

1. `GET /docs/publish/status` compares working and published payloads.
2. `POST /docs/publish/confirm` returns the proposed copy/remove diff without writing.
3. `POST /docs/publish/apply` requires `confirm: true` and recomputes the operation before synchronizing files.

Local scopes do not advertise a publish target. Their generated JSON remains under Docs Viewer-owned working roots and must not be redirected into public `site/assets/data/` paths.

## Public Payload Contract

Public routes read compact scope-owned files:

- `index-tree.json` for public-viewable navigation
- `recently-added.json` for the small recent list
- `by-id/<doc_id>.json` for rendered document content and public-safe metadata
- the scope search `index.json`

Public per-document payloads intentionally omit management metadata such as parent paths, visibility state, UI status, internal route details, and report/service data. Search and tree generation exclude non-viewable documents, while local management can still inspect their working generated payloads.

Exact schemas belong to [Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts) and the builders/tests, not this boundary summary.

## Creating And Deleting Public Scopes

[Scope Lifecycle](/docs/?scope=studio&doc=docs-viewer-new-scopes-builder) creates a public scope by writing its conventional source/config records, rendering a tracked static route shell, adding public and management route records, building working output, and copying the initial public snapshots.

The lifecycle manifest records the created route shell, source/output roots, and published payloads. Delete may remove them only for a scope recorded as user-created and tool-created. Shared runtime, CSS, templates, and route registry files are changed or reused; they are never recorded as deletable scope assets.

## Executable Assurance

`public_docs_viewer_readonly.py` boots public routes from a static site root and verifies:

- public app kind with management and source service disabled
- no local service base URLs or management controls
- the public route registry and public payload URLs are used
- management query state is normalized away
- only public-safe metadata appears in the info panel
- tree, recent, document, search, and public report paths remain functional

Lifecycle tests separately prove that creating a public scope produces its route/config/payload set and that deleting an eligible scope removes only its owned records and files.

## Extension Method

Add a public scope through lifecycle rather than hand-assembling a route. A change to the public delivery model should preserve four independent checks:

1. canonical source and working outputs remain outside `site/assets/`
2. Publish is the explicit working-to-public synchronization boundary
3. the public route loads only public-filtered config, payloads, and entrypoint modules
4. browser smoke proves the absence of management/service state as well as successful reading

## Weak Spots

- Working and published payloads can intentionally differ until Publish; there is no automatic deployment or persistent publication ledger.
- Public route and viewer configs are generated projections from canonical registries. Manual edits can create drift until builders or lifecycle rewrite them.
- Public media objects are referenced by URL/token but are not covered by scope publish or lifecycle manifests.
- Public isolation is layered across config filtering, route policy, entrypoint imports, capability absence, payload filtering, and loopback authorization. A change crossing those layers needs more than a UI visibility test.
- Lifecycle artifact tests and public browser smoke are separate; a newly created route is not booted end to end in the same test.

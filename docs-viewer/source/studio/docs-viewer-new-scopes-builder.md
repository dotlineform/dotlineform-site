---
doc_id: docs-viewer-new-scopes-builder
title: Scope Lifecycle
added_date: 2026-05-15
last_updated: 2026-07-14
summary: Create, rename, and delete Docs Viewer scopes through previewed server plans, explicit ownership, and public-isolation safeguards.
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Scope Lifecycle

Scope lifecycle is the local-management boundary for creating, narrowly renaming, and deleting Docs Viewer scopes. It coordinates canonical source, generated data, configuration, route assets, media ownership, and rebuilds; it is not a browser-side file helper.

The assurance model is:

- scope config describes where a scope lives and how it is delivered
- the lifecycle manifest records what this tool may later delete
- the server plans from current state before every mutation
- apply requires explicit confirmation and recomputes the plan
- per-scope capabilities tell the UI which operations are eligible
- public routes receive neither the management entrypoint nor local service configuration

Exact endpoint payloads belong to [Scope Lifecycle Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-scope-lifecycle).

## Structure

```text
management UI
    |
    | request preview
    v
loopback Docs Viewer service
    |
    +-- scope config -------- topology, scope type, source/output/media paths
    +-- lifecycle manifest -- tool ownership and delete eligibility
    +-- route registries ---- management route defaults and public route records
    +-- current filesystem -- conflicts, missing paths, containment
    |
    v
write-free plan: allowed + blockers + created/changed/deleted paths
    |
    | confirm apply
    v
server recomputes plan -> mutates allowlisted roots -> rebuilds -> refreshes capabilities
```

The browser never submits an authoritative filesystem plan. It sends scope identities and choices; the service resolves paths and eligibility again.

## Scope Types

| mode | canonical source | working generated data | public delivery |
| --- | --- | --- | --- |
| `public_readonly` | Repo source root. | `docs-viewer/generated/` working docs/search. | Static route shell and copied snapshots under `site/assets/data/`. |
| `local_committed` | Repo source root. | `docs-viewer/generated/` only. | None; read through local `/docs/`. |
| `local_external` | Derived `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/source/<scope>/`. | Derived external docs/search roots. | None; read through local service endpoints. |

The external root is derived from one configured workspace marker. The UI does not collect arbitrary absolute paths, and checked-in config does not store user-specific paths.

## Operator Workflow

### Create

1. Choose `New scope` in the local `/docs/` Actions menu.
2. Choose the scope id, title, default document, and publishing mode.
3. For a public scope, supply its public route; for a repo-backed scope, supply the required conventional source root.
4. Review the server-planned storage and affected paths.
5. Confirm apply.

Create writes a default source document, appends config and manifest records, creates only mode-appropriate route/output paths, and rebuilds the new scope. A public create also renders the static route shell, updates the public route registry, and copies the initial generated snapshots.

### Rename

Rename is intentionally limited to lifecycle-created external-local scopes. It moves derived source, media, generated-docs, and generated-search roots; updates scope config, manifest identity, UI-status keys, and sub-scope paths; then rebuilds under the new id.

It does not rename public or committed scopes, rewrite document links, rename R2 objects, or inspect arbitrary source text.

### Delete

Delete is available only when the manifest says the scope is both user-created and created by this lifecycle tool. System/backfilled scopes and a scope used as a management route default are blocked.

Preview lists manifest-owned paths that exist or are already missing. Apply removes eligible owned paths, removes config and route records, removes the manifest record, and rebuilds remaining scopes. Missing recorded files do not prevent removal of the remaining owned state.

Sub-scopes have separate preview/apply services and remain entries owned by their parent scope configuration rather than independent top-level manifest scopes.

## Ownership And Asset Consequences

The manifest records roots and generated artifacts, not semantic ownership of every future file.

| resource | lifecycle behavior |
| --- | --- |
| Repo-backed source root | Created and delete-owned as a directory. Media placed beneath its configured `media/` directory is therefore removed with that source root. |
| External-local source and generated roots | Created, renamed, and delete-owned by their recorded derived paths. |
| External-local media root | Not created or delete-owned by the current create manifest; delete preserves it. External rename nevertheless moves it when present. |
| Public route shell and published snapshots | Created and delete-owned for a lifecycle-created public scope. Shared route registry files are changed, never deleted as scope-owned files. |
| Public R2 objects | Outside the lifecycle manifest. Scope delete and rename do not remove or rename them. |
| Shared runtime, CSS, templates, and browser config families | Never recorded as scope-delete targets. |

This distinction matters: “belongs to a scope” does not automatically mean “safe for lifecycle deletion.” The manifest is the deletion authority, while media publication has its own ownership rules.

## Public Isolation

Public routes and local management share public-safe reader modules, but they do not share authority or delivery inputs.

```text
public static route                     local /docs/ management
-------------------                     ----------------------
public route registry                   management route registry
public-filtered viewer config           full browser-safe scope config
site/assets/data snapshots              local generated-data service reads
public runtime entrypoint               management entrypoint contributions
no local base URLs                      loopback service capabilities
no write/import/lifecycle controls      capability-gated write workflows
```

Public route shells set public app context and load the public entrypoint. Their route config fixes the scope, strips local service base URLs, points only at published static payloads, and does not allow `scope` or `mode` query state to turn the route into management.

Server authorization remains the final boundary even in management mode. UI visibility and capability projection are not write authority.

[Public Scopes](/docs/?scope=studio&doc=docs-viewer-public-scopes) owns working-to-published data flow and the browser-facing isolation contract. [Runtime Architecture](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) owns the entrypoint/import boundary.

## Configuration And Capability Owners

- `docs-viewer/config/scopes/docs_scopes.json` — canonical scope topology and media policy
- `docs-viewer/config/scopes/docs_scope_manifest.json` — lifecycle ownership evidence
- `docs_scope_manifest.py` — ids, publishing modes, planned paths, manifest eligibility, and shared lifecycle rules
- `docs_scope_create.py`, `docs_scope_rename.py`, `docs_scope_delete.py` — top-level preview/apply operations
- `docs_sub_scope_lifecycle.py` — nested source/generated/published sub-scope lifecycle
- `docs_management_capabilities_service.py` — global operation support plus per-scope create/delete/rename eligibility
- `docs-viewer-management-scope-lifecycle-controller.js` — capability-gated UI projection and lazy flow loading
- `docs-viewer-scope-lifecycle.js` — modal choices, preview, confirmation, and result rendering

## Executable Assurance

The current test boundaries prove different parts of the structure:

- `test_docs_scope_config.py` rejects invalid public/local output combinations and escaping sub-scope paths.
- `test_docs_scope_lifecycle.py` covers preview, explicit confirmation, allowlisted create, external rename, system/default-scope delete blockers, public route/payload creation and removal, and sub-scope lifecycle.
- `test_docs_management_capabilities.py` checks capability and portable external-root projection.
- `public_docs_viewer_readonly.py` boots public routes and verifies public app context, no management controls or local service URLs, public-only payload requests, query normalization, and filtered metadata.
- browser module smokes cover capability error projection and active-scope delete navigation.

These tests are more authoritative than copied endpoint or file lists. When lifecycle structure changes, update the smallest test boundary that proves the new invariant.

## Extension Method

When adding a lifecycle-owned resource or operation:

1. Define whether config, manifest, or another registry owns its identity.
2. Make preview derive every affected path from current server-side state.
3. Separate changed shared files from deletable scope-owned paths.
4. Recompute the same plan on confirmed apply.
5. Project eligibility from the service; do not infer it from DOM state, scope names, or paths.
6. Add containment, ownership, partial-state, and public-isolation tests before exposing the control.
7. Document the stable ownership consequence here; keep exact request/response fields in the endpoint reference.

## Weak Spots

- Create, rename, and delete are ordered multi-file operations, not transactions. A filesystem, config, route, or rebuild failure can leave partial current state; there is no rollback bundle.
- Manifest ownership is only as current as the recorded path set. Manual config/filesystem edits can make preview block, omit an unrecorded associated asset, or target a coarse directory containing later-added files.
- External-local media is preserved on delete but moved on rename. That asymmetry is current code, not a general ownership model, and must be resolved before External Asset Collections can rely on it.
- Rename does not rewrite document URLs, `scope=` query values, local media links, or R2 keys.
- Public and committed scopes cannot currently be renamed through lifecycle.
- R2 objects have no lifecycle manifest, reference count, or automatic scope cleanup.
- Unit tests create and remove a new public route and its payloads, while browser smoke boots configured public routes separately. There is no single end-to-end test that creates a fresh public scope and then boots that new route in a browser.
- Public isolation depends on several mutually reinforcing layers—static route config, filtered browser config, entrypoint separation, capability absence, and server authorization—rather than one universal policy object.

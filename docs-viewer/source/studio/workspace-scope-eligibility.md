---
doc_id: workspace-scope-eligibility
title: Workspace Scope Eligibility
added_date: 2026-07-12
last_updated: 2026-07-12
ui_status: proposed
parent_id: workspaces
viewable: true
summary: Focused task to make workspace views, modes, and controls eligible by active Docs Viewer scope, first for Analysis semantic tools and Moments composition tools.
---
# Workspace Scope Eligibility

Status: proposed

## Outcome

Add one shared scope-eligibility contract for code-owned Docs Viewer views, document modes, and controls.

Use it first to enforce:

- `semantic-token-picker` is available only while managing the `analysis` scope
- Moments axis-editor views, modes, and controls are available only while managing the `moments` scope

Public routes must not gain management tools through scope eligibility.
Application kind, route features, backend capabilities, route policy, and active-mode eligibility remain separate checks.

## Proposed Contract

Code-owned view, mode, and control definitions may declare an optional scope allowlist:

```js
{
  id: "semantic-token-picker",
  appKinds: ["manage"],
  scopeIds: ["analysis"]
}
```

The future axis editor should use the same contract:

```js
{
  id: "moment-axis-editor",
  appKinds: ["manage"],
  scopeIds: ["moments"]
}
```

An omitted or empty `scopeIds` list means that the definition is not narrowed by scope.
Scope ids remain configuration identities; definitions must not infer eligibility from route paths such as `/analysis/` or `/moments/`.

## Required Behavior

- The view registry receives the current dynamic viewer scope as a projection input.
- Scope eligibility is evaluated alongside existing app-kind, feature, capability, and route-policy checks.
- An ineligible definition projects a named `scope` unavailability reason.
- Changing managed scope reprojects eligible controls and hosted views.
- A configured default info view falls back safely when it is not eligible in the active scope.
- The Markdown source editor remains available wherever its existing route and backend contracts allow it; only the semantic picker is Analysis-specific.

## Verification

Focused registry and coordinator checks should prove:

- managed Analysis can resolve and open `semantic-token-picker`
- managed Studio, Library, and Moments cannot resolve it as available
- public Analysis cannot load the manage-only picker
- a representative Moments-only definition is available in managed Moments and unavailable elsewhere
- switching away from an eligible scope does not leave the previous scope-specific hosted view active

## Change Boundary

This task adds frontend scope eligibility.
It does not grant write authority, add the axis editor, redesign route configuration, or introduce arbitrary conditional expressions into config.
Source writes remain protected by the existing manage-only service and backend capability contracts.

## Documentation Boundary

This delivery is the single owner of the unresolved `scopeIds` proposal and its verification. Do not distribute the proposed rule across configuration, runtime, workspace, and capability documents before it ships.

If implemented, [Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts) will absorb the stable scope-eligibility rule, extension method, and any known weakness because the rule belongs to the code-owned view/mode/control registry. This delivery should then retain only unresolved follow-up work or be deleted.

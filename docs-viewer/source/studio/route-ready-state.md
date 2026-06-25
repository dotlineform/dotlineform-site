---
doc_id: route-ready-state
title: Route Ready State
added_date: 2026-06-25
last_updated: 2026-06-25
parent_id: change-requests
viewable: true
---
# Route Ready State

## Related Ready-State References

Core references:

- [Studio Route State](/docs/?scope=studio&doc=studio-ready-state) documents the implemented Studio route-ready contract, helper API, route inventory, smoke wait pattern, and current audit coverage.
- [Browser Smoke Testing](/docs/?scope=studio&doc=smoke-testing) defines when browser smokes should use route ready/busy state and records the current gap this change request is closing.
- [Testing](/docs/?scope=studio&doc=testing) places shared ready/busy contracts in the broader test policy and profile guidance.
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime) describes route script ownership, including route-ready state, data loading, event binding, and local API coordination.
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state) documents the current Studio-only audit and its strict-mode checks.
- [Audit Runner](/docs/?scope=studio&doc=audit-runner), [Audits](/docs/?scope=studio&doc=audits), and [Run Checks](/docs/?scope=studio&doc=scripts-run-checks) describe how the ready-state audit is exposed through Admin tooling and profiles.

Route contract examples:

- Studio routes: [Catalogue Works](/docs/?scope=studio&doc=studio-works), [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor), [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor), [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor), [Catalogue Drafts](/docs/?scope=studio&doc=catalogue-status), [Catalogue Field Registry Review](/docs/?scope=studio&doc=catalogue-field-registry-review), [Bulk Add Work](/docs/?scope=studio&doc=bulk-add-work), [Project State](/docs/?scope=studio&doc=project-state-page), and [Activity](/docs/?scope=studio&doc=activity).
- Analytics routes: [Series Tag Editor](/docs/?scope=studio&doc=tag-editor), [Series Tags](/docs/?scope=studio&doc=series-tags), [Tag Registry](/docs/?scope=studio&doc=tag-registry), [Tag Aliases](/docs/?scope=studio&doc=tag-aliases), and [Tag Groups](/docs/?scope=studio&doc=tag-groups).
- Docs Viewer import route: [Docs HTML Import](/docs/?scope=studio&doc=user-guide-docs-html-import).
- Static route templates: [Admin Static Route Template](/docs/?scope=studio&doc=admin-static-route-template) and [Analytics Static Route Template](/docs/?scope=studio&doc=analytics-static-route-template).

We need to turn “some routes expose readiness” into an enforced route lifecycle contract across Studio, Admin, Analytics, and Docs Viewer.

The practical work is:

1. **Define the contract once**
   Document the canonical meaning of:
   - `ready=false`: route is mounted but not safe for interaction yet
   - `busy=true`: route is doing initial load, save, import, audit run, or other blocking async work
   - `ready=true` + `busy=false`: route is stable enough for browser smokes and dependent UI
   - stable failure state: failed/unavailable routes should still become `ready=true`, with `service=unavailable` or equivalent, once the error UI is rendered

2. **Settle the attribute naming**
   Current state is app-prefixed:
   - Studio: `data-studio-ready`, `data-studio-busy`
   - Admin: `data-admin-ready`, `data-admin-busy`
   - Analytics: `data-analytics-ready`, `data-analytics-busy`
   - Docs Viewer: mixed local state, no consistent route-level contract everywhere

   I would keep app-prefixed attributes for now and standardize the semantics. Adding generic aliases like `data-route-ready` would create duplicate contracts unless we deliberately migrate everything.

3. **Inventory every app route**
   For each route template, identify:
   - root selector
   - owning app
   - expected ready/busy attributes
   - controller/module responsible for transitions
   - initial async work
   - write/import/run actions that should set busy
   - stable error/unavailable state

4. **Patch missing templates**
   Every route root should start with:
   - `ready="false"`
   - `busy="false"`

   Static/home routes can become ready immediately, but the initial template should still expose the baseline consistently unless there is a specific reason not to.

5. **Patch controllers to drive state**
   Each route script needs to:
   - initialize route state after mount
   - set `busy=true` before blocking async work
   - set `busy=false` in `finally`
   - set `ready=true` after successful render or stable unavailable/error render
   - avoid leaving `ready=false` forever on fetch/config/service failure

6. **Validate templates during route loading**
   Studio already does this in [studio-route-templates.js](/Users/dlf/Developer/dotlineform/dotlineform-site/studio/app/frontend/js/studio-route-templates.js). Admin and Analytics loaders currently parse templates but do not enforce ready/busy roots. They should get equivalent validation in:
   - [admin-route-templates.js](/Users/dlf/Developer/dotlineform/dotlineform-site/admin-app/app/frontend/js/admin-route-templates.js)
   - [analytics-route-templates.js](/Users/dlf/Developer/dotlineform/dotlineform-site/analytics-app/app/frontend/js/analytics-route-templates.js)

7. **Expand the audit**
   The current audit is Studio-only: [audit_studio_ready_state.py](/Users/dlf/Developer/dotlineform/dotlineform-site/admin-app/checks/audit_studio_ready_state.py). To close the gap, add cross-app audits for Admin, Analytics, and Docs Viewer route templates, or replace it with a general `audit_route_ready_state.py` that uses per-app config.

8. **Normalize smoke helpers**
   Smoke tests should use a shared helper shape:

   ```python
   wait_for_route_ready(page, root_selector, ready_attr, busy_attr)
   ```

   Then Studio/Admin/Analytics/Docs Viewer smokes can stop hand-rolling waits and route-specific timing guesses.

9. **Add focused route-ready smokes only where useful**
   The goal is not a huge UI test suite. Add narrow smokes for routes where the contract protects real integration risk: route boot, module load, API reachability, and stable unavailable states.

10. **Update docs and remove the gap**
   Once all owned routes are audited and smoke helpers use the contract, update [smoke-testing.md](/Users/dlf/Developer/dotlineform/dotlineform-site/docs-viewer/source/studio/smoke-testing.md) to replace the current gap with the maintained rule and audit command.

Definition of done: every app route has a documented root, starts with ready/busy attributes, reaches `ready=true` on success or stable failure, clears busy reliably, is covered by a template audit, and browser smokes wait on the shared contract instead of timing or ad hoc loaded text.

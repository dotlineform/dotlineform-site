---
doc_id: route-ready-state-tasks
title: Route Ready State Tasks
added_date: 2026-06-09
last_updated: 2026-06-09
parent_id: route-ready-state
viewable: true
---
# Route Ready State Tasks

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

3. **Inventory every app route** — done for active route roots
   For each route template, identify:
   - root selector
   - owning app
   - expected ready/busy attributes
   - controller/module responsible for transitions
   - initial async work
   - write/import/run actions that should set busy
   - stable error/unavailable state

4. **Patch missing templates** — done for Docs Viewer public/manage shells
   Every route root should start with:
   - `ready="false"`
   - `busy="false"`

   Static/home routes can become ready immediately, but the initial template should still expose the baseline consistently unless there is a specific reason not to.

   Docs Viewer public/manage shells now expose `data-docs-viewer-ready="false"` and `data-docs-viewer-busy="false"` on `#docsViewerRoot`.

5. **Patch controllers to drive state** — partly done for Docs Viewer shell startup
   Each route script needs to:
   - initialize route state after mount
   - set `busy=true` before blocking async work
   - set `busy=false` in `finally`
   - set `ready=true` after successful render or stable unavailable/error render
   - avoid leaving `ready=false` forever on fetch/config/service failure

   Docs Viewer shell boot now sets `data-docs-viewer-busy` during initial startup and marks `data-docs-viewer-ready="true"` after startup reaches a stable success or error state.
   Remaining work: review route-level command busy projection across app controllers and Docs Viewer management actions.

6. **Validate templates during route loading**
   Studio already does this in `studio/app/frontend/js/studio-route-templates.js`. Admin and Analytics loaders currently parse templates but do not enforce ready/busy roots. They should get equivalent validation in:
   - `admin-app/app/frontend/js/admin-route-templates.js`
   - `analytics-app/app/frontend/js/analytics-route-templates.js`

7. **Expand the audit**
   The current audit is Studio-only: `admin-app/checks/audit_studio_ready_state.py`. To close the gap, add cross-app audits for Admin, Analytics, and Docs Viewer route templates, or replace it with a general `audit_route_ready_state.py` that uses per-app config.

8. **Normalize smoke helpers**
   Smoke tests should use a shared helper shape:

   ```python
   wait_for_route_ready(page, root_selector, ready_attr, busy_attr)
   ```

   Then Studio/Admin/Analytics/Docs Viewer smokes can stop hand-rolling waits and route-specific timing guesses.

9. **Add focused route-ready smokes only where useful**
   The goal is not a huge UI test suite. Add narrow smokes for routes where the contract protects real integration risk: route boot, module load, API reachability, and stable unavailable states.

10. **Update docs and remove the gap**
   Once all owned routes are audited and smoke helpers use the contract, update [Browser Smoke Testing](/docs/?scope=studio&doc=smoke-testing) to replace the current gap with the maintained rule and audit command.

Definition of done: every app route has a documented root, starts with ready/busy attributes, reaches `ready=true` on success or stable failure, clears busy reliably, is covered by a template audit, and browser smokes wait on the shared contract instead of timing or ad hoc loaded text.

---
doc_id: studio-audits
title: Studio Audits
added_date: 2026-05-03
last_updated: "2026-05-06 20:51"
parent_id: studio
sort_order: 50
---
# Studio Audits

Route:

- `/studio/audits/`

The Studio Audits page surfaces local maintenance audits inside Studio.

The first version lists the Studio ready-state audit and provides a Run command. Results show pass/fail state, exit code, warning/error counts, run timestamp, findings when present, and a collapsible raw output block for debugging.

## Runtime

The page uses:

- `studio/audits/index.md`
- `assets/studio/js/studio-audits.js`
- `assets/studio/js/studio-transport.js`
- `scripts/studio/audit_service.py`
- `scripts/checks/audit_studio_ready_state.py`

Visible runtime copy lives under `ui_text.studio_audits` in `assets/studio/data/studio_config.json`.

The local service endpoint definitions live in `assets/studio/js/studio-transport.js`, matching the existing Studio transport pattern.

## Ready State

The route root is `#studioAuditsRoot`.

The page exposes:

- `data-studio-route="studio-audits"`
- `data-studio-ready`
- `data-studio-busy`
- `data-studio-mode="summary|running|result|unavailable"`
- `data-studio-service="available|unavailable"`

The page marks busy while an audit run is in progress and returns to ready after the service response or request failure settles.

## Service Behavior

When the audit service is unavailable, the page stays readable, disables the Run command, and exposes `data-studio-service="unavailable"`.

When the service is available, the page fetches `/audits` to list allowlisted audits. It currently expects:

- `studio-ready-state`

Running the audit posts only the audit ID to `/audits/run`. The browser never sends command text, paths, shell flags, environment variables, or working directories.

## Related References

- [Studio Audit Service](/docs/?scope=studio&doc=scripts-studio-audit-service)
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
- [Studio Audits Page Request](/docs/?scope=studio&doc=site-request-studio-audits-page)

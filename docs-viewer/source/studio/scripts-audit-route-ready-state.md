---
doc_id: scripts-audit-route-ready-state
title: Route Ready-State Audit
added_date: 2026-06-25
last_updated: 2026-07-15
parent_id: admin
---
# Route Ready-State Audit

## Question It Answers

Do current Studio, Admin, Analytics, and Docs Viewer templates expose one consistent app-owned ready/busy root?

The audit validates the static template baseline. It does not prove that every controller reaches ready state at runtime.

## Run It

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_route_ready_state.py --strict
```

Limit investigation to one or more apps:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_route_ready_state.py --strict --app admin
```

Valid IDs come from `APP_CONFIGS` in the script. `--json` is the structured mode used by the [Audit Runner](/docs/?scope=studio&doc=audit-runner).

## Contract Checked

For each configured template the audit expects:

- exactly one app-prefixed ready-state root;
- the matching busy attribute on that same element;
- busy initially `false`;
- ready initially `false`, except for explicitly allowlisted static home templates.

Template globs, attribute names, and initial-ready exceptions are code-owned in `APP_CONFIGS`. The broader lifecycle and controller responsibilities are explained in [Route Ready State](/docs/?scope=studio&doc=route-ready-state).

## Interpretation

- errors always fail;
- strict mode also fails warnings;
- missing configured templates, duplicate roots, invalid boolean values, and mismatched ready/busy ownership are structural failures;
- runtime loading, error recovery, and stale-request behaviour require focused service or browser-boundary tests.

The `quick` check profile includes this audit. Run the direct command when template ownership is the only contract that changed.

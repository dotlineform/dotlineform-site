---
draft: false
doc_id: d-20260625-174523-74cf61
title: Route Ready-State Audit
added_date: "2026-06-25 17:45:23"
last_updated: "2026-10-11 00:00:00"
parent_id: d-20260501-174746-efd581
---
# Route Ready-State Audit

## Question It Answers

Do current Studio and Docs Viewer templates expose one consistent app-owned ready/busy root?

The audit validates the static template baseline. It does not prove that every controller reaches ready state at runtime.

## Run It

```bash
python3 tests/audits/route_ready_state.py --strict
```

Limit investigation to one or more apps:

```bash
python3 tests/audits/route_ready_state.py --strict --app studio
```

Valid IDs come from `APP_CONFIGS` in the script. Use `--json` when a structured result is useful for automation or focused diagnosis.

## Contract Checked

For each configured template the audit expects:

- exactly one app-prefixed ready-state root;
- the matching busy attribute on that same element;
- busy initially `false`;
- ready initially `false`.

Template globs and attribute names are code-owned in `APP_CONFIGS`. There is no initial-ready exception. The broader lifecycle and controller responsibilities are explained in [Route Ready State](Route_Ready_State.md); [Studio Frontend Retirement](Testing.md#studio-frontend-retirement) records the approved removal of the obsolete home-route exception and the current focused coverage.

## Interpretation

- errors always fail;
- strict mode also fails warnings;
- missing configured templates, duplicate roots, invalid boolean values, and mismatched ready/busy ownership are structural failures;
- runtime loading, error recovery, and stale-request behaviour require focused service or browser-boundary tests.

The `quick` check profile includes this audit. Run the direct command when template ownership is the only contract that changed.

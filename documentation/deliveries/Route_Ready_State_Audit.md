---
draft: false
doc_id: d-20260625-174523-74cf61
title: Route Ready-State Audit
added_date: "2026-06-25 17:45:23"
last_updated: "2026-10-11 00:00:00"
parent_id: d-20261118-235200-9870c4
---
# Route Ready-State Audit

Historical record of the static route markup audit retired with the site suite. [Current contract](../reference/Route_Ready_State.md) · [Site test retirement](Review_Test_Policy_And_Checks.md#recovery)

## Question It Answers

Did the configured Studio and Docs Viewer templates expose one consistent app-owned ready/busy root?

The audit validated static template markup. Run-time readiness still required exercising the route.

## Former Commands

```bash
python3 tests/audits/route_ready_state.py --strict
```

The focused Studio selection was:

```bash
python3 tests/audits/route_ready_state.py --strict --app studio
```

App IDs came from `APP_CONFIGS`. The former `--json` flag emitted structured findings.

## Contract Checked

For each matched template the audit expected:

- exactly one app-prefixed ready-state root;
- the matching busy attribute on that same element;
- busy initially `false`;
- ready initially `false`.

The Studio frontend retirement removed the obsolete home-route initial-ready exception. The audit skipped absent templates and omitted the installed public entrypoint and Docs Review. [Studio retirement evidence](Studio_And_Catalogue_Ownership_Review.md#studio-retirement-evidence)

## Interpretation

- Errors failed the audit. Strict mode also failed on warnings.
- Duplicate roots, invalid boolean values and mismatched ready/busy ownership were structural findings.
- Runtime loading, error recovery and stale-request behaviour were outside the static audit.

The former `quick` profile selected this audit.

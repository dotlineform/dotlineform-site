---
doc_id: admin-checks-target-map-architecture
title: Target Map Architecture
added_date: 2026-06-09
last_updated: 2026-07-15
parent_id: admin-checks
viewable: true
---
# Target Map Architecture

## Stable Structure

```text
admin-checks.json
  -> admin_checks_config.py validates policy
  -> target_map_resolver.py resolves source files and boundary flags
     -> audit_target_map.py reviews config health across the repository
     -> reports/target_map.py answers one selected run question
```

The audit and report have different purposes but must share resolution mechanics.

## Maintenance Audit

`audit_target_map.py` asks whether the maintained map still fits the repository:

- which patterns are stale or unexpectedly broad;
- which files are unclassified or likely unmapped;
- where files match several families, areas, or routes;
- which dependencies are shared across targets;
- whether route inventory and ownership need review.

It normally inspects the whole config and may write a local maintenance snapshot under `var/admin/checks/target-map-audit/`.

The audit is not a user-selected report and should not change behavior based on one checks run.

## Run-Scoped Report

The `target-map` report asks how files in one selected scope/filter set are classified. It runs through `run_reports.py`, writes ordinary report artifacts under the run ID, and appears in Admin Checks.

It is evidence rather than pass/fail policy. Cross-route or cross-area files may be valid shared infrastructure; the report makes them visible for review.

## Resolver Contract

The resolver owns:

- source-file discovery after exclusions;
- direct and shared matches for scopes/families/areas/routes;
- selected target intersection;
- pattern status;
- unclassified and boundary flags;
- structured counts and file rows for both callers.

Neither caller should reimplement glob matching or infer shared dependencies independently.

## Artifact Ownership

- durable target policy: `admin-app/checks/config/`;
- shared implementation: config loader and target-map resolver;
- maintenance snapshot: `var/admin/checks/target-map-audit/`;
- selected report evidence: `var/admin/checks/<run-id>/target-map/`.

Do not commit a resolved per-file map as permanent architecture. It would immediately create another inventory that must be updated for every move.

## Weak Spots

- Route discovery and route ownership are not yet cleanly separated in the config lifecycle.
- Broad patterns can conceal missing focused mappings.
- The all-repo scope is useful for maintenance but easy to mistake for a meaningful product boundary.
- Boundary flags identify review candidates; without a decision/action workflow they can become another accumulating dashboard.

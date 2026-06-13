---
doc_id: scripts-audit-projection-contract
title: Projection Contract Validation
added_date: 2026-05-23
last_updated: 2026-05-30
parent_id: architecture
viewable: true
---
# Projection Contract Audit

[this doc and the script needs reviewing]

Script:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_projection_contract.py
```

This check validates the Phase 6 source/projection contract used by the Local Studio migration.

The manifest is `admin-app/checks/projection_contract.json`.
It is the machine-readable source of truth for cross-domain artifact classification, public-build policy, source-only leak rules, owner docs, and public Docs Viewer scope policy.

## Common Runs

Validate the manifest, `_config.yml` exclusion policy, and checked-in public JSON leak rules:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_projection_contract.py
```

Audit a built public site from the same manifest:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_projection_contract.py --site-root /tmp/dlf-...
```

The legacy public-surface audit wrapper now uses the same manifest-backed public build audit:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_public_build_surface.py --site-root /tmp/dlf-...
```

## What It Checks

- manifest schema version, family ids, classifications, owner docs, path lists, public-output policies, and duplicate path declarations
- checked-in public JSON/search projections for fields listed in manifest `field_leak_rules`
- public templates and public browser assets for forbidden Studio-only source/projection references listed in manifest `public_source_reference_audit`
- built public output for required and forbidden public-output families when `--site-root` is supplied
- public Docs Viewer config scope ids when `--site-root` is supplied
- forbidden public HTML links such as `/studio/` and local `/docs/` management links when `--site-root` is supplied

## Boundary

This script owns the cross-domain projection classification check.
It does not replace domain-specific configs:

- Docs Viewer scope build details stay in `docs-viewer/config/scopes/docs_scopes.json`
- search source-family behavior stays in `scripts/search/build_config.json`
- catalogue field-aware build scoping stays in `studio/data/config/catalogue/catalogue-field-registry.json`

The projection contract audit checks those systems at the public/local boundary.

## Update Rule

When adding a source family, generated payload, local working output, public runtime asset, Studio-only artifact, Analytics app artifact, or UI Catalogue app artifact, classify it in `admin-app/checks/projection_contract.json`.

When a field becomes source-only, add it to a manifest `field_leak_rules` entry with the public paths that must not contain it.
Do not add fields to leak rules if they are still intentionally present in current public runtime payloads.

When a public template or browser asset needs to reference a new generated path, classify that path first and keep public reads pointed at public projections rather than Studio-only source or lookup data.

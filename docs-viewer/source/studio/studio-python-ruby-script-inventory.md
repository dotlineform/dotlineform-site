---
doc_id: studio-python-ruby-script-inventory
title: Studio Python And Ruby Script Inventory
added_date: 2026-05-19
last_updated: 2026-05-31
ui_status: reference
parent_id: audit
viewable: true
---
# Studio Python And Ruby Script Inventory

This document records detailed transition evidence for maintenance, structure/consistency, and performance risk in Python and Ruby script families.

It follows [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy), but uses script-family ownership rather than browser payload size as the primary review unit.
Use [Studio Risk Priority Dashboard](/docs/?scope=studio&doc=studio-risk-priority-dashboard) for the current short priority order before reading the full inventory.

## Transition Status

Use the app inventories and active change requests for current priority and implementation ownership:

- [Studio App Risk Inventory](/docs/?scope=studio&doc=studio-app-risk-inventory)
- [Docs Viewer Risk Inventory](/docs/?scope=studio&doc=docs-viewer-risk-inventory)
- [Analytics Risk Inventory](/docs/?scope=studio&doc=analytics-risk-inventory)
- [Public Site Risk Inventory](/docs/?scope=studio&doc=public-site-risk-inventory)
- [Catalogue Save Build Diagnostics Request](/docs/?scope=studio&doc=site-request-catalogue-save-build-diagnostics)
- [Docs Viewer Runtime Risk Reduction Request](/docs/?scope=studio&doc=site-request-docs-viewer-runtime-risk-reduction)
- [Analytics Data Sharing Growth Path Request](/docs/?scope=studio&doc=site-request-analytics-data-sharing-growth-path)

This page remains as script-family evidence, guardrails, rerun instructions, and largest-file watch context.
Do not use it as a separate backend/script priority queue.
When a family becomes actionable, move the app-level evidence into the owning app inventory or change request.

## Current Priority

1. Add catalogue save/build diagnostics for the repeated local write paths: source writes, lookup refreshes, generated artifact groups, search updates, media work, elapsed time, and fallback reasons.
2. Use those catalogue diagnostics to reduce conservative rebuilds where field-aware metadata can safely identify smaller generated artifact, lookup, search, or media scopes.
3. Add media-derivation timing and count diagnostics, then evaluate bounded parallelism or batched freshness checks only for the slow paths the diagnostics identify.
4. Treat docs rebuild work as monitoring mode for now: keep the current targeted payload/search contract stable, and revisit remaining full-scope fallbacks only when diagnostics show a repeated cost.
5. Keep orchestration files from regrowing, standardize local service mechanics only where contracts are identical, and group broad audit scripts before adding more unrelated checks.

The next implementation plan should start with catalogue diagnostics, not another broad structural split.
The useful sequence is visibility first, then targeted reductions in generated artifact, search, and media work based on measured local-service behavior.

## Structure Guardrails

- New catalogue generated payload behavior belongs in `studio/services/catalogue/catalogue_generation_*`, `catalogue_lookup*`, or source-model modules, not directly in write-server handlers.
- New docs source mutation behavior belongs in `docs_management_mutations.py`, source config/settings modules, or import-source services, not directly in the HTTP server.
- New tag assignment, registry, alias, promotion, or Data Sharing behavior belongs in `analytics-app/app/server/analytics_app/tag_services/` and the Analytics API/Data Sharing adapters, not in Studio service scripts or standalone service scripts.
- New local-service behavior should preserve explicit write allowlists, dry-run semantics, backup paths, and compact logging.
- New rebuild performance work should first expose counts and fallback reasons, then optimize the path with the highest measured cost.
- New command examples in docs should use project-local script paths from `dotlineform-site/`.

## Classification

Each area is classified as high, medium, or low for:

- Maintenance risk: how likely future changes are to require broad local knowledge or carry hidden side effects.
- Structure and consistency risk: how much the area diverges from established module ownership, command shape, testability, logging, backup, or write-safety patterns.
- Performance risk: how likely the area is to add avoidable runtime cost through repeated full scans, subprocess calls, repeated JSON loads/writes, serial media work, or coarse rebuilds.

These are risk classifications, not quality scores.
High means the area should be considered for near-term improvement when related work is opened.
Medium means watch it and improve opportunistically.
Low means no immediate structural or performance action is recommended.

This review is static.
Performance risk is inferred from script shape, file size, subprocess usage, and rebuild boundaries; it is not a timing benchmark.

## Current Summary

Measured on 2026-06-01 with `studio/checks/risk_evidence_pack.py` script-family inventory:

- Python and Ruby scripts under active Studio, Docs Viewer, Analytics, and Data Sharing roots: 156
- Python scripts: 156
- Ruby scripts: 0
- Total Python/Ruby script lines: 48,174
- Files over the 1,000-line review threshold: 8
- Largest script family by lines: `studio/services/catalogue/`
- Largest individual script: `docs-viewer/services/docs_html_import.py`

The inventory roots no longer include active app-facing Ruby builder entrypoints.
Ruby/Bundler/Jekyll remains the public-site preview/build layer through `Gemfile`, `Gemfile.lock`, `.ruby-version`, `bin/public-site-preview`, and `bin/public-site-build`; that public-site boundary is tracked separately from app runtime script risk.

The script surface is now better structured than the raw size suggests.
The previous structural-review work extracted major catalogue write-server, Docs management service, tag write-server, generator, and scoped-build responsibilities into named module owners.
The remaining risk is less about one obvious file to split and more about keeping future changes inside the right owner, reducing repeated rebuild work, and standardizing command and service mechanics.

## Family Risk Matrix

| Area | Files | Lines | Maintenance | Structure and consistency | Performance | Main reason |
| --- | ---: | ---: | --- | --- | --- | --- |
| `studio/services/catalogue/` | 48 | 17,013 | high | medium | high | Large source/build/write surface with multiple generated artifact families, field-aware build planning, media derivation, lookup refreshes, Python catalogue search rebuilds, publication flows, prose rendering, and local write-service orchestration. |
| `docs-viewer/` | 34 | 13,266 | high | medium | medium | Docs build, import, export, management mutations, generated reads, live rebuild, and docs search are now Python-owned. Targeted docs payload/search rebuilds reduce routine write cost, while builder/watcher/management contracts and resolver-data fallbacks still need care. |
| `studio/` | 18 | 5,165 | medium | medium | low | Command-owned registries and helper entrypoints such as `studio/commands/run_checks.py` should remain orchestration surfaces rather than owning domain behavior. |
| `studio/checks/` | 10 | 3,647 | medium | medium | medium | Audit scripts intentionally span many site contracts, especially `audit_site_consistency.py`; risk grows when new checks are added without grouping or shared report contracts. |
| `analytics-app/app/server/analytics_app/` | 9 | 2,653 | medium | medium | low | Analytics API and Data Sharing dispatch stay Python-owned; keep route adapters thin and domain behavior in focused helper modules. |
| `studio/app/server/studio/` | 8 | 2,352 | medium | medium | low | Shared Studio services are small, but catalogue, audit, risk, and Activity mechanics overlap with docs and catalogue services. |
| `analytics-app/app/server/analytics_app/tag_services/` | 10 | 2,131 | medium | medium | low | Analytics-owned tag helper package for source path contracts, validation, planning, dry-run/write transactions, backups, route constants, and compact activity projection. Data Sharing and tag import/apply flows remain broad enough to watch. |
| `data-sharing/` | 19 | 1,947 | medium | medium | low | Headless Data Sharing adapters are Python-owned and should keep package I/O, adapter registry behavior, and apply boundaries explicit. |

## Highest Priority Areas

### Catalogue build and write path

| Criterion | Classification |
| --- | --- |
| Maintenance risk | high |
| Structure and consistency risk | medium |
| Performance risk | high |

Relevant files:

- `studio/services/catalogue/catalogue_write_service.py`
- `studio/services/catalogue/generate_work_pages.py`
- `studio/services/catalogue/catalogue_json_build.py`
- `studio/services/catalogue/catalogue_build_media.py`
- `studio/services/catalogue/catalogue_lookup_refresh.py`
- `studio/services/catalogue/catalogue_generation_*`

The immediate maintenance risk is the breadth of the catalogue workflow.
A single Studio save can touch canonical source JSON, backups, lookup refreshes, generated public JSON, route stubs, search rebuilds, media derivatives, publication state, and Studio Activity rows.
The completed extraction work gives many of those responsibilities explicit owners, but the workflow still requires careful coordination when adding fields, generated artifacts, or write-server endpoints.

The main performance risk is rebuild scope.
The field-aware build plan and focused lookup refresh work are the right direction, but future changes should keep reducing conservative full-fallback behavior where the field registry can safely identify smaller artifact sets.
Media derivation is also expensive because image tasks invoke external commands and check source/output freshness repeatedly.

Recommended improvements:

- Keep expanding field-aware build coverage for saves that still fall back to broad generated artifact work.
- Add lightweight timing or count diagnostics for save-triggered media, generation, lookup, and search steps so slow paths are visible in local service responses.
- Keep generated artifact ownership in the existing `catalogue_generation_*` modules; do not add new record shaping or index construction directly to `generate_work_pages.py`.
- Keep catalogue write behavior in focused service modules and avoid adding generated artifact planning back into HTTP/API adapters.
- Review whether media planning can batch freshness checks or run independent derivative operations concurrently without weakening dry-run/write behavior.

Immediate work signal: high.

### Docs build, management, import, and export path

| Criterion | Classification |
| --- | --- |
| Maintenance risk | high |
| Structure and consistency risk | medium |
| Performance risk | medium |

Relevant files:

- `docs-viewer/build/build_docs.py`
- `docs-viewer/services/docs_html_import.py`
- `docs-viewer/services/docs_export.py`
- `docs-viewer/services/docs_import.py`
- `docs-viewer/services/docs_management_mutations.py`
- `docs-viewer/services/docs_management_service.py`
- `docs-viewer/services/docs_viewer_service.py`
- `docs-viewer/services/docs_live_rebuild_watcher.py`
- `docs-viewer/build/build_search.py`

Docs have been moving out of the cross-language ownership risk that originally motivated this inventory.
Python now owns the generated Docs Viewer payload builder, management writes, imports, exports, generated reads, live rebuild orchestration, and source configuration writes.
Python also owns Docs Viewer search generation after the Rubyless app-runtime cleanup removed the retired Ruby entrypoint.
The remaining consistency risk is keeping source rules, generated payload shape, search behavior, management responses, and docs-watch behavior aligned as the Python builders evolve.

The remaining performance risk is fallback visibility, not a missing targeted-build contract.
The builder now accepts targeted same-scope docs payload ids, and docs-management, source import, Library returned-package apply, and watcher paths use those ids when dependency rules are explicit.
Explicit rebuilds, source-config settings changes, missing generated output, ambiguous watcher changes, and resolver-data changes outside docs source intentionally fall back to full same-scope docs payload rebuilds.
As Library and Studio docs grow, the diagnostics added to rebuild responses and watcher logs are the way to tell whether those intentional fallbacks are actually expensive.

Current guardrails and watch points:

- source config, generated reads, mutations, import/export adapters, and rebuild orchestration already have current Python owners; avoid moving that behavior back into the HTTP service layer
- Docs management transport and endpoint dispatch remain current architecture in `docs-viewer/services/docs_viewer_service.py`, `docs-viewer/services/docs_management_service.py`, and `docs-viewer/services/docs_management_routes.py`; endpoint behavior should stay in focused read, capability, mutation, import, source, rebuild, or audit service modules before being wired through the dispatcher
- the `build_docs.py --only-doc-ids` contract is intentionally same-scope only, caller-owned for affected ids, and backed by full fallback when generated output or dependency data is incomplete
- rebuild diagnostics already expose source files scanned, docs emitted, item payloads changed, references changed, search records touched, and elapsed time in rebuild responses or logs
- resolver-data changes outside docs source, such as catalogue title or route changes, remain full-scope until a future change defines explicit affected-id rules for them
- Python builder and management response contracts should stay documented together when generated Docs Viewer schema changes

Immediate work signal: medium.

Completed implementation record: [Docs Build Management Import Export Improvements](/docs/?scope=studio&doc=docs-build-management-import-export-improvements).

### Media derivation and remote publishing

| Criterion | Classification |
| --- | --- |
| Maintenance risk | medium |
| Structure and consistency risk | medium |
| Performance risk | high |

Relevant files:

- `studio/services/media/make_srcset_images.py`
- `studio/services/media/publish_media_to_r2.py`
- `studio/services/catalogue/catalogue_build_media.py`

Media scripts are smaller than catalogue and docs scripts, but their performance risk is high because they are external-command and file-I/O heavy.
They also depend on local environment values, source image location, derivative naming, accepted legacy sizes, and R2 credentials.

Retired media tooling:

- `studio/retired/thumbnail-quality/build_thumbnail_quality_preview.py`

Recommended improvements:

- Keep `DOTLINEFORM_PROJECTS_BASE_DIR` and pipeline config as the source of truth for media source and size policy.
- Add batch-level timing and per-step counts to media reports.
- Evaluate parallel derivative generation for independent images or widths, with bounded concurrency and unchanged dry-run behavior.
- Keep remote R2 publishing isolated from local derivative generation so credential handling does not spread into catalogue build modules.
- Consolidate repeated freshness and path-display helpers only after the catalogue/media boundary is clear.

Immediate work signal: medium for maintainability, high for performance when media batches grow.

### Cross-service local server mechanics

| Criterion | Classification |
| --- | --- |
| Maintenance risk | medium |
| Structure and consistency risk | medium |
| Performance risk | low |

Relevant files:

- `studio/services/catalogue/catalogue_write_service.py`
- `docs-viewer/services/docs_viewer_service.py`
- `docs-viewer/services/docs_management_service.py`
- `studio/app/server/studio/studio_audit_api.py`
- `studio/app/server/studio/audit_runner.py`
- `studio/shared/python/script_logging.py`
- `studio/shared/python/studio_activity.py`

The local services share a pattern: loopback-only HTTP, CORS checks, JSON request parsing, write allowlists, backups, local logs, dry-run responses, and Studio Activity rows.
Studio audit execution is now a direct runner plus local app API adapter rather than a sibling HTTP service.
The services are currently domain-specific enough that a broad shared framework would be premature, but repeated mechanics can drift.

Recommended improvements:

- Standardize request-size limits, JSON parse errors, CORS response headers, and local log event fields across local services.
- Keep service-specific write allowlists visible in each service.
- Extract only tiny shared helpers where the contract is identical across services.
- Keep Activity row construction domain-owned, with shared infrastructure limited to append, feed, and contract normalization helpers.

Immediate work signal: medium.

### Check and audit scripts

| Criterion | Classification |
| --- | --- |
| Maintenance risk | medium |
| Structure and consistency risk | medium |
| Performance risk | medium |

Relevant files:

- `studio/checks/audit_site_consistency.py`
- `studio/checks/audit_studio_ready_state.py`
- `studio/checks/css_token_audit.py`
- `studio/checks/check_runtime_payload_budgets.py`
- `studio/commands/run_checks.py`

Audit scripts intentionally cut across the repo, so they will always have broader source knowledge than a domain script.
The risk is that new checks get appended as unrelated logic without shared output shape, sampling rules, or profile integration.

Recommended improvements:

- Group `audit_site_consistency.py` checks by source family and report section before adding many more checks.
- Keep check output machine-readable first, with Markdown as a presentation layer.
- Add focused tests for check helpers when a check becomes complicated enough to have edge cases.
- Keep `run_checks.py` as the user-facing profile runner, but avoid making it own check logic directly.

Immediate work signal: medium.

## Largest File Watch List

| File | Lines | Maintenance | Structure and consistency | Performance | Notes |
| --- | ---: | --- | --- | --- | --- |
| `docs-viewer/services/docs_html_import.py` | 1,987 | high | medium | medium | Large conversion surface with HTML, Markdown, package, media, and preview behavior. Watch as import requirements expand. |
| `studio/services/catalogue/generate_work_pages.py` | 1,773 | high | medium | high | Generator orchestration remains broad. Keep new payload shaping in extracted generation modules and keep prose rendering on the shared Python Markdown helper. |
| `docs-viewer/build/build_docs.py` | 1,383 | high | medium | medium | Central Python docs builder. Targeted payload input and diagnostics are implemented; future risk is dependency-rule drift across builder, watcher, and management callers. |
| `studio/checks/audit_site_consistency.py` | 1,360 | medium | medium | medium | Broad audit surface. Grouping matters more than splitting by line count. |
| `data-sharing/data_sharing/adapters/tags/adapter.py` | 1,280 | medium | medium | low | Data Sharing apply paths remain adapter-owned and directly tested while delegating tag validation and writes to Analytics helpers. |
| `docs-viewer/services/docs_export.py` | 1,236 | medium | medium | medium | Export adapter grows with Data Sharing requirements. Keep profile/config behavior explicit. |
| `studio/services/catalogue/catalogue_build_media.py` | 1,184 | medium | medium | high | Local media planning/execution is a concrete performance improvement candidate. |
| `docs-viewer/services/docs_import.py` | 1,151 | medium | medium | medium | Returned-package parsing and preview writing should stay separated from source-apply services. |

## How To Rerun

Use [Studio Risk Evidence Pack](/docs/?scope=studio&doc=studio-risk-evidence-pack) for current deterministic reruns.
The old ad hoc `find`, `wc`, and inline Python snippets have been replaced by the `script-family-inventory.json` producer.

Run this from `dotlineform-site/`:

```bash
$HOME/miniconda3/bin/python3 studio/checks/risk_evidence_pack.py --app all --area script-family-inventory --write
```

Read:

```text
var/studio/risk/runs/<run-id>/script-family-inventory.json
```

When updating this doc from an evidence pack, keep the three risk classifications separate.
A large file can be low performance risk if it is rarely run, and a small file can be high performance risk if it sits on a repeated save or rebuild path.

## Related References

- [Studio](/docs/?scope=studio&doc=studio)
- [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Docs Semantic References Request](/docs/?scope=studio&doc=site-request-docs-semantic-references)
- [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

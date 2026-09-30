---
draft: false
doc_id: d-20260930-213926-a186b4
title: Collection Icons Delivery
added_date: "2026-09-30 21:39:26"
last_updated: "2026-09-30 21:39:26"
summary: Configure selected collection SVGs and use them for exact Index-panel hosts in local and public readers.
ui_status: in-progress
parent_id: d-20260930-195002-b3417e
---
# Collection Icons Delivery

## Requirements

Replace the generic Index-panel collection marker with the user-selected Catalogue, Concepts, Context and Moments SVGs. Store one extensionless `icon` value per existing configured collection so the future related-links builder can use the same selection. Preserve exact collection/host identity, current list-icon appearance and existing navigation. Related-links generation, ordinary-document index icons, native App work and test changes remain separate.

## Deliverables And Process

The workspace collection config owns selection; local/public browser settings project the filename and exact report host. The Index uses its already loaded configuration to select a decorative SVG mask. Manual tokens and collection configuration share one confined filename lookup. The four public SVG assets and changed shared JavaScript use the maintained site projection inventory. Config changes require browser-settings regeneration and runtime/artwork projection; no document or Search rebuild is needed.

## Delivery Steps

### CI-0 — Readiness

- [x] Confirm the user's filename mapping and existing config/sidebar/public owners.
- [x] Record approval for the config and Index slice, with related-links implementation deferred.

Gate: one bounded outcome, using existing configuration and list-icon styling. Verification budget: explicit lint and Python syntax for four Python and two JavaScript sources; production config loading and browser-config generation; required site-code projection/check and site validation; bounded source/diff/whitespace and asset inspection. Expected runtime is seconds, with normal lint/bytecode cache effects and intentional writes only to the three reader config files and inventoried site code/artwork. No tests, fixtures, browser/server operations, canonical document writes, Docs/Search builds or Publish are authorized or required. Visual fit remains user manual review.

### CI-1 — Implementation

- [x] Require and validate the configured SVG stems through the shared filename owner.
- [x] Project each collection icon and exact report host into local/public browser settings.
- [x] Render Index markers from the loaded host mapping, retaining existing size, tint and accessibility.
- [x] Regenerate reader configuration and project the four selected public SVGs and changed JavaScript.
- [x] Complete the selected static checks and documentation transfer.

Gate: the code and projected runtime are ready for bounded review. Record: explicit lint passed for the four Python and two JavaScript sources; Python compilation passed. Production configuration loaded all four selected icons; the existing writer regenerated local, public and site-public reader settings. `bin/site-code-update` added four SVGs and changed only the config controller and sidebar in this slice. `bin/site-code-update --check` confirmed 102 current projections, and `bin/site-validate` passed. Tracked/new source whitespace checks reported no issues. No tests, browser review, Docs/Search build, Publish, deployment, commit or push was performed.

### CI-2 — Code Review

- [x] Review configuration authority, filename/path validation, host lookup, local/public URL resolution, public projection and failure behaviour.
- [x] Resolve findings and rerun only affected evidence.

Gate: no blocking review findings. Record: review confirmed one checked filename owner, exact existing SVG confinement, public-safe icon/host projection and host lookup using already loaded settings. Module-relative SVG URLs match both the maintained local static routes and the tracked public layout. Shared list-icon CSS retains sizing/tint and the host link owns the accessible name. The inspected Working index has four collection-report rows matching the four configured hosts. Generated browser-config changes contain only the intended fields and JSON ordering; original user artwork was preserved. There is no fallback name, menu compatibility mode or second mapping. Static evidence does not establish browser appearance; manual visual acceptance remains pending.

### CI-3 — Closeout

- [ ] Record user manual acceptance of the four collection markers in the Index panel.
- [x] Transfer durable ownership to [Source Organisation](Source_Organisation.md#collection-icons) and update [Shared Icons](Shared_Icons.md) and the parent [Related Links](Related_Links.md).

Gate: manual visual acceptance. Retain this delivery through review; recommend archiving it after acceptance. No document is deleted automatically. The related-links directive remains proposed, and Publish, deployment, commit and push remain separate actions.

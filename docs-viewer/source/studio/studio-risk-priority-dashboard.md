---
doc_id: studio-risk-priority-dashboard
title: Studio Risk Priority Dashboard
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: review
parent_id: audit
viewable: true
---
# Studio Risk Priority Dashboard

This dashboard is the short decision surface for Studio maintenance-risk work.
Use it before reading the full inventories.

The source inventories remain the evidence:

- [JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory)
- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
- [Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory)

## Current Message

The next risk-reduction work should start with visibility and decision clarity, not another broad split.

The highest-value improvement is catalogue save/build diagnostics: make repeated write, generated artifact, lookup, search, and media costs visible, then reduce the measured broad fallbacks.
For JavaScript, the near-term priority is to reconcile stale or conflicting inventory rows before selecting a new score-reduction batch, then work by route family rather than by one long file table.

## Current Priorities

| Priority | Area | Unit | Main risk | Next action | Evidence of improvement |
| ---: | --- | --- | --- | --- | --- |
| 1 | Catalogue save/build path | Script family | Maintenance and performance | Add save/build diagnostics for source writes, lookup refreshes, generated artifacts, search updates, media work, elapsed time, and fallback reasons. | Local save/build responses or logs show per-step counts, elapsed time, and fallback reasons. |
| 2 | Catalogue generated/search/media rebuild scope | Script family | Performance | Use the diagnostics from priority 1 to reduce repeated broad generated artifact, lookup, search, or media work where field-aware metadata can safely narrow the scope. | A measured repeated broad path becomes a narrower path with the same dry-run/write behavior and focused verification. |
| 3 | JavaScript inventory reconciliation | Inventory quality | Planning risk | Reconcile the full JavaScript inventory with the Docs Viewer-specific inventory before starting another browser-JS batch. | Current scores, active paths, and Docs Viewer entry/runtime rows agree across the dashboard and source inventories. |
| 4 | Docs Viewer browser-JS controller boundaries | File family | Structural and architectural | Pick one complete controller family, such as management, bookmarks, search, or config, and narrow one remaining broad handoff to explicit owner inputs. | One above-target Docs Viewer row moves toward score 4 because a complete responsibility has a focused owner and tests or smoke coverage. |
| 5 | Media derivation and publishing path | Script family | Performance | Add batch-level media timing and counts, then evaluate bounded parallelism or batched freshness checks only for the measured slow path. | Media reports identify source count, derivative count, skipped count, elapsed time, and the slowest stage. |
| 6 | Cross-service local server mechanics | Cross-cutting family | Structure and consistency | Standardize only identical local-service mechanics: request-size limits, JSON parse errors, CORS headers, compact log fields, and response envelopes. | Shared mechanics are consistent without hiding service-specific write allowlists or domain behavior. |
| 7 | Audit and check scripts | Script family | Maintenance and structure | Group broad checks by source family and report section before adding more unrelated checks. | `audit_site_consistency.py` remains readable by source family and emits machine-readable sections. |

## Action Cards

### Catalogue save/build diagnostics

Priority: 1

Unit: script family.

Primary risk: maintenance and performance.

Why it matters: a single save can touch canonical source JSON, backups, lookup refreshes, generated public JSON, route stubs, search rebuilds, media derivatives, publication state, and Studio Activity rows.

Recommended next slice: add diagnostics to catalogue save/build responses and logs for elapsed time, counts, skipped work, generated artifact groups, media work, search updates, lookup refreshes, and fallback reasons.

Evidence required before closing: a local save or dry-run build can show which steps ran, which fell back to broad work, and which steps consumed meaningful time.

### Catalogue rebuild scope reduction

Priority: 2

Unit: script family.

Primary risk: performance.

Why it matters: conservative full-fallback behavior can hide repeated generated artifact, lookup, search, or media work.

Recommended next slice: after diagnostics are available, choose the most repeated broad path and narrow it using field-aware build metadata.

Evidence required before closing: the narrowed path preserves source writes, backups, dry-run behavior, generated output correctness, search consistency, and media freshness rules.

### JavaScript inventory reconciliation

Priority: 3

Unit: inventory quality.

Primary risk: planning risk.

Why it matters: the full JavaScript table and the Docs Viewer-focused table should not disagree about active Docs Viewer entry/runtime risk.
When they diverge, the inventory becomes harder to use for priority decisions.

Recommended next slice: refresh active paths and scores across [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) and [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory), then record the current above-target rows by family.

Evidence required before closing: the same active files have the same score and focus note in both reports, or a deliberate reason for separate treatment is documented.

### Docs Viewer browser-JS controller boundaries

Priority: 4

Unit: file family, with file-level score movement.

Primary risk: structural and architectural.

Why it matters: the Docs Viewer runtime has useful focused owners, but management, bookmark, search, config, and controller handoffs still need active guardrails so new features do not drift back into broad runtime coordination.

Recommended next slice: choose one complete responsibility inside one above-target controller family and move it behind explicit owner inputs, without adding behavior back to the app runtime coordinator.

Evidence required before closing: the target row can be rescored because future related changes have a clearer destination, broad state handoff was narrowed, or focused checks cover behavior that previously required full route boot.

### Media derivation diagnostics

Priority: 5

Unit: script family.

Primary risk: performance.

Why it matters: media work is external-command and file-I/O heavy, so a small script surface can still dominate local build time when batches grow.

Recommended next slice: add batch-level timing, source counts, derivative counts, skipped counts, and slow-stage reporting before considering parallelism.

Evidence required before closing: media reports show enough detail to decide whether parallel derivative generation, batched freshness checks, or no action is justified.

## Category View

Use these category views to avoid mixing unrelated risks in one table.

### Maintenance Risk

| Priority | Area | Unit | Improvement direction |
| ---: | --- | --- | --- |
| 1 | Catalogue save/build path | Script family | Make save/build side effects visible before narrowing rebuild behavior. |
| 2 | Docs build, management, import, and export | Script family | Keep cross-language contracts documented together; revisit full fallbacks only when diagnostics show repeated cost. |
| 3 | Audit and check scripts | Script family | Group checks and shared output contracts before adding more broad checks. |

### Structural And Ownership Risk

| Priority | Area | Unit | Improvement direction |
| ---: | --- | --- | --- |
| 1 | Docs Viewer browser-JS controllers | File family | Continue narrowing broad runtime handoffs into explicit owner contracts. |
| 2 | Cross-service local server mechanics | Cross-cutting family | Standardize identical mechanics without creating a broad service framework. |
| 3 | Catalogue write server | File within family | Keep HTTP orchestration separate from generated artifact, lookup, media, and source-model behavior. |

### Performance Risk

| Priority | Area | Unit | Improvement direction |
| ---: | --- | --- | --- |
| 1 | Catalogue generated/search/media work | Script family | Use diagnostics to reduce repeated broad rebuilds and media work. |
| 2 | Media derivation | Script family | Measure batch cost, then consider bounded parallelism or batched freshness checks. |
| 3 | Docs rebuilds | Script family | Monitor targeted-build diagnostics; avoid optimization work until repeated full fallbacks are visible. |

### Architectural Drift Risk

| Priority | Area | Unit | Improvement direction |
| ---: | --- | --- | --- |
| 1 | Docs Viewer app/runtime boundary | File family | Do not add new feature lifecycle ownership to the private runtime coordinator. |
| 2 | Catalogue editor/action browser modules | File family | Keep route shells as orchestration and move complete responsibilities to focused owners. |
| 3 | Catalogue script generation modules | Script family | Keep new generated artifact behavior in existing generation, lookup, or source-model owners. |

## Not Current Priorities

- Do not split the largest files only because they are large.
- Do not start another broad script-structure split before catalogue diagnostics exist.
- Do not create a broad shared local-service framework; extract only mechanics with identical contracts.
- Do not optimize docs rebuild fallbacks until diagnostics show repeated cost.
- Do not pick browser-JS work from the full table alone when a route-family batch would give clearer ownership movement.

## Update Rules

Update this dashboard when:

- a source inventory is refreshed
- an above-target JavaScript family changes score
- script-family risk classifications change
- diagnostics change the priority order
- a priority action is completed or replaced

Keep this page short.
Detailed evidence belongs in the inventory, category report, implementation plan, or task document that owns the work.

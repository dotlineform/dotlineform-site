---
doc_id: studio-javascript-payload-inventory
title: JavaScript Inventory Policy
added_date: 2026-05-14
last_updated: 2026-05-21
parent_id: audit
sort_order: 6000
viewable: true
---
# JavaScript Inventory Policy

This document defines the scoring policy and maintenance method for browser JavaScript inventory work.

Current risk scores live in:

- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- Docs Viewer-specific follow-up lives in [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)

## Purpose

Use the JavaScript inventory to decide where refactoring will reduce real future-change risk.
The inventory is not a payload-size leaderboard and it is not a mandate to split every large file.
A high score means the current file shape exposes meaningful risk; a low score means the file's current role, ownership boundary, and route exposure are acceptable.

This repo's code is Codex-authored and Codex-maintained. The inventory is therefore operational guidance for future Codex sessions as much as it is project documentation: it records where fast iterative development has left fragile ownership boundaries, and where future Codex work should slow down and create clearer helpers before adding behavior.

The project target is a risk score of 4 or lower for normal browser JavaScript files.

- A score of 4 remains the normal acceptable target: maintenance, structural, performance, and architectural risk are each present but low.
- A category score of 0 is allowed only when that risk dimension is materially absent or inapplicable for a physically achievable reason.

`assets/docs-viewer/js/docs-viewer.js` is tracked separately because it is the shared Docs Viewer entry runtime and needs its own feature-driven mitigation path.

## Risk Categories

**Maintenance Risk** is the cost and danger of changing behavior later.

Useful indicators:

- mixed responsibilities such as rendering, validation, service calls, state mutation, modal lifecycle, and data normalization in one module
- high edit frequency or repeated recent touches
- bug-prone ownership where the same concept is updated in several places
- hidden contracts where functions depend on broad route `state` rather than explicit inputs
- hard-to-test behavior that only runs through DOM events or route boot
- large local helper clusters that are only implicitly related
- interleaved fallback paths such as post, patch, offline, and manual modes

**Structural Risk** is whether the module shape matches the desired architecture.

Useful indicators:

- route/controller files own behavior that belongs in domain, save, service, render, modal, route-state, or workflow modules
- lower-level helpers import route-level concepts or know too much about a parent controller
- several modules mutate the same state fields without a clear owner
- route files invent markup or event patterns instead of using established route-family primitives
- entry controllers do implementation work rather than orchestration

**Performance Risk** is route cost and interaction cost, not raw file size alone.

Useful indicators:

- eager loading on public or shared routes
- large initial route payloads
- heavy boot-time work before route-ready
- repeated full-list renders where incremental rendering would matter
- expensive filtering or sorting on every input event
- large generated-data reads or joins on the client
- modal, import, management, or report code loaded before it is needed

**Architectural Risk** is whether the current shape will attract future work into the wrong place.

Useful indicators:

- no obvious owner exists for a complete responsibility that is likely to change
- sibling routes have clearer boundaries that this file does not match
- extracted responsibilities can easily be reintroduced inline because contracts are loose
- reviewers must reason about unrelated concerns together
- the next useful slice is a complete responsibility but still has no module owner

## Scoring Model

Each file receives a score from 0 to 3 for each risk category.
The total risk score is the sum of the four category scores.

Use 0 carefully. It means "this category does not materially apply to this file in its current role," not "this seems easy."
For example, an isolated Studio operational helper may have no meaningful performance requirement as long as it remains route-local, rare, and free of heavy boot or input-time work.

| Risk | Score 0: absent or inapplicable | Score 1: low risk | Score 2: medium risk | Score 3: high risk |
| --- | --- | --- | --- | --- |
| Maintenance | no direct maintenance surface beyond preserving an isolated, stable, generated, declarative, or mechanically owned file | focused role, explicit inputs, stable behavior, directly testable or small enough to review | some mixed concerns, recurring touches, broad reads, or moderate test friction | many mixed concerns, broad reads/writes, frequent edits, fallback paths, or hard-to-test behavior |
| Structural | no meaningful structural ownership decision exists beyond keeping the file isolated in its current role | module shape matches its role and established route-family boundaries | partial split exists, but ownership or contracts remain incomplete | route/controller owns layers that belong in domain, service, render, modal, route-state, or workflow modules |
| Performance | no material runtime performance requirement for the file's current route exposure, data volume, and interaction pattern | lazy, rare, small, public-cost-neutral, or no meaningful boot/input cost | route-local exposure, moderate size, repeated list work, or occasional input-time cost | public/shared eager exposure, large initial payload, heavy boot work, repeated full renders, or expensive input-time operations |
| Architectural | no plausible future-responsibility drift because the file is a stable isolated owner or future work has a clearly separate owner | clear owner exists for future changes and the file reinforces durable patterns | future changes may drift into the file because ownership is only partly clear | current shape is likely to attract unrelated future work, diverge from sibling patterns, or require unrelated concerns to be reviewed together |

Risk bands:

- 0-3: below the normal target; acceptable only when one or more category scores are legitimately absent or inapplicable.
- 4: normal target state; currently acceptable.
- 5: low-priority watch item; improve opportunistically when changing nearby behavior.
- 6-7: medium priority; schedule as part of the relevant route-family batch.
- 8-12: high priority; plan a focused mitigation slice before adding more behavior to that file.

Priority should be based on current risk, not ease or theoretical leverage:

`risk score = maintenance risk + structural risk + performance risk + architectural risk`

## Application Rules

The target is not a thin pass-through layer; the target is a file whose remaining responsibilities are coherent and low risk.

- Prefer extraction slices that remove a complete responsibility from a mixed controller and leave a clearer ownership boundary behind.
- Do not prioritise a slice because it is narrow, mechanical, or easy. Avoid cosmetic splits that only move tiny helpers.
- Prioritise slices that reduce future change risk, clarify state ownership, improve route-load behavior, or establish a repeatable pattern for sibling routes.
- A file should not be rescored down just because code moved elsewhere.

Rescore downward only when at least one of these is true:

- a category is now materially absent or inapplicable, justifying a score of 0
- a complete responsibility has a focused owner with explicit inputs
- route boot or input-time work was reduced
- future related changes now have an obvious destination outside the route shell
- focused module checks cover behavior that previously required full route boot
- sibling routes now share a stable boundary pattern

A route entry module may remain above 4 if it legitimately coordinates multiple async sources, event wiring, route ready/busy state, and dynamic module activation.

Maintenance mitigation slices must be classified before implementation:

- **Score-moving slice:** expected to lower at least one target file's risk score because a complete responsibility moves to a focused owner with explicit inputs and focused checks. If the expected score movement does not happen, record that as a failed or partial mitigation decision rather than treating the batch as complete.
- **Guardrail slice:** pins a contract, smoke, or policy that prevents regression but is not expected to lower a score by itself. For score-6 and score-7 files, a mitigation batch should not close on guardrail slices alone. If a guardrail slice is needed first, the same task definition must name the follow-on score-moving slice, target score movement, and evidence required before rescoring.

## Inventory Refresh Method

Refresh the inventory from the current filesystem before starting a new batch. Do not rely on stale row counts or previous ranks.

1. List all browser JavaScript under `assets/`.
2. Collect raw size, gzip size, line count, imports, route exposure, and recent edit history.
3. Review the highest-risk files manually against the four categories.
4. Assign category scores, not just a total.
5. Update [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) with current rows and scores.
6. Update [JavaScript Inventory Implementation Plan](/docs/?scope=studio&doc=javascript-inventory-implementation-plan) when the family batching or next concrete tasks change.
7. Update [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) when Docs Viewer-specific scores or follow-up tasks change.

Useful metric command from the repo root:

```bash
python3 - <<'PY'
from pathlib import Path
import gzip

rows = []
for path in Path('assets').rglob('*.js'):
    data = path.read_bytes()
    rows.append((len(data), len(gzip.compress(data, compresslevel=9)), str(path)))

print('files', len(rows))
for raw, gz, path in sorted(rows, reverse=True)[:30]:
    print(f'{path}	{raw / 1024:.1f} KiB	{gz / 1024:.1f} KiB')
PY
```

Use `git log --since=90 days --name-only` to inform maintenance risk, then manually review the highest-risk files for responsibility boundaries and route exposure.
When checking route exposure, search checked-in route shells and includes while avoiding generated docs payload noise.

## Related References

- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)

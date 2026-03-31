---
doc_id: css-audit-spec
title: CSS Audit Spec (v1)
last_updated: 2026-03-28
parent_id: design
---

# CSS Audit Spec (v1)

## Goal

Create a repeatable CSS audit that:

- documents CSS usage clearly
- detects likely drift and maintainability risks
- produces actionable recommendations with confidence levels

Related contract:

- [CSS Primitives](/docs/?scope=studio&doc=css-primitives)

## Scope (v1)

Static and heuristic checks only (no browser required).

Included:

- selector inventory from `assets/css/**/*.css`
- usage inventory across templates/pages (`_layouts`, `_includes`, `*.md`, `*.html`)
- unused selector detection (confidence-tagged)
- undefined class usage in templates
- specificity hotspots
- `!important` usage
- duplicate/conflicting declarations
- token drift heuristics (hardcoded values vs CSS variables/tokens)
- large-rule / selector-density hotspots

Excluded (future phase):

- full cascade correctness checks
- responsive visual regression checks
- runtime computed-style verification

## Inputs

- CSS: `assets/css/**/*.css`
- templates/content:
  - `_layouts/**/*`
  - `_includes/**/*`
  - root `*.md`, `*.html`
  - section index pages (e.g. `works/index.md`, `work_details/index.md`)
- optional JS hints:
  - `assets/js/**/*.js`
  - inline scripts for `classList.add/remove/toggle`

## Confidence Model

Each finding is labeled:

- `high`: deterministic static fact
- `medium`: strong heuristic
- `low`: weak heuristic / advisory

## Proposed Checks

- `css_unused_selector`
- `css_undefined_class_ref`
- `css_specificity_hotspot`
- `css_important_overuse`
- `css_duplicate_declaration`
- `css_conflicting_declaration`
- `css_token_drift_color`
- `css_token_drift_typography_spacing`
- `css_rule_size_hotspot`

## CLI (v1)

- `--site-root` default `.`
- `--checks` default `all`
- `--check-only` (repeat/comma-separated)
- `--strict` (fail on errors)
- `--json-out` optional
- `--md-out` default `docs/css-audit-latest.md`
- `--max-samples` default `20`
- `--specificity-threshold` default `0,3,0`
- `--ignore-file` optional (`docs/css-audit-ignore.txt`)

## Output

Markdown report (default): `docs/css-audit-latest.md`

Top section:

- run timestamp
- duration
- flags (value + default marker)
- summary counts by severity/confidence

Body:

- check summary table
- grouped findings with file/selector references
- prioritized recommendations (`P1`, `P2`, `P3`)

Optional JSON report for tooling/CI.

## Priority Heuristic

Use weighted scoring:

- severity weight
- confidence weight
- frequency weight

Map to:

- `P1` immediate
- `P2` next pass
- `P3` backlog

## Implementation Plan

1. Build parser/index layer (selectors + template usage).
2. Implement deterministic checks first.
3. Add heuristic checks with confidence tags.
4. Add Markdown/JSON reporting.
5. Document usage in [CSS Token Audit](/docs/?scope=studio&doc=scripts-css-token-audit).
6. Add follow-up tasks in `docs/backlog.md`.

## Acceptance Criteria (v1)

- Runs with current local Python environment.
- Writes stable report to `docs/css-audit-latest.md`.
- Findings include confidence labels.
- Noise is manageable via ignore file support.
- Report includes actionable recommendations, not only raw findings.

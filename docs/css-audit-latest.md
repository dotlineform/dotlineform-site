# CSS Audit Latest

Generated: 2026-03-09 18:17:11 UTC

Files:
- `assets/css/main.css`
- `assets/studio/css/studio.css`

## Summary

- `assets/css/main.css`: 38 `font-size` declarations, 0 raw literal sizes, 5 direct color literal usages
- `assets/studio/css/studio.css`: 42 `font-size` declarations, 0 raw literal sizes, 10 direct color literal usages

## Findings

### `assets/css/main.css`

Raw font-size hotspots:
- none

Direct color literal hotspots:
- `#777`: 2 occurrence(s) at line(s) 652, 657
- `rgba(0,0,0,.08)`: 1 occurrence(s) at line(s) 383
- `#d11`: 1 occurrence(s) at line(s) 1081
- `#1166cc`: 1 occurrence(s) at line(s) 1085

### `assets/studio/css/studio.css`

Raw font-size hotspots:
- none

Direct color literal hotspots:
- `#fff`: 2 occurrence(s) at line(s) 465, 554
- `#1f1f1f`: 2 occurrence(s) at line(s) 552, 555
- `#d9a43f`: 1 occurrence(s) at line(s) 469
- `#57a368`: 1 occurrence(s) at line(s) 473
- `#fafafa`: 1 occurrence(s) at line(s) 507
- `#d0d0d0`: 1 occurrence(s) at line(s) 508
- `#2f2f2f`: 1 occurrence(s) at line(s) 509
- `#d2d2d2`: 1 occurrence(s) at line(s) 834

## Recommendations

### P1 Typography

- Finalize one shared text scale before touching page selectors further.
- Replace repeated raw caption/meta values in `main.css` with semantic tokens.
- Fit component and page typography to the existing shared tokens instead of preserving local near-duplicate sizes.

### P2 Color

- Keep palette tokens centralized and remove the remaining component-level hardcoded colors.
- Add semantic aliases for states and special chips instead of repeating neutrals and weight-dot fills inline.

### P3 Primitives

- Standardize shared list, panel, input, button, and toolbar primitives before page-by-page cleanup.
- Migrate pages by primitive family rather than by file or route.

### P4 Guardrails

- Re-run this audit after each CSS cleanup pass.
- Block new raw `font-size` and color literals once the replacement token family exists.

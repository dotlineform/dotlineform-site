# CSS Audit Latest

Generated: 2026-03-09 17:46:44 UTC

Files:
- `assets/css/main.css`
- `assets/studio/css/studio.css`

## Summary

- `assets/css/main.css`: 38 `font-size` declarations, 26 raw literal sizes, 5 direct color literal usages
- `assets/studio/css/studio.css`: 42 `font-size` declarations, 42 raw literal sizes, 10 direct color literal usages

## Findings

### `assets/css/main.css`

Raw font-size hotspots:
- `12px`: 12 occurrence(s) at line(s) 219, 415, 444, 448, 463, 511, ...
- `0.95em`: 2 occurrence(s) at line(s) 156, 1277
- `13px`: 2 occurrence(s) at line(s) 242, 243
- `clamp(1.125rem, 1.25vw, 1.375rem)`: 2 occurrence(s) at line(s) 484, 1040
- `0.95rem`: 2 occurrence(s) at line(s) 705, 949
- `0.9rem`: 2 occurrence(s) at line(s) 711, 719
- `0.88rem`: 2 occurrence(s) at line(s) 1007, 1016
- `16px`: 1 occurrence(s) at line(s) 222
- `1.1rem`: 1 occurrence(s) at line(s) 353

Direct color literal hotspots:
- `#777`: 2 occurrence(s) at line(s) 652, 657
- `rgba(0,0,0,.08)`: 1 occurrence(s) at line(s) 383
- `#d11`: 1 occurrence(s) at line(s) 1081
- `#1166cc`: 1 occurrence(s) at line(s) 1085

### `assets/studio/css/studio.css`

Raw font-size hotspots:
- `0.78rem`: 12 occurrence(s) at line(s) 616, 802, 812, 854, 886, 919, ...
- `0.82rem`: 9 occurrence(s) at line(s) 262, 450, 556, 677, 730, 870, ...
- `0.86rem`: 5 occurrence(s) at line(s) 429, 535, 587, 720, 1346
- `0.83rem`: 3 occurrence(s) at line(s) 389, 1264, 1272
- `0.9rem`: 2 occurrence(s) at line(s) 153, 1004
- `0.88rem`: 2 occurrence(s) at line(s) 383, 581
- `1.3rem`: 1 occurrence(s) at line(s) 90
- `1rem`: 1 occurrence(s) at line(s) 136
- `0.72rem`: 1 occurrence(s) at line(s) 309
- `0.84rem`: 1 occurrence(s) at line(s) 339

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
- Add a small Studio typography alias layer so repeated UI sizes stop drifting by hundredths of a rem.

### P2 Color

- Keep palette tokens centralized and remove the remaining component-level hardcoded colors.
- Add semantic aliases for states and special chips instead of repeating neutrals and weight-dot fills inline.

### P3 Primitives

- Standardize shared list, panel, input, button, and toolbar primitives before page-by-page cleanup.
- Migrate pages by primitive family rather than by file or route.

### P4 Guardrails

- Re-run this audit after each CSS cleanup pass.
- Block new raw `font-size` and color literals once the replacement token family exists.

Main.css immediate target values:
- `12px` (12 occurrence(s))
- `0.95em` (2 occurrence(s))
- `13px` (2 occurrence(s))

Studio.css immediate target values:
- `0.78rem` (12 occurrence(s))
- `0.82rem` (9 occurrence(s))
- `0.86rem` (5 occurrence(s))
- `0.83rem` (3 occurrence(s))
- `0.9rem` (2 occurrence(s))

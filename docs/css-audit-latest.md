# CSS Audit Latest

Generated: 2026-03-09 21:58:01 UTC

Files:
- `assets/css/main.css`
- `assets/studio/css/studio.css`

## Summary

- `assets/css/main.css`: 35 `font-size` declarations, 0 raw literal sizes, 0 direct color literal usages
- `assets/studio/css/studio.css`: 32 `font-size` declarations, 0 raw literal sizes, 0 direct color literal usages

## Findings

### `assets/css/main.css`

Raw font-size hotspots:
- none

Direct color literal hotspots:
- none

### `assets/studio/css/studio.css`

Raw font-size hotspots:
- none

Direct color literal hotspots:
- none

## Recommendations

### P1 Typography

- Finalize one shared text scale before touching page selectors further.
- Replace repeated raw caption/meta values in `main.css` with semantic tokens.
- Fit component and page typography to the existing shared tokens instead of preserving local near-duplicate sizes.

### P2 Color

- Keep palette tokens centralized and remove the remaining component-level hardcoded colors.
- Fit component colors to the shared palette and state tokens instead of preserving local one-off literals.

### P3 Primitives

- Standardize shared list, panel, input, button, and toolbar primitives before page-by-page cleanup.
- Migrate pages by primitive family rather than by file or route.

### P4 Guardrails

- Re-run this audit after each CSS cleanup pass.
- Block new raw `font-size` and color literals once the replacement token family exists.

### Editor Variant

- `tagStudio__panel--editor` does not change the outer border, radius, or background. It only adds stacked internal layout via `display: grid`, `gap`, and `align-content: start`.
- If an editor panel looks wrong, check the shell around it before adding page-local spacing fixes. The variant itself should remain a shell-plus-rhythm modifier only.

### Nested Panels

- Panel-inside-panel is a supported composition case for grouped subsections and should be tested in the primitive catalogue, not hidden by page-local fixes.
- Direct nested child panels now inherit a subordinate surface treatment from the primitive itself so the inner group reads as secondary containment rather than a duplicate top-level card.
- If nested panels still require local compensation on a page, treat that as evidence that the primitive contract is incomplete and fix the shared source or document a shared composition rule.

### Compact Variant

- `tagStudio__panel--compact` only reduces padding. Do not use it to solve layout issues caused by unrelated parent layout decisions.
- When checking a compact or nested panel on a real page, look for double borders, unclear hierarchy, or cramped spacing and resolve those in the shared panel contract where possible.

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

### Panel Link Variation

- Use `tagStudio__panel tagStudio__panelLink` for static-content navigation panels where the whole panel is the click target.
- This variation uses a fixed design-time height via `--panel-link-height`. Content should be edited to fit the panel, not vice versa.
- Short copy discipline is part of the contract. Do not rely on auto-growing panel height to accommodate longer dashboard copy.
- Use `tagStudio__panelLink--image` with `--panel-image` when a full-panel background image is needed. The image is decorative support for the fixed panel shell, not a reason to change the click or sizing behavior.

### Design Guidance

- Panel-link copy should wrap against the panel width itself. Do not add an internal text-measure cap that makes the copy look like it belongs to an invisible inner column.
- For short-copy landing-page entry panels such as `/studio/`, prefer narrower centered columns rather than stretching the cards to fill the whole content area width.
- For denser dashboard grids such as analytics/library/search, equal-fit grid tracks can still be appropriate as long as the panel height remains fixed and the copy stays short.

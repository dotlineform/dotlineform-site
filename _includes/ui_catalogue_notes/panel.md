### Editor Variant

1. `tagStudio__panel--editor` does not change the outer border, radius, or background. It only adds stacked internal layout via `display: grid`, `gap`, and `align-content: start`.
2. If an editor panel looks wrong, check the shell around it before adding page-local spacing fixes. The variant itself should remain a shell-plus-rhythm modifier only.

### Nested Panels

1. Panel-inside-panel is a supported composition case for grouped subsections and should be tested in the primitive catalogue, not hidden by page-local fixes.
2. Direct nested child panels now inherit a subordinate surface treatment from the primitive itself so the inner group reads as secondary containment rather than a duplicate top-level card.
3. If nested panels still require local compensation on a page, treat that as evidence that the primitive contract is incomplete and fix the shared source or document a shared composition rule.

### Compact Variant

1. `tagStudio__panel--compact` only reduces padding. Do not use it to solve layout issues caused by unrelated parent layout decisions.
2. When checking a compact or nested panel on a real page, look for double borders, unclear hierarchy, or cramped spacing and resolve those in the shared panel contract where possible.

### Panel Link Variation

1. Use `tagStudio__panel tagStudio__panelLink` for static-content navigation panels where the whole panel is the click target.
2. This variation uses a fixed design-time height via `--panel-link-height`. Content should be edited to fit the panel, not vice versa.
3. Short copy discipline is part of the contract. Do not rely on auto-growing panel height to accommodate longer dashboard copy.
4. Use `tagStudio__panelLink--image` with `--panel-image` when a full-panel background image is needed. The image is decorative support for the fixed panel shell, not a reason to change the click or sizing behavior.
5. Background images for Studio panel links should be chosen at design time from `assets/studio/img/panel-backgrounds/`.
6. On Jekyll-rendered routes, keep the selected image width in shared page data such as `_data/studio_panel_images.json` rather than burying `800` or `1200` directly in the page markup.
7. Use a page-level default width plus optional per-panel `width` overrides in that data so each route can share a baseline without forcing every panel to use the same source size.
8. The filename convention for those assets is `{asset_id}-{variant}-{width}.{format}`, for example `01007-primary-800.webp`.
9. The base image variant keeps the site-default dark text. Add `tagStudio__panelLink--imageContrast` when a darker image needs white text and a stronger overlay.
10. The image fill uses centered `cover` behavior, so small images are scaled up to fit and mismatched aspect ratios are cropped rather than stretched.

### Design Guidance

1. Panel-link copy should wrap against the panel width itself. Do not add an internal text-measure cap that makes the copy look like it belongs to an invisible inner column.
2. For short-copy landing-page entry panels such as `/studio/`, prefer narrower centered columns rather than stretching the cards to fill the whole content area width.
3. For denser dashboard grids such as analytics/library/search, equal-fit grid tracks can still be appropriate as long as the panel height remains fixed and the copy stays short.
4. Include common design-led overrides in the code samples when they materially affect how the primitive is reused. The image-panel contrast override is part of the working reference, not supplementary commentary.

---
doc_id: studio-ui-rules
title: "Studio UI Rules And Decision Log"
last_updated: 2026-04-20
parent_id: design
sort_order: 30
---
# Studio UI Rules And Decision Log

This document is the working record for Studio UI issues, decisions, and permanent standards that emerge from real fixes.

Use it to separate:

- one-off page corrections
- repeated issues that should become shared Studio rules
- local Codex changes that would otherwise disappear without PR discussion

Use this as the single capture surface for Studio UI work:

- open UI observations from IAB review
- one-off route corrections
- systemic findings that should become permanent rules
- local Codex change notes for UI work that did not go through PR review

## Purpose

Use this document to:

- capture open UI issues as they are found
- record the triage note for a UI issue
- decide whether the issue is local or systemic
- capture the permanent rule when the issue should affect future work
- record where the rule is enforced
- leave a short local change log when work is done directly with Codex instead of through PR review

## Triage Labels

Every UI issue should start with one triage note:

- `one-off`
  The problem belongs to one route or one piece of markup only.
- `systemic`
  The problem exposes a shared primitive, token, layout pattern, or behavior that should be corrected at the design-system level.
- `pending`
  The issue has not yet been classified.

## Local Workflow

Because the primary workflow is local Codex work rather than PR-based review, each systemic fix should leave evidence in this document.

For local work, record:

- the route where the issue was seen
- the triage note
- the reasoning behind the classification
- the exact shared rule or non-rule decision
- the files changed
- the local verification method
- any follow-up work still needed

If a similar issue appears a second time, promote it to `systemic` unless there is a clear reason not to.

## Workflow

Use this sequence for Studio UI work:

1. Capture the issue here when it is observed in IAB or local browser testing.
2. Add the initial triage note as `pending`, `one-off`, or `systemic`.
3. Fix the issue locally.
4. Update the same entry with the outcome:
   - keep it `local-only` if it was truly route-specific
   - mark it `adopted` if it became a permanent Studio rule
5. Record the files changed and the local verification method.

## Standing Instruction

For every Studio UI issue reported and fixed:

1. Fix the issue.
2. Decide whether it is `one-off` or `systemic`.
3. Update this document with a new or amended entry.
4. Record the route, issue, triage, reasoning, files changed, verification method, and any permanent rule adopted.
5. If the issue is systemic, prefer changing the shared primitive, token, or pattern rather than adding a page-specific workaround.
6. Rebuild docs if this document changed.

## Working Rule

Use this decision test:

- if the fix should change only one route, keep it local
- if the fix changes a shared class, shared token, shared layout primitive, or common interaction, record it here as a permanent rule

## Entry Template

```text
## UI Rule Log YYYY-MM-DD / UI-###

- status: open | adopted | local-only | superseded
- route:
- issue:
- triage: pending | one-off | systemic
- reasoning:
- permanent rule:
- enforcement point:
- files changed:
- local verification:
- follow-up:
```

## Current Rules And Log

Add new entries at the top of this section.

## UI Rule Log 2026-04-20 / UI-011

- status: adopted
- route: `/studio/series-tag-editor/`, `/studio/ui-catalogue/button/`
- issue: the series tag editor’s button-related status and warning text was rendering in a shared message area far above the `Add` / `Save` controls, which made the feedback feel detached from the related field and commands.
- triage: systemic
- reasoning: command feedback belongs to the command area, not to a distant generic message block. The button primitive needs to state that placement rule explicitly, and the live series tag editor should follow it so the primitive page reflects a real page pattern.
- permanent rule: button-related status, warning, and success copy must stay adjacent to the related command area. Place it on the same row only if space allows; otherwise put it in a dedicated row immediately below the relevant button row. Keep broader page context hints separate from local command feedback.
- enforcement point: `studio/series-tag-editor/index.md`, `studio/ui-catalogue/button/index.md`, `_includes/studio_ui_catalogue_button_demo.html`, `_includes/ui_catalogue_notes/button.md`, and the button/message guidance in `studio-ui-framework.md`
- files changed:
  - `studio/series-tag-editor/index.md`
  - `assets/studio/css/studio.css`
  - `studio/ui-catalogue/button/index.md`
  - `_includes/studio_ui_catalogue_button_demo.html`
  - `_includes/ui_catalogue_notes/button.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/series-tag-editor/` on desktop and mobile and confirm the feedback row sits directly below the `Add` / `Save` row inside the editor panel
  - inspect `/studio/ui-catalogue/button/` and confirm the first example and canonical markup show local button feedback placement
- follow-up:
  - review modal command feedback after the basic page sweep and apply the same adjacency rule where relevant

## UI Rule Log 2026-04-20 / UI-010

- status: adopted
- route: `/studio/series-tag-editor/`, `/studio/ui-catalogue/button/`
- issue: the series tag editor’s `Add` and `Save Tags` buttons sit directly beside the tag input field, which makes them the clearest live use case for the small command-button pattern. The label `Save Tags` also overstates the action relative to the button-width guidance.
- triage: systemic
- reasoning: this is the first direct live-page adoption of the new button contract, so the primitive page should show the same field-row pattern explicitly. The page fix and the primitive reference need to move together or the pattern stays abstract.
- permanent rule: when a command button sits beside a text field in the same row, use the small button size and the standard default width unless a specific override is justified. Prefer the shortest accurate label that fits the shared width, for example `Save` rather than `Save Tags`.
- enforcement point: `studio/series-tag-editor/index.md`, `studio/ui-catalogue/button/index.md`, and `_includes/ui_catalogue_notes/button.md`
- files changed:
  - `studio/series-tag-editor/index.md`
  - `studio/ui-catalogue/button/index.md`
  - `_includes/studio_ui_catalogue_button_demo.html`
  - `_includes/ui_catalogue_notes/button.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/series-tag-editor/` and confirm `Add` and `Save` are the same default width beside the tag field
  - inspect `/studio/ui-catalogue/button/` and confirm the first example now shows the field-row pattern explicitly
- follow-up:
  - use the same field-row rule when reviewing other input-adjacent buttons during the wider button sweep

## UI Rule Log 2026-04-20 / UI-009

- status: adopted
- route: `/studio/ui-catalogue/button/`
- issue: the first button primitive draft was still mixing command buttons with navigation-style anchor buttons and toolbar-forward assumptions. The requirement is actually narrower: buttons are commands only, toolbar is optional and separate, and the initial contract should stay minimal.
- triage: systemic
- reasoning: keeping the primitive small is more important than speculating about future button families. The button page should establish role boundaries, two sizes, standard width guidance, and modal default-action behavior without pulling in link patterns, toolbar patterns, or special destructive styling.
- permanent rule: Studio buttons are command controls only. Navigation actions should move to a link pattern. The shared button contract currently defines two sizes, a standard width target, bold default-modal action, and no special destructive styling by default. Do not use a panel as the grouping device when buttons need a boundary.
- enforcement point: `studio/ui-catalogue/button/index.md`, `_includes/studio_ui_catalogue_button_demo.html`, `_includes/ui_catalogue_notes/button.md`, `assets/studio/css/studio.css`, and the button guidance in `studio-ui-framework.md`
- files changed:
  - `studio/ui-catalogue/button/index.md`
  - `_includes/studio_ui_catalogue_button_demo.html`
  - `_includes/ui_catalogue_notes/button.md`
  - `assets/studio/css/studio.css`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/ui-catalogue/button/` on desktop and mobile
  - confirm the page no longer shows anchor-as-button or toolbar-subset examples
  - confirm modal default action is bold and default-width behavior is shown with `OK` and `Cancel`
- follow-up:
  - run a later consistency sweep on live Studio pages for navigation-like buttons and overlong labels such as `Save Tags`

## UI Rule Log 2026-04-20 / UI-008

- status: adopted
- route: `/studio/ui-catalogue/button/`
- issue: Studio currently uses one shared command-button class across editor pages, modal actions, and toolbar-style action rows, but the role boundary is still blurry because clickable pills and docs-viewer management buttons sit nearby as similar-looking controls.
- triage: systemic
- reasoning: the button primitive needs to establish scope before visual refinement. The immediate problem is not missing color variants; it is unclear ownership of command buttons versus pills and toolbar subsets. The first primitive page should therefore capture the shared baseline and the drift explicitly, rather than pretending the emphasis system is already solved.
- permanent rule: the button primitive covers command buttons only. Clickable pills are a separate primitive. Modal actions stay within the button primitive, but toolbar remains an optional composition primitive to define separately.
- enforcement point: `studio/ui-catalogue/button/index.md`, `_includes/studio_ui_catalogue_button_demo.html`, `_includes/ui_catalogue_notes/button.md`, and the shared `tagStudio__button` baseline in `assets/studio/css/studio.css`
- files changed:
  - `studio/ui-catalogue/button/index.md`
  - `_includes/studio_ui_catalogue_button_demo.html`
  - `_includes/ui_catalogue_notes/button.md`
  - `studio/ui-catalogue/index.md`
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/ui-catalogue/button/` on desktop and mobile
  - confirm the page establishes the command-button baseline and explicitly excludes clickable pills from this primitive
- follow-up:
  - refine the button contract toward smaller role boundaries and a clearer size/width model once the first page is in place

## UI Rule Log 2026-04-20 / UI-007

- status: adopted
- route: `/studio/`
- issue: the Studio landing page needed real panel-background image assignments, but the chosen source width is a design-time decision that should stay visible and adjustable rather than being embedded as hardcoded width-specific filenames in the page markup. The data shape also needed to make clear that a route can share a default width without forcing every panel to use the same source size, and that the asset naming convention is deliberate.
- triage: systemic
- reasoning: the image-fit behavior belongs to the primitive, while the chosen source asset and width belong to the page composition. On Jekyll-rendered pages, that design choice should be expressed through shared data so future panel-size changes do not require searching for scattered literal filenames.
- permanent rule: keep Jekyll-rendered Studio panel-link background-image selections in shared page data such as `_data/studio_panel_images.json`. Treat widths like `800` or `1200` as explicit design variables for the route, not implicit primitive defaults. Use a page-level default width plus optional per-panel overrides, and keep the asset filename pattern explicit as `{asset_id}-{variant}-{width}.{format}`.
- enforcement point: `_data/studio_panel_images.json`, `studio/index.md`, and the panel primitive notes/docs
- files changed:
  - `_data/studio_panel_images.json`
  - `studio/index.md`
  - `_includes/ui_catalogue_notes/panel.md`
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/config-studio-config-json.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/` on desktop and mobile
  - confirm all four landing panels render with background images from `assets/studio/img/panel-backgrounds/`
  - confirm the page markup reads the chosen image width from `_data/studio_panel_images.json`
- follow-up:
  - if another Jekyll-rendered landing/dashboard page adopts image panels, add its route-specific image choices to the same data file or a closely related shared data source

## UI Rule Log 2026-04-20 / UI-006

- status: adopted
- route: `/studio/ui-catalogue/panel/`
- issue: the image-fill panel-link example had drifted into treating white text as the default primitive behavior, even though dark text is the site-wide default. The catalogue also was not yet showing the contrast override as an explicit reusable code pattern.
- triage: systemic
- reasoning: the image-fill behavior and the contrast treatment are different concerns. The primitive should stay neutral by default and the working reference should show common design-led overrides in code when they materially affect how the primitive is applied on real pages.
- permanent rule: `tagStudio__panelLink--image` keeps the default dark text and centered `cover` image behavior. Use `tagStudio__panelLink--imageContrast` as the explicit override when a selected image needs white text and a stronger overlay. Studio panel-link background images should be selected at design time from `assets/studio/img/panel-backgrounds/`.
- enforcement point: `.tagStudio__panelLink--image` and `.tagStudio__panelLink--imageContrast` in `assets/studio/css/studio.css`, plus the panel primitive examples and notes
- files changed:
  - `assets/studio/css/studio.css`
  - `assets/studio/img/panel-backgrounds/.gitkeep`
  - `studio/ui-catalogue/panel/index.md`
  - `_includes/studio_ui_catalogue_panel_demo.html`
  - `_includes/ui_catalogue_notes/panel.md`
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/ui-catalogue/panel/` and confirm the base image panel keeps dark text
  - confirm the contrast override example uses white text and a stronger overlay
  - confirm the code samples show both the neutral image variant and the explicit contrast override
- follow-up:
  - add actual design-time background image files under `assets/studio/img/panel-backgrounds/` before wiring image panels onto live Studio routes
## UI Rule Log 2026-04-20 / UI-005

- status: adopted
- route: `/studio/`, `/studio/ui-catalogue/panel/`
- issue: the shared panel-link variation was constraining paragraph copy with an internal text-measure cap, which made the text look like it was wrapping inside an unspecified inner column. On the `/studio/` landing page, the equal-fill two-column layout also made the short-copy entry panels feel over-wide and visually sparse.
- triage: systemic
- reasoning: both issues affect how the primitive should be reused, not just how it is coded. The panel-link contract needs explicit design guidance as well as CSS behavior so the working reference can steer page composition instead of documenting code in isolation.
- permanent rule: primitive definitions may include design guidance when layout choices materially affect correct reuse. For panel-link cards, copy should wrap to the panel width, and short-copy landing-page entry panels may use narrower centered columns instead of full-width equal-fill tracks.
- enforcement point: `.tagStudio__panelLink` in `assets/studio/css/studio.css`, `/studio/` layout rules, and the panel primitive docs
- files changed:
  - `assets/studio/css/studio.css`
  - `assets/css/main.css`
  - `_includes/ui_catalogue_notes/panel.md`
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `_docs_src/site-change-log.md`
- local verification:
  - inspect `/studio/` and confirm the entry panels are narrower and centered
  - confirm panel-link copy wraps to the card width rather than an implicit inner measure
  - inspect `/studio/ui-catalogue/panel/` and confirm the design-guidance notes are present
- follow-up:
  - if another panel-link route feels too sparse or too dense, adjust the shared composition guidance first before introducing route-local overrides

## UI Rule Log 2026-04-20 / UI-004

- status: adopted
- route: `/studio/`, `/studio/analytics/`, `/studio/library/`, `/studio/search/`
- issue: the Studio landing page and the analytics/library/search dashboards were using two duplicated card-panel patterns. The analytics/library/search cards also sized themselves to content, which made panel height drift with copy instead of staying a deliberate design object.
- triage: systemic
- reasoning: these cards are a real panel variation, not a one-off page layout. Keeping them duplicated in `assets/css/main.css` would keep the primitive hidden and encourage local drift. The intended behavior is fixed-height, whole-panel-clickable static navigation with optional image fill.
- permanent rule: clickable panel-navigation cards must use the shared Studio panel-link variation in `assets/studio/css/studio.css`. Their height is fixed at design time, and copy must be edited to fit the panel rather than stretching the panel to fit content.
- enforcement point: `.tagStudio__panelLink` and `.tagStudio__panelLink--image` in `assets/studio/css/studio.css`
- files changed:
  - `assets/studio/css/studio.css`
  - `assets/css/main.css`
  - `studio/index.md`
  - `studio/analytics/index.md`
  - `studio/library/index.md`
  - `studio/search/index.md`
  - `studio/ui-catalogue/panel/index.md`
  - `_includes/studio_ui_catalogue_panel_demo.html`
  - `_includes/ui_catalogue_notes/panel.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/ui-catalogue.md`
- local verification:
  - inspect `/studio/`, `/studio/analytics/`, `/studio/library/`, and `/studio/search/`
  - confirm the clickable panels share one fixed-height treatment
  - confirm panel height stays stable when card copy differs slightly
  - confirm hover/focus states still treat the whole panel as the click target
- follow-up:
  - if a future dashboard panel needs more room, add an explicit shared size modifier instead of letting content auto-size the card

## UI Rule Log 2026-04-20 / UI-003

- status: adopted
- route: `/studio/ui-catalogue/panel/`
- issue: panel nesting is a real container use case, so treating the first apparent nested-shell problem as a pure demo-environment artifact would hide a shared composition requirement.
- triage: systemic
- reasoning: for this project, the primitive catalogue is meant to expose hidden one-off fixes in live pages. If a primitive fails in the catalogue but looks fine on a route, that route may simply be compensating for the primitive locally. The catalogue should pressure the shared source rather than preserve legacy behavior by default.
- permanent rule: when a primitive can validly compose with itself, test that case in the catalogue and prefer fixing the primitive or shared composition contract over documenting page-local compensation. Future design reliability takes priority over preserving accidental legacy behavior.
- enforcement point: `ui-catalogue.md`, primitive docs under `_docs_src/`, and shared primitive CSS when the failure is systemic
- files changed:
  - `_docs_src/ui-catalogue.md`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/studio-ui-rules.md`
  - `studio/ui-catalogue/panel/index.md`
  - `_includes/studio_ui_catalogue_panel_demo.html`
  - `_includes/ui_catalogue_notes/panel.md`
  - `assets/studio/css/studio.css`
- local verification:
  - build docs payloads and the site to a separate destination
  - inspect the nested panel example on `/studio/ui-catalogue/panel/`
  - confirm the inner panel reads as subordinate containment without page-local overrides
- follow-up:
  - use the same rule when defining future primitives that can self-compose
  - audit live pages for obsolete local compensation after shared primitive fixes land

## UI Rule Log 2026-04-20 / UI-002

- status: adopted
- route: `/studio/ui-catalogue/panel/`
- issue: the first panel primitive reference wrapped the live examples in outer `.tagStudio__panel` sections and arranged the variants in a horizontal comparison grid. That made the editor variant appear to overlap its container and made edge inspection noisy.
- triage: systemic
- reasoning: the visible defect came from the primitive catalogue template, not from the shared `tagStudio__panel--editor` variant itself. If the catalogue page introduces nested-shell artifacts, future page work can inherit false assumptions about which primitive is broken.
- permanent rule: primitive catalogue pages must show shared primitives in a neutral wrapper by default, use vertical variant stacking, and keep notes focused on implementation constraints and composition warnings. When self-composition is a real use case, add it deliberately as its own variation rather than letting it appear accidentally through the page shell.
- enforcement point: `studio/ui-catalogue/*`, `_includes/studio_ui_catalogue_*.html`, and the primitive-catalogue guidance in `studio-ui-framework.md`
- files changed:
  - `studio/ui-catalogue/panel/index.md`
  - `_includes/studio_ui_catalogue_panel_demo.html`
  - `_includes/ui_catalogue_notes/panel.md`
  - `assets/studio/css/studio.css`
  - `_docs_src/studio-ui-framework.md`
  - `_docs_src/ui-catalogue.md`
- local verification:
  - build the site to a separate destination
  - inspect `/studio/ui-catalogue/panel/` on desktop and mobile widths
  - confirm each panel variant sits on a neutral surface with no enclosing panel shell
  - confirm self-composition cases are shown only when intentionally added in the markup
- follow-up:
  - apply the same neutral-surface template to future primitive pages
  - if a primitive still shows a defect after neutral rendering, fix the primitive rather than documenting around it

## UI Rule Log 2026-04-19 / UI-001

- status: adopted
- route: `/studio/catalogue-work/`
- issue: the `New Detail` action looked visually inconsistent beside the shared Studio search input and adjacent section actions; the reported symptom was non-standard button height
- triage: systemic
- reasoning: the first pass treated the issue as local layout only, but the more important finding was that shared Studio buttons were not explicitly using `border-box` sizing. That meant anchor-backed buttons using `tagStudio__button` could render at a different effective height from standard Studio controls even when they appeared to share the same class.
- permanent rule: shared Studio action controls must derive their geometry from the shared primitive, not from route-specific compensation. If a control uses `tagStudio__button`, its height and box model must match the Studio control token contract whether the element is a native `<button>` or an `<a>` styled as a button.
- enforcement point: `assets/studio/css/studio.css` in the shared `.tagStudio__button` rule
- files changed:
  - `assets/studio/css/studio.css`
  - `studio/catalogue-work/index.md`
- local verification:
  - inspect the route in the in-app browser at `/studio/catalogue-work/`
  - compare `New Detail`, `New File`, `New Link`, and nearby search/input controls
  - confirm the shared control height is visually consistent after refresh
- follow-up:
  - when a future UI issue touches a shared primitive, record the decision here even if the visible defect was first reported on one route
  - prefer fixing shared primitives before adding page-specific overrides

### Example Triage Note For This Issue

Use this structure when the issue first appears:

```text
route: /studio/catalogue-work/
problem: `New Detail` button appears visually inconsistent; reported symptom is non-standard height
initial triage: pending
first hypothesis: local layout mismatch in the work-details header row
after inspection: systemic
reason: shared `tagStudio__button` sizing contract is incomplete for anchor-backed buttons
action: fix shared button primitive, then record permanent rule in studio-ui-rules.md
```

### Subsequent Actions For This Issue

1. Fix the immediate UI defect.
2. Decide whether the root cause lives in page markup or a shared primitive.
3. If shared, update the shared primitive rather than compensating on one route.
4. Add or update the rule entry in this document.
5. Recheck the original route and at least one sibling route that uses the same primitive.

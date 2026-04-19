---
doc_id: css-refactor
title: "CSS Refactor"
last_updated: 2026-04-19
parent_id: design
sort_order: 60
---
# CSS Refactor

This is the active cleanup strategy for the shared UI layer.

Treat it as a controlled design-system refactor, not a general “make CSS nicer” pass.

The core problem is not just stylesheet size. The main sources of friction are:

- raw values like `12px` or ad hoc colors
- page-specific selectors solving the same visual problem differently
- shared elements being designed and modified at the same time as page layout
- primitives that exist in practice but are not enforced tightly enough

## Current Position

The repo already has useful foundations:

- `assets/css/main.css` for site-wide tokens
- `assets/studio/css/studio.css` for Studio tokens and shared primitives
- [UI Framework](/docs/?scope=studio&doc=ui-framework) for site-wide UI contract boundaries
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework) for shared Studio primitives and modal patterns
- [CSS Primitives](/docs/?scope=studio&doc=css-primitives) for the shared CSS contract

So the next step is not a broad rewrite and not a default move to JS web components.

The immediate need is to make the UI vocabulary more formal and harder to drift away from.

## Formalize The UI Vocabulary

Define and maintain a small approved set of layers:

- tokens
- primitives
- compositions
- behaviors

### Tokens

Lock the foundations first:

- typography scale
- color, surface, and border tokens
- spacing, radius, shadow, and measure tokens
- a small semantic alias layer such as `--surface-panel`, `--text-muted`, and approved control sizing tokens

### Primitives

Define a small stable set of reusable building blocks:

- panel
- button
- input
- pill / chip
- message / status block
- list shell

These should have canonical markup and styling rules, not just “similar-looking examples”.

### Compositions

Define a few approved higher-level patterns:

- editor panel
- toolbar / action row
- filter row
- split view
- confirm modal
- grouped data list

Rule:

- pages should compose approved primitives and compositions
- if a page needs a new shared element, define or update the primitive first
- avoid inventing page-local versions of shared UI during page layout work

## Web Components Boundary

Native custom elements may be useful, but they are not the first lever.

Use plain HTML plus shared CSS and template/includes for:

- visual shells such as panels, cards, simple list wrappers, and content sections

Consider native web components only for repeated stateful widgets such as:

- modal controllers
- tag pickers
- search/filter widgets
- viewer controls
- other repeated interactive modules with internal state and event handling

For this site, do not start by turning a passive shell like `panel` into a JS component. That adds ceremony without solving the main problem.

If custom elements are introduced, prefer light DOM unless there is a strong reason to isolate styling. The current site already depends heavily on shared tokens and global theming.

## Migration Order

Work in this sequence:

1. freeze the token layer
2. audit duplicated raw values and repeated UI patterns
3. finalize the approved primitive and composition inventory
4. migrate one concern at a time
5. add guardrails so drift does not regrow

Do not mix multiple refactor concerns in one pass. Keep rollback boundaries clear.

## One-Concern-At-A-Time Sequence

Use this order:

1. typography tokens and font-size cleanup
2. color tokens
3. spacing, radius, border, and shadow cleanup
4. shared layout primitives and compositions
5. page-by-page removal of redundant selectors

Do not redesign components while doing token cleanup. First stabilize the shared contract, then migrate callers onto it.

## Guardrails

Once a token family or primitive is standardized, add checks so the codebase does not slide back:

- audit raw `font-size` declarations outside approved token files
- audit raw hex colors outside approved token files
- audit repeated border, radius, and shadow literals
- audit new page-specific selectors that recreate an existing primitive

The initial cleanup matters less than preventing drift from returning.

## Success Criteria

The goal is not just smaller CSS. Better structural signals are:

- fewer raw values
- fewer page-specific selectors for shared UI
- more pages composed from shared primitives
- clearer expectations for recurring elements such as `panel`, `toolbar`, and `list shell`
- easier global restyling by changing tokens rather than rewriting page CSS

## Immediate Next Steps

The current next step should be:

1. re-run the token audit across `main.css` and `studio.css`
2. finalize the shared text scale and color/token aliases
3. write down the canonical contract for the first primitive set:
   `panel`, `button`, `input`, `list shell`, `toolbar`, `modal shell`
4. migrate typography first, without redesigning page layouts
5. only then decide whether any repeated interactive widget actually merits a native custom element

## Audit Status

The earlier audit direction is still sound:

- `main.css` shows typography drift more than color drift
- `studio.css` has too many near-duplicate UI text sizes
- several Studio rules still hardcode values that should become tokens or semantic aliases

So the first real cleanup pass should still be typography before color or broader layout work.

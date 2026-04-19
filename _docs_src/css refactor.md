---
doc_id: css-refactor
title: "CSS Refactor"
last_updated: 2026-03-31
parent_id: design
sort_order: 60
---
Tackle it as a controlled design-system cleanup, not a general “make CSS nicer” pass.

The core problem is probably not just file length. It’s that the codebase has too many one-off decisions:
- raw values like `12px` or ad hoc colors
- page-specific selectors solving the same visual problem differently
- primitives that exist informally but are not enforced

I would do it in this order.

**1. Freeze the foundations**
Start by defining the tokens and rules you actually want to keep using:
- typography tokens
- color tokens
- spacing tokens
- radius, border, shadow, z-index, breakpoints
- a small set of semantic aliases like `--font-size-body-sm`, `--color-text-muted`, `--surface-panel`

Important point: don’t write a big abstract style guide first. Build a small “living foundation” in CSS and a short doc while you refactor.

**2. Audit before rewriting**
Do a quick inventory of the values and patterns that are currently duplicated:
- every raw `font-size`
- every raw color
- repeated border/radius/shadow declarations
- repeated list/table/card/filter/toolbar/modal patterns

This gives you the high-value targets. You already know `font-size` is one. Colors are likely next. After that, spacing and panel/list shells are usually where redundancy hides.

**3. Standardize primitives, not pages**
Don’t start page-by-page with arbitrary cleanup. First define a handful of reusable patterns:
- text scale
- panel
- button
- input
- list shell
- chip/tag
- toolbar/filter row
- form row
- modal shell

For your “lists” example, define maybe 3-4 approved list patterns only:
- content list
- data list
- chip list
- grouped list

Then migrate existing pages onto those patterns instead of inventing per-page list CSS.

**4. Migrate one concern at a time**
Best sequence:
1. typography tokens and font-size cleanup
2. color tokens
3. spacing/radius/border/shadow cleanup
4. shared layout primitives
5. page-by-page removal of now-redundant selectors

Do not mix all of those in one pass. If you do, you’ll lose the rollback boundary and won’t know what caused regressions.

**5. Add guardrails**
Once a token family is in place, stop the codebase from drifting back:
- add a lint rule or check for raw `font-size: 12px` style declarations outside approved files
- do the same for raw hex colors
- optionally add a small audit script that reports new raw values

That matters more than the initial cleanup. Otherwise the redundancy just regrows.

**6. Measure success structurally**
The goal is not “smaller CSS” by itself. The better signals are:
- fewer raw values
- fewer page-specific selectors for shared UI
- more selectors composed from shared primitives
- easier to restyle the whole site by changing tokens
- file size reduction as a side effect

My recommendation for the immediate next step:
- do a token audit for typography and color across `main.css` and `studio.css`
- create the final token set
- migrate only those two concerns first
- then review what repeated UI patterns remain, especially lists/panels/toolbars

If you want, I can take the next practical step and do the audit pass first: extract the current raw `font-size` and color values from both CSS files and turn that into a cleanup plan.

I added a repeatable audit script at `scripts/css_token_audit.py`, generated the current snapshot in [CSS Audit Latest](/docs/?scope=studio&doc=css-audit-latest), and documented it in [CSS Token Audit](/docs/?scope=studio&doc=scripts-css-token-audit). Verification was just the script run: `python3 scripts/css_token_audit.py`.

What the audit says is useful:
- `main.css` has a typography drift problem more than a color problem. The biggest hotspot is `12px` used 12 times, plus smaller clusters at `13px`, `0.88rem`, `0.9rem`, `0.95rem`, and one `16px` lede.
- `studio.css` has a compressed-but-messy UI text scale: `0.78rem` 12 times, `0.82rem` 9 times, `0.86rem` 5 times, `0.83rem` 3 times. That is almost certainly too many near-duplicate sizes for a ~10-page site.
- Color is less urgent in `main.css`: only a handful of direct literals remain outside the theme tokens. `studio.css` is more mixed: the palette is tokenized at the top, but several component rules still hardcode values like `#fff`, `#1f1f1f`, `#d2d2d2`, and the weight-dot fills.

So the first real cleanup pass should be typography only, not lists or colors yet:
1. Finalize a shared text scale and decide whether `13px` survives or gets eliminated.
2. Add a small Studio typography alias layer so `0.78/0.82/0.83/0.86/0.88/0.9` collapse into a controlled set.
3. Replace repeated literals in `main.css` and `studio.css` with those tokens, without redesigning components yet.
4. Re-run [CSS Audit Latest](/docs/?scope=studio&doc=css-audit-latest) and only then start the color pass.

If you want, I can take that next pass now and do the typography-token consolidation only.

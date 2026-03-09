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
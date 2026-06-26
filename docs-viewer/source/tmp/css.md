---
doc_id: css
title: "css"
added_date: 2026-06-26
last_updated: 2026-06-26
---

> I notice that analytics.css is 2600 lines, do css files normally get so long? how do you tell that it's full of stuff it shouldn't have?

Yes, CSS files can get that long, especially in older single-app stylesheets. `2600` lines is not automatically bad. It becomes a problem when the file stops being a coherent stylesheet and turns into a dumping ground.

Signals it’s probably carrying stuff it shouldn’t:

- Unclear ownership: unrelated route styles mixed together with no sections or naming boundary.
- High selector coupling: selectors reach across components, like `.page .panel .row button span`, instead of styling a local class.
- Many one-off overrides: lots of “fix this specific element” rules after the main rule.
- Dead classes: rules for markup that no longer exists.
- Repeated patterns: same grid, modal, button, field, list styles recreated under different names.
- Global leakage: route-specific rules affecting shared controls unintentionally.
- CSS used to hide bad markup: duplicated DOM or inaccessible labels hidden with CSS instead of fixing markup.
- Hard-coded layout values everywhere: many magic widths/heights that make responsive behavior fragile.
- Frequent need for `!important`.
- A small UI change requires searching hundreds of lines to understand side effects.

For this file, the naming is actually a useful clue: many classes are route-scoped, like `dataSharingPrepare...`, `dataSharingReview...`, `tagRegistry...`. That suggests it’s a bundled app stylesheet rather than pure chaos. But at 2600 lines, I’d expect stale route CSS and repeated modal/list/form patterns to accumulate.

A practical audit is:

```bash
rg -n "!important|display:\\s*none|position:\\s*absolute|z-index|min-height|height:|width:|dataSharingPrepareContextModal" analytics-app/app/assets/css/analytics.css
```

Then check whether selectors map to live markup:

```bash
rg -n "dataSharingPrepareContextModal__textarea|dataSharingPrepareContextModal__fieldLabel" analytics-app/app
```

If a class appears only in CSS and nowhere in generated/static markup, it’s probably dead. The file is “too full” when those dead/duplicated/cross-route rules become common enough that changes feel risky.

~

`rg` is **ripgrep**, a fast command-line search tool. It’s like `grep`, but usually faster and nicer for codebases.

If it doesn’t run for you, it probably isn’t installed or isn’t on your `PATH`.

Use `grep` instead:

```bash
grep -RIn "dataSharingPrepareContextModal__textarea" analytics-app/app
```

Equivalent to the earlier examples:

```bash
grep -nE "!important|display:[[:space:]]*none|position:[[:space:]]*absolute|z-index|min-height|height:|width:" analytics-app/app/assets/css/analytics.css
```

Search for a class across the app:

```bash
grep -RIn "dataSharingPrepareContextModal__fieldLabel" analytics-app/app
```

On macOS, you can install `rg` with Homebrew:

```bash
brew install ripgrep
```

But `grep` is fine for these checks.

~

It can be, if you try to “audit CSS” as a project. I wouldn’t.

For this repo, I’d treat it opportunistically:

- When touching a UI area, check only the nearby route/component classes.
- Remove dead CSS only when you can prove the class is no longer used.
- Prefer fixing markup over hiding odd markup with CSS.
- Avoid adding new global rules unless they are truly shared.
- If a section gets painful, split that route’s styles then, not preemptively.

For the Edit context modal, the useful check was just:

```bash
grep -RIn "dataSharingPrepareContextModal" analytics-app/app
```

That tells you the local ownership boundary. No need to inventory all 2600 lines unless the stylesheet itself starts blocking routine changes.